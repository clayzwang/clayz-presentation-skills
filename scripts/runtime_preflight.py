#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Run one Clayz runtime capability scan and write a locked route plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.runtime.preflight import (  # noqa: E402
    HOST_INVENTORY_CONTRACT,
    RUN_CHALLENGE_CONSUMPTION_CONTRACT,
    RUN_CHALLENGE_ISSUANCE_CONTRACT,
    build_preflight_report,
    issue_run_challenge,
    task_root_digest,
    validate_run_challenge,
)


def default_config_path() -> Path:
    personal = ROOT / "config" / "personal-extension-resolved.json"
    return personal if personal.is_file() else ROOT / "config" / "default.json"


def _write_payload(payload: dict[str, object], output: Path | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def _issue_challenge(task_request: Path, output: Path) -> None:
    task_root = output.resolve().parent
    challenge = issue_run_challenge(task_request.read_bytes(), task_root=task_root)
    challenge_raw = (json.dumps(challenge, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open("xb") as handle:
            handle.write(challenge_raw)
    except FileExistsError as exc:
        raise ValueError("challenge output already exists; use a new task-local path") from exc
    challenge_sha256 = hashlib.sha256(challenge_raw).hexdigest()
    issuance_path = task_root / Path(*PurePosixPath(challenge["issuance_record"]).parts)
    issuance_path.parent.mkdir(parents=True, exist_ok=True)
    issuance = {
        "contract": RUN_CHALLENGE_ISSUANCE_CONTRACT,
        "challenge_sha256": challenge_sha256,
        "run_id": challenge["run_id"],
        "task_request_sha256": challenge["task_request_sha256"],
        "nonce": challenge["nonce"],
        "task_root_sha256": challenge["task_root_sha256"],
        "issued_at": challenge["issued_at"],
        "expires_at": challenge["expires_at"],
    }
    issuance_raw = (json.dumps(issuance, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    try:
        with issuance_path.open("xb") as handle:
            handle.write(issuance_raw)
    except FileExistsError as exc:
        raise ValueError("run challenge issuance record already exists") from exc


def _validate_issuance_receipt(
    challenge_path: Path,
    challenge: dict[str, object],
    challenge_sha256: str,
) -> dict[str, object]:
    task_root = challenge_path.resolve().parent
    validate_run_challenge(
        challenge,
        challenge_sha256=challenge_sha256,
        task_root=task_root,
    )
    relative = PurePosixPath(str(challenge.get("issuance_record", "")))
    issuance_path = (task_root / Path(*relative.parts)).resolve()
    try:
        issuance_path.relative_to(task_root)
    except ValueError as exc:
        raise ValueError("run challenge issuance record escapes the task root") from exc
    raw = issuance_path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get("contract") != RUN_CHALLENGE_ISSUANCE_CONTRACT:
        raise ValueError("run challenge issuance record is missing or unsupported")
    expected = {
        "challenge_sha256": challenge_sha256,
        "run_id": challenge.get("run_id"),
        "task_request_sha256": challenge.get("task_request_sha256"),
        "nonce": challenge.get("nonce"),
        "task_root_sha256": challenge.get("task_root_sha256"),
        "issued_at": challenge.get("issued_at"),
        "expires_at": challenge.get("expires_at"),
    }
    if any(value.get(key) != item for key, item in expected.items()):
        raise ValueError("run challenge issuance record does not match the challenge")
    return {
        **value,
        "receipt_path": issuance_path.as_posix(),
        "receipt_sha256": hashlib.sha256(raw).hexdigest(),
    }


def _validate_host_evidence(
    attestation: dict[str, object] | None,
    attestation_path: Path | None,
    challenge: dict[str, object],
    challenge_sha256: str,
) -> dict[str, object] | None:
    if not attestation or attestation.get("available") is not True:
        return None
    if attestation_path is None:
        raise ValueError("available host attestation requires a source file")
    receipts = attestation.get("evidence_receipts")
    if not isinstance(receipts, list) or not receipts:
        raise ValueError("available host attestation requires evidence_receipts")
    validated: list[dict[str, object]] = []
    observed_capabilities: set[str] = set()
    for index, receipt in enumerate(receipts):
        if not isinstance(receipt, dict):
            raise ValueError(f"host evidence receipt {index} must be an object")
        relative = PurePosixPath(str(receipt.get("artifact", "")))
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise ValueError(f"host evidence receipt {index} has an unsafe artifact path")
        artifact = (attestation_path.resolve().parent / Path(*relative.parts)).resolve()
        try:
            artifact.relative_to(attestation_path.resolve().parent)
        except ValueError as exc:
            raise ValueError(f"host evidence receipt {index} escapes its evidence root") from exc
        raw = artifact.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != receipt.get("sha256"):
            raise ValueError(f"host evidence receipt {index} SHA-256 mismatch")
        inventory = json.loads(raw)
        if not isinstance(inventory, dict) or inventory.get("contract") != HOST_INVENTORY_CONTRACT:
            raise ValueError(f"host evidence receipt {index} has an unsupported inventory contract")
        for key in ("run_id", "task_request_sha256", "nonce"):
            if inventory.get(key) != challenge.get(key):
                raise ValueError(f"host inventory {index} does not match challenge {key}")
        if inventory.get("challenge_sha256") != challenge_sha256:
            raise ValueError(f"host inventory {index} does not match challenge SHA-256")
        capabilities = inventory.get("capabilities")
        if not isinstance(capabilities, list) or any(not isinstance(item, str) or not item for item in capabilities):
            raise ValueError(f"host inventory {index} capabilities must be a string array")
        observed_capabilities.update(capabilities)
        validated.append(dict(receipt))
    declared = attestation.get("capabilities")
    if not isinstance(declared, list) or set(declared) != observed_capabilities:
        raise ValueError("host attestation capabilities must exactly equal evidence inventory capabilities")
    return {
        "validated": True,
        "challenge_sha256": challenge_sha256,
        "evidence_receipts": validated,
    }


def _consume_challenge(challenge_path: Path, challenge: dict[str, object], challenge_sha256: str) -> dict[str, object]:
    task_root = challenge_path.resolve().parent
    if challenge.get("task_root_sha256") != task_root_digest(task_root):
        raise ValueError("run challenge is not bound to the current task root")
    receipt_root = task_root / ".clayz-run-challenges" / "consumed"
    receipt_root.mkdir(parents=True, exist_ok=True)
    receipt_path = receipt_root / f"{challenge_sha256}.json"
    payload: dict[str, object] = {
        "contract": RUN_CHALLENGE_CONSUMPTION_CONTRACT,
        "challenge_sha256": challenge_sha256,
        "run_id": challenge.get("run_id"),
        "task_request_sha256": challenge.get("task_request_sha256"),
        "nonce": challenge.get("nonce"),
        "task_root_sha256": challenge.get("task_root_sha256"),
        "consumed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    raw = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    try:
        with receipt_path.open("xb") as handle:
            handle.write(raw)
    except FileExistsError as exc:
        raise ValueError("run challenge was already consumed; issue a fresh challenge") from exc
    return {
        **payload,
        "receipt_path": receipt_path.resolve().as_posix(),
        "receipt_sha256": hashlib.sha256(raw).hexdigest(),
    }


def _validate_task_request(task_request_path: Path, challenge: dict[str, object]) -> None:
    """Bind the scan to the same immutable task-request bytes used at issuance."""

    actual = hashlib.sha256(task_request_path.read_bytes()).hexdigest()
    if actual != challenge.get("task_request_sha256"):
        raise ValueError("current task request does not match the fresh run challenge")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issue-challenge", action="store_true", help="Issue a fresh run challenge before the single capability scan")
    parser.add_argument("--task-request", type=Path, help="Canonical current task-request bytes required for issuance and scan binding")
    parser.add_argument("--challenge", type=Path, help="Fresh run challenge emitted by --issue-challenge")
    parser.add_argument("--config", type=Path, default=default_config_path())
    parser.add_argument("--model-profile", choices=["A", "B", "C", "D"])
    parser.add_argument("--model-capabilities", type=Path, help="JSON object used only when --model-profile is omitted")
    parser.add_argument("--host-capabilities", type=Path, help="JSON object declaring inspected host presentation-tool capabilities")
    parser.add_argument("--require", action="append", default=[], help="Add a stricter required capability; repeat as needed")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.issue_challenge:
            if args.task_request is None or args.output is None:
                raise ValueError("--issue-challenge requires --task-request and --output")
            _issue_challenge(args.task_request, args.output)
            return 0
        if args.challenge is None or args.task_request is None:
            raise ValueError("the capability scan requires --challenge and the same --task-request used at issuance")
        challenge_raw = args.challenge.read_bytes()
        challenge = json.loads(challenge_raw)
        challenge_sha256 = hashlib.sha256(challenge_raw).hexdigest()
        validate_run_challenge(
            challenge,
            challenge_sha256=challenge_sha256,
            task_root=args.challenge.resolve().parent,
        )
        issuance = _validate_issuance_receipt(args.challenge, challenge, challenge_sha256)
        _validate_task_request(args.task_request, challenge)
        config_raw = args.config.read_bytes()
        config = json.loads(config_raw)
        model_caps = json.loads(args.model_capabilities.read_text(encoding="utf-8")) if args.model_capabilities else None
        host_caps = json.loads(args.host_capabilities.read_text(encoding="utf-8")) if args.host_capabilities else None
        host_context = _validate_host_evidence(host_caps, args.host_capabilities, challenge, challenge_sha256)
        consumption = _consume_challenge(args.challenge, challenge, challenge_sha256)
        report = build_preflight_report(
            config,
            model_profile=args.model_profile,
            model_capabilities=model_caps,
            host_capabilities=host_caps,
            required_capabilities=args.require or None,
            run_challenge=challenge,
            run_challenge_sha256=challenge_sha256,
            run_challenge_issuance=issuance,
            run_challenge_consumption=consumption,
            host_attestation_context=host_context,
            config_binding={
                "path": args.config.resolve().as_posix(),
                "sha256": hashlib.sha256(config_raw).hexdigest(),
                "source": "personal-resolved" if args.config.name == "personal-extension-resolved.json" else "public-default",
            },
        )
        _write_payload(report, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0 if report["selected_route"].get("available") or report["selected_route"].get("attemptable") else 1


if __name__ == "__main__":
    raise SystemExit(main())
