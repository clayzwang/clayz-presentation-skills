# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Local runtime facade for plugin inspection and confirmed knowledge retrieval.

This module deliberately keeps the local plugin boundary narrow.  It validates
the installed Public Core, loads the bundled public provider through the
existing :mod:`packages.index_runtime` implementation, and asks the external
knowledge store for one immutable snapshot.  It does not implement another
index, execute arbitrary commands, run production preflight, or write owner
data.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from packages.index_runtime import CompositeIndex, IndexProvider


CONTRACT = "io.clayz.presentation.plugin-session/1.0"
INSPECTION_CONTRACT = "io.clayz.presentation.plugin-inspection/1.0"
TOOL_INVENTORY_CONTRACT = "io.clayz.presentation.tool-inventory/1.0"
CONTENT_MANIFEST_CONTRACT = "io.clayz.presentation.plugin-content/1.0"
PUBLIC_MANIFEST_CONTRACT = "io.clayz.presentation.provider-manifest/1.0"
RETRIEVAL_RECEIPT_CONTRACT = "io.clayz.presentation.retrieval-receipt/1.0"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class PluginSessionError(ValueError):
    """Raised when the installed plugin or a knowledge snapshot is invalid."""


# These are the files that make the local facade a complete, inspectable
# plugin.  Versioned core files are added below from component_version_guard so
# the facade follows the same dependency table as the packager and mount check.
BASE_REQUIRED_FILES = (
    ".codex-plugin/plugin.json",
    "VERSION",
    "config/default.json",
    "config/component-versions.json",
    "config/tool-catalog.json",
    "scripts/plugin_cli.py",
    "scripts/component_version_guard.py",
    "packages/contracts/plugin-system.md",
    "docs/plugin-system.md",
    "docs/plugin-system.zh-CN.md",
    "packages/knowledge_session/discussion.py",
    "packages/knowledge_session/store.py",
    "packages/runtime/plugin_session.py",
    "packages/index_runtime/provider.py",
    "packages/index_runtime/retrieval.py",
    "packages/index_runtime/validation.py",
    "catalog/provider-manifest.json",
    "catalog/records.jsonl",
)
STAGE_NAMES = ("logic", "copy", "art-direction", "output", "supervisor")
ADDITIONAL_REQUIRED_FILES = (
    "scripts/build_component_candidate_manifest.py",
    "scripts/finalize_task_acceptance.py",
    "scripts/bootstrap_owner_learning.py",
    "scripts/runtime_preflight.py",
    "scripts/validate_personal_extension.py",
    "scripts/materialize_owner_index.py",
    "scripts/validate_index_regression_gates.py",
    "scripts/finalize_resource_inventory.py",
    "scripts/validate_resource_inventory_regression.py",
    "packages/contracts/knowledge-learning.md",
    "packages/contracts/component-version-report.schema.json",
    "packages/contracts/component-candidate-manifest.schema.json",
    "packages/contracts/version-private-learning-audit.schema.json",
    "packages/contracts/index-execution-evidence.schema.json",
    "packages/contracts/task-acceptance.schema.json",
    "packages/contracts/chatgpt-release-acceptance.schema.json",
    "packages/contracts/resource-inventory.schema.json",
    "packages/validators/index_evidence.py",
    "packages/validators/acceptance_contract.py",
    "packages/validators/resource_inventory.py",
    "packages/validators/validate_output_qa.py",
    "packages/validators/audit_ppt_font_names.py",
    "packages/validators/validate_supervision_report.py",
    "packages/validators/independent_audit.py",
    "packages/contracts/supervisor-calibration.schema.json",
    "packages/contracts/independent-audit.schema.json",
    "packages/validators/task_commitments.py",
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PluginSessionError(message)


def _ensure_plugin_root(plugin_root: Path) -> Path:
    root = Path(plugin_root).resolve()
    _require(root.is_dir(), f"plugin root is not a directory: {root}")
    return root


def _ensure_external_store(plugin_root: Path, store_root: Path) -> Path:
    store = Path(store_root).resolve()
    _require(store != plugin_root and plugin_root not in store.parents, "owner Library must be outside the plugin root")
    return store


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PluginSessionError(f"cannot read JSON {path}: {exc}") from exc


def _read_object(path: Path) -> dict[str, Any]:
    value = _read_json(path)
    _require(isinstance(value, dict), f"{path}: expected a JSON object")
    return value


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise PluginSessionError(f"cannot read attachment {path}: {exc}") from exc
    return digest.hexdigest()


def _safe_relative(root: Path, raw: Any, label: str) -> Path:
    _require(isinstance(raw, str) and raw.strip(), f"{label} must be a relative path")
    candidate = PurePosixPath(raw.replace("\\", "/"))
    _require(not candidate.is_absolute() and ".." not in candidate.parts, f"{label} has an unsafe path")
    _require(candidate.parts and ":" not in candidate.parts[0], f"{label} has an unsafe path")
    resolved = (root / Path(*candidate.parts)).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise PluginSessionError(f"{label} escapes its root") from exc
    return resolved


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _required_files() -> list[str]:
    paths = set(BASE_REQUIRED_FILES)
    try:
        from scripts.component_version_guard import component_dependency_paths

        paths.update(component_dependency_paths())
    except (ImportError, OSError, ValueError):
        # The explicit BASE_REQUIRED_FILES still gives a useful report when a
        # partially copied installation cannot import its version guard.
        pass
    # Keep inspection aligned with the complete-plugin mount contract,
    # including shared validators and runtime scripts that are not version
    # markers themselves.  Keep this list local so a standalone ChatGPT Skill
    # does not acquire a dependency on the local-only mount checker.
    paths.update(ADDITIONAL_REQUIRED_FILES)
    paths.update(f"skills/clayz-presentation-{stage}/SKILL.md" for stage in STAGE_NAMES)
    return sorted(paths)


def _required_file_report(root: Path) -> dict[str, Any]:
    missing: list[str] = []
    invalid: list[str] = []
    for relative in _required_files():
        path = root / Path(*PurePosixPath(relative).parts)
        if not path.is_file():
            if path.exists():
                invalid.append(relative)
            else:
                missing.append(relative)
    return {
        "status": "complete" if not missing and not invalid else "incomplete",
        "required_paths": _required_files(),
        "missing_paths": missing,
        "invalid_paths": invalid,
    }


def _verify_content_manifest(root: Path) -> dict[str, Any]:
    """Verify the optional byte inventory emitted into local archives.

    A source checkout is intentionally reported as ``source-unsealed``.  A
    packaged root must declare the exact file set and hash every file except
    this manifest itself.
    """

    relative_manifest = "runtime/plugin-content-manifest.json"
    manifest_path = root / Path(*PurePosixPath(relative_manifest).parts)
    if not manifest_path.is_file():
        runtime_lock = root / "runtime/runtime-lock.json"
        if runtime_lock.is_file() and _read_object(runtime_lock).get("bundle") == "local-public-light":
            return {
                "status": "blocked", "present": False,
                "manifest_path": manifest_path.as_posix(),
                "missing_paths": [relative_manifest], "extra_paths": [], "hash_mismatches": [],
                "errors": ["packaged local plugin is missing its content inventory"],
            }
        return {
            "status": "source-unsealed",
            "present": False,
            "manifest_path": manifest_path.as_posix(),
            "missing_paths": [],
            "extra_paths": [],
            "hash_mismatches": [],
        }

    errors: list[str] = []
    missing: list[str] = []
    extra: list[str] = []
    mismatches: list[str] = []
    try:
        value = _read_object(manifest_path)
    except PluginSessionError as exc:
        return {
            "status": "blocked",
            "present": True,
            "manifest_path": manifest_path.as_posix(),
            "error": str(exc),
            "missing_paths": [],
            "extra_paths": [],
            "hash_mismatches": [],
        }
    if value.get("contract") != CONTENT_MANIFEST_CONTRACT:
        errors.append("wrong-contract")
    files = value.get("files")
    if not isinstance(files, dict) or not files:
        errors.append("files-must-be-nonempty-object")
        files = {}

    declared: dict[str, str] = {}
    for raw_relative, expected_hash in files.items():
        if not isinstance(raw_relative, str):
            errors.append("declared-path-must-be-string")
            continue
        try:
            target = _safe_relative(root, raw_relative, "content-manifest path")
        except PluginSessionError as exc:
            errors.append(str(exc))
            continue
        normalized = _relative(root, target)
        if normalized == relative_manifest:
            errors.append("content manifest must be excluded from its own files")
            continue
        if normalized in declared:
            errors.append(f"duplicate content-manifest path: {normalized}")
            continue
        if not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(expected_hash):
            errors.append(f"{normalized}: invalid SHA-256")
            continue
        declared[normalized] = expected_hash
        if not target.is_file():
            missing.append(normalized)
        elif _sha256_file(target) != expected_hash:
            mismatches.append(normalized)

    actual: set[str] = set()
    for path in root.rglob("*"):
        if path.is_file() and path.resolve() != manifest_path.resolve():
            actual.add(_relative(root, path))
    extra.extend(sorted(actual - set(declared)))
    missing.extend(sorted(set(declared) - actual))
    errors.extend(f"missing:{item}" for item in sorted(set(missing)))
    # Installed Python may create __pycache__ files after the archive was
    # mounted.  They are useful observations, but do not invalidate the
    # declared bytes.  A missing or changed declared file remains blocking.
    errors.extend(f"hash:{item}" for item in sorted(set(mismatches)))
    return {
        "status": "verified" if not errors else "blocked",
        "present": True,
        "manifest_path": manifest_path.as_posix(),
        "declared_file_count": len(declared),
        "missing_paths": sorted(set(missing)),
        "extra_paths": sorted(set(extra)),
        "hash_mismatches": sorted(set(mismatches)),
        "observations": ([{"kind": "unbound-installed-files", "paths": sorted(set(extra))}] if extra else []),
        "errors": errors,
    }


def _load_component_report(root: Path) -> dict[str, Any]:
    try:
        from scripts.component_version_guard import build_application_report

        report = build_application_report(root)
        _require(isinstance(report, dict), "component version guard returned a non-object")
        return report
    except (ImportError, OSError, ValueError, TypeError) as exc:
        return {
            "contract": "io.clayz.presentation.component-version-report/1.0",
            "status": "blocked",
            "error_codes": ["INSTALLED_COMPONENTS_INVALID"],
            "error": str(exc),
        }


def _load_public_provider(root: Path) -> tuple[IndexProvider, dict[str, Any]]:
    manifest_path = root / "catalog" / "provider-manifest.json"
    index_path = root / "catalog" / "records.jsonl"
    manifest = _read_object(manifest_path)
    _require(manifest.get("contract") == PUBLIC_MANIFEST_CONTRACT, "public provider manifest contract is invalid")
    _require(manifest.get("visibility") == "public", "public provider manifest must be public")
    _require(manifest.get("rights_context") == "public-open-source", "public provider manifest rights context is invalid")
    _require(manifest.get("human_admission_required") is True, "public provider manifest must require human admission")
    provider_id = manifest.get("provider_id")
    _require(isinstance(provider_id, str) and provider_id, "public provider manifest has no provider_id")
    index = manifest.get("index")
    _require(isinstance(index, dict), "public provider manifest index is invalid")
    _require(index.get("record_contract") == "io.clayz.presentation.index-record/1.0", "public index record contract is invalid")
    _require(index.get("format") == "jsonl", "public index format is invalid")
    _require(index.get("refresh_policy") == "immutable-release", "public index refresh policy is invalid")
    uri = index.get("uri")
    _require(isinstance(uri, str) and uri.startswith("bundle://"), "public index URI must be a bundle URI")
    expected_snapshot = index.get("snapshot")
    _require(isinstance(expected_snapshot, dict), "public provider manifest snapshot is missing")
    _require(expected_snapshot.get("provider_id") == provider_id, "public provider snapshot provider_id mismatch")
    try:
        provider = IndexProvider.from_jsonl(provider_id, index_path)
    except (OSError, ValueError, TypeError) as exc:
        raise PluginSessionError(f"public index is corrupt: {exc}") from exc
    actual_snapshot = provider.snapshot()
    _require(actual_snapshot == expected_snapshot, "public provider snapshot does not match catalog/provider-manifest.json")
    return provider, {
        "status": "ready",
        "provider_id": provider_id,
        "manifest_path": manifest_path.as_posix(),
        "index_path": index_path.as_posix(),
        "index_uri": uri,
        "snapshot": actual_snapshot,
    }


def _load_tool_catalog(root: Path) -> tuple[dict[str, Any], Path]:
    path = root / "config" / "tool-catalog.json"
    catalog = _read_object(path)
    _require(catalog.get("contract") == "io.clayz.presentation.tool-catalog/1.0", "tool catalog contract is invalid")
    _require(catalog.get("policy_scope") == "discovery-only", "tool catalog policy scope must be discovery-only")
    _require(catalog.get("network_policy") == "no-network-during-discovery", "tool catalog must disable network access during discovery")
    _require(catalog.get("arbitrary_executor") is False, "tool catalog must forbid arbitrary execution")
    tools = catalog.get("tools")
    _require(isinstance(tools, list) and tools, "tool catalog must contain tools")
    seen: set[str] = set()
    for index, tool in enumerate(tools):
        _require(isinstance(tool, dict), f"tool catalog entry {index} must be an object")
        tool_id = tool.get("tool_id")
        _require(isinstance(tool_id, str) and tool_id and tool_id not in seen, f"tool catalog entry {index} has duplicate or invalid tool_id")
        seen.add(tool_id)
        entrypoints = tool.get("entrypoints")
        _require(isinstance(entrypoints, list) and entrypoints and all(isinstance(item, str) and item for item in entrypoints), f"tool {tool_id} entrypoints are invalid")
        execution = tool.get("execution")
        _require(isinstance(execution, dict), f"tool {tool_id} execution policy is missing")
        _require(execution.get("arbitrary") is False, f"tool {tool_id} execution policy allows arbitrary execution")
        _require(execution.get("network") in {"disabled", "not-used", "no-network", "task-authorized-host-tools"}, f"tool {tool_id} execution network policy is unsupported")
    return catalog, path


def list_tools(plugin_root: Path) -> dict[str, Any]:
    """List real bundled entrypoints and separately mark host requirements."""

    root = _ensure_plugin_root(plugin_root)
    try:
        catalog, catalog_path = _load_tool_catalog(root)
    except PluginSessionError as exc:
        return {
            "contract": TOOL_INVENTORY_CONTRACT,
            "status": "blocked",
            "plugin_root": root.as_posix(),
            "catalog_path": (root / "config/tool-catalog.json").as_posix(),
            "tools": [],
            "error": str(exc),
            "guards": {"arbitrary_executor": False, "network_access": False},
        }

    resolved_tools: list[dict[str, Any]] = []
    for raw in catalog["tools"]:
        entrypoints = [str(item) for item in raw["entrypoints"]]
        missing = []
        for relative in entrypoints:
            try:
                target = _safe_relative(root, relative, f"tool {raw['tool_id']} entrypoint")
            except PluginSessionError:
                missing.append(relative)
                continue
            if not target.is_file():
                missing.append(relative)
        implementation_status = "installed" if not missing else "missing"
        host = dict(raw.get("host_capability") or {})
        host_required = bool(host.get("required", False))
        host["required"] = host_required
        host["status"] = "not-inspected" if host_required else "not-required"
        host["observed"] = False
        resolved_tools.append({
            **raw,
            "implementation": {
                "status": implementation_status,
                "entrypoints": entrypoints,
                "missing": sorted(set(missing)),
            },
            "host_capability": host,
            "available": implementation_status == "installed",
        })
    status = "ready" if all(item["available"] for item in resolved_tools) else "blocked"
    return {
        "contract": TOOL_INVENTORY_CONTRACT,
        "status": status,
        "plugin_root": root.as_posix(),
        "catalog_path": catalog_path.as_posix(),
        "policy_scope": catalog.get("policy_scope"),
        "network_policy": catalog.get("network_policy"),
        "tools": resolved_tools,
        "guards": {
            "arbitrary_executor": False,
            "network_access": False,
            "discovery_network_access": False,
            "host_capabilities_separate_from_installed_code": True,
        },
    }


def _store_unavailable(store: Path, reason: str, *, snapshot_id: str | None = None) -> dict[str, Any]:
    return {
        "status": "unavailable",
        "reason": reason,
        "store_root": store.as_posix(),
        "snapshot_id": snapshot_id,
    }


def _load_snapshot(store_root: Path, snapshot_id: str | None) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Call the storage agent's loader and preserve absent/no-CURRENT states."""

    store = Path(store_root).resolve()
    if not store.exists():
        return None, _store_unavailable(store, "store-absent", snapshot_id=snapshot_id)
    if not store.is_dir():
        return None, {"status": "blocked", "reason": "store-root-is-not-a-directory", "store_root": store.as_posix(), "snapshot_id": snapshot_id}
    current = store / "CURRENT"
    if snapshot_id is None and not current.is_file():
        return None, _store_unavailable(store, "no-current-snapshot")
    if snapshot_id is not None:
        if not SHA256_RE.fullmatch(snapshot_id):
            return None, {
                "status": "blocked",
                "reason": "invalid-snapshot-id",
                "store_root": store.as_posix(),
                "snapshot_id": snapshot_id,
            }
        candidate_dir = store / "snapshots" / snapshot_id
        if not candidate_dir.is_dir():
            return None, _store_unavailable(store, "snapshot-absent", snapshot_id=snapshot_id)
    try:
        from packages.knowledge_session.store import load_snapshot
    except (ImportError, ModuleNotFoundError) as exc:
        return None, {"status": "blocked", "reason": "knowledge-store-unavailable", "store_root": store.as_posix(), "error": str(exc)}
    try:
        snapshot = load_snapshot(store, snapshot_id)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        if snapshot_id is None and not current.is_file():
            return None, _store_unavailable(store, "no-current-snapshot", snapshot_id=snapshot_id)
        return None, {"status": "blocked", "reason": "snapshot-invalid", "store_root": store.as_posix(), "snapshot_id": snapshot_id, "error": str(exc)}
    _require(isinstance(snapshot, dict), "knowledge store returned a non-object snapshot")
    for key in ("snapshot_id", "provider_id", "records", "index_path", "manifest_path", "entries"):
        _require(key in snapshot, f"knowledge snapshot is missing {key}")
    _require(isinstance(snapshot.get("snapshot_id"), str) and snapshot["snapshot_id"], "knowledge snapshot_id is invalid")
    if snapshot_id is not None:
        _require(snapshot["snapshot_id"] == snapshot_id, "knowledge store returned a different snapshot than requested")
    _require(isinstance(snapshot.get("provider_id"), str) and snapshot["provider_id"], "knowledge provider_id is invalid")
    _require(isinstance(snapshot.get("records"), list), "knowledge snapshot records must be a list")
    _require(isinstance(snapshot.get("entries"), list), "knowledge snapshot entries must be a list")
    info = {
        "status": "ready",
        "store_root": store.as_posix(),
        "snapshot_id": snapshot["snapshot_id"],
        "provider_id": snapshot["provider_id"],
        "index_path": str(snapshot["index_path"]),
        "manifest_path": str(snapshot["manifest_path"]),
        "provider_manifest_path": str(snapshot.get("provider_manifest_path")) if snapshot.get("provider_manifest_path") else None,
        "record_count": len(snapshot["records"]),
        "entry_count": len(snapshot["entries"]),
    }
    return snapshot, info


def _private_index_uri(snapshot: Mapping[str, Any]) -> str:
    manifest_path = snapshot.get("provider_manifest_path")
    _require(isinstance(manifest_path, str) and manifest_path, "knowledge snapshot provider manifest path is missing")
    manifest = _read_object(Path(manifest_path))
    _require(manifest.get("contract") == PUBLIC_MANIFEST_CONTRACT, "knowledge provider manifest contract is invalid")
    _require(manifest.get("provider_id") == snapshot.get("provider_id"), "knowledge provider manifest provider_id mismatch")
    index = manifest.get("index")
    _require(isinstance(index, Mapping), "knowledge provider manifest index is invalid")
    uri = index.get("uri")
    _require(isinstance(uri, str) and uri.startswith("library://"), "knowledge provider manifest URI is invalid")
    return uri


def _provider_bindings(public_info: Mapping[str, Any], snapshot: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "provider_id": public_info["provider_id"],
            "manifest_path": public_info["manifest_path"],
            "index_path": public_info["index_path"],
            "uri": public_info["index_uri"],
            "snapshot": public_info["snapshot"],
        },
        {
            "provider_id": snapshot["provider_id"],
            "manifest_path": str(snapshot.get("provider_manifest_path") or snapshot["manifest_path"]),
            "index_path": str(snapshot["index_path"]),
            "uri": _private_index_uri(snapshot),
            "snapshot_id": snapshot["snapshot_id"],
        },
    ]


