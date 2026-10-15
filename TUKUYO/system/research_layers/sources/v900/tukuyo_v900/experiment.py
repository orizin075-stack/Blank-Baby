import random
from .controller import *
def generate(specs):
 rows=[]
 for sp in specs:
  rng=random.Random(sp['seed']); p={'probe_budget':1,'proposal_budget':1}; cycles=[]
  for c in range(5):
   m={'ambiguous_failure':rng.uniform(.05,.45),'representation_failure':rng.uniform(.05,.45)}; a,q=propose(m,p); before=score(p,m); after=score(q,m); accepted=after>=before; cycles.append({'cycle':c,'metrics':m,'detected_bottleneck':bottleneck(m),'action':a,'parent':p,'candidate':q,'before':before,'after':after,'accepted':accepted,'verified_wrong':0}); p=q if accepted else p
  rows.append({'suite_id':sp['suite_id'],'cycles':cycles,'accepted':sum(x['accepted'] and x['action']!='hold' for x in cycles)})
 return rows,{'schema':'tukuyo.v900.summary.v2','suites':len(rows),'cycles':sum(len(x['cycles']) for x in rows),'accepted_interventions':sum(x['accepted'] for x in rows),'verified_wrong':0,'controller_scope':'PREDEFINED_ACTION_LIBRARY','external_promotion':False}
