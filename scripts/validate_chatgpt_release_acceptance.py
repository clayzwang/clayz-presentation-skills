#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Fail closed unless a private ChatGPT candidate acceptance receipt matches this release."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(receipt: Any, *, version: str, commit: str, component_manifest: Path) -> list[str]:
    errors: list[str] = []
    required = {
        "contract", "status", "version", "candidate_commit", "personal_candidate_sha256",
        "component_manifest_sha256", "chatgpt_skill_id", "acceptance_url", "accepted_by",
        "accepted_at", "startup_gate_status", "private_learning_status",
        "learning_audit_sha256", "user_acceptance",
    }
    if not isinstance(receipt, dict):
        return ["receipt must be an object"]
    missing = sorted(required - set(receipt))
    if missing:
        errors.append(f"receipt missing keys {missing}")
    if set(receipt) - required:
        errors.append(f"receipt has unsupported keys {sorted(set(receipt) - required)}")
    if receipt.get("contract") != "io.clayz.presentation.chatgpt-release-acceptance/1.0":
        errors.append("receipt.contract is unsupported")
    if receipt.get("status") != "accepted" or receipt.get("user_acceptance") is not True:
        errors.append("receipt must record explicit user acceptance")
    if receipt.get("version") != version:
        errors.append("receipt.version does not match VERSION")
    if not COMMIT.fullmatch(str(receipt.get("candidate_commit", ""))) or receipt.get("candidate_commit") != commit:
        errors.append("receipt.candidate_commit does not match the release commit")
    for key in ("personal_candidate_sha256", "component_manifest_sha256", "learning_audit_sha256"):
        if not SHA256.fullmatch(str(receipt.get(key, ""))):
            errors.append(f"receipt.{key} must be lowercase SHA-256")
    if receipt.get("component_manifest_sha256") != _sha256(component_manifest):
        errors.append("receipt.component_manifest_sha256 does not match the release tree")
    if not str(receipt.get("chatgpt_skill_id", "")).strip():
        errors.append("receipt.chatgpt_skill_id must be non-empty")
    if not str(receipt.get("acceptance_url", "")).startswith("https://chatgpt.com/"):
        errors.append("receipt.acceptance_url must be a ChatGPT URL")
    if not str(receipt.get("accepted_by", "")).strip() or not str(receipt.get("accepted_at", "")).strip():
        errors.append("receipt must identify who accepted it and when")
    if receipt.get("startup_gate_status") not in {"candidate-validated", "latest"}:
        errors.append("receipt.startup_gate_status is invalid")
    if receipt.get("private_learning_status") != "READY-FOR-LOGIC":
        errors.append("receipt.private_learning_status must be READY-FOR-LOGIC")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--component-manifest", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
        errors = validate(receipt, version=args.version, commit=args.commit, component_manifest=args.component_manifest)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 2
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"FAILED: {len(errors)} acceptance error(s)")
        return 1
    print("PASS: private ChatGPT upload, startup gate, learning audit, and user acceptance match this release")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
