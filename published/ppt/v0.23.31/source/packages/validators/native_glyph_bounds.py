"""Inspect reopened PDF line bounds against approved manual text frames.

Exact normalized text matching is deliberately conservative. Tables, unmatched
text and visual quality require separate inspection; an empty spill list alone
is not a release approval.
"""
import hashlib,json,pathlib,re,subprocess,tempfile,xml.etree.ElementTree as E

def normalize(value):return re.sub(r'\s','',value)
def frames(spec,width,height):
 for e in spec['elements']:
  x,y,w,h=e['box'];frame=[x*width,y*height,(x+w)*width,(y+h)*height]
  if e['kind']=='text':yield e,frame
  elif e['kind']=='table':
   table=e['semantic_table'];sx=w*width/table['width'];sy=h*height/table['height'];yy=frame[1]
   for ri,row in enumerate(table['cells']):
    xx=frame[0]
    for ci,cell in enumerate(row):
     yield dict(element_id=e['element_id']+f':r{ri}c{ci}',lines=cell['lines']),[xx,yy,xx+table['widths'][ci]*sx,yy+table['heights'][ri]*sy]
     xx+=table['widths'][ci]*sx
    yy+=table['heights'][ri]*sy
def inspect_bbox(xml, specs, tolerance=1.0):
 root=E.fromstring(xml);ns='{http://www.w3.org/1999/xhtml}';pages=list(root.iter(ns+'page'));matched=[];unmatched=[];spills=[]
 if len(pages)!=len(specs):raise ValueError('PDF and approved design page counts differ')
 for page,spec in zip(pages,specs):
  width=float(page.attrib['width']);height=float(page.attrib['height']);actual=[]
  for line in page.iter(ns+'line'):
   text=''.join(w.text or '' for w in line.iter(ns+'word'));actual.append((normalize(text),text,{k:float(v) for k,v in line.attrib.items()}))
  for e,frame in frames(spec,width,height):
   for expected in e.get('lines',[]):
    found=[(txt,b) for norm,txt,b in actual if norm==normalize(expected) and b['yMax']>=frame[1]-tolerance and b['yMin']<=frame[3]+tolerance and b['xMax']>=frame[0]-tolerance and b['xMin']<=frame[2]+tolerance]
    if len(found)!=1:
     unmatched.append(dict(slide_id=spec['slide_id'],element_id=e['element_id'],expected=expected,candidate_count=len(found)));continue
    text,bounds=found[0];row=dict(slide_id=spec['slide_id'],element_id=e['element_id'],text=text,bounds=bounds,frame=frame);matched.append(row)
    over={'left':frame[0]-bounds['xMin'],'right':bounds['xMax']-frame[2],'top':frame[1]-bounds['yMin'],'bottom':bounds['yMax']-frame[3]};over={k:round(v,3) for k,v in over.items() if v>tolerance}
    if over:spills.append({**row,'overrun_pt':over,'outside_page':bounds['xMin']<0 or bounds['yMin']<0 or bounds['xMax']>width or bounds['yMax']>height})
 return dict(status='needs-review' if spills or unmatched else 'clear-for-matched-text',matched_line_count=len(matched),matched_table_line_count=sum(':r' in r['element_id'] for r in matched),matched_lines=matched,unmatched_lines=unmatched,frame_spills=spills,limitations=['Only exact normalized approved text lines are matched; unmatched remains unresolved.','Table lines use complete cell frames, not inner padding; ink shape, meaning, hierarchy and comparison efficiency require visual review.'])

def audit(pdf,design):
 pdf=pathlib.Path(pdf);design=pathlib.Path(design)
 with tempfile.TemporaryDirectory(prefix='ppt-glyph-bounds-') as directory:
  xml=pathlib.Path(directory)/'bbox.html';subprocess.run(['pdftotext','-bbox-layout',str(pdf),str(xml)],check=True,capture_output=True)
  result=inspect_bbox(xml.read_bytes(),json.loads(design.read_text()))
 result['inputs']={key:dict(path=str(p.resolve()),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for key,p in [('pdf',pdf),('design',design)]}
 return result
