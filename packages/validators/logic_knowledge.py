"""Retrieve explicitly selected reference knowledge for Logic, without quality scores."""
import hashlib,json,pathlib

def ref(path):
 p=pathlib.Path(path).resolve();return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)

def lookup(root,selection):
 root=pathlib.Path(root);manifest=json.loads((root/'manifest.json').read_text());nodes_path=root/manifest['nodes']
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
  seen.add(code);results.append(dict(record=by_code[code],reason=item['reason'],decision=item['decision']))
 cases=[];case_index=None
 if 'industry-research-cases.json' in manifest['files']:
  path=root/'industry-research-cases.json'
  if ref(path)['sha256']!=manifest['files'][path.name]:raise ValueError('industry case index hash mismatch')
  case_index=ref(path);available={c['case_id']:c for c in json.loads(path.read_text())['cases']}
  for case_id in selection.get('case_ids',[]):
   if case_id not in available:raise ValueError('unknown industry case: '+str(case_id))
   cases.append(available[case_id])
 elif selection.get('case_ids'):raise ValueError('industry case index missing')
 return dict(contract='io.clayz.presentation.logic-knowledge-retrieval/1.0',status='retrieved-reference-only',knowledge_version=manifest['version'],manifest=ref(root/'manifest.json'),nodes=ref(nodes_path),selected=results,case_index=case_index,selected_cases=cases,limitation='检索证明所选参考条目与版本；不证明研究质量、当期事实或人类确认。历史案例不可替代新行业官方资料调研。')
