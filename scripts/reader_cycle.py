#!/usr/bin/env python3
"""Collect reader findings, reserve one repair, and close with remaining issues."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from packages.validators.reader_cycle import collect,start_repair,close,validate_cycle,read

def main():
 p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
 a=s.add_parser('collect');a.add_argument('--phase',choices=['copy','final'],required=True)
 for k in ['config','package','output']:a.add_argument('--'+k,type=Path,required=True)
 a.add_argument('--review',action='append',type=Path,required=True,dest='reviews')
 for k in ['plan','pptx','renders']:a.add_argument('--'+k,type=Path)
 a=s.add_parser('start-repair');a.add_argument('--cycle',type=Path,required=True);a.add_argument('--owner',required=True);a.add_argument('--rationale',required=True)
 a=s.add_parser('close');a.add_argument('--cycle',type=Path,required=True);a.add_argument('--closure',type=Path,required=True)
 a=s.add_parser('validate');a.add_argument('--cycle',type=Path,required=True)
 v=vars(p.parse_args());cmd=v.pop('command')
 try:
  if cmd=='collect':result=collect(**v)
  elif cmd=='start-repair':result=start_repair(v['cycle'],v['owner'],v['rationale'])
  elif cmd=='close':result=close(v['cycle'],read(v['closure']))
  else:result=validate_cycle(read(v['cycle']))['cycle']
  print(json.dumps({'record_valid':True,'status':result['status'],'phase':result['phase'],'quality_pass_claimed':False}));return 0
 except (ValueError,KeyError,TypeError,OSError) as e:print(json.dumps({'record_valid':False,'error':str(e)}));return 1
if __name__=='__main__':sys.exit(main())
