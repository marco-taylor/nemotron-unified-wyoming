"""Anonymous streaming verification of approved versioned release assets.

No authentication, no remote trust manifests, no model-file writes or uploads.
Run only after publication approval. Reads the locally reviewed asset plan.
"""
import hashlib
import json
from pathlib import Path
import runpy
import sys
import time
from urllib.parse import urlsplit

plan = json.loads(Path("releases/models-l37-v1.0.0.plan.json").read_text())
receive = runpy.run_path("scripts/model-init.py", run_name="verification")["receive"]
base = "https://github.com/marco-taylor/nemotron-unified-wyoming/releases/download/models-l37-v1.0.0/"
verified = []
for entry in plan["assets"]:
    assert entry["url"] == base + entry["name"]
    print("Verifying anonymously: " + entry["name"], file=sys.stderr, flush=True)
    digest = hashlib.sha256()
    total = 0
    deadline = time.monotonic() + 1800
    with receive(entry["url"]) as response:
        assert response.status == 200
        host = urlsplit(response.geturl()).hostname
        while True:
            chunk = response.read(min(1024 * 1024, entry["bytes"] - total + 1))
            if not chunk:
                break
            total += len(chunk)
            if total > entry["bytes"] or time.monotonic() > deadline:
                raise RuntimeError("asset size/deadline exceeded: " + entry["name"])
            digest.update(chunk)
    assert total == entry["bytes"] and digest.hexdigest() == entry["sha256"], entry["name"]
    verified.append({"name": entry["name"], "bytes": total, "sha256": digest.hexdigest(),
                     "anonymous": True, "final_host": host})
    print("Verified: " + entry["name"], file=sys.stderr, flush=True)
print(json.dumps({"status": "passed", "tag": plan["tag"], "assets": verified,
                  "total_bytes": sum(row["bytes"] for row in verified)}, indent=2))
