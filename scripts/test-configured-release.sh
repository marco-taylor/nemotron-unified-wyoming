#!/bin/sh
# Opt-in, isolated real model test. Creates only its own disposable containers, no host ports.
set -eu
image=${IMAGE:-ghcr.io/marco-taylor/nemotron-unified-rust-wyoming:latest}
client_image=${CLIENT_IMAGE:-nemotron-unified-checks:phase5.2}
server="nemotron-unified-phase51-test-$$"
client="nemotron-unified-phase51-signal-client-$$"
test_results_dir=${TEST_RESULTS_DIR:-docs/evidence/phase5_1}
out="$PWD/$test_results_dir"
mkdir -p "$out"
cleanup() {
  docker stop --time 60 "$server" >/dev/null 2>&1 || true
  docker rm "$server" >/dev/null 2>&1 || true
  docker rm "$client" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM
# Fail rather than silently obtain an unknown large client image.
docker image inspect "$client_image" >/dev/null
# Read-only root/model mounts, no network outside the shared test namespace.
docker run -d --name "$server" --network none --read-only --cap-drop ALL --cap-add SETUID --cap-add SETGID \
  --security-opt no-new-privileges:true --memory 4g --cpus 4 --pids-limit 128 \
  --tmpfs /tmp:size=16m,noexec,nosuid,nodev --stop-timeout 60 \
  -e THREADS=1 -e MAX_AUDIO_SECONDS=2 -e WYOMING_HOST=127.0.0.1 -e WYOMING_PORT=10444 \
  -e MODEL_DIR=/intentionally-unused -e ENCODER_PATH=/models/encoder.int8.onnx \
  -e DECODER_PATH=/models/decoder.onnx -e JOINER_PATH=/models/joiner.onnx -e TOKENS_PATH=/models/tokens.txt \
  -e INFERENCE_CHUNK_MS=80 -e MAX_AUDIO_CHUNK_BYTES=128000 -e LOG_LEVEL=debug -e LOG_TRANSCRIPTS=true \
  -v "$PWD/models/L37-runtime:/models:ro" "$image" > "$out/test-container-id.txt"
# Startup probe is bounded; backend errors are retained by cleanup logs below on success.
i=0
until docker exec "$server" /usr/local/bin/docker-entrypoint.sh healthcheck > "$out/healthcheck.log" 2>&1; do
  i=$((i+1))
  if [ "$i" -ge 45 ]; then docker logs "$server" > "$out/server.log" 2>&1; exit 1; fi
  sleep 1
done
docker run --rm --network "container:$server" \
  -e PYTHONPATH=/work/tests/reference -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$PWD:/work" -w /work "$client_image" \
  python3 tests/real_server.py --port 10444 --chunk-ms 160 --max-chunk-bytes 128000 --wav benchmarks/audio/einsteigen-bitte.wav \
  --output "$test_results_dir/real-server.json" > "$out/real-server.log" 2>&1
docker exec "$server" /usr/local/bin/docker-entrypoint.sh healthcheck >> "$out/healthcheck.log" 2>&1
docker stats --no-stream --format '{{json .}}' "$server" > "$out/docker-stats.json"
docker inspect "$server" > "$out/test-container-inspect.json"
ready="$test_results_dir/signal-ready-$$"
docker run -d --name "$client" --network "container:$server" \
  -e PYTHONPATH=/work/tests/reference -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$PWD:/work" -w /work "$client_image" \
  python3 tests/signal_client.py "$ready" "$test_results_dir/signal-client.json" 10444 > "$out/signal-client-id.txt"
i=0
until [ -f "$ready" ]; do
  i=$((i+1))
  if [ "$i" -ge 30 ]; then docker logs "$client" > "$out/signal-client.log" 2>&1; exit 1; fi
  sleep 1
done
docker kill --signal TERM "$server" > "$out/signal-command.log"
docker wait "$server" > "$out/server-exit-code.txt"
docker wait "$client" > "$out/signal-client-exit-code.txt"
docker logs "$server" > "$out/server.log" 2>&1
docker logs "$client" > "$out/signal-client.log" 2>&1
docker inspect "$server" > "$out/test-container-after-stop.json"
test "$(cat "$out/server-exit-code.txt")" = 0
test "$(cat "$out/signal-client-exit-code.txt")" = 0
docker image inspect "$image" > "$out/image-inspect.json"
rg -q 'transcript:.*Einsteigen bitte' "$out/server.log"
rg -q 'debug: client' "$out/server.log"
printf '%s\n' 'Real release-image protocol/inference/shutdown checks passed.'
