#!/usr/bin/env python3
"""After approved export: real-weight graph/ABI diagnostics, NOT speech recognition."""
import argparse
import json
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('bundle')
    a=p.parse_args()
    root=Path(a.bundle)
    import numpy as np
    import onnx
    import onnxruntime as ort
    options=ort.SessionOptions()
    options.intra_op_num_threads=1
    options.inter_op_num_threads=1
    sessions={}
    quantized=False
    for key,file in [('encoder','encoder.int8.onnx'),('decoder','decoder.onnx'),('joiner','joiner.onnx')]:
        path=root/file
        onnx.checker.check_model(str(path))
        graph=onnx.load(str(path),load_external_data=False)
        if key=='encoder':
            quantized=any(n.op_type in ('MatMulInteger','QLinearMatMul') for n in graph.graph.node)
        del graph
        sessions[key]=ort.InferenceSession(str(path),options,providers=['CPUExecutionProvider'])
    assert quantized, 'encoder contains no quantized MatMul operator'
    enc,dec,joint=[sessions[k] for k in ['encoder','decoder','joiner']]
    m=enc.get_modelmeta().custom_metadata_map
    assert m['streaming_model_type']=='nemo_parakeet_unified_streaming'
    assert [int(m[k]) for k in ['left_encoder_frames','chunk_encoder_frames','right_encoder_frames']]==[37,7,7]
    prompts=json.loads(m.get('prompt_dictionary',m.get('language_prompt_ids','{}')))
    assert 'de' in prompts and 'auto' in prompts
    tokens=[]
    for line in (root/'tokens.txt').read_text().splitlines():
        token,idx=line.rsplit(' ',1)
        assert int(idx)==len(tokens), 'token IDs not contiguous'
        tokens.append(token)
    blank=int(m['vocab_size'])
    assert len(tokens)==blank+1 and tokens[blank]=='<blk>'
    assert [v.type for v in enc.get_inputs()]==['tensor(float)','tensor(int64)','tensor(int64)']
    assert [v.type for v in dec.get_inputs()]==['tensor(int32)','tensor(int32)','tensor(float)','tensor(float)']
    assert len(joint.get_inputs())==2
    total=sum(int(m[k]) for k in ['left_feature_frames','chunk_feature_frames','right_feature_frames'])
    features=np.zeros((1,int(m['feat_dim']),total),dtype=np.float32)
    # Diagnostic zeros exercise graph wiring; these are never interpreted as recorded speech.
    def run(s,values):
        inputs=s.get_inputs()
        assert len(inputs)==len(values)
        result=s.run(None,dict(zip([i.name for i in inputs],values)))
        assert all(np.all(np.isfinite(x)) for x in result)
        return result
    encoded=run(enc,[features,np.array([total],dtype=np.int64),np.array([prompts['de']],dtype=np.int64)])
    shape=(int(m['pred_rnn_layers']),1,int(m['pred_hidden']))
    predicted=run(dec,[np.array([[blank]],dtype=np.int32),np.array([1],dtype=np.int32),
                       np.zeros(shape,dtype=np.float32),np.zeros(shape,dtype=np.float32)])
    assert len(predicted)==4 and all(x.shape==shape for x in predicted[2:])
    joined=run(joint,[encoded[0][:,:,:1],predicted[0]])
    assert joined[0].shape[-1]==len(tokens), 'joint vocabulary mismatch'
    report={'status':'graph-and-ABI-diagnostics-passed','speech_recognition_validated':False,
            'reference_recording_used':False,'language':'de','prompt_id':prompts['de'],
            'token_count':len(tokens),'blank_id':blank,'tokenizer_scope':'ID table only; SentencePiece parity still pending',
            'quantized_matmul_present':quantized,'onnxruntime_version':ort.__version__,
            'graphs':{k:{'inputs':[(x.name,x.type,x.shape) for x in s.get_inputs()],
                         'outputs':[(x.name,x.type,x.shape) for x in s.get_outputs()]} for k,s in sessions.items()}}
    dest=root/'component-diagnostics.json'
    with dest.open('x') as f:
        json.dump(report,f,indent=2)
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    main()
