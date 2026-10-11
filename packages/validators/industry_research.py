"""Inspect industry research references without pretending to judge insight.

The optional ledger is a research aid, not a slide template or quality score.
Unknowns and inferred sector links remain explicit. A sector-level relation
does not establish a named customer contract.
"""
from __future__ import annotations


def reader_brief(profile):
    """Carry the actual audience and task through; never assume finance fluency."""
    keys = ('audience', 'purpose', 'task')
    if set(profile) != set(keys) or any(not isinstance(profile[k], str) or not profile[k].strip() for k in keys):
        raise ValueError('Reader profile requires neutral audience, purpose and task')
    return {key: profile[key] for key in keys}


def inspect(ledger, source_ids):
    errors = []
    if ledger.get('contract') != 'io.clayz.presentation.industry-research/1.0':
        errors.append('unsupported industry research contract')
    def collection(key, id_key):
        rows = ledger.get(key, [])
        if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
            errors.append(key + ': array of objects required')
            return [], set()
        ids = [r.get(id_key) for r in rows]
        if any(not isinstance(i, str) or not i.strip() for i in ids) or len(set(ids)) != len(ids):
            errors.append(key + ': unique identifiers required')
        return rows, {i for i in ids if isinstance(i, str)}
    stages, stage_ids = collection('stages', 'stage_id')
    firms, firm_ids = collection('companies', 'company_id')
    links, _ = collection('links', 'link_id')
    known_sources = set(source_ids)
    for group, rows in [('stages', stages), ('companies', firms), ('links', links)]:
        for row in rows:
            refs = row.get('source_ids', [])
            if not isinstance(refs, list) or any(ref not in known_sources for ref in refs):
                errors.append(group + ': unknown source reference')
            if row.get('claim_status') not in {'source-fact', 'interpretation', 'missing-data'}:
                errors.append(group + ': explicit evidence status required')
            if row.get('claim_status') == 'source-fact' and not refs:
                errors.append(group + ': source facts require source references')
    for firm in firms:
        if not isinstance(firm.get('stage_ids'), list) or any(i not in stage_ids for i in firm['stage_ids']):
            errors.append('companies: unknown stage reference')
        if not firm.get('role') or not firm.get('selection_basis'):
            errors.append('companies: explain role and selection basis')
    for link in links:
        if link.get('from_stage') not in stage_ids or link.get('to_stage') not in stage_ids:
            errors.append('links: unknown endpoint')
        if link.get('kind') not in {'goods', 'service', 'information', 'payment', 'rights', 'mixed'}:
            errors.append('links: distinguish the relationship type')
        if link.get('scope') not in {'sector-pattern', 'verified-company-relationship'}:
            errors.append('links: distinguish sector pattern from an observed contract')
        if link.get('scope') == 'verified-company-relationship':
            if not link.get('company_ids') or any(i not in firm_ids for i in link['company_ids']):
                errors.append('links: verified company relationship needs known companies')
        if not link.get('what_moves'):
            errors.append('links: explain what actually moves between stages')
    isolated = sorted(stage_ids - {i for link in links for i in (link.get('from_stage'), link.get('to_stage'))})
    return {'ok': not errors, 'errors': errors,
            'counts': {'stages': len(stages), 'companies': len(firms), 'links': len(links)},
            'isolated_stages': isolated,
            'limitation': 'Reference consistency only; substantive completeness, company importance, explanation and readability require actual research and reader judgment.'}
