#!/usr/bin/env python3
"""Bounded, resumable file fetch; only explicitly supplied URLs, sizes and hashes."""
import argparse,hashlib,json,os,urllib.request
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('url');p.add_argument('output');p.add_argument('--bytes',type=int,required=True);p.add_argument('--sha256',required=True);a=p.parse_args()
dest=Path(a.output);part=dest.with_name(dest.name+'.part');dest.parent.mkdir(parents=True,exist_ok=True)
if dest.exists():
    assert dest.stat().st_size==a.bytes
    with dest.open('rb') as f: assert hashlib.file_digest(f,'sha256').hexdigest()==a.sha256
    print('Already verified:',dest);raise SystemExit(0)
offset=part.stat().st_size if part.exists() else 0
assert offset<=a.bytes
if offset<a.bytes:
    req=urllib.request.Request(a.url,headers={'Range':f'bytes={offset}-'} if offset else {})
    with urllib.request.urlopen(req,timeout=90) as r:
        if offset and r.status!=206: raise RuntimeError('server ignored resume range; preserving partial file')
        length=r.headers.get('Content-Length')
        if length and int(length)+offset!=a.bytes: raise RuntimeError('Content-Length mismatch')
        with part.open('ab' if offset else 'xb') as f:
            while True:
                b=r.read(1024*1024)
                if not b:break
                offset+=len(b)
                if offset>a.bytes:raise RuntimeError('download size limit exceeded')
                f.write(b)
assert part.stat().st_size==a.bytes
with part.open('rb') as f: assert hashlib.file_digest(f,'sha256').hexdigest()==a.sha256,'SHA256 mismatch'
part.rename(dest)
print(json.dumps({'file':str(dest),'bytes':a.bytes,'sha256':a.sha256,'verified':True}))
