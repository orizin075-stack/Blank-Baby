from __future__ import annotations
from collections import deque
from .deps import activate
activate()
import tukuyo_v846.evolution as ev

OPS=ev.OPS

def apply_op(parent,op):
 p=ev.normalize_genome(parent)
 if op=='identity':c=p
 elif op=='wrap_abs':c={'op':'abs','arg':p}
 elif op=='add_plus1':c={'op':'add','left':p,'right':{'op':'const','value':1}}
 elif op=='add_minus1':c={'op':'add','left':p,'right':{'op':'const','value':-1}}
 elif op=='mul2':c={'op':'mul','left':p,'right':{'op':'const','value':2}}
 elif op=='negate':c={'op':'neg','arg':p}
 elif op=='add_var':c={'op':'add','left':p,'right':{'op':'x'}}
 elif op=='prune':
  if p['op'] in ('abs','neg'):c=p['arg']
  elif p['op'] in ('add','sub','mul','max','min'):c=p['left']
  else:c=p
 else:raise ValueError(op)
 try:return ev.normalize_genome(c)
 except Exception:return p

def discovery_depth(founders,cases,max_depth=6):
 target=len(cases);seen={};q=deque()
 for name,g in founders.items():
  g=ev.normalize_genome(g);h=ev.genome_sha(g)
  if h not in seen:seen[h]=0;q.append((g,0,name,[]))
 successes=[];by_budget={1:False,2:False,4:False}
 while q:
  g,d,origin,path=q.popleft();score=ev.score_genome(g,cases)['correct']
  if score==target:successes.append({'depth':d,'origin':origin,'path':path,'genome':g,'genome_sha256':ev.genome_sha(g)})
  if d>=max_depth:continue
  for op in OPS:
   c=apply_op(g,op);h=ev.genome_sha(c);nd=d+1
   if h in seen and seen[h]<=nd:continue
   seen[h]=nd;q.append((c,nd,origin,path+[op]))
 if not successes:return {'shortest_mutation_depth':None,'success_count':0,'unique_states':len(seen),'success_rate_at_budget_1':0.0,'success_rate_at_budget_2':0.0,'success_rate_at_budget_4':0.0}
 depths=sorted(x['depth'] for x in successes);n=len(depths)
 def qtile(p):return depths[min(n-1,max(0,int((n-1)*p+0.999999)))]
 shortest=depths[0]
 for b in by_budget:by_budget[b]=any(d<=b for d in depths)
 return {'shortest_mutation_depth':shortest,'median_success_depth':qtile(.5),'p90_success_depth':qtile(.9),'success_count':n,'unique_states':len(seen),'success_rate_at_budget_1':1.0 if by_budget[1] else 0.0,'success_rate_at_budget_2':1.0 if by_budget[2] else 0.0,'success_rate_at_budget_4':1.0 if by_budget[4] else 0.0,'shortest_examples':[x for x in successes if x['depth']==shortest][:8]}
