"""v950 actual bounded improver comparison over a finite grammar-search policy space."""
from __future__ import annotations
from tukuyo_v945.primitive import evaluate,render,complexity

def config0():return {'binops':('ADD','SUB','MUL','MAX','MIN'),'unary':('ABS','NEG'),'constants':(-2,-1,0,1,2),'max_nodes':7}
def _norm(e):
 if e[0] in ('ADD','MUL','MAX','MIN') and render(e[1])>render(e[2]):return (e[0],e[2],e[1])
 return e
def _enumerate(cfg,inputs,cap=30000):
 base=[('A',),('B',)]+[('CONST',c) for c in cfg['constants']];by={};seen=set();texts=set();out=[]
 def add(e):
  e=_norm(e);txt=render(e);c=complexity(e)
  if c>cfg['max_nodes'] or txt in texts:return False
  sig=tuple(evaluate(e,a,b) for a,b in inputs)
  if any(abs(v)>10**9 for v in sig) or sig in seen:return False
  seen.add(sig);texts.add(txt);by.setdefault(c,[]).append(e);out.append((e,sig));return len(out)>=cap
 for e in base:
  if add(e):return out
 for nodes in range(2,cfg['max_nodes']+1):
  for x in list(by.get(nodes-1,())):
   for op in cfg['unary']:
    if add((op,x)):return out
  for l in range(1,nodes-1):
   r=nodes-1-l
   for x in list(by.get(l,())):
    for y in list(by.get(r,())):
     for op in cfg['binops']:
      if add((op,x,y)):return out
 return out

def tasks(inputs):
 fs={
 't1':lambda a,b:a*b+a-b,
 't2':lambda a,b:a*b-a+b,
 't3':lambda a,b:(a+b)*(a-b),
 't4':lambda a,b:a*b+a+b,
 }
 return {k:tuple(f(a,b) for a,b in inputs) for k,f in fs.items()}
def benchmark(cfg,inputs=None):
 inputs=inputs or tuple((i-6,((i*7+2)%11)-5) for i in range(18));targets=tasks(inputs);exprs=_enumerate(cfg,inputs);found={};
 for idx,(e,sig) in enumerate(exprs,1):
  for name,t in targets.items():
   if name not in found and sig==t:found[name]={'at':idx,'expression':render(e)}
 effort=max((v['at'] for v in found.values()),default=len(exprs)+1)
 return {'success':len(found)==len(targets),'task_count':len(targets),'solved':len(found),'effort':effort,'generated':len(exprs),'found':found,'config':{k:list(v) if isinstance(v,tuple) else v for k,v in cfg.items()}}
def neighbors(cfg):
 out=[]
 if 'MAX' in cfg['binops'] or 'MIN' in cfg['binops']:
  x=dict(cfg);x['binops']=tuple(o for o in cfg['binops'] if o not in ('MAX','MIN'));out.append(('remove_unused_minmax',x))
 if len(cfg['constants'])>3:
  x=dict(cfg);x['constants']=tuple(c for c in cfg['constants'] if c in (-1,0,1));out.append(('prune_large_constants',x))
 elif len(cfg['constants'])>1:
  x=dict(cfg);x['constants']=(0,);out.append(('prune_unused_constants',x))
 if cfg['unary']:
  x=dict(cfg);x['unary']=();out.append(('remove_unused_unary',x))
 return out
def propose_next(cfg,inputs=None):
 current=benchmark(cfg,inputs);cands=[]
 for edit,n in neighbors(cfg):
  b=benchmark(n,inputs)
  if b['success'] and current['success'] and b['effort']<current['effort']:cands.append((b['effort'],b['generated'],edit,n,b))
 if not cands:return {'improved':False,'current':current}
 cands.sort(key=lambda x:(x[0],x[1],x[2]));_,_,edit,n,b=cands[0]
 return {'improved':True,'edit':edit,'before':current,'after':b,'next_config':n}
