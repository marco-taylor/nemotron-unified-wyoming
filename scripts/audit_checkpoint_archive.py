import json,tarfile
from pathlib import Path
p=Path('models/source/nemotron-labs-unified-asr-0.6b.nemo')
with tarfile.open(p) as t:
    members=t.getmembers()
    out=[{'name':m.name,'bytes':m.size} for m in members]
    cfg=next(m for m in members if m.name.endswith('model_config.yaml'))
    Path('export/reports/checkpoint-model-config.yaml').write_bytes(t.extractfile(cfg).read())
Path('export/reports/checkpoint-members.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
