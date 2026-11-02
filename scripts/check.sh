#!/bin/sh
set -eu
# From project root: all checks and the release build live in isolated Docker stages.
# No server is started, no host port is published, no weights are downloaded.
docker build --progress=plain --target runtime -t ghcr.io/marco-taylor/nemotron-unified-rust-wyoming:latest .
docker run --rm --network none ghcr.io/marco-taylor/nemotron-unified-rust-wyoming:latest --version
