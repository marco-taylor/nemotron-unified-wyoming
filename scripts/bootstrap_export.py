#!/usr/bin/env python3
"""Small packaging prerequisites, each metadata-checked and <=2 MiB."""
import hashlib,json,subprocess,urllib.request,zipfile
from pathlib import Path
root=Path('export/bootstrap');records=[]
for name,version,kind in [('setuptools','80.9.0','bdist_wheel'),('wheel','0.45.1','bdist_wheel'),('packaging','25.0','bdist_wheel'),('antlr4-python3-runtime','4.9.3','sdist')]:
    with urllib.request.urlopen(f'https://pypi.org/pypi/{name}/{version}/json',timeout=30) as r:meta=json.load(r)
    f=next(f for f in meta['urls'] if f['packagetype']==kind)
    assert f['size']<=2*1024**2
    subprocess.run(['python3','scripts/download_bounded.py',f['url'],str(root/f['filename']),'--bytes',str(f['size']),'--sha256',f['digests']['sha256']],check=True)
    records.append({'name':name,'bytes':f['size'],'file':f['filename'],'sha256':f['digests']['sha256']})
Path('export/reports/bootstrap-downloads.json').write_text(json.dumps(records,indent=2))
