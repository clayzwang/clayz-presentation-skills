#!/usr/bin/env python3
"""Render a native Art prototype before visual locking; never infer quality."""
import argparse,hashlib,json,pathlib,subprocess,datetime,re

def ref(p):
    p=pathlib.Path(p).resolve()
    return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)

def render(pptx,directory,slide_ids=None):
    pptx=pathlib.Path(pptx).resolve();directory=pathlib.Path(directory).resolve()
    directory.mkdir(parents=True,exist_ok=False)
    def run(cmd):
        r=subprocess.run(list(map(str,cmd)),capture_output=True,text=True)
        if r.returncode: raise RuntimeError(r.stdout+r.stderr)
        return r.stdout+r.stderr
    (directory/'libreoffice.log').write_text(run(['libreoffice','-env:UserInstallation=file://'+str(directory/'lo-profile'),'--headless','--convert-to','pdf','--outdir',directory,pptx]))
    pdf=directory/pptx.with_suffix('.pdf').name
    (directory/'pdffonts.txt').write_text(run(['pdffonts',pdf]))
    run(['pdftoppm','-png','-scale-to','1600',pdf,directory/'slide'])
    files=sorted(directory.glob('slide-*.png'))
    if not files: raise ValueError('native prototype produced no images')
    ids=slide_ids if slide_ids is not None else [f'S{i:02}' for i in range(1,len(files)+1)]
    if len(ids)!=len(files) or len(set(ids))!=len(ids) or any(not isinstance(s,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*',s) for s in ids):
        raise ValueError('Art slide identities must safely cover rendered physical pages once')
    for sid,p in zip(ids,files):p.rename(directory/(sid+'.png'))
    manifest=dict(contract='io.clayz.presentation.native-art-preview/1.0',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),pptx=ref(pptx),pdf=ref(pdf),backend='LibreOffice + Poppler',slides=[dict(slide_id=sid,**ref(directory/(sid+'.png'))) for sid in ids],limitations=['Actual native prototype; not final Output evidence.','Rendering alone does not establish visual or content quality.','PowerPoint and WPS are not observed.'])
    (directory/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('pptx',type=pathlib.Path);p.add_argument('--directory',type=pathlib.Path,required=True);p.add_argument('--art-content',type=pathlib.Path);a=p.parse_args()
    content=json.loads(a.art_content.read_text()) if a.art_content else None
    ids=[s['slide_id'] for s in content['slides']] if content else None
    m=render(a.pptx,a.directory,ids);print(json.dumps(dict(pages=len(m['slides']),manifest=str(a.directory/'manifest.json'))))
