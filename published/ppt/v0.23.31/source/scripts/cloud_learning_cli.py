#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Bounded bridge for confirmed learning and a host-native Library.

This command line facade is intentionally smaller than a Library client.  It
uses the existing discussion and knowledge-store contracts to prepare and
commit one verified snapshot into a task-local mirror, then emits a
host-consumable write plan.  A host Skill is responsible for discovering its
own file tools and applying that plan.  This module never calls a host API,
network service, UI automation, or an invented Library endpoint.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.index_runtime import CompositeIndex, IndexProvider  # noqa: E402
from packages.knowledge_session.discussion import (  # noqa: E402
    confirm_draft,
    prepare_draft,
)
from packages.knowledge_session.store import (  # noqa: E402
    KnowledgeStoreError,
    commit_knowledge,
    load_snapshot,
)
from packages.personal_extension.resolver import (  # noqa: E402
    prepare_unified_task_selection,
    validate_task_selection,
)


POLICY_CONTRACT = "io.clayz.presentation.native-library-policy/1.0"
PLAN_CONTRACT = "io.clayz.presentation.native-library-write-plan/1.0"
READBACK_CONTRACT = "io.clayz.presentation.native-library-readback/1.0"
INSPECTION_CONTRACT = "io.clayz.presentation.native-library-inspection/1.0"
POLICY_FIELDS = {"contract", "adapter", "host_root", "logical_root", "provider_id"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


class CloudLearningError(ValueError):
    """Raised when a cloud/native Library handoff is not trustworthy."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CloudLearningError(message)


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CloudLearningError(f"cannot read JSON {path}: {exc}") from exc


def read_object(path: Path) -> dict[str, Any]:
    value = _read_json(Path(path))
    _require(isinstance(value, dict), f"expected a JSON object: {path}")
    return value


def bindings(values: Iterable[str]) -> dict[str, Path]:
    """Parse strict ``ATTACHMENT_ID=PATH`` bindings."""

    result: dict[str, Path] = {}
    for raw in values:
        identifier, separator, value = str(raw).partition("=")
        if not separator or not identifier or not value or identifier in result:
            raise CloudLearningError("attachments require unique ID=PATH bindings")
        try:
            result[identifier] = Path(value).resolve(strict=True)
        except (OSError, RuntimeError, ValueError) as exc:
            raise CloudLearningError(f"attachment path is unavailable: {identifier}") from exc
    return result


def provider_spec(raw: str) -> tuple[str, Path]:
    identifier, separator, value = str(raw).partition("=")
    if not separator or not identifier or not value:
        raise argparse.ArgumentTypeError("provider must use PROVIDER_ID=PATH")
    try:
        path = Path(value).resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        raise argparse.ArgumentTypeError(f"provider path is unavailable: {value}") from exc
    return identifier, path


def external_artifact(path: Path) -> Path:
    """Keep review and handoff artifacts outside the installed Skill root."""

    resolved = Path(path).resolve()
    if resolved == ROOT or ROOT in resolved.parents:
        raise CloudLearningError("review and handoff artifacts must be outside the Skill installation")
    return resolved


def emit(value: Mapping[str, Any], output: Path | None) -> None:
    """Write one immutable JSON artifact and mirror it to stdout."""

    text = json.dumps(dict(value), ensure_ascii=False, indent=2) + "\n"
    if output is not None:
        destination = Path(output).resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            try:
                existing = destination.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise CloudLearningError(f"cannot read existing output: {destination}") from exc
            if existing != text:
                raise CloudLearningError(
                    "output already exists with different content; use a new revision path"
                )
        else:
            try:
                with destination.open("x", encoding="utf-8", newline="\n") as stream:
                    stream.write(text)
            except OSError as exc:
                raise CloudLearningError(f"cannot write output {destination}: {exc}") from exc
    print(text, end="")


def _canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(dict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _new_output_dir(path: Path) -> Path:
    destination = Path(path).resolve()
    _require(destination != ROOT and ROOT not in destination.parents, "task output directory must be outside the Skill installation")
    _require(not destination.exists(), "task output directory must be new and must not overwrite an existing directory")
    return destination


def _write_new_bytes(path: Path, payload: bytes) -> None:
    try:
        with path.open("xb") as stream:
            stream.write(payload)
    except OSError as exc:
        raise CloudLearningError(f"cannot write new task artifact: {path}") from exc


def configure_task(
    output_dir: Path, *, personal_config_path: Path | None = None,
    task_overrides_path: Path | None = None, library_locator: str | None = None,
    library_enabled: bool | None = None, previous_selection: Path | None = None,
) -> dict[str, Any]:
    """Create one unified task-local config/selection pair without changing the bundle."""
    previous: dict[str, Any] | None = None
    if previous_selection is not None:
        previous_path = Path(previous_selection).resolve()
        previous = read_object(previous_path)
        previous_config = previous.get("config_path")
        _require(isinstance(previous_config, str) and Path(previous_config).is_absolute(),
                 "previous selection must bind an absolute config_path")
        previous = validate_task_selection(previous_path, Path(previous_config), ROOT)
    destination = _new_output_dir(output_dir)
    config_path = destination / "task-config.json"
    task_config, selection = prepare_unified_task_selection(
        ROOT, config_path, personal_config_path=personal_config_path,
        task_overrides_path=task_overrides_path, library_locator=library_locator,
        library_enabled=library_enabled, previous_selection=previous,
    )
    try:
        destination.mkdir(parents=True)
    except OSError as exc:
        raise CloudLearningError(f"cannot create task output directory: {destination}") from exc
    _write_new_bytes(config_path, _canonical_json_bytes(task_config))
    selection_path = destination / "task-selection.json"
    _write_new_bytes(selection_path, _canonical_json_bytes(selection))
    validate_task_selection(selection_path, config_path, ROOT, expected_mode="unified")
    print(json.dumps(selection, ensure_ascii=False, indent=2) + "\n", end="")
    return selection


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise CloudLearningError(f"cannot read file {path}: {exc}") from exc
    return digest.hexdigest()


def _safe_relative(raw: Any, label: str) -> str:
    _require(isinstance(raw, str) and bool(raw.strip()), f"{label} must be a relative path")
    _require("\\" not in raw and ":" not in raw, f"{label} contains an unsafe character")
    candidate = PurePosixPath(raw)
    _require(
        not candidate.is_absolute()
        and bool(candidate.parts)
        and all(part not in {".", ".."} for part in candidate.parts)
        and str(candidate) == raw,
        f"{label} must be a normalized relative path",
    )
    return raw


def _safe_join(root: Path, relative: str, label: str) -> Path:
    _safe_relative(relative, label)
    path = root.joinpath(*PurePosixPath(relative).parts)
    for cursor in (path, *path.parents):
        if cursor == root:
            break
        if cursor.is_symlink() or (hasattr(cursor, "is_junction") and cursor.is_junction()):
            raise CloudLearningError(f"{label} may not traverse a symlink or junction")
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise CloudLearningError(f"{label} escapes its root") from exc
    return path


def _validate_logical_root(raw: Any) -> str:
    _require(isinstance(raw, str) and raw.startswith("library://"), "policy.logical_root must be a library:// URI")
    _require(raw.endswith("/") and "\\" not in raw and "?" not in raw and "#" not in raw, "policy.logical_root must be a normalized library root")
    remainder = raw[len("library://") :]
    _require(bool(remainder) and "/" in remainder, "policy.logical_root must include a namespace")
    _require(all(part not in {"", ".", ".."} for part in remainder.split("/")[:-1]), "policy.logical_root contains an unsafe path")
    return raw


def validate_policy(value: Mapping[str, Any]) -> dict[str, str]:
    """Validate the five-key policy emitted by the root composer.

    The physical host root is read from this policy.  No private profile or
    host binding is inferred here.
    """

    _require(isinstance(value, Mapping), "native Library policy must be an object")
    normalized = dict(value)
    _require(set(normalized) == POLICY_FIELDS, f"native Library policy must contain exactly {sorted(POLICY_FIELDS)}")
    _require(normalized.get("contract") == POLICY_CONTRACT, f"policy.contract must be {POLICY_CONTRACT}")
    _require(normalized.get("adapter") == "host-library", "policy.adapter must be host-library")
    host_root = _safe_relative(normalized.get("host_root"), "policy.host_root")
    logical_root = _validate_logical_root(normalized.get("logical_root"))
    provider_id = normalized.get("provider_id")
    _require(isinstance(provider_id, str) and bool(provider_id.strip()) and bool(IDENTIFIER.fullmatch(provider_id)), "policy.provider_id is invalid")
    return {
        "contract": POLICY_CONTRACT,
        "adapter": "host-library",
        "host_root": host_root,
        "logical_root": logical_root,
        "provider_id": provider_id,
    }


def read_policy(path: Path) -> dict[str, str]:
    return validate_policy(read_object(Path(path)))


def _store_root(path: Path) -> Path:
    """Resolve a mirror root while preserving the store's external boundary."""

    resolved = Path(path).resolve()
    _require(resolved != ROOT and ROOT not in resolved.parents, "Library mirror must be outside the Skill installation")
    if resolved.exists() and not resolved.is_dir():
        raise CloudLearningError("Library mirror root is not a directory")
    return resolved


def _current_path(store_root: Path) -> Path:
    return store_root / "CURRENT"


def _capture_current(store_root: Path) -> tuple[str | None, bytes | None]:
    pointer = _current_path(store_root)
    if not pointer.exists() and not pointer.is_symlink():
        return None, None
    _require(pointer.is_file() and not pointer.is_symlink(), "CURRENT must be a regular file")
    try:
        payload = pointer.read_bytes()
    except OSError as exc:
        raise CloudLearningError(f"cannot read CURRENT: {exc}") from exc
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CloudLearningError(f"CURRENT is not valid UTF-8 JSON: {exc}") from exc
    _require(isinstance(value, dict) and isinstance(value.get("snapshot_id"), str), "CURRENT does not identify a snapshot")
    return _sha256_bytes(payload), payload


def _source_path(snapshot_root: Path, relative: str) -> Path:
    return _safe_join(snapshot_root, relative, "snapshot file")


def _snapshot_file_rows(snapshot: Mapping[str, Any], host_root: str | None = None) -> list[dict[str, Any]]:
    snapshot_id = snapshot.get("snapshot_id")
    _require(isinstance(snapshot_id, str) and bool(SHA256.fullmatch(snapshot_id)), "verified snapshot ID is invalid")
    root_raw = snapshot.get("snapshot_root")
    _require(isinstance(root_raw, str) and bool(root_raw), "verified snapshot has no root")
    snapshot_root = Path(root_raw).resolve()
    _require(snapshot_root.is_dir(), "verified snapshot root is unavailable")
    manifest_path = _source_path(snapshot_root, "manifest.json")
    manifest = read_object(manifest_path)
    files = manifest.get("files")
    _require(isinstance(files, dict) and bool(files), "verified snapshot manifest has no files")
    relatives = sorted(set(files) | {"manifest.json"})
    rows: list[dict[str, Any]] = []
    for relative in relatives:
        _require(isinstance(relative, str), "snapshot manifest path must be a string")
        source = _source_path(snapshot_root, relative)
        _require(source.is_file() and not source.is_symlink(), f"verified snapshot file is unavailable: {relative}")
        digest = _sha256_file(source)
        if relative != "manifest.json":
            expected = files.get(relative)
            _require(isinstance(expected, str) and SHA256.fullmatch(expected) and digest == expected, f"verified snapshot file hash mismatch: {relative}")
        target_relative = f"snapshots/{snapshot_id}/{relative}"
        row = {
            "kind": "file",
            "target_relative": target_relative,
            "relative_path": target_relative,
            "source_path": source.as_posix(),
            "sha256": digest,
            "bytes": source.stat().st_size,
        }
        if host_root is not None:
            row["native_target_relative"] = f"{host_root}/{target_relative}"
        rows.append(row)
    return rows


def _locked_source_binding(policy: Mapping[str, Any], snapshot_id: str) -> dict[str, Any]:
    host_root = str(policy["host_root"])
    return {
        "adapter": policy["adapter"],
        "provider_id": policy["provider_id"],
        "logical_root": policy["logical_root"],
        "host_root": host_root,
        "snapshot_relative_root": f"snapshots/{snapshot_id}/",
        "native_snapshot_root": f"{host_root}/snapshots/{snapshot_id}/",
    }


def _assert_snapshot_matches_policy(
    snapshot: Mapping[str, Any],
    policy: Mapping[str, Any],
    *,
    require_cloud_host: bool = True,
) -> None:
    _require(snapshot.get("provider_id") == policy["provider_id"], "policy.provider_id does not match the verified snapshot provider")
    provider_manifest_path = snapshot.get("provider_manifest_path")
    _require(isinstance(provider_manifest_path, str) and bool(provider_manifest_path), "verified snapshot has no provider manifest")
    provider_manifest = read_object(Path(provider_manifest_path))
    allowed_hosts = provider_manifest.get("allowed_hosts")
    _require(isinstance(allowed_hosts, list), "verified provider manifest has no allowed_hosts list")
    if require_cloud_host:
        _require("chatgpt-personal" in allowed_hosts, "verified provider manifest does not authorize the host-library adapter")
    records = snapshot.get("records")
    _require(isinstance(records, list) and records, "verified snapshot has no records")
    logical_root = str(policy["logical_root"])
    for index, record in enumerate(records):
        source = record.get("source") if isinstance(record, Mapping) else None
        source_uri = source.get("source_uri") if isinstance(source, Mapping) else None
        _require(isinstance(source_uri, str) and source_uri.startswith(logical_root), f"snapshot record {index} is outside policy.logical_root")


def stage_learning(
    store_root: Path,
    draft: Mapping[str, Any],
    confirmation: Mapping[str, Any],
    attachments: Mapping[str, Path],
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    """Commit to a mirror and emit a plan for the host's native Library."""

    store = _store_root(Path(store_root))
    normalized_policy = validate_policy(policy)
    old_current_sha256, _ = _capture_current(store) if store.exists() else (None, None)

    # A mirror with no CURRENT must be genuinely fresh.  A mirror with CURRENT
    # is accepted only after the existing complete snapshot is read through the
    # shared store loader; no partial host download is silently reused.
    if store.exists() and old_current_sha256 is None:
        try:
            entries = list(store.iterdir())
        except OSError as exc:
            raise CloudLearningError(f"cannot inspect Library mirror: {exc}") from exc
        _require(not entries, "Library mirror without CURRENT must be empty")
    if old_current_sha256 is not None:
        previous = load_snapshot(store)
        _assert_snapshot_matches_policy(previous, normalized_policy, require_cloud_host=False)

    try:
        committed = commit_knowledge(
            store,
            dict(draft),
            dict(confirmation),
            dict(attachments),
            allowed_hosts=("local", "chatgpt-personal"),
        )
    except (KnowledgeStoreError, OSError, ValueError, TypeError, KeyError) as exc:
        raise CloudLearningError(str(exc)) from exc

    # Never expose the store's local ``committed`` status as a host-save claim.
    # Re-load the exact published mirror through the shared verifier before
    # constructing any native write action.
    snapshot_id = committed.get("snapshot_id") if isinstance(committed, Mapping) else None
    _require(isinstance(snapshot_id, str), "knowledge store did not return a snapshot ID")
    try:
        snapshot = load_snapshot(store, snapshot_id)
        current_snapshot = load_snapshot(store)
    except (KnowledgeStoreError, OSError, ValueError, TypeError, KeyError) as exc:
        raise CloudLearningError(f"staged mirror failed verification: {exc}") from exc
    _require(current_snapshot.get("snapshot_id") == snapshot_id, "staged mirror CURRENT does not point to the plan snapshot")
    _assert_snapshot_matches_policy(snapshot, normalized_policy)

    file_actions = _snapshot_file_rows(snapshot, normalized_policy["host_root"])
    pointer = _current_path(store)
    _require(pointer.is_file() and not pointer.is_symlink(), "staged mirror CURRENT is unavailable")
    current_payload = pointer.read_bytes()
    current_sha256 = _sha256_bytes(current_payload)
    _require(current_sha256 is not None and current_payload, "staged mirror CURRENT is empty")
    pointer_action = {
        "kind": "current-pointer",
        "target_relative": "CURRENT",
        "relative_path": "CURRENT",
        "native_target_relative": f"{normalized_policy['host_root']}/CURRENT",
        "source_path": pointer.resolve().as_posix(),
        "sha256": current_sha256,
        "bytes": len(current_payload),
        "expected_previous_sha256": old_current_sha256,
        "expected_previous_current_sha256": old_current_sha256,
        "expected_previous_current": old_current_sha256,
        "conditional_precondition": {"current_sha256": old_current_sha256},
        "conflict_policy": "reject-changed-current",
        "last": True,
    }
    actions = [*file_actions, pointer_action]
    return {
        "contract": PLAN_CONTRACT,
        "status": "awaiting-host-write",
        "adapter": normalized_policy["adapter"],
        "provider_id": snapshot["provider_id"],
        "logical_root": normalized_policy["logical_root"],
        "host_root": normalized_policy["host_root"],
        "policy": normalized_policy,
        "snapshot_id": snapshot_id,
        "staging_store": store.as_posix(),
        "saved": False,
        "host_saved": False,
        "expected_previous_current_sha256": old_current_sha256,
        "expected_previous_current": old_current_sha256,
        "expected_previous_current_record": {"sha256": old_current_sha256},
        "locked_source_binding": _locked_source_binding(normalized_policy, snapshot_id),
        "files": file_actions,
        "current": pointer_action,
        "actions": actions,
        "staging": {
            "status": "verified-task-mirror",
            "store_root": store.as_posix(),
            "reused": bool(committed.get("reused")) if isinstance(committed, Mapping) else False,
            "persistence": "task-scratch-only",
            "host_saved": False,
        },
        "write_semantics": {
            "snapshot_before_current": True,
            "current_action_last": True,
            "conditional_current_update": "expected_previous_sha256",
            "multi_file_cloud_atomicity": "not-claimed",
            "atomic": False,
        },
        "guards": {
            "snapshot_verified_before_plan": True,
            "host_write_required": True,
            "saved": False,
            "host_fetch_origin_authenticated": False,
        },
    }


def _plan_files(plan: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    _require(plan.get("contract") == PLAN_CONTRACT, f"plan.contract must be {PLAN_CONTRACT}")
    _require(plan.get("status") == "awaiting-host-write", "plan is not awaiting a host write")
    snapshot_id = plan.get("snapshot_id")
    _require(isinstance(snapshot_id, str) and bool(SHA256.fullmatch(snapshot_id)), "plan.snapshot_id is invalid")
    policy = plan.get("policy")
    _require(isinstance(policy, Mapping), "plan.policy is missing")
    normalized_policy = validate_policy(policy)
    _require(plan.get("adapter") == normalized_policy["adapter"], "plan.adapter does not match its policy")
    _require(plan.get("host_root") == normalized_policy["host_root"], "plan.host_root does not match its policy")
    _require(plan.get("logical_root") == normalized_policy["logical_root"], "plan.logical_root does not match its policy")
    _require(plan.get("provider_id") == normalized_policy["provider_id"], "plan provider does not match its policy")
    _require(
        plan.get("locked_source_binding") == _locked_source_binding(normalized_policy, snapshot_id),
        "plan locked source binding does not match its policy",
    )
    files = plan.get("files")
    _require(isinstance(files, list) and bool(files), "plan.files must be a non-empty list")
    normalized_files: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(files):
        _require(isinstance(raw, Mapping), f"plan.files[{index}] must be an object")
        row = dict(raw)
        target = row.get("target_relative")
        _require(isinstance(target, str), f"plan.files[{index}].target_relative is invalid")
        _safe_relative(target, f"plan.files[{index}].target_relative")
        _require(target.startswith(f"snapshots/{snapshot_id}/"), f"plan.files[{index}] is outside the plan snapshot")
        _require(target not in seen and target != "CURRENT", f"plan contains duplicate or invalid target: {target}")
        seen.add(target)
        if "native_target_relative" in row:
            _require(
                row.get("native_target_relative") == f"{normalized_policy['host_root']}/{target}",
                f"plan.files[{index}].native_target_relative is not bound to policy.host_root",
            )
        digest = row.get("sha256")
        _require(isinstance(digest, str) and bool(SHA256.fullmatch(digest)), f"plan.files[{index}].sha256 is invalid")
        size = row.get("bytes")
        _require(isinstance(size, int) and not isinstance(size, bool) and size >= 0, f"plan.files[{index}].bytes is invalid")
        normalized_files.append(row)
    current = plan.get("current")
    _require(isinstance(current, Mapping), "plan.current is missing")
    _require(current.get("target_relative") == "CURRENT" and current.get("last") is True, "plan.current must be the last CURRENT action")
    _require(
        current.get("native_target_relative") == f"{normalized_policy['host_root']}/CURRENT",
        "plan.current.native_target_relative is not bound to policy.host_root",
    )
    current_sha256 = current.get("sha256")
    _require(isinstance(current_sha256, str) and bool(SHA256.fullmatch(current_sha256)), "plan.current.sha256 is invalid")
    _require(current.get("expected_previous_sha256") == plan.get("expected_previous_current_sha256"), "plan CURRENT precondition is not bound")
    if "expected_previous_current" in current:
        _require(current.get("expected_previous_current") == plan.get("expected_previous_current"), "plan CURRENT previous digest alias is not bound")
    actions = plan.get("actions")
    _require(isinstance(actions, list) and len(actions) == len(normalized_files) + 1, "plan action inventory is incomplete")
    _require(actions[:-1] == normalized_files and actions[-1] == current, "plan actions do not match files and CURRENT")
    _require(isinstance(actions[-1], Mapping) and actions[-1].get("target_relative") == "CURRENT" and actions[-1].get("last") is True, "CURRENT must be the final host action")
    return normalized_files, dict(current)


def verify_readback(store_root: Path, plan: Mapping[str, Any]) -> dict[str, Any]:
    """Verify a fresh host-fetched mirror against one write plan."""

    normalized_plan = dict(plan)
    file_rows, current_action = _plan_files(normalized_plan)
    store = _store_root(Path(store_root))
    staging_store = normalized_plan.get("staging_store")
    _require(isinstance(staging_store, str) and bool(staging_store), "plan.staging_store is missing")
    try:
        same_store = Path(staging_store).resolve() == store
    except (OSError, RuntimeError, ValueError) as exc:
        raise CloudLearningError("plan.staging_store is invalid") from exc
    _require(not same_store, "verify requires a fresh host readback directory, not the staging mirror")
    snapshot_id = str(normalized_plan["snapshot_id"])
    try:
        snapshot = load_snapshot(store, snapshot_id)
        current_snapshot = load_snapshot(store)
    except (KnowledgeStoreError, OSError, ValueError, TypeError, KeyError) as exc:
        raise CloudLearningError(f"host readback mirror failed verification: {exc}") from exc
    _require(snapshot.get("snapshot_id") == snapshot_id, "host readback loaded a different snapshot")
    _require(current_snapshot.get("snapshot_id") == snapshot_id, "host readback CURRENT does not point to the plan snapshot")
    _assert_snapshot_matches_policy(snapshot, normalized_plan["policy"])

    snapshot_root = Path(str(snapshot["snapshot_root"])).resolve()
    expected_targets: set[str] = set()
    verified_files: list[dict[str, Any]] = []
    for row in file_rows:
        target = str(row["target_relative"])
        expected_targets.add(target)
        # The plan's target is relative to policy.host_root, which is the
        # mirror root supplied to this command.  It never becomes a filesystem
        # path outside that root.
        target_path = _safe_join(store, target, "host readback target")
        _require(target_path.is_file() and not target_path.is_symlink(), f"host readback file is missing: {target}")
        actual_digest = _sha256_file(target_path)
        actual_size = target_path.stat().st_size
        _require(actual_digest == row["sha256"], f"host readback file hash mismatch: {target}")
        _require(actual_size == row["bytes"], f"host readback file size mismatch: {target}")
        verified_files.append({"target_relative": target, "sha256": actual_digest, "bytes": actual_size})

    actual_relatives = {
        f"snapshots/{snapshot_id}/{path.relative_to(snapshot_root).as_posix()}"
        for path in snapshot_root.rglob("*")
        if path.is_file() and path.relative_to(snapshot_root).as_posix() != "manifest.json"
    }
    actual_relatives.add(f"snapshots/{snapshot_id}/manifest.json")
    _require(expected_targets == actual_relatives, "host readback file inventory differs from the plan")

    current_digest, _ = _capture_current(store)
    _require(current_digest == current_action["sha256"], "host readback CURRENT hash does not match the plan")
    return {
        "contract": READBACK_CONTRACT,
        "status": "verified-readback",
        "snapshot_id": snapshot_id,
        "provider_id": normalized_plan["provider_id"],
        "logical_root": normalized_plan["logical_root"],
        "host_root": normalized_plan["host_root"],
        "current_sha256": current_digest,
        "expected_previous_current_sha256": normalized_plan.get("expected_previous_current_sha256"),
        "files_verified": len(verified_files),
        "files": verified_files,
        "locked_source_binding": normalized_plan.get("locked_source_binding"),
        "host_fetch_origin": {
            "status": "not-authenticated",
            "authenticated": False,
            "responsibility": "host",
            "note": "The host is responsible for fetching the readback mirror; this result authenticates bytes against the plan only.",
        },
        "guards": {
            "load_snapshot_verified": True,
            "current_matches_plan": True,
            "file_inventory_matches_plan": True,
            "host_fetch_origin_authenticated": False,
            "saved_claim": False,
        },
    }


def _snapshot_source_binding(snapshot: Mapping[str, Any]) -> dict[str, Any] | None:
    records = snapshot.get("records")
    if not isinstance(records, list):
        return None
    uris = []
    for record in records:
        source = record.get("source") if isinstance(record, Mapping) else None
        uri = source.get("source_uri") if isinstance(source, Mapping) else None
        if isinstance(uri, str) and uri.startswith("library://"):
            namespace_start = len("library://")
            first_separator = uri.find("/", namespace_start)
            if first_separator >= 0:
                uris.append(uri[: first_separator + 1])
    if not uris:
        return None
    roots = sorted({uri[: uri.rfind("/") + 1] for uri in uris})
    return {
        "provider_id": snapshot.get("provider_id"),
        "logical_roots": roots,
        "snapshot_id": snapshot.get("snapshot_id"),
        "snapshot_relative_root": f"snapshots/{snapshot.get('snapshot_id')}/",
    }


def read_library(
    store_root: Path,
    record_id: str,
    snapshot_id: str | None = None,
    policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Read one exact consensus and its verified attachment bindings.

    The store loader remains the authority for snapshot integrity.  This
    helper only selects one record and resolves the attachment paths already
    bound by that verified snapshot; it does not create another index or
    materializer.
    """

    store = _store_root(Path(store_root))
    try:
        snapshot = load_snapshot(store, snapshot_id)
    except (KnowledgeStoreError, OSError, ValueError, TypeError, KeyError) as exc:
        raise CloudLearningError(f"Library snapshot unavailable: {exc}") from exc
    if policy is not None:
        normalized_policy = validate_policy(policy)
        _assert_snapshot_matches_policy(snapshot, normalized_policy)
    else:
        normalized_policy = None

    records = [
        record for record in snapshot.get("records", [])
        if isinstance(record, Mapping) and record.get("record_id") == record_id
    ]
    _require(len(records) == 1, f"record not found in the selected knowledge snapshot: {record_id}")
    record = dict(records[0])
    session_id = record_id[len("consensus.") :] if record_id.startswith("consensus.") else ""
    entries = snapshot.get("entries")
    _require(isinstance(entries, list), "verified snapshot entries are invalid")
    matches = [
        entry for entry in entries
        if isinstance(entry, Mapping)
        and entry.get("session_id") == session_id
        and record.get("source", {}).get("sha256") == entry.get("draft_sha256")
    ]
    _require(len(matches) == 1, f"record {record_id} has no exact committed entry")
    entry = dict(matches[0])
    draft = entry.get("draft")
    confirmation = entry.get("confirmation")
    _require(isinstance(draft, Mapping) and isinstance(confirmation, Mapping), "committed discussion entry is incomplete")
    _require(record_id == f"consensus.{draft.get('session_id')}", "record and draft session_id do not match")
    _require(record.get("summary") == draft.get("consensus"), "record consensus does not match its exact draft")
    payload = record.get("payload")
    ref = payload.get("ref") if isinstance(payload, Mapping) else None
    if isinstance(ref, Mapping) and "consensus" in ref:
        _require(ref.get("consensus") == draft.get("consensus"), "record payload consensus does not match its exact draft")

    snapshot_root = Path(str(snapshot.get("snapshot_root"))).resolve()
    _require(snapshot_root.is_dir(), "verified snapshot root is unavailable")
    mapped = entry.get("attachments", {})
    _require(isinstance(mapped, Mapping), "committed attachment bindings are invalid")
    attachment_bindings: dict[str, str] = {}
    attachment_rows: list[dict[str, Any]] = []
    draft_attachments = draft.get("attachments", [])
    _require(isinstance(draft_attachments, list), "committed draft attachments are invalid")
    for raw in draft_attachments:
        _require(isinstance(raw, Mapping), "committed attachment metadata is invalid")
        attachment_id = raw.get("attachment_id")
        expected_sha = raw.get("sha256")
        relative = mapped.get(attachment_id) if isinstance(attachment_id, str) else None
        _require(isinstance(attachment_id, str) and isinstance(relative, str), "committed attachment binding is missing")
        _require(isinstance(expected_sha, str) and bool(SHA256.fullmatch(expected_sha)), f"attachment {attachment_id} SHA-256 is invalid")
        path = _safe_join(snapshot_root, relative, f"attachment {attachment_id}")
        _require(path.is_file() and not path.is_symlink(), f"attachment {attachment_id} is unavailable")
        actual_sha = _sha256_file(path)
        _require(actual_sha == expected_sha, f"attachment {attachment_id} failed hash verification")
        attachment_bindings[attachment_id] = path.as_posix()
        attachment_rows.append({
            **dict(raw),
            "relative_path": relative,
            "path": path.as_posix(),
            "verified": True,
        })
    _require(set(mapped) == set(attachment_bindings), "committed attachment map contains unbound files")
    return {
        "contract": "io.clayz.presentation.native-library-read/1.0",
        "status": "verified-read",
        "snapshot_id": snapshot["snapshot_id"],
        "provider_id": snapshot["provider_id"],
        "record_id": record_id,
        "session_id": draft.get("session_id"),
        "consensus": draft.get("consensus"),
        "draft": dict(draft),
        "confirmation": dict(confirmation),
        "record": record,
        "attachments": attachment_rows,
        "attachment_bindings": attachment_bindings,
        "locked_source_binding": (
            _locked_source_binding(normalized_policy, str(snapshot["snapshot_id"]))
            if normalized_policy is not None
            else _snapshot_source_binding(snapshot)
        ),
        "guards": {
            "loaded_through_store": True,
            "exact_record_match": True,
            "exact_session_id_match": True,
            "consensus_matches_draft": True,
            "attachment_hashes_verified": True,
            "no_arbitrary_path_reads": True,
        },
    }


def _providers(
    store_root: Path | None,
    snapshot_id: str | None,
    specs: Iterable[tuple[str, Path]],
) -> tuple[list[IndexProvider], dict[str, Any] | None, dict[str, Any] | None]:
    providers: list[IndexProvider] = []
    snapshot: dict[str, Any] | None = None
    if store_root is not None:
        store = _store_root(Path(store_root))
        try:
            snapshot = load_snapshot(store, snapshot_id)
        except (KnowledgeStoreError, OSError, ValueError, TypeError, KeyError) as exc:
            raise CloudLearningError(f"Library snapshot unavailable: {exc}") from exc
        provider_id = snapshot.get("provider_id")
        records = snapshot.get("records")
        _require(isinstance(provider_id, str) and isinstance(records, list), "Library snapshot provider is invalid")
        try:
            providers.append(IndexProvider.from_records(provider_id, records))
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise CloudLearningError(f"Library provider is invalid: {exc}") from exc
    seen = {provider.provider_id for provider in providers}
    for provider_id, path in specs:
        _require(provider_id not in seen, f"duplicate provider_id: {provider_id}")
        try:
            provider = IndexProvider.from_jsonl(provider_id, path)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise CloudLearningError(f"provider {provider_id} is invalid: {exc}") from exc
        providers.append(provider)
        seen.add(provider_id)
    return providers, snapshot, _snapshot_source_binding(snapshot) if snapshot else None


def inspect_library(
    store_root: Path | None,
    specs: Iterable[tuple[str, Path]],
    snapshot_id: str | None = None,
) -> dict[str, Any]:
    providers, snapshot, source_binding = _providers(store_root, snapshot_id, specs)
    runtime = CompositeIndex(providers) if providers else None
    return {
        "contract": INSPECTION_CONTRACT,
        "status": "ready" if providers else "no-provider",
        "library": {
            "status": "ready" if snapshot else "not-requested",
            "snapshot_id": snapshot.get("snapshot_id") if snapshot else None,
            "provider_id": snapshot.get("provider_id") if snapshot else None,
        },
        "locked_source_binding": source_binding,
        "providers": runtime.snapshots() if runtime is not None else [],
        "guards": {
            "read_only": True,
            "uses_load_snapshot": snapshot is not None,
            "uses_shared_composite_index": runtime is not None,
            "host_api_called": False,
            "network_access": False,
        },
    }


def retrieve_library(
    store_root: Path | None,
    request: Mapping[str, Any],
    specs: Iterable[tuple[str, Path]],
    snapshot_id: str | None = None,
) -> dict[str, Any]:
    providers, snapshot, _ = _providers(store_root, snapshot_id, specs)
    _require(providers, "retrieve requires a Library snapshot or at least one --provider")
    try:
        return CompositeIndex(providers).search(dict(request))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise CloudLearningError(f"retrieval request is invalid: {exc}") from exc


HOST_OBSERVATION_CONTRACT = "io.clayz.presentation.host-access-observation/1.0"
HOST_ACCESS_REPORT_CONTRACT = "io.clayz.presentation.host-access-report/1.0"
HOST_TOOL_KINDS = {"native-library", "current-chat-file", "other"}
HOST_OPERATIONS = {"locate", "read", "write"}
HOST_ATTEMPT_STATUSES = {"ok", "not_found", "denied", "error"}
HOST_READABLE_STATES = {"readable-native", "readable-attachment"}


def _host_text(value: Any, label: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{label} must be a non-empty string")
    return value


def _host_id(value: Any, label: str) -> str:
    identifier = _host_text(value, label)
    _require(bool(IDENTIFIER.fullmatch(identifier)), f"{label} must be a stable identifier")
    return identifier


def _host_locator(value: Any, label: str) -> str:
    locator = _host_text(value, label)
    _require(locator == locator.strip(), f"{label} must be a normalized display locator")
    _require(not any(ord(char) < 0x20 or ord(char) == 0x7F for char in locator), f"{label} contains a control character")
    _require("\\" not in locator and ":" not in locator and "//" not in locator, f"{label} must be a display locator, not an OS path or URI")
    if locator.startswith("/"):
        _require(not locator.startswith("//"), f"{label} must not be an UNC locator")
        locator = locator[1:]
    _require(bool(locator) and all(part not in {"", ".", ".."} for part in locator.split("/")), f"{label} must be a normalized display locator")
    return locator


def _host_match(raw: Any, label: str) -> dict[str, str]:
    _require(isinstance(raw, Mapping), f"{label} must be an object")
    return {"reference": _host_text(raw.get("reference"), f"{label}.reference"), "locator": _host_locator(raw.get("locator"), f"{label}.locator")}


def _validate_host_observation(observation: Mapping[str, Any]) -> dict[str, Any]:
    _require(isinstance(observation, Mapping), "host access observation must be an object")
    _require(observation.get("contract") == HOST_OBSERVATION_CONTRACT, f"observation.contract must be {HOST_OBSERVATION_CONTRACT}")
    session_id = _host_text(observation.get("session_id"), "observation.session_id")
    raw_tools, raw_resources, raw_attempts = (observation.get(key) for key in ("tools", "resources", "attempts"))
    _require(isinstance(raw_tools, list), "observation.tools must be a list")
    _require(isinstance(raw_resources, list), "observation.resources must be a list")
    _require(isinstance(raw_attempts, list), "observation.attempts must be a list")

    tools: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(raw_tools):
        label = f"tools[{index}]"
        _require(isinstance(raw, Mapping), f"{label} must be an object")
        tool_id = _host_id(raw.get("tool_id"), f"{label}.tool_id")
        _require(tool_id not in tools, f"duplicate tool_id: {tool_id}")
        kind, operations = raw.get("kind"), raw.get("operations")
        _require(isinstance(kind, str) and kind in HOST_TOOL_KINDS, f"{label}.kind is invalid")
        _require(isinstance(operations, list), f"{label}.operations must be a list")
        _require(all(isinstance(op, str) and op in HOST_OPERATIONS for op in operations) and len(operations) == len(set(operations)), f"{label}.operations is invalid or duplicated")
        tools[tool_id] = {"tool_id": tool_id, "kind": kind, "operations": set(operations)}

    resources: list[dict[str, Any]] = []
    resource_map: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(raw_resources):
        label = f"resources[{index}]"
        _require(isinstance(raw, Mapping), f"{label} must be an object")
        resource_id = _host_id(raw.get("resource_id"), f"{label}.resource_id")
        _require(resource_id not in resource_map, f"duplicate resource_id: {resource_id}")
        logical_uri = _host_text(raw.get("logical_uri"), f"{label}.logical_uri")
        _require(logical_uri.startswith("library://") and "\\" not in logical_uri and "?" not in logical_uri and "#" not in logical_uri, f"{label}.logical_uri is invalid")
        required = raw.get("required")
        _require(type(required) is bool, f"{label}.required must be a boolean")
        expected = raw.get("expected_sha256")
        if expected is not None:
            _require(isinstance(expected, str) and bool(SHA256.fullmatch(expected)), f"{label}.expected_sha256 is invalid")
        explicit = raw.get("explicit_attachment_ref")
        selected = raw.get("selected_reference")
        explicit = _host_text(explicit, f"{label}.explicit_attachment_ref") if explicit is not None else None
        selected = _host_text(selected, f"{label}.selected_reference") if selected is not None else None
        normalized = {"resource_id": resource_id, "logical_uri": logical_uri, "host_locator": _host_locator(raw.get("host_locator"), f"{label}.host_locator"), "required": required, "expected_sha256": expected, "explicit_attachment_ref": explicit, "selected_reference": selected}
        resources.append(normalized)
        resource_map[resource_id] = normalized

    attempts: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_attempts):
        label = f"attempts[{index}]"
        _require(isinstance(raw, Mapping), f"{label} must be an object")
        resource_id, tool_id = _host_id(raw.get("resource_id"), f"{label}.resource_id"), _host_id(raw.get("tool_id"), f"{label}.tool_id")
        _require(resource_id in resource_map, f"attempt references unknown resource_id: {resource_id}")
        _require(tool_id in tools, f"attempt references unknown tool_id: {tool_id}")
        operation, status = raw.get("operation"), raw.get("status")
        _require(isinstance(operation, str) and operation in {"locate", "read"}, f"{label}.operation is invalid")
        _require(operation in tools[tool_id]["operations"], f"attempt uses undeclared operation: {operation}")
        _require(isinstance(status, str) and status in HOST_ATTEMPT_STATUSES, f"{label}.status is invalid")
        normalized = {"resource_id": resource_id, "tool_id": tool_id, "operation": operation, "status": status}
        if operation == "locate" and status == "ok":
            matches = raw.get("matches")
            _require(isinstance(matches, list), f"{label}.matches must be a list")
            normalized["matches"] = [_host_match(match, f"{label}.matches[{match_index}]") for match_index, match in enumerate(matches)]
        elif operation == "read":
            if raw.get("reference") is not None:
                normalized["reference"] = _host_text(raw.get("reference"), f"{label}.reference")
            _require(status != "ok" or "reference" in normalized, f"{label}.reference is required for a successful read")
            if status == "ok":
                normalized["materialized_path"] = _host_text(raw.get("materialized_path"), f"{label}.materialized_path")
        attempts.append(normalized)
    return {"session_id": session_id, "tools": tools, "resources": resources, "resource_map": resource_map, "attempts": attempts}


def _host_fingerprint(observation: Mapping[str, Any]) -> str:
    tools = [{"tool_id": t["tool_id"], "kind": t["kind"], "operations": sorted(t["operations"])} for t in observation["tools"].values()]
    payload = {"session_id": observation["session_id"], "tools": sorted(tools, key=lambda item: item["tool_id"]), "resources": sorted(observation["resources"], key=lambda item: item["resource_id"])}
    return _sha256_bytes(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _host_materialize(attempts: list[dict[str, Any]], expected_sha256: str | None) -> dict[str, Any]:
    if not attempts:
        return {"state": "reference-resolved", "sha256": None, "materialized_path": None}
    # Attempts are ordered observations; a later bound attempt supersedes stale evidence.
    attempt = attempts[-1]
    if attempt["status"] == "denied":
        return {"state": "read-denied", "sha256": None, "materialized_path": None}
    if attempt["status"] == "error":
        return {"state": "read-error", "sha256": None, "materialized_path": None}
    if attempt["status"] == "not_found":
        return {"state": "resource-unresolved", "sha256": None, "materialized_path": None}
    path_text = attempt["materialized_path"]
    try:
        materialized = Path(path_text)
        if not materialized.exists() or not materialized.is_file():
            return {"state": "materialization-missing", "sha256": None, "materialized_path": path_text}
        digest = _sha256_file(materialized)
    except (OSError, ValueError, TypeError, CloudLearningError):
        return {"state": "read-error", "sha256": None, "materialized_path": path_text}
    if expected_sha256 is not None and digest != expected_sha256:
        return {"state": "hash-mismatch", "sha256": None, "materialized_path": path_text}
    return {"state": "readable", "sha256": digest, "materialized_path": path_text}


def _host_previous_unresolved(previous_report: Mapping[str, Any] | None, session_id: str, fingerprint: str) -> bool:
    if not isinstance(previous_report, Mapping) or previous_report.get("session_id") != session_id or previous_report.get("input_fingerprint") != fingerprint:
        return False
    if previous_report.get("required_unresolved"):
        return True
    resources = previous_report.get("resources")
    return isinstance(resources, list) and any(isinstance(item, Mapping) and item.get("state") not in HOST_READABLE_STATES for item in resources)


def resolve_access(observation: dict[str, Any], previous_report: dict[str, Any] | None = None) -> dict[str, Any]:
    """Resolve caller-reported host Library/file evidence without host API calls."""
    _require(previous_report is None or isinstance(previous_report, Mapping), "previous_report must be an object")
    normalized = _validate_host_observation(observation)
    fingerprint = _host_fingerprint(normalized)
    tools = normalized["tools"]
    native_tools = {tool_id for tool_id, tool in tools.items() if tool["kind"] == "native-library"}
    native_locate_available = any("locate" in tools[tool_id]["operations"] for tool_id in native_tools)
    native_read_available = any("read" in tools[tool_id]["operations"] for tool_id in native_tools)
    attachment_tools = {tool_id for tool_id, tool in tools.items() if tool["kind"] == "current-chat-file" and "read" in tool["operations"]}
    read_exposed = any(tool["kind"] in {"native-library", "current-chat-file"} and "read" in tool["operations"] for tool in tools.values())
    write_exposed = any(tool["kind"] == "native-library" and "write" in tool["operations"] for tool in tools.values())
    by_resource: dict[str, list[dict[str, Any]]] = {resource["resource_id"]: [] for resource in normalized["resources"]}
    for attempt in normalized["attempts"]:
        by_resource[attempt["resource_id"]].append(attempt)
    rows: list[dict[str, Any]] = []

    for resource in normalized["resources"]:
        resource_id, resource_attempts = resource["resource_id"], by_resource[resource["resource_id"]]
        located = [match for attempt in resource_attempts if attempt["operation"] == "locate" and attempt["status"] == "ok" and attempt["tool_id"] in native_tools for match in attempt.get("matches", [])]
        observed_refs = {match["reference"] for match in located}
        located = [match for match in located if match["locator"] == resource["host_locator"]]
        distinct = {(match["reference"], match["locator"]): match for match in located}
        refs, locators = {match["reference"] for match in distinct.values()}, {match["locator"] for match in distinct.values()}
        selected = resource["selected_reference"]
        if selected is not None:
            _require(selected in observed_refs, f"resources[{resource_id}].selected_reference was not observed")
        resolved = selected if selected in refs else (None if selected is not None else next(iter(refs)) if len(refs) == len(locators) == 1 else None)
        native_state = "capability-not-exposed" if not native_locate_available else "resource-unresolved"
        if distinct and resolved is None and selected is None:
            native_state = "resource-ambiguous"
        native_reads = [attempt for attempt in resource_attempts if attempt["operation"] == "read" and attempt["tool_id"] in native_tools and attempt.get("reference") == resolved]
        native_result = {"state": native_state, "sha256": None, "materialized_path": None}
        if resolved is not None:
            native_result = _host_materialize(native_reads, resource["expected_sha256"]) if native_read_available else {"state": "capability-not-exposed", "sha256": None, "materialized_path": None}

        attachment_reference = resource["explicit_attachment_ref"]
        attachment_result = {"state": "resource-unresolved", "sha256": None, "materialized_path": None}
        if attachment_reference is not None:
            attachment_reads = [attempt for attempt in resource_attempts if attempt["operation"] == "read" and attempt["tool_id"] in attachment_tools and attempt.get("reference") == attachment_reference]
            attachment_result = _host_materialize(attachment_reads, resource["expected_sha256"]) if attachment_tools else {"state": "capability-not-exposed", "sha256": None, "materialized_path": None}

        if attachment_result["state"] == "readable":
            state, reference, origin, result = "readable-attachment", attachment_reference, "current-chat-attachment", attachment_result
        elif native_result["state"] == "readable":
            state, reference, origin, result = "readable-native", resolved, "native-library", native_result
        elif attachment_reference is not None and attachment_tools and (attachment_result["state"] != "resource-unresolved" or resolved is None):
            state, reference, origin, result = attachment_result["state"], attachment_reference, "current-chat-attachment", attachment_result
        elif resolved is not None:
            state, reference, origin, result = native_result["state"], resolved, "native-library", native_result
        else:
            state, reference, origin, result = native_state, None, None, native_result
        rows.append({"resource_id": resource_id, "state": state, "reference": reference, "sha256": result["sha256"], "materialized_path": result["materialized_path"], "origin": origin, "library_access_verified": state == "readable-native"})

    required_unresolved = [row["resource_id"] for row, resource in zip(rows, normalized["resources"]) if resource["required"] and row["state"] not in HOST_READABLE_STATES]
    if not rows:
        status = "no-resources"
    else:
        required_rows = [row for row, resource in zip(rows, normalized["resources"]) if resource["required"]]
        readable_required = sum(row["state"] in HOST_READABLE_STATES for row in required_rows)
        status = "ready" if not required_rows or readable_required == len(required_rows) else "partial" if readable_required else "blocked"
    return {"contract": HOST_ACCESS_REPORT_CONTRACT, "session_id": normalized["session_id"], "input_fingerprint": fingerprint, "status": status, "resources": rows, "required_unresolved": required_unresolved, "read_capability_exposed": read_exposed, "write_capability_exposed": write_exposed, "write_verified": False, "library_access_verified": bool(rows) and any(row["state"] == "readable-native" for row in rows), "retry_discovery": not _host_previous_unresolved(previous_report, normalized["session_id"], fingerprint), "evidence_level": "host-reported-and-byte-verified", "host_api_called": False, "limitations": ["Evidence is caller-reported JSON.", "No authenticated host proof is available.", "No native host API calls were made.", "This resolver cannot install tools or grant permissions."]}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    configure = commands.add_parser("configure-task", help="create a unified task selection and derived config")
    # Keep old spelling parseable only so callers receive an actionable
    # migration error instead of silently creating another v1 record.
    configure.add_argument("--mode", dest="_legacy_mode", help=argparse.SUPPRESS)
    configure.add_argument("--visual-source", dest="_legacy_visual_source", help=argparse.SUPPRESS)
    configure.add_argument("--personal-config", type=Path, metavar="PERSONAL_CONFIG_JSON")
    configure.add_argument("--task-overrides", type=Path, metavar="TASK_OVERRIDES_JSON")
    configure.add_argument("--library-locator", metavar="LIBRARY_LOCATOR")
    library = configure.add_mutually_exclusive_group()
    library.add_argument("--with-library", dest="library_enabled", action="store_true")
    library.add_argument("--without-library", dest="library_enabled", action="store_false")
    configure.set_defaults(library_enabled=None)
    configure.add_argument("--previous-selection", type=Path, metavar="SELECTION_JSON")
    configure.add_argument("--output-dir", type=Path, required=True, metavar="NEW_TASK_DIRECTORY")

    draft = commands.add_parser("draft", help="prepare exact consensus and attachment review")
    draft.add_argument("--content", type=Path, required=True)
    draft.add_argument("--attachment", action="append", default=[], metavar="ID=PATH")
    draft.add_argument("--output", type=Path, required=True)

    confirm = commands.add_parser("confirm", help="record the user's exact-draft decision")
    confirm.add_argument("--draft", type=Path, required=True)
    confirm.add_argument("--expected-sha256", required=True)
    confirm.add_argument("--confirmed-by", required=True)
    confirm.add_argument("--decision", required=True)
    confirm.add_argument("--confirm-human-decision", action="store_true")
    confirm.add_argument("--output", type=Path, required=True)

    stage = commands.add_parser("stage", help="stage one verified snapshot and emit a native host write plan")
    stage.add_argument("--store", type=Path, required=True, metavar="MIRRORED_LIBRARY_ROOT")
    stage.add_argument("--draft", type=Path, required=True)
    stage.add_argument("--confirmation", type=Path, required=True)
    stage.add_argument("--attachment", action="append", default=[], metavar="ID=PATH")
    stage.add_argument("--policy", type=Path, default=ROOT / "runtime" / "native-library-policy.json")
    stage.add_argument("--output", type=Path, required=True, metavar="PLAN_JSON")

    verify = commands.add_parser("verify", help="verify one fresh host readback mirror against a write plan")
    verify.add_argument("--store", type=Path, required=True, metavar="FRESH_HOST_READBACK_MIRROR")
    verify.add_argument("--plan", type=Path, required=True, metavar="PLAN_JSON")
    verify.add_argument("--output", type=Path)

    read = commands.add_parser("read", help="read one verified consensus and its attachment bindings")
    read.add_argument("--store", type=Path, required=True)
    read.add_argument("--record-id", required=True)
    read.add_argument("--snapshot")
    read.add_argument("--policy", type=Path)
    read.add_argument("--output", type=Path)

    inspect = commands.add_parser("inspect", help="inspect a Library snapshot and optional providers")
    inspect.add_argument("--store", type=Path)
    inspect.add_argument("--snapshot")
    inspect.add_argument("--provider", action="append", default=[], type=provider_spec, metavar="PROVIDER_ID=PATH")
    inspect.add_argument("--output", type=Path)

    retrieve = commands.add_parser("retrieve", help="search the shared CompositeIndex")
    retrieve.add_argument("--store", type=Path)
    retrieve.add_argument("--snapshot")
    retrieve.add_argument("--provider", action="append", default=[], type=provider_spec, metavar="PROVIDER_ID=PATH")
    retrieve.add_argument("--request", type=Path, required=True)
    retrieve.add_argument("--output", type=Path)

    resolve = commands.add_parser("resolve-access", help="resolve caller-reported native Library/file access evidence")
    resolve.add_argument("--observation", type=Path, required=True, metavar="OBSERVATION_JSON")
    resolve.add_argument("--previous-report", type=Path, metavar="PREVIOUS_REPORT_JSON")
    resolve.add_argument("--output", type=Path, required=True, metavar="REPORT_JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "configure-task":
            if args._legacy_mode is not None or args._legacy_visual_source is not None:
                raise CloudLearningError(
                    "legacy --mode/--visual-source selection is v1; use --personal-config, "
                    "--task-overrides, and --with-library/--without-library"
                )
            configure_task(
                args.output_dir,
                personal_config_path=args.personal_config,
                task_overrides_path=args.task_overrides,
                library_locator=args.library_locator,
                library_enabled=args.library_enabled,
                previous_selection=args.previous_selection,
            )
            return 0
        if args.command == "draft":
            output = external_artifact(args.output)
            result = prepare_draft(read_object(args.content), bindings(args.attachment))
            emit(result, output)
            return 0
        if args.command == "confirm":
            output = external_artifact(args.output)
            result = confirm_draft(
                read_object(args.draft),
                expected_sha256=args.expected_sha256,
                confirmed_by=args.confirmed_by,
                decision=args.decision,
                confirm_human_decision=args.confirm_human_decision,
            )
            emit(result, output)
            return 0
        if args.command == "stage":
            output = external_artifact(args.output)
            result = stage_learning(
                args.store,
                read_object(args.draft),
                read_object(args.confirmation),
                bindings(args.attachment),
                read_policy(args.policy),
            )
            emit(result, output)
            return 0
        if args.command == "verify":
            output = external_artifact(args.output) if args.output else None
            result = verify_readback(args.store, read_object(args.plan))
            emit(result, output)
            return 0
        if args.command == "read":
            output = external_artifact(args.output) if args.output else None
            policy = read_policy(args.policy) if args.policy else None
            result = read_library(args.store, args.record_id, args.snapshot, policy)
            emit(result, output)
            return 0
        if args.command == "inspect":
            output = external_artifact(args.output) if args.output else None
            result = inspect_library(args.store, args.provider, args.snapshot)
            emit(result, output)
            return 0
        if args.command == "resolve-access":
            output = external_artifact(args.output)
            previous_report = read_object(args.previous_report) if args.previous_report else None
            result = resolve_access(read_object(args.observation), previous_report)
            emit(result, output)
            return 0
        output = external_artifact(args.output) if args.output else None
        result = retrieve_library(args.store, read_object(args.request), args.provider, args.snapshot)
        # Keep the standard CompositeIndex receipt unwrapped so the existing
        # index_runtime_cli can finalize it without a second receipt contract.
        emit(result, output)
        return 0
    except (CloudLearningError, KnowledgeStoreError, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
