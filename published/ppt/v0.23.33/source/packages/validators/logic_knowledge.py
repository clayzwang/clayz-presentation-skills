"""Retrieve explicitly selected reference knowledge for Logic, without quality scores."""
import hashlib,json,pathlib

FOUNDATION_FIELDS = {
 'code','kind','parent','title','principle','flow_ids','source_ids','provenance',
 'applicability','actions','limits','concepts','related_codes','reading','question',
 'conclusion_requirement','action_requirement','knowledge_codes','operation_codes','check',
}

def ref(path):
 p=pathlib.Path(path).resolve();return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)

def lookup(root,selection):
 root=pathlib.Path(root);manifest=json.loads((root/'manifest.json').read_text());nodes_path=root/manifest.get('nodes','nodes.json')
 if manifest['files'].get(nodes_path.name)!=ref(nodes_path)['sha256']:raise ValueError('knowledge nodes hash mismatch')
 nodes=json.loads(nodes_path.read_text())['nodes'];by_code={n['code']:n for n in nodes}
 if len(by_code)!=len(nodes):raise ValueError('duplicate knowledge code')
 choices=selection.get('selections')
 if not isinstance(choices,list) or not choices:raise ValueError('explicit Logic knowledge selection required')
 results=[];seen=set()
 for item in choices:
  code=item.get('code')
  if code in seen or code not in by_code:raise ValueError('unknown or duplicate knowledge selection: '+str(code))
  if any(not isinstance(item.get(k),str) or not item[k].strip() for k in ['reason','decision']):raise ValueError('selection needs actual reason and research decision')
  method={key:value for key,value in by_code[code].items() if key in FOUNDATION_FIELDS}
  seen.add(code);results.append(dict(record=method,reason=item['reason'],decision=item['decision']))
 if selection.get('case_ids'):
  raise ValueError('Case-method retrieval is not part of the general Logic workflow; use only the selected foundational knowledge')
 return dict(contract='io.clayz.presentation.logic-knowledge-retrieval/1.1',status='retrieved-reference-only',knowledge_version=manifest['version'],manifest=ref(root/'manifest.json'),nodes=ref(nodes_path),selected=results,limitation='返回所选节点的基础方法字段，省略教学例子与案例字段；版本引用不证明研究质量，不自动读取或采用历史行业案例。')
