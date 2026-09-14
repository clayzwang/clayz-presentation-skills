# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Immutable owner knowledge snapshots with a single atomic publication pointer.

One snapshot contains confirmed drafts, original attachments and an ordinary
IndexRecord provider. All readers verify it before using the existing Index.
This is filesystem persistence, not a ChatGPT Library client or identity service.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
from typing import Any
import uuid

from packages.index_runtime import IndexProvider, INDEX_CONTRACT
from packages.personal_extension import build_provider_manifest
from .discussion import validate_draft, validate_confirmation

PROVIDER_ID = "clayz.owner-consensus"
CONTRACT = "io.clayz.presentation.knowledge-snapshot/1.0"
PLUGIN_ROOT = Path(__file__).resolve().parents[2]
HEX = re.compile(r"[0-9a-f]{64}\Z")


class KnowledgeStoreError(ValueError):
    """Knowledge cannot be used or published without its complete evidence."""


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _file_hash(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def _root(value: Path, *, create: bool = False) -> Path:
    raw = Path(value).absolute()
    # A mount may not redirect knowledge through symlinks/junctions.
    for part in (raw, *raw.parents):
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise KnowledgeStoreError("Library root may not traverse a symlink or junction")
    root = raw.resolve()
    if root == PLUGIN_ROOT or PLUGIN_ROOT in root.parents:
        raise KnowledgeStoreError("owner Library must be outside the plugin installation")
    if create:
        root.mkdir(parents=True, exist_ok=True)
    if not root.is_dir():
        raise KnowledgeStoreError("Library is unavailable: no persistent store exists")
    return root


def _path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise KnowledgeStoreError("invalid snapshot relative path")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or any(part in {"..", "."} for part in pure.parts) or str(pure) != relative:
        raise KnowledgeStoreError("snapshot path escapes its root")
    path = root.joinpath(*pure.parts)
    cursor = path
    while cursor != root:
        if cursor.is_symlink() or (hasattr(cursor, "is_junction") and cursor.is_junction()):
            raise KnowledgeStoreError("snapshot paths may not traverse symlinks or junctions")
        cursor = cursor.parent
    if not path.resolve().is_relative_to(root.resolve()):
        raise KnowledgeStoreError("snapshot path escapes its root")
    return path


def _json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise KnowledgeStoreError("snapshot JSON must be an object")
    return value


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _index_record(draft: dict, *, content_file: bool = False) -> dict:
    sid, digest = draft["session_id"], draft["draft_sha256"]
    return {
        "contract": INDEX_CONTRACT, "record_id": "consensus." + sid,
        "record_type": "knowledge", "provider_id": PROVIDER_ID,
        "title": draft["title"], "summary": draft["consensus"],
        "source": {"source_id": "discussion." + sid,
                   "source_uri": f"library://clayz-confirmed/entries/{sid}/{digest}/{'content.json' if content_file else 'draft.json'}",
                   "source_revision": digest, "sha256": digest},
        "governance": {"human_admitted": True, "quality_status": "admitted",
                       "public_catalog_eligible": False, "deprecated": False},
        "rights": {"license": "owner-discussion-private", "redistribution": "owner-private",
                   "materialization": "owner-private", "commercial_use": None, "derivative_use": None,
                   "attribution_required": False, "never_copy": ["Do not redistribute original attachments without their own permission"]},
        "classification": {"stages": sorted(set([draft["stage"], *draft.get("applicable_stages", [])])),
                           "task_modes": [], "page_roles": [], "semantic_relations": [],
                           "purpose_tags": draft["purpose_tags"], "languages": [draft["language"]],
                           "failure_signals": [], "asset_class": "confirmed-knowledge", "brand_scope": "none"},
        "payload": {"kind": "inline", "ref": {
            "consensus": draft["consensus"], "applicability": draft["applicability"],
            "limitations": draft["limitations"], "provenance": draft["provenance"],
            "evidence_refs": draft["evidence_refs"], "owner_stage": draft["stage"],
            "draft_sha256": digest,
        }},
        "neighbors": {"physical": [], "semantic": []},
    }


def _provider(records: list[dict], allowed_hosts=("local",)) -> tuple[IndexProvider, dict]:
    provider = IndexProvider.from_records(PROVIDER_ID, records)
    manifest = build_provider_manifest(
        provider, index_uri="library://clayz-confirmed/records.jsonl",
        visibility="owner-private", allowed_hosts=allowed_hosts,
    )
    return provider, manifest


def _load_directory(directory: Path, expected_id: str) -> dict:
    manifest = _json(_path(directory, "manifest.json"))
    if manifest.get("contract") != CONTRACT or _digest(manifest) != expected_id:
        raise KnowledgeStoreError("snapshot manifest digest does not match snapshot ID")
    if manifest.get("provider_id") != PROVIDER_ID:
        raise KnowledgeStoreError("unexpected knowledge provider")
    files = manifest.get("files")
    entries = manifest.get("entries")
    if not isinstance(files, dict) or not files or not isinstance(entries, list) or not entries:
        raise KnowledgeStoreError("snapshot is incomplete")
    observed = set()
    for path in directory.rglob("*"):
        relative = path.relative_to(directory).as_posix()
        _path(directory, relative)
        if path.is_file() and relative != "manifest.json":
            observed.add(relative)
    if observed != set(files):
        raise KnowledgeStoreError("snapshot file inventory differs from its manifest")
    for relative, digest in files.items():
        if not isinstance(digest, str) or not HEX.fullmatch(digest) or _file_hash(_path(directory, relative)) != digest:
            raise KnowledgeStoreError(f"snapshot file is missing or changed: {relative}")
    loaded, expected_records, seen = [], [], set()
    expected_files = {"records.jsonl", "provider.manifest.json"}
    for entry in entries:
        if not isinstance(entry, dict):
            raise KnowledgeStoreError("invalid snapshot entry")
        draft = validate_draft(_json(_path(directory, entry["draft_path"])))
        confirmation = validate_confirmation(draft, _json(_path(directory, entry["confirmation_path"])))
        sid = draft["session_id"]
        if sid in seen or entry.get("session_id") != sid or entry.get("draft_sha256") != draft["draft_sha256"]:
            raise KnowledgeStoreError("duplicate or mismatched discussion identity")
        seen.add(sid)
        paths = entry.get("attachments")
        if not isinstance(paths, dict) or set(paths) != {item["attachment_id"] for item in draft["attachments"]}:
            raise KnowledgeStoreError("attachment inventory mismatch")
        for item in draft["attachments"]:
            relative = paths[item["attachment_id"]]
            path = _path(directory, relative)
            if relative not in files or _file_hash(path) != item["sha256"] or path.stat().st_size != item["bytes"]:
                raise KnowledgeStoreError("confirmed attachment changed")
            expected_files.add(relative)
        expected_files.update((entry["draft_path"], entry["confirmation_path"]))
        content_path = entry.get("content_path")
        if content_path is not None:
            if content_path != f"entries/{sid}/{draft['draft_sha256']}/content.json":
                raise KnowledgeStoreError("knowledge source path does not match its revision")
            if content_path not in files or _file_hash(_path(directory, content_path)) != draft["draft_sha256"]:
                raise KnowledgeStoreError("knowledge source bytes do not match the indexed SHA-256")
            expected_files.add(content_path)
        loaded.append({**entry, "draft": draft, "confirmation": confirmation})
        expected_records.append(_index_record(draft, content_file=content_path is not None))
    if set(files) != expected_files:
        raise KnowledgeStoreError("snapshot contains unowned files")
    stored_provider_manifest = _json(_path(directory, "provider.manifest.json"))
    provider, provider_manifest = _provider(expected_records, stored_provider_manifest.get("allowed_hosts", []))
    index_path = _path(directory, "records.jsonl")
    actual = IndexProvider.from_jsonl(PROVIDER_ID, index_path)
    if list(actual.records) != list(provider.records):
        raise KnowledgeStoreError("index does not match confirmed knowledge")
    if stored_provider_manifest != provider_manifest:
        raise KnowledgeStoreError("provider manifest does not match verified index")
    return {"snapshot_id": expected_id, "snapshot_root": str(directory), "provider_id": PROVIDER_ID,
            "records": list(provider.records), "index_path": str(index_path),
            "manifest_path": str(directory / "manifest.json"),
            "provider_manifest_path": str(directory / "provider.manifest.json"), "entries": loaded}


def load_snapshot(store_root: Path, snapshot_id: str | None = None) -> dict:
    root = _root(store_root)
    if snapshot_id is None:
        pointer = _path(root, "CURRENT")
        if not pointer.is_file():
            raise KnowledgeStoreError("Library is unavailable: no committed snapshot")
        current = _json(pointer)
        snapshot_id = current.get("snapshot_id")
    if not isinstance(snapshot_id, str) or not HEX.fullmatch(snapshot_id):
        raise KnowledgeStoreError("invalid snapshot ID")
    directory = _path(root, "snapshots/" + snapshot_id)
    if not directory.is_dir():
        raise KnowledgeStoreError("committed snapshot is missing")
    return _load_directory(directory, snapshot_id)


@contextmanager
def _writer(root: Path):
    path = _path(root, ".writer.lock")
    token = uuid.uuid4().hex
    try:
        with path.open("x", encoding="ascii") as stream:
            stream.write(token)
    except FileExistsError as exc:
        raise KnowledgeStoreError("another writer holds this Library; retry after it finishes") from exc
    try:
        yield
    finally:
        if path.is_file() and path.read_text(encoding="ascii") == token:
            path.unlink()


def commit_knowledge(store_root: Path, draft: dict, confirmation: dict, attachments: dict[str, Path], *, allowed_hosts=("local",)) -> dict:
    draft = validate_draft(draft)
    confirmation = validate_confirmation(draft, confirmation)
    expected_attachments = {item["attachment_id"]: item for item in draft["attachments"]}
    if set(attachments) != set(expected_attachments):
        raise KnowledgeStoreError("attachment bindings must match the reviewed inventory exactly")
    for aid, raw in attachments.items():
        path = Path(raw)
        item = expected_attachments[aid]
        if not path.is_file() or _file_hash(path) != item["sha256"] or path.stat().st_size != item["bytes"]:
            raise KnowledgeStoreError("attachment changed after confirmation")
    root = _root(store_root, create=True)
    with _writer(root):
        current_path = _path(root, "CURRENT")
        previous = load_snapshot(root) if current_path.exists() else None
        old_entries = {item["session_id"]: item for item in previous["entries"]} if previous else {}
        old = old_entries.get(draft["session_id"])
        if old and old["draft_sha256"] == draft["draft_sha256"]:
            return {**previous, "status": "committed", "reused": True}
        expected_parent = old["draft_sha256"] if old else None
        if draft.get("supersedes") != expected_parent:
            raise KnowledgeStoreError("stale or missing parent revision; review the current consensus before retrying")
        snapshots = _path(root, "snapshots")
        staging = _path(root, "staging")
        snapshots.mkdir(exist_ok=True)
        staging.mkdir(exist_ok=True)
        temp = Path(tempfile.mkdtemp(prefix="transaction-", dir=staging))
        pointer_temp = root / (".CURRENT-" + uuid.uuid4().hex)
        try:
            entries = []
            for sid, entry in sorted(old_entries.items()):
                if sid == draft["session_id"]:
                    continue
                metadata = {key: value for key, value in entry.items() if key not in {"draft", "confirmation"}}
                for relative in [entry["draft_path"], entry["confirmation_path"], *([entry["content_path"]] if entry.get("content_path") else []), *entry["attachments"].values()]:
                    source = _path(Path(previous["snapshot_root"]), relative)
                    _write(_path(temp, relative), source.read_bytes())
                entries.append(metadata)
            prefix = f"entries/{draft['session_id']}/{draft['draft_sha256']}"
            entry = {"session_id": draft["session_id"], "draft_sha256": draft["draft_sha256"],
                     "draft_path": prefix + "/draft.json", "content_path": prefix + "/content.json",
                     "confirmation_path": prefix + "/confirmation.json", "attachments": {}}
            _write(_path(temp, entry["draft_path"]), _canonical(draft))
            # The index source SHA is the reviewed body digest. Give generic
            # host readers actual bytes with exactly that digest, without the
            # self-referential draft_sha256 field carried by the review wrapper.
            _write(_path(temp, entry["content_path"]), _canonical({key: value for key, value in draft.items() if key != "draft_sha256"}))
            _write(_path(temp, entry["confirmation_path"]), _canonical(confirmation))
            for aid, item in sorted(expected_attachments.items()):
                relative = prefix + "/attachments/" + aid + "/" + item["filename"]
                _write(_path(temp, relative), Path(attachments[aid]).read_bytes())
                # Recheck the copied bytes to close source-read races.
                if _file_hash(_path(temp, relative)) != item["sha256"]:
                    raise KnowledgeStoreError("attachment changed during copying")
                entry["attachments"][aid] = relative
            entries.append(entry)
            entries.sort(key=lambda item: item["session_id"])
            records = [_index_record(validate_draft(_json(_path(temp, item["draft_path"]))), content_file=bool(item.get("content_path"))) for item in entries]
            provider, provider_manifest = _provider(records, allowed_hosts)
            _write(temp / "records.jsonl", b"".join(_canonical(record) + b"\n" for record in provider.records))
            _write(temp / "provider.manifest.json", _canonical(provider_manifest))
            files = {path.relative_to(temp).as_posix(): _file_hash(path) for path in sorted(temp.rglob("*")) if path.is_file()}
            manifest = {"contract": CONTRACT, "provider_id": PROVIDER_ID, "files": files, "entries": entries}
            snapshot_id = _digest(manifest)
            _write(temp / "manifest.json", _canonical(manifest))
            _load_directory(temp, snapshot_id)
            target = _path(snapshots, snapshot_id)
            if target.exists():
                _load_directory(target, snapshot_id)
            else:
                os.rename(temp, target)
            # The single visibility boundary. A failure leaves CURRENT intact.
            _write(pointer_temp, _canonical({"snapshot_id": snapshot_id}))
            os.replace(pointer_temp, current_path)
            return {**load_snapshot(root), "status": "committed", "reused": False}
        finally:
            if pointer_temp.exists():
                pointer_temp.unlink()
            # Only our verified transaction directory may be recursively removed.
            if temp.exists() and temp.parent.resolve() == staging.resolve() and temp.name.startswith("transaction-"):
                shutil.rmtree(temp)
