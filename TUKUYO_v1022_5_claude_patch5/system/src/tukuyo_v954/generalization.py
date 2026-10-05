from __future__ import annotations
import hashlib,json
from functools import lru_cache
from tukuyo_v950.improver import config0,benchmark

def mixed_tasks(inputs):
 fs={
  'poly_product_shift':lambda a,b:a*b+a-b,
  'poly_square_plus':lambda a,b:a*a+b,
  'poly_cubeish':lambda a,b:a*b*b,
  'piecewise_max_product':lambda a,b:max(a,b)+a*b,
  'piecewise_min_triple':lambda a,b:min(a,b)*3,
  'absolute_gap':lambda a,b:abs(a-b),
  'absolute_plus':lambda a,b:abs(a)+b,
 }
 return {k:tuple(f(a,b) for a,b in inputs) for k,f in fs.items()}

def _cfgkey(cfg): return (tuple(cfg['binops']),tuple(cfg['unary']),tuple(cfg['constants']),int(cfg['max_nodes']))
@lru_cache(maxsize=64)
def _bench_cached(key,inputs):
 from tukuyo_v950.improver import _enumerate,render
 cfg={'binops':key[0],'unary':key[1],'constants':key[2],'max_nodes':key[3]}
 targets=mixed_tasks(inputs);exprs=_enumerate(cfg,inputs);found={}
 for idx,(e,sig) in enumerate(exprs,1):
  for name,t in targets.items():
   if name not in found and sig==t:found[name]={'at':idx,'expression':render(e)}
 effort=max((v['at'] for v in found.values()),default=len(exprs)+1)
 return {'success':len(found)==len(targets),'task_count':len(targets),'solved':len(found),'effort':effort,'generated':len(exprs),'found':found}

def _bench(cfg,inputs):
 return _bench_cached(_cfgkey(cfg),tuple(inputs))

def candidate_edits(cfg):
 out=[]
 # deletions retained as adversarial candidates
 if 'MAX' in cfg['binops'] or 'MIN' in cfg['binops']:
  x=dict(cfg);x['binops']=tuple(o for o in cfg['binops'] if o not in ('MAX','MIN'));out.append(('remove_minmax',x))
 if cfg['unary']:
  x=dict(cfg);x['unary']=();out.append(('remove_unary',x))
 # non-deletion edits: ordering and bounded search budget / node policy
 x=dict(cfg);x['binops']=('MUL','ADD','SUB','MAX','MIN');out.append(('priority_mul_add_sub',x))
 x=dict(cfg);x['binops']=('MAX','MIN','MUL','ADD','SUB');out.append(('priority_piecewise_first',x))
 x=dict(cfg);x['constants']=(0,1,-1,2,-2);out.append(('priority_small_constants',x))
 return out

def authority_evaluate(parent,candidate,train_inputs,unseen_inputs):
 ptrain=_bench(parent,train_inputs);ctrain=_bench(candidate,train_inputs);pun=_bench(parent,unseen_inputs);cun=_bench(candidate,unseen_inputs)
 families=sorted(mixed_tasks(unseen_inputs))
 retention={f:{'parent':int(f in pun['found']),'candidate':int(f in cun['found'])} for f in families}
 no_regression=all(v['candidate']>=v['parent'] for v in retention.values())
 improves=(cun['solved']>pun['solved']) or (cun['solved']==pun['solved'] and cun['effort']<pun['effort'])
 return {'promote':bool(no_regression and improves),'parent_unseen':pun,'candidate_unseen':cun,'parent_train':ptrain,'candidate_train':ctrain,'retention':retention,'no_family_regression':no_regression,'strict_improvement':improves}

def propose_generalizing(parent=None):
 parent=parent or config0();train=tuple((i-6,((i*7+2)%11)-5) for i in range(18));unseen=tuple((i-11,((i*11+5)%19)-9) for i in range(26))
 rows=[]
 for name,cfg in candidate_edits(parent):
  ev=authority_evaluate(parent,cfg,train,unseen);rows.append({'edit':name,'config':cfg,'evaluation':ev})
 passing=[r for r in rows if r['evaluation']['promote']]
 if not passing:return {'promoted':False,'parent':parent,'candidates':rows}
 passing.sort(key=lambda r:(-r['evaluation']['candidate_unseen']['solved'],r['evaluation']['candidate_unseen']['effort'],r['edit']))
 best=passing[0]
 return {'promoted':True,'edit':best['edit'],'next_config':best['config'],'evaluation':best['evaluation'],'candidates':rows,'scope':'FROZEN_MIXED_UNSEEN_TASK_FAMILY'}
