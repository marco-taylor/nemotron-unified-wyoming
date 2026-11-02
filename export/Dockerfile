# No package-network operations: approved wheels/source are installed in the project venv.
# New CPython supplies NeMo's required secure tar extraction API.
FROM python:3.11.14-slim-bookworm@sha256:83f339c1be6340ae1096010fdccf6552ac932d8f410d45d206014916bdf37e48 AS python
FROM nemotron-unified-development:pr4141
COPY --from=python /usr/local /usr/local
RUN ldconfig && /usr/local/bin/python3.11 -c 'import sys,tarfile; assert sys.version_info >= (3,11,8); assert hasattr(tarfile,"data_filter"); print(sys.version)'
ENV PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin
ENV LD_LIBRARY_PATH=/usr/local/lib:/opt/sherpa/lib
ENV PYTHONPATH=/work/export/venv/lib/python3.11/site-packages
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1
WORKDIR /work
