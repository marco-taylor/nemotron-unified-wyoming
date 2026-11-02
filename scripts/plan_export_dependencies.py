#!/usr/bin/env python3
"""Make resolver inputs from the pinned NeMo pyproject; no wheel downloads here."""
import json,tomllib
from pathlib import Path
x=tomllib.loads(Path('docs/evidence/phase4-nemo-pyproject.toml').read_text())['project']
req=x['dependencies']+x['optional-dependencies']['asr']+['torchaudio==2.7.1+cpu','onnxruntime==1.23.2','ipython','wheel']
Path('export/requirements.in').write_text('\n'.join(dict.fromkeys(req))+'\n')
