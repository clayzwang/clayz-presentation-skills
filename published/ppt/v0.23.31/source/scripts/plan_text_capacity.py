#!/usr/bin/env python3
"""Calculate a diagnostic width bound; never approve a layout or render it."""
import argparse,json,math

def plan(span,frame,margins=0.0,paragraph_edges=0.0,reserve=0.1):
    values=(span,frame,margins,paragraph_edges,reserve)
    if not all(math.isfinite(x) for x in values): raise ValueError("Finite measurements required")
    if span<0 or margins<0 or paragraph_edges<0 or frame<=margins+paragraph_edges or not 0<=reserve<1:
        raise ValueError("Invalid width, deductions or reserve")
    usable=frame-margins-paragraph_edges
    required=span/(1-reserve)+margins+paragraph_edges
    return dict(observed_span_pt=span,current_usable_width_pt=usable,
                observed_reserve=1-span/usable,required_frame_width_pt=required,
                additional_width_pt=max(0.0,required-frame),
                scope="Unchanged measured line span only; reflow and font changes require actual observation; not acceptance")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--span',type=float,required=True);p.add_argument('--frame',type=float,required=True)
    p.add_argument('--margins',type=float,default=0);p.add_argument('--paragraph-edges',type=float,default=0)
    p.add_argument('--reserve',type=float,default=0.1)
    a=p.parse_args();print(json.dumps(plan(a.span,a.frame,a.margins,a.paragraph_edges,a.reserve),ensure_ascii=False))
if __name__=='__main__': main()
