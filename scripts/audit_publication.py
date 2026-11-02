"""Check the exact Git index before publication. No secret values are printed."""
import hashlib
import json
import pathlib
import re
import subprocess
import sys

history='--history' in sys.argv
worktree='--worktree' in sys.argv
entries=[]
if history:
    commits=subprocess.check_output(['git','rev-list','--all' if '--all-refs' in sys.argv else 'HEAD']).decode().splitlines()
    for commit in commits:
        records=subprocess.check_output(['git','ls-tree','-rz',commit]).split(b'\0')
        for record in filter(None,records):
            metadata,name=record.split(b'\t',1)
            mode,kind,oid=metadata.decode().split()
            if kind=='blob': entries.append((name.decode(),oid))
    entries=list(dict.fromkeys(entries))
else:
    command=['git','ls-files','-z']
    if worktree:
        command += ['--cached','--others','--exclude-standard']
    names=subprocess.check_output(command).decode().split('\0')
    entries=[(name,':'+name) for name in filter(None,names)]
patterns=[rb'github_pat_[A-Za-z0-9_]{30,}',rb'gh[pousr]_[A-Za-z0-9]{30,}',rb'hf_[A-Za-z0-9]{20,}',rb'sk-[A-Za-z0-9_-]{30,}',rb'-----BEGIN (?:OPENSSH |RSA |EC |DSA )?PRIVATE KEY-----',rb'AKIA[A-Z0-9]{16}',rb'[?&](?:X-Amz-Signature|X-Goog-Signature|token)=[A-Za-z0-9%_-]{20,}']
icons={
    "assets/icons/nemotron-hq.png": "ebc6f304d492a6523d5afebf8d21faf87f9a6d10d5ee362e924bfa2ead1a5b25",
    "assets/icons/nemotron-lowq.png": "242a931bd2c14dfc05a8bbbee544120ede39845a97350146a11c552c299d077b",
}
# Known superseded logo assets must never slip into the published ancestry.
legacy_icon_hashes={
    'cc53b98a5c51d2eafc3ad12a9145f5dbc97600668da660fb1fe2475b272bbc26',
    '2e9de9ecfaa42b4bfcff7536ed2b7f6cbfe090d25b7c2c67ed78257e81411082',
}
errors=[]
size=0
count=0
for name,ref in entries:
    path=pathlib.PurePosixPath(name)
    forbidden=path.suffix.lower() in {'.onnx','.nemo','.safetensors','.pt','.pth','.ckpt','.wav','.flac','.whl','.zip','.pem','.key','.bin'}
    forbidden|=name.startswith(('models/','target/','export/reports/','benchmarks/audio/','benchmarks/results/'))
    forbidden|=path.name=='.env' or (path.name.startswith('.env.') and path.name!='.env.example')
    if forbidden: errors.append({'path':name,'reason':'forbidden file type/location'})
    body=pathlib.Path(name).read_bytes() if worktree else subprocess.check_output(['git','show',ref])
    digest=hashlib.sha256(body).hexdigest()
    if digest in legacy_icon_hashes: errors.append({'path':name,'reason':'superseded NVIDIA logo in publication history'})
    approved_icon=name in icons and digest==icons[name]
    if name in icons and not approved_icon: errors.append({'path':name,'reason':'unreviewed icon content'})
    if len(body)>1024*1024 and not approved_icon: errors.append({'path':name,'reason':'file exceeds 1 MiB'})
    if b'\0' in body and not approved_icon: errors.append({'path':name,'reason':'binary file'})
    if any(re.search(p,body) for p in patterns): errors.append({'path':name,'reason':'credential/signature pattern'})
    size+=len(body);count+=1
print(json.dumps({'scope':'reachable history' if history else 'worktree' if worktree else 'index','files':count,'total_bytes':size,'findings':errors},indent=2))
if not count or errors: raise SystemExit(1)
