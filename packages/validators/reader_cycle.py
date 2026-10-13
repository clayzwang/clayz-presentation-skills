"""Consolidated, single-repair reading cycles. Quality findings never become passes."""
from __future__ import annotations
import json
from copy import deepcopy
from functools import wraps
from datetime import datetime, timezone
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from packages.validators.reader_review import read, ref, load_ref, validate_review, _time

CONTRACT = 'io.clayz.presentation.reader-cycle/1.0'
POLICY = 'consolidated-once'


def bounded(config):
    return config.get('workflow', {}).get('reader_review', {}).get('repair_policy') == POLICY


def now():
    return datetime.now(timezone.utc).isoformat()


def same(a, b):
    return all(k in a and k in b and a[k] == b[k] for k in ('sha256', 'bytes'))


def write(path, value, *, new=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if new:
        with path.open('x', encoding='utf-8') as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.write('\n')
    else:
        tmp = path.with_name(path.name + '.tmp')
        with tmp.open('x', encoding='utf-8') as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.write('\n')
        tmp.replace(path)


def artifacts(value, phase):
    required = {'package'} if phase == 'copy' else {'package', 'plan', 'pptx', 'renders'}
    if set(value) != required:
        raise ValueError('cycle artifact roles differ from ' + str(sorted(required)))
    for item in value.values():
        load_ref(item, json_value=False)
    package = load_ref(value['package'])
    if package.get('status') != 'copy-approved':
        raise ValueError('cycle requires a delivered Copy package')
    if phase == 'final':
        manifest = load_ref(value['renders'])
        if manifest.get('pptx_sha256') != value['pptx']['sha256']:
            raise ValueError('cycle renders do not bind current PPTX')
        from .reader_review import projection
        ids = [p['slide_id'] for p in projection(package, 'final', load_ref(value['plan']))]
        if [p.get('slide_id') for p in manifest.get('slides', [])] != ids:
            raise ValueError('cycle renders do not cover all current pages in order')
        for page in manifest['slides']:
            load_ref({k: page[k] for k in ('path', 'sha256', 'bytes')}, json_value=False)
    return package


def inspect(value):
    if value.get('contract') != CONTRACT or value.get('phase') not in {'copy', 'final'}:
        raise ValueError('invalid reader cycle')
    config = load_ref(value['config'])
    if not bounded(config):
        raise ValueError('reader cycle requires selected consolidated-once config')
    package = artifacts(value['baseline'], value['phase'])
    if value['binding'] != {k: package['run_binding'][k] for k in ('run_id', 'task_request_sha256')}:
        raise ValueError('cycle run/task binding changed')
    expected = {'title', 'content'} if value['phase'] == 'copy' else {'final'}
    if set(value['reviews']) != expected:
        raise ValueError('collect all required readers before any repair')
    reviews, issues, contexts = {}, [], set()
    for phase, item in value['reviews'].items():
        review = validate_review(load_ref(item), current_package=package,
                                pptx_sha256=value['baseline'].get('pptx', {}).get('sha256'))
        first, packet, result = review['first_read'], review['packet'], review['review']
        if result['phase'] != phase or any(result[k] != value['binding'][k] for k in value['binding']):
            raise ValueError('reader phase/run/task differs from cycle')
        if not same(packet['package'], value['baseline']['package']):
            raise ValueError('readers must inspect the same delivered Copy bytes')
        if first['status'] != 'observed' or review['assessment'] in {'not-run', 'insufficient-input'} or review['independence'] == 'same-context-limited':
            raise ValueError('missing or non-independent reading is not a completed cycle')
        context = first['context']['context_id']
        if context in contexts:
            raise ValueError('title and content require different reader contexts')
        contexts.add(context)
        if _time(result['reconciled_at']) > _time(value['collected_at']):
            raise ValueError('collect only after both readers finish reconciliation')
        if phase == 'final' and not same(packet.get('art_plan') or {}, value['baseline']['plan']):
            raise ValueError('final cycle must bind the actual reviewed Art plan')
        dispositions = {x['finding_id']: x for x in result['dispositions']}
        for finding in first['response']['findings']:
            issues.append({'issue_id': phase + ':' + finding['finding_id'], 'phase': phase,
                           'finding': finding, 'disposition': dispositions[finding['finding_id']]})
        if result.get('comparison', {}).get('verdict') != 'pass':
            issues.append({'issue_id': phase + ':comparison', 'phase': phase,
                           'comparison': result.get('comparison')})
        reviews[phase] = review
    repair = value.get('repair')
    if repair is not None:
        owners = {'copy'} if value['phase'] == 'copy' else {'art-direction', 'output'}
        if repair.get('owner') not in owners or repair.get('number') != 1 or not repair.get('rationale', '').strip():
            raise ValueError('cycle permits exactly one repair by its designated owner')
        if not issues or _time(repair['started_at']) < _time(value['collected_at']):
            raise ValueError('repair must follow consolidated reader findings')
    return package, reviews, issues


def validate_cycle(value, *, current_package=None, current_plan=None, current_pptx=None, config=None):
    package, reviews, issues = inspect(value)
    if value.get('status') != 'closed':
        raise ValueError('reader cycle is not closed')
    if config is not None and config != load_ref(value['config']):
        raise ValueError('cycle selected config differs from current config')
    closure = value['closure']
    current = artifacts(closure['artifacts'], value['phase'])
    if current['run_binding'] != package['run_binding']:
        raise ValueError('repair changed task/run identity')
    if value['phase'] == 'final' and not same(closure['artifacts']['package'], value['baseline']['package']):
        raise ValueError('final repair belongs to Art/Output; do not reopen Copy/Logic')
    if current_package is not None and current != current_package:
        raise ValueError('cycle is stale for current Copy')
    if current_plan is not None and load_ref(closure['artifacts']['plan']) != current_plan:
        raise ValueError('cycle is stale for current Art plan')
    if current_pptx is not None and not same(closure['artifacts']['pptx'], current_pptx):
        raise ValueError('cycle is stale for current PPTX')
    if bool(issues) != bool(value.get('repair')):
        raise ValueError('findings require one consolidated repair attempt before closure')
    if not issues and closure['artifacts'] != value['baseline']:
        raise ValueError('a no-repair cycle cannot change delivered artifacts')
    after = value['repair']['started_at'] if value.get('repair') else value['collected_at']
    if _time(closure['closed_at']) < _time(after):
        raise ValueError('closure precedes reading or repair')
    rows = closure['resolutions']
    expected = {x['issue_id'] for x in issues}
    if len(rows) != len(expected) or {x.get('issue_id') for x in rows} != expected:
        raise ValueError('every consolidated finding/comparison needs exactly one disposition')
    for row in rows:
        if row.get('status') not in {'resolved', 'remaining'} or not row.get('explanation', '').strip() or not row.get('evidence'):
            raise ValueError('repair disposition needs status, explanation and actual evidence')
        for item in row['evidence']:
            load_ref(item, json_value=False)
    if value.get('repair'):
        check = load_ref(closure['verification'])
        if (check.get('owner') != value['repair']['owner'] or check.get('artifacts') != closure['artifacts']
                or not isinstance(check.get('checks'), list) or not check['checks']):
            raise ValueError('owner verification must bind current artifacts and actual checks')
        for row in check['checks']:
            if row.get('status') not in {'pass', 'fail', 'deferred'} or not row.get('observation', '').strip():
                raise ValueError('verification checks need actual status and observation')
    confirmations, new_findings = validate_confirmations(value, reviews, issues)
    return {'cycle': value, 'reviews': reviews, 'issues': issues,
            'confirmations': confirmations, 'new_findings': new_findings,
            'remaining': [x for x in rows if x['status'] == 'remaining'],
            'repair_count': int(value.get('repair') is not None)}


def collect(*, phase, config, package, reviews, output, plan=None, pptx=None, renders=None):
    baseline = {'package': ref(package)}
    if phase == 'final':
        baseline.update(plan=ref(plan), pptx=ref(pptx), renders=ref(renders))
    p = read(package)
    value = {'contract': CONTRACT, 'phase': phase, 'status': 'collected', 'config': ref(config),
             'binding': {k: p['run_binding'][k] for k in ('run_id', 'task_request_sha256')},
             'baseline': baseline, 'reviews': {read(x)['phase']: ref(x) for x in reviews},
             'collected_at': now(), 'repair': None}
    if len(value['reviews']) != len(reviews):
        raise ValueError('duplicate reader phase')
    inspect(value)
    write(output, value, new=True)
    return value


def exclusive_update(function):
    @wraps(function)
    def guarded(path, *args, **kwargs):
        lock = Path(str(path) + '.lock')
        # Atomic exclusive create: two dispatchers cannot reserve the same repair.
        with lock.open('x', encoding='utf-8') as stream:
            stream.write(function.__name__)
        try:
            return function(path, *args, **kwargs)
        finally:
            lock.unlink()
    return guarded

@exclusive_update
def start_repair(path, owner, rationale):
    value = read(path)
    _, _, issues = inspect(value)
    if value['status'] != 'collected' or value.get('repair') is not None:
        raise ValueError('one repair already reserved or cycle closed; no second dispatch')
    if not issues:
        raise ValueError('no reader finding requires repair')
    value.update(status='repairing', repair={'number': 1, 'owner': owner,
                                           'rationale': rationale, 'started_at': now()})
    inspect(value)
    write(path, value)
    return value


@exclusive_update
def close(path, closure):
    value = read(path)
    if value['status'] not in {'collected', 'repairing'}:
        raise ValueError('closed cycle is immutable; no additional repair')
    value.update(status='closed', closure={**deepcopy(closure), 'closed_at': now()})
    validate_cycle(value)
    write(path, value)
    return value


def validate_confirmations(value, reviews, issues):
    """Reinspection is by the original readers, not a second repair authorization."""
    closure = value['closure']
    confirmations = closure.get('confirmations', {})
    if not value.get('repair'):
        if confirmations:
            raise ValueError('no repair: retain original reading, no fabricated confirmation')
        return {}, []
    if set(confirmations) != set(reviews):
        raise ValueError('every original reader must reread after repair')
    result, new_findings = {}, []
    resolutions = {r['issue_id']: r for r in closure['resolutions']}
    for phase, item in confirmations.items():
        c = load_ref(item)
        original = reviews[phase]['first_read']['context']['context_id']
        if (c.get('contract') != 'io.clayz.presentation.reader-confirmation/1.0'
                or c.get('phase') != phase or c.get('context_id') != original
                or c.get('binding') != value['binding']
                or c.get('artifacts') != closure['artifacts']):
            raise ValueError('confirmation must bind original reader and repaired artifacts')
        if not (_time(value['repair']['started_at']) <= _time(c['reviewed_at']) <= _time(closure['closed_at'])):
            raise ValueError('confirmation must follow repair and precede closure')
        receipt = load_ref(c['host_receipt'])
        if (receipt.get('context_id') != original or not receipt.get('host_tool')
                or receipt.get('input_artifacts') != closure['artifacts']):
            raise ValueError('confirmation requires actual same-reader follow-up receipt')
        load_ref(receipt['raw_receipt'], json_value=False)
        expected = {x['issue_id'] for x in issues if x['phase'] == phase}
        rows = c.get('resolutions', [])
        if len(rows) != len(expected) or {x.get('issue_id') for x in rows} != expected:
            raise ValueError('reader must confirm every original issue from their reading')
        for row in rows:
            if row != resolutions[row['issue_id']]:
                raise ValueError('closure may not override reader repair confirmation')
        new = c.get('new_findings')
        if not isinstance(new, list) or len({x.get('finding_id') for x in new}) != len(new):
            raise ValueError('confirmation must explicitly record unique new findings or []')
        for finding in new:
            if not all(isinstance(finding.get(k), str) and finding[k].strip()
                       for k in ('finding_id', 'statement', 'reader_impact', 'visible_evidence')):
                raise ValueError('new finding requires concrete visible reading evidence')
            if not isinstance(finding.get('slide_ids'), list) or not finding['slide_ids']:
                raise ValueError('new finding requires affected pages')
            new_findings.append({'phase': phase, **finding})
        result[phase] = c
    return result, new_findings


def source_ref(row):
    return {k: row[k] for k in ('path', 'sha256', 'bytes')}


def audit_cycles(auditor, config):
    sources = {r['kind']: r for r in auditor.get('source_records', [])}
    package = load_ref(source_ref(sources['package']))
    plan = load_ref(source_ref(sources['plan']))
    result, cycles, contexts = {}, {}, set()
    for phase in ('copy', 'final'):
        value = load_ref(source_ref(sources['reader-cycle-' + phase]))
        check = validate_cycle(value, current_package=package, config=config,
                               current_plan=plan if phase == 'final' else None,
                               current_pptx=auditor['final_pptx'] if phase == 'final' else None)
        if value['phase'] != phase or any(value['binding'][k] != auditor[k] for k in value['binding']):
            raise ValueError('cycle phase/run/task differs from audit')
        if _time(value['closure']['closed_at']) > _time(auditor['audited_at']):
            raise ValueError('audit must follow all reader confirmations')
        for reader_phase, review in check['reviews'].items():
            if source_ref(sources['reader-review-' + reader_phase]) != value['reviews'][reader_phase]:
                raise ValueError('audit reader source differs from cycle original reading')
            context = review['first_read']['context']['context_id']
            if context in contexts:
                raise ValueError('initial readers require distinct contexts')
            contexts.add(context)
            result[reader_phase] = review
        cycles[phase] = check
    if _time(cycles['copy']['cycle']['closure']['closed_at']) > _time(result['final']['packet']['created_at']):
        raise ValueError('final reading must follow closed Copy reading/repair/confirmation')
    return result


def remaining_findings(auditor):
    sources = {r['kind']: r for r in auditor.get('source_records', [])}
    if 'config' not in sources or not bounded(load_ref(source_ref(sources['config']))):
        return []
    result = []
    for phase in ('copy', 'final'):
        source = source_ref(sources['reader-cycle-' + phase])
        check = validate_cycle(load_ref(source))
        issues = {x['issue_id']: x for x in check['issues']}
        pending = []
        for row in check['remaining']:
            issue = issues[row['issue_id']]
            finding = issue.get('finding', {})
            pending.append({'id': row['issue_id'], 'slide_ids': finding.get('slide_ids', []),
                            'statement': row['explanation'], 'reader_impact': finding.get('reader_impact', 'Unresolved reader comparison')})
        for f in check['new_findings']:
            pending.append({**f, 'id': 'new-' + f['phase'] + '-' + f['finding_id']})
        for f in pending:
            result.append({'finding_id': 'READER-CYCLE-' + phase + '-' + f['id'],
                'requirement_ids': [], 'rule_ids': [], 'slide_ids': f['slide_ids'],
                'owner_layer': 'copy' if phase == 'copy' else 'output', 'severity': 'moderate',
                'statement': f['statement'], 'expected': 'Readers understand the visible delivered material.',
                'actual': f['statement'], 'impact': f['reader_impact'],
                'evidence_refs': ['reader-cycle-' + phase + ' sha256=' + source['sha256']],
                'recommended_change': 'Report only: repair budget exhausted; retain for next task or version.'})
    return result
