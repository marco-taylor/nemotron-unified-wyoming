#!/usr/bin/env python3
"""Read package metadata/CPU wheel index only; never download wheels."""
import json
import urllib.request
from html.parser import HTMLParser
from datetime import datetime, timezone

def get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read()
report = {'checked_utc':datetime.now(timezone.utc).isoformat(), 'metadata_only':True, 'packages':[]}
for name, version in [('onnx','1.18.0'),('onnxruntime','1.28.2'),('torchaudio','2.7.1'),('numpy','1.26.4')]:
    url=f'https://pypi.org/pypi/{name}/{version}/json'
    try:
        x=json.loads(get(url))
        report['packages'].append({'name':name,'version':version,'url':url,'requires_dist':x['info'].get('requires_dist'),
            'linux_cp311_wheels':[{'filename':f['filename'],'bytes':f['size'],'sha256':f['digests']['sha256']}
                for f in x['urls'] if 'cp311' in f['filename'] and 'x86_64' in f['filename'] and 'linux' in f['filename']]})
    except Exception as e:
        report['packages'].append({'name':name,'version':version,'error':str(e)})
class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]
    def handle_starttag(self, tag, attrs):
        if tag=='a':
            href=dict(attrs).get('href','')
            if '2.7.1%2Bcpu' in href and 'cp311-cp311' in href and ('linux_x86_64' in href or 'manylinux' in href and 'x86_64' in href):
                self.links.append(href)
for package in ['torch','torchaudio']:
    url=f'https://download.pytorch.org/whl/cpu/{package}/'
    try:
        p=Links();p.feed(get(url).decode())
        report[package+'_cpu_candidates']=p.links
    except Exception as e:
        report[package+'_cpu_error']=str(e)
print(json.dumps(report,indent=2))
