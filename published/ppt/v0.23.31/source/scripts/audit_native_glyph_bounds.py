#!/usr/bin/env python3
import argparse,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from packages.validators.native_glyph_bounds import audit
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('pdf');p.add_argument('design');p.add_argument('--output',required=True);a=p.parse_args();r=audit(a.pdf,a.design);pathlib.Path(a.output).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['status','matched_line_count']}))
