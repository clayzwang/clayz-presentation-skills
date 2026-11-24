#!/usr/bin/env python3
"""Copy graph generation journal and identity interface; no authoring defaults."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from packages.copy_graph import model as m, workflow as w


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='command',required=True)
    fields={'prepare':('report','brief','output'), 'main':('input','payload','output'),
            'heads':('input','payload','previous','output'),'bodies':('input','payload','previous','output'),
            'assemble':('last-record','review','output'), 'interface':('copy-output','output','receipt'),
            'check':('graph',),'markdown':('graph','output'),'coverage':('graph','output'),
            'art-lock':('receipt','output'),'review-evidence':('graph','phase','output'),
            'source-index':('input','output')}
    for name, keys in fields.items():
        s=sub.add_parser(name)
        for k in keys:s.add_argument('--'+k,required=True)
        if name=='assemble':s.add_argument('--framing')
    a=vars(p.parse_args(argv)); cmd=a.pop('command')
    try:
        if cmd=='prepare':r=w.prepare(a['report'],a['brief'],a['output'])
        elif cmd in {'main','heads','bodies'}:r=w.record(a['input'],cmd,a['payload'],a.get('previous'),a['output'])
        elif cmd=='assemble':r=w.assemble(a['last_record'],a['review'],a['output'],a['framing'])
        elif cmd=='interface':r=w.passthrough(a['copy_output'],a['output'],a['receipt'])
        elif cmd=='art-lock':r=w.write(a['output'],w.art_lock(a['receipt']))
        elif cmd=='source-index':
            inp=w.load(a['input']);raw=w.check_input(inp)
            r=w.write(a['output'],{'research_report':inp['research_report'],'offset_unit':'Unicode characters in the exact UTF-8 decoded bytes; CRLF is not normalized','segments':m.source_segments(raw)})
        else:
            g=m.require_valid(w.load(a['graph']))
            if cmd=='check':r={'status':'structure-valid','quality':'not-established'}
            elif cmd=='coverage':r=w.write(a['output'],m.coverage(g))
            elif cmd=='review-evidence':r=w.write(a['output'],m.review_projection(g,a['phase']))
            else:
                out=Path(a['output']);out.parent.mkdir(parents=True,exist_ok=True)
                with out.open('x',encoding='utf-8') as f:f.write(m.markdown(g))
                r=m.file_ref(out)
        print(json.dumps(r,ensure_ascii=False));return 0
    except (OSError,ValueError,TypeError,KeyError) as e:
        print('ERROR: '+str(e),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
