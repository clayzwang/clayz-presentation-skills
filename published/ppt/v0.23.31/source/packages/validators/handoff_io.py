# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Immutable handoff retries: preserve original evidence and timestamps."""
import hashlib
import json
from pathlib import Path

GENERATED = {"recorded_at", "audited_at", "reconciled_at", "created_at", "record_sha256"}

def write_record(path, value):
    path = Path(path).expanduser().resolve()
    if path.exists():
        old = json.loads(path.read_text(encoding="utf-8"))
        project = lambda row: {k: v for k, v in row.items() if k not in GENERATED}
        if not value.get("contract") or project(old) != project(value):
            raise FileExistsError(f"{path}: different input; preserve this record and use a new revision. Retry only this handoff.")
        def verify(item):
            if isinstance(item, dict):
                if {"path", "sha256", "bytes"} <= item.keys():
                    raw = Path(item["path"]).read_bytes()
                    if len(raw) != item["bytes"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
                        raise ValueError(f"{path}: bound evidence changed; cannot reuse record")
                for child in item.values():
                    verify(child)
            elif isinstance(item, list):
                for child in item:
                    verify(child)
        verify(old)
        if "record_sha256" in old:
            raw = json.dumps({k: v for k, v in old.items() if k != "record_sha256"}, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
            if hashlib.sha256(raw).hexdigest() != old["record_sha256"]:
                raise ValueError(f"{path}: existing record checksum is invalid")
        contract = old.get("contract", "")
        if contract.startswith("io.clayz.presentation.reader-"):
            from packages.validators.reader_review import validate_first, validate_review, validate_packet
            {"io.clayz.presentation.reader-first-read/1.0": validate_first,
             "io.clayz.presentation.reader-review/1.0": validate_review,
             "io.clayz.presentation.reader-packet/1.0": validate_packet}[contract](old)
        elif contract == "io.clayz.presentation.independent-audit/1.0":
            from packages.validators.independent_audit import validate_auditor_artifact
            validate_auditor_artifact(old)
        value.clear()
        value.update(old)
        return
    serialized = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(serialized)
