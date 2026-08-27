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
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


CONTRACT = "io.clayz.presentation.runtime-preflight/1.0"

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


def _host_tools(value: Mapping[str, Any] | None) -> dict[str, Any]:
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
    return {"host": host, "available": available, "capabilities": sorted(set(capabilities))}


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
    renderers: list[tuple[str, bool]] = [
        ("native-presentation-tool", bool(dependencies["host_tools"]["available"])),
        ("powerpoint-com", bool(dependencies["powerpoint_com"]["available"])),
        ("libreoffice", bool(dependencies["commands"]["libreoffice"])),
        ("artifact-tool", bool(dependencies["artifact_tool"]["available"])),
        ("none", True),
    ]
    authors: list[tuple[str, bool]] = [
        ("native-presentation-tool", bool(dependencies["host_tools"]["available"])),
        ("python-pptx", bool(dependencies["python_modules"]["pptx"])),
        ("artifact-tool", bool(dependencies["artifact_tool"]["available"])),
        ("powerpoint-com", bool(dependencies["powerpoint_com"]["available"])),
        ("spec-only", True),
    ]
    for author, available in authors:
        if not available:
            continue
        for renderer, render_available in renderers:
            if not render_available:
                continue
            missing = sorted(required - (authoring_caps[author] | renderer_caps[renderer]))
            if "render-preview" in required and renderer == "none":
                continue
            route_id = f"{author}+{renderer}"
            candidates.append({
                "route_id": route_id,
                "authoring_backend": author,
                "render_backend": renderer,
                "available": not missing,
                "missing_capabilities": missing,
                "host_model_private_tool_required": author in {"artifact-tool", "native-presentation-tool"},
            })
            break
    return candidates


def build_preflight_report(
    config: Mapping[str, Any],
    *,
    model_profile: str | None = None,
    model_capabilities: Mapping[str, Any] | None = None,
    host_capabilities: Mapping[str, Any] | None = None,
    required_capabilities: list[str] | None = None,
) -> dict[str, Any]:
    profile = classify_model_profile(model_capabilities, model_profile)
    runtime = config.get("runtime", {}) if isinstance(config, Mapping) else {}
    renderer = config.get("renderer", {}) if isinstance(config, Mapping) else {}
    required = set(required_capabilities or renderer.get("required_capabilities", []))
    resolved_host_tools = _host_tools(host_capabilities)
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
        selected = {
            "route_id": "spec-only+none",
            "authoring_backend": "spec-only",
            "render_backend": "none",
            "available": required.issubset({"structured-spec"}),
            "missing_capabilities": sorted(required - {"structured-spec"}),
            "host_model_private_tool_required": False,
        }
    warnings: list[str] = []
    if selected["authoring_backend"] == "spec-only":
        warnings.append("No executable PPTX authoring route satisfies the requested capabilities; emit an internal spec only.")
    if "render-preview" in required and selected["render_backend"] == "none":
        warnings.append("No final-render backend is available; production delivery is blocked.")
    if dependencies["commands"]["pdfinfo"] is None or dependencies["commands"]["pdftoppm"] is None:
        warnings.append("PDF page ingestion is unavailable; ordinary PPTX authoring is unaffected.")
    stable = {
        "platform": platform.system().lower(),
        "profile": profile,
        "required": sorted(required),
        "dependencies": dependencies,
        "selected": selected,
    }
    scan_id = hashlib.sha256(json.dumps(stable, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:20]
    return {
        "contract": CONTRACT,
        "scan_id": f"runtime-{scan_id}",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "platform": {"system": platform.system(), "release": platform.release(), "machine": platform.machine()},
        "model": {"profile": profile, **MODEL_PROFILES[profile]},
        "required_capabilities": sorted(required),
        "dependencies": dependencies,
        "selected_route": {**selected, "locked": True},
        "fallback_routes": [item for item in candidates if item["route_id"] != selected["route_id"]],
        "budgets": dict(runtime.get("budgets", {})),
        "guards": {
            "scan_once": True,
            "route_locked_for_run": True,
            "no_mid_run_backend_switch": True,
            "fallback_requires_new_preflight_run": True,
            "pdf_support_is_lazy": True,
        },
        "warnings": warnings,
    }
