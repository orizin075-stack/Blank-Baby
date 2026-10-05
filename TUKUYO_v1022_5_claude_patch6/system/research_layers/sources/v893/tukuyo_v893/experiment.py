import random
from .dsl import *
from .gap import classify
OUT={'mod2':lambda x:x%2,'mod3':lambda x:x%3,'floordiv2':lambda x:x//2,'sign':lambda x:(x>0)-(x<0)}; DIAG=list(range(-8,9))
def generate(specs):
 rows=[]; suites=[]; reps=composed_programs('scalar')
 for sp in specs:
  rng=random.Random(sp['seed']); rr=[]
  for ep in range(sp['episodes']):
   if ep%2==0:t=rng.choice(reps);f=lambda x,t=t:run(t,x);truth='SEARCH_INSUFFICIENT_FOR_BASE_ONLY_SEARCH';name=repr(t)
   else:name=rng.choice(list(OUT));f=OUT[name];truth='REPRESENTATION_INSUFFICIENT_WITHIN_DEPTH2_DSL'
   obs=[(x,f(x)) for x in DIAG]; pred=classify('scalar',obs); ok=pred['label']==truth; row={'suite_id':sp['suite_id'],'episode':ep,'truth':truth,'prediction':pred['label'],'correct':ok,'target':name};rows.append(row);rr.append(row)
  suites.append({'suite_id':sp['suite_id'],'n':len(rr),'correct':sum(x['correct'] for x in rr),'wrong':sum(not x['correct'] for x in rr)})
 return rows,suites,{'schema':'tukuyo.v893.summary.v2','episodes':len(rows),'correct':sum(x['correct'] for x in rows),'wrong':sum(not x['correct'] for x in rows),'all_suites_perfect':all(x['wrong']==0 for x in suites),'scope':'FINITE_DEPTH2_DSL_DIAGNOSTIC_GRID'}
