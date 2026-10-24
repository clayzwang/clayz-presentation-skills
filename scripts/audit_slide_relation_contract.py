#!/usr/bin/env python3
"""Check authored spatial relation commitments in editable PPTX slides.

This is a bounded structural check. A reader must still judge whether declared
relations and page wording are economically and visually honest.
"""
import argparse,json,math
from pathlib import Path
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Inches

p=argparse.ArgumentParser();p.add_argument('--pptx',required=True);p.add_argument('--manifest',required=True);p.add_argument('--output',required=True);a=p.parse_args()
spec=json.loads(Path(a.manifest).read_text());deck=Presentation(a.pptx);findings=[]
def item(slide,s):
    return [(sh,sh.text) for sh in slide.shapes if sh.has_text_frame and s in sh.text]
def err(kind,slide,detail):findings.append({'kind':kind,'slide':slide,'detail':detail})
if spec.get('forbid_arrowheads'):
    import zipfile,re
    with zipfile.ZipFile(a.pptx) as z:
        for i in range(1,len(deck.slides)+1):
            xml=z.read(f'ppt/slides/slide{i}.xml').decode()
            for m in re.finditer(r'<a:(headEnd|tailEnd)\b[^>]*type="([^"]+)"',xml):
                if m.group(2)!='none':err('unexpected_arrowhead',i,m.group(0))
