# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Resolve one private extension into the unchanged five-stage public workflow."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit

from packages.index_runtime import INDEX_CONTRACT, IndexProvider
from packages.index_runtime.utils import sha256_json


PERSONAL_EXTENSION_PROFILE_CONTRACT = "io.clayz.presentation.personal-extension-profile/1.0"
PROVIDER_MANIFEST_CONTRACT = "io.clayz.presentation.provider-manifest/1.0"
PERSONAL_EXTENSION_RUNTIME_CONTRACT = "io.clayz.presentation.personal-extension-runtime/1.1"
TASK_RESOURCE_SELECTION_CONTRACT = "io.clayz.presentation.task-resource-selection/1.0"
TASK_RESOURCE_SELECTION_V2_CONTRACT = "io.clayz.presentation.task-resource-selection/2.0"
TASK_SELECTION_V2_CONTRACT = TASK_RESOURCE_SELECTION_V2_CONTRACT
WORKFLOW_STAGES = ["logic", "copy", "art-direction", "output", "supervisor"]
TASK_MODES = {"public-core", "owner-personal"}
VISUAL_SOURCES = {"public-default", "personal-config"}
LIBRARY_STATUSES = {"unconfigured", "locator-pending-verification"}
UNIFIED_LIBRARY_STATUSES = {"unconfigured", "enabled-pending-verification", "locator-pending-verification"}
SUPPORTED_HOSTS = {"local", "chatgpt-personal"}
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")
SEMVER_PATTERN = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")


REPLACE_PATHS = {
    "locale.default",
    "theme.profile",
    "theme.source",
    "theme.master_path",
    "theme.slide_size",
    "theme.typography.primary_fonts",
    "theme.typography.font_validation",
    "theme.typography.prefer_even_point_sizes",
    "theme.typography.allow_fractional_point_sizes",
    "theme.typography.minimum_exception_policy",
    "layout.column_count",
    "layout.safe_margin_in",
    "layout.title_zone_height_in",
    "layout.footer_zone_height_in",
    "layout.minimum_gap_in",
    "layout.maximum_horizontal_nodes",
    "layout.cardification_policy",
    "delivery.default_profile",
}
APPEND_UNIQUE_PATHS = {
    "theme.layout_roles",
    "renderer.required_capabilities",
    "renderer.optional_capabilities",
    "renderer.preferred_backends",
    "renderer.target_applications",
}
STRICTER_ONLY_PATHS = {
    "theme.typography.body_minimum_pt",
    "theme.typography.minimum_audience_text_pt",
    "theme.typography.minimum_chart_text_pt",
    "theme.typography.fail_on_missing_primary_font",
    "references.require_human_admission",
    "renderer.require_final_reopen_render",
    "delivery.preserve_editability",
    "qa.require_source_traceability",
    "qa.require_copy_id_traceability",
    "qa.require_object_inventory",
    "qa.require_full_deck_render_review",
    "qa.automatic_scores_are_diagnostic_only",
    "qa.scatter_lines_require_semantic_meaning",
    "qa.labels_must_be_legible",
}


