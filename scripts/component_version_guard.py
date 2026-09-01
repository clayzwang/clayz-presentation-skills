#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Fail closed unless every mounted presentation component is the latest release.

The normal path checks the official GitHub Latest Release endpoint on every
presentation run. A host may instead materialize that exact JSON response and
pass it with ``--latest-release-json`` when direct network access is unavailable.
The report is deliberately user-facing and must be printed before Logic.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
REPORT_CONTRACT = "io.clayz.presentation.component-version-report/1.0"
MANIFEST_CONTRACT = "io.clayz.presentation.component-version-manifest/1.0"
OFFICIAL_REPOSITORY = "clayzwang/clayz-presentation-skills"
OFFICIAL_LATEST_RELEASE_API = "https://api.github.com/repos/clayzwang/clayz-presentation-skills/releases/latest"
OFFICIAL_RELEASE_PREFIX = "https://github.com/clayzwang/clayz-presentation-skills/releases/"
OFFICIAL_RAW_PREFIX = "https://raw.githubusercontent.com/clayzwang/clayz-presentation-skills/"
SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")

# v0.7.1 predates the remote component-manifest file. This frozen bootstrap
# record describes that immutable tag and is used only to detect an unversioned
# local change while the first manifest-aware release is being prepared.
V071_COMPONENT_MANIFEST = {
    "contract": MANIFEST_CONTRACT,
    "repository": OFFICIAL_REPOSITORY,
    "latest_release_api": OFFICIAL_LATEST_RELEASE_API,
    "release_version": "0.7.1",
    "components": {
        "public-core": "0.7.1",
        "plugin-manifest": "0.7.1",
        "central-config": "0.7.1",
        "workflow-contract": "3.1-open",
        "runtime-preflight": "1.2",
        "personal-extension-runtime": "1.0",
        "resource-inventory": "1.0",
        "index-execution-evidence": "1.0",
        "logic-package": "2.3",
        "copy-package": "2.3",
        "art-direction-plan": "1.6",
        "output-qa": "3.9",
        "supervision-report": "3.3",
        "owner-index-materialization": "1.0",
    },
    "guards": {
        "official_latest_release_required": True,
        "all_components_must_match_manifest": True,
        "user_visible_before_work": True,
        "unverified_latest_fails_closed": True,
    },
}


