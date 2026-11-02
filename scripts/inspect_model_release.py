"""Read-only exact bundle audit for a future GitHub model release (no upload)."""
import collections
import hashlib
import json
from pathlib import Path

import onnx
from google.protobuf.message import Message

manifest = json.loads(Path("config/model-manifest.json").read_text())
limit = 2 * 1024**3


def tensors(message):
    if isinstance(message, onnx.TensorProto):
        yield message
    for field, value in message.ListFields():
        if field.message_type is None:
            continue
        if field.is_repeated:
            for child in value:
                if isinstance(child, Message):
                    yield from tensors(child)
        else:
            yield from tensors(value)


records = []
for entry in manifest["files"]:
    path = Path("models/L37-runtime") / entry["name"]
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    size = path.stat().st_size
    assert digest == entry["sha256"] and size == entry["size"], path
    assert size < limit, path
    record = {"path": str(path), "bytes": size, "MiB": size / 1024**2,
              "GiB": size / 1024**3, "sha256": digest, "readable": True,
              "below_github_2GiB_limit": True}
    if path.suffix == ".onnx":
        graph = onnx.load(str(path), load_external_data=False)
        external = [t.name for t in tensors(graph)
                    if t.data_location == onnx.TensorProto.EXTERNAL or t.external_data]
        assert not external, external
        onnx.checker.check_model(str(path))
        record.update(format="ONNX protobuf ModelProto", ir_version=graph.ir_version,
                      opsets=[{"domain": x.domain, "version": x.version} for x in graph.opset_import],
                      producer=graph.producer_name, producer_version=graph.producer_version,
                      inputs=[x.name for x in graph.graph.input], outputs=[x.name for x in graph.graph.output],
                      external_tensors=external, checker="passed",
                      initializers_by_type=dict(collections.Counter(onnx.TensorProto.DataType.Name(x.data_type) for x in graph.graph.initializer)),
                      MatMulInteger_nodes=sum(x.op_type == "MatMulInteger" for x in graph.graph.node),
                      metadata={x.key: x.value for x in graph.metadata_props})
        del graph
    else:
        lines = path.read_text(encoding="utf-8").splitlines()
        ids = [int(line.rsplit(" ", 1)[1]) for line in lines]
        assert len(ids) == len(set(ids)) and min(ids) == 0 and max(ids) == len(ids) - 1
        record.update(format="UTF-8 token table (not ONNX)", token_count=len(lines),
                      external_data=False, checker="UTF-8 and unique contiguous token IDs passed")
    records.append(record)
total = sum(row["bytes"] for row in records)
print(json.dumps({"onnx_version": onnx.__version__, "assets": records,
                  "total_bytes": total, "total_MiB": total / 1024**2,
                  "total_GiB": total / 1024**3, "github_individual_asset_limit_exclusive_bytes": limit}, indent=2))