class PersonalExtensionError(ValueError):
    """Raised when a Personal Extension Profile violates the public contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PersonalExtensionError(message)


def _nonempty(value: Any, path: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{path} must be a non-empty string")
    return value


def _semver(value: Any, path: str) -> tuple[int, int, int]:
    text = _nonempty(value, path)
    _require(bool(SEMVER_PATTERN.fullmatch(text)), f"{path} must be a stable semantic version")
    return tuple(int(part) for part in text.split("."))  # type: ignore[return-value]


def _identifier(value: Any, path: str) -> str:
    text = _nonempty(value, path)
    _require(bool(ID_PATTERN.fullmatch(text)), f"{path} has invalid characters")
    return text


def _string_set(value: Any, path: str, *, allowed: set[str] | None = None) -> list[str]:
    _require(isinstance(value, list), f"{path} must be an array")
    _require(all(isinstance(item, str) and item for item in value), f"{path} must contain non-empty strings")
    _require(len(value) == len(set(value)), f"{path} must not contain duplicates")
    if allowed is not None:
        _require(set(value).issubset(allowed), f"{path} contains unsupported values")
    return list(value)


def _library_uri(value: Any, path: str, *, root: bool = False) -> str:
    uri = _nonempty(value, path)
    parsed = urlsplit(uri)
    _require(parsed.scheme == "library" and bool(parsed.netloc), f"{path} must use library://<namespace>/...")
    _require(not parsed.query and not parsed.fragment, f"{path} must not contain query or fragment")
    parts = PurePosixPath(parsed.path).parts
    _require(".." not in parts, f"{path} must not traverse above its logical root")
    if root:
        _require(uri.endswith("/"), f"{path} must end with /")
    return uri


def _provider_uri(value: Any, path: str, *, scheme: str) -> str:
    uri = _nonempty(value, path)
    parsed = urlsplit(uri)
    _require(parsed.scheme == scheme and bool(parsed.netloc), f"{path} must use {scheme}://<namespace>/...")
    _require(not parsed.query and not parsed.fragment, f"{path} must not contain query or fragment")
    _require(".." not in PurePosixPath(parsed.path).parts, f"{path} must not traverse above its logical root")
    return uri


def _policy_for(path: str) -> str | None:
    if path.startswith("theme.colors.") and len(path.split(".")) == 3:
        return "replace"
    if path in REPLACE_PATHS:
        return "replace"
    if path in APPEND_UNIQUE_PATHS:
        return "append_unique"
    if path in STRICTER_ONLY_PATHS:
        return "stricter_only"
    return None


def _get_path(value: Mapping[str, Any], path: str) -> Any:
    current: Any = value
    for part in path.split("."):
        _require(isinstance(current, Mapping) and part in current, f"override path is missing from core config: {path}")
        current = current[part]
    return current


def _set_path(value: dict[str, Any], path: str, replacement: Any) -> None:
    parts = path.split(".")
    current = value
    for part in parts[:-1]:
        nested = current.get(part)
        _require(isinstance(nested, dict), f"override parent is not an object: {path}")
        current = nested
    current[parts[-1]] = replacement


def _validate_binding(binding: Any, path: str, host: str) -> dict[str, str]:
    _require(isinstance(binding, Mapping), f"{path} must be an object")
    adapter = _nonempty(binding.get("adapter"), f"{path}.adapter")
    native_root = _nonempty(binding.get("root"), f"{path}.root")
    expected = "filesystem" if host == "local" else "host-library"
    _require(adapter == expected, f"{path}.adapter must be {expected} for {host}")
    if adapter == "host-library":
        pure = PurePosixPath(native_root)
        _require(not pure.is_absolute() and ".." not in pure.parts, f"{path}.root must be a safe host-library root name")
    return {"adapter": adapter, "root": native_root}


def validate_profile(profile: Mapping[str, Any], core_version: str) -> dict[str, Any]:
    """Validate and normalize one private authoring profile without reading its assets."""

    _require(isinstance(profile, Mapping), "profile must be an object")
    normalized = copy.deepcopy(dict(profile))
    _require(normalized.get("contract") == PERSONAL_EXTENSION_PROFILE_CONTRACT, "profile.contract is unsupported")
    _identifier(normalized.get("profile_id"), "profile.profile_id")
    _semver(normalized.get("profile_version"), "profile.profile_version")
    core = _semver(core_version, "core_version")

    compatibility = normalized.get("compatibility")
    _require(isinstance(compatibility, Mapping), "profile.compatibility must be an object")
    minimum = _semver(compatibility.get("minimum_core_version"), "profile.compatibility.minimum_core_version")
    maximum = _semver(compatibility.get("maximum_core_version_exclusive"), "profile.compatibility.maximum_core_version_exclusive")
    _require(minimum <= core < maximum, f"profile is not compatible with core {core_version}")

    overrides = normalized.get("overrides", [])
    _require(isinstance(overrides, list), "profile.overrides must be an array")
    seen_paths: set[str] = set()
    for index, override in enumerate(overrides):
        path = f"profile.overrides[{index}]"
        _require(isinstance(override, Mapping), f"{path} must be an object")
        field_path = _nonempty(override.get("path"), f"{path}.path")
        _require(field_path not in seen_paths, f"duplicate override path: {field_path}")
        seen_paths.add(field_path)
        expected_policy = _policy_for(field_path)
        _require(expected_policy is not None, f"sealed or unsupported override path: {field_path}")
        _require(override.get("policy") == expected_policy, f"{field_path} must use policy {expected_policy}")
        _require("value" in override, f"{path}.value is required")

    mounts = normalized.get("mounts", [])
    _require(isinstance(mounts, list), "profile.mounts must be an array")
    mount_ids: set[str] = set()
    logical_roots: set[str] = set()
    for index, mount in enumerate(mounts):
        path = f"profile.mounts[{index}]"
        _require(isinstance(mount, Mapping), f"{path} must be an object")
        mount_id = _identifier(mount.get("mount_id"), f"{path}.mount_id")
        logical_root = _library_uri(mount.get("logical_root"), f"{path}.logical_root", root=True)
        _require(mount_id not in mount_ids, f"duplicate mount_id: {mount_id}")
        _require(logical_root not in logical_roots, f"duplicate logical_root: {logical_root}")
        mount_ids.add(mount_id)
        logical_roots.add(logical_root)
        bindings = mount.get("bindings")
        _require(isinstance(bindings, Mapping), f"{path}.bindings must be an object")
        _require(set(bindings) == SUPPORTED_HOSTS, f"{path}.bindings must define local and chatgpt-personal")
        for host in sorted(SUPPORTED_HOSTS):
            _validate_binding(bindings[host], f"{path}.bindings.{host}", host)

    providers = normalized.get("providers", [])
    _require(isinstance(providers, list), "profile.providers must be an array")
    provider_ids: set[str] = set()
    for index, provider in enumerate(providers):
        path = f"profile.providers[{index}]"
        _require(isinstance(provider, Mapping), f"{path} must be an object")
        provider_id = _identifier(provider.get("provider_id"), f"{path}.provider_id")
        _require(provider_id not in provider_ids, f"duplicate provider_id: {provider_id}")
        provider_ids.add(provider_id)
        mount_id = _identifier(provider.get("mount_id"), f"{path}.mount_id")
        _require(mount_id in mount_ids, f"{path}.mount_id does not name a declared mount")
        _library_uri(provider.get("manifest_uri"), f"{path}.manifest_uri")
        _require(isinstance(provider.get("required"), bool), f"{path}.required must be boolean")
        _string_set(provider.get("stages", []), f"{path}.stages", allowed=set(WORKFLOW_STAGES))
    return normalized


def validate_provider_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one public-bundle or owner-private provider snapshot."""

    _require(isinstance(manifest, Mapping), "provider manifest must be an object")
    normalized = copy.deepcopy(dict(manifest))
    normalized.pop("$schema", None)
    _require(normalized.get("contract") == PROVIDER_MANIFEST_CONTRACT, "provider manifest contract is unsupported")
    _identifier(normalized.get("provider_id"), "provider.provider_id")
    visibility = normalized.get("visibility")
    _require(visibility in {"public", "owner-private"}, "provider.visibility is unsupported")
    expected_context = "public-open-source" if visibility == "public" else "private-runtime"
    _require(normalized.get("rights_context") == expected_context, f"provider.rights_context must be {expected_context}")
    _require(normalized.get("human_admission_required") is True, "provider.human_admission_required must be true")
    _string_set(normalized.get("allowed_hosts"), "provider.allowed_hosts", allowed=SUPPORTED_HOSTS)
    index = normalized.get("index")
    _require(isinstance(index, Mapping), "provider.index must be an object")
    _require(index.get("record_contract") == INDEX_CONTRACT, "provider.index.record_contract is unsupported")
    _require(index.get("format") == "jsonl", "provider.index.format must be jsonl")
    if visibility == "public":
        _provider_uri(index.get("uri"), "provider.index.uri", scheme="bundle")
        _require(index.get("refresh_policy") == "immutable-release", "public provider index must be immutable per release")
        expected_methods = {
            "continuous_learning": "deferred",
            "community_aggregation": "deferred",
            "automatic_update": "deferred",
            "cross_source_fusion": "deferred",
        }
        _require(normalized.get("evolution_methods") == expected_methods, "public provider evolution methods must remain explicitly deferred")
    else:
        _library_uri(index.get("uri"), "provider.index.uri")
        _require(index.get("refresh_policy") == "read-once-lock-for-run", "private provider index refresh policy is unsupported")
        _require("evolution_methods" not in normalized, "private provider must not declare public evolution methods")
    snapshot = index.get("snapshot")
    _require(isinstance(snapshot, Mapping), "provider.index.snapshot must be an object")
    _require(snapshot.get("provider_id") == normalized.get("provider_id"), "provider snapshot identity mismatch")
    digest = _nonempty(snapshot.get("digest"), "provider.index.snapshot.digest")
    _require(bool(re.fullmatch(r"[0-9a-f]{64}", digest)), "provider.index.snapshot.digest must be lowercase SHA-256")
    _require(isinstance(snapshot.get("record_count"), int) and snapshot["record_count"] >= 0, "provider.index.snapshot.record_count is invalid")
    return normalized


def build_provider_manifest(
    provider: IndexProvider,
    *,
    index_uri: str,
    visibility: str = "owner-private",
    allowed_hosts: Sequence[str] = ("local", "chatgpt-personal"),
) -> dict[str, Any]:
    """Create a manifest for an already admitted public or private IndexProvider."""

    _require(visibility in {"public", "owner-private"}, "visibility is unsupported")
    _provider_uri(index_uri, "index_uri", scheme="bundle" if visibility == "public" else "library")
    hosts = sorted(set(allowed_hosts))
    _string_set(hosts, "allowed_hosts", allowed=SUPPORTED_HOSTS)
    manifest = {
        "contract": PROVIDER_MANIFEST_CONTRACT,
        "provider_id": provider.provider_id,
        "visibility": visibility,
        "rights_context": "public-open-source" if visibility == "public" else "private-runtime",
        "human_admission_required": True,
        "allowed_hosts": hosts,
        "index": {
            "record_contract": INDEX_CONTRACT,
            "format": "jsonl",
            "uri": index_uri,
            "refresh_policy": "immutable-release" if visibility == "public" else "read-once-lock-for-run",
            "snapshot": provider.snapshot(),
        },
    }
    if visibility == "public":
        manifest["evolution_methods"] = {
            "continuous_learning": "deferred",
            "community_aggregation": "deferred",
            "automatic_update": "deferred",
            "cross_source_fusion": "deferred",
        }
    return validate_provider_manifest(manifest)


def _apply_override(config: dict[str, Any], override: Mapping[str, Any]) -> Any:
    path = str(override["path"])
    policy = str(override["policy"])
    current = _get_path(config, path)
    value = copy.deepcopy(override["value"])
    if policy == "replace":
        replacement = value
    elif policy == "append_unique":
        _require(isinstance(current, list) and isinstance(value, list), f"{path}: append_unique requires arrays")
        _require(all(isinstance(item, str) and item for item in value), f"{path}: append_unique values must be strings")
        replacement = list(current)
        for item in value:
            if item not in replacement:
                replacement.append(item)
    else:
        if isinstance(current, bool):
            _require(isinstance(value, bool) and (current or value), f"{path}: stricter_only cannot weaken true to false")
            replacement = value
        elif isinstance(current, (int, float)) and not isinstance(current, bool):
            _require(isinstance(value, (int, float)) and not isinstance(value, bool) and value >= current, f"{path}: stricter_only cannot decrease the value")
            replacement = value
        else:
            _require(False, f"{path}: unsupported stricter_only value type")
            replacement = value
    _set_path(config, path, replacement)
    return replacement


