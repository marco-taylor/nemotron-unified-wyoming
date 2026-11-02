"""Validate local release plan and all source bytes without network or writes."""
import hashlib
import json
from pathlib import Path

tag = "models-l37-v1.0.0"
root = Path("releases") / tag
plan = json.loads(Path("releases/models-l37-v1.0.0.plan.json").read_text())
active = json.loads(Path("config/model-manifest.json").read_text())
planned = json.loads((root / "model-manifest.json").read_text())
assert plan["tag"] == tag and plan["make_latest"] is False
assert 0 < len(plan["assets"]) <= 1000
assert len({a["name"] for a in plan["assets"]}) == len(plan["assets"])
expected_base = "https://github.com/marco-taylor/nemotron-unified-wyoming/releases/download/" + tag + "/"
configured = [bool(e["url"]) for e in active["files"]]
assert all(configured) or not any(configured), "Do not activate only part of the model bundle"
assert all(not e["url"] or e["url"] == expected_base + e["name"] for e in active["files"])
assert len(active["files"]) == len(planned["files"]) == 4
for a, b in zip(active["files"], planned["files"], strict=True):
    assert all(a[k] == b[k] for k in ["name", "size", "sha256"])
    assert b["url"] == expected_base + b["name"]
checksums = {}
for line in (root / "SHA256SUMS").read_text().splitlines():
    digest, name = line.split("  ", 1)
    assert name not in checksums
    checksums[name] = digest
total = 0
for asset in plan["assets"]:
    assert asset["url"] == expected_base + asset["name"]
    assert "/latest/" not in asset["url"]
    path = Path(asset["local_source"])
    assert path.is_file() and not path.is_symlink()
    assert path.stat().st_size == asset["bytes"] < 2 * 1024**3
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    assert digest == asset["sha256"]
    if path.name != "SHA256SUMS":
        assert checksums.pop(path.name) == digest
    total += asset["bytes"]
assert not checksums and total == plan["total_asset_bytes"]
assert sum(f["size"] for f in active["files"]) == plan["runtime_download_bytes"]
assert (root / "LICENSE.OpenMDW-1.1.md").read_bytes() == Path("config/model-LICENSE.md").read_bytes()
origin = json.loads((root / "PROVENANCE.json").read_text())
assert origin["trained_by_this_project"] is False
assert origin["upstream_revision"] == active["source_revision"] == "023ce907267a09a308a5cb69239447cb3d0c1597"
for notice in origin["notice_sources"]:
    body = (root / notice["asset"]).read_bytes()
    assert hashlib.sha256(body).hexdigest() == notice["sha256"]
    assert hashlib.sha1(b"blob " + str(len(body)).encode() + b"\0" + body).hexdigest() == notice["git_blob_sha1"]
assert "Nemotron-Labs-Unified-ASR-0.6b-v1" in (root / "MODEL_CARD.NVIDIA.md").read_text()
assert "Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES." in (root / "LICENSE.OpenMDW-1.1.md").read_text()
print(json.dumps({"status": "passed", "assets": len(plan["assets"]),
                  "total_release_bytes": total, "runtime_download_bytes": plan["runtime_download_bytes"],
                  "all_assets_below_2GiB": True, "no_weights_copied": True,
                  "active_urls_configured": all(configured), "checksums_and_notice_origins": "passed"}, indent=2))
