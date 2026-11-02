#!/bin/sh
# Opt-in local image checks; no listening service succeeds, no downloads or host ports.
set -eu
image=${IMAGE:-ghcr.io/marco-taylor/nemotron-unified-rust-wyoming:latest}
test_results_dir=${TEST_RESULTS_DIR:-docs/evidence/phase5}
out="$PWD/$test_results_dir"
mkdir -p "$out"
docker run --rm --network none --read-only "$image" --version > "$out/runtime-version.log" 2>&1
if docker run --rm --network none --read-only "$image" serve > "$out/missing-model.log" 2>&1; then
  printf '%s\n' 'Missing-model start unexpectedly succeeded'; exit 1
else
  test "$?" = 2
fi
if docker run --rm --network none --read-only -e THREADS=3 "$image" serve > "$out/invalid-config.log" 2>&1; then
  printf '%s\n' 'Invalid configuration unexpectedly accepted'; exit 1
else
  test "$?" = 2
fi
docker run --rm --network none --read-only \
  -v "$PWD/models/L37-runtime:/models:ro" "$image" check-model > "$out/model-preflight.json" 2>&1
# Deliberately invalid decoder exists only in this disposable container's tmpfs.
if docker run --rm --network none --read-only --memory 4g --cpus 2 \
  --tmpfs /tmp:size=16m,noexec,nosuid,nodev \
  -v "$PWD/models/L37-runtime:/models:ro" --entrypoint /bin/sh "$image" -c '
    mkdir /tmp/invalid &&
    ln -s /models/encoder.int8.onnx /tmp/invalid/encoder.int8.onnx &&
    ln -s /models/joiner.onnx /tmp/invalid/joiner.onnx &&
    ln -s /models/tokens.txt /tmp/invalid/tokens.txt &&
    printf "invalid ONNX\n" > /tmp/invalid/decoder.onnx &&
    exec /usr/local/bin/docker-entrypoint.sh serve --model /tmp/invalid
  ' > "$out/incompatible-model.log" 2>&1; then
  printf '%s\n' 'Invalid decoder unexpectedly loaded'; exit 1
else
  test "$?" = 2
fi
docker run --rm --network none --read-only --user 99:100 --entrypoint /bin/sh "$image" -c '
  id
  if command -v python3; then exit 1; fi
  if command -v cargo; then exit 1; fi
  ldd /usr/local/bin/nemotron-wyoming
  test -s /usr/share/licenses/nemotron-wyoming/rust-dependencies.json
  test -s /usr/share/licenses/nemotron-wyoming/native/onnxruntime-src/ThirdPartyNotices.txt
' > "$out/runtime-environment.log" 2>&1
printf '%s\n' 'Runtime preflight checks passed.'
