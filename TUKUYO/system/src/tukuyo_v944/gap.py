"""v944 hypothesis-class gap detection.

Fail-closed classifier. A poor fit alone never means representation insufficiency.
The evidence must show enough data, complete bounded search under multiple seeds and
strategies, and persistent residuals after all known hypotheses were evaluated.
"""
from __future__ import annotations
import hashlib,json,random
OPS={
 'ADD':lambda a,b:a+b,'MUL':lambda a,b:a*b,'SUB':lambda a,b:a-b,
 'MAX':max,'MIN':min,
}
REQUIRED_STRATEGIES=('exhaustive','reverse','shuffled')
REQUIRED_SEEDS=(11,23,47)

def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def shaobj(x):return hashlib.sha256(canon(x)).hexdigest()
def _validate_rows(rows):
 if not isinstance(rows,list):raise ValueError('ROWS_NOT_LIST')
 out=[]
 for i,r in enumerate(rows):
  if not isinstance(r,dict) or set(r)!={'a','b','expected'}:raise ValueError('ROW_SCHEMA:'+str(i))
  if any(type(r[k]) is not int or abs(r[k])>10_000 for k in r):raise ValueError('ROW_VALUE:'+str(i))
  out.append(dict(r))
 return out

def score(rows,op):
 f=OPS[op]; wrong=[]
 for i,r in enumerate(rows):
  got=f(r['a'],r['b'])
  if got!=r['expected']:wrong.append({'i':i,'a':r['a'],'b':r['b'],'expected':r['expected'],'got':got})
 return {'operator':op,'correct':len(rows)-len(wrong),'wrong':len(wrong),'residual_sha256':shaobj(wrong)}

def search_evidence(rows,seeds=REQUIRED_SEEDS,strategies=REQUIRED_STRATEGIES,budget=None):
 rows=_validate_rows(rows);budget=len(OPS) if budget is None else int(budget)
 reports=[]
 for strategy in strategies:
  for seed in seeds:
   order=list(OPS)
   if strategy=='reverse':order=list(reversed(order))
   elif strategy=='shuffled':random.Random(seed).shuffle(order)
   elif strategy!='exhaustive':raise ValueError('UNKNOWN_STRATEGY')
   evaluated=[score(rows,o) for o in order[:max(0,budget)]]
   best_wrong=min((x['wrong'] for x in evaluated),default=None)
   best=sorted(x['operator'] for x in evaluated if x['wrong']==best_wrong) if best_wrong is not None else []
   residuals=sorted(x['residual_sha256'] for x in evaluated if x['wrong']==best_wrong)
   reports.append({'schema':'tukuyo.v944.search_run/1','strategy':strategy,'seed':seed,'budget':budget,
                   'budget_exhausted':budget>=len(OPS),'evaluated':evaluated,'best_wrong':best_wrong,
                   'best_operators':best,'best_residual_sha256':shaobj(residuals)})
 return {'schema':'tukuyo.v944.search_evidence/1','rows_sha256':shaobj(rows),'row_count':len(rows),'runs':reports}

def _coverage(rows):
 # crude but explicit support check: signs and zero/nonzero combinations must not collapse to one tiny region
 pairs={(0 if r['a']==0 else 1 if r['a']>0 else -1,0 if r['b']==0 else 1 if r['b']>0 else -1) for r in rows}
 distinct=len({(r['a'],r['b']) for r in rows})
 return {'sign_buckets':len(pairs),'distinct_inputs':distinct}

def classify(rows,evidence):
 rows=_validate_rows(rows)
 if evidence.get('schema')!='tukuyo.v944.search_evidence/1' or evidence.get('rows_sha256')!=shaobj(rows) or evidence.get('row_count')!=len(rows):
  raise ValueError('EVIDENCE_BINDING')
 cov=_coverage(rows)
 if len(rows)<12 or cov['distinct_inputs']<10 or cov['sign_buckets']<4:
  return {'state':'DATA_INSUFFICIENT','coverage':cov,'reason':'minimum support not met'}
 runs=evidence.get('runs')
 if not isinstance(runs,list):raise ValueError('RUNS_SCHEMA')
 by={(x.get('strategy'),x.get('seed')):x for x in runs if isinstance(x,dict)}
 required={(s,n) for s in REQUIRED_STRATEGIES for n in REQUIRED_SEEDS}
 if set(by)!=required:
  return {'state':'SEARCH_INSUFFICIENT','coverage':cov,'reason':'required strategy/seed matrix incomplete'}
 recomputed=search_evidence(rows)['runs']; expected={(x['strategy'],x['seed']):x for x in recomputed}
 for k in required:
  if by[k]!=expected[k]:raise ValueError('SEARCH_EVIDENCE_NOT_RECOMPUTABLE:'+str(k))
 if not all(x['budget_exhausted'] and x['budget']>=len(OPS) for x in runs):
  return {'state':'SEARCH_INSUFFICIENT','coverage':cov,'reason':'known hypothesis budget not exhausted'}
 sig={(tuple(x['best_operators']),x['best_wrong'],x['best_residual_sha256']) for x in runs}
 if len(sig)!=1: return {'state':'SEARCH_INSUFFICIENT','coverage':cov,'reason':'residual not stable across searches'}
 best_ops=next(iter(sig))[0]; best_wrong=next(iter(sig))[1]
 if best_wrong==0 and len(best_ops)==1:
  return {'state':'RESOLVED_IN_CLASS','coverage':cov,'best_operator':best_ops[0],'wrong':0}
 if best_wrong==0 and len(best_ops)>1:
  return {'state':'HYPOTHESIS_AMBIGUOUS','coverage':cov,'best_operators':list(best_ops),'wrong':0}
 return {'state':'REPRESENTATION_INSUFFICIENT','coverage':cov,'best_operators':list(best_ops),'best_wrong':best_wrong,
         'evidence_sha256':shaobj(evidence),'criteria':{'multiple_seeds':True,'multiple_strategies':True,'budget_exhausted':True,'residual_persistent':True}}
