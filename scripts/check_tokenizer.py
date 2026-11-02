"""Validate the actual checkpoint tokenizer/vocabulary, not speech recognition."""
import json,tarfile
from pathlib import Path
import sentencepiece as spm
import yaml
root=Path('export/reports/tokenizer');root.mkdir(exist_ok=True)
with tarfile.open('models/source/nemotron-labs-unified-asr-0.6b.nemo') as t:
    cfg=yaml.safe_load(t.extractfile('./model_config.yaml'))
    member=next(m for m in t.getmembers() if m.name.endswith('_tokenizer.model'))
    data=t.extractfile(member).read()
sp=spm.SentencePieceProcessor(model_proto=data)
vocab=cfg['joint']['vocabulary']
assert len(vocab)==sp.get_piece_size()
assert all(token==sp.id_to_piece(i) for i,token in enumerate(vocab))
assert cfg['model_defaults']['prompt_dictionary']['de']==9
exported=[line.rsplit(' ',1)[0] for line in Path('models/L37-runtime/tokens.txt').read_text().splitlines()]
assert exported==vocab+['<blk>'], 'exported tokens differ from original SentencePiece vocabulary'
text=Path('benchmarks/reference.txt').read_text().strip()
ids=sp.encode(text,out_type=int)
report={'checkpoint_tokenizer_vocab_parity':True,'exported_tokens_match_checkpoint':True,'vocabulary_without_blank':len(vocab),
    'blank_id':cfg['decoder']['vocab_size'],'german_prompt_id':9,'reference':text,
    'token_ids':ids,'decoded_reference':sp.decode(ids),'speech_recognition_validated':False}
(root/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
