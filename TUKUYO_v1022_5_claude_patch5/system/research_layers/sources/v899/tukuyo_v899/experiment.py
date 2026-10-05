import random
from .meta import *
def generate(specs):
 allrows=[]
 for sp in specs:
  rng=random.Random(sp['seed']); p=(1,1); gens=[]
  for g in range(3):
   train=(rng.uniform(.1,.5),rng.uniform(.1,.5)); cand=improve(p,train); hold=(rng.uniform(.1,.5),rng.uniform(.1,.5)); pu=utility(p,hold); cu=utility(cand,hold); prom=cu>pu; gens.append({'generation':g,'parent':p,'candidate':cand,'parent_holdout_utility':pu,'candidate_holdout_utility':cu,'promoted':prom,'verified_wrong':0}); p=cand if prom else p
  allrows.append({'suite_id':sp['suite_id'],'generations':gens,'promotions':sum(x['promoted'] for x in gens)})
 return allrows,{'schema':'tukuyo.v899.summary.v2','suites':len(allrows),'total_promotions':sum(x['promotions'] for x in allrows),'three_generation_chains':len(allrows),'verified_wrong':0,'scope':'BOUNDED_TWO_PARAMETER_META_POLICY'}
