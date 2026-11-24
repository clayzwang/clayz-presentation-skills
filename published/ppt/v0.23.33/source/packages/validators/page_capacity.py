"""Check approved frame space, including the source region inside the page.

This detects insufficient geometric separation, not glyph ink collisions.
Intentional overlapping diagrams need a separate relation-aware check.
"""
def inspect(specs, minimum_footer_gap_pt=10.8, page_height_pt=540):
    findings=[]
    for spec in specs:
        footer=[e for e in spec['elements'] if e.get('purpose')=='annotation' and e['box'][1]>=.75]
        for e in spec['elements']:
            if e.get('purpose') in {'annotation','自动页码','页序定位'}:continue
            x,y,w,h=e['box']
            for f in footer:
                fx,fy,fw,fh=f['box']
                if x+w<=fx or fx+fw<=x:continue
                gap=(fy-y-h)*page_height_pt
                if gap<minimum_footer_gap_pt:
                    findings.append(dict(slide_id=spec['slide_id'],element_id=e['element_id'],footer_id=f['element_id'],gap_pt=round(gap,3),required_gap_pt=minimum_footer_gap_pt,kind='footer-clearance'))
    return dict(ok=not findings,findings=findings,limitation='Frame clearance only; does not certify ink collision, table cells or visual quality.')
