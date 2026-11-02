# Host remains unchanged; all compilers/dependencies live in Docker.
FROM rust:1.91-bookworm@sha256:c1e5f19e773b7878c3f7a805dd00a495e747acbdc76fb2337a4ebf0418896b33 AS toolchain
RUN apt-get update && apt-get install -y --no-install-recommends cmake ninja-build python3 time && rm -rf /var/lib/apt/lists/*
WORKDIR /work

FROM toolchain AS checks
RUN rustup component add rustfmt clippy

FROM toolchain AS native
# Exact PR #4141 head, including its stacked streaming fixes. Never use release prebuilts.
ENV SHERPA_COMMIT=31ba0e438f8065189a8e5589d84dfd7faf516d3d
RUN git init /opt/sherpa/src && cd /opt/sherpa/src && git remote add origin https://github.com/k2-fsa/sherpa-onnx.git && git fetch --depth 1 origin "$SHERPA_COMMIT" && git checkout --detach FETCH_HEAD && test "$(git rev-parse HEAD)" = "$SHERPA_COMMIT"
RUN cmake -S /opt/sherpa/src -B /opt/sherpa/build -G Ninja \
    -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON \
    -DSHERPA_ONNX_ENABLE_PORTAUDIO=OFF -DSHERPA_ONNX_ENABLE_WEBSOCKET=OFF \
    -DSHERPA_ONNX_ENABLE_TTS=OFF -DSHERPA_ONNX_ENABLE_SPEAKER_DIARIZATION=OFF \
    -DSHERPA_ONNX_ENABLE_BINARY=OFF -DSHERPA_ONNX_BUILD_C_API_EXAMPLES=OFF \
    -DSHERPA_ONNX_ENABLE_PYTHON=OFF -DSHERPA_ONNX_ENABLE_TESTS=OFF \
    && cmake --build /opt/sherpa/build --target sherpa-onnx-c-api -j 2 \
    && mkdir -p /opt/sherpa/lib \
    && find /opt/sherpa/build -name '*.so*' -exec cp -a -t /opt/sherpa/lib {} + \
    && printf '%s\n' "$SHERPA_COMMIT" > /opt/sherpa/lib/SOURCE_COMMIT
ENV SHERPA_ONNX_LIB_DIR=/opt/sherpa/lib
ENV LD_LIBRARY_PATH=/opt/sherpa/lib

FROM native AS stamped
COPY scripts/stamp_native_version.py /tmp/stamp_native_version.py
RUN python3 /tmp/stamp_native_version.py \
    && cmake --build /opt/sherpa/build --target sherpa-onnx-c-api -j 2 \
    && cp -a /opt/sherpa/build/lib/libsherpa-onnx-c-api.so /opt/sherpa/lib/

FROM stamped AS development
RUN rustup component add rustfmt clippy

FROM development AS build
ENV CARGO_NET_GIT_FETCH_WITH_CLI=true
COPY Cargo.toml Cargo.lock ./
COPY src ./src
COPY tests ./tests
COPY config/variables.json ./config/variables.json
COPY LICENSE THIRD_PARTY_NOTICES.md ./
COPY scripts/collect_licenses.py ./scripts/collect_licenses.py
RUN cargo build --locked --release --features sherpa
RUN cargo fmt --check && cargo test --locked --features sherpa && cargo clippy --locked --all-targets --features sherpa -- -D warnings
COPY scripts/model-init.py ./scripts/model-init.py
COPY tests/model_init_test.py ./tests/model_init_test.py
RUN python3 -m unittest discover -s tests -p model_init_test.py -v

RUN python3 scripts/collect_licenses.py

FROM debian:bookworm-slim@sha256:99c0b25c46d0214d5a2091092e7908907dcaecd6a962cde0ac700acee222b6f3 AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 libgomp1 ca-certificates python3 libseccomp2 && rm -rf /var/lib/apt/lists/*
COPY --from=build /opt/sherpa/lib /opt/sherpa/lib
COPY --from=build /work/runtime-licenses /usr/share/licenses/nemotron-wyoming
COPY --from=build /work/target/release/nemotron-unified-wyoming /usr/local/bin/nemotron-wyoming
ENV LD_LIBRARY_PATH=/opt/sherpa/lib
LABEL org.opencontainers.image.source="https://github.com/marco-taylor/nemotron-unified-wyoming" \
      net.unraid.docker.icon="https://raw.githubusercontent.com/marco-taylor/nemotron-unified-wyoming/main/assets/icons/nemotron-lowq.png" \
      org.opencontainers.image.title="Nemotron Unified Wyoming" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="MIT"
ENV MODEL_DIR=/models LANGUAGE=de THREADS=2 WYOMING_HOST=0.0.0.0 WYOMING_PORT=10300
COPY --chmod=755 scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
COPY scripts/model-init.py config/model-manifest.json config/model-LICENSE.md /usr/local/lib/nemotron/
RUN mkdir -p /models && command -v setpriv
ENV PUID=99 PGID=100
# Root only for the UID/GID bootstrap; the server execs as PUID:PGID.
USER 0:0
EXPOSE 10300
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=30s --timeout=5s --start-period=35m --retries=3 CMD ["/usr/local/bin/docker-entrypoint.sh", "healthcheck"]
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["serve"]
