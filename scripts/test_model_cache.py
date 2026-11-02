"""Operate only on a disposable /models test mount, never production weights."""
import hashlib
import json
from pathlib import Path
import sys

root = Path("/models")
entries = json.loads(Path("/usr/local/lib/nemotron/model-manifest.json").read_text())["files"]
mode = sys.argv[1]
if mode == "snapshot":
    records = {}
    for entry in entries:
        path = root / entry["name"]
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        meta = path.stat()
        assert meta.st_size == entry["size"] and digest == entry["sha256"]
        assert meta.st_uid == 99 and meta.st_gid == 100
        records[entry["name"]] = {"inode": meta.st_ino, "mtime_ns": meta.st_mtime_ns,
                                   "bytes": meta.st_size, "sha256": digest,
                                   "uid": meta.st_uid, "gid": meta.st_gid}
    print(json.dumps(records, indent=2))
elif mode == "missing":
    target = root / "tokens.txt"
    backup = root / "tokens.before-missing-test"
    assert target.is_file() and not backup.exists()
    target.rename(backup)
elif mode == "corrupt":
    target = root / "joiner.onnx"
    backup = root / "joiner.before-corruption-test"
    assert target.is_file() and not backup.exists()
    target.rename(backup)
    with backup.open("rb") as source, target.open("xb") as output:
        first = source.read(1)
        output.write(bytes([first[0] ^ 1]))
        while chunk := source.read(1024 * 1024):
            output.write(chunk)
    assert target.stat().st_size == backup.stat().st_size
elif mode == "orphan":
    path = root / ".encoder.int8.onnx.part-abcd1234"
    with path.open("xb") as stream:
        stream.write(b"controlled interrupted-download fixture")
else:
    raise SystemExit("unknown disposable cache operation")
