from __future__ import annotations
import argparse,json
from pathlib import Path
from .semantic import init,evaluate,make_proposal,verifier_receipt,promote,audit

def j(x): print(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2))
def main():
 p=argparse.ArgumentParser(); sp=p.add_subparsers(dest='cmd',required=True)
 a=sp.add_parser('init'); a.add_argument('root')
 a=sp.add_parser('eval'); a.add_argument('root'); a.add_argument('query')
 a=sp.add_parser('propose'); a.add_argument('surface'); a.add_argument('training_json')
 a=sp.add_parser('audit'); a.add_argument('root')
 x=p.parse_args()
 if x.cmd=='init': j(init(Path(x.root))['payload'])
 elif x.cmd=='eval': j(evaluate(Path(x.root),x.query))
 elif x.cmd=='propose': j(make_proposal(x.surface,json.loads(Path(x.training_json).read_text())))
 elif x.cmd=='audit': j(audit(Path(x.root)))
if __name__=='__main__': main()
