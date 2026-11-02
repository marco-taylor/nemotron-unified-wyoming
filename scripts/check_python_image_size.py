import json,urllib.request
from pathlib import Path
repo='library/python';tag='3.11.14-slim-bookworm'
with urllib.request.urlopen('https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/python:pull',timeout=30) as r:token=json.load(r)['token']
def manifest(ref):
    req=urllib.request.Request(f'https://registry-1.docker.io/v2/{repo}/manifests/{ref}',headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json'})
    with urllib.request.urlopen(req,timeout=30) as r:return json.load(r),r.headers.get('Docker-Content-Digest')
x,idx=manifest(tag)
if 'manifests' in x:
    digest=next(m['digest'] for m in x['manifests'] if m['platform'].get('architecture')=='amd64' and m['platform'].get('os')=='linux')
    x,_=manifest(digest)
else:digest=idx
size=sum(l['size'] for l in x['layers'])
used=sum(p.stat().st_size for d in ['export/downloads','export/bootstrap'] for p in Path(d).glob('*') if p.is_file())
assert used+size+128*1024**2<3*1024**3
out={'tag':tag,'amd64_digest':digest,'compressed_layer_bytes':size,'layers':x['layers'],'previous_artifact_bytes':used,'budget_limit':3*1024**3}
Path('export/reports/python-image-size.json').write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items() if k!='layers'}))
