import argparse,json
from .integration import init,run_life_ticks,learn,evaluate,audit
def main():
 p=argparse.ArgumentParser();s=p.add_subparsers(dest='cmd',required=True)
 a=s.add_parser('init');a.add_argument('root');a.add_argument('--id',default='TUKUYO-v840-organism-001')
 a=s.add_parser('run');a.add_argument('root');a.add_argument('ticks',type=int)
 a=s.add_parser('eval');a.add_argument('root');a.add_argument('query')
 a=s.add_parser('audit');a.add_argument('root')
 x=p.parse_args()
 if x.cmd=='init':o=init(x.root,x.id)
 elif x.cmd=='run':o=run_life_ticks(x.root,x.ticks)
 elif x.cmd=='eval':o=evaluate(x.root,x.query)
 else:o=audit(x.root)
 print(json.dumps(o,ensure_ascii=False,indent=2))
