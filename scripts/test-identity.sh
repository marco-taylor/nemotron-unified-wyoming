#!/bin/sh
# Creates ONLY disposable identity tests; no host ports, no permission changes on models.
set -eu
image=${IMAGE:-ghcr.io/marco-taylor/nemotron-unified-wyoming:latest}
client_image=${CLIENT_IMAGE:-nemotron-unified-checks:phase5.2}
server="nemotron-unified-puid-test-$$"
override="nemotron-unified-puid-override-$$"
test_results_dir=${TEST_RESULTS_DIR:-docs/evidence/phase5_2}
out="$PWD/$test_results_dir"
mkdir -p "$out"
cleanup() {
    for name in "$server" "$override"; do
        docker stop --time 60 "$name" >/dev/null 2>&1 || true
        docker rm "$name" >/dev/null 2>&1 || true
    done
}
trap cleanup EXIT INT TERM
# Defaults are supplied by the image (not by test environment overrides).
docker run -d --pull never --name "$server" --network none --read-only \
    --cap-drop ALL --cap-add SETUID --cap-add SETGID --security-opt no-new-privileges:true \
    --memory 4g --cpus 2 --pids-limit 128 --stop-timeout 60 \
    --env MAX_AUDIO_SECONDS=2 \
    --mount "type=bind,src=$PWD/models/L37-runtime,dst=/models,readonly" \
    "$image" > "$out/identity-container-id.txt"
i=0
until docker exec "$server" /usr/local/bin/docker-entrypoint.sh healthcheck > "$out/identity-health.log" 2>&1; do
    i=$((i+1)); if [ "$i" -ge 45 ]; then docker logs "$server"; exit 1; fi
    sleep 1
done
docker exec --user 99:100 "$server" awk '/^(Uid|Gid|Groups|CapEff|CapPrm|CapAmb|NoNewPrivs):/' /proc/1/status > "$out/process-identity.txt"
awk '$1=="Uid:" {if($2!=99 || $3!=99 || $4!=99 || $5!=99)exit 1; uid=1}
     $1=="Gid:" {if($2!=100 || $3!=100 || $4!=100 || $5!=100)exit 1; gid=1}
     $1=="CapEff:" || $1=="CapPrm:" || $1=="CapAmb:" {if($2!="0000000000000000")exit 1}
     $1=="NoNewPrivs:" {if($2!=1)exit 1; nnp=1}
     END {if(!uid || !gid || !nnp)exit 1}' "$out/process-identity.txt"
docker run --rm --pull never --network "container:$server" \
    --env PYTHONDONTWRITEBYTECODE=1 --env PYTHONPATH=/work/tests/reference \
    --mount "type=bind,src=$PWD,dst=/work" --workdir /work "$client_image" \
    python3 tests/real_server.py --wav benchmarks/audio/einsteigen-bitte.wav \
    --output "$test_results_dir/real-server.json" > "$out/real-server.log" 2>&1
docker inspect "$server" > "$out/identity-container-inspect.json"
# Environment-only overrides must change the actual server identity from root bootstrap.
docker run -d --pull never --name "$override" --network none --read-only \
    --env PUID=12345 --env PGID=23456 \
    --cap-drop ALL --cap-add SETUID --cap-add SETGID --security-opt no-new-privileges:true --memory 4g --cpus 2 \
    --mount "type=bind,src=$PWD/models/L37-runtime,dst=/models,readonly" \
    "$image" > "$out/override-container-id.txt"
i=0
until docker exec --user 12345:23456 "$override" /usr/local/bin/docker-entrypoint.sh healthcheck > "$out/override-health.log" 2>&1; do
    i=$((i+1)); if [ "$i" -ge 45 ]; then docker logs "$override"; exit 1; fi
    sleep 1
done
docker exec --user 12345:23456 "$override" awk '/^(Uid|Gid|CapEff|NoNewPrivs):/' /proc/1/status > "$out/override-process-identity.txt"
awk '$1=="Uid:" {if($2!=12345 || $3!=12345)exit 1; uid=1}
     $1=="Gid:" {if($2!=23456 || $3!=23456)exit 1; gid=1}
     END {if(!uid || !gid)exit 1}' "$out/override-process-identity.txt"
# Already nonroot with matching IDs works without any capabilities.
docker run --rm --pull never --network none --read-only --user 12345:23456 \
    --env PUID=12345 --env PGID=23456 --cap-drop ALL \
    "$image" --version > "$out/already-nonroot.log" 2>&1
# Invalid IDs fail before model access, never silently default or run as root.
for variable in PUID PGID; do
    for value in 0 -1 invalid '' 099 2147483648; do
        if docker run --rm --pull never --network none --read-only --env "$variable=$value" "$image" --version > "$out/invalid-$variable.log" 2>&1; then
            echo "Invalid $variable accepted"; exit 1
        else
            test "$?" = 2
            grep -q "$variable" "$out/invalid-$variable.log"
        fi
    done
done
if docker run --rm --pull never --network none --user 12345:23456 "$image" --version > "$out/mismatched-user.log" 2>&1; then
    echo 'Mismatched Docker user accepted'; exit 1
else
    test "$?" = 2
fi
# Verify inaccessible model mount fails after drop; fixture exists only in container tmpfs.
if docker run --rm --pull never --network none --read-only --tmpfs /tmp:size=1m \
    --entrypoint /bin/sh "$image" -c 'mkdir -m 700 /tmp/denied && MODEL_DIR=/tmp/denied exec /usr/local/bin/docker-entrypoint.sh serve' > "$out/denied-model.log" 2>&1; then
    echo 'Inaccessible model directory accepted'; exit 1
else
    test "$?" = 2
    grep -q 'Permission denied' "$out/denied-model.log"
fi
docker logs "$server" > "$out/identity-server.log" 2>&1
docker stop --time 60 "$server" > "$out/identity-stop.log"
docker inspect "$server" --format '{{.State.ExitCode}}' > "$out/identity-exit.txt"
test "$(cat "$out/identity-exit.txt")" = 0
docker image inspect "$image" > "$out/image-inspect.json"
printf '%s\n' 'Identity defaults, overrides, no effective capabilities, model access, real STT, invalid IDs and shutdown passed.'
