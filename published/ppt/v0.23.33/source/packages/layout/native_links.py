"""Attach supplied source links without changing the visible text or typography."""
import copy,re

def link_runs(paragraph,links):
    keys=sorted(links,key=len,reverse=True)
    if not keys:return 0
    pattern=re.compile(r'(?<![A-Za-z0-9])('+ '|'.join(re.escape(k) for k in keys)+r')(?![A-Za-z0-9])')
    count=0
    for run in list(paragraph.runs):
        matches=list(pattern.finditer(run.text))
        if not matches:continue
        old=run._r;parent=old.getparent();pos=parent.index(old);segments=[];at=0
        for m in matches:
            if m.start()>at:segments.append((run.text[at:m.start()],None))
            segments.append((m.group(),links[m.group()]));at=m.end()
        if at<len(run.text):segments.append((run.text[at:],None))
        for text,url in segments:
            new=paragraph.add_run();new.text=text
            if old.rPr is not None:new._r.insert(0,copy.deepcopy(old.rPr))
            if url:new.hyperlink.address=url;count+=1
            parent.remove(new._r);parent.insert(pos,new._r);pos+=1
        parent.remove(old)
    return count

def link_table(table,links):
    return sum(link_runs(p,links) for row in table.rows for cell in row.cells for p in cell.text_frame.paragraphs)
