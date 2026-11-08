"""Reject failed or stale technical records before constructing formal QA."""
import hashlib,pathlib
def inspect(pptx,pdf,reports,manifest):
    pptx=pathlib.Path(pptx);pdf=pathlib.Path(pdf);ph=hashlib.sha256(pptx.read_bytes()).hexdigest();dh=hashlib.sha256(pdf.read_bytes()).hexdigest();errors=[]
    bound={'native-comparison','font-name-audit','cjk-render-report','size-audit','object-inventory'}
    checks=bound-{'object-inventory'}|{'font-environment','pdf-text-check'}
    for name in bound:
        if reports.get(name,{}).get('pptx_sha256')!=ph:errors.append(name+': stale or missing PPTX binding')
    for name in checks:
        if reports.get(name,{}).get('ok') is not True:errors.append(name+': actual success not established')
    if manifest.get('pptx_sha256')!=ph:errors.append('render-manifest: stale PPTX binding')
    if reports.get('cjk-render-report',{}).get('pdf_sha256')!=dh or reports.get('pdf-text-check',{}).get('pdf',{}).get('sha256')!=dh:errors.append('final PDF binding differs')
    return {'ok':not errors,'errors':errors,'pptx_sha256':ph,'pdf_sha256':dh,'scope':'Technical binding only; visual evidence and fresh readers remain separate gates.'}
