import collections,hashlib,json,math
from pathlib import Path
import onnx
root=Path('models/L37-runtime')
m=onnx.load(str(root/'encoder.int8.onnx'),load_external_data=False)
counts=collections.Counter(n.op_type for n in m.graph.node)
params=collections.Counter()
for t in m.graph.initializer:params[onnx.TensorProto.DataType.Name(t.data_type)]+=math.prod(t.dims)
assert counts['MatMulInteger']>0
assert params['UINT8']>0
assert not any(t.data_location==onnx.TensorProto.EXTERNAL for t in m.graph.initializer)
files={}
for n in ['encoder.int8.onnx','decoder.onnx','joiner.onnx','tokens.txt']:
    p=root/n
    with p.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    files[n]={'bytes':p.stat().st_size,'sha256':digest}
r={'files':files,'total_runtime_bytes':sum(v['bytes'] for v in files.values()),
    'matmul_integer_nodes':counts['MatMulInteger'],'initializer_elements_by_dtype':dict(params),
    'encoder_requires_external_weights':False,'precision':'partial encoder QUInt8; predictor/joiner FP32',
    'quantization_wer_delta_to_fp32':'not measured'}
Path('export/reports/final-bundle-audit.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
