# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Small deterministic helpers used by the retrieval runtime."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

from .constants import IndexRuntimeError


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise IndexRuntimeError(message)


def require_nonempty_string(value: Any, path: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), f"{path} must be a non-empty string")
    return value


def require_string_list(value: Any, path: str) -> list[str]:
    require(isinstance(value, list), f"{path} must be an array")
    require(all(isinstance(item, str) and item for item in value), f"{path} must contain non-empty strings")
    require(len(value) == len(set(value)), f"{path} must not contain duplicates")
    return list(value)


def tokenize(text: str) -> list[str]:
    """Tokenize Latin terms and CJK bigrams without third-party dependencies."""

    lowered = text.casefold()
    latin = re.findall(r"[a-z0-9][a-z0-9_+.-]*", lowered)
    cjk_runs = re.findall(r"[\u3400-\u9fff]+", lowered)
    cjk: list[str] = []
    for run in cjk_runs:
        if len(run) == 1:
            cjk.append(run)
        else:
            cjk.extend(run[index : index + 2] for index in range(len(run) - 1))
    return latin + cjk
