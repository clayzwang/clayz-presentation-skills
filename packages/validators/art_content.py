# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Art-owned presentation projection; approved Copy remains an immutable baseline.

Differences are reviewable facts, not automatic failures or approvals. The final
reader assesses their justification after a blind read of the actual renders.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from packages.validators.art_learning import digest, text


def presentation_pages(package, plan=None):
    extension = (plan or {}).get('art_content')
    return extension['slides'] if extension is not None else package.get('copy_layer', {}).get('slides', [])


def differences(package, slides):
    before = package.get('copy_layer', {}).get('slides', [])
    result = []
    def add(category, location, old, new):
        if old != new:
            row = {'category': category, 'location': location, 'before': old, 'after': new}
            result.append({'change_id': 'ART-' + digest(row)[:16], **row})
    add('page-sequence-and-pagination', 'deck', [p['slide_id'] for p in before], [p['slide_id'] for p in slides])
    old_pages = {p['slide_id']: p for p in before}
    new_pages = {p['slide_id']: p for p in slides}
    for sid in dict.fromkeys([*old_pages, *new_pages]):
        add('page-content-and-argument', sid, old_pages.get(sid), new_pages.get(sid))
    return result


def validate_art_content(package, plan):
    value = plan.get('art_content')
    if value is None:
        return []
    errors = []
    if not isinstance(value, dict) or value.get('contract') != 'io.clayz.presentation.art-content/1.0':
        return ['art_content: supported presentation projection required']
    if value.get('copy_package_sha256') != digest(package):
        errors.append('art_content: original approved Copy digest mismatch')
    pages = value.get('slides')
    if not isinstance(pages, list) or not pages or not all(isinstance(p, dict) for p in pages):
        return errors + ['art_content: nonempty presentation pages required']
    page_ids, unit_ids = set(), set()
    for page in pages:
        sid = page.get('slide_id')
        if not text(sid) or sid in page_ids:
            errors.append('art_content: distinct slide IDs required')
        if text(sid):
            page_ids.add(sid)
        units = page.get('copy_units')
        if not isinstance(units, list) or not units or not all(isinstance(u, dict) for u in units):
            errors.append('art_content: visible text units required')
            continue
        for unit in units:
            cid = unit.get('copy_id')
            if (not text(cid) or cid in unit_ids or not text(unit.get('text'))
                    or unit.get('role') not in {'title', 'subtitle', 'heading', 'body', 'annotation'}):
                errors.append('art_content: distinct text IDs, roles and wording required')
            if unit.get('role') == 'heading' and (not isinstance(unit.get('heading_level'), int) or isinstance(unit.get('heading_level'), bool) or unit['heading_level'] < 1):
                errors.append('art_content: heading_level required')
            if text(cid):
                unit_ids.add(cid)
        if package.get('contract_version') == '3.4':
            from packages.validators.page_planning import validate_content_relationships
            errors.extend(validate_content_relationships(page))
    if errors:
        return errors
    expected = differences(package, pages)
    changes = value.get('changes')
    if not isinstance(changes, list) or not all(isinstance(c, dict) for c in changes):
        return ['art_content: auto-computed differences with rationale required']
    keys = {'change_id', 'category', 'location', 'before', 'after'}
    if [{k: c.get(k) for k in keys} for c in changes] != expected:
        errors.append('art_content: changes must exactly cover original-to-actual differences in order')
    for change in changes:
        if not all(text(change.get(k)) for k in ('reason', 'evidence', 'impact')):
            errors.append('art_content: every difference needs reason, evidence (or explicit uncertainty) and impact')
    return errors


def validate_change_audit(package, plan, observations, verdict):
    errors = validate_art_content(package, plan)
    changes = (plan.get('art_content') or {}).get('changes', [])
    if not isinstance(observations, list) or not all(isinstance(o, dict) for o in observations):
        return errors + ['final comparison: Art change observations must be an array']
    if [o.get('change_id') for o in observations] != [c['change_id'] for c in changes]:
        errors.append('final comparison: independently assess every Art difference')
    for observation in observations:
        if observation.get('assessment') not in {'justified', 'unsupported', 'uncertain'} or not all(
                text(observation.get(k)) for k in ('explanation', 'evidence')):
            errors.append('final comparison: grounded Art change assessment required')
        if verdict == 'pass' and observation.get('assessment') != 'justified':
            errors.append('final comparison: unresolved Art change cannot receive pass')
    return errors
