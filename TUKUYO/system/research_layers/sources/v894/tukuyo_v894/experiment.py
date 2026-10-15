import random
from .proposal import *
DIAG=list(range(-9,10)); HOLD=[-17,-13,-11,11,13,17,19]
def generate(specs):
 rows=[]; suites=[]
 for sp in specs:
  rng=random.Random(sp['seed']); rr=[]
  for ep in range(sp['episodes']):
   t=rng.choice(META); obs=[(x,run(t,x)) for x in DIAG]; q=propose(obs); ok=q['program'] is not None and all(run(q['program'],x)==run(t,x) for x in HOLD); wrong=q['program'] is not None and not ok
   row={'suite_id':sp['suite_id'],'episode':ep,'target':t,'proposal':q,'verified':ok,'verified_wrong':int(wrong)};rows.append(row);rr.append(row)
  suites.append({'suite_id':sp['suite_id'],'verified':sum(x['verified'] for x in rr),'wrong':sum(x['verified_wrong'] for x in rr),'n':len(rr)})
 return rows,suites,{'schema':'tukuyo.v894.summary.v1','episodes':len(rows),'verified':sum(x['verified'] for x in rows),'verified_wrong':sum(x['verified_wrong'] for x in rows),'coverage':sum(x['verified'] for x in rows)/len(rows),'proposal_space':'INACTIVE_HUMAN_DEFINED_META_GRAMMAR'}
