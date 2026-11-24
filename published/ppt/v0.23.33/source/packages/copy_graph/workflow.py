"""Immutable Copy generation records and a lossless, versioned Art boundary.

This is an interface, not an author or sixth production stage. Source text and
editorial judgments are always supplied by Copy; no prose/layout generator.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from . import model as m

INPUT = 'io.clayz.presentation.copy-input/1.0'
RECORD = 'io.clayz.presentation.copy-generation/1.0'
INTERFACE = 'io.clayz.presentation.copy-art-interface/1.0'


def now():
    return datetime.now(timezone.utc).isoformat()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    return m.file_ref(p)


def prepare(report, brief, output):
    task = load(brief)
    allowed = {'purpose', 'audience', 'pagination_requirements', 'wording_requirements'}
    if not isinstance(task, dict) or set(task) - allowed or not m.nonempty(task.get('purpose')):
        raise ValueError('Copy input contains only its professional brief and the full Logic written report')
    for v in task.values():
        if not (m.nonempty(v) or isinstance(v, list) and all(m.nonempty(x) for x in v)):
            raise ValueError('Copy brief uses task wording, not old accounts or runtime configuration')
    text = Path(report).read_text(encoding='utf-8')
    if not text.strip():
        raise ValueError('full written Logic report is required')
    return write(output, {'contract': INPUT, 'research_report': m.file_ref(report),
                          'brief': task, 'recorded_at': now()})


def check_input(value):
    if not isinstance(value, dict) or set(value) != {'contract', 'research_report', 'brief', 'recorded_at'} or value['contract'] != INPUT:
        raise ValueError('fresh report-only Copy input required')
    text = m.read_ref(value['research_report']).decode('utf-8')
    brief = value['brief']
    if not isinstance(brief,dict) or set(brief) - {'purpose','audience','pagination_requirements','wording_requirements'} or not m.nonempty(brief.get('purpose')) or any(not (m.nonempty(v) or isinstance(v,list) and all(m.nonempty(x) for x in v)) for v in brief.values()):
        raise ValueError('Copy input brief must contain only purpose, audience, pagination_requirements and wording_requirements')
    if not text.strip():
        raise ValueError('written report is empty')
    return text


def check_record(value):
    if not isinstance(value, dict) or value.get('contract') != RECORD or set(value) != {'contract', 'phase', 'input', 'previous', 'payload', 'recorded_at'}:
        raise ValueError('actual Copy generation record required')
    inp = json.loads(m.read_ref(value['input'])); text = check_input(inp)
    phase, payload, prev = value['phase'], value['payload'], value['previous']
    if prev is not None:
        old = check_record(json.loads(m.read_ref(prev)))
        if old['input'] != value['input']:
            raise ValueError('generation record changed the original Copy input')
    else:
        old = None
    if phase == 'main':
        if prev is not None or set(payload) != {'pages', 'nodes', 'connections', 'reading_review'} or not m.nonempty(payload['reading_review']):
            raise ValueError('read the whole report and record all storylines before subsidiary chains')
        graph = {'contract': m.CONTRACT, 'research_report': inp['research_report'],
                 **{k: payload[k] for k in ('pages', 'nodes', 'connections')},
                 'main_chain': [p['storyline_id'] for p in payload['pages']],
                 'semantic_review': {k: 'Main-chain structural check; full editorial review follows.' for k in ('storylines','information_preservation','selection_and_omissions','uncertainty','relations')}}
        if len(graph['nodes']) < 2:
            # A singleton main chain has no relation yet; final graph must connect
            # it to local content or actual framing. Do not invent a self edge.
            for n in graph['nodes']:
                m.validate_node(n, text)
            if len(graph['pages']) != 1 or len(graph['nodes']) != 1 or graph['pages'][0] != {'id': graph['nodes'][0]['page_id'], 'role':'content', 'storyline_id':graph['nodes'][0]['id'], 'node_ids':[graph['nodes'][0]['id']]} or graph['nodes'][0]['kind'] != 'head' or graph['nodes'][0]['level'] != 1 or graph['connections']:
                raise ValueError('single-page main chain requires exactly its one storyline')
        else:
            m.require_valid(graph)
        if any(n['kind'] != 'head' or n['level'] != 1 for n in payload['nodes']) or any(p['role'] != 'content' for p in payload['pages']):
            raise ValueError('main is the complete ordered content-storyline chain only')
    elif phase in {'heads', 'bodies'}:
        if old is None or set(payload) != ({'page_id','nodes'} if phase == 'heads' else {'page_id','nodes','connections'}):
            raise ValueError('page generation needs its previous actual immutable record')
        history = history_records(value, include_self=False)
        main = history[0]['payload']; pids = [p['id'] for p in main['pages']]
        completed = [r['payload']['page_id'] for r in history if r['phase'] == 'bodies']
        if len(completed) >= len(pids) or payload['page_id'] != pids[len(completed)]:
            raise ValueError('generate each page subsidiary chain sequentially after the complete main chain')
        if phase == 'heads' and old['phase'] not in {'main','bodies'} or phase == 'bodies' and (old['phase'] != 'heads' or old['payload']['page_id'] != payload['page_id']):
            raise ValueError('generate all heading layers, then bodies; no retroactive heading insertion')
        if not isinstance(payload['nodes'], list):
            raise ValueError('actual node array required, possibly empty')
        known = [n for r in history for n in r['payload']['nodes']]
        for n in payload['nodes']:
            m.validate_node(n, text)
            if n['page_id'] != payload['page_id'] or n['kind'] != ('head' if phase == 'heads' else 'body') or n['level'] < 2 or n['id'] in {x['id'] for x in known}:
                raise ValueError('subsidiary nodes must retain their page, kind, level and unique identity')
            known.append(n)
        if phase == 'heads':
            levels = [n['level'] for n in payload['nodes']]
            if levels != sorted(levels) or set(levels) != set(range(2, max(levels, default=1)+1)):
                raise ValueError('subheadings are generated in complete ascending layers')
        else:
            local = {n['id']:n for n in known if n['page_id'] == payload['page_id']}
            m.validate_edges(payload['connections'], local)
            if any(e['scope'] != 'page' for e in payload['connections']) or not m.connected(local, payload['connections']):
                raise ValueError('page subsidiary chain must connect every local node into its storyline')
    else:
        raise ValueError('unsupported Copy generation phase')
    return value


def history_records(record, include_self=True):
    result = [record] if include_self else []
    prev = record['previous']
    while prev is not None:
        item = json.loads(m.read_ref(prev)); result.append(item); prev = item['previous']
    return list(reversed(result))


def record(input_path, phase, payload_path, previous, output):
    check_input(load(input_path))
    value = {'contract':RECORD, 'phase':phase, 'input':m.file_ref(input_path),
             'previous':m.file_ref(previous) if previous else None,
             'payload':load(payload_path), 'recorded_at':now()}
    check_record(value)
    return write(output, value)


def assemble(last_record, review, output, framing=None):
    last = check_record(load(last_record)); history = history_records(last)
    main = history[0]['payload']; pids = [p['id'] for p in main['pages']]
    if [r['payload']['page_id'] for r in history if r['phase']=='bodies'] != pids:
        raise ValueError('all sequential page subsidiary chains must actually exist before assembly')
    pages = json.loads(json.dumps(main['pages'])); nodes = list(main['nodes']); edges = list(main['connections'])
    for r in history[1:]:
        payload = r['payload']; nodes += payload['nodes']
        page = next(p for p in pages if p['id']==payload['page_id'])
        page['node_ids'] += [n['id'] for n in payload['nodes']]
        if r['phase']=='bodies':
            edges += payload['connections']
    if framing:
        frame = load(framing)
        if set(frame) != {'pages','nodes','connections'} or any(p['role'] not in {'cover','closing'} for p in frame['pages']):
            raise ValueError('framing adds only actual cover/closing content, never content-page edits')
        cover = [p for p in frame['pages'] if p['role']=='cover']; closing = [p for p in frame['pages'] if p['role']=='closing']
        pages = cover + pages + closing; nodes += frame['nodes']; edges += frame['connections']
    graph = {'contract':m.CONTRACT, 'research_report':load(last['input']['path'])['research_report'],
             'pages':pages,'nodes':nodes,'connections':edges,
             'main_chain':[p['storyline_id'] for p in main['pages']], 'semantic_review':load(review)}
    m.require_valid(graph)
    return write(output,graph)


def check_assembly(graph, last_ref):
    last = check_record(json.loads(m.read_ref(last_ref))); history = history_records(last)
    main = history[0]['payload']
    if graph['research_report'] != json.loads(m.read_ref(last['input']))['research_report']:
        raise ValueError('assembly changed the original Logic report')
    expected_nodes = [n for r in history for n in r['payload']['nodes']]
    expected_edges = [e for r in history for e in r['payload'].get('connections',[])]
    actual_nodes = [n for n in graph['nodes'] if n['page_id'] in {p['id'] for p in main['pages']}]
    if actual_nodes != expected_nodes or [p['storyline_id'] for p in main['pages']] != graph['main_chain']:
        raise ValueError('final Copy must be assembled from its actual preceding generation records')
    expected_pages = json.loads(json.dumps(main['pages']))
    for record in history[1:]:
        page = next(p for p in expected_pages if p['id'] == record['payload']['page_id'])
        page['node_ids'] += [n['id'] for n in record['payload']['nodes']]
    if [p for p in graph['pages'] if p['role']=='content'] != expected_pages:
        raise ValueError('assembly changed the recorded content-page sequence or ownership')
    if not all(e in graph['connections'] for e in expected_edges) or any(e not in expected_edges and e['scope'] not in {'framing','cross-page'} for e in graph['connections']):
        raise ValueError('Copy changed previously recorded main/page relations')
    if [r['payload']['page_id'] for r in history if r['phase']=='bodies'] != [p['id'] for p in main['pages']]:
        raise ValueError('page generation is incomplete')
    return last


def passthrough(copy_output, output, receipt):
    original = m.file_ref(copy_output); raw = m.read_ref(original); graph = json.loads(raw); m.require_valid(graph)
    p = Path(output); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:
        f.write(raw)
    value = {'contract':INTERFACE,'payload_contract':m.CONTRACT,'mode':'identity',
             'input':original,'output':m.file_ref(p),'recorded_at':now(),
             'quality':'structure/provenance only; requires native readers and audit'}
    check_interface(value)
    return write(receipt,value)


def check_interface(value):
    if not isinstance(value,dict) or set(value) != {'contract','payload_contract','mode','input','output','recorded_at','quality'} or value['contract'] != INTERFACE or value['payload_contract'] != m.CONTRACT or value['mode'] != 'identity':
        raise ValueError('supported identity Copy-to-Art interface receipt required')
    if m.read_ref(value['input']) != m.read_ref(value['output']):
        raise ValueError('identity interface changed Copy output bytes')
    return m.require_valid(json.loads(m.read_ref(value['output'])))


def art_lock(receipt):
    value = load(receipt); graph = check_interface(value)
    return {'interface':m.file_ref(receipt),'graph_sha256':m.digest(graph),'authority':'presentation-only'}


def check_art(graph, design, receipt_ref):
    value = json.loads(m.read_ref(receipt_ref)); actual = check_interface(value)
    if actual != graph:
        raise ValueError('Art input must equal the interface output Copy graph')
    expected = {'interface':receipt_ref,'graph_sha256':m.digest(graph),'authority':'presentation-only'}
    if design.get('copy_structure_lock') != expected or 'art_content' in design:
        raise ValueError('Art cannot edit, repaginate or project Copy content; bind the exact interface output')
    if [s.get('slide_id') for s in design.get('slides',[])] != [p['id'] for p in graph['pages']]:
        raise ValueError('Art must faithfully present the exact Copy page sequence')
    if any(s.get('expression_additions') for s in design.get('slides',[])):
        raise ValueError('Art cannot add textual conclusions or expression beyond supplied Copy elements')
    observations = design.get('audit_observations')
    if not isinstance(observations,list):
        raise ValueError('Art must explicitly retain actual objections in audit_observations, possibly empty')
    known = {n['id'] for n in graph['nodes']}
    for row in observations:
        if not isinstance(row,dict) or set(row) != {'node_ids','observation','impact','disposition'} or not isinstance(row['node_ids'],list) or any(x not in known for x in row['node_ids']) or not m.nonempty(row['observation']) or not m.nonempty(row['impact']) or row['disposition'] != 'audit-only':
            raise ValueError('Art objections are attributed audit-only observations, never rewrite dispatches')
    return actual
