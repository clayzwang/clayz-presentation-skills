# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Provider snapshots for local, host, built-in, and ephemeral indexes."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from .constants import IndexRuntimeError
from .utils import require, require_nonempty_string, sha256_json
from .validation import validate_record


@dataclass(frozen=True)
class IndexProvider:
    """A deterministic snapshot of records from one provider."""

    provider_id: str
    records: tuple[dict[str, Any], ...]

    @classmethod
    def from_records(cls, provider_id: str, records: Iterable[Mapping[str, Any]]) -> "IndexProvider":
        require_nonempty_string(provider_id, "provider_id")
        normalized: list[dict[str, Any]] = []
        seen: set[str] = set()
        for raw in records:
            record = validate_record(raw)
            require(record["provider_id"] == provider_id, "record.provider_id must match provider")
            record_id = record["record_id"]
            require(record_id not in seen, f"duplicate record_id within provider: {record_id}")
            seen.add(record_id)
            normalized.append(record)
        normalized.sort(key=lambda item: item["record_id"])
        return cls(provider_id=provider_id, records=tuple(normalized))

    @classmethod
    def from_jsonl(cls, provider_id: str, path: Path) -> "IndexProvider":
        rows: list[dict[str, Any]] = []
        if path.exists():
            for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if not raw.strip():
                    continue
                try:
                    value = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise IndexRuntimeError(f"{path}:{line_number}: {exc}") from exc
                require(isinstance(value, dict), f"{path}:{line_number}: expected an object")
                rows.append(value)
        return cls.from_records(provider_id, rows)

    def snapshot(self) -> dict[str, Any]:
        payload = [
            {
                "record_id": record["record_id"],
                "source_sha256": record["source"]["sha256"],
                "quality_status": record["governance"]["quality_status"],
                "rights": record["rights"],
                "payload": record["payload"],
            }
            for record in self.records
        ]
        return {"provider_id": self.provider_id, "digest": sha256_json(payload), "record_count": len(payload)}