def _mount_runtime(profile: Mapping[str, Any], host: str) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for mount in profile.get("mounts", []):
        binding = _validate_binding(mount["bindings"][host], f"mount {mount['mount_id']} binding", host)
        result.append({
            "mount_id": mount["mount_id"],
            "logical_root": mount["logical_root"],
            "adapter": binding["adapter"],
            "root": binding["root"],
        })
    return sorted(result, key=lambda item: item["mount_id"])


def resolve_logical_uri(uri: str, mount: Mapping[str, str], *, environment: Mapping[str, str] | None = None) -> str:
    """Resolve a logical library URI only at the selected host boundary."""

    logical_root = _library_uri(mount.get("logical_root"), "mount.logical_root", root=True)
    target = _library_uri(uri, "uri")
    _require(target.startswith(logical_root), f"uri is outside mount {mount.get('mount_id')}")
    relative = target[len(logical_root):]
    relative_parts = PurePosixPath(relative).parts
    _require(".." not in relative_parts, "uri must not traverse above its mount")
    adapter = mount.get("adapter")
    root = _nonempty(mount.get("root"), "mount.root")
    if adapter == "host-library":
        return PurePosixPath(root, *relative_parts).as_posix()
    _require(adapter == "filesystem", "mount.adapter is unsupported")
    env = dict(os.environ if environment is None else environment)
    match = re.fullmatch(r"\$\{([A-Z][A-Z0-9_]*)\}", root)
    if match:
        variable = match.group(1)
        _require(variable in env and bool(env[variable]), f"missing filesystem mount variable {variable}")
        root = env[variable]
    return str(Path(root).joinpath(*relative_parts))


