#!/bin/sh
set -eu
# Preparation example. Requires approved model files and real corpus first.
# Run manually from the project root. Development container only, no ports.
: "${MODEL_DIR:?Set MODEL_DIR to the approved L37 directory}"
: "${CORPUS_DIR:?Set CORPUS_DIR to the directory containing manifest.jsonl}"
docker run --rm --network none --cpus 4 --memory 8g \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$PWD:/work" -v "$MODEL_DIR:/models:ro" -v "$CORPUS_DIR:/corpus:ro" \
  -w /work nemotron-unified-development:pr4141 \
  python3 scripts/benchmark.py --model /models --manifest /corpus/manifest.jsonl \
  --output /work/benchmarks/results/n100-l37-run.jsonl --repeats 3
