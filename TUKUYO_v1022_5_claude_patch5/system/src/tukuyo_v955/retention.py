from __future__ import annotations
from functools import lru_cache
from tukuyo_v950.improver import config0,_enumerate,render

FAMILIES={
 'add':lambda a,b:a+b,
 'sub':lambda a,b:a-b,
 'mul':lambda a,b:a*b,
 'square_plus':lambda a,b:a*a+b,
 'product_shift':lambda a,b:a*b+a-b,
 'max':lambda a,b:max(a,b),
 'min':lambda a,b:min(a,b),
 'abs_gap':lambda a,b:abs(a-b),
 'abs_plus':lambda a,b:abs(a)+b,
 'neg_shift':lambda a,b:-a+b,
}
DOMAINS={
 'balanced':tuple((i-7,((i*5+1)%15)-7) for i in range(20)),
 'negative_heavy':tuple((-i-1,((i*7+3)%13)-9) for i in range(18)),
 'edge_mixed':((-9,-9),(-9,8),(-4,7),(-1,9),(0,-8),(1,8),(3,-7),(7,2),(9,-4),(9,9)),
}
def _key(cfg):return (tuple(cfg['binops']),tuple(cfg['unary']),tuple(cfg['constants']),int(cfg['max_nodes']))
@lru_cache(maxsize=128)
def _matrix_cached(key):
 cfg={'binops':key[0],'unary':key[1],'constants':key[2],'max_nodes':key[3]};matrix={};total_effort=0
 for dname,inputs in DOMAINS.items():
  exprs=_enumerate(cfg,inputs);targets={f:tuple(fn(a,b) for a,b in inputs) for f,fn in FAMILIES.items()};found={}
  for idx,(e,sig) in enumerate(exprs,1):
   for fam,t in targets.items():
    if fam not in found and sig==t:found[fam]={'at':idx,'expression':render(e)}
  total_effort+=max((x['at'] for x in found.values()),default=len(exprs)+1)
  matrix[dname]={'solved':len(found),'total':len(targets),'found':found,'generated':len(exprs)}
 return {'matrix':matrix,'all_solved':all(x['solved']==x['total'] for x in matrix.values()),'aggregate_effort':total_effort}
def capability_matrix(cfg):return _matrix_cached(_key(cfg))
def retention_gate(parent,candidate):
 p=capability_matrix(parent);c=capability_matrix(candidate);reg=[]
 for d in DOMAINS:
  pf=set(p['matrix'][d]['found']);cf=set(c['matrix'][d]['found'])
  for fam in sorted(pf-cf):reg.append({'domain':d,'family':fam})
 promote=(not reg and c['aggregate_effort']<p['aggregate_effort'])
 return {'promote':promote,'regressions':reg,'parent':p,'candidate':c,'strict_effort_gain':c['aggregate_effort']<p['aggregate_effort'],'no_capability_regression':not reg}
def demo():
 p=config0();c1=dict(p);c1['binops']=tuple(x for x in p['binops'] if x not in ('MAX','MIN'))
 c2=dict(p);c2['unary']=()
 return {'remove_minmax':retention_gate(p,c1),'remove_unary':retention_gate(p,c2),'scope':'FROZEN_MULTI_DOMAIN_CAPABILITY_RETENTION'}
