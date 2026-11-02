# Nemotron L37 runtime adaptation

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

This model bundle is versioned separately as models-l37-v1.0.0. Each file must
match the pinned size and SHA256 before inference; do not mix model versions.
