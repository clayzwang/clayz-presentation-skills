# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Copy meaning relationships and immutable, reader-facing Art page planning.

These checks prove coverage, identity and recording order, not design quality
or the order of a model's private reasoning. Layout remains Art's judgment.
"""
from __future__ import annotations

import base64
import hashlib
import json

from story_handoff import digest, file_bytes, rows, text, timestamp

PLANNING_CONTRACT = "io.clayz.presentation.page-planning/1.0"
PLANNING_FIELDS = ("page_message", "content_analysis", "composition", "element_strategy", "addition_decision")
AUDIT_CHECKS = ("page_planning", "content_relationships", "expression_additions", "planned_realization")


def validate_content_relationships(page):
    errors = []
    sid = page.get("slide_id")
    units = {u.get("copy_id"): u for u in rows(page.get("copy_units")) if isinstance(u, dict)}
    headings = {cid for cid, unit in units.items() if unit.get("role") == "heading"}
    bodies = {cid for cid, unit in units.items() if unit.get("role") == "body"}
    relation = page.get("content_relationships")
    if not isinstance(relation, dict):
        return [f"Copy {sid}: content_relationships must explicitly state body ownership and heading relationships"]
    if not text(relation.get("heading_relationships")):
        errors.append(f"Copy {sid}: explain heading relationships, or explicitly describe a page without local headings")
    records = relation.get("body_relations")
    if not isinstance(records, list):
        return errors + [f"Copy {sid}: body_relations array required, including [] when no body exists"]
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            errors.append(f"Copy {sid}: body relation must be an object")
            continue
        cid = record.get("copy_id")
        if not text(cid) or cid not in units or units.get(cid, {}).get("role") not in {"body", "annotation"}:
            errors.append(f"Copy {sid}: body relation must reference a body or annotation on this page")
        elif cid in seen:
            errors.append(f"Copy {sid}.{cid}: duplicate body relation")
        if text(cid):
            seen.add(cid)
        refs = record.get("heading_ids")
        if (not isinstance(refs, list) or not all(text(ref) for ref in refs)
                or len(set(refs)) != len(refs) or any(ref not in headings for ref in refs)):
            errors.append(f"Copy {sid}.{cid}: heading_ids must identify local headings; [] explicitly means no heading ownership")
        if not text(record.get("purpose")):
            errors.append(f"Copy {sid}.{cid}: explain the passage's role, including shared or page-level support")
    if not bodies.issubset(seen):
        errors.append(f"Copy {sid}: every body needs explicit ownership; missing {sorted(bodies - seen)}")
    return errors


def validate_planning_record(package, record, require_recorded=True):
    errors = []
    if not isinstance(record, dict):
        return ["page_planning: actual planning document required"]
    if require_recorded:
        if record.get("contract") != PLANNING_CONTRACT:
            errors.append("page_planning: supported planning contract required")
        for key, expected in (("package_id", package.get("package_id")),
                              ("package_version", package.get("version")),
                              ("copy_package_sha256", digest(package))):
            if record.get(key) != expected:
                errors.append(f"page_planning.{key}: planning must bind the exact Copy handoff")
        try:
            timestamp(record.get("recorded_at"))
        except (ValueError, TypeError):
            errors.append("page_planning.recorded_at: actual timezone timestamp required")
    from packages.validators.art_content import presentation_pages, validate_art_content
    from packages.validators.art_learning import validate_cognition
    errors.extend(validate_art_content(package, record))
    if "art_cognition" in record:
        errors.extend(validate_cognition(record["art_cognition"]))
    if errors:
        return errors
    pages = presentation_pages(package, record)
    designs = record.get("slides")
    if not isinstance(designs, list) or not all(isinstance(p, dict) for p in designs):
        return errors + ["page_planning.slides: page planning objects required"]
    if [p.get("slide_id") for p in designs] != [p.get("slide_id") for p in pages]:
        errors.append("page_planning: cover every recorded presentation page in its actual order")
    for page, design in zip(pages, designs):
        sid = page.get("slide_id")
        for key in PLANNING_FIELDS:
            if not text(design.get(key)):
                errors.append(f"page_planning {sid}.{key}: concrete prose required")
        additions = design.get("expression_additions")
        if not isinstance(additions, list):
            errors.append(f"page_planning {sid}: expression_additions array required; [] is valid")
            continue
        ids = {u.get("copy_id") for u in rows(page.get("copy_units")) if isinstance(u, dict)}
        for item in additions:
            if not isinstance(item, dict):
                errors.append(f"page_planning {sid}: expression additions must be objects")
                continue
            if not text(item.get("text")) or not text(item.get("purpose")):
                errors.append(f"page_planning {sid}: added expression needs text and purpose")
            refs = item.get("source_copy_ids")
            if (not isinstance(refs, list) or not refs or not all(text(ref) for ref in refs)
                    or len(set(refs)) != len(refs) or any(ref not in ids for ref in refs)):
                errors.append(f"page_planning {sid}: added expression must trace to this page's approved Copy IDs")
    return errors


def planning_reference(path):
    payload = path.read_bytes()
    return {"path": str(path.resolve()), "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload),
            "content": json.loads(payload), "base64": base64.b64encode(payload).decode()}


def validate_planning_snapshot(reference):
    """Validate exact bytes portably, without reopening an originating path."""
    try:
        if not isinstance(reference, dict):
            raise ValueError("planning reference required")
        payload = base64.b64decode(reference.get("base64", ""), validate=True)
        if (not payload or len(payload) != reference.get("bytes")
                or hashlib.sha256(payload).hexdigest() != reference.get("sha256")
                or json.loads(payload) != reference.get("content")):
            raise ValueError("planning bytes, snapshot or SHA-256 mismatch")
        return []
    except (ValueError, TypeError) as exc:
        return [f"page_planning: {exc}"]


def validate_art_planning(package, plan):
    reference = plan.get("page_planning")
    errors = validate_planning_snapshot(reference)
    if errors:
        return errors
    try:
        if file_bytes(reference) != base64.b64decode(reference["base64"]):
            errors.append("page_planning: original planning file differs from its snapshot")
    except (OSError, ValueError, TypeError) as exc:
        errors.append(f"page_planning original file: {exc}")
    errors.extend(validate_planning_record(package, reference["content"]))
    for key in ("art_content", "art_cognition"):
        if plan.get(key) != reference["content"].get(key):
            errors.append(f"{key}: plan must preserve the actual planning snapshot")
    try:
        if timestamp(reference["content"].get("recorded_at")) >= timestamp((plan.get("visual_baseline") or {}).get("locked_at")):
            errors.append("page_planning: planning recorded after the design lock; do not retrofit evidence")
    except (ValueError, TypeError):
        errors.append("page_planning: planning and design lock require timezone timestamps")
    return errors


def planning_markdown(record):
    lines = ["# Art page planning", "", f"Recorded: {record.get('recorded_at', 'not-recorded')}", ""]
    for page in rows(record.get("slides")):
        lines += [f"## {page['slide_id']}", ""]
        for key in PLANNING_FIELDS:
            lines += [f"### {key}", "", page[key], ""]
        for item in rows(page.get("expression_additions")):
            lines += [f"- {item['text']}: {item['purpose']} [Copy: {', '.join(item['source_copy_ids'])}]", ""]
    for key in ("art_cognition", "art_content"):
        if key in record:
            lines += [f"## {key}", "", "```json", json.dumps(record[key], ensure_ascii=False, indent=2), "```", ""]
    return "\n".join(lines)
