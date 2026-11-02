#!/usr/bin/env python3
"""Metadata only. Never follow weight/download links."""
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

urls = [
    'https://api.github.com/repos/k2-fsa/sherpa-onnx/pulls/4141',
    'https://api.github.com/repos/k2-fsa/sherpa-onnx/pulls/4133',
    'https://api.github.com/repos/k2-fsa/sherpa-onnx/releases/tags/asr-models',
    'https://api.github.com/repos/k2-fsa/sherpa-onnx/releases/tags/asr-models-2',
    'https://api.github.com/repos/k2-fsa/sherpa-onnx/releases/tags/asr-models-3',
    'https://huggingface.co/api/models/FluidInference/nemotron-labs-unified-asr-0.6b-coreml?blobs=true',
    'https://huggingface.co/api/models?search=nemotron-labs-unified&limit=100',
    'https://huggingface.co/api/models/csukuangfj2/sherpa-onnx-nemotron-labs-unified-asr-0.6b-int8-streaming-1120ms-L37?blobs=true',
    'https://huggingface.co/api/models/nvidia/nemotron-labs-unified-asr-0.6b?blobs=true',
    'https://huggingface.co/api/models/loom-ai-org/nemotron-labs-unified-asr-0.6b-loom?blobs=true',
]
report = {'checked_utc': datetime.now(timezone.utc).isoformat(), 'metadata_only': True, 'sources': []}
for url in urls:
    record = {'url': url}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'nemotron-feasibility/0.2'}), timeout=30) as response:
            record['http_status'] = response.status
            x = json.load(response)
            if '/pulls/' in url:
                record.update(state=x['state'], merged=x['merged'], head=x['head']['sha'], body=x['body'])
            elif '/releases/' in url:
                record['asset_count'] = len(x['assets'])
                record['matching_assets'] = [{'name':a['name'],'size':a['size'],'url':a['browser_download_url']} for a in x['assets'] if 'nemotron-labs-unified' in a['name'].lower()]
            elif isinstance(x, list):
                record['repositories'] = [m['id'] for m in x]
            else:
                record.update(sha=x.get('sha'), files=[{'path':f['rfilename'],'size':f.get('size'),'lfs':f.get('lfs')} for f in x.get('siblings',[])])
    except urllib.error.HTTPError as e:
        record['http_status'] = e.code
        record['note'] = 'Not publicly accessible; no claim about private repository existence.'
    except Exception as e:
        record['error'] = str(e)
    report['sources'].append(record)
print(json.dumps(report, indent=2))
