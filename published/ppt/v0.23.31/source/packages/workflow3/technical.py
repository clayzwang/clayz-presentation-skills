"""Observable native file checks, separate from human/host quality judgments."""
from __future__ import annotations
import posixpath
import re
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile
from . import io

CONTRACT='io.clayz.presentation.mode-output-qa/1.0'
REQUIRED=('all_page_images','reading_path','data_signs_units','native_editability','fonts_native_reopen','overflow','relationship_expression')
NS={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships','c':'http://schemas.openxmlformats.org/drawingml/2006/chart'}


def native_inventory(pptx):
    with zipfile.ZipFile(pptx)as z:
        pres=ET.fromstring(z.read('ppt/presentation.xml'))
        rel=ET.fromstring(z.read('ppt/_rels/presentation.xml.rels'))
        targets={r.attrib['Id']:r.attrib['Target']for r in rel if r.attrib.get('TargetMode')!='External'}
        result=[]
        for element in pres.findall('p:sldIdLst/p:sldId',NS):
            target=targets[element.attrib['{'+NS['r']+'}id']]
            path=target.lstrip('/')if target.startswith('/')else posixpath.normpath(posixpath.join('ppt',target))
            if not path.startswith('ppt/slides/'):raise ValueError('unsafe PPTX slide relationship')
            root=ET.fromstring(z.read(path))
            paragraphs=[''.join(p.itertext())for p in root.findall('.//a:t',NS)]
            # Joining runs preserves signs and punctuation. Whitespace is the
            # only normalization, so a missing minus or unit is not erased.
            text=''.join(paragraphs)
            chart_values=[]
            relpath=posixpath.join(posixpath.dirname(path),'_rels',posixpath.basename(path)+'.rels')
            if relpath in z.namelist():
                relationships=ET.fromstring(z.read(relpath))
                for relation in relationships:
                    if relation.attrib.get('TargetMode')=='External' or not relation.attrib.get('Type','').endswith('/chart'):continue
                    target=relation.attrib['Target']
                    member=target.lstrip('/')if target.startswith('/')else posixpath.normpath(posixpath.join(posixpath.dirname(path),target))
                    if not member.startswith('ppt/charts/'):raise ValueError('unsafe native chart relationship')
                    chart=ET.fromstring(z.read(member))
                    chart_values += [n.text or '' for n in chart.findall('.//c:v',NS)]+[n.text or ''for n in chart.findall('.//a:t',NS)]
            result.append({'member':path,'native_text':text,'native_chart_values':chart_values,'text_run_count':len(paragraphs),'picture_count':len(root.findall('.//p:pic',NS))})
        return result


def capture(root,qa,files,dependency):
    if qa.get('contract')!=CONTRACT:raise ValueError('explicit mode-output-qa/1.0 observations required; do not relabel legacy QA')
    checks=qa.get('checks',{})
    if set(checks)!=set(REQUIRED):raise ValueError('all required quality checks need explicit observed/deferred/not-observed status')
    evidence={};unobserved=[];failed=[]
    for key,row in checks.items():
        if not isinstance(row,dict)or row.get('status')not in {'pass','fail','not-observed','deferred'}or not row.get('explanation'):raise ValueError('concrete check status and scope/explanation required')
        refs=row.get('evidence',[])
        if not isinstance(refs,list)or(row['status']in {'pass','fail'}and not refs):raise ValueError('observed quality judgments need actual evidence files')
        evidence[key]=[]
        for ref in refs:
            path=Path(ref['path']);raw=path.read_bytes()
            if io.digest(raw)!=ref['sha256']or len(raw)!=ref['bytes']:raise ValueError('QA evidence identity changed')
            evidence[key].append(io.snapshot(root,path))
        if row['status']in {'not-observed','deferred'}:unobserved.append(key)
        if row['status']=='fail':failed.append(key)
    inventory=native_inventory(io.resolve(root,files['pptx']))
    if len(inventory)!=len(dependency['details']['pages']):raise ValueError('written PPTX slide order/count differs from Art')
    graph=io.read(io.resolve(root,dependency['details']['copy_graph']))
    from packages.copy_graph import model
    missing=[]
    def normalized(s):return re.sub(r'\s+','',s)
    for page,actual in zip(graph['pages'],inventory):
        nodes={n['id']:n for n in graph['nodes']}
        text=normalized(actual['native_text'])
        for nid in page['node_ids']:
            node=nodes[nid]
            tokens=model.table_tokens(node)if node['kind']=='body'and node['content']['type']=='table'else[{'copy_id':nid,'text':model.node_text(node)}]
            for token in tokens:
                if normalized(token['text'])not in text and normalized(token['text'])not in {normalized(v)for v in actual['native_chart_values']}:missing.append({'slide_id':page['id'],'copy_id':token['copy_id'],'expected':token['text']})
    if missing:raise ValueError('Copy text/data missing from editable native slide text: '+str(missing[:8]))
    return {'contract':CONTRACT,'quality_evidence':evidence,'unobserved_checks':unobserved,'failed_checks':failed,'native_inventory':inventory,'scope':'XML native-text and slide-count checks only. Human graph/visual judgment and native PowerPoint rendering remain the explicit observations above.'}
