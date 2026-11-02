"""Prepare only text assets for models-l37-v1.0.0; never upload/copy model weights.

Run in an isolated Python container. Existing output directories are refused.
Online reads are restricted to small official, revision-pinned NVIDIA notices.
The active runtime manifest and publication gate deliberately remain unchanged.
"""
import hashlib
import json
from pathlib import Path
import urllib.request

TAG = "models-l37-v1.0.0"
REVISION = "023ce907267a09a308a5cb69239447cb3d0c1597"
UPSTREAM = "nvidia/nemotron-labs-unified-asr-0.6b"
BASE = "https://github.com/marco-taylor/nemotron-unified-wyoming/releases/download/" + TAG
directory = Path("releases") / TAG
manifest = json.loads(Path("config/model-manifest.json").read_text())
assert manifest["source_revision"] == REVISION

notices = {"LICENSE.md": "LICENSE.OpenMDW-1.1.md", "README.md": "MODEL_CARD.NVIDIA.md",
           "bias.md": "bias.md", "explainability.md": "explainability.md",
           "privacy.md": "privacy.md", "safety.md": "safety.md"}
# Pin to Git blob IDs from the locally recorded official upstream inventory.
upstream = json.loads(Path("docs/evidence/hf-model-metadata.json").read_text())
assert upstream["sha"] == REVISION
inventory = {row["rfilename"]: row for row in upstream["siblings"]}
directory.mkdir(parents=True, exist_ok=False)
origins = []
for source, target in notices.items():
    url = f"https://huggingface.co/{UPSTREAM}/resolve/{REVISION}/{source}"
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read(1024 * 1024 + 1)
    assert len(data) <= 1024 * 1024 and len(data) == inventory[source]["size"]
    blob = b"blob " + str(len(data)).encode() + b"\0" + data
    assert hashlib.sha1(blob).hexdigest() == inventory[source]["blobId"], source
    if source == "LICENSE.md":
        assert data == Path("config/model-LICENSE.md").read_bytes()
    (directory / target).write_bytes(data)
    origins.append({"asset": target, "upstream_path": source, "url": url,
                    "git_blob_sha1": inventory[source]["blobId"],
                    "sha256": hashlib.sha256(data).hexdigest()})

planned = json.loads(json.dumps(manifest))
planned["public_source_status"] = "PLANNED ONLY: release absent; not activated or publicly tested"
for entry in planned["files"]:
    entry["url"] = BASE + "/" + entry["name"]
(directory / "model-manifest.json").write_text(json.dumps(planned, indent=2) + "\n")
provenance = {
    "release_tag_planned": TAG, "release_state": "local preparation only; no public release",
    "model_trained_by": "NVIDIA", "trained_by_this_project": False,
    "upstream_model": UPSTREAM, "upstream_revision": REVISION,
    "upstream_checkpoint": "nemotron-labs-unified-asr-0.6b.nemo",
    "upstream_checkpoint_sha256": manifest["source_checkpoint_sha256"],
    "upstream_checkpoint_bytes": 2507735040,
    "model_license": "OpenMDW-1.1",
    "copyright": "Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.",
    "adaptation": "ONNX export, L37 context, partial encoder QUInt8 quantization; no training or fine-tuning by this project",
    "exporter": "k2-fsa/sherpa-onnx scripts/nemo/nemotron-labs-unified-asr-0.6b/export_onnx.py",
    "exporter_revision": manifest["sherpa_revision"], "exporter_license": "Apache-2.0 (tool, not replacement model license)",
    "context": manifest["export_context"], "quantization": manifest["quantization"],
    "local_export_record": "docs/PHASE4_RESULTS.md and export/reports/final-bundle-audit.json",
    "notice_sources": origins,
    "runtime_files": [{**row, "local_source": "models/L37-runtime/" + row["name"]} for row in planned["files"]],
}
(directory / "PROVENANCE.json").write_text(json.dumps(provenance, indent=2) + "\n")
(directory / "EXPORT_INFO.md").write_text("""# Nemotron L37 runtime adaptation

NVIDIA trained the original Nemotron Labs Unified ASR 0.6B model. This project
did not train or fine-tune a model. It exported the existing checkpoint to ONNX
for the pinned sherpa-onnx backend and quantized parts of the encoder to QUInt8.
Decoder/predictor and joiner remain FP32. L37 uses left=37, center=7, right=7.
The original model and these adapted weights remain subject to OpenMDW-1.1;
the server code's MIT license does not relicense the weights or tokenizer.
No NVIDIA sponsorship, endorsement or trademark license is claimed.

See PROVENANCE.json for exact upstream revision, checkpoint hash, exporter
revision, adaptation and runtime hashes. The upstream model card and notices
are unmodified; relative image links in that card refer to the upstream model
repository. Bias, privacy, safety and explainability documents are retained
as upstream context, not as a new project's safety certification.

Only the four runtime files are required by the server; tokens.txt is UTF-8
text, not an ONNX graph. The three ONNX files are self-contained, without
external tensor files (verified locally). No .nemo checkpoint, training data,
test recordings, development environment or export cache is part of this release.

This directory is local preparation. No assets have been uploaded. All planned
URLs require separate publication approval and anonymous hash verification.
""")
assets = [{"name": row["name"], "local_source": "models/L37-runtime/" + row["name"],
           "bytes": row["size"], "sha256": row["sha256"], "url": row["url"]}
          for row in planned["files"]]
for path in sorted(directory.iterdir()):
    body = path.read_bytes()
    assets.append({"name": path.name, "local_source": str(path), "bytes": len(body),
                   "sha256": hashlib.sha256(body).hexdigest(), "url": BASE + "/" + path.name})
(directory / "SHA256SUMS").write_text("".join(row["sha256"] + "  " + row["name"] + "\n" for row in assets))
path = directory / "SHA256SUMS"
assets.append({"name": path.name, "local_source": str(path), "bytes": path.stat().st_size,
               "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "url": BASE + "/SHA256SUMS"})
assert len({row["name"] for row in assets}) == len(assets) <= 1000
assert all(row["bytes"] < 2 * 1024**3 for row in assets)
plan = {"state": "local only; no Git tag or release created", "tag": TAG,
        "repository": "marco-taylor/nemotron-unified-wyoming", "make_latest": False,
        "immutable_release_recommended": True, "assets": assets,
        "total_asset_bytes": sum(row["bytes"] for row in assets),
        "runtime_download_bytes": sum(row["size"] for row in planned["files"])}
# Kept outside asset directory: a plan is not a new runtime trust anchor.
Path("releases/models-l37-v1.0.0.plan.json").write_text(json.dumps(plan, indent=2) + "\n")
print(json.dumps({"metadata_directory": str(directory), "asset_count": len(assets),
                  "total_asset_bytes": plan["total_asset_bytes"],
                  "weights_copied_or_uploaded": False}, indent=2))