def resolve_personal_extension(
    base_config: Mapping[str, Any],
    profile: Mapping[str, Any],
    *,
    host: str,
    public_provider_manifests: Sequence[Mapping[str, Any]],
    provider_manifests: Sequence[Mapping[str, Any]],
    config_path: str = "config/personal-extension-resolved.json",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Compose a host-specific runtime without changing the five-stage workflow."""

    _require(host in SUPPORTED_HOSTS, f"unsupported host: {host}")
    _require(isinstance(base_config, Mapping), "base config must be an object")
    core_version = _nonempty(base_config.get("identity", {}).get("version") if isinstance(base_config.get("identity"), Mapping) else None, "base_config.identity.version")
    normalized_profile = validate_profile(profile, core_version)
    public_manifests = [validate_provider_manifest(value) for value in public_provider_manifests]
    _require(len(public_manifests) == 1, "exactly one public provider manifest is required")
    public_manifest = public_manifests[0]
    _require(public_manifest["visibility"] == "public", "public provider manifest must have public visibility")
    manifests = [validate_provider_manifest(value) for value in provider_manifests]
    _require(all(value["visibility"] == "owner-private" for value in manifests), "profile providers must be owner-private")
    manifests_by_id = {manifest["provider_id"]: manifest for manifest in manifests}
    _require(len(manifests_by_id) == len(manifests), "provider manifests must have unique provider_id values")
    declared_provider_ids = {provider["provider_id"] for provider in normalized_profile.get("providers", [])}
    _require(set(manifests_by_id) == declared_provider_ids, "provider manifests must match the profile provider list exactly")

    resolved = copy.deepcopy(dict(base_config))
    origin_map: list[dict[str, Any]] = []
    for override in normalized_profile.get("overrides", []):
        replacement = _apply_override(resolved, override)
        origin_map.append({
            "path": override["path"],
            "policy": override["policy"],
            "source": f"profile:{normalized_profile['profile_id']}",
            "resolved_value_sha256": sha256_json(replacement),
        })

    if resolved.get("theme", {}).get("source") == "user-master":
        master = resolved.get("theme", {}).get("master_path")
        _library_uri(master, "resolved_config.theme.master_path")
    if resolved.get("locale", {}).get("default") not in resolved.get("locale", {}).get("supported", []):
        raise PersonalExtensionError("resolved locale.default must remain supported")
    if resolved.get("delivery", {}).get("default_profile") not in resolved.get("delivery", {}).get("profiles", {}):
        raise PersonalExtensionError("resolved delivery.default_profile must name an existing profile")

    mounts = [{
        "mount_id": "public-library",
        "logical_root": "bundle://public-library/",
        "adapter": "bundle",
        "root": ".",
    }, *_mount_runtime(normalized_profile, host)]
    mounts_by_id = {mount["mount_id"]: mount for mount in mounts}
    providers: list[dict[str, Any]] = [{
        "provider_id": public_manifest["provider_id"],
        "visibility": "public",
        "manifest_uri": "bundle://public-library/catalog/provider-manifest.json",
        "manifest_contract": PROVIDER_MANIFEST_CONTRACT,
        "mount_id": "public-library",
        "required": True,
        "stages": WORKFLOW_STAGES,
        "snapshot_policy": "immutable-release",
        "index_snapshot": public_manifest["index"]["snapshot"],
    }]
    for declaration in normalized_profile.get("providers", []):
        provider_id = declaration["provider_id"]
        manifest = manifests_by_id.get(provider_id)
        _require(manifest is not None, f"missing provider manifest for {provider_id}")
        _require(host in manifest["allowed_hosts"], f"provider {provider_id} is not allowed on {host}")
        mount = mounts_by_id[declaration["mount_id"]]
        _require(declaration["manifest_uri"].startswith(mount["logical_root"]), f"provider {provider_id} manifest URI is outside its mount")
        _require(manifest["index"]["uri"].startswith(mount["logical_root"]), f"provider {provider_id} index URI is outside its mount")
        providers.append({
            "provider_id": provider_id,
            "visibility": "owner-private",
            "manifest_uri": declaration["manifest_uri"],
            "manifest_contract": PROVIDER_MANIFEST_CONTRACT,
            "mount_id": declaration["mount_id"],
            "required": declaration["required"],
            "stages": declaration["stages"],
            "snapshot_policy": "read-once-lock-for-run",
        })

    config_sha256 = sha256_json(resolved)
    runtime: dict[str, Any] = {
        "contract": PERSONAL_EXTENSION_RUNTIME_CONTRACT,
        "core": {
            "name": "clayz-presentation-skills",
            "version": core_version,
            "workflow_stages": WORKFLOW_STAGES,
        },
        "extension": {
            "enabled": True,
            "profile_id": normalized_profile["profile_id"],
            "profile_version": normalized_profile["profile_version"],
            "profile_sha256": sha256_json(normalized_profile),
            "host": host,
            "decision_point": "before-logic",
        },
        "config": {
            "path": config_path,
            "sha256": config_sha256,
            "format": "json",
        },
        "mounts": mounts,
        "providers": sorted(providers, key=lambda item: item["provider_id"]),
        "resource_inventory": {
            "contract": "io.clayz.presentation.resource-inventory-policy/1.0",
            "artifact": "ppt-resource-inventory.json",
            "finalizer_script": "scripts/finalize_resource_inventory.py",
            "evidence_contract": "packages/contracts/resource-inventory.schema.json",
            "required_scan_scopes": [
                "plugin-runtime", "task-inputs", "owner-library", "public-index",
                "brand-assets", "host-capabilities", "font-environment",
            ],
            "user_brief_before_logic": True,
            "final_usage_reconciliation": True,
            "fail_closed": True,
        },
        "index_execution": {
            "contract": "io.clayz.presentation.index-execution-policy/1.0",
            "mode": "first-class-stage-gated",
            "task_provider_id": "task-private-learning",
            "source_manifest": "runtime-input://owner-learning-manifest",
            "source_manifest_contract": "io.clayz.presentation.owner-learning-sources/1.0",
            "source_manifest_required": True,
            "materializer_script": "scripts/materialize_owner_index.py",
            "evidence_contract": "packages/contracts/index-execution-evidence.schema.json",
            "fail_closed_stages": WORKFLOW_STAGES,
            "required_receipt_stages": WORKFLOW_STAGES,
        },
        "version_learning": {
            "contract": "io.clayz.presentation.version-private-learning-policy/1.0",
            "mode": "immutable-source-revisions",
            "state_root": "runtime-input://owner-private-version-learning-state",
            "bootstrap_script": "scripts/bootstrap_owner_learning.py",
            "audit_contract": "io.clayz.presentation.version-private-learning-audit/1.0",
            "audit_schema": "packages/contracts/version-private-learning-audit.schema.json",
            "required_knowledge_kinds": ["private-knowledge", "template", "standard", "method"],
            "reuse_requires_hash_match": True,
            "source_drift_fails_closed": True,
            "fail_closed": True,
        },
        "origin_map": sorted(origin_map, key=lambda item: item["path"]),
        "guards": {
            "single_public_workflow": True,
            "no_sixth_stage": True,
            "public_fallback_when_optional_provider_unavailable": True,
            "required_private_provider_fails_closed": True,
            "provider_snapshot_locked_per_run": True,
            "public_material_evolution_methods_deferred": True,
            "resource_inventory_required": True,
            "resource_brief_before_logic": True,
            "resource_usage_reconciliation_required": True,
            "first_class_index_required": True,
            "stage_receipts_fail_closed": True,
            "latest_version_guard_required": True,
            "version_private_learning_required": True,
            "one_learning_run_per_source_revision": True,
            "source_drift_fails_closed": True,
        },
    }
    runtime["lock"] = {"algorithm": "sha256", "digest": sha256_json(runtime)}
    return resolved, validate_personal_extension_runtime(runtime, resolved_config=resolved)


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _file_json(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.resolve().read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PersonalExtensionError(f"{label} cannot be read as UTF-8 JSON: {exc}") from exc
    _require(isinstance(value, Mapping), f"{label} must be a JSON object")
    return copy.deepcopy(dict(value)), raw


def _validate_pack_artifact(bundle_root: Path, relative: str, path: Path) -> None:
    """Check a source against an installed pack lock when one is present."""
    lock_path = bundle_root.resolve() / "runtime" / "runtime-lock.json"
    if not lock_path.is_file():
        return
    lock, _ = _file_json(lock_path, "runtime pack lock")
    hashes = lock.get("artifact_sha256")
    if hashes is None:
        return  # development/local lock formats before artifact hashes remain usable
    _require(isinstance(hashes, Mapping), "runtime pack lock artifact_sha256 must be an object")
    expected = hashes.get(relative)
    _require(isinstance(expected, str) and bool(re.fullmatch(r"[0-9a-f]{64}", expected)),
             f"runtime pack lock has no valid hash for {relative}")
    _require(hashlib.sha256(path.resolve().read_bytes()).hexdigest() == expected,
             f"installed artifact hash mismatch: {relative}")


def _private_runtime_source(bundle_root: Path) -> tuple[Path, dict[str, Any], bytes] | None:
    """Read and validate the original bundled private resolved config, if installed."""
    root = bundle_root.resolve()
    runtime_path = root / "runtime" / "personal-extension.json"
    if not runtime_path.is_file():
        return None
    lock_path = root / "runtime" / "runtime-lock.json"
    _require(lock_path.is_file(), "installed Personal Runtime requires runtime/runtime-lock.json")
    runtime, _ = _file_json(runtime_path, "Personal Extension Runtime")
    lock, _ = _file_json(lock_path, "runtime pack lock")
    config_binding = runtime.get("config")
    _require(isinstance(config_binding, Mapping), "Personal Runtime config binding is missing")
    relative = config_binding.get("path")
    _require(isinstance(relative, str) and relative and not PurePosixPath(relative).is_absolute() and ".." not in PurePosixPath(relative).parts,
             "Personal Runtime config path is unsafe")
    source_path = (root / Path(*PurePosixPath(relative).parts)).resolve()
    try:
        source_path.relative_to(root)
    except ValueError as exc:
        raise PersonalExtensionError("Personal Runtime config escapes the bundle") from exc
    private_config, raw = _file_json(source_path, "private resolved config")
    try:
        validate_personal_extension_runtime(runtime, resolved_config=private_config, runtime_pack_lock=lock)
    except (PersonalExtensionError, ValueError) as exc:
        raise PersonalExtensionError(f"installed Personal Runtime validation failed: {exc}") from exc
    _validate_pack_artifact(root, relative, source_path)
    return source_path, private_config, raw


def build_task_config(
    base_config: Mapping[str, Any], visual_config: Mapping[str, Any], *,
    mode: str, visual_source: str, private_runtime_present: bool = False,
) -> dict[str, Any]:
    """Derive task config by replacing only ``theme`` and required private capability."""
    _require(isinstance(mode, str) and mode in TASK_MODES, f"mode must be one of {sorted(TASK_MODES)}")
    _require(isinstance(visual_source, str) and visual_source in VISUAL_SOURCES,
             f"visual_source must be one of {sorted(VISUAL_SOURCES)}")
    _require(isinstance(base_config, Mapping), "base_config must be an object")
    _require(isinstance(visual_config, Mapping), "visual_config must be an object")
    _require(isinstance(base_config.get("theme"), Mapping), "base_config.theme must be an object")
    _require(isinstance(visual_config.get("theme"), Mapping), "visual_config.theme must be an object")
    result = copy.deepcopy(dict(base_config))
    result["theme"] = copy.deepcopy(dict(visual_config["theme"]))
    theme = result["theme"]
    needs_master = theme.get("source") == "user-master" or (
        isinstance(theme.get("master_path"), str) and bool(theme["master_path"].strip())
    )
    if needs_master or (mode == "owner-personal" and not private_runtime_present):
        renderer = result.get("renderer")
        _require(isinstance(renderer, dict), "task config requires renderer settings")
        required = renderer.get("required_capabilities")
        _require(isinstance(required, list) and all(isinstance(item, str) and item for item in required),
                 "task config requires renderer.required_capabilities")
        if needs_master:
            for capability in ("master-preservation", "layout-inheritance", "east-asian-font-name"):
                if capability not in required:
                    required.append(capability)
        if mode == "owner-personal" and not private_runtime_present and "owner-private-library" not in required:
            required.append("owner-private-library")
    return result


def prepare_task_selection(
    bundle_root: Path | str, mode: str, visual_source: str, config_path: Path | str,
    *, library_locator: str | None = None, parent_selection_sha256: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Resolve observed bundle sources and return ``(task_config, selection)``."""
    root = Path(bundle_root).resolve()
    default_path = root / "config" / "default.json"
    default_config, default_raw = _file_json(default_path, "bundled public config")
    _validate_pack_artifact(root, "config/default.json", default_path)
    private = _private_runtime_source(root)
    if mode == "owner-personal" and private is not None:
        base_path, base_config, base_raw = private
    else:
        base_path, base_config, base_raw = default_path, default_config, default_raw
    if visual_source == "personal-config":
        _require(private is not None, "personal-config visual source requires a validated Personal Runtime")
        visual_path, visual_config, visual_raw = private
    else:
        visual_path, visual_config, visual_raw = default_path, default_config, default_raw
    task_config = build_task_config(
        base_config, visual_config, mode=mode, visual_source=visual_source,
        private_runtime_present=private is not None and mode == "owner-personal",
    )
    task_raw = _canonical_bytes(task_config)
    selection = create_task_selection(
        mode, visual_source,
        base_config_sha256=hashlib.sha256(base_raw).hexdigest(),
        visual_config_sha256=hashlib.sha256(visual_raw).hexdigest(),
        config_sha256=hashlib.sha256(task_raw).hexdigest(),
        config_path=config_path,
        library_locator=library_locator,
        parent_selection_sha256=parent_selection_sha256,
    )
    _require(base_path.is_file() and visual_path.is_file(), "selected config source is unavailable")
    return task_config, selection


def create_task_selection(
    mode: str, visual_source: str, *, base_config_sha256: str, visual_config_sha256: str,
    config_sha256: str, config_path: str | Path, library_locator: str | None = None,
    library_status: str | None = None, parent_selection_sha256: str | None = None,
) -> dict[str, Any]:
    """Create the task-local resource selection envelope without writing files."""
    _require(isinstance(mode, str) and mode in TASK_MODES, f"mode must be one of {sorted(TASK_MODES)}")
    _require(isinstance(visual_source, str) and visual_source in VISUAL_SOURCES,
             f"visual_source must be one of {sorted(VISUAL_SOURCES)}")
    for label, value in (("base_config_sha256", base_config_sha256), ("visual_config_sha256", visual_config_sha256), ("config_sha256", config_sha256)):
        _require(isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{64}", value)), f"{label} must be lowercase SHA-256")
    path = Path(config_path).resolve()
    _require(path.is_absolute(), "config_path must be absolute")
    if library_locator is not None:
        _require(isinstance(library_locator, str) and bool(library_locator.strip()), "library_locator must be non-empty when supplied")
        library_locator = library_locator.strip()
    expected_status = "locator-pending-verification" if library_locator is not None else "unconfigured"
    if library_status is None:
        library_status = expected_status
    _require(library_status in LIBRARY_STATUSES, "library_status is unsupported")
    _require(library_status == expected_status, "library_status does not match library_locator")
    _require(parent_selection_sha256 is None or bool(re.fullmatch(r"[0-9a-f]{64}", str(parent_selection_sha256))),
             "parent_selection_sha256 must be null or lowercase SHA-256")
    selection: dict[str, Any] = {
        "contract": TASK_RESOURCE_SELECTION_CONTRACT,
        "mode": mode,
        "visual_source": visual_source,
        "library_status": library_status,
        "base_config_sha256": base_config_sha256,
        "visual_config_sha256": visual_config_sha256,
        "config_sha256": config_sha256,
        "config_path": str(path),
        "parent_selection_sha256": parent_selection_sha256,
    }
    if library_locator is not None:
        selection["library_locator"] = library_locator
    selection["selection_sha256"] = sha256_json(selection)
    return selection


build_task_selection = create_task_selection


def canonical_task_selection_sha256(selection: Mapping[str, Any]) -> str:
    _require(isinstance(selection, Mapping), "task selection must be an object")
    body = dict(selection)
    body.pop("selection_sha256", None)
    return sha256_json(body)


def _validate_task_selection_v1(
    selection_path: Path | str, config_path: Path | str, bundle_root: Path | str,
    expected_mode: str | None = None,
) -> dict[str, Any]:
    """Validate one saved selection and its derived task config against observed files."""
    selection_file = Path(selection_path).resolve()
    selection, _ = _file_json(selection_file, "task resource selection")
    required = {
        "contract", "mode", "visual_source", "library_status", "base_config_sha256",
        "visual_config_sha256", "config_sha256", "config_path", "parent_selection_sha256", "selection_sha256",
    }
    _require(set(selection).issubset(required | {"library_locator"}) and required.issubset(selection),
             "task resource selection has unsupported or missing fields")
    _require(selection.get("contract") == TASK_RESOURCE_SELECTION_CONTRACT,
             f"selection.contract must be {TASK_RESOURCE_SELECTION_CONTRACT}")
    mode, visual = selection.get("mode"), selection.get("visual_source")
    _require(isinstance(mode, str) and mode in TASK_MODES, "selection.mode is unsupported")
    _require(isinstance(visual, str) and visual in VISUAL_SOURCES, "selection.visual_source is unsupported")
    if expected_mode is not None:
        _require(mode == expected_mode, "selection.mode does not match expected_mode")
    locator = selection.get("library_locator")
    if locator is not None:
        _require(isinstance(locator, str) and bool(locator.strip()), "selection.library_locator is invalid")
    expected_status = "locator-pending-verification" if locator is not None else "unconfigured"
    _require(selection.get("library_status") == expected_status, "selection.library_status does not match locator")
    _require(selection.get("parent_selection_sha256") is None or _sha256_text(selection.get("parent_selection_sha256")),
             "selection.parent_selection_sha256 is invalid")
    _require(selection.get("selection_sha256") == canonical_task_selection_sha256(selection),
             "selection.selection_sha256 does not match canonical content")
    requested_config = Path(config_path).resolve()
    stored_config = selection.get("config_path")
    _require(isinstance(stored_config, str) and Path(stored_config).is_absolute() and Path(stored_config).resolve() == requested_config,
             "selection.config_path does not match the observed config path")
    task_config, config_raw = _file_json(requested_config, "task config")
    _require(config_raw == _canonical_bytes(task_config), "task config must use canonical JSON bytes plus newline")
    _require(hashlib.sha256(config_raw).hexdigest() == selection.get("config_sha256"),
             "selection.config_sha256 does not match task config bytes")

    root = Path(bundle_root).resolve()
    default_path = root / "config" / "default.json"
    default_config, default_raw = _file_json(default_path, "bundled public config")
    _validate_pack_artifact(root, "config/default.json", default_path)
    private = _private_runtime_source(root)
    if mode == "owner-personal" and private is not None:
        base_path, base_config, base_raw = private
    else:
        base_path, base_config, base_raw = default_path, default_config, default_raw
    if visual == "personal-config":
        _require(private is not None, "personal-config visual source requires a validated Personal Runtime")
        visual_path, visual_config, visual_raw = private
    else:
        visual_path, visual_config, visual_raw = default_path, default_config, default_raw
    _require(hashlib.sha256(base_raw).hexdigest() == selection.get("base_config_sha256"),
             "selection.base_config_sha256 does not match its observed source")
    _require(hashlib.sha256(visual_raw).hexdigest() == selection.get("visual_config_sha256"),
             "selection.visual_config_sha256 does not match its observed source")
    expected_config = build_task_config(base_config, visual_config, mode=mode, visual_source=visual,
                                        private_runtime_present=private is not None and mode == "owner-personal")
    _require(task_config == expected_config, "task config is not derived from the selected base and visual config")
    # Keep these locals intentionally tied to observed paths; no host locator is resolved here.
    _require(base_path.is_file() and visual_path.is_file(), "selected config source is unavailable")
    return selection


_UNIFIED_FIELDS = frozenset({
    "contract", "workflow", "layers", "preferences", "library_enabled", "library_status",
    "library_locator", "base_config_sha256", "config_sha256", "config_path",
    "parent_selection_sha256", "selection_sha256",
})
_LAYER_FIELDS = frozenset({"source_path", "source_sha256", "snapshot"})
_SNAPSHOT_FIELDS = frozenset({"config", "preferences"})
_LAYER_CONFIG_KEYS = frozenset({"theme", "layout", "locale"})


def _merge_values(base: Any, overlay: Any) -> Any:
    if isinstance(base, Mapping) and isinstance(overlay, Mapping):
        merged = copy.deepcopy(dict(base))
        for key, value in overlay.items():
            merged[key] = _merge_values(merged[key], value) if key in merged else copy.deepcopy(value)
        return merged
    return copy.deepcopy(overlay)


def _layer_snapshot(value: Mapping[str, Any], label: str) -> tuple[dict[str, Any], str | None]:
    _require(isinstance(value, Mapping), f"{label} must be an object")
    if "config" in value:
        config = value.get("config")
        _require(isinstance(config, Mapping), f"{label}.config must be an object")
        unknown = set(config) - _LAYER_CONFIG_KEYS
        _require(not unknown, f"{label}.config contains unsupported keys: {sorted(unknown)}")
        source_config = config
    else:
        # Full resolved configs are accepted as input, but only these three
        # user-facing settings are admitted into the reusable layer.
        source_config = {key: value[key] for key in _LAYER_CONFIG_KEYS if key in value}
    normalized_config: dict[str, Any] = {}
    for key, section in source_config.items():
        _require(isinstance(section, Mapping), f"{label}.config.{key} must be an object")
        normalized_config[key] = copy.deepcopy(dict(section))
    preferences = value.get("preferences", {})
    _require(isinstance(preferences, Mapping), f"{label}.preferences must be an object")
    locator = value.get("library_locator")
    if locator is not None:
        _require(isinstance(locator, str) and bool(locator.strip()), f"{label}.library_locator must be non-empty")
        locator = locator.strip()
    return {"config": normalized_config, "preferences": copy.deepcopy(dict(preferences))}, locator


def _layer_file(path: Path | str, label: str) -> tuple[dict[str, Any], str | None]:
    source_path = Path(path).resolve()
    value, raw = _file_json(source_path, label)
    snapshot, locator = _layer_snapshot(value, label)
    return {
        "source_path": str(source_path),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "snapshot": snapshot,
    }, locator


def _empty_layer() -> dict[str, Any]:
    return {"source_path": None, "source_sha256": None, "snapshot": {"config": {}, "preferences": {}}}


def _default_layer(path: Path, config: Mapping[str, Any], raw: bytes) -> dict[str, Any]:
    return {
        "source_path": str(path.resolve()),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "snapshot": {
            "config": {key: copy.deepcopy(dict(config[key])) for key in _LAYER_CONFIG_KEYS if isinstance(config.get(key), Mapping)},
            "preferences": {},
        },
    }


def _personal_layer_file(bundle_root: Path, path: Path | str, label: str) -> tuple[dict[str, Any], str | None]:
    """Use the installed runtime validator when the original resolved file is selected."""
    candidate = Path(path).resolve()
    runtime = bundle_root.resolve() / "runtime" / "personal-extension.json"
    if runtime.is_file():
        private = _private_runtime_source(bundle_root)
        if private is not None and private[0] == candidate:
            return _layer_file(private[0], label)
    return _layer_file(candidate, label)


def _validate_layer(layer: Any, label: str, *, allow_missing: bool = True, verify_source: bool = False) -> dict[str, Any]:
    _require(isinstance(layer, Mapping) and set(layer) == _LAYER_FIELDS, f"{label} has invalid fields")
    source_path, source_sha = layer.get("source_path"), layer.get("source_sha256")
    _require(source_path is None or (isinstance(source_path, str) and Path(source_path).is_absolute()),
             f"{label}.source_path must be null or absolute")
    _require(source_sha is None or _sha256_text(source_sha), f"{label}.source_sha256 is invalid")
    _require((source_path is None) == (source_sha is None), f"{label} source path/hash must be both null or present")
    snapshot = layer.get("snapshot")
    _require(isinstance(snapshot, Mapping) and set(snapshot) == _SNAPSHOT_FIELDS, f"{label}.snapshot has invalid fields")
    config = snapshot.get("config")
    _require(isinstance(config, Mapping) and set(config).issubset(_LAYER_CONFIG_KEYS), f"{label}.snapshot.config is invalid")
    for key, section in config.items():
        _require(isinstance(section, Mapping), f"{label}.snapshot.config.{key} must be an object")
    preferences = snapshot.get("preferences")
    _require(isinstance(preferences, Mapping), f"{label}.snapshot.preferences must be an object")
    normalized = {
        "source_path": source_path,
        "source_sha256": source_sha,
        "snapshot": {"config": copy.deepcopy(dict(config)), "preferences": copy.deepcopy(dict(preferences))},
    }
    if source_path is not None and verify_source:
        path = Path(source_path).resolve()
        if path.is_file():
            actual, raw = _file_json(path, label)
            _require(hashlib.sha256(raw).hexdigest() == source_sha, f"{label} source bytes changed")
            actual_snapshot, _ = _layer_snapshot(actual, label)
            _require(actual_snapshot == normalized["snapshot"], f"{label} snapshot no longer matches source")
        elif not allow_missing:
            raise PersonalExtensionError(f"{label} source is unavailable")
    return normalized


def _master_requirements(config: dict[str, Any]) -> None:
    theme = config.get("theme")
    needs_master = isinstance(theme, Mapping) and (
        theme.get("source") == "user-master"
        or (isinstance(theme.get("master_path"), str) and bool(theme["master_path"].strip()))
    )
    if not needs_master:
        return
    renderer = config.get("renderer")
    _require(isinstance(renderer, dict), "master-backed task config requires renderer settings")
    required = renderer.get("required_capabilities")
    _require(isinstance(required, list) and all(isinstance(item, str) and item for item in required),
             "master-backed task config requires renderer.required_capabilities")
    for capability in ("master-preservation", "layout-inheritance", "east-asian-font-name"):
        if capability not in required:
            required.append(capability)


def _build_unified_config(default_config: Mapping[str, Any], personal: Mapping[str, Any], task: Mapping[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(dict(default_config))
    for layer in (personal, task):
        snapshot = layer.get("snapshot", {}) if isinstance(layer, Mapping) else {}
        sections = snapshot.get("config", {}) if isinstance(snapshot, Mapping) else {}
        if isinstance(sections, Mapping):
            for key, value in sections.items():
                result[key] = _merge_values(result.get(key, {}), value)
    _master_requirements(result)
    return result


def _unified_library_state(enabled: bool, locator: str | None) -> str:
    _require(type(enabled) is bool, "library_enabled must be a boolean")
    if not enabled:
        _require(locator is None, "disabled Library selection cannot retain a locator")
        return "unconfigured"
    return "locator-pending-verification" if locator else "enabled-pending-verification"


def _validate_unified_selection(
    selection_path: Path | str, selection: Mapping[str, Any], config_path: Path | str,
    bundle_root: Path | str, expected_mode: str | None = None,
) -> dict[str, Any]:
    _require(expected_mode in (None, "unified"), "v2 task selection only accepts expected_mode='unified'")
    _require(set(selection).issubset(_UNIFIED_FIELDS) and _UNIFIED_FIELDS - {"library_locator"} <= set(selection),
             "unified task selection has unsupported or missing fields")
    _require(selection.get("selection_sha256") == canonical_task_selection_sha256(selection),
             "selection.selection_sha256 does not match canonical content")
    _require(selection.get("contract") == TASK_RESOURCE_SELECTION_V2_CONTRACT,
             f"selection.contract must be {TASK_RESOURCE_SELECTION_V2_CONTRACT}")
    _require(selection.get("workflow") == "unified", "selection.workflow must be unified")
    _require(type(selection.get("library_enabled")) is bool, "selection.library_enabled must be boolean")
    locator = selection.get("library_locator")
    _require(locator is None or (isinstance(locator, str) and bool(locator.strip())), "selection.library_locator is invalid")
    _require(selection.get("library_status") == _unified_library_state(selection["library_enabled"], locator),
             "selection.library_status does not match Library selection")
    for field in ("base_config_sha256", "config_sha256"):
        _require(_sha256_text(selection.get(field)), f"selection.{field} is invalid")
    parent = selection.get("parent_selection_sha256")
    _require(parent is None or _sha256_text(parent), "selection.parent_selection_sha256 is invalid")
    requested = Path(config_path).resolve()
    stored = selection.get("config_path")
    _require(isinstance(stored, str) and Path(stored).is_absolute() and Path(stored).resolve() == requested,
             "selection.config_path does not match the observed config path")
    task_config, task_raw = _file_json(requested, "task config")
    _require(task_raw == _canonical_bytes(task_config), "task config must use canonical JSON bytes plus newline")
    _require(hashlib.sha256(task_raw).hexdigest() == selection.get("config_sha256"),
             "selection.config_sha256 does not match task config bytes")

    root = Path(bundle_root).resolve()
    default_path = root / "config" / "default.json"
    default_config, default_raw = _file_json(default_path, "bundled public config")
    _validate_pack_artifact(root, "config/default.json", default_path)
    _require(hashlib.sha256(default_raw).hexdigest() == selection.get("base_config_sha256"),
             "selection.base_config_sha256 does not match bundled config")
    default_layer = selection["layers"].get("defaults") if isinstance(selection.get("layers"), Mapping) else None
    _require(isinstance(default_layer, Mapping), "selection.layers.defaults is missing")
    _require(_validate_layer(default_layer, "selection.layers.defaults", allow_missing=False, verify_source=True) == _default_layer(default_path, default_config, default_raw),
             "selection.layers.defaults does not match bundled config")

    layers = selection.get("layers")
    _require(isinstance(layers, Mapping) and set(layers) == {"defaults", "personal", "task_overrides"},
             "selection.layers must contain defaults, personal, and task_overrides")
    personal = _validate_layer(layers["personal"], "selection.layers.personal")
    task = _validate_layer(layers["task_overrides"], "selection.layers.task_overrides")
    # If an installed private runtime exists, validate its original config and
    # pack lock even though unified selection only admits its visual settings.
    _private_runtime_source(root)
    expected = _build_unified_config(default_config, personal, task)
    _require(task_config == expected, "task config is not derived from unified layer snapshots")
    preferences: dict[str, Any] = {}
    for layer in (personal, task):
        preferences = _merge_values(preferences, layer["snapshot"]["preferences"])
    _require(selection.get("preferences") == preferences, "selection.preferences does not match merged layers")
    return dict(selection)


def _load_previous_selection(previous: Any, bundle_root: Path) -> dict[str, Any] | None:
    if previous is None:
        return None
    if isinstance(previous, (str, Path)):
        path = Path(previous).resolve()
        raw_selection, _ = _file_json(path, "previous task selection")
        previous_config = raw_selection.get("config_path")
        _require(isinstance(previous_config, str) and Path(previous_config).is_absolute(),
                 "previous task selection must bind an absolute config_path")
        return validate_task_selection(path, Path(previous_config), bundle_root)
    _require(isinstance(previous, Mapping), "previous_selection must be a path or object")
    selection = dict(previous)
    contract = selection.get("contract")
    if contract == TASK_RESOURCE_SELECTION_V2_CONTRACT:
        config_path = selection.get("config_path")
        _require(isinstance(config_path, str) and Path(config_path).is_absolute(),
                 "previous v2 selection must bind an absolute config_path")
        return _validate_unified_selection(selection.get("selection_path", "in-memory-selection"), selection,
                                           config_path, bundle_root)
    if contract == TASK_RESOURCE_SELECTION_CONTRACT:
        # An in-memory v1 object can still be checked for its self hash. The
        # CLI path form remains the preferred historical validation route.
        _require(selection.get("selection_sha256") == canonical_task_selection_sha256(selection),
                 "previous v1 selection SHA-256 does not match canonical content")
        return selection
    raise PersonalExtensionError("previous task selection contract is unsupported")


def prepare_unified_task_selection(
    bundle_root: Path | str, config_path: Path | str, personal_config_path: Path | str | None = None,
    task_overrides_path: Path | str | None = None, library_locator: str | None = None,
    library_enabled: bool | None = None, previous_selection: Any = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build one v2 unified task config from defaults, personal layer, and task overrides."""
    root = Path(bundle_root).resolve()
    default_path = root / "config" / "default.json"
    default_config, default_raw = _file_json(default_path, "bundled public config")
    _validate_pack_artifact(root, "config/default.json", default_path)
    prior = _load_previous_selection(previous_selection, root)
    prior_v2 = prior is not None and prior.get("contract") == TASK_RESOURCE_SELECTION_V2_CONTRACT

    personal_locator: str | None = None
    if personal_config_path is not None:
        personal, personal_locator = _personal_layer_file(root, personal_config_path, "personal config")
    elif prior_v2:
        personal = copy.deepcopy(prior["layers"]["personal"])
    else:
        personal = None
        if prior is not None and prior.get("contract") == TASK_RESOURCE_SELECTION_CONTRACT:
            old_config_path = Path(str(prior["config_path"])).resolve()
            old_config, _ = _file_json(old_config_path, "previous v1 task config")
            old_snapshot, _ = _layer_snapshot(old_config, "previous v1 effective settings")
            # Migrate the effective settings, without carrying v1 mode/visual
            # labels or its legacy renderer/provider requirements forward.
            personal = {"source_path": None, "source_sha256": None, "snapshot": old_snapshot}
        elif (root / "runtime" / "personal-extension.json").is_file():
            # Implicit reuse is allowed only after the installed private
            # runtime and its original pack lock validate.
            try:
                private = _private_runtime_source(root)
            except PersonalExtensionError:
                private = None
            if private is not None:
                personal, personal_locator = _layer_file(private[0], "bundled personal config")
        if personal is None:
            personal = _empty_layer()

    if task_overrides_path is not None:
        task, task_locator = _layer_file(task_overrides_path, "task overrides")
    elif prior_v2:
        task, task_locator = copy.deepcopy(prior["layers"]["task_overrides"]), None
    else:
        task, task_locator = _empty_layer(), None
    requested_locator = library_locator
    if library_enabled is False:
        _require(requested_locator is None, "--without-library cannot be combined with a library locator")
        library_locator = None
    elif library_locator is not None:
        _require(isinstance(library_locator, str) and bool(library_locator.strip()), "library_locator must be non-empty")
        library_locator = library_locator.strip()
    elif prior is not None and isinstance(prior.get("library_locator"), str):
        library_locator = prior["library_locator"]
    elif personal_locator is not None:
        library_locator = personal_locator
    elif task_locator is not None:
        library_locator = task_locator

    if library_enabled is None:
        if prior_v2:
            library_enabled = prior.get("library_enabled")
        else:
            library_enabled = library_locator is not None
    _require(type(library_enabled) is bool, "library_enabled must be a boolean")
    status = _unified_library_state(library_enabled, library_locator)
    if not library_enabled:
        library_locator = None

    config = _build_unified_config(default_config, personal, task)
    config_raw = _canonical_bytes(config)
    selection: dict[str, Any] = {
        "contract": TASK_RESOURCE_SELECTION_V2_CONTRACT,
        "workflow": "unified",
        "layers": {
            "defaults": _default_layer(default_path, default_config, default_raw),
            "personal": personal,
            "task_overrides": task,
        },
        "preferences": _merge_values(personal["snapshot"]["preferences"], task["snapshot"]["preferences"]),
        "library_enabled": library_enabled,
        "library_status": status,
        "base_config_sha256": hashlib.sha256(default_raw).hexdigest(),
        "config_sha256": hashlib.sha256(config_raw).hexdigest(),
        "config_path": str(Path(config_path).resolve()),
        "parent_selection_sha256": prior.get("selection_sha256") if prior else None,
    }
    if library_locator is not None:
        selection["library_locator"] = library_locator
    selection["selection_sha256"] = canonical_task_selection_sha256(selection)
    return config, selection


def validate_task_selection(
    selection_path: Path | str, config_path: Path | str, bundle_root: Path | str,
    expected_mode: str | None = None,
) -> dict[str, Any]:
    """Dispatch validation for historical v1 and current unified v2 selections."""
    selection, _ = _file_json(Path(selection_path).resolve(), "task resource selection")
    contract = selection.get("contract")
    if contract == TASK_RESOURCE_SELECTION_CONTRACT:
        return _validate_task_selection_v1(selection_path, config_path, bundle_root, expected_mode)
    if contract == TASK_RESOURCE_SELECTION_V2_CONTRACT:
        return _validate_unified_selection(selection_path, selection, config_path, bundle_root, expected_mode)
    raise PersonalExtensionError("task resource selection contract is unsupported")


build_unified_task_selection = prepare_unified_task_selection
canonical_unified_task_selection_sha256 = canonical_task_selection_sha256


def _sha256_text(value: Any) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{64}", value))


def required_provider_bindings(runtime: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return the immutable required-Provider surface for an external pack lock."""

    providers = runtime.get("providers") if isinstance(runtime, Mapping) else None
    _require(isinstance(providers, list), "runtime.providers must be an array")
    bindings: list[dict[str, Any]] = []
    for index, provider in enumerate(providers):
        _require(isinstance(provider, Mapping), f"runtime.providers[{index}] must be an object")
        if provider.get("required") is not True:
            continue
        bindings.append({
            "provider_id": provider.get("provider_id"),
            "visibility": provider.get("visibility"),
            "manifest_uri": provider.get("manifest_uri"),
            "mount_id": provider.get("mount_id"),
            "stages": provider.get("stages"),
            "snapshot_policy": provider.get("snapshot_policy"),
        })
    return sorted(bindings, key=lambda item: str(item.get("provider_id")))


def validate_personal_extension_runtime(
    runtime: Mapping[str, Any],
    *,
    resolved_config: Mapping[str, Any] | None = None,
    runtime_pack_lock: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate the generated cloud/local runtime envelope and embedded lock."""

    _require(isinstance(runtime, Mapping), "personal extension runtime must be an object")
    normalized = copy.deepcopy(dict(runtime))
    _require(normalized.get("contract") == PERSONAL_EXTENSION_RUNTIME_CONTRACT, "personal extension runtime contract is unsupported")
    core = normalized.get("core")
    _require(isinstance(core, Mapping), "runtime.core must be an object")
    _semver(core.get("version"), "runtime.core.version")
    _require(core.get("workflow_stages") == WORKFLOW_STAGES, "runtime must preserve the five-stage workflow")
    extension = normalized.get("extension")
    _require(isinstance(extension, Mapping), "runtime.extension must be an object")
    _require(extension.get("enabled") is True, "runtime.extension.enabled must be true")
    _identifier(extension.get("profile_id"), "runtime.extension.profile_id")
    _semver(extension.get("profile_version"), "runtime.extension.profile_version")
    _require(extension.get("host") in SUPPORTED_HOSTS, "runtime.extension.host is unsupported")
    _require(extension.get("decision_point") == "before-logic", "extension decision must occur before Logic")
    config = normalized.get("config")
    _require(isinstance(config, Mapping), "runtime.config must be an object")
    config_path = _nonempty(config.get("path"), "runtime.config.path")
    pure_config = PurePosixPath(config_path)
    _require(not pure_config.is_absolute() and ".." not in pure_config.parts, "runtime.config.path must stay inside the bundle")
    digest = _nonempty(config.get("sha256"), "runtime.config.sha256")
    _require(bool(re.fullmatch(r"[0-9a-f]{64}", digest)), "runtime.config.sha256 must be lowercase SHA-256")
    if resolved_config is not None:
        _require(digest == sha256_json(resolved_config), "runtime config digest does not match resolved config")
    mounts = normalized.get("mounts")
    _require(isinstance(mounts, list), "runtime.mounts must be an array")
    for index, mount in enumerate(mounts):
        _require(isinstance(mount, Mapping), f"runtime.mounts[{index}] must be an object")
        _identifier(mount.get("mount_id"), f"runtime.mounts[{index}].mount_id")
        if mount.get("adapter") == "bundle":
            _require(mount.get("logical_root") == "bundle://public-library/", "bundle mount must name the public Library")
            _require(mount.get("root") == ".", "bundle mount root must stay relative to the plugin root")
        else:
            _library_uri(mount.get("logical_root"), f"runtime.mounts[{index}].logical_root", root=True)
            expected = "filesystem" if extension.get("host") == "local" else "host-library"
            _require(mount.get("adapter") == expected, f"runtime.mounts[{index}].adapter must be {expected}")
    providers = normalized.get("providers")
    _require(isinstance(providers, list), "runtime.providers must be an array")
    public_provider_count = 0
    for index, provider in enumerate(providers):
        _require(isinstance(provider, Mapping), f"runtime.providers[{index}] must be an object")
        _identifier(provider.get("provider_id"), f"runtime.providers[{index}].provider_id")
        visibility = provider.get("visibility")
        _require(visibility in {"public", "owner-private"}, "runtime provider visibility is unsupported")
        _require(provider.get("manifest_contract") == PROVIDER_MANIFEST_CONTRACT, "runtime provider manifest contract is unsupported")
        if visibility == "public":
            public_provider_count += 1
            _provider_uri(provider.get("manifest_uri"), f"runtime.providers[{index}].manifest_uri", scheme="bundle")
            _require(provider.get("snapshot_policy") == "immutable-release", "public runtime provider must be immutable")
            _require(isinstance(provider.get("index_snapshot"), Mapping), "public runtime provider must bind its index snapshot")
        else:
            _library_uri(provider.get("manifest_uri"), f"runtime.providers[{index}].manifest_uri")
            _require(provider.get("snapshot_policy") == "read-once-lock-for-run", "private runtime provider snapshot policy is unsupported")
    _require(public_provider_count == 1, "runtime must contain exactly one bundled public Provider")
    expected_resource_inventory = {
        "contract": "io.clayz.presentation.resource-inventory-policy/1.0",
        "artifact": "ppt-resource-inventory.json",
        "finalizer_script": "scripts/finalize_resource_inventory.py",
        "evidence_contract": "packages/contracts/resource-inventory.schema.json",
        "required_scan_scopes": [
            "plugin-runtime", "task-inputs", "owner-library", "public-index",
            "brand-assets", "host-capabilities", "font-environment",
        ],
        "user_brief_before_logic": True,
        "final_usage_reconciliation": True,
        "fail_closed": True,
    }
    _require(normalized.get("resource_inventory") == expected_resource_inventory, "runtime.resource_inventory must enforce the pre-Logic user-visible resource gate")
    index_execution = normalized.get("index_execution")
    expected_index_execution = {
        "contract": "io.clayz.presentation.index-execution-policy/1.0",
        "mode": "first-class-stage-gated",
        "task_provider_id": "task-private-learning",
        "source_manifest": "runtime-input://owner-learning-manifest",
        "source_manifest_contract": "io.clayz.presentation.owner-learning-sources/1.0",
        "source_manifest_required": True,
        "materializer_script": "scripts/materialize_owner_index.py",
        "evidence_contract": "packages/contracts/index-execution-evidence.schema.json",
        "fail_closed_stages": WORKFLOW_STAGES,
        "required_receipt_stages": WORKFLOW_STAGES,
    }
    _require(index_execution == expected_index_execution, "runtime.index_execution must enforce the first-class stage-gated Index policy")
    expected_version_learning = {
        "contract": "io.clayz.presentation.version-private-learning-policy/1.0",
        "mode": "immutable-source-revisions",
        "state_root": "runtime-input://owner-private-version-learning-state",
        "bootstrap_script": "scripts/bootstrap_owner_learning.py",
        "audit_contract": "io.clayz.presentation.version-private-learning-audit/1.0",
        "audit_schema": "packages/contracts/version-private-learning-audit.schema.json",
        "required_knowledge_kinds": ["private-knowledge", "template", "standard", "method"],
        "reuse_requires_hash_match": True,
        "source_drift_fails_closed": True,
        "fail_closed": True,
    }
    _require(
        normalized.get("version_learning") == expected_version_learning,
        "runtime.version_learning must enforce one immutable audited snapshot per source revision",
    )
    guards = normalized.get("guards")
    _require(isinstance(guards, Mapping) and all(value is True for value in guards.values()), "runtime guards must all be true")
    lock = normalized.get("lock")
    _require(isinstance(lock, Mapping), "runtime.lock must be an object")
    _require(lock.get("algorithm") == "sha256", "runtime.lock.algorithm must be sha256")
    unlocked = copy.deepcopy(normalized)
    unlocked.pop("lock", None)
    _require(lock.get("digest") == sha256_json(unlocked), "runtime.lock.digest mismatch")
    if runtime_pack_lock is not None:
        _require(isinstance(runtime_pack_lock, Mapping), "runtime pack lock must be an object")
        _require(
            runtime_pack_lock.get("contract") == "io.clayz.presentation.runtime-pack-lock/1.2",
            "runtime pack lock contract is unsupported",
        )
        _require(
            runtime_pack_lock.get("personal_extension_digest") == lock.get("digest"),
            "runtime pack lock personal_extension_digest mismatch",
        )
        _require(
            runtime_pack_lock.get("resolved_config_digest") == digest,
            "runtime pack lock resolved_config_digest mismatch",
        )
        expected_bindings = required_provider_bindings(normalized)
        _require(
            runtime_pack_lock.get("required_provider_bindings") == expected_bindings,
            "runtime pack lock required Provider bindings mismatch",
        )
        _require(
            runtime_pack_lock.get("required_provider_set_sha256") == sha256_json(expected_bindings),
            "runtime pack lock required Provider set digest mismatch",
        )
    return normalized
