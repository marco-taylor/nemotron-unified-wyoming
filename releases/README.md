# Versioned model-release assets

The immutable GitHub release models-l37-v1.0.0 is published. All 14 assets were
verified against local sizes/hashes and downloaded anonymously for verification.
Actual publication and image/CA status: docs/PHASE12_PUBLICATION.md.
releases/models-l37-v1.0.0.plan.json lists the 14 exact individual assets.
The four large runtime sources stay in models/L37-runtime; this directory
contains only release text, notices, checksums and a planned manifest.
The active config/model-manifest.json pins this release's four download URLs.

The tag models-l37-v1.0.0 versions this exact adapted runtime bundle, not a
server v1.0.0 release and not a newly trained NVIDIA model. Do not mark this
model release as the repository's latest application release. This release is
immutable; do not change the published asset files or reuse its tag for other
weights. A future model version needs a new approved tag and a complete review.

Validate locally with scripts/validate_model_release.py in an isolated Python
container; it reads the original weights and never uploads or alters them.
Generate the text assets only into a new, nonexistent target using
scripts/prepare_model_release.py. That generator fetches only small, official,
revision-pinned upstream notices and verifies their recorded Git blob hashes.
It refuses an existing target. The local upstream inventory is ignored evidence;
retain it privately for reproduction rather than fetching an unpinned latest.

Initial review: docs/PHASE11_1_GITHUB_MODEL_RELEASE.md.
