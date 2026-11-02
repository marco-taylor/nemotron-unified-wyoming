#!/bin/sh
set -eu
# Run from project root, after verified offline dependency installation.
# Dedicated short-lived job, no network, no ports, no GPU.
docker run --rm --name nemotron-unified-export-phase4 --network none \
  --cpus 2 --memory 12g --memory-swap 12g \
  -e PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  -e PYTHONPATH=/work/export/venv/lib/python3.11/site-packages \
  -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 -e CUDA_VISIBLE_DEVICES= \
  -e OMP_NUM_THREADS=2 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=2 \
  -v "$PWD:/work" -v "$PWD/export:/opt/export" -w /work \
  nemotron-unified-export:phase4 \
  /usr/bin/time -v /usr/local/bin/python3.11 scripts/export_l37.py \
  --model /work/models/source/nemotron-labs-unified-asr-0.6b.nemo \
  --output "${OUTPUT_DIR:-/work/models/L37}"
