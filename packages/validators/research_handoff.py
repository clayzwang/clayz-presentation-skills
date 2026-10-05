#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Package 3.2: research meaning, Copy content structure, Art presentation structure.

These checks prove ownership, provenance and coverage. They cannot prove that
an answer is insightful or that prose reads naturally; reviewers must read it.
"""
from __future__ import annotations

from story_handoff import digest, file_bytes, rows, text
import json

EVIDENCE_STATUSES = {
    'source-fact', 'direct-calculation', 'interpretation', 'causal-claim',
    'forecast', 'recommendation', 'target', 'hypothesis', 'missing-data',
}
PRESENTATION_KEYS = {
    'slides', 'slide_id', 'slide_order', 'pagination_owner', 'page_count',
    'title_copy_id', 'storyline_copy_id', 'copy_units', 'narrative_role',
    'page_message_tree', 'deck_message_tree', 'opening', 'closing',
    'slide_title', 'page_title', 'conclusion_page', 'layout', 'coordinates',
    'font_size', 'visual_layers', 'reading_order',
}


def object_list(value, name, errors, *, nonempty=False):
    if not isinstance(value, list) or any(not isinstance(v, dict) for v in value) or (nonempty and not value):
        errors.append(f'{name}: {"nonempty " if nonempty else ""}array of objects required')
        return []
    return value


def unique(items, key, path, errors):
    ids = [x.get(key) for x in items]
    if any(not text(x) for x in ids) or len(set(x for x in ids if isinstance(x, str))) != len(ids):
        errors.append(f'{path}: unique nonempty {key} required')
    return {x for x in ids if isinstance(x, str)}


def valid_refs(refs, known):
    return isinstance(refs, list) and all(isinstance(x, str) and x in known for x in refs)


def forbid_presentation(value, path, errors):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in PRESENTATION_KEYS:
                errors.append(f'{path}.{key}: presentation organization belongs to Copy/Art, not Logic research')
            forbid_presentation(child, f'{path}.{key}', errors)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            forbid_presentation(child, f'{path}[{i}]', errors)


def validate_data(items, sources, errors):
    unique(items, 'data_id', 'research.data', errors)
    for item in items:
        for key in ('metric_name', 'display_value', 'unit', 'period', 'definition_ref'):
            if not text(item.get(key)):
                errors.append(f'research.data.{item.get("data_id")}.{key}: required')
        if 'raw_value' not in item:
            errors.append('research.data.raw_value: required (null when unavailable)')
        status = item.get('evidence_status')
        refs = item.get('source_ids')
        if status not in EVIDENCE_STATUSES or not valid_refs(refs, sources):
            errors.append('research.data: valid evidence status and source references required')
        elif status in {'source-fact', 'direct-calculation'} and not refs:
            errors.append('research.data: facts/calculations require sources')


def validate_research_package(package, require_status):
    from acceptance_contract import validate_acceptance_contract, validate_stage_retrieval_budget
    from resource_inventory import validate_resource_inventory
    from index_evidence import validate_index_evidence
    from validate_logic_package import validate_brief
    errors = []
    rank = {'draft': 0, 'logic-approved': 1, 'copy-approved': 2}
    status = package.get('status')
    if rank.get(status, -1) < rank.get(require_status, 100):
        errors.append('research package: approval status insufficient')
    for key in ('package_id', 'version'):
        if not text(package.get(key)):
            errors.append(f'research package.{key}: required')
    validate_brief(package.get('brief'), errors)
    validate_acceptance_contract(package.get('acceptance_contract'), 'acceptance_contract', errors)
    validate_resource_inventory(package.get('resource_inventory'), 'resource_inventory', errors, require_ready=status != 'draft')
    stages = [] if status == 'draft' else ['logic'] + (['copy'] if status == 'copy-approved' else [])
    validate_index_evidence(package.get('index_evidence'), stages, 'index_evidence', errors)
    validate_stage_retrieval_budget(package.get('index_evidence'), package.get('acceptance_contract'), stages, 'index_evidence', errors)
    if package.get('story') is not None:
        errors.append(f'package {package.get("contract_version")} uses research, not a Logic-authored presentation story')
    if status != 'copy-approved' and (package.get('logic_layer') is not None or package.get('copy_layer') is not None):
        errors.append('Logic research must not preallocate pages or visible copy')
    research = package.get('research')
    if not isinstance(research, dict):
        return errors + ['research: complete research report required']
    forbid_presentation(research, 'research', errors)
    for key in ('research_question', 'scope', 'summary'):
        if not text(research.get(key)):
            errors.append(f'research.{key}: substantive prose required')
    for key in ('glossary', 'metric_dictionary', 'open_items', 'invariants'):
        if not isinstance(research.get(key), list):
            errors.append(f'research.{key}: array required')
    sources = object_list(research.get('sources'), 'research.sources', errors)
    source_ids = unique(sources, 'source_id', 'research.sources', errors)
    selected = (package.get('resource_inventory') or {}).get('selected_resource_ids', [])
    for source in sources:
        if source.get('resource_id') not in selected or not text(source.get('locator')):
            errors.append('research.sources: bind selected resource and locator')
    findings = object_list(research.get('findings'), 'research.findings', errors, nonempty=True)
    unique(findings, 'finding_id', 'research.findings', errors)
    data = object_list(research.get('data'), 'research.data', errors)
    validate_data(data, source_ids, errors)
    data_ids = {x.get('data_id') for x in data if text(x.get('data_id'))}
    for finding in findings:
        fid = finding.get('finding_id')
        for key in ('question', 'text'):
            if not text(finding.get(key)):
                errors.append(f'research.{fid}.{key}: complete research answer required')
        if finding.get('claim_status') not in EVIDENCE_STATUSES:
            errors.append(f'research.{fid}: explicit evidence status required')
        refs = finding.get('source_ids')
        if not valid_refs(refs, source_ids):
            errors.append(f'research.{fid}: valid source references required')
        elif finding.get('claim_status') in {'source-fact', 'direct-calculation'} and not refs:
            errors.append(f'research.{fid}: facts/calculations require sources')
        if not isinstance(finding.get('must_preserve'), bool) or not isinstance(finding.get('qualifiers'), list):
            errors.append(f'research.{fid}: must_preserve and qualifiers required')
        if not valid_refs(finding.get('data_ids'), data_ids):
            errors.append(f'research.{fid}: valid data_ids required')
    approval = (package.get('approvals') or {}).get('logic') or {}
    if status != 'draft' and (approval.get('status') != 'approved' or not text(approval.get('approved_by'))):
        errors.append('approvals.logic: approved research decision required')
    return errors


def validate_research_copy(package):
    errors = []
    try:
        origin = json.loads(file_bytes(package.get('logic_artifact')))
        if origin.get('contract_version') != '3.2' or origin.get('status') != 'logic-approved':
            errors.append('logic_artifact: original package 3.2 approved research required')
        else:
            errors.extend(validate_research_package(origin, 'logic-approved'))
        for key in ('research', 'brief', 'acceptance_contract', 'resource_inventory', 'package_id', 'version', 'configuration_sha256', 'task_selection', 'run_binding'):
            if origin.get(key) != package.get(key):
                errors.append(f'Copy changed immutable Logic {key}')
    except (OSError, ValueError, TypeError) as exc:
        errors.append(f'logic_artifact: {exc}')
    research = package.get('research') or {}
    copy = package.get('copy_layer') or {}
    if copy.get('pagination_owner') != 'copy' or copy.get('research_sha256') != digest(research):
        errors.append('Copy owns pagination and must bind the immutable research SHA-256')
    if not text(copy.get('semantic_preservation_review')):
        errors.append('Copy: concrete meaning and reader-understanding review required')
    chapters = object_list(copy.get('chapters'), 'copy_layer.chapters', errors, nonempty=True)
    chapter_ids = unique(chapters, 'chapter_id', 'copy_layer.chapters', errors)
    if copy.get('chapter_order') != [c.get('chapter_id') for c in chapters]:
        errors.append('Copy chapter_order must match its own content structure')
    for chapter in chapters:
        if not text(chapter.get('title')) or not text(chapter.get('purpose')):
            errors.append('Copy chapters require title and content purpose')
    layer = package.get('logic_layer') or {}
    if layer.get('owner') != 'copy' or (layer.get('lock') or {}).get('slide_order_locked') is not True:
        errors.append('logic_layer compatibility projection: Copy owner and approved page order required')
    pages = object_list(layer.get('slides'), 'Copy page projection', errors, nonempty=True)
    unique(pages, 'slide_id', 'Copy page projection', errors)
    findings = {x.get('finding_id'): x for x in rows(research.get('findings')) if isinstance(x, dict)}
    data = {x.get('data_id'): x for x in rows(research.get('data')) if isinstance(x, dict)}
    for page in pages:
        for key in ('claim', 'narrative_role'):
            if not text(page.get(key)):
                errors.append(f'Copy page.{key}: required')
        if page.get('chapter_id') not in chapter_ids:
            errors.append('Copy page.chapter_id: unknown Copy chapter')
        refs = page.get('source_finding_ids')
        if not valid_refs(refs, findings) or not refs:
            errors.append('Copy page: valid source_finding_ids required')
        for item in object_list(page.get('data'), 'Copy page.data', errors):
            if item != data.get(item.get('data_id')):
                errors.append('Copy page.data: cannot invent or alter research data')
    covered = set()
    for page in object_list(copy.get('slides'), 'copy_layer.slides', errors, nonempty=True):
        units = object_list(page.get('copy_units'), 'copy_units', errors, nonempty=True)
        for unit in units + object_list(page.get('speaker_notes', []), 'speaker_notes', errors):
            refs = unit.get('source_finding_ids')
            if not valid_refs(refs, findings) or not refs:
                errors.append('Copy unit/note: valid source_finding_ids required')
            elif unit in units:
                covered.update(refs)
        requests = object_list(page.get('presentation_requests', []), 'presentation_requests', errors)
        unique(requests, 'request_id', 'presentation_requests', errors)
        unit_ids = {u.get('copy_id') for u in units if text(u.get('copy_id'))}
        for request in requests:
            if request.get('kind') not in {'table', 'chart', 'logo', 'ordinal', 'image', 'diagram', 'other'} or not text(request.get('purpose')):
                errors.append('presentation request: kind and semantic purpose required')
            if not valid_refs(request.get('copy_ids', []), unit_ids) or not valid_refs(request.get('data_ids', []), data):
                errors.append('presentation request: unknown Copy/data reference')
    for fid, finding in findings.items():
        if finding.get('must_preserve') and fid not in covered:
            errors.append(f'Copy omitted required research finding {fid} from visible content')
    cover = (package.get('acceptance_contract') or {}).get('cover_policy') or {}
    for role, key, index in (('cover', 'cover_required', 0), ('closing', 'closing_required', -1)):
        if cover.get(key, cover.get('mode') != 'not-applicable') and (not pages or sum(p.get('narrative_role') == role for p in pages) != 1 or pages[index].get('narrative_role') != role):
            errors.append(f'Copy content structure: one {role} required at the sequence boundary')
    return errors


def validate_art_requests(package, plan):
    """Copy may request media; Art chooses and records the concrete presentation."""
    if package.get('contract_version') != '3.2':
        return []
    errors = []
    for copy_page, design in zip(rows((package.get('copy_layer') or {}).get('slides')), rows(plan.get('slides'))):
        requested = {r.get('request_id'): r for r in rows(copy_page.get('presentation_requests')) if isinstance(r, dict)}
        resolutions = object_list(design.get('presentation_request_resolutions', []), 'Art request resolutions', errors)
        resolved = unique(resolutions, 'request_id', 'Art request resolutions', errors)
        if resolved != set(requested):
            errors.append('Art must resolve every Copy presentation request on its page')
        for response in resolutions:
            if response.get('status') not in {'accepted', 'adapted', 'declined'} or not text(response.get('reason')):
                errors.append('Art request resolution: status and reason required')
    return errors