for ss in spec['slides']:
    n=ss['slide'];slide=deck.slides[n-1]
    for term in ss.get('required_text',[]):
        if not item(slide,term):err('missing_visible_text',n,term)
    for c in ss.get('min_vertical_separation',[]):
        aa=item(slide,c['a']);bb=item(slide,c['b'])
        if len(aa)!=1 or len(bb)!=1:err('ambiguous_separation_subject',n,c)
        else:
            ya=aa[0][0].top+aa[0][0].height/2;yb=bb[0][0].top+bb[0][0].height/2
            if abs(ya-yb)<Inches(c['inches']):err('false_magnitude_pairing',n,{'a':c['a'],'b':c['b'],'gap_inches':round(abs(ya-yb)/Inches(1),3)})
    for c in ss.get('forbid_aligned_pair',[]):
        aa=item(slide,c['a']);bb=item(slide,c['b'])
        if aa and bb:
            ya=aa[0][0].top+aa[0][0].height/2;yb=bb[0][0].top+bb[0][0].height/2
            if abs(ya-yb)<Inches(c.get('tolerance_inches',0.25)):
                err('undeclared_row_pairing',n,{'a':c['a'],'b':c['b'],'gap_inches':round(abs(ya-yb)/Inches(1),3)})
    for c in ss.get('part_whole_bar',[]):
        vals=c['parts'];total=c['total']
        if not math.isclose(sum(vals),total,abs_tol=c.get('sum_tolerance',.02)):
            err('invalid_part_sum',n,{'parts':vals,'total':total});continue
        top=Inches(c['top_inches']);height=Inches(c['height_inches'])
        rects=[sh for sh in slide.shapes if sh.shape_type==MSO_SHAPE_TYPE.AUTO_SHAPE and abs(sh.top-top)<Inches(.04) and abs(sh.height-height)<Inches(.04)]
        rects=sorted(rects,key=lambda sh:sh.left)
        if len(rects)!=len(vals):err('bar_segment_count',n,{'expected':len(vals),'found':len(rects)});continue
        for prev,cur in zip(rects,rects[1:]):
            if abs((prev.left+prev.width)-cur.left)>Inches(.03):err('disjoint_part_whole_bar',n,'segments not adjacent')
        w=sum(sh.width for sh in rects)
        for i,(sh,v) in enumerate(zip(rects,vals)):
            if abs(sh.width/w-v/total)>c.get('ratio_tolerance',.01):
                err('bar_ratio_mismatch',n,{'part':i,'render_fraction':round(sh.width/w,4),'declared_fraction':round(v/total,4)})
    for c in ss.get('nested_composition_bar',[]):
        # A nested label is only honest if each declared parent equals its leaves
        # and the visible segments use the whole as their common denominator.
        whole=float(c['whole']);leaves=[float(v) for v in c['leaves']]
        tolerance=float(c.get('sum_tolerance',.02))
        if not math.isclose(sum(leaves),whole,abs_tol=tolerance):
            err('nested_leaf_identity',n,{'leaves':leaves,'whole':whole})
        claimed=[]
        for group in c['groups']:
            indices=group['leaf_indices'];value=float(group['value'])
            if any(i<0 or i>=len(leaves) for i in indices):
                err('nested_bad_leaf_index',n,group);continue
            claimed.extend(indices)
            if not math.isclose(sum(leaves[i] for i in indices),value,abs_tol=tolerance):
                err('nested_group_identity',n,{'group':group.get('name'),'leaves':[leaves[i] for i in indices],'value':value})
        if sorted(claimed)!=list(range(len(leaves))):
            err('nested_group_partition',n,{'claimed_indices':claimed,'leaf_count':len(leaves)})
        start=Inches(c['start_inches']);width=Inches(c['full_width_inches'])
        top=Inches(c['top_inches']);height=Inches(c['height_inches'])
        pos_tol=Inches(c.get('geometry_tolerance_inches',.04))
        rects=sorted((sh for sh in slide.shapes if sh.shape_type==MSO_SHAPE_TYPE.AUTO_SHAPE
                      and abs(sh.top-top)<=pos_tol and abs(sh.height-height)<=pos_tol),key=lambda sh:sh.left)
        if len(rects)!=len(leaves):
            err('nested_segment_count',n,{'expected':len(leaves),'found':len(rects)});continue
        cursor=start
        for i,(sh,value) in enumerate(zip(rects,leaves)):
            expected_width=width*value/whole
            if abs(sh.left-cursor)>pos_tol or abs(sh.width-expected_width)>pos_tol:
                err('nested_geometry_mismatch',n,{'leaf':i,'expected_left_inches':round(cursor/Inches(1),3),'actual_left_inches':round(sh.left/Inches(1),3),'expected_width_inches':round(expected_width/Inches(1),3),'actual_width_inches':round(sh.width/Inches(1),3)})
            cursor+=expected_width
    for c in ss.get('scenario_matrix',[]):
        # The checker validates authored arithmetic and visible numbers, not
        # whether the assumed range is a credible forecast.
        revenue=float(c['base_revenue']);profit=float(c['base_profit'])
        deltas=[float(v) for v in c['revenue_changes']]
        margins=[float(v) for v in c['profit_margins']]
        declared=c['net_profit_grid'];decimals=int(c.get('decimals',2))
        slide_text=' '.join(sh.text for sh in slide.shapes if sh.has_text_frame)
        if len(declared)!=len(deltas) or any(len(row)!=len(margins) for row in declared):
            err('scenario_grid_shape',n,{'rows':len(declared),'revenue_changes':len(deltas),'profit_margins':len(margins)});continue
        for i,delta in enumerate(deltas):
            row_revenue=round(revenue*(1+delta),decimals)
            if f'{row_revenue:.{decimals}f}' not in slide_text:
                err('scenario_revenue_not_visible',n,{'row':i,'revenue':row_revenue})
            for j,margin in enumerate(margins):
                expected=round(revenue*(1+delta)*margin,decimals)
                observed=float(declared[i][j])
                if not math.isclose(expected,observed,abs_tol=10**(-decimals)/2):
                    err('scenario_grid_arithmetic',n,{'row':i,'column':j,'expected':expected,'declared':observed})
                if f'{observed:.{decimals}f}' not in slide_text:
                    err('scenario_profit_not_visible',n,{'row':i,'column':j,'profit':observed})
        full=c.get('full_year_endpoints')
        if full:
            expected=[round(revenue+revenue*(1+min(deltas)),decimals),
                      round(revenue+revenue*(1+max(deltas)),decimals),
                      round(profit+min(float(v) for row in declared for v in row),decimals),
                      round(profit+max(float(v) for row in declared for v in row),decimals)]
            observed=[float(v) for v in full]
            if any(not math.isclose(x,y,abs_tol=10**(-decimals)/2) for x,y in zip(expected,observed)):
                err('scenario_full_year_arithmetic',n,{'expected':expected,'declared':observed})
            for value in observed:
                if f'{value:.{decimals}f}' not in slide_text:
                    err('scenario_full_year_not_visible',n,{'value':value})
    for c in ss.get('paired_stacked_bars',[]):
        # Check both the accounting identity and a common visual amount scale.
        start=Inches(c['start_inches']);unit=Inches(c['full_scale_width_inches'])/float(c['full_scale_value'])
        pos_tol=Inches(c.get('geometry_tolerance_inches',.04))
        for period in c['periods']:
            vals=[float(v) for v in period['parts']];total=float(period['total'])
            if not math.isclose(sum(vals),total,abs_tol=c.get('sum_tolerance',.02)):
                err('paired_stack_value_identity',n,{'period':period.get('label'),'parts':vals,'total':total});continue
            top=Inches(period['top_inches']);height=Inches(period['height_inches'])
            rects=[sh for sh in slide.shapes if sh.shape_type==MSO_SHAPE_TYPE.AUTO_SHAPE and abs(sh.top-top)<=pos_tol and abs(sh.height-height)<=pos_tol]
            rects=sorted(rects,key=lambda sh:sh.left)
            if len(rects)!=len(vals):
                err('paired_stack_segment_count',n,{'period':period.get('label'),'expected':len(vals),'found':len(rects)});continue
            x=start
            for i,(sh,v) in enumerate(zip(rects,vals)):
                expected_width=v*unit
                if abs(sh.left-x)>pos_tol or abs(sh.width-expected_width)>pos_tol:
                    err('paired_stack_geometry_mismatch',n,{'period':period.get('label'),'part':i,'expected_left_inches':round(x/Inches(1),3),'actual_left_inches':round(sh.left/Inches(1),3),'expected_width_inches':round(expected_width/Inches(1),3),'actual_width_inches':round(sh.width/Inches(1),3)})
                x+=expected_width
    for c in ss.get('waterfall',[]):
        # Values and geometry are author declarations; source truth still needs a reader.
        start=float(c['start']);changes=[float(v) for v in c['changes']];end=float(c['end'])
        xs=c['x_inches'];top=Inches(c['top_inches']);bottom=Inches(c['bottom_inches'])
        maximum=float(c['axis_max']);tol=Inches(c.get('geometry_tolerance_inches',.04))
        if len(xs)!=len(changes)+2:
            err('waterfall_bar_count',n,{'x_positions':len(xs),'expected':len(changes)+2});continue
        if not math.isclose(start+sum(changes),end,abs_tol=c.get('value_tolerance',.02)):
            err('waterfall_value_identity',n,{'start':start,'changes':changes,'end':end});continue
        levels=[(0,start)];running=start
        for change in changes:
            levels.append((min(running,running+change),max(running,running+change)))
            running+=change
        levels.append((0,end))
        def y(value):return bottom-(value/maximum)*(bottom-top)
        for i,(x,(low,high)) in enumerate(zip(xs,levels)):
            candidates=[sh for sh in slide.shapes if sh.shape_type==MSO_SHAPE_TYPE.AUTO_SHAPE and abs(sh.left-Inches(x))<=tol]
            if len(candidates)!=1:
                err('waterfall_shape_ambiguous',n,{'bar':i,'x_inches':x,'found':len(candidates)});continue
            sh=candidates[0];expected_top=y(high);expected_bottom=y(low)
            if abs(sh.top-expected_top)>tol or abs(sh.top+sh.height-expected_bottom)>tol:
                err('waterfall_geometry_mismatch',n,{'bar':i,'expected_top_inches':round(expected_top/Inches(1),3),'actual_top_inches':round(sh.top/Inches(1),3),'expected_bottom_inches':round(expected_bottom/Inches(1),3),'actual_bottom_inches':round((sh.top+sh.height)/Inches(1),3)})
result={'schema':'slide-relation-contract/1.0','pptx':str(Path(a.pptx).resolve()),'manifest':str(Path(a.manifest).resolve()),'valid':not findings,'findings':findings,'scope':'Authored text/geometry/arrow commitments only; cannot infer missing or false semantic relations without reader inspection.'}
Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('PASS' if result['valid'] else 'FAIL',len(findings))
raise SystemExit(0 if result['valid'] else 1)
