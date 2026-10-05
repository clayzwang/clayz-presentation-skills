# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Package 3.3: editorial text and Art-owned presentation, without layout presets.

Checks establish identity, content coverage and native-object bindings. They do
not prescribe an aesthetic, visual reading order or one object per paragraph.
"""
from __future__ import annotations

import json
from collections import Counter

from story_handoff import digest, file_bytes, rows, text
from research_handoff import object_list, unique, valid_refs

COPY_ROLES = {"title", "subtitle", "heading", "body", "annotation"}
UNIT_KEYS = {"copy_id", "text", "role", "heading_level"}
RETIRED_COPY_KEYS = {
    "kind", "columns", "table", "ladder", "rows", "flow", "layout", "layout_index",
    "parent_copy_id", "sibling_group_id", "logic_level", "order", "text_mode",
    "render_separately", "merge_with_children", "intentional_line_breaks",
    "presentation_requests", "node_copy_map", "title_copy_id", "storyline_copy_id",
    "footnote_copy_ids", "grammar_signature", "cross_slide_copy_contract", "lock",
    "title_mode", "storyline_function", "audience_transition_copy_strategy", "series_copy_review",
}
RETIRED_QA_CHECKS = {
    "atomic_copy_separation", "parent_child_hierarchy", "peer_parallelism",
    "storyline_single_line", "list_alignment",
}


def content_pages(package):
    """Use Copy's pages directly; 3.3 needs no fabricated Logic page projection."""
    if package.get("contract_version") == "3.3":
        return rows((package.get("copy_layer") or {}).get("slides"))
    return rows((package.get("logic_layer") or {}).get("slides"))


