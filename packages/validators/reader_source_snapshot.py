"""Freeze reader source bytes outside the blind-input directory."""
import hashlib,json,pathlib,shutil

def ref(path):
 p=pathlib.Path(path).resolve();return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)

def freeze(root,*,package,pptx=None,renders=None,plan=None):
 root=pathlib.Path(root).resolve();root.mkdir(parents=True,exist_ok=False)
 originals={};snapshots={};paths={}
 for key,value,name in [('package',package,'package.json'),('pptx',pptx,'actual.pptx'),('plan',plan,'art-plan.json')]:
  if value is None:continue
  originals[key]=ref(value);target=root/name;shutil.copyfile(value,target)
  snapshots[key]=ref(target);paths[key]=target
  if any(originals[key][k]!=snapshots[key][k] for k in ['sha256','bytes']):raise ValueError('source copy differs: '+key)
 if renders is not None:
  originals['renders']=ref(renders);value=json.loads(pathlib.Path(renders).read_text());out=root/'rendered';out.mkdir()
  image_bindings=[]
  for row in value['slides']:
   old={k:row[k] for k in ['path','sha256','bytes']}
   if ref(old['path'])!=old:raise ValueError('source render differs before snapshot')
   target=out/(row['slide_id']+'.png');shutil.copyfile(old['path'],target);new=ref(target)
   if any(old[k]!=new[k] for k in ['sha256','bytes']):raise ValueError('source render copy differs')
   image_bindings.append(dict(slide_id=row['slide_id'],original=old,snapshot=new));row.update(new)
  paths['renders']=root/'render-manifest.json';paths['renders'].write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');snapshots['renders']=ref(paths['renders'])
 else:image_bindings=[]
 (root/'binding.json').write_text(json.dumps(dict(contract='io.clayz.presentation.reader-source-snapshot/1.0',originals=originals,snapshots=snapshots,images=image_bindings,limitation='只证明准备首读时的实际输入字节被复制保存；不作阅读质量判断。'),ensure_ascii=False,indent=2)+'\n')
 return paths
