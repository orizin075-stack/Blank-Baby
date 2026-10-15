"""v945 bounded novel representation proposal.

The proposer only receives labelled training rows plus a v944 gap certificate. It
enumerates a generic AST grammar; no target-specific primitive name is hardcoded.
"""
from __future__ import annotations
import hashlib,json
from tukuyo_v944.gap import classify,shaobj
COMM={'ADD','MUL','MAX','MIN'}
BASE=(('A',),('B',),('CONST',-1),('CONST',0),('CONST',1))
# The proposer grammar is deliberately smaller than the evaluator's known class.
# This bounds combinatorics while still allowing genuinely composed representations.
BIN=('ADD','SUB','MUL')
UN=('ABS','NEG')

def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def complexity(e):return 1 if e[0] in ('A','B','CONST') else 1+sum(complexity(x) for x in e[1:] if isinstance(x,tuple))
def render(e):
 op=e[0]
 if op=='A':return 'a'
 if op=='B':return 'b'
 if op=='CONST':return str(e[1])
 if op=='ABS':return f'abs({render(e[1])})'
 if op=='NEG':return f'(-{render(e[1])})'
 s={'ADD':'+','SUB':'-','MUL':'*','MAX':'max','MIN':'min'}[op]
 if op in ('MAX','MIN'):return f'{s}({render(e[1])},{render(e[2])})'
 return f'({render(e[1])}{s}{render(e[2])})'
def evaluate(e,a,b):
 op=e[0]
 if op=='A':return a
 if op=='B':return b
 if op=='CONST':return e[1]
 if op=='ABS':return abs(evaluate(e[1],a,b))
 if op=='NEG':return -evaluate(e[1],a,b)
 x,y=evaluate(e[1],a,b),evaluate(e[2],a,b)
 if op=='ADD':return x+y
 if op=='SUB':return x-y
 if op=='MUL':return x*y
 if op=='MAX':return max(x,y)
 if op=='MIN':return min(x,y)
 raise ValueError('BAD_AST')
def normalize(e):
 if e[0] in COMM and render(e[1])>render(e[2]):return (e[0],e[2],e[1])
 return e

def enumerate_exprs(max_nodes=7,semantic_rows=None,limit=12000):
 by={};seen_sig={};seen_text=set();out=[]
 def add(e):
  e=normalize(e);c=complexity(e)
  if c>max_nodes:return False
  key=render(e)
  if key in seen_text:return False
  if semantic_rows:
   try:sig=tuple(evaluate(e,r['a'],r['b']) for r in semantic_rows)
   except (OverflowError,ValueError):return False
   if any(abs(v)>10**9 for v in sig):return False
   if sig in seen_sig:return False
   seen_sig[sig]=key
  seen_text.add(key);by.setdefault(c,[]).append(e);out.append(e)
  return len(out)>=limit
 for e in BASE:
  if add(e):return out
 for nodes in range(2,max_nodes+1):
  subn=nodes-1
  for x in list(by.get(subn,())):
   for op in UN:
    if add((op,x)):return out
  for l in range(1,nodes-1):
   r=nodes-1-l
   for x in list(by.get(l,())):
    for y in list(by.get(r,())):
     for op in BIN:
      if add((op,x,y)):return out
 return out

def propose(rows,gap_evidence,max_nodes=7):
 gap=classify(rows,gap_evidence)
 if gap['state']!='REPRESENTATION_INSUFFICIENT':raise ValueError('REPRESENTATION_GAP_REQUIRED:'+gap['state'])
 exprs=enumerate_exprs(max_nodes=max_nodes,semantic_rows=rows)
 known={'(a+b)','(a*b)','(a-b)','max(a,b)','min(a,b)'}
 scored=[]
 for e in exprs:
  text=render(e)
  if text in known:continue
  wrong=sum(evaluate(e,r['a'],r['b'])!=r['expected'] for r in rows)
  scored.append((wrong,complexity(e),text,e))
 if not scored:raise ValueError('NO_CANDIDATES')
 scored.sort(key=lambda x:(x[0],x[1],x[2]))
 best=scored[0]; baseline=gap['best_wrong']
 if best[0]>=baseline:raise ValueError('NO_IMPROVING_REPRESENTATION')
 tied=[x for x in scored if x[:2]==best[:2]]
 ast=json.loads(json.dumps(best[3]))
 proposal={'schema':'tukuyo.v945.primitive_proposal/1','training_rows_sha256':shaobj(rows),'gap_evidence_sha256':shaobj(gap_evidence),
           'ast':ast,'expression':best[2],'complexity':best[1],'training_wrong':best[0],'baseline_wrong':baseline,
           'candidate_count':len(scored),'equal_score_complexity_count':len(tied),'selection_rule':'wrong,complexity,lexical'}
 proposal['candidate_sha256']=shaobj({k:v for k,v in proposal.items() if k!='candidate_sha256'})
 return proposal

def eval_proposal(proposal,a,b):
 if proposal.get('schema')!='tukuyo.v945.primitive_proposal/1':raise ValueError('PROPOSAL_SCHEMA')
 body={k:v for k,v in proposal.items() if k!='candidate_sha256'}
 if proposal.get('candidate_sha256')!=shaobj(body):raise ValueError('CANDIDATE_HASH')
 def tup(x):return tuple(tup(i) if isinstance(i,list) else i for i in x)
 return evaluate(tup(proposal['ast']),a,b)
