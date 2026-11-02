"""Verify the successful lock against installed metadata and retained wheel hashes."""
import hashlib,importlib.metadata as md,json,re
from pathlib import Path
rows=[]
for line in Path('export/requirements.lock').read_text().splitlines():
    if not line or line.startswith('#'):continue
    spec,sha=line.split(' --hash=sha256:');name,version=spec.split('==')
    assert md.version(name)==version,(name,md.version(name),version)
    candidates=[]
    for p in Path('export/downloads').glob('*.whl'):
        if p.name.lower().replace('_','-').startswith(name.lower().replace('_','-')+'-'+version):candidates.append(p)
    match=None
    for p in candidates:
        with p.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        if actual==sha:match=p;break
    assert match is not None,'retained matching wheel missing: '+name
    rows.append({'name':name,'version':version,'filename':match.name,'bytes':match.stat().st_size,'sha256':sha})
assert md.version('nemo_toolkit')=='3.1.0'
r={'locked_packages_verified':len(rows),'nemo_toolkit':'3.1.0','packages':rows,'status':'matches-successful-installed-environment'}
Path('export/reports/working-artifacts.json').write_text(json.dumps(r,indent=2)+'\n')
print(r['status'],len(rows))
