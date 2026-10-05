import random
from .dsl import *
from .agent import *
CFG={'scalar':([-5],[-5,-3,-1,0,1,2,4,6],[-8,-6,-4,-2,3,5,7,8]),'sequence':([(-3,-1,2)],[(-3,-1,2),(0,0,1),(4,-2,1,0),(-1,-1,-1),(2,3,4),(5,),(-5,5),(1,0,-1,2,-2)],[(3,3,-2,-2,1),(4,0,-4),(1,2,3,4)])}
def generate(specs):
 rows=[]; suites=[]
 for sp in specs:
  rng=random.Random(sp['seed']); rr=[]
  for d in ('scalar','sequence'):
   init,pool,hold=CFG[d]
   for ep in range(sp['episodes_per_domain']):
    t=rng.choice(composed_programs(d)); obs=[(x,run(t,x)) for x in init]; tr=[]
    for k in range(sp['max_active_probes']):
     if resolve_vs(d,obs) is not None: break
     q=choose_probe(d,obs,pool)
     if q is None: break
     bef=len(version_space(d,obs)); y=run(t,q); obs.append((q,y)); tr.append({'query':q,'answer':y,'before':bef,'after':len(version_space(d,obs))})
    c=resolve_vs(d,obs); ok=c is not None and valid(c,t,hold); wrong=c is not None and not ok
    nobs=len(obs); po=[(x,run(t,x)) for x in pool[:nobs]]; pc=resolve_vs(d,po); pok=pc is not None and valid(pc,t,hold)
    row={'suite_id':sp['suite_id'],'domain':d,'episode':ep,'active_verified':ok,'verified_wrong':int(wrong),'abstain':c is None,'passive_verified_same_budget':pok,'probe_count':len(tr),'transcript':tr}; rows.append(row); rr.append(row)
  suites.append({'suite_id':sp['suite_id'],'active_verified':sum(x['active_verified'] for x in rr),'passive_verified_same_budget':sum(x['passive_verified_same_budget'] for x in rr),'verified_wrong':sum(x['verified_wrong'] for x in rr),'n':len(rr)})
 return rows,suites,{'schema':'tukuyo.v892.summary.v2','episodes':len(rows),'active_verified':sum(x['active_verified'] for x in rows),'passive_verified_same_budget':sum(x['passive_verified_same_budget'] for x in rows),'verified_wrong':sum(x['verified_wrong'] for x in rows),'strict_gain_suites':sum(x['active_verified']>x['passive_verified_same_budget'] for x in suites),'mean_probe_count':sum(x['probe_count'] for x in rows)/len(rows)}