class VersionGuardError(ValueError):
    """Raised when latest-version evidence cannot be established."""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_json(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise VersionGuardError(f"{path}: expected a JSON object")
    return raw, value


def _regex_value(path: Path, pattern: str, label: str) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        raise VersionGuardError(f"{label}: version marker not found in {path}")
    return match.group(1)


def _latest_release(payload: Mapping[str, Any], source: str) -> dict[str, str]:
    tag = payload.get("tag_name")
    html_url = payload.get("html_url")
    if not isinstance(tag, str) or not tag.startswith("v") or not SEMVER.fullmatch(tag[1:]):
        raise VersionGuardError("official latest release response has no stable vX.Y.Z tag")
    if not isinstance(html_url, str) or not html_url.startswith(OFFICIAL_RELEASE_PREFIX):
        raise VersionGuardError("latest release response is not from the official repository")
    if payload.get("draft") is True or payload.get("prerelease") is True:
        raise VersionGuardError("latest release response points to a draft or prerelease")
    return {
        "version": tag[1:],
        "tag_name": tag,
        "html_url": html_url,
        "observed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": source,
    }


def fetch_official_latest(api_url: str, timeout: float = 15.0) -> dict[str, str]:
    if api_url != OFFICIAL_LATEST_RELEASE_API:
        raise VersionGuardError("latest release API must be the fixed official GitHub endpoint")
    request = urllib.request.Request(
        api_url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "clayz-presentation-component-version-guard/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed HTTPS URL is validated below.
            payload = json.loads(response.read())
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise VersionGuardError(f"official latest release could not be verified: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise VersionGuardError("official latest release response must be a JSON object")
    return _latest_release(payload, "official-github-latest-release")


def _validate_official_manifest(value: Mapping[str, Any], release_version: str) -> dict[str, Any]:
    if value.get("contract") != MANIFEST_CONTRACT or value.get("repository") != OFFICIAL_REPOSITORY:
        raise VersionGuardError("official component manifest identity is invalid")
    if value.get("latest_release_api") != OFFICIAL_LATEST_RELEASE_API or value.get("release_version") != release_version:
        raise VersionGuardError("official component manifest does not match the latest release")
    components = value.get("components")
    if not isinstance(components, Mapping) or not components:
        raise VersionGuardError("official component manifest has no components")
    return dict(value)


def fetch_official_component_manifest(tag_name: str, release_version: str, timeout: float = 15.0) -> dict[str, Any]:
    if tag_name == "v0.7.1":
        return _validate_official_manifest(V071_COMPONENT_MANIFEST, release_version)
    if tag_name != f"v{release_version}" or not SEMVER.fullmatch(release_version):
        raise VersionGuardError("latest release tag and version are inconsistent")
    url = f"{OFFICIAL_RAW_PREFIX}{tag_name}/config/component-versions.json"
    request = urllib.request.Request(url, headers={"User-Agent": "clayz-presentation-component-version-guard/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed official prefix and validated tag.
            payload = json.loads(response.read())
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise VersionGuardError(f"official component manifest could not be verified: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise VersionGuardError("official component manifest must be a JSON object")
    return _validate_official_manifest(payload, release_version)


def _collect_actual(root: Path) -> tuple[dict[str, str | None], dict[str, Any] | None]:
    _, config = _read_json(root / "config" / "default.json")
    release_version = (root / "VERSION").read_text(encoding="utf-8").strip() if (root / "VERSION").is_file() else str(config.get("identity", {}).get("version", ""))
    plugin_version: str | None = None
    plugin_path = root / ".codex-plugin" / "plugin.json"
    if plugin_path.is_file():
        _, plugin = _read_json(plugin_path)
        plugin_version = plugin.get("version") if isinstance(plugin.get("version"), str) else None
    actual: dict[str, str | None] = {
        "public-core": release_version,
        "plugin-manifest": plugin_version or release_version,
        "central-config": config.get("identity", {}).get("version"),
        "workflow-contract": config.get("workflow", {}).get("contract_version"),
        "runtime-preflight": config.get("runtime", {}).get("contract_version"),
        "personal-extension-runtime": _regex_value(
            root / "packages" / "personal_extension" / "resolver.py",
            r'^PERSONAL_EXTENSION_RUNTIME_CONTRACT\s*=\s*"io\.clayz\.presentation\.personal-extension-runtime/([^\"]+)"',
            "personal-extension-runtime",
        ),
        "resource-inventory": _regex_value(root / "packages" / "validators" / "resource_inventory.py", r'^CONTRACT\s*=\s*"io\.clayz\.presentation\.resource-inventory/([^\"]+)"', "resource-inventory"),
        "index-execution-evidence": _regex_value(root / "packages" / "validators" / "index_evidence.py", r'^CONTRACT\s*=\s*"io\.clayz\.presentation\.index-execution-evidence/([^\"]+)"', "index-execution-evidence"),
        "logic-package": _regex_value(root / "packages" / "validators" / "validate_logic_package.py", r'^CONTRACT_VERSION\s*=\s*"([^\"]+)"', "logic-package"),
        "copy-package": _regex_value(root / "skills" / "clayz-presentation-copy" / "references" / "copy-package-contract.md", r'^# PPT v([^ ]+) Copy-layer contract$', "copy-package"),
        "art-direction-plan": _regex_value(root / "packages" / "validators" / "validate_art_direction_plan.py", r'^CONTRACT_VERSION\s*=\s*"([^\"]+)"', "art-direction-plan"),
        "output-qa": _regex_value(root / "packages" / "validators" / "validate_output_qa.py", r'^CONTRACT_VERSION\s*=\s*"([^\"]+)"', "output-qa"),
        "supervision-report": _regex_value(root / "packages" / "validators" / "validate_supervision_report.py", r'^CONTRACT_VERSION\s*=\s*"([^\"]+)"', "supervision-report"),
        "owner-index-materialization": _regex_value(root / "scripts" / "materialize_owner_index.py", r'^CONTRACT\s*=\s*"io\.clayz\.presentation\.owner-index-materialization/([^\"]+)"', "owner-index-materialization"),
        "version-private-learning-audit": _regex_value(root / "scripts" / "bootstrap_owner_learning.py", r'^AUDIT_CONTRACT\s*=\s*"io\.clayz\.presentation\.version-private-learning-audit/([^\"]+)"', "version-private-learning-audit"),
    }
    personal: dict[str, Any] | None = None
    runtime_path = root / "runtime" / "personal-extension.json"
    if runtime_path.is_file():
        _, runtime = _read_json(runtime_path)
        extension = runtime.get("extension", {}) if isinstance(runtime.get("extension"), Mapping) else {}
        core = runtime.get("core", {}) if isinstance(runtime.get("core"), Mapping) else {}
        personal = {
            "runtime_contract": runtime.get("contract"),
            "core_version": core.get("version"),
            "profile_id": extension.get("profile_id"),
            "profile_version": extension.get("profile_version"),
            "runtime_lock_digest": runtime.get("lock", {}).get("digest") if isinstance(runtime.get("lock"), Mapping) else None,
        }
    return actual, personal


def build_report(root: Path, latest_release: Mapping[str, Any], official_manifest: Mapping[str, Any]) -> dict[str, Any]:
    root = root.resolve()
    manifest_raw, manifest = _read_json(root / "config" / "component-versions.json")
    if manifest.get("contract") != MANIFEST_CONTRACT or manifest.get("repository") != OFFICIAL_REPOSITORY:
        raise VersionGuardError("component version manifest identity is invalid")
    if manifest.get("latest_release_api") != OFFICIAL_LATEST_RELEASE_API:
        raise VersionGuardError("component version manifest does not name the official latest-release API")
    verified_official_manifest = _validate_official_manifest(official_manifest, str(latest_release.get("version", "")))
    expected = verified_official_manifest.get("components")
    if not isinstance(expected, Mapping) or not expected:
        raise VersionGuardError("component version manifest has no components")
    actual, personal = _collect_actual(root)
    local_release = str(actual.get("public-core") or "")
    components: list[dict[str, Any]] = []
    errors: list[str] = []
    if manifest.get("release_version") != verified_official_manifest.get("release_version") or manifest.get("components") != expected:
        errors.append("COMPONENT_MANIFEST_DRIFT")
    for component_id in sorted(expected):
        expected_version = str(expected[component_id])
        actual_version = actual.get(component_id)
        status = "current" if actual_version == expected_version else ("missing" if actual_version is None else "drift")
        if status != "current":
            errors.append("COMPONENT_VERSION_DRIFT")
        components.append({
            "component_id": component_id,
            "actual_version": actual_version,
            "expected_version": expected_version,
            "status": status,
            "evidence": f"mounted:{component_id}",
        })
    latest_version = str(latest_release.get("version", ""))
    if not SEMVER.fullmatch(local_release) or local_release != latest_version:
        errors.append("NON_LATEST_COMPONENT")
    if personal is not None and personal.get("core_version") != local_release:
        errors.append("PERSONAL_RUNTIME_VERSION_DRIFT")
    errors = sorted(set(errors))
    status = "latest" if not errors else "blocked"
    official_manifest_raw = json.dumps(verified_official_manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    brief = [
        f"公共核心 {local_release}；官方最新版本 {latest_version}。",
        "核心组件：" + "；".join(f"{item['component_id']}={item['actual_version'] or 'missing'}" for item in components),
    ]
    if personal is not None:
        brief.append(
            f"Personal Runtime：core={personal.get('core_version')}，profile={personal.get('profile_id')}@{personal.get('profile_version')}。"
        )
    brief.append("版本门禁通过，可以继续。" if status == "latest" else f"版本门禁失败：{', '.join(errors)}；不得进入 Logic。")
    return {
        "contract": REPORT_CONTRACT,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "repository": OFFICIAL_REPOSITORY,
        "status": status,
        "local_release_version": local_release,
        "latest_release": dict(latest_release),
        "manifest_sha256": _sha256_bytes(official_manifest_raw),
        "local_manifest_sha256": _sha256_bytes(manifest_raw),
        "components": components,
        "personal_extension": personal,
        "error_codes": errors,
        "user_brief": brief,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--latest-release-json", type=Path, help="host-materialized official GitHub Latest Release response")
    parser.add_argument("--latest-component-manifest-json", type=Path, help="host-materialized component manifest from the latest release tag")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--brief-output", type=Path)
    args = parser.parse_args()
    try:
        _, manifest = _read_json(args.root / "config" / "component-versions.json")
        if args.latest_release_json:
            _, payload = _read_json(args.latest_release_json)
            latest = _latest_release(payload, "official-host-fetched-github-response")
        else:
            latest = fetch_official_latest(str(manifest.get("latest_release_api", "")))
        if args.latest_component_manifest_json:
            _, official_manifest = _read_json(args.latest_component_manifest_json)
            official_manifest = _validate_official_manifest(official_manifest, latest["version"])
        else:
            official_manifest = fetch_official_component_manifest(latest["tag_name"], latest["version"])
        report = build_report(args.root, latest, official_manifest)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        if args.brief_output:
            args.brief_output.parent.mkdir(parents=True, exist_ok=True)
            args.brief_output.write_text("\n".join(report["user_brief"]) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({"ok": report["status"] == "latest", "status": report["status"], "brief": report["user_brief"]}, ensure_ascii=False))
        return 0 if report["status"] == "latest" else 2
    except (OSError, json.JSONDecodeError, VersionGuardError, ValueError) as exc:
        print(f"ERROR: LATEST_VERSION_UNVERIFIED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
