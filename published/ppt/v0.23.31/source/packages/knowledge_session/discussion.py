# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Immutable discussion drafts and exact human confirmations.

This module deliberately has no filesystem write path.  ``prepare_draft`` may
read attachment bytes to bind their hashes, but the returned review object
contains only portable metadata, hashes, and byte counts.  The storage layer is
responsible for publishing a confirmed draft.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DRAFT_CONTRACT = "io.clayz.presentation.discussion-draft/1.0"
CONFIRMATION_CONTRACT = "io.clayz.presentation.discussion-confirmation/1.0"
STAGES = {"logic", "copy", "art-direction", "output"}
PROVENANCE = {"source-fact", "user-experience", "joint-inference"}

_SESSION_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_ATTACHMENT_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")

_CONTENT_FIELDS = {
    "session_id",
    "title",
    "stage",
    "applicable_stages",
    "consensus",
    "applicability",
    "limitations",
    "provenance",
    "evidence_refs",
    "unresolved_questions",
    "language",
    "purpose_tags",
    "attachments",
    "supersedes",
}
_REQUIRED_CONTENT_FIELDS = _CONTENT_FIELDS - {"applicable_stages"}
_DRAFT_FIELDS = _CONTENT_FIELDS | {"contract", "draft_sha256"}
_CONFIRMATION_FIELDS = {
    "contract",
    "draft_sha256",
    "confirmed_by",
    "decision",
    "confirmed_at",
    "confirm_human_decision",
}
_ATTACHMENT_METADATA_FIELDS = {
    "attachment_id",
    "filename",
    "origin",
    "rights",
    "locator",
}
_ATTACHMENT_DRAFT_FIELDS = _ATTACHMENT_METADATA_FIELDS | {"sha256", "bytes"}


