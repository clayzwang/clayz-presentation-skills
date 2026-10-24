"""Verify explicitly selected native edit units in an editable PPTX.

The author supplies only commitments made for this deck. This does not choose
charts, tables, connectors, or layout, and it cannot prove GUI drag behaviour.
"""
from __future__ import annotations

import argparse,json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path

P='{http://schemas.openxmlformats.org/presentationml/2006/main}'
A='{http://schemas.openxmlformats.org/drawingml/2006/main}'

def audit(pptx:Path,plan:dict)->dict:
    pptx=Path(pptx);issues=[];slides=[]
    with zipfile.ZipFile(pptx) as z:
        names=sorted((p for p in z.namelist() if p.startswith('ppt/slides/slide') and p.endswith('.xml')),key=lambda p:int(p.rsplit('slide',1)[1].split('.')[0]))
        for i,path in enumerate(names,1):
            root=ET.fromstring(z.read(path));shapes={}
            for sp in root.findall('.//'+P+'sp'):
                pr=sp.find('.//'+P+'cNvPr');name=pr.get('name') if pr is not None else ''
                shapes[name]=''.join(t.text or '' for t in sp.findall('.//'+A+'t'))
            slides.append({'slide':i,'page_fields':len(root.findall('.//'+A+'fld[@type="slidenum"]')),'tables':len(root.findall('.//'+A+'tbl')),'shapes':shapes})
    for s in plan.get('automatic_page_fields',[]):
        i=int(s['slide']);expected=int(s.get('count',1))
        if i<1 or i>len(slides) or slides[i-1]['page_fields']!=expected:issues.append({'kind':'page_fields','slide':i,'expected':expected,'actual':slides[i-1]['page_fields'] if 1<=i<=len(slides) else None})
    for s in plan.get('native_tables',[]):
        i=int(s['slide']);minimum=int(s.get('minimum',1))
        if i<1 or i>len(slides) or slides[i-1]['tables']<minimum:issues.append({'kind':'native_tables','slide':i,'minimum':minimum,'actual':slides[i-1]['tables'] if 1<=i<=len(slides) else None})
    for s in plan.get('integrated_labels',[]):
        i=int(s['slide']);name=s['shape'];needle=s.get('contains','')
        actual=slides[i-1]['shapes'].get(name) if 1<=i<=len(slides) else None
        if actual is None or not actual or (needle and needle not in actual):issues.append({'kind':'integrated_label','slide':i,'shape':name,'contains':needle,'actual':actual})
    for s in plan.get('forbidden_overlay_shapes',[]):
        i=int(s['slide']);name=s['shape']
        if 1<=i<=len(slides) and name in slides[i-1]['shapes']:issues.append({'kind':'overlay_shape_remains','slide':i,'shape':name})
    return {'pptx':str(pptx),'slides':len(slides),'checked':{k:len(plan.get(k,[])) for k in ('automatic_page_fields','native_tables','integrated_labels','forbidden_overlay_shapes')},'issues':issues,'passed':not issues,'scope':'OOXML structure only; no PowerPoint/WPS GUI edit or composition quality claim.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('pptx',type=Path);p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path);a=p.parse_args()
    result=audit(a.pptx,json.loads(a.plan.read_text()))
    data=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(data)
    else:print(data,end='')
    return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
