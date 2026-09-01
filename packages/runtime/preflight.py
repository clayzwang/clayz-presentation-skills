#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Scan once, select one presentation route, and emit a locked execution plan."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import re
import secrets
import shutil
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


CONTRACT = "io.clayz.presentation.runtime-preflight/1.3"
RUN_CHALLENGE_CONTRACT = "io.clayz.presentation.run-challenge/1.0"
RUN_CHALLENGE_ISSUANCE_CONTRACT = "io.clayz.presentation.run-challenge-issuance/1.0"
RUN_CHALLENGE_CONSUMPTION_CONTRACT = "io.clayz.presentation.run-challenge-consumption/1.0"
HOST_ATTESTATION_CONTRACT = "io.clayz.presentation.host-capability-attestation/1.0"
HOST_INVENTORY_CONTRACT = "io.clayz.presentation.host-tool-inventory/1.0"
RUN_CHALLENGE_TTL = timedelta(hours=24)
SHA256_HEX = set("0123456789abcdef")

MODEL_PROFILES: dict[str, dict[str, Any]] = {
    "A": {
        "label": "full-agent",
        "interaction_mode": "direct-orchestrated",
        "requires": ["tool-calling", "structured-output", "visual-inspection"],
    },
    "B": {
        "label": "tool-agent",
        "interaction_mode": "direct-with-external-visual-qa",
        "requires": ["tool-calling", "structured-output"],
    },
    "C": {
        "label": "spec-model",
        "interaction_mode": "adapter-mediated",
        "requires": ["structured-output"],
    },
    "D": {
        "label": "constrained-model",
        "interaction_mode": "narrow-tool-or-adapter-mediated",
        "requires": [],
    },
}


def _present(value: str | None) -> bool:
    return bool(value and Path(value).exists())


def _module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _command(*names: str) -> str | None:
    for name in names:
        resolved = shutil.which(name)
        if resolved:
            return str(Path(resolved).resolve())
    return None


def _windows_powerpoint() -> dict[str, Any]:
    result: dict[str, Any] = {"available": False, "evidence": None}
    if platform.system() != "Windows":
        return result
    try:
        import winreg  # type: ignore[import-not-found]

        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"PowerPoint.Application\CLSID") as key:
            clsid, _ = winreg.QueryValueEx(key, None)
        evidence = f"CLSID:{clsid}"
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, rf"CLSID\{clsid}\LocalServer32") as key:
                server, _ = winreg.QueryValueEx(key, None)
                evidence = server
        except OSError:
            pass
        result.update({"available": True, "evidence": evidence})
    except (OSError, ImportError):
        pass
    return result


def classify_model_profile(capabilities: Mapping[str, Any] | None = None, explicit: str | None = None) -> str:
    if explicit:
        profile = explicit.upper()
        if profile not in MODEL_PROFILES:
            raise ValueError(f"unsupported model profile: {explicit}")
        return profile
    caps = capabilities or {}
    if caps.get("tool_calling") and caps.get("structured_output") and caps.get("visual_inspection"):
        return "A"
    if caps.get("tool_calling") and caps.get("structured_output"):
        return "B"
    if caps.get("structured_output"):
        return "C"
    return "D"


def _artifact_tool() -> dict[str, Any]:
    node = os.environ.get("RUNTIME_NODE")
    modules = os.environ.get("RUNTIME_NODE_MODULES")
    binaries = os.environ.get("RUNTIME_BIN_DIR")
    package = Path(modules, "@oai", "artifact-tool", "package.json") if modules else None
    available = _present(node) and _present(modules) and _present(binaries) and bool(package and package.is_file())
    return {
        "available": available,
        "node": node,
        "node_modules": modules,
        "bin_dir": binaries,
        "package": str(package) if package else None,
    }