class DiscussionError(ValueError):
    """Raised when a discussion draft or confirmation is not trustworthy."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DiscussionError(message)


def _nonempty_string(value: Any, path: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{path} must be a non-empty string")
    return value


def _string_list(value: Any, path: str) -> list[str]:
    _require(isinstance(value, list), f"{path} must be a list")
    _require(
        all(isinstance(item, str) and bool(item.strip()) for item in value),
        f"{path} must contain non-empty strings",
    )
    _require(len(value) == len(set(value)), f"{path} must not contain duplicates")
    return list(value)


def canonical_sha256(value: Any) -> str:
    """Return the SHA-256 of deterministic, UTF-8 canonical JSON."""

    try:
        canonical = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise DiscussionError(f"value is not canonical JSON: {exc}") from exc
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _validate_timestamp(value: Any, path: str) -> str:
    text = _nonempty_string(value, path)
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DiscussionError(f"{path} must be ISO-8601") from exc
    return text


def _validate_attachment_metadata(value: Any, path: str, *, prepared: bool) -> dict[str, Any]:
    _require(isinstance(value, Mapping), f"{path} must be an object")
    item = copy.deepcopy(dict(value))
    allowed = _ATTACHMENT_DRAFT_FIELDS if prepared else _ATTACHMENT_METADATA_FIELDS
    _require(set(item) == allowed, f"{path} must contain exactly {sorted(allowed)}")

    attachment_id = _nonempty_string(item.get("attachment_id"), f"{path}.attachment_id")
    _require(bool(_ATTACHMENT_ID.fullmatch(attachment_id)), f"{path}.attachment_id has invalid characters")

    filename = _nonempty_string(item.get("filename"), f"{path}.filename")
    _require("/" not in filename and "\\" not in filename, f"{path}.filename must be one path component")
    _require(filename not in {".", ".."} and ":" not in filename, f"{path}.filename is unsafe")
    _require(not any(ord(char) < 32 for char in filename), f"{path}.filename contains a control character")

    for key in ("origin", "rights"):
        _nonempty_string(item.get(key), f"{path}.{key}")
    # A locator is useful when a page/section is known; an explicit null or
    # empty locator keeps the fact that no precise locator was available.
    locator = item.get("locator")
    _require(locator is None or isinstance(locator, str), f"{path}.locator must be a string or null")

    if prepared:
        sha256 = _nonempty_string(item.get("sha256"), f"{path}.sha256")
        _require(bool(_SHA256.fullmatch(sha256)), f"{path}.sha256 must be lowercase SHA-256")
        byte_count = item.get("bytes")
        _require(isinstance(byte_count, int) and not isinstance(byte_count, bool) and byte_count >= 0, f"{path}.bytes must be a non-negative integer")
    return item


def _validate_content(value: Mapping[str, Any], *, prepared_attachments: bool) -> dict[str, Any]:
    _require(isinstance(value, Mapping), "discussion content must be an object")
    normalized = copy.deepcopy(dict(value))
    missing = _REQUIRED_CONTENT_FIELDS - set(normalized)
    _require(not missing, f"discussion content is missing fields: {sorted(missing)}")
    unknown = set(normalized) - _CONTENT_FIELDS
    _require(not unknown, f"discussion content has unsupported fields: {sorted(unknown)}")

    session_id = _nonempty_string(normalized.get("session_id"), "session_id")
    _require(len(session_id) <= 80, "session_id must be at most 80 characters")
    _require(bool(_SESSION_ID.fullmatch(session_id)), "session_id has invalid characters")
    for key in ("title", "consensus", "language"):
        _nonempty_string(normalized.get(key), key)

    stage = _nonempty_string(normalized.get("stage"), "stage")
    _require(stage in STAGES, f"unsupported stage: {stage}")
    applicable_stages = normalized.get("applicable_stages", [stage])
    applicable_stages = _string_list(applicable_stages, "applicable_stages")
    _require(set(applicable_stages).issubset(STAGES), "applicable_stages contains an unsupported stage")
    _require(stage in set(applicable_stages), "applicable_stages must include the owner stage")
    normalized["applicable_stages"] = applicable_stages

    for key in ("applicability", "limitations", "evidence_refs", "unresolved_questions", "purpose_tags"):
        normalized[key] = _string_list(normalized.get(key), key)

    provenance = _nonempty_string(normalized.get("provenance"), "provenance")
    _require(provenance in PROVENANCE, f"unsupported provenance: {provenance}")
    if provenance == "source-fact":
        _require(bool(normalized["evidence_refs"]), "source-fact requires at least one evidence_ref")

    attachments = normalized.get("attachments")
    _require(isinstance(attachments, list), "attachments must be a list")
    normalized_attachments: list[dict[str, Any]] = []
    attachment_ids: set[str] = set()
    for index, raw in enumerate(attachments):
        item = _validate_attachment_metadata(raw, f"attachments[{index}]", prepared=prepared_attachments)
        attachment_id = item["attachment_id"]
        _require(attachment_id not in attachment_ids, f"duplicate attachment_id: {attachment_id}")
        attachment_ids.add(attachment_id)
        normalized_attachments.append(item)
    normalized["attachments"] = normalized_attachments

    # Attachment-free personal or jointly inferred knowledge remains valid, but
    # its limits must stay visible in the review object.
    if provenance in {"user-experience", "joint-inference"} and not normalized["evidence_refs"] and not normalized_attachments:
        _require(bool(normalized["limitations"]), "attachment-free discussion knowledge requires visible limitations")

    supersedes = normalized.get("supersedes")
    _require(supersedes is None or (isinstance(supersedes, str) and bool(_SHA256.fullmatch(supersedes))), "supersedes must be null or a lowercase SHA-256")
    return normalized


def _validate_draft_body(draft: Mapping[str, Any]) -> dict[str, Any]:
    _require(isinstance(draft, Mapping), "draft must be an object")
    normalized = copy.deepcopy(dict(draft))
    _require(set(normalized) == _DRAFT_FIELDS, f"draft must contain exactly {sorted(_DRAFT_FIELDS)}")
    _require(normalized.get("contract") == DRAFT_CONTRACT, f"draft.contract must be {DRAFT_CONTRACT}")
    content = {key: normalized[key] for key in _CONTENT_FIELDS}
    return {
        "contract": DRAFT_CONTRACT,
        **_validate_content(content, prepared_attachments=True),
        "draft_sha256": normalized["draft_sha256"],
    }


def validate_draft(draft: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a prepared draft and its self-excluding canonical digest."""

    normalized = _validate_draft_body(draft)
    digest = _nonempty_string(normalized.get("draft_sha256"), "draft_sha256")
    _require(bool(_SHA256.fullmatch(digest)), "draft_sha256 must be lowercase SHA-256")
    body = {key: value for key, value in normalized.items() if key != "draft_sha256"}
    _require(canonical_sha256(body) == digest, "draft_sha256 does not match canonical draft content")
    return normalized


