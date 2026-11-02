"""Audit a streaming Docker export without printing credential values."""
import hashlib
import json
import pathlib
import re
import sys
import tarfile

# Token boundaries avoid matching long character-name tables in libunistring.
secret_patterns = [
    rb'(?<![A-Za-z0-9_])github_pat_[A-Za-z0-9_]{30,}(?![A-Za-z0-9_])',
    rb'(?<![A-Za-z0-9_])gh[pousr]_[A-Za-z0-9]{30,}(?![A-Za-z0-9_])',
    rb'(?<![A-Za-z0-9_])hf_[A-Za-z0-9]{20,}(?![A-Za-z0-9_])',
    rb'-----BEGIN (?:OPENSSH |RSA |EC |DSA )?PRIVATE KEY-----',
    rb'(?<![A-Za-z0-9_])AKIA[A-Z0-9]{16}(?![A-Za-z0-9_])',
]
# Exact Debian libgnutls30 3.7.9-2+deb12u7 binary, verified against dpkg.
# Its six complete PEM blocks match public upstream crypto self-test fixtures:
# https://github.com/gnutls/gnutls/blob/3.7.9/lib/crypto-selftests-pk.c
# Only key-marker findings in this exact binary qualify; all other patterns fail.
public_test_key_libraries = {
    'usr/lib/x86_64-linux-gnu/libgnutls.so.30.34.3':
        '779b25d20249988bea2c1aa6bbeb218f5ae7ea8a9d30ce4f54ea37372965cc4b',
}
secret_findings = []
findings = []
public_fixtures = []
files = 0
with tarfile.open(fileobj=sys.stdin.buffer, mode='r|*') as archive:
    for entry in archive:
        name = entry.name.lstrip('./')
        path = pathlib.PurePosixPath(name)
        if not entry.isfile():
            continue
        files += 1
        if (name.startswith('models/') or path.suffix.lower() in
                {'.onnx', '.nemo', '.safetensors', '.pt', '.pth', '.ckpt'} or
                entry.size > 128 * 1024 * 1024):
            findings.append({'path': name, 'bytes': entry.size})
        stream = archive.extractfile(entry)
        tail = b''
        digest = hashlib.sha256()
        matched = set()
        while stream is not None:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            window = tail + chunk
            matched.update(i for i, pattern in enumerate(secret_patterns)
                           if re.search(pattern, window))
            tail = window[-2048:]
        if (3 in matched and
                public_test_key_libraries.get(name) == digest.hexdigest()):
            matched.remove(3)
            public_fixtures.append({'path': name, 'sha256': digest.hexdigest(),
                                    'reason': 'verified public GnuTLS self-test keys'})
        if matched:
            secret_findings.append({'path': name, 'reason': 'credential pattern'})
print(json.dumps({'files_checked': files, 'model_weight_findings': findings,
                  'credential_findings': secret_findings,
                  'known_public_test_keys': public_fixtures}, indent=2))
if findings or secret_findings:
    raise SystemExit(1)
