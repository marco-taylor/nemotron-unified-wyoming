#!/usr/bin/env python3
"""Fix only stale version-reporting literals in the pinned upstream source."""
import json
import os
from pathlib import Path
import subprocess

root = Path('/opt/sherpa/src')
expected = os.environ['SHERPA_COMMIT']
actual = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
assert actual == expected
path = root / 'sherpa-onnx/csrc/version.cc'
source = path.read_text()
old = 'static const char *sha1 = "96255a1b";'
assert source.count(old) == 1, 'Upstream changed: re-review provenance patch'
source = source.replace(old, 'static const char *sha1 = ' + json.dumps(actual) + ';')
date = subprocess.check_output(['git', '-C', str(root), 'show', '-s', '--format=%ad', '--date=default', 'HEAD'], text=True).strip()
old_date = 'static const char *date = "Mon Oct 26 21:50:15 2026";'
assert source.count(old_date) == 1
source = source.replace(old_date, 'static const char *date = ' + json.dumps(date) + ';')
path.write_text(source)
Path('/opt/sherpa/lib/SOURCE_PATCH').write_text('Only version.cc Git SHA/date reporting literals stamped from verified checkout. No model/runtime logic changes.\n')
print('Stamped actual source commit:', actual)
