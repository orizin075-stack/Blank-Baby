import random
from .transfer import *
def generate(specs):
 rows=[]; suites=[]
 for sp in specs:
  rng=random.Random(sp['seed']); rr=[]
  for ep in range(sp['episodes']):
   k=rng.randrange(2,7); learned=infer_k(source_examples(k)); d=rng.choice(['sequence_sum','event_count','state_terminal'])
   if d=='sequence_sum': x=[rng.randrange(-5,6) for _ in range(5)]
   elif d=='event_count': x=[bool(rng.randrange(2)) for _ in range(9)]
   else:x=[rng.randrange(-9,10) for _ in range(6)]
   y=apply(d,k,x); pred=apply(d,learned,x) if learned else None; ok=pred==y
   row={'suite_id':sp['suite_id'],'episode':ep,'k_learned_on_scalar':learned,'target_domain':d,'verified':ok,'retrained_on_target_domain':False};rows.append(row);rr.append(row)
  suites.append({'suite_id':sp['suite_id'],'verified':sum(x['verified'] for x in rr),'n':len(rr)})
 return rows,suites,{'schema':'tukuyo.v896.summary.v1','episodes':len(rows),'verified':sum(x['verified'] for x in rows),'coverage':sum(x['verified'] for x in rows)/len(rows),'target_domain_retraining':False,'scope':'SAME_OPERATOR_RECOMPOSED_WITH_HUMAN_DEFINED_DOMAIN_ADAPTERS'}
