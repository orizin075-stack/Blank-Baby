import random
from .dsl import *
SP={'scalar':([-5,-3,-1,0],[-8,-6,-4,-2,1,2,3,4,5,6,7,8]),'sequence':([(-3,-1,2),(0,0,1),(4,-2,1,0)],[(-1,-1,-1),(2,3,4),(5,),(-5,5),(1,0,-1,2,-2),(3,3,-2,-2,1)])}
def nearest_base(d,obs): return min(base_programs(d),key=lambda p:(sum(abs(run(p,x)-y) for x,y in obs),repr(p)))
def generate(specs):
 rows=[]; suites=[]
 for sp in specs:
  rng=random.Random(sp['seed']); rr=[]
  for d in ('scalar','sequence'):
   probes,hold=SP[d]; targets=composed_programs(d)
   for ep in range(sp['episodes_per_domain']):
    t=rng.choice(targets); obs=[(x,run(t,x)) for x in probes]; c=resolve(d,obs); b=nearest_base(d,obs)
    ok=c is not None and valid(c,t,hold); wrong=c is not None and not ok; bok=all(run(b,x)==run(t,x) for x in hold)
    row={'suite_id':sp['suite_id'],'domain':d,'episode':ep,'target_program':t,'target_in_base_candidates':t in base_programs(d),'composition_match_count':len(matches(d,obs)),'synth_program':c,'synth_verified':ok,'synth_abstain':c is None,'verified_wrong':int(wrong),'baseline_program':b,'baseline_verified':bok}; rows.append(row); rr.append(row)
  suites.append({'suite_id':sp['suite_id'],'n':len(rr),'synth_verified':sum(x['synth_verified'] for x in rr),'baseline_verified':sum(x['baseline_verified'] for x in rr),'abstain':sum(x['synth_abstain'] for x in rr),'verified_wrong':sum(x['verified_wrong'] for x in rr),'candidate_absent_all':all(not x['target_in_base_candidates'] for x in rr)})
 return rows,suites,{'schema':'tukuyo.v891.summary.v2','episodes':len(rows),'synth_verified':sum(x['synth_verified'] for x in rows),'baseline_verified':sum(x['baseline_verified'] for x in rows),'abstain':sum(x['synth_abstain'] for x in rows),'verified_wrong':sum(x['verified_wrong'] for x in rows),'strict_gain_suites':sum(x['synth_verified']>x['baseline_verified'] for x in suites),'candidate_absent_all':all(x['candidate_absent_all'] for x in suites)}