def retrieve_knowledge(
    plugin_root: Path,
    store_root: Path,
    request: dict[str, Any],
    snapshot_id: str | None = None,
) -> dict[str, Any]:
    """Retrieve one pinned knowledge snapshot through ``CompositeIndex``.

    The returned receipt intentionally has an empty selection.  Stage owners
    must inspect the selected record and use ``index_runtime_cli.py finalize``
    or their existing production artifact contract to record adoption.
    """

    root = _ensure_plugin_root(plugin_root)
    store = _ensure_external_store(root, store_root)
    public_provider, public_info = _load_public_provider(root)
    snapshot, store_info = _load_snapshot(store, snapshot_id)
    if snapshot is None:
        return {
            "contract": CONTRACT,
            "status": store_info["status"],
            "snapshot_id": store_info.get("snapshot_id"),
            "providers": [public_provider.snapshot()],
            "library": store_info,
            "public_index": public_info,
            "receipt": None,
            "selection": {"status": "not-finalized", "reason": "knowledge-snapshot-unavailable"},
        }

    try:
        private_provider = IndexProvider.from_records(snapshot["provider_id"], snapshot["records"])
    except (OSError, ValueError, TypeError) as exc:
        raise PluginSessionError(f"private knowledge index is corrupt: {exc}") from exc
    _require(private_provider.provider_id != public_provider.provider_id, "private provider_id must differ from builtin-catalog")
    runtime = CompositeIndex([public_provider, private_provider])
    receipt = runtime.search(request)
    bindings = _provider_bindings(public_info, snapshot)
    return {
        "contract": CONTRACT,
        "status": "ready",
        "snapshot_id": snapshot["snapshot_id"],
        "providers": runtime.snapshots(),
        "library": store_info,
        "public_index": public_info,
        "provider_bindings": bindings,
        "receipt": receipt,
        "selection": {
            "status": "not-finalized",
            "tool": "scripts/index_runtime_cli.py",
            "action": "finalize",
            "receipt_path": None,
            "provider_bindings": bindings,
        },
        "guards": {
            "existing_composite_index": True,
            "snapshot_pinned": True,
            "selection_not_finalized": True,
            "drafts_excluded_by_store": True,
            "no_inventory_forged": True,
        },
    }