def _valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= SHA256_HEX


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _parse_time(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a timezone-aware ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be a timezone-aware ISO timestamp") from exc
    if parsed.utcoffset() is None:
        raise ValueError(f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc)


def task_root_digest(path: Path | str) -> str:
    normalized = os.path.normcase(str(Path(path).resolve()))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def issue_run_challenge(
    task_request: bytes,
    *,
    task_root: Path | str | None = None,
    now: datetime | None = None,
) -> dict[str, str]:
    """Issue a fresh script-generated binding for one exact task request."""

    if not isinstance(task_request, bytes) or not task_request:
        raise ValueError("task request bytes must be non-empty")
    issued = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(microsecond=0)
    expires = issued + RUN_CHALLENGE_TTL
    run_id = f"run-{uuid.uuid4().hex}"
    return {
        "contract": RUN_CHALLENGE_CONTRACT,
        "issuer": "scripts/runtime_preflight.py",
        "run_id": run_id,
        "task_request_sha256": hashlib.sha256(task_request).hexdigest(),
        "nonce": secrets.token_hex(32),
        "issued_at": _iso(issued),
        "expires_at": _iso(expires),
        "task_root_sha256": task_root_digest(task_root or Path.cwd()),
        "issuance_record": f".clayz-run-challenges/{run_id}.issued.json",
    }


def _challenge_digest(challenge: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(challenge, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def validate_run_challenge(
    challenge: Mapping[str, Any],
    *,
    challenge_sha256: str | None = None,
    task_root: Path | str | None = None,
    now: datetime | None = None,
) -> dict[str, str]:
    if not isinstance(challenge, Mapping) or challenge.get("contract") != RUN_CHALLENGE_CONTRACT:
        raise ValueError("run challenge contract is unsupported")
    if challenge.get("issuer") != "scripts/runtime_preflight.py":
        raise ValueError("run challenge issuer is unsupported")
    run_id = challenge.get("run_id")
    if not isinstance(run_id, str) or not re_full_run_id(run_id):
        raise ValueError("run challenge run_id must be script-generated UUID form")
    task_sha = challenge.get("task_request_sha256")
    nonce = challenge.get("nonce")
    if not _valid_sha256(task_sha) or len(set(str(task_sha))) == 1:
        raise ValueError("run challenge task_request_sha256 is invalid or trivial")
    if not _valid_sha256(nonce):
        raise ValueError("run challenge nonce must be a 256-bit lower-case hex value")
    root_sha = challenge.get("task_root_sha256")
    if not _valid_sha256(root_sha):
        raise ValueError("run challenge task_root_sha256 is invalid")
    if task_root is not None and root_sha != task_root_digest(task_root):
        raise ValueError("run challenge is not bound to the current task root")
    issuance_record = challenge.get("issuance_record")
    if issuance_record != f".clayz-run-challenges/{run_id}.issued.json":
        raise ValueError("run challenge issuance record path is invalid")
    issued = _parse_time(challenge.get("issued_at"), "run challenge issued_at")
    expires = _parse_time(challenge.get("expires_at"), "run challenge expires_at")
    if expires <= issued or expires - issued > RUN_CHALLENGE_TTL:
        raise ValueError("run challenge validity window is invalid")
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if current < issued - timedelta(minutes=1) or current > expires:
        raise ValueError("run challenge is not current")
    digest = challenge_sha256 or _challenge_digest(challenge)
    if not _valid_sha256(digest):
        raise ValueError("run challenge SHA-256 is invalid")
    return {
        "run_id": run_id,
        "task_request_sha256": str(task_sha),
        "nonce": str(nonce),
        "issued_at": _iso(issued),
        "expires_at": _iso(expires),
        "challenge_sha256": digest,
        "task_root_sha256": str(root_sha),
        "issuance_record": str(issuance_record),
        "binding_source": "challenge-structure-valid",
    }


def _validate_ledger_receipt(
    binding: Mapping[str, str],
    receipt: Mapping[str, Any],
    *,
    kind: str,
) -> tuple[str, str]:
    """Reopen one canonical task ledger and bind its actual bytes.

    The preflight library deliberately does not trust an in-memory receipt object.
    A final script-issued binding exists only when the expected task-local ledger
    file is present at its canonical path and its bytes match the supplied hash.
    """

    if kind == "issuance":
        contract = RUN_CHALLENGE_ISSUANCE_CONTRACT
        expected_path = Path(*PurePosixPath(binding["issuance_record"]).parts)
        expected_keys = {
            "contract", "challenge_sha256", "run_id", "task_request_sha256", "nonce",
            "task_root_sha256", "issued_at", "expires_at",
        }
    elif kind == "consumption":
        contract = RUN_CHALLENGE_CONSUMPTION_CONTRACT
        expected_path = (
            Path(".clayz-run-challenges") / "consumed" / f"{binding['challenge_sha256']}.json"
        )
        expected_keys = {
            "contract", "challenge_sha256", "run_id", "task_request_sha256", "nonce",
            "task_root_sha256", "consumed_at",
        }
    else:  # pragma: no cover - internal programming guard
        raise ValueError(f"unsupported run challenge ledger kind: {kind}")

    if receipt.get("contract") != contract:
        raise ValueError(f"run challenge {kind} contract is unsupported")
    receipt_path_value = receipt.get("receipt_path")
    receipt_sha256 = receipt.get("receipt_sha256")
    if not isinstance(receipt_path_value, str) or not receipt_path_value.strip():
        raise ValueError(f"run challenge {kind} receipt path is missing")
    if not _valid_sha256(receipt_sha256):
        raise ValueError(f"run challenge {kind} receipt SHA-256 is invalid")

    receipt_path = Path(receipt_path_value)
    if not receipt_path.is_absolute():
        raise ValueError(f"run challenge {kind} receipt path must be absolute")
    receipt_path = receipt_path.resolve()
    suffix_parts = expected_path.parts
    if len(receipt_path.parts) <= len(suffix_parts) or receipt_path.parts[-len(suffix_parts):] != suffix_parts:
        raise ValueError(f"run challenge {kind} receipt path is not canonical")
    task_root = Path(*receipt_path.parts[:-len(suffix_parts)])
    if task_root_digest(task_root) != binding.get("task_root_sha256"):
        raise ValueError(f"run challenge {kind} receipt is outside the bound task root")
    canonical_path = (task_root / expected_path).resolve()
    if canonical_path != receipt_path:
        raise ValueError(f"run challenge {kind} receipt path is not canonical")

    try:
        raw = receipt_path.read_bytes()
    except OSError as exc:
        raise ValueError(f"run challenge {kind} receipt file is missing") from exc
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if actual_sha256 != receipt_sha256:
        raise ValueError(f"run challenge {kind} receipt SHA-256 does not match its bytes")
    try:
        record = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"run challenge {kind} receipt is not valid JSON") from exc
    if not isinstance(record, Mapping) or set(record) != expected_keys:
        raise ValueError(f"run challenge {kind} receipt has an invalid field set")
    if record.get("contract") != contract:
        raise ValueError(f"run challenge {kind} receipt contract is unsupported")
    for key in ("challenge_sha256", "run_id", "task_request_sha256", "nonce", "task_root_sha256"):
        if record.get(key) != binding.get(key) or receipt.get(key) != record.get(key):
            raise ValueError(f"run challenge {kind} receipt must match {key}")
    if kind == "issuance":
        for key in ("issued_at", "expires_at"):
            if record.get(key) != binding.get(key) or receipt.get(key) != record.get(key):
                raise ValueError(f"run challenge issuance receipt must match {key}")
    else:
        consumed = _parse_time(record.get("consumed_at"), "run challenge consumed_at")
        issued = _parse_time(binding.get("issued_at"), "run challenge issued_at")
        expires = _parse_time(binding.get("expires_at"), "run challenge expires_at")
        if consumed < issued or consumed > expires:
            raise ValueError("run challenge consumption must fall inside the challenge window")
        if receipt.get("consumed_at") != record.get("consumed_at"):
            raise ValueError("run challenge consumption receipt must match consumed_at")
    return receipt_path.as_posix(), actual_sha256


def re_full_run_id(value: str) -> bool:
    if not value.startswith("run-") or len(value) != 36:
        return False
    try:
        parsed = uuid.UUID(hex=value[4:])
    except ValueError:
        return False
    return parsed.version == 4


def _run_binding(
    run_id: str | None,
    task_request_sha256: str | None,
    run_challenge: Mapping[str, Any] | None,
    run_challenge_sha256: str | None,
    run_challenge_issuance: Mapping[str, Any] | None,
    run_challenge_consumption: Mapping[str, Any] | None,
) -> dict[str, str]:
    if run_challenge is not None:
        binding = validate_run_challenge(run_challenge, challenge_sha256=run_challenge_sha256)
        if not isinstance(run_challenge_issuance, Mapping):
            raise ValueError("run challenge requires a script issuance receipt")
        if not isinstance(run_challenge_consumption, Mapping):
            raise ValueError("script-issued run challenge requires an exclusive consumption receipt")
        issuance_path, issuance_sha = _validate_ledger_receipt(
            binding,
            run_challenge_issuance,
            kind="issuance",
        )
        consumption_path, receipt_sha = _validate_ledger_receipt(
            binding,
            run_challenge_consumption,
            kind="consumption",
        )
        binding["binding_source"] = "script-issued-challenge"
        binding["issuance_receipt"] = issuance_path
        binding["issuance_receipt_sha256"] = issuance_sha
        binding["consumption_receipt"] = consumption_path
        binding["consumption_receipt_sha256"] = receipt_sha
        return binding
    issued = datetime.now(timezone.utc).replace(microsecond=0)
    resolved_run_id = run_id or f"run-{uuid.uuid4().hex}"
    if not isinstance(resolved_run_id, str) or not resolved_run_id.strip():
        raise ValueError("run_id must be a non-empty string")
    resolved_task_sha256 = task_request_sha256 or hashlib.sha256(
        f"direct-api:{resolved_run_id}".encode("utf-8")
    ).hexdigest()
    if not _valid_sha256(resolved_task_sha256):
        raise ValueError("task_request_sha256 must be a lower-case SHA-256")
    nonce = secrets.token_hex(32)
    direct = {
        "contract": RUN_CHALLENGE_CONTRACT,
        "issuer": "direct-api-unattested",
        "run_id": resolved_run_id.strip(),
        "task_request_sha256": resolved_task_sha256,
        "nonce": nonce,
        "issued_at": _iso(issued),
        "expires_at": _iso(issued + RUN_CHALLENGE_TTL),
    }
    return {
        "run_id": resolved_run_id.strip(),
        "task_request_sha256": resolved_task_sha256,
        "nonce": nonce,
        "issued_at": direct["issued_at"],
        "expires_at": direct["expires_at"],
        "challenge_sha256": _challenge_digest(direct),
        "task_root_sha256": task_root_digest(Path.cwd()),
        "binding_source": "direct-api-unattested",
        "issuance_receipt": "not-applicable",
        "issuance_receipt_sha256": hashlib.sha256(b"direct-api-unattested-issuance").hexdigest(),
        "consumption_receipt": "not-applicable",
        "consumption_receipt_sha256": hashlib.sha256(b"direct-api-unattested").hexdigest(),
    }


def _config_binding(config: Mapping[str, Any], value: Mapping[str, Any] | None) -> dict[str, str]:
    canonical_sha256 = hashlib.sha256(
        json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    raw = value or {}
    path = raw.get("path", "in-memory-config")
    sha256 = raw.get("sha256", canonical_sha256)
    source = raw.get("source", "in-memory")
    if not isinstance(path, str) or not path.strip():
        raise ValueError("config binding path must be a non-empty string")
    if not _valid_sha256(sha256):
        raise ValueError("config binding sha256 must be a lower-case SHA-256")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("config binding source must be a non-empty string")
    return {"path": path, "sha256": sha256, "source": source}


def _component_version_gate(config: Mapping[str, Any], value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("a fresh component version report is required before runtime preflight")
    required = {
        "artifact", "sha256", "generated_at", "status", "local_release_version",
        "latest_release_version", "manifest_sha256", "all_components_current",
    }
    if not required.issubset(value):
        raise ValueError("component version gate is incomplete")
    identity = config.get("identity") if isinstance(config, Mapping) else None
    configured_version = identity.get("version") if isinstance(identity, Mapping) else None
    if value.get("status") != "latest" or value.get("all_components_current") is not True:
        raise ValueError("component version gate did not establish latest components")
    if value.get("local_release_version") != configured_version or value.get("latest_release_version") != configured_version:
        raise ValueError("component version gate does not match the resolved configuration release")
    for key in ("sha256", "manifest_sha256"):
        if not isinstance(value.get(key), str) or not re.fullmatch(r"[0-9a-f]{64}", str(value.get(key))):
            raise ValueError(f"component version gate {key} must be lowercase SHA-256")
    return dict(value)


def _host_tools(
    value: Mapping[str, Any] | None,
    run_binding: Mapping[str, str],
    attestation_context: Mapping[str, Any] | None,
) -> dict[str, Any]:
    raw = value or {}
    capabilities = raw.get("capabilities", [])
    if not isinstance(capabilities, list) or not all(isinstance(item, str) and item for item in capabilities):
        raise ValueError("host capabilities must be a string array")
    available = raw.get("available", False)
    if not isinstance(available, bool):
        raise ValueError("host capability availability must be boolean")
    host = raw.get("host", "local")
    if not isinstance(host, str) or not host:
        raise ValueError("host capability host must be a non-empty string")
    if available:
        if run_binding.get("binding_source") != "script-issued-challenge":
            raise ValueError("available host capabilities require a fresh script-issued run challenge")
        if raw.get("contract") != HOST_ATTESTATION_CONTRACT:
            raise ValueError("host capability attestation contract is unsupported")
        for key in ("run_id", "task_request_sha256", "nonce", "challenge_sha256"):
            if raw.get(key) != run_binding.get(key):
                raise ValueError(f"available host capabilities must match run challenge {key}")
        if raw.get("source") not in {"host-inspection", "host-tool-inventory"}:
            raise ValueError("available host capabilities require an inspected source")
        evidence_receipts = raw.get("evidence_receipts")
        if not isinstance(evidence_receipts, list) or not evidence_receipts or any(
            not isinstance(item, Mapping)
            or not isinstance(item.get("artifact"), str)
            or not item.get("artifact", "").strip()
            or not _valid_sha256(item.get("sha256"))
            or item.get("contract") != HOST_INVENTORY_CONTRACT
            for item in evidence_receipts
        ):
            raise ValueError("available host capabilities require structured evidence receipts")
        if not isinstance(attestation_context, Mapping) or attestation_context.get("validated") is not True:
            raise ValueError("available host capabilities require file-validated evidence receipts")
        if attestation_context.get("challenge_sha256") != run_binding.get("challenge_sha256"):
            raise ValueError("host evidence context must match the run challenge")
        if attestation_context.get("evidence_receipts") != evidence_receipts:
            raise ValueError("host evidence context must exactly match the attestation receipts")
        observed_at = raw.get("observed_at")
        observed = _parse_time(observed_at, "host capability observed_at")
        issued = _parse_time(run_binding.get("issued_at"), "run binding issued_at")
        expires = _parse_time(run_binding.get("expires_at"), "run binding expires_at")
        if observed < issued or observed > expires:
            raise ValueError("host capability observation must fall inside the run challenge window")
        verification_status = "challenge-bound-host-declaration"
        assurance_level = "host-declared-unverified"
        route_eligible = False
    else:
        evidence_receipts = raw.get("evidence_receipts", [])
        observed_at = raw.get("observed_at", "not-applicable")
        verification_status = "runtime-probed"
        assurance_level = "runtime-probed-absent"
        route_eligible = False
    return {
        "host": host,
        "available": available,
        "capabilities": sorted(set(capabilities)),
        "observation": {
            "run_id": run_binding["run_id"],
            "task_request_sha256": run_binding["task_request_sha256"],
            "challenge_sha256": run_binding["challenge_sha256"],
            "source": raw.get("source", "local-runtime"),
            "observed_at": observed_at,
            "evidence_receipts": evidence_receipts,
            "verification_status": verification_status,
            "assurance_level": assurance_level,
            "route_eligible": route_eligible,
        },
    }


def _route_candidates(dependencies: Mapping[str, Any], required: set[str]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    authoring_caps = {
        "artifact-tool": {
            "editable-text", "editable-shapes", "charts", "tables", "images", "svg", "speaker-notes", "pptx-inspection"
        },
        "python-pptx": {
            "editable-text", "editable-shapes", "charts", "tables", "images", "speaker-notes", "pptx-inspection"
        },
        "powerpoint-com": {
            "editable-text", "editable-shapes", "tables", "images", "svg", "speaker-notes", "pptx-inspection"
        },
        "native-presentation-tool": set(dependencies["host_tools"]["capabilities"]),
        "spec-only": {"structured-spec"},
    }
    renderer_caps = {
        "powerpoint-com": {"render-preview", "pptx-inspection"},
        "libreoffice": {"render-preview", "pptx-inspection"},
        "artifact-tool": {"render-preview", "pptx-inspection", "svg"},
        "native-presentation-tool": set(dependencies["host_tools"]["capabilities"]),
        "none": set(),
    }
    host_present = bool(dependencies["host_tools"]["available"])
    host_verified = bool(dependencies["host_tools"]["observation"]["route_eligible"])
    renderers: list[tuple[str, bool, bool]] = [
        ("native-presentation-tool", host_present, host_verified),
        ("powerpoint-com", bool(dependencies["powerpoint_com"]["available"]), bool(dependencies["powerpoint_com"]["available"])),
        ("libreoffice", bool(dependencies["commands"]["libreoffice"]), bool(dependencies["commands"]["libreoffice"])),
        ("artifact-tool", bool(dependencies["artifact_tool"]["available"]), bool(dependencies["artifact_tool"]["available"])),
        ("none", True, True),
    ]
    authors: list[tuple[str, bool, bool]] = [
        ("native-presentation-tool", host_present, host_verified),
        ("python-pptx", bool(dependencies["python_modules"]["pptx"]), bool(dependencies["python_modules"]["pptx"])),
        ("artifact-tool", bool(dependencies["artifact_tool"]["available"]), bool(dependencies["artifact_tool"]["available"])),
        ("powerpoint-com", bool(dependencies["powerpoint_com"]["available"]), bool(dependencies["powerpoint_com"]["available"])),
        ("spec-only", True, True),
    ]
    for author, author_present, author_verified in authors:
        if not author_present:
            continue
        for renderer, renderer_present, renderer_verified in renderers:
            if not renderer_present:
                continue
            missing = sorted(required - (authoring_caps[author] | renderer_caps[renderer]))
            if "render-preview" in required and renderer == "none":
                continue
            attemptable = not missing
            available = attemptable and author_verified and renderer_verified
            assurance = (
                "runtime-probed"
                if available
                else "host-declared-unverified"
                if attemptable and "native-presentation-tool" in {author, renderer}
                else "insufficient"
            )
            route_id = f"{author}+{renderer}"
            candidates.append({
                "route_id": route_id,
                "authoring_backend": author,
                "render_backend": renderer,
                "available": available,
                "attemptable": attemptable,
                "assurance_level": assurance,
                "missing_capabilities": missing,
                "host_model_private_tool_required": author in {"artifact-tool", "native-presentation-tool"},
            })
    return candidates


def _target_application_checks(
    renderer: Mapping[str, Any],
    dependencies: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Observe native target-app acceptance without turning it into an authoring gate."""

    raw_targets = renderer.get("target_applications", [])
    if not isinstance(raw_targets, list) or not all(isinstance(item, str) and item.strip() for item in raw_targets):
        raise ValueError("renderer.target_applications must be a non-empty string array")

    host_tools = dependencies["host_tools"]
    host_capabilities = set(host_tools["capabilities"]) if host_tools["available"] else set()
    checks: list[dict[str, Any]] = []
    for raw_target in raw_targets:
        application = raw_target.strip().lower()
        capability = f"{application}-reopen-render"
        available = capability in host_capabilities
        evidence = (
            f"host-declared-unverified:{host_tools['host']}:{capability}"
            if available
            else "not-detected-in-host-capabilities-or-local-runtime"
        )

        if application == "powerpoint" and dependencies["powerpoint_com"]["available"]:
            available = True
            evidence = f"powerpoint-com:{dependencies['powerpoint_com']['evidence']}"
        elif application == "libreoffice" and dependencies["commands"]["libreoffice"]:
            available = True
            evidence = f"command:{dependencies['commands']['libreoffice']}"

        checks.append({
            "application": application,
            "capability": capability,
            "availability": "available" if available else "unavailable",
            "disposition": "eligible-after-output" if available else "deferred-and-recorded",
            "blocks_authoring": False,
            "evidence": evidence,
        })
    return checks


def build_preflight_report(
    config: Mapping[str, Any],
    *,
    model_profile: str | None = None,
    model_capabilities: Mapping[str, Any] | None = None,
    host_capabilities: Mapping[str, Any] | None = None,
    required_capabilities: list[str] | None = None,
    run_id: str | None = None,
    task_request_sha256: str | None = None,
    run_challenge: Mapping[str, Any] | None = None,
    run_challenge_sha256: str | None = None,
    run_challenge_issuance: Mapping[str, Any] | None = None,
    run_challenge_consumption: Mapping[str, Any] | None = None,
    host_attestation_context: Mapping[str, Any] | None = None,
    config_binding: Mapping[str, Any] | None = None,
    component_version_gate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    profile = classify_model_profile(model_capabilities, model_profile)
    runtime = config.get("runtime", {}) if isinstance(config, Mapping) else {}
    renderer = config.get("renderer", {}) if isinstance(config, Mapping) else {}
    configured_capabilities = renderer.get("required_capabilities", [])
    if not isinstance(configured_capabilities, list) or any(
        not isinstance(item, str) or not item for item in configured_capabilities
    ):
        raise ValueError("renderer.required_capabilities must be a string array")
    if required_capabilities is not None and any(
        not isinstance(item, str) or not item for item in required_capabilities
    ):
        raise ValueError("additional required capabilities must be a string array")
    required = set(configured_capabilities) | set(required_capabilities or [])
    resolved_run_binding = _run_binding(
        run_id,
        task_request_sha256,
        run_challenge,
        run_challenge_sha256,
        run_challenge_issuance,
        run_challenge_consumption,
    )
    resolved_config_binding = _config_binding(config, config_binding)
    resolved_component_version_gate = _component_version_gate(config, component_version_gate)
    resolved_host_tools = _host_tools(host_capabilities, resolved_run_binding, host_attestation_context)
    dependencies = {
        "python": {"executable": sys.executable, "version": platform.python_version()},
        "python_modules": {
            "pptx": _module("pptx"),
            "PIL": _module("PIL"),
            "yaml": _module("yaml"),
        },
        "artifact_tool": _artifact_tool(),
        "host_tools": resolved_host_tools,
        "powerpoint_com": _windows_powerpoint(),
        "commands": {
            "libreoffice": _command("soffice", "libreoffice"),
            "pdfinfo": _command("pdfinfo"),
            "pdftoppm": _command("pdftoppm"),
        },
    }
    candidates = _route_candidates(dependencies, required)
    selected = next((item for item in candidates if item["available"]), None)
    if selected is None:
        selected = next((item for item in candidates if item["attemptable"]), None)
    if selected is None:
        selected = {
            "route_id": "spec-only+none",
            "authoring_backend": "spec-only",
            "render_backend": "none",
            "available": required.issubset({"structured-spec"}),
            "attemptable": required.issubset({"structured-spec"}),
            "assurance_level": "runtime-probed" if required.issubset({"structured-spec"}) else "insufficient",
            "missing_capabilities": sorted(required - {"structured-spec"}),
            "host_model_private_tool_required": False,
        }
    target_application_checks = _target_application_checks(renderer, dependencies)
    warnings: list[str] = []
    if selected["authoring_backend"] == "spec-only":
        warnings.append("No executable PPTX authoring route satisfies the requested capabilities; emit an internal spec only.")
    if selected.get("attemptable") is True and selected.get("available") is not True:
        warnings.append(
            "The locked native route is provisional because it rests on an unverified host declaration; "
            "it cannot establish delivery readiness without independently validated final PPTX and render evidence."
        )
    if "render-preview" in required and selected["render_backend"] == "none":
        warnings.append("No final-render backend is available; production delivery is blocked.")
    if dependencies["commands"]["pdfinfo"] is None or dependencies["commands"]["pdftoppm"] is None:
        warnings.append("PDF page ingestion is unavailable; ordinary PPTX authoring is unaffected.")
    for check in target_application_checks:
        if check["availability"] == "unavailable":
            warnings.append(
                f"{check['application']} native reopen/render acceptance is unavailable; "
                "record it as deferred without blocking authoring."
            )
    stable = {
        "run_binding": resolved_run_binding,
        "config_binding": resolved_config_binding,
        "component_version_gate": resolved_component_version_gate,
        "platform": platform.system().lower(),
        "profile": profile,
        "required": sorted(required),
        "dependencies": dependencies,
        "selected": selected,
        "target_application_checks": target_application_checks,
    }
    scan_id = hashlib.sha256(json.dumps(stable, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:20]
    return {
        "contract": CONTRACT,
        "scan_id": f"runtime-{scan_id}",
        "run_binding": resolved_run_binding,
        "config_binding": resolved_config_binding,
        "component_version_gate": resolved_component_version_gate,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "platform": {"system": platform.system(), "release": platform.release(), "machine": platform.machine()},
        "model": {"profile": profile, **MODEL_PROFILES[profile]},
        "required_capabilities": sorted(required),
        "dependencies": dependencies,
        "selected_route": {**selected, "locked": True},
        "fallback_routes": [item for item in candidates if item["route_id"] != selected["route_id"]],
        "target_application_checks": target_application_checks,
        "budgets": dict(runtime.get("budgets", {})),
        "guards": {
            "scan_once": True,
            "route_locked_for_run": True,
            "no_mid_run_backend_switch": True,
            "fallback_requires_new_preflight_run": True,
            "pdf_support_is_lazy": True,
            "target_application_checks_do_not_block_authoring": True,
            "configured_capabilities_cannot_be_reduced": True,
            "host_capabilities_bound_to_run": True,
            "host_declarations_never_self_authorize_route_readiness": True,
            "run_challenge_has_nonce_and_freshness_window": True,
            "run_challenge_requires_issuance_and_canonical_consumption_ledgers": True,
            "latest_component_versions_verified_before_preflight": True,
        },
        "warnings": warnings,
    }