def retired_fields(value, path, errors):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in RETIRED_COPY_KEYS:
                errors.append(f"{path}.{key}: retired Copy presentation field; Art owns rendering")
            retired_fields(child, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            retired_fields(child, f"{path}[{i}]", errors)


def validate_clean_copy(package):
    from research_handoff import validate_research_package
    errors = []
    try:
        origin = json.loads(file_bytes(package.get("logic_artifact")))
        if origin.get("contract_version") != "3.3" or origin.get("status") != "logic-approved":
            errors.append("logic_artifact: original package 3.3 approved research required")
        else:
            errors.extend(validate_research_package(origin, "logic-approved"))
        for key in ("research", "brief", "acceptance_contract", "resource_inventory", "package_id", "version",
                    "configuration_sha256", "task_selection", "run_binding"):
            if origin.get(key) != package.get(key):
                errors.append(f"Copy changed immutable Logic {key}")
    except (OSError, ValueError, TypeError) as exc:
        errors.append(f"logic_artifact: {exc}")
    if package.get("logic_layer") is not None:
        errors.append("package 3.3: Copy pages belong in copy_layer, without a Logic page projection")
    research = package.get("research") or {}
    layer = package.get("copy_layer")
    if not isinstance(layer, dict):
        return errors + ["copy_layer: content document required"]
    retired_fields(layer, "copy_layer", errors)
    if layer.get("pagination_owner") != "copy" or layer.get("research_sha256") != digest(research):
        errors.append("Copy owns pagination and binds the immutable research SHA-256")
    if layer.get("logic_version") != package.get("version"):
        errors.append("copy_layer.logic_version: must bind root version")
    if not text(layer.get("semantic_preservation_review")):
        errors.append("Copy: concrete meaning and reader-understanding review required")
    approval = (package.get("approvals") or {}).get("copy") or {}
    if approval.get("status") != "approved" or not text(approval.get("approved_by")):
        errors.append("approvals.copy: approved stage decision required")
    pages = object_list(layer.get("slides"), "copy_layer.slides", errors, nonempty=True)
    unique(pages, "slide_id", "copy_layer.slides", errors)
    ids = set()
    for page in pages:
        units = object_list(page.get("copy_units"), "copy_units", errors, nonempty=True)
        for unit in units:
            cid = unit.get("copy_id")
            if not text(cid) or cid in ids:
                errors.append("copy_id: unique nonempty ID required across deck")
            if text(cid):
                ids.add(cid)
            if set(unit) - UNIT_KEYS:
                errors.append(f"copy unit {cid}: content fields are copy_id, text, role and optional heading_level")
            if not text(unit.get("text")) or not isinstance(unit.get("role"), str) or unit.get("role") not in COPY_ROLES:
                errors.append(f"copy unit {cid}: text and title/subtitle/heading/body/annotation role required")
            level = unit.get("heading_level")
            if unit.get("role") == "heading":
                if isinstance(level, bool) or not isinstance(level, int) or level < 1:
                    errors.append(f"copy unit {cid}: heading requires a positive heading_level")
            elif "heading_level" in unit:
                errors.append(f"copy unit {cid}: heading_level belongs only to a heading")
        for note in object_list(page.get("speaker_notes", []), "speaker_notes", errors):
            if not text(note.get("text")):
                errors.append("speaker_notes: supplied notes must contain text")
        if not valid_refs(page.get("data_ids", []), {d.get("data_id") for d in rows(research.get("data"))}):
            errors.append("Copy page.data_ids: unknown research data")
    # Provenance travels separately from the text document, never as a parent,
    # sibling, shape, order or style instruction to Art.
    provenance = package.get("copy_provenance")
    findings = {f.get("finding_id"): f for f in rows(research.get("findings"))}
    if not isinstance(provenance, dict) or set(provenance) != ids:
        errors.append("copy_provenance: source finding references must cover the visible copy IDs")
        provenance = provenance if isinstance(provenance, dict) else {}
    covered = set()
    for cid, refs in provenance.items():
        if not valid_refs(refs, findings) or not refs:
            errors.append(f"copy_provenance.{cid}: valid source_finding_ids required")
        else:
            covered.update(refs)
    for fid, finding in findings.items():
        if finding.get("must_preserve") and fid not in covered:
            errors.append(f"Copy omitted required research finding {fid} from visible content")
    cover = (package.get("acceptance_contract") or {}).get("cover_policy") or {}
    for role, key, index in (("cover", "cover_required", 0), ("closing", "closing_required", -1)):
        if cover.get(key, cover.get("mode") != "not-applicable") and (not pages or
                sum(p.get("narrative_role") == role for p in pages) != 1 or pages[index].get("narrative_role") != role):
            errors.append(f"Copy content structure: one {role} required at the sequence boundary")
    return errors


def validate_reference_research(value, errors):
    if not isinstance(value, dict):
        errors.append("reference_research: actual reference approach required")
        return
    available = value.get("learning_package_available")
    strategy = value.get("source_strategy")
    if not isinstance(available, bool) or strategy not in {"learning-first", "web-first", "autonomous"}:
        errors.append("reference_research: learning availability and learning-first/web-first/autonomous strategy required")
    if available is True and strategy == "web-first":
        errors.append("reference_research: available learning package is the first reference source")
    if available is False and strategy == "learning-first":
        errors.append("reference_research: cannot claim an unavailable learning package")
    if not text(value.get("notes")):
        errors.append("reference_research.notes: describe actual use, no-match or access limitation")
    refs = object_list(value.get("references", []), "reference_research.references", errors)
    for ref in refs:
        if ref.get("source") not in {"learning-package", "web", "user-reference"} or not text(ref.get("locator")) or not text(ref.get("use")):
            errors.append("reference_research: source, real locator and concrete use required for each reference")
    # Empty/no-match records are valid. No source count or preset is a design gate.


def validate_native_location(mapping, path, errors):
    location = mapping.get("native_location")
    kind = mapping.get("target_type")
    if kind not in {"shape", "table-cell", "chart-label"} or not isinstance(location, dict):
        errors.append(f"{path}: editable shape/table-cell/chart-label location required")
        return
    if not text(location.get("shape_name")):
        errors.append(f"{path}.native_location.shape_name: actual object name required")
    if kind == "table-cell":
        for key in ("row", "column"):
            if isinstance(location.get(key), bool) or not isinstance(location.get(key), int) or location.get(key, -1) < 0:
                errors.append(f"{path}.native_location.{key}: zero-based index required")
    if kind == "chart-label" and location.get("label_kind") not in {"title", "series-name", "category", "value", "data-label"}:
        errors.append(f"{path}.native_location.label_kind: chart label selector required")
    if kind == "chart-label":
        for key in ("series_index", "point_index"):
            if key in location and (isinstance(location[key], bool) or not isinstance(location[key], int) or location[key] < 0):
                errors.append(f"{path}.native_location.{key}: zero-based index required")
    span = location.get("text_range")
    if span is not None and (not isinstance(span, list) or len(span) != 2 or
                            any(isinstance(n, bool) or not isinstance(n, int) for n in span) or
                            span[0] < 0 or span[1] <= span[0]):
        errors.append(f"{path}.native_location.text_range: [start,end) character indexes required")


def validate_free_art(package, plan, policy=None):
    from validate_ppt_package import validate_package
    from story_handoff import validate_visual_baseline
    from resource_inventory import resource_inventory_signature
    from index_evidence import index_lock_signature, validate_index_evidence
    from acceptance_contract import validate_stage_retrieval_budget
    errors = validate_package(package, "copy-approved")
    if errors:
        return errors
    if not isinstance(plan, dict):
        return errors + ["Art plan: object required"]
    if plan.get("contract_version") not in {"2.1", "2.2"} or plan.get("package_contract_version") != "3.3":
        errors.append("package 3.3 requires Art plan 2.2 (2.1 retained for replay)")
    if plan.get("status") != "art-direction-approved":
        errors.append("plan.status: art-direction-approved required")
    if plan.get("package_id") != package.get("package_id") or plan.get("package_version") != package.get("version"):
        errors.append("Art package identity/version must match Copy")
    if plan.get("acceptance_contract") != package.get("acceptance_contract"):
        errors.append("Art must inherit the task acceptance contract")
    if plan.get("resource_inventory_lock") != resource_inventory_signature(package.get("resource_inventory")):
        errors.append("Art must preserve the resource inventory signature")
    if plan.get("communication_contract") != (package.get("brief") or {}).get("preflight"):
        errors.append("Art must preserve brief.preflight")
    # Existing retrieval evidence still proves consulted sources. Art's original
    # design does not require a built-in layout, a match or a fake Index receipt.
    evidence = plan.get("index_evidence")
    validate_index_evidence(evidence, ["logic", "copy"], "plan.index_evidence", errors)
    validate_stage_retrieval_budget(evidence, plan.get("acceptance_contract"), ["logic", "copy", "art-direction"], "plan.index_evidence", errors)
    if index_lock_signature(evidence) != index_lock_signature(package.get("index_evidence")):
        errors.append("Art must preserve the task Provider lock")
    validate_reference_research(plan.get("reference_research"), errors)
    approval = (plan.get("art_direction") or {}).get("approval") or {}
    if approval.get("status") != "approved" or not text(approval.get("approved_by")):
        errors.append("art_direction.approval: approved stage decision required")
    pages = rows((package.get("copy_layer") or {}).get("slides"))
    designs = object_list(plan.get("slides"), "plan.slides", errors, nonempty=True)
    if [p.get("slide_id") for p in designs] != [p.get("slide_id") for p in pages]:
        errors.append("Art pages must preserve Copy's page sequence")
    baseline_pages = {p.get("slide_id"): p for p in rows((plan.get("visual_baseline") or {}).get("slides")) if isinstance(p, dict)}
    for page, design in zip(pages, designs):
        sid = page.get("slide_id")
        ids = [u.get("copy_id") for u in rows(page.get("copy_units"))]
        reading = design.get("reading_sequence")
        if not isinstance(reading, list) or not all(text(cid) for cid in reading) or Counter(reading) != Counter(ids):
            errors.append(f"Art {sid}: reading_sequence must cover visible text once, in Art's chosen order")
        maps = object_list(design.get("copy_unit_map"), f"Art {sid}.copy_unit_map", errors)
        if not all(text(m.get("copy_id")) for m in maps) or Counter(m.get("copy_id") for m in maps) != Counter(ids):
            errors.append(f"Art {sid}: native mappings must cover each copy_id once")
        element_by_id = {e.get("element_id"): e for e in rows(baseline_pages.get(sid, {}).get("elements")) if isinstance(e, dict)}
        targets, ranges = {}, {}
        for mapping in maps:
            cid, target = mapping.get("copy_id"), mapping.get("render_target_id")
            if not text(target):
                errors.append(f"Art {sid}: render_target_id required")
            validate_native_location(mapping, f"Art {sid}.{cid}", errors)
            location = mapping.get("native_location")
            if not isinstance(location, dict) or not text(target):
                continue
            identity = digest({k: v for k, v in location.items() if k != "text_range"})
            physical = (mapping.get("target_type"), location.get("shape_name"))
            if target in targets and targets[target] != physical:
                errors.append(f"Art {sid}: a shared target must identify the same native object")
            targets[target] = physical
            element = element_by_id.get(target)
            if element is None or cid not in rows(element.get("copy_ids")):
                errors.append(f"Art {sid}: native target must bind its baseline element and Copy IDs")
            span = location.get("text_range")
            if isinstance(span, list) and len(span) == 2 and all(isinstance(n, int) and not isinstance(n, bool) for n in span):
                ranges.setdefault((mapping.get("target_type"), identity), []).append(tuple(span))
        locations = Counter((m.get("target_type"), digest({k: v for k, v in m["native_location"].items() if k != "text_range"}))
                            for m in maps if isinstance(m.get("native_location"), dict) and isinstance(m.get("target_type"), str))
        for key, count in locations.items():
            spans = sorted(ranges.get(key, []))
            if count > 1 and (len(spans) != count or any(a[1] > b[0] for a, b in zip(spans, spans[1:]))):
                errors.append(f"Art {sid}: shared native text requires disjoint text_range bindings")
        medium = design.get("medium_execution_contract")
        if not isinstance(medium, dict) or not text(medium.get("structure_type")):
            errors.append(f"Art {sid}: describe the chosen presentation structure")
        elif not isinstance(medium.get("minimum_object_counts", {}), dict) or any(
                isinstance(n, bool) or not isinstance(n, int) or n < 0 for n in medium.get("minimum_object_counts", {}).values()):
            errors.append(f"Art {sid}: object minima must be nonnegative counts")
        if "atomicity_review" in design:
            errors.append(f"Art {sid}: retired atomicity_review is not a new-run design requirement")
    errors.extend(validate_visual_baseline(package, plan))
    if plan.get("contract_version") == "2.2" and not errors:
        errors.extend(validate_editable_object_contract(plan))
    return errors


def validate_editable_object_contract(plan):
    """Art declares native objects; Copy units never prescribe separation."""
    errors = []
    baseline = {page.get("slide_id"): page for page in rows((plan.get("visual_baseline") or {}).get("slides"))}
    for design in rows(plan.get("slides")):
        sid = design.get("slide_id")
        elements = rows(baseline.get(sid, {}).get("elements"))
        names = set()
        by_id = {}
        for element in elements:
            if not isinstance(element, dict):
                continue
            eid, name = element.get("element_id"), element.get("native_name")
            by_id[eid] = element
            if not text(name) or name in names:
                errors.append(f"Art {sid}.{eid}: a unique native_name identifies each editable object")
            elif text(name):
                names.add(name)
            if element.get("render_separately") is not True:
                errors.append(f"Art {sid}.{eid}: render_separately must be true for the Art-declared native object")
            path = element.get("native_group_path", [])
            if not isinstance(path, list) or not all(text(value) for value in path) or len(set(path)) != len(path):
                errors.append(f"Art {sid}.{eid}: native_group_path must list distinct native group names, outermost first")
            elif name in path:
                errors.append(f"Art {sid}.{eid}: an editable child object cannot be its own native group")
        for mapping in rows(design.get("copy_unit_map")):
            element = by_id.get(mapping.get("render_target_id"), {})
            if (mapping.get("native_location") or {}).get("shape_name") != element.get("native_name"):
                errors.append(f"Art {sid}.{mapping.get('copy_id')}: native mapping must use its Art object's native_name")
    return errors
