"""Publication gate: fail until every exact L37 artifact has an approved URL."""
import json
from pathlib import Path
from urllib.parse import urlsplit

manifest = json.loads(Path("config/model-manifest.json").read_text())
for entry in manifest["files"]:
    url = urlsplit(entry.get("url") or "")
    if url.scheme != "https" or not url.netloc or url.username or url.password:
        raise SystemExit("PUBLICATION BLOCKED: no approved exact model source for " + entry["name"])
print("Pinned model sources configured; verify remote bytes and licenses before publication")