def _attachment_bindings(bindings: Mapping[str, Any]) -> dict[str, Path]:
    _require(isinstance(bindings, Mapping), "attachments must be a mapping of attachment_id to path")
    result: dict[str, Path] = {}
    for key, value in bindings.items():
        attachment_id = _nonempty_string(key, "attachment binding id")
        _require(bool(_ATTACHMENT_ID.fullmatch(attachment_id)), f"attachment binding id has invalid characters: {attachment_id}")
        _require(isinstance(value, (str, Path)) or hasattr(value, "__fspath__"), f"attachment binding {attachment_id} must be a path")
        try:
            result[attachment_id] = Path(value)
        except TypeError as exc:
            raise DiscussionError(f"attachment binding {attachment_id} is not a path") from exc
    return result


def prepare_draft(content: dict, attachments: dict[str, Path]) -> dict[str, Any]:
    """Read attachment bytes and return a deterministic immutable review object."""

    normalized = _validate_content(content, prepared_attachments=False)
    bindings = _attachment_bindings(attachments)
    declared = {item["attachment_id"] for item in normalized["attachments"]}
    provided = set(bindings)
    _require(provided == declared, f"attachment bindings must exactly match metadata IDs; missing={sorted(declared - provided)}, extra={sorted(provided - declared)}")

    prepared_attachments: list[dict[str, Any]] = []
    for item in normalized["attachments"]:
        attachment_id = item["attachment_id"]
        path = bindings[attachment_id]
        try:
            if not path.is_file():
                raise DiscussionError(f"attachment does not exist or is not a file: {attachment_id}")
            payload = path.read_bytes()
        except OSError as exc:
            raise DiscussionError(f"cannot read attachment {attachment_id}: {exc}") from exc
        prepared_attachments.append({
            **item,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
        })

    body = {
        "contract": DRAFT_CONTRACT,
        **normalized,
        "attachments": prepared_attachments,
    }
    body["draft_sha256"] = canonical_sha256(body)
    return validate_draft(body)


def validate_confirmation(draft: Mapping[str, Any], confirmation: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a confirmation and bind it to the exact prepared draft hash."""

    normalized_draft = validate_draft(draft)
    _require(isinstance(confirmation, Mapping), "confirmation must be an object")
    normalized = copy.deepcopy(dict(confirmation))
    _require(set(normalized) == _CONFIRMATION_FIELDS, f"confirmation must contain exactly {sorted(_CONFIRMATION_FIELDS)}")
    _require(normalized.get("contract") == CONFIRMATION_CONTRACT, f"confirmation.contract must be {CONFIRMATION_CONTRACT}")
    draft_sha256 = _nonempty_string(normalized.get("draft_sha256"), "confirmation.draft_sha256")
    _require(bool(_SHA256.fullmatch(draft_sha256)), "confirmation.draft_sha256 must be lowercase SHA-256")
    _require(draft_sha256 == normalized_draft["draft_sha256"], "confirmation does not match draft_sha256")
    _nonempty_string(normalized.get("confirmed_by"), "confirmation.confirmed_by")
    _nonempty_string(normalized.get("decision"), "confirmation.decision")
    _validate_timestamp(normalized.get("confirmed_at"), "confirmation.confirmed_at")
    _require(normalized.get("confirm_human_decision") is True, "confirmation requires confirm_human_decision=true")
    return normalized


def confirm_draft(
    draft: Mapping[str, Any],
    *,
    expected_sha256: str,
    confirmed_by: str,
    decision: str,
    confirm_human_decision: bool,
) -> dict[str, Any]:
    """Record the actual user's assertion for one exact draft digest."""

    _require(confirm_human_decision is True, "confirmation requires confirm_human_decision=true")
    normalized_draft = validate_draft(draft)
    _require(isinstance(expected_sha256, str) and bool(_SHA256.fullmatch(expected_sha256)), "expected_sha256 must be lowercase SHA-256")
    _require(expected_sha256 == normalized_draft["draft_sha256"], "expected_sha256 does not match draft_sha256")
    confirmation = {
        "contract": CONFIRMATION_CONTRACT,
        "draft_sha256": normalized_draft["draft_sha256"],
        "confirmed_by": _nonempty_string(confirmed_by, "confirmed_by"),
        "decision": _nonempty_string(decision, "decision"),
        "confirmed_at": _utc_now(),
        "confirm_human_decision": True,
    }
    return validate_confirmation(normalized_draft, confirmation)


__all__ = [
    "CONFIRMATION_CONTRACT",
    "DRAFT_CONTRACT",
    "DiscussionError",
    "canonical_sha256",
    "confirm_draft",
    "prepare_draft",
    "validate_confirmation",
    "validate_draft",
]
