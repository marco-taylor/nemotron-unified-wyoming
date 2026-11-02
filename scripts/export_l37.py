#!/usr/bin/env python3
"""Offline-only wrapper for the actual pinned PR exporter. Never downloads a model."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

COMMIT = '31ba0e438f8065189a8e5589d84dfd7faf516d3d'
MODEL_SHA = '1718cc1b44fb8597b2356328d706a8d89f31c389ca6f2256c2e3f743c0246936'
MODEL_BYTES = 2507735040

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model', required=True)
    p.add_argument('--output', required=True)
    a=p.parse_args()
    model=Path(a.model).resolve()
    if model.stat().st_size != MODEL_BYTES:
        p.error('checkpoint size does not match approved official model')
    with model.open('rb') as f:
        if hashlib.file_digest(f,'sha256').hexdigest() != MODEL_SHA:
            p.error('checkpoint SHA256 mismatch')
    source=Path('/opt/sherpa/src')
    actual=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
    if actual != COMMIT:
        p.error('exporter source revision mismatch')
    output=Path(a.output).resolve()
    # Exporter itself unlinks intermediate weights. Never run inside an existing output.
    if output.exists():
        p.error('output must be a NEW directory; existing results are preserved')
    if shutil.disk_usage(output.parent).free < 40*1024**3:
        p.error('less than conservative 40 GiB free disk budget')
    env=dict(os.environ, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', CUDA_VISIBLE_DEVICES='',
             OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='1')
    output.mkdir()
    exporter=source/'scripts/nemo/nemotron-labs-unified-asr-0.6b/export_onnx.py'
    with (output/'export.log').open('w') as log:
        result=subprocess.run(['python',str(exporter),'--model',str(model),'--left-context','37'],
            cwd=output,env=env,stdout=log,stderr=subprocess.STDOUT)
    record={'sherpa_commit':COMMIT,'checkpoint_sha256':MODEL_SHA,'left_encoder_frames':37,
            'chunk_encoder_frames':7,'right_encoder_frames':7,'returncode':result.returncode,
            'status':'exported-awaiting-validation' if result.returncode==0 else 'failed'}
    (output/'export-status.json').write_text(json.dumps(record,indent=2)+'\n')
    if result.returncode:
        raise SystemExit(result.returncode)
    # This validates graph/ABI only, never claims a German transcription.
    subprocess.run(['python','/opt/export/validate_bundle.py',str(output)],env=env,check=True)

if __name__=='__main__':
    main()
