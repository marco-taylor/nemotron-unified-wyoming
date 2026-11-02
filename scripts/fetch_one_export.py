import json,subprocess,urllib.request,sys
from pathlib import Path
name,version=sys.argv[1:]
with urllib.request.urlopen(f'https://pypi.org/pypi/{name}/{version}/json',timeout=30) as r:m=json.load(r)
files=[f for f in m['urls'] if f['filename'].endswith('.whl') and ('cp311-cp311' in f['filename'] and 'manylinux' in f['filename'] and 'x86_64' in f['filename'] or 'py3-none-any' in f['filename'])]
assert files,'no suitable prebuilt wheel'
f=files[0];assert f['size']<100*1024**2
# Include all previous wheel/source/bootstrap downloads conservatively; keep budget headroom.
used=sum(p.stat().st_size for d in ['export/downloads','export/bootstrap'] for p in Path(d).glob('*') if p.is_file())
assert used+f['size']+128*1024**2<3*1024**3
record={'name':name,'version':version,'filename':f['filename'],'bytes':f['size'],'sha256':f['digests']['sha256']}
with Path('export/reports/extra-downloads.jsonl').open('a') as out:out.write(json.dumps(record)+'\n')
print(json.dumps(record),flush=True)
subprocess.run(['python3','scripts/download_bounded.py',f['url'],'export/downloads/'+f['filename'],'--bytes',str(f['size']),'--sha256',f['digests']['sha256']],check=True)
