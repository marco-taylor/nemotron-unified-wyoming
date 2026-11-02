#!/bin/sh
# Own disposable bridge container, loopback-only random host port; models read-only.
set -eu
image=${IMAGE:-ghcr.io/marco-taylor/nemotron-unified-wyoming:latest}
client_image=${CLIENT_IMAGE:-ghcr.io/esphome/esphome:stable}
out="$PWD/${TEST_RESULTS_DIR:-docs/evidence/phase10/minimal}"
server="nemotron-phase10-minimal-$$"
mkdir -p "$out"
port_internal=10300
expected_uid=99
expected_gid=100
max_chunk=320000
chunk_ms=20
case "${TEST_MODE:-minimal}" in
 minimal) set -- ;;
 template) set -- --env THREADS=2 --env MAX_AUDIO_SECONDS=120 --env MAX_CONNECTIONS=8 \
  --env CLIENT_TIMEOUT_SECONDS=30 --env LOG_LEVEL=info --env LOG_TRANSCRIPTS=false \
  --env PUID=99 --env PGID=100 ;;
 legacy)
  port_internal=10444; expected_uid=12345; expected_gid=23456; max_chunk=128000; chunk_ms=160
  set -- --env PUID=12345 --env PGID=23456 --env THREADS=1 \
   --env WYOMING_HOST=0.0.0.0 --env WYOMING_PORT=10444 --env LANGUAGE=de --env STT_DEVICE=cpu \
   --env MODEL_DIR=/intentionally-unused --env ENCODER_PATH=/models/encoder.int8.onnx \
   --env DECODER_PATH=/models/decoder.onnx --env JOINER_PATH=/models/joiner.onnx --env TOKENS_PATH=/models/tokens.txt \
   --env MAX_AUDIO_SECONDS=2 --env MAX_AUDIO_CHUNK_BYTES=128000 --env INFERENCE_CHUNK_MS=80 \
   --env MAX_CONNECTIONS=4 --env CLIENT_TIMEOUT_SECONDS=5 --env LOG_LEVEL=debug --env LOG_TRANSCRIPTS=true ;;
 *) echo 'Unknown TEST_MODE' >&2; exit 2 ;;
esac
cleanup() {
 docker logs "$server" > "$out/server.log" 2>&1 || true
 docker stop --time 60 "$server" >/dev/null 2>&1 || true
 docker inspect "$server" > "$out/after-stop.json" 2>/dev/null || true
 docker rm "$server" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM
# Minimal omits all settings; template supplies its eight defaults; legacy supplies all 19.
docker run -d --pull never --name "$server" --network bridge --read-only \
 --publish "127.0.0.1::$port_internal" --cap-drop ALL --cap-add SETUID --cap-add SETGID \
 --security-opt no-new-privileges:true --memory 4g --cpus 4 --pids-limit 128 --stop-timeout 60 \
 --tmpfs /tmp:size=16m,noexec,nosuid,nodev \
 --mount "type=bind,src=$PWD/models/L37-runtime,dst=/models,readonly" \
 "$@" "$image" > "$out/id.txt"
tries=0
until docker exec "$server" /usr/local/bin/docker-entrypoint.sh healthcheck > "$out/health.log" 2>&1; do
 tries=$((tries+1)); if [ "$tries" -ge 60 ]; then exit 1; fi
 sleep 1
done
docker exec --user "$expected_uid:$expected_gid" "$server" awk '/^(Uid|Gid|CapEff|CapPrm|CapAmb|NoNewPrivs):/' /proc/1/status > "$out/security.txt"
awk -v expected_uid="$expected_uid" -v expected_gid="$expected_gid" '$1=="Uid:" {if($2!=expected_uid || $3!=expected_uid)exit 1;uid=1}
 $1=="Gid:" {if($2!=expected_gid || $3!=expected_gid)exit 1;gid=1}
 $1=="CapEff:" || $1=="CapPrm:" || $1=="CapAmb:" {if($2!="0000000000000000")exit 1}
 $1=="NoNewPrivs:" {if($2!=1)exit 1;nnp=1}
 END {if(!uid||!gid||!nnp)exit 1}' "$out/security.txt"
docker inspect "$server" > "$out/inspect.json"
docker port "$server" "$port_internal/tcp" > "$out/published-port.txt"
port=$(docker inspect "$server" --format "{{(index (index .NetworkSettings.Ports \"$port_internal/tcp\") 0).HostPort}}")
php -r '$s=fsockopen("127.0.0.1",(int)$argv[1],$errno,$error,5); if(!$s)exit(1);fwrite($s,"{\"type\":\"describe\"}\n");$h=json_decode(fgets($s),true);if(($h["type"]??"")!=="info")exit(2);fclose($s);echo "Host-loopback mapping reaches Wyoming info\n";' "$port" > "$out/host-port-check.log"
docker run --rm --pull never --read-only --network "container:$server" \
 --cap-drop ALL --security-opt no-new-privileges:true --env PYTHONDONTWRITEBYTECODE=1 \
 --env PYTHONPATH=/project/tests/reference --mount "type=bind,src=$PWD,dst=/project,readonly" \
 --mount "type=bind,src=$out,dst=/out" --entrypoint python3 "$client_image" \
 /project/tests/unraid_minimal.py --port "$port_internal" --chunk-ms "$chunk_ms" --max-audio-chunk-bytes "$max_chunk" --output /out/transcripts.json
# Check readiness again after protocol errors; no installed container is probed/changed.
docker exec "$server" /usr/local/bin/docker-entrypoint.sh healthcheck >> "$out/health.log" 2>&1
tries=0
until [ "$(docker inspect "$server" --format '{{.State.Health.Status}}')" = healthy ]; do
 tries=$((tries+1)); if [ "$tries" -ge 40 ]; then exit 1; fi
 sleep 1
done
docker inspect "$server" > "$out/healthy-inspect.json"
docker stop --time 60 "$server" >/dev/null
test "$(docker inspect "$server" --format '{{.State.ExitCode}}')" = 0
printf '%s\n' 'Selected configuration, host mapping, identity, real inference, healthcheck and shutdown passed.'