def _find_entry(snapshot: Mapping[str, Any], record: Mapping[str, Any]) -> dict[str, Any]:
    record_id = record.get("record_id")
    source = record.get("source")
    source_sha256 = source.get("sha256") if isinstance(source, Mapping) else None
    matches = [
        entry
        for entry in snapshot["entries"]
        if isinstance(entry, Mapping)
        and record_id == f"consensus.{entry.get('session_id')}"
        and source_sha256 == entry.get("draft_sha256")
    ]
    _require(len(matches) == 1, f"record {record.get('record_id')} does not have one exact committed entry")
    return dict(matches[0])


def _attachment_path(snapshot_root: Path, raw: Any, attachment_id: str) -> Path:
    if isinstance(raw, Mapping):
        raw = raw.get("relative_path") or raw.get("path") or raw.get("locator")
    return _safe_relative(snapshot_root, raw, f"attachment {attachment_id}")


def materialize_knowledge(
    plugin_root: Path,
    store_root: Path,
    record_id: str,
    snapshot_id: str | None = None,
) -> dict[str, Any]:
    """Read one exact, hash-verified committed consensus and its attachments."""

    root = _ensure_plugin_root(plugin_root)
    store = _ensure_external_store(root, store_root)
    snapshot, store_info = _load_snapshot(store, snapshot_id)
    _require(snapshot is not None, f"knowledge snapshot unavailable: {store_info.get('reason', store_info.get('status'))}")
    records = [record for record in snapshot["records"] if isinstance(record, Mapping) and record.get("record_id") == record_id]
    _require(len(records) == 1, f"record not found in the selected knowledge snapshot: {record_id}")
    record = dict(records[0])
    entry = _find_entry(snapshot, record)
    draft = entry.get("draft")
    _require(isinstance(draft, Mapping), f"record {record_id} has no committed draft")
    confirmation = entry.get("confirmation")
    _require(isinstance(confirmation, Mapping), f"record {record_id} has no confirmation")
    if entry.get("draft_sha256") is not None and confirmation.get("draft_sha256") is not None:
        _require(entry.get("draft_sha256") == confirmation.get("draft_sha256"), f"record {record_id} confirmation does not bind its draft")

    payload = record.get("payload")
    ref = payload.get("ref") if isinstance(payload, Mapping) else None
    if isinstance(ref, Mapping):
        record_consensus = ref.get("consensus")
        if record_consensus is None and isinstance(ref.get("draft"), Mapping):
            record_consensus = ref["draft"].get("consensus")
        if record_consensus is not None:
            _require(record_consensus == draft.get("consensus"), f"record {record_id} consensus does not match its committed draft")

    snapshot_root_raw = snapshot.get("snapshot_root")
    if snapshot_root_raw is None:
        snapshot_root_raw = Path(str(snapshot["manifest_path"])).parent.as_posix()
    snapshot_root = Path(str(snapshot_root_raw)).resolve()
    _require(snapshot_root.is_dir(), f"knowledge snapshot root is missing: {snapshot_root}")
    mapped_attachments = entry.get("attachments", {})
    _require(isinstance(mapped_attachments, Mapping), f"record {record_id} attachment map is invalid")
    attachment_rows: list[dict[str, Any]] = []
    draft_attachments = draft.get("attachments", [])
    _require(isinstance(draft_attachments, list), f"record {record_id} draft attachments are invalid")
    for raw_attachment in draft_attachments:
        _require(isinstance(raw_attachment, Mapping), f"record {record_id} attachment metadata is invalid")
        attachment_id = raw_attachment.get("attachment_id")
        _require(isinstance(attachment_id, str) and attachment_id, f"record {record_id} attachment_id is invalid")
        _require(attachment_id in mapped_attachments, f"record {record_id} attachment {attachment_id} is not persisted")
        expected_hash = raw_attachment.get("sha256")
        _require(isinstance(expected_hash, str) and SHA256_RE.fullmatch(expected_hash), f"record {record_id} attachment {attachment_id} SHA-256 is invalid")
        path = _attachment_path(snapshot_root, mapped_attachments[attachment_id], attachment_id)
        actual_hash = _sha256_file(path)
        _require(actual_hash == expected_hash, f"record {record_id} attachment {attachment_id} failed hash verification")
        attachment_rows.append({
            **dict(raw_attachment),
            "path": path.as_posix(),
            "relative_path": _relative(snapshot_root, path),
            "sha256": expected_hash,
            "verified": True,
        })
    _require(set(mapped_attachments) == {str(item.get("attachment_id")) for item in draft_attachments}, f"record {record_id} attachment map has unbound files")
    return {
        "contract": CONTRACT,
        "status": "ready",
        "snapshot_id": snapshot["snapshot_id"],
        "provider_id": snapshot["provider_id"],
        "record_id": record_id,
        "consensus": draft.get("consensus"),
        "owner_stage": draft.get("stage"),
        "applicable_stages": draft.get("applicable_stages", [draft.get("stage")]),
        "applicability": draft.get("applicability", []),
        "limitations": draft.get("limitations", []),
        "provenance": draft.get("provenance"),
        "evidence_refs": draft.get("evidence_refs", []),
        "unresolved_questions": draft.get("unresolved_questions", []),
        "language": draft.get("language"),
        "purpose_tags": draft.get("purpose_tags", []),
        "session_id": draft.get("session_id") or entry.get("session_id"),
        "attachments": attachment_rows,
        "record": record,
        "confirmation": dict(confirmation),
        "library": store_info,
        "evidence": {
            "index_path": str(snapshot["index_path"]),
            "manifest_path": str(snapshot["manifest_path"]),
            "provider_manifest_path": str(snapshot.get("provider_manifest_path")) if snapshot.get("provider_manifest_path") else None,
            "draft_path": str(entry.get("draft_path")) if entry.get("draft_path") else None,
            "confirmation_path": str(entry.get("confirmation_path")) if entry.get("confirmation_path") else None,
        },
        "guards": {
            "loaded_through_store": True,
            "exact_record_match": True,
            "attachment_hashes_verified": True,
            "unresolved_questions_preserved": True,
            "no_arbitrary_path_reads": True,
        },
    }


