# Local model-release preparation

No GitHub tag, draft, release or asset has been created or uploaded.
releases/models-l37-v1.0.0.plan.json lists 14 proposed individual assets.
The four large runtime sources stay in models/L37-runtime; this directory
contains only release text, notices, checksums and a planned manifest.
The active config/model-manifest.json still has no download URLs.

The tag models-l37-v1.0.0 versions this exact adapted runtime bundle, not a
server v1.0.0 release and not a newly trained NVIDIA model. Do not mark this
model release as the repository's latest application release. Prefer immutable
releases: only after approval, enable the feature, attach all verified assets
to a draft and then publish. Nothing in this directory performs those actions.

Validate locally with scripts/validate_model_release.py in an isolated Python
container; it reads the original weights and never uploads or alters them.
Generate the text assets only into a new, nonexistent target using
scripts/prepare_model_release.py. That generator fetches only small, official,
revision-pinned upstream notices and verifies their recorded Git blob hashes.
It refuses an existing target. The local upstream inventory is ignored evidence;
retain it privately for reproduction rather than fetching an unpinned latest.

Review and next steps: docs/PHASE11_1_GITHUB_MODEL_RELEASE.md.
