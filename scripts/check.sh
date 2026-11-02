#!/bin/sh
set -eu
# From project root: all checks and the release build live in isolated Docker stages.
# No server is started, no host port is published, no weights are downloaded.
docker build --progress=plain --target runtime -t nemotron-unified-wyoming:local-check .
docker run --rm --network none nemotron-unified-wyoming:local-check --version
