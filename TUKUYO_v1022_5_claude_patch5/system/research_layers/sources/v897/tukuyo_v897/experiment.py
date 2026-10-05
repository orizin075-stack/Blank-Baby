import random
from .loop import *
KINDS=['direct','compose','ambiguous','outside']
def generate(specs):
 rows=[]; suites=[]
 for sp in specs:
  rng=random.Random(sp['seed']); rr=[]
  for ep in range(sp['episodes']):
   c={'kind':rng.choice(KINDS)}; n=route(c); o=old_route(c); row={'suite_id':sp['suite_id'],'episode':ep,'kind':c['kind'],'new_action':n,'old_action':o,'new_success':success(n,c),'old_success':success(o,c)};rows.append(row);rr.append(row)
  suites.append({'suite_id':sp['suite_id'],'new_success':sum(x['new_success'] for x in rr),'old_success':sum(x['old_success'] for x in rr),'n':len(rr)})
 return rows,suites,{'schema':'tukuyo.v897.summary.v1','episodes':len(rows),'new_success':sum(x['new_success'] for x in rows),'old_success':sum(x['old_success'] for x in rows),'strict_gain_suites':sum(x['new_success']>x['old_success'] for x in suites),'scope':'BOUNDED_SYNTHETIC_RESEARCH_ROUTING_HARNESS'}
