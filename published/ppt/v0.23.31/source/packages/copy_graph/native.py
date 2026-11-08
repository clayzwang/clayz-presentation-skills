"""Graph adapter to existing five-stage native verification/report envelope.

The machine envelope stays 3.5; professional Copy authoring is graph/1.0.
Its generated slides are a read-only inspection projection, never authority.
"""
import json
from . import model as m, workflow as w

ENVELOPE = '3.5'
HANDOFF = 'io.clayz.presentation.stage-files/1.1'
ARTIFACTS = {'content','process','generation','art_input','interface'}


def is_graph(package):
    return isinstance(package,dict) and isinstance(package.get('copy_layer'),dict) and 'graph' in package['copy_layer']


def check_handoff(value):
    from packages.validators import stage_files as sf
    if set(value) != {'contract','stage','input','artifacts','recorded_at'} or value['contract'] != HANDOFF or value['stage'] != 'copy':
        raise ValueError('Copy graph professional handoff 1.1 required')
    inp = sf.check_input(sf.json_ref(value['input']))
    if inp['stage'] != 'copy' or set(value['artifacts']) != ARTIFACTS:
        raise ValueError('Copy graph handoff must bind graph, actual generation, interface and process')
    docs=value['artifacts']; graph=m.require_valid(sf.json_ref(docs['content']))
    last=w.check_assembly(graph,docs['generation'])
    report=sf.json_ref(inp['inputs'][0])['artifacts']['report']
    if graph['research_report'] != report or sf.json_ref(last['input'])['research_report'] != report:
        raise ValueError('Copy must consume exactly the approved Logic written report')
    receipt=sf.json_ref(docs['interface']); actual=w.check_interface(receipt)
    if actual != graph or receipt['input'] != docs['content'] or receipt['output'] != docs['art_input']:
        raise ValueError('professional Art input must be the exact interface output')
    sf.validate_process(docs['process'])
    return value


def record_copy(input_path, content, generation, interface, process, output):
    from packages.validators import stage_files as sf
    receipt=w.load(interface); w.check_interface(receipt)
    value={'contract':HANDOFF,'stage':'copy','input':sf.file_ref(input_path),
           'artifacts':{'content':sf.file_ref(content),'generation':sf.file_ref(generation),
                        'interface':sf.file_ref(interface),'art_input':receipt['output'],
                        'process':sf.file_ref(process)},'recorded_at':sf.now()}
    check_handoff(value)
    return sf.write_new(output,value)


def layer(graph, docs, package):
    from packages.validators.story_handoff import digest
    return {'logic_version':package['version'],'pagination_owner':'copy',
            'research_sha256':digest(package['research']),
            'semantic_preservation_review':json.dumps(graph['semantic_review'],ensure_ascii=False),
            'documents':docs,'graph':graph,'slides':m.projection(graph)}


def provenance(graph):
    result={}
    for node in graph['nodes']:
        tokens=m.table_tokens(node) if node['kind']=='body' and node['content']['type']=='table' else [{'copy_id':node['id']}]
        for token in tokens:result[token['copy_id']]=node['source_spans']
    return result


def validate_package(package):
    from packages.validators import stage_files as sf
    from packages.validators.research_handoff import validate_research_package
    from packages.validators.clean_content import validate_cover_policy
    errors=[]
    try:
        origin=sf.json_ref(package['logic_artifact'])
        if origin.get('contract_version') != '3.5' or origin.get('status') != 'logic-approved':
            raise ValueError('original approved Logic native binding required')
        errors.extend(validate_research_package(origin,'logic-approved'))
        for key in ('contract_version','research','brief','acceptance_contract','resource_inventory','package_id','version','configuration_sha256','task_selection','run_binding'):
            if origin.get(key) != package.get(key):raise ValueError(f'Copy changed immutable Logic {key}')
        if package.get('logic_layer') is not None:raise ValueError('Copy cannot invent Logic presentation pages')
        handoff=check_handoff(sf.json_ref(package['professional_handoff'])); docs=handoff['artifacts']
        if sf.json_ref(handoff['input'])['inputs'] != [origin['professional_handoff']]:
            raise ValueError('Copy native binding changed its actual approved Logic handoff')
        graph=sf.json_ref(docs['art_input'])
        if package['copy_layer'] != layer(graph,docs,package) or package.get('copy_provenance') != provenance(graph):
            raise ValueError('Copy graph or technical projection changed after the interface')
        approval=package.get('approvals',{}).get('copy') or {}
        if approval.get('status') != 'approved' or not m.nonempty(approval.get('approved_by')):
            raise ValueError('actual existing Copy approval record required')
        errors.extend(validate_cover_policy(package,package['copy_layer']['slides']))
    except (OSError,ValueError,TypeError,KeyError) as e:
        errors.append('Copy graph binding: '+str(e))
    return errors


def validate_art(package,plan):
    try:
        docs=package['copy_layer']['documents']; graph=package['copy_layer']['graph']
        w.check_art(graph,plan,docs['interface'])
        return []
    except (OSError,ValueError,TypeError,KeyError) as e:return ['Art structure lock: '+str(e)]
