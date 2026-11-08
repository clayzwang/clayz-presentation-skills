"""Portable immutable files and a verifiable append-only run history."""
from __future__ import annotations
import contextlib
import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return path


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", value):
        raise ValueError("expected a stable ID, not a path or command")
    return value


def resolve(root, ref):
    if not isinstance(ref, dict) or not {"path", "sha256", "bytes"} <= set(ref):
        raise ValueError("file reference requires path/sha256/bytes")
    part = PurePosixPath(ref["path"])
    if part.is_absolute() or ".." in part.parts:
        raise ValueError("run snapshots require safe relative paths")
    root = Path(root).resolve()
    path = root.joinpath(*part.parts)
    if not path.resolve().is_relative_to(root) or path.is_symlink():
        raise ValueError("snapshot leaves the run")
    data = path.read_bytes()
    if len(data) != ref["bytes"] or digest(data) != ref["sha256"]:
        raise ValueError("snapshot identity changed: " + ref["path"])
    return path


def snapshot(root, source):
    """Capture current bytes, never recursively reinterpret historical JSON refs."""
    root, source = Path(root).resolve(), Path(source).resolve(strict=True)
    before = source.stat()
    if not source.is_file():
        raise ValueError("a regular source file is required")
    data = source.read_bytes()
    after = source.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise ValueError("source changed while being captured")
    suffix = source.suffix if re.fullmatch(r"\.[A-Za-z0-9]{1,10}", source.suffix) else ".bin"
    relative = "objects/" + digest(data) + suffix
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        if target.read_bytes() != data:
            raise ValueError("content-addressed snapshot collision")
    return {"path": relative, "sha256": digest(data), "bytes": len(data), "original_path": str(source)}


def snapshot_json(root, value, name="payload.json"):
    temp = Path(root) / "scratch" / (uuid.uuid4().hex + "-" + Path(name).name)
    write_new(temp, value)
    return snapshot(root, temp)


@contextlib.contextmanager
def locked(root):
    lock = Path(root) / ".workflow.lock"
    try:
        handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError("another transaction holds this run lock; inspect before recovering it")
    try:
        os.write(handle, str(os.getpid()).encode())
        os.close(handle)
        yield
    finally:
        lock.unlink()


def events(root):
    result, previous = [], None
    for index, path in enumerate(sorted((Path(root) / "events").glob("*.json")), 1):
        value = read(path)
        saved = value.get("record_sha256")
        unsigned = {k:v for k,v in value.items() if k != "record_sha256"}
        if value.get("sequence") != index or value.get("previous_sha256") != previous or saved != digest(canonical(unsigned)):
            raise ValueError("run event chain is invalid")
        result.append(value)
        previous = saved
    return result


def append(root, kind, payload):
    """Caller holds the run lock; a committed event is the authority, not a cache."""
    history = events(root)
    value = {"sequence":len(history)+1, "event_id":uuid.uuid4().hex,
             "recorded_at":now(), "kind":kind, "payload":payload,
             "previous_sha256":history[-1]["record_sha256"] if history else None}
    value["record_sha256"] = digest(canonical(value))
    write_new(Path(root)/"events"/(f'{value["sequence"]:06d}-'+value["event_id"]+".json"), value)
    return value