def _store_for_inspection(root: Path, store_root: Path | None) -> dict[str, Any]:
    if store_root is None:
        return {"status": "not-requested", "snapshot_id": None}
    store = _ensure_external_store(root, store_root)
    _, info = _load_snapshot(store, None)
    return info


def inspect_plugin(plugin_root: Path, store_root: Path | None = None) -> dict[str, Any]:
    """Inspect local package integrity and optional Library availability."""

    root = _ensure_plugin_root(plugin_root)
    required = _required_file_report(root)
    component = _load_component_report(root)
    content = _verify_content_manifest(root)
    try:
        _, public = _load_public_provider(root)
    except PluginSessionError as exc:
        public = {
            "status": "blocked",
            "manifest_path": (root / "catalog/provider-manifest.json").as_posix(),
            "index_path": (root / "catalog/records.jsonl").as_posix(),
            "error": str(exc),
        }
    tools = list_tools(root)
    library = _store_for_inspection(root, store_root)
    component_ok = component.get("status") == "installed" and not component.get("error_codes")
    blocking: list[str] = []
    if not component_ok:
        blocking.append("installed-components")
    if required["status"] != "complete":
        blocking.append("required-files")
    if public.get("status") != "ready":
        blocking.append("public-index")
    if content.get("status") == "blocked":
        blocking.append("content-manifest")
    if tools.get("status") != "ready":
        blocking.append("tool-catalog")
    if library.get("status") == "blocked":
        blocking.append("library-snapshot")
    return {
        "contract": INSPECTION_CONTRACT,
        "status": "ready" if not blocking else "blocked",
        "plugin_root": root.as_posix(),
        "component_report": component,
        "required_files": required,
        "content_manifest": content,
        "public_index": public,
        "library": library,
        "tools": tools,
        "blocking_checks": blocking,
        "guards": {
            "read_only": True,
            "production_preflight": False,
            "retrieval_receipt_created": False,
            "network_access": False,
            "governance_management": False,
        },
    }


__all__ = [
    "CONTRACT",
    "PluginSessionError",
    "inspect_plugin",
    "list_tools",
    "materialize_knowledge",
    "retrieve_knowledge",
]
