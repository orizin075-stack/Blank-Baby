import random
from .meta import *
def generate(specs):
 rows=[]
 for sp in specs:
  rng=random.Random(sp['seed']); train=[rng.choice(['direct','compose','ambiguous','outside']) for _ in range(200)]; hold=[rng.choice(['direct','compose','ambiguous','outside']) for _ in range(200)]; p=propose(train); baseline={'probe_budget':1,'proposal_budget':1}; rows.append({'suite_id':sp['suite_id'],'candidate':p,'candidate_holdout_utility':utility(p,hold),'baseline_holdout_utility':utility(baseline,hold),'strict_gain':utility(p,hold)>utility(baseline,hold),'training_seed':sp['seed'],'holdout_seed_derived':sp['seed']})
 return rows,{'schema':'tukuyo.v898.summary.v1','suites':len(rows),'strict_gain_suites':sum(x['strict_gain'] for x in rows),'scope':'BOUNDED_POLICY_GRID_SEARCH','self_generated_code':False}
