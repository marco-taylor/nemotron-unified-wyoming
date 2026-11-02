#!/usr/bin/python3
"""Pinned L37 bootstrap. Runs after UID/GID drop; never imports network manifests.

No runtime download switches or URL overrides: only the reviewed image manifest
is trusted. Existing absolute/relative model path overrides remain supported.
"""
import ctypes
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "model-manifest.json"
ENV_PATHS = ["ENCODER_PATH", "DECODER_PATH", "JOINER_PATH", "TOKENS_PATH"]


def log(message):
    print("model-init: " + message, file=sys.stderr, flush=True)


def valid(path, entry):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as source:
            meta = os.fstat(source.fileno())
            if not stat.S_ISREG(meta.st_mode) or meta.st_size != entry["size"]:
                return False
            return hashlib.file_digest(source, "sha256").hexdigest() == entry["sha256"]
    except FileNotFoundError:
        return False


class HTTPSOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlsplit(newurl)
        if parsed.scheme != "https" or parsed.username or parsed.password:
            raise RuntimeError("refusing download redirect outside credential-free HTTPS")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def receive(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise RuntimeError("model source must be an approved HTTPS URL without credentials")
    return urllib.request.build_opener(HTTPSOnly).open(url, timeout=30)


def sync_dir(directory):
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def download(path, entry, opener=receive, deadline=None):
    """Bounded writes, exact hash, same-directory rename; preserve invalid originals."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".part-", dir=path.parent)
    temporary = Path(temporary)
    try:
        digest = hashlib.sha256()
        total = 0
        log("downloading " + path.name)
        # Timeout per read + total deadline; no shell, proxy secrets or URLs in logs.
        deadline = deadline or time.monotonic() + 1800
        with os.fdopen(fd, "wb") as output, opener(entry["url"]) as source:
            while True:
                chunk = source.read(min(1024 * 1024, entry["size"] - total + 1))
                if not chunk:
                    break
                total += len(chunk)
                if total > entry["size"]:
                    raise RuntimeError(path.name + ": response exceeds pinned file size")
                if time.monotonic() > deadline:
                    raise RuntimeError(path.name + ": download deadline exceeded")
                output.write(chunk)
                digest.update(chunk)
            output.flush()
            os.fsync(output.fileno())
        if total != entry["size"] or digest.hexdigest() != entry["sha256"]:
            raise RuntimeError(path.name + ": SHA256/size verification failed; not installed")
        os.chmod(temporary, 0o644)
        # Do not destroy an existing damaged model. A unique hard link retains its
        # inode before atomic replacement; compliant concurrent initializers lock.
        if path.exists() or path.is_symlink():
            backup = path.with_name(path.name + ".corrupt-" + temporary.name.rsplit("-", 1)[-1])
            os.link(path, backup, follow_symlinks=False)
            sync_dir(path.parent)
            log("retained previous invalid file as " + backup.name)
        os.replace(temporary, path)
        sync_dir(path.parent)
        log("verified and installed " + path.name)
    finally:
        temporary.unlink(missing_ok=True)


def ensure_models(directory, entries, paths=None, opener=receive):
    paths = paths or [directory / entry["name"] for entry in entries]
    if all(valid(path, entry) for path, entry in zip(paths, entries, strict=True)):
        log("all four pinned L37 files verified; no download")
        return
    # There is deliberately no guessed URL for the private, custom ONNX export.
    missing = [(p, e) for p, e in zip(paths, entries, strict=True) if not valid(p, e)]
    if any(not entry.get("url") for _, entry in missing):
        raise RuntimeError("missing or damaged L37 files (" + ", ".join(p.name for p, _ in missing)
                           + "): no approved public source for this exact export. "
                           "Provision the verified L37 bundle; see docs/MODELS.md. "
                           "No substitute model will be downloaded.")
    directory.mkdir(parents=True, exist_ok=True)
    lock_fd = os.open(directory / ".model-init.lock",
                      os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    with os.fdopen(lock_fd, "r+b") as lock:
        if not stat.S_ISREG(os.fstat(lock.fileno()).st_mode):
            raise RuntimeError("initialization lock is not a regular file")
        log("waiting for exclusive model initialization lock")
        deadline = time.monotonic() + 1800
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() > deadline:
                    raise RuntimeError("timeout waiting for model initialization lock")
                time.sleep(0.2)
        for path, entry in zip(paths, entries, strict=True):
            if valid(path, entry):
                continue
            # Require enough room for new bytes plus the retained damaged original.
            space = os.statvfs(path.parent if path.parent.exists() else directory)
            if space.f_bavail * space.f_frsize < entry["size"] + 1024 * 1024:
                raise RuntimeError(path.name + ": insufficient free disk space for verified download")
            download(path, entry, opener, deadline=deadline)
        if not all(valid(path, entry) for path, entry in zip(paths, entries, strict=True)):
            raise RuntimeError("final model verification failed")


def restrict_writes():
    """Deny filesystem mutation after download, inherited by exec/ORT threads.

    libseccomp resolves syscalls for the native architecture; no SYS_ADMIN,
    privileged mounts, kernel Landlock dependency or model ownership changes.
    Existing stdout/stderr descriptors remain writable. No writable model file
    descriptors are inherited from initialization (all opened in context managers).
    """
    libc = ctypes.CDLL(None, use_errno=True)
    sec = ctypes.CDLL("libseccomp.so.2", use_errno=True)
    sec.seccomp_init.argtypes = [ctypes.c_uint32]
    sec.seccomp_init.restype = ctypes.c_void_p
    sec.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    sec.seccomp_syscall_resolve_name.restype = ctypes.c_int
    class Comparison(ctypes.Structure):
        _fields_ = [("arg", ctypes.c_uint), ("op", ctypes.c_int),
                    ("datum_a", ctypes.c_uint64), ("datum_b", ctypes.c_uint64)]
    sec.seccomp_rule_add_array.argtypes = [ctypes.c_void_p, ctypes.c_uint32,
                                         ctypes.c_int, ctypes.c_uint, ctypes.POINTER(Comparison)]
    sec.seccomp_load.argtypes = [ctypes.c_void_p]
    sec.seccomp_release.argtypes = [ctypes.c_void_p]
    context = sec.seccomp_init(0x7fff0000)  # SCMP_ACT_ALLOW
    if not context:
        raise RuntimeError("could not create inference filesystem seccomp filter")
    deny = 0x00050000 | errno.EACCES  # SCMP_ACT_ERRNO
    def rule(name, comparison=None):
        number = sec.seccomp_syscall_resolve_name(name.encode())
        if number < 0:
            return
        pointer = ctypes.byref(comparison) if comparison is not None else None
        if sec.seccomp_rule_add_array(context, deny, number, int(comparison is not None), pointer) != 0:
            raise RuntimeError("could not restrict syscall " + name)
    try:
        # Masked equality for every write-intent flag. Keep O_DIRECTORY reads.
        for name, argument in [("open", 1), ("openat", 2)]:
            for flag in [os.O_WRONLY, os.O_RDWR, os.O_CREAT, os.O_TRUNC, os.O_APPEND, 0x400000]:
                rule(name, Comparison(argument, 7, flag, flag))  # SCMP_CMP_MASKED_EQ
        # openat2 contains pointers, so cannot safely inspect its flags with BPF.
        for name in ("openat2", "creat", "open_by_handle_at", "io_uring_setup",
                     "truncate", "ftruncate", "unlink", "unlinkat", "rename", "renameat", "renameat2",
                     "link", "linkat", "symlink", "symlinkat", "mkdir", "mkdirat", "rmdir",
                     "mknod", "mknodat", "chmod", "fchmod", "fchmodat", "fchmodat2",
                     "chown", "fchown", "lchown", "fchownat", "setxattr", "lsetxattr", "fsetxattr",
                     "removexattr", "lremovexattr", "fremovexattr", "utime", "utimes",
                     "utimensat", "futimesat", "mount", "umount2", "pivot_root"):
            rule(name)
        if libc.prctl(38, 1, 0, 0, 0) != 0 or sec.seccomp_load(context) != 0:
            raise RuntimeError("could not enforce inference filesystem seccomp filter")
    finally:
        sec.seccomp_release(context)
    log("inference seccomp active: filesystem mutation denied; models remain readable")


def main(args):
    mode = args[0] if args else "serve"
    if mode == "serve":
        directory = Path(os.environ.get("MODEL_DIR", "/models"))
        if "--model" in args:
            directory = Path(args[args.index("--model") + 1])
        entries = json.loads(MANIFEST.read_text())["files"]
        paths = []
        for entry, env in zip(entries, ENV_PATHS, strict=True):
            override = os.environ.get(env) or entry["name"]
            path = Path(override)
            paths.append(path if path.is_absolute() else directory / path)
        ensure_models(directory, entries, paths)
        # License/provenance ship in the image even when a valid RO cache is used.
        # A future model host must distribute the same notices alongside artifacts.
        restrict_writes()
    os.execv("/usr/local/bin/nemotron-wyoming", ["nemotron-wyoming"] + args)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except (OSError, RuntimeError, ValueError, IndexError) as error:
        log(str(error))
        if isinstance(error, OSError) and error.errno in (errno.EACCES, errno.EROFS):
            log("initialization needs write access as PUID/PGID; existing valid models need only read access. No ownership changes were made.")
        sys.exit(2)
