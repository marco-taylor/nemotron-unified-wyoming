"""Small deterministic transport fixtures; never presented as real model downloads."""
import contextlib
import hashlib
import importlib.util
import io
import fcntl
import http.server
import json
import multiprocessing
import os
from pathlib import Path
import signal
import ssl
import subprocess
import sys
import tempfile
import time
import threading
import urllib.request
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("model_init", Path(__file__).resolve().parents[1] / "scripts/model-init.py")
init = importlib.util.module_from_spec(spec)
spec.loader.exec_module(init)
PAYLOADS = [b"encoder-fixture", b"decoder-fixture", b"joiner-fixture", b"tokens-fixture"]
ENTRIES = [{"name": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest(), "url": "https://fixture.invalid/" + name}
           for name, data in zip(["encoder.int8.onnx", "decoder.onnx", "joiner.onnx", "tokens.txt"], PAYLOADS)]


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.calls = []

    def tearDown(self):
        self.temporary.cleanup()

    def source(self, url):
        name = url.rsplit("/", 1)[1]
        self.calls.append(name)
        return io.BytesIO(PAYLOADS[[e["name"] for e in ENTRIES].index(name)])

    def ensure(self, **kwargs):
        init.ensure_models(self.root, ENTRIES, opener=kwargs.get("opener", self.source))

    def test_empty_then_restart_no_download(self):
        self.ensure()
        self.assertEqual(len(self.calls), 4)
        inodes = [p.stat().st_ino for p in [self.root / e["name"] for e in ENTRIES]]
        self.calls.clear()
        self.ensure()
        self.assertEqual(self.calls, [])
        self.assertEqual(inodes, [(self.root / e["name"]).stat().st_ino for e in ENTRIES])

    def test_single_missing_file(self):
        self.ensure()
        (self.root / "joiner.onnx").unlink()
        self.calls.clear()
        self.ensure()
        self.assertEqual(self.calls, ["joiner.onnx"])

    def test_corrupt_same_size_is_preserved_and_repaired(self):
        self.ensure()
        damaged = b"x" * ENTRIES[0]["size"]
        (self.root / ENTRIES[0]["name"]).write_bytes(damaged)
        self.calls.clear()
        self.ensure()
        self.assertEqual(self.calls, ["encoder.int8.onnx"])
        self.assertEqual(next(self.root.glob("encoder.int8.onnx.corrupt-*")).read_bytes(), damaged)

    def test_hash_failure_not_installed(self):
        with self.assertRaisesRegex(RuntimeError, "SHA256"):
            self.ensure(opener=lambda _: io.BytesIO(b"X" * ENTRIES[0]["size"]))
        self.assertFalse((self.root / "encoder.int8.onnx").exists())
        self.assertFalse(list(self.root.glob("*.part-*")))

    def test_oversized_response_bounded(self):
        with self.assertRaisesRegex(RuntimeError, "exceeds"):
            self.ensure(opener=lambda _: io.BytesIO(b"X" * 10000))
        self.assertFalse((self.root / "encoder.int8.onnx").exists())

    def test_network_failure_then_resume(self):
        def fail(_):
            raise OSError("network unreachable fixture")
        with self.assertRaisesRegex(OSError, "network unreachable"):
            self.ensure(opener=fail)
        self.ensure()
        self.assertTrue(all(init.valid(self.root / e["name"], e) for e in ENTRIES))

    def test_interrupted_download_restart(self):
        ready = multiprocessing.Event()
        def worker():
            def blocked(_):
                ready.set()
                time.sleep(60)
                return io.BytesIO()
            self.ensure(opener=blocked)
        process = multiprocessing.Process(target=worker)
        process.start()
        self.assertTrue(ready.wait(5))
        process.kill()
        process.join(5)
        self.assertTrue(list(self.root.glob(".*.part-*")))
        self.assertFalse((self.root / "encoder.int8.onnx").exists())
        self.ensure()
        self.assertTrue(init.valid(self.root / "encoder.int8.onnx", ENTRIES[0]))
        self.assertFalse(list(self.root.glob(".*.part-*")))

    def test_complete_cache_cleans_orphans_without_redownload(self):
        self.ensure()
        self.calls.clear()
        path = self.root / ".encoder.int8.onnx.part-abcdefgh"
        path.write_bytes(b"incomplete")
        original = self.root / "encoder.int8.onnx"
        inode = original.stat().st_ino
        self.ensure()
        self.assertFalse(path.exists())
        self.assertEqual(self.calls, [])
        self.assertEqual(inode, original.stat().st_ino)

    def test_cleanup_preserves_symlinks_hardlinks_and_unknown_files(self):
        self.ensure()
        symlink = self.root / ".encoder.int8.onnx.part-abcdefgh"
        symlink.symlink_to(self.root / "encoder.int8.onnx")
        hardlink = self.root / ".joiner.onnx.part-abcdefgh"
        os.link(self.root / "joiner.onnx", hardlink)
        unknown = self.root / ".tokens.txt.part-unknown-user-file"
        unknown.write_bytes(b"retain")
        self.calls.clear()
        self.ensure()
        self.assertTrue(symlink.is_symlink())
        self.assertTrue(hardlink.exists())
        self.assertEqual(unknown.read_bytes(), b"retain")
        self.assertEqual(self.calls, [])

    def test_cleanup_skips_active_download_tempfile(self):
        self.ensure()
        path = self.root / ".decoder.onnx.part-abcdefgh"
        ready = multiprocessing.Event()
        release = multiprocessing.Event()
        def worker():
            with path.open("wb") as stream:
                fcntl.flock(stream, fcntl.LOCK_EX)
                stream.write(b"active")
                stream.flush()
                ready.set()
                release.wait(10)
        process = multiprocessing.Process(target=worker)
        process.start()
        try:
            self.assertTrue(ready.wait(5))
            self.ensure()
            self.assertTrue(path.exists())
        finally:
            release.set()
            process.join(5)
        self.assertEqual(process.exitcode, 0)
        self.ensure()
        self.assertFalse(path.exists())

    def test_concurrent_initializers_only_one_download_each(self):
        counter = multiprocessing.Value("i", 0)
        def worker():
            def slow(url):
                with counter.get_lock():
                    counter.value += 1
                time.sleep(0.03)
                return self.source(url)
            self.ensure(opener=slow)
        processes = [multiprocessing.Process(target=worker) for _ in range(3)]
        for p in processes:
            p.start()
        for p in processes:
            p.join(10)
            self.assertEqual(p.exitcode, 0)
        self.assertEqual(counter.value, 4)

    def test_public_source_missing_fails_closed(self):
        entries = [dict(e, url=None) for e in ENTRIES]
        with self.assertRaisesRegex(RuntimeError, "no approved public source"):
            init.ensure_models(self.root, entries)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_disk_full_preflight(self):
        class Full:
            f_bavail = 0
            f_frsize = 4096
        with patch.object(init.os, "statvfs", return_value=Full()):
            with self.assertRaisesRegex(RuntimeError, "insufficient free disk"):
                self.ensure()
        self.assertEqual(self.calls, [])

    def test_enospc_preserves_original(self):
        path = self.root / "encoder.int8.onnx"
        path.write_bytes(b"damaged")
        with patch.object(init.os, "fsync", side_effect=OSError(28, "No space left on device")):
            with self.assertRaises(OSError):
                init.download(path, ENTRIES[0], self.source)
        self.assertEqual(path.read_bytes(), b"damaged")

    def test_symlink_refused(self):
        path = self.root / "encoder.int8.onnx"
        path.symlink_to("/etc/passwd")
        with self.assertRaises(OSError):
            self.ensure()
        self.assertTrue(path.is_symlink())

    def test_https_and_redirect_policy(self):
        for url in ["http://example.org/a", "file:///etc/passwd", "https://user:password@example.org/a"]:
            with self.assertRaises(RuntimeError):
                init.receive(url)
        with self.assertRaises(RuntimeError):
            init.HTTPSOnly().redirect_request(None, None, 302, "", {}, "http://example.org/a")

    def test_absolute_relative_overrides(self):
        alternate = self.root / "custom"
        alternate.mkdir()
        paths = [alternate / (e["name"] + ".custom") for e in ENTRIES]
        init.ensure_models(self.root, ENTRIES, paths, self.source)
        self.assertTrue(all(init.valid(p, e) for p, e in zip(paths, ENTRIES)))

    def test_local_http_transport_fixture(self):
        # HTTP is deliberately injected only here; production receive() rejects it.
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                name = self.path.rsplit("/", 1)[-1]
                names = [e["name"] for e in ENTRIES]
                if name not in names:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.end_headers()
                self.wfile.write(PAYLOADS[names.index(name)])
            def log_message(self, *args):
                pass
        with http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            try:
                entries = [dict(e, url="http://127.0.0.1:" + str(server.server_port) + "/" + e["name"]) for e in ENTRIES]
                init.ensure_models(self.root, entries, opener=urllib.request.urlopen)
                self.assertTrue(all(init.valid(self.root / e["name"], e) for e in entries))
            finally:
                server.shutdown()
                thread.join()

    def test_real_https_transport_and_certificate_verification(self):
        certificate = self.root / "fixture-cert.pem"
        key = self.root / "fixture-key.pem"
        subprocess.run(["openssl", "req", "-x509", "-nodes", "-newkey", "rsa:2048",
                        "-keyout", str(key), "-out", str(certificate), "-days", "1",
                        "-subj", "/CN=127.0.0.1", "-addext", "subjectAltName=IP:127.0.0.1"],
                       check=True, capture_output=True)
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                name = self.path.rsplit("/", 1)[-1]
                names = [e["name"] for e in ENTRIES]
                self.send_response(200)
                self.end_headers()
                self.wfile.write(PAYLOADS[names.index(name)])
            def log_message(self, *args):
                pass
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certificate, key)
        with http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            server.socket = context.wrap_socket(server.socket, server_side=True)
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            try:
                entries = [dict(e, url="https://127.0.0.1:" + str(server.server_port) + "/" + e["name"]) for e in ENTRIES]
                with self.assertRaises(OSError):
                    init.ensure_models(self.root, entries)
                with patch.dict(os.environ, {"SSL_CERT_FILE": str(certificate)}):
                    init.ensure_models(self.root, entries)
                self.assertTrue(all(init.valid(self.root / e["name"], e) for e in entries))
            finally:
                server.shutdown()
                thread.join()

    def test_inference_seccomp_denies_owned_file_mutation(self):
        path = self.root / "owned-model"
        path.write_bytes(b"verified")
        code = '''
import runpy, os, sys
m=runpy.run_path(sys.argv[1],run_name="test")
m["restrict_writes"]()
p=sys.argv[2]
assert open(p,"rb").read()==b"verified"
for operation in [lambda:open(p,"wb"), lambda:open(p+".new","w"),lambda:os.unlink(p),lambda:os.chmod(p,0o777),lambda:os.rename(p,p+".renamed")]:
 try: operation()
 except PermissionError: pass
 else: raise AssertionError("filesystem mutation unexpectedly allowed")
print("filesystem writes blocked; reads, exec and stdout allowed")
'''
        result = subprocess.run([sys.executable, "-c", code, str(Path(init.__file__)), str(path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(path.read_bytes(), b"verified")


if __name__ == "__main__":
    unittest.main()
