#!/bin/sh
# Full real first install/repair test; only own containers and a new empty cache.
set -eu
image=${IMAGE:-nemotron-unified-wyoming:phase12-test}
client_image=${CLIENT_IMAGE:-ghcr.io/esphome/esphome:stable}
out="$PWD/${TEST_RESULTS_DIR:-docs/evidence/phase12/first-install}"
mkdir -p "$out"
cache=$(mktemp -d "$out/cache.XXXXXXXX")
chown 99:100 "$cache" # Only this just-created EMPTY test directory.
chmod 755 "$cache"
printf '%s\n' "$cache" > "$out/cache-path.txt"
server="nemotron-phase12-first-install-$$"
cleanup() {
 docker logs "$server" > "$out/server-final.log" 2>&1 || true
 docker stop --time 60 "$server" >/dev/null 2>&1 || true
 docker rm "$server" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM
cache_op() {
 docker run --rm --pull never --network none --read-only --user 99:100 \
  --cap-drop ALL --security-opt no-new-privileges:true \
  --mount "type=bind,src=$cache,dst=/models" \
  --mount "type=bind,src=$PWD/scripts/test_model_cache.py,dst=/test-cache.py,readonly" \
  --entrypoint python3 "$image" /test-cache.py "$1"
}
ready() {
 i=0
 until [ "$(docker inspect "$server" --format '{{.State.Health.Status}}')" = healthy ]; do
  if [ "$(docker inspect "$server" --format '{{.State.Running}}')" != true ]; then docker logs "$server"; return 1; fi
  i=$((i+1)); if [ "$i" -ge 1050 ]; then docker logs "$server"; return 1; fi
  sleep 2
 done
 docker exec "$server" /usr/local/bin/docker-entrypoint.sh healthcheck
}
asr() {
 docker run --rm --pull never --read-only --network "container:$server" \
  --cap-drop ALL --security-opt no-new-privileges:true --env PYTHONDONTWRITEBYTECODE=1 \
  --env PYTHONPATH=/project/tests/reference --mount "type=bind,src=$PWD,dst=/project,readonly" \
  --mount "type=bind,src=$out,dst=/out" --entrypoint python3 "$client_image" \
  /project/tests/unraid_minimal.py --port 10300 --output "/out/transcripts-$1.json"
}
downloads() {
 docker logs "$server" > "$out/log-$1.txt" 2>&1
 count=$(grep -c '^model-init: downloading ' "$out/log-$1.txt" || true)
 test "$count" = "$2"
}
test -z "$(ls -A "$cache")"
docker run -d --pull never --name "$server" --network bridge --read-only \
 --publish 127.0.0.1::10300 --cap-drop ALL --cap-add SETUID --cap-add SETGID \
 --security-opt no-new-privileges:true --memory 4g --cpus 4 --pids-limit 128 \
 --stop-timeout 60 --tmpfs /tmp:size=16m,noexec,nosuid,nodev \
 --mount "type=bind,src=$cache,dst=/models" "$image" > "$out/container-id.txt"
ready
docker exec --user 99:100 "$server" awk '/^(Uid|Gid|CapEff|CapPrm|CapAmb|NoNewPrivs|Seccomp|Seccomp_filters):/' /proc/1/status > "$out/security.txt"
awk '$1=="Uid:" {if($2!=99 || $3!=99)exit 1;uid=1}
 $1=="Gid:" {if($2!=100 || $3!=100)exit 1;gid=1}
 $1=="CapEff:" || $1=="CapPrm:" || $1=="CapAmb:" {if($2!="0000000000000000")exit 1}
 $1=="NoNewPrivs:" {if($2!=1)exit 1;nnp=1}
 $1=="Seccomp_filters:" {if($2<2)exit 1;filter=1}
 END {if(!uid||!gid||!nnp||!filter)exit 1}' "$out/security.txt"
docker inspect "$server" > "$out/healthy-first.json"
asr first
cache_op snapshot > "$out/snapshot-first.json"
downloads first 4
docker restart --time 60 "$server" >/dev/null
ready
asr restart
cache_op snapshot > "$out/snapshot-restart.json"
cmp "$out/snapshot-first.json" "$out/snapshot-restart.json"
downloads restart 4
docker stop --time 60 "$server" >/dev/null
cache_op missing
docker start "$server" >/dev/null
ready
cache_op snapshot > "$out/snapshot-missing.json"
downloads missing 5
docker stop --time 60 "$server" >/dev/null
cache_op corrupt
docker start "$server" >/dev/null
ready
cache_op snapshot > "$out/snapshot-repaired.json"
downloads repaired 6
docker stop --time 60 "$server" >/dev/null
cache_op orphan
docker start "$server" >/dev/null
ready
test ! -e "$cache/.encoder.int8.onnx.part-abcd1234"
cache_op snapshot > "$out/snapshot-orphan.json"
cmp "$out/snapshot-repaired.json" "$out/snapshot-orphan.json"
downloads orphan 6
test "$(grep -c '^model-init: downloading encoder.int8.onnx$' "$out/log-orphan.txt")" = 1
test "$(grep -c '^model-init: downloading decoder.onnx$' "$out/log-orphan.txt")" = 1
test "$(grep -c '^model-init: downloading joiner.onnx$' "$out/log-orphan.txt")" = 2
test "$(grep -c '^model-init: downloading tokens.txt$' "$out/log-orphan.txt")" = 2
php -r '$d=$argv[1];$first=json_decode(file_get_contents($d."/snapshot-first.json"),true);$missing=json_decode(file_get_contents($d."/snapshot-missing.json"),true);$fixed=json_decode(file_get_contents($d."/snapshot-repaired.json"),true);foreach($first as $name=>$row)if($name!=="tokens.txt"&&$row!==$missing[$name])exit(1);foreach($missing as $name=>$row)if($name!=="joiner.onnx"&&$row!==$fixed[$name])exit(2);echo "Only requested missing/corrupt files replaced; other inodes, mtimes and hashes unchanged\n";' "$out" > "$out/selective-repair-check.log"
asr repaired
docker inspect "$server" > "$out/healthy-final.json"
docker stop --time 60 "$server" >/dev/null
test "$(docker inspect "$server" --format '{{.State.ExitCode}}')" = 0
printf '%s\n' 'PASS: empty GitHub install, 99:100, health, German ASR, restart reuse, targeted missing/corrupt repair, orphan cleanup; original test files retained.'
