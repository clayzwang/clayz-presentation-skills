import argparse,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from packages.validators.logic_knowledge import lookup,ref
def main():
 a=argparse.ArgumentParser();a.add_argument('--pack',required=True);a.add_argument('--selection',required=True);a.add_argument('--output',required=True);x=a.parse_args()
 result=lookup(x.pack,json.loads(pathlib.Path(x.selection).read_text()))
 result['selection']=ref(x.selection)
 pathlib.Path(x.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(dict(status=result['status'],knowledge_version=result['knowledge_version'],codes=[r['record']['code'] for r in result['selected']]),ensure_ascii=False))
if __name__=='__main__':main()
