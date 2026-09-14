#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Execute measured checks, reuse unchanged evidence, and assemble audit snapshots."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
    temporary.replace(path)


def run_check(root, check_id, command, inputs, outputs, *, reuse=False, timeout=120):
    """Reuse only explicitly deterministic checks whose inputs AND outputs match.

    Declare scripts, config, font inventory, renderer identity and input artifacts
    as inputs. Do not cache live-source queries, application acceptance, or
    professional judgments. Output always remains subordinate to final deck QA.
    """
    root = Path(root).resolve()
    if not check_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in check_id):
        raise ValueError("check-id must contain only letters, digits, dash or underscore")
    inputs = [Path(p).resolve() for p in inputs]
    outputs = [Path(p).resolve() for p in outputs]
    if not inputs or not outputs:
        raise ValueError("checks require explicit input and output artifacts")
    state = root / ".clayz-checks" / (check_id + ".json")
    input_hashes = {str(p): digest(p) for p in inputs}
    signature = canonical({"command": command, "cwd": str(root), "inputs": input_hashes})
    if reuse and state.is_file():
        receipt = json.loads(state.read_text(encoding="utf-8"))
        if receipt.get("signature") == signature and receipt.get("returncode") == 0 and all(
            p.is_file() and receipt.get("outputs", {}).get(str(p)) == digest(p) for p in outputs
        ):
            return {**receipt, "reused": True, "elapsed_seconds_this_call": 0}
    started = time.monotonic()
    # shell=False: no expansion, credential probing, or string-built shell commands.
    result = subprocess.run(command, cwd=root, timeout=timeout, capture_output=True)
    elapsed = time.monotonic() - started
    inputs_unchanged = all(p.is_file() and input_hashes[str(p)] == digest(p) for p in inputs)
    receipt = {
        "check_id": check_id, "signature": signature, "returncode": result.returncode if inputs_unchanged else -1,
        "inputs_unchanged": inputs_unchanged,
        "elapsed_seconds_this_call": elapsed, "reused": False,
        "outputs": {str(p): digest(p) for p in outputs if p.is_file()},
        "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
    }
    write_json(state, receipt)
    with (state.parent / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(receipt, ensure_ascii=False) + "\n")
    if receipt["returncode"] or len(receipt["outputs"]) != len(outputs):
        raise RuntimeError(f"check {check_id} failed or did not produce its declared artifacts; see {state}")
    return receipt


def snapshots(package_path, plan_path):
    package = json.loads(Path(package_path).read_text(encoding="utf-8"))
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    values = {
        "logic": ({"brief": package["brief"], "logic_layer": package["logic_layer"]}, package_path),
        "copy": (package["copy_layer"], package_path),
        "art_direction": ({k: plan.get(k) for k in (
            "communication_contract", "art_direction", "decision_log", "typography_contract", "deck_rhythm", "slides"
        )}, plan_path),
    }
    return {stage: {"artifact_sha256": digest(path), "snapshot_sha256": canonical(value), "snapshot": value}
            for stage, (value, path) in values.items()}


def checkpoint(root, run_id, request, phase, artifacts):
    root = Path(root).resolve()
    state = {"run_id": run_id, "task_request_sha256": digest(request), "next_phase": phase,
             "artifacts": {str(Path(p).resolve()): digest(p) for p in artifacts}}
    write_json(root / "run-context-checkpoint.json", state)
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    run = sub.add_parser("check")
    run.add_argument("--root", type=Path, required=True)
    run.add_argument("--check-id", required=True)
    run.add_argument("--input", type=Path, action="append", required=True)
    run.add_argument("--output", type=Path, action="append", required=True)
    run.add_argument("--reuse", action="store_true")
    run.add_argument("--timeout", type=int, default=120)
    run.add_argument("command", nargs=argparse.REMAINDER)
    snap = sub.add_parser("snapshots")
    snap.add_argument("--package", type=Path, required=True)
    snap.add_argument("--plan", type=Path, required=True)
    snap.add_argument("--output", type=Path, required=True)
    cp = sub.add_parser("checkpoint")
    cp.add_argument("--root", type=Path, required=True)
    cp.add_argument("--run-id", required=True)
    cp.add_argument("--request", type=Path, required=True)
    cp.add_argument("--next-phase", required=True)
    cp.add_argument("--artifact", type=Path, action="append", default=[])
    args = parser.parse_args()
    if args.action == "check":
        command = args.command[1:] if args.command[:1] == ["--"] else args.command
        print(json.dumps(run_check(args.root, args.check_id, command, args.input, args.output,
                                  reuse=args.reuse, timeout=args.timeout)))
    elif args.action == "snapshots":
        write_json(args.output, snapshots(args.package, args.plan))
        print(json.dumps({"output": str(args.output), "status": "written"}))
    else:
        print(json.dumps(checkpoint(args.root, args.run_id, args.request, args.next_phase, args.artifact)))


if __name__ == "__main__":
    main()
