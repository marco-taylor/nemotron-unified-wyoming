#!/usr/bin/env python3
"""Inspect EVERY candidate size, enforce total budget, then fetch hash-locked wheels."""
import concurrent.futures,hashlib,json,subprocess,urllib.parse,urllib.request
from pathlib import Path
root=Path('export')
if (root/'requirements.lock').exists():
    raise SystemExit('Existing successful lock is preserved. Use offline installation from retained wheels; do not overwrite it with a new resolver plan.')
plan=json.loads((root/'reports/pip-plan.json').read_text())
def inspect(item):
    d=item['download_info'];u=d['url'];m=item['metadata'];sha=d['archive_info']['hashes']['sha256']
    name=urllib.parse.unquote(urllib.parse.urlsplit(u).path.split('/')[-1])
    if u.startswith('file:'):
        size=Path(urllib.parse.unquote(urllib.parse.urlsplit(u).path)).stat().st_size
    else:
        req=urllib.request.Request(u,method='HEAD')
        with urllib.request.urlopen(req,timeout=45) as r:
            value=r.headers.get('Content-Length')
        if not value:
            with urllib.request.urlopen(f'https://pypi.org/pypi/{m["name"]}/{m["version"]}/json',timeout=30) as r:x=json.load(r)
            size=next(x['size'] for x in x['urls'] if x['filename']==name)
        else:size=int(value)
    return {'name':m['name'],'version':m['version'],'url':u,'filename':name,'bytes':size,'sha256':sha}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:rows=list(pool.map(inspect,plan['install']))
preexisting=sum(p.stat().st_size for p in (root/'bootstrap').glob('*') if p.is_file())
preexisting+=(root/'downloads/nemo-43dd97ddf.tar.gz').stat().st_size
reserve=128*1024**2
network=sum(r['bytes'] for r in rows if not r['url'].startswith('file:'))
report={'wheel_count':len(rows),'planned_wheel_bytes':network,'previous_artifact_bytes':preexisting,
    'metadata_and_retries_reserve_bytes':reserve,'conservative_total_bytes':network+preexisting+reserve,
    'limit_bytes':3*1024**3,'packages':rows}
(root/'reports/download-size-plan.json').write_text(json.dumps(report,indent=2)+'\n')
assert report['conservative_total_bytes']<=report['limit_bytes'],'download budget exceeded before wheel downloads'
print(json.dumps({k:v for k,v in report.items() if k!='packages'}),flush=True)
(root/'requirements.lock').write_text('\n'.join(f'{r["name"]}=={r["version"]} --hash=sha256:{r["sha256"]}' for r in rows)+'\n')
def download(r):
    dest=root/'downloads'/r['filename']
    source=root/'bootstrap'/r['filename']
    if source.exists():
        assert source.stat().st_size==r['bytes']
        assert hashlib.sha256(source.read_bytes()).hexdigest()==r['sha256']
        if not dest.exists():dest.write_bytes(source.read_bytes())
        return
    if r['url'].startswith('file:'):return
    subprocess.run(['python3','scripts/download_bounded.py',r['url'],str(dest),'--bytes',str(r['bytes']),'--sha256',r['sha256']],check=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(download,rows))
print('All planned wheels verified',flush=True)
