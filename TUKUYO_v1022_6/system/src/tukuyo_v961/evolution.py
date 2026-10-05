"""v961 bounded evolution-of-evolution assay.
Compares research/search policies on a frozen unseen mixed-family suite under identical enumeration limits.
No code self-rewrite or general L6 claim.
"""
from __future__ import annotations
from tukuyo_v950.improver import config0,_enumerate,render

def frozen_suite(inputs):
    fs={
      'poly_composite':('polynomial',lambda a,b:a*b+a-b),
      'square_linear':('polynomial',lambda a,b:a*a+b),
      'higher_product':('polynomial',lambda a,b:a*b*b),
      'maximum':('piecewise',lambda a,b:max(a,b)),
      'minimum':('piecewise',lambda a,b:min(a,b)),
      'abs_difference':('absolute',lambda a,b:abs(a-b)),
      'abs_linear':('absolute',lambda a,b:abs(a)+b),
    }
    return {k:{'family':fam,'target':tuple(f(a,b) for a,b in inputs)} for k,(fam,f) in fs.items()}

def _cfg(name):
    b=config0()
    if name=='BASE': return b
    if name=='MUL_FIRST': return {**b,'binops':('MUL','ADD','SUB','MAX','MIN')}
    if name=='PIECEWISE_FIRST': return {**b,'binops':('MAX','MIN','MUL','ADD','SUB')}
    raise ValueError('UNKNOWN_POLICY_CONFIG')

def benchmark_policy(policy,inputs=None,cap=30000):
    inputs=inputs or tuple((i-8,((i*7+3)%13)-6) for i in range(20))
    suite=frozen_suite(inputs)
    family_cfg=policy.get('family_config',{})
    if set(family_cfg)!={'polynomial','piecewise','absolute'}: raise ValueError('POLICY_SCHEMA')
    # Same task suite, same cap; only search ordering changes by task family.
    cache={}; found={}; family_stats={}
    for family in ('polynomial','piecewise','absolute'):
        cfgname=family_cfg[family]
        cfg=_cfg(cfgname)
        exprs=_enumerate(cfg,inputs,cap=cap); cache[family]=(cfgname,exprs)
        family_stats[family]={'config':cfgname,'generated':len(exprs),'solved':0,'effort':0}
    for name,entry in suite.items():
        family=entry['family']; target=entry['target']; exprs=cache[family][1]; hit=None
        for idx,(e,sig) in enumerate(exprs,1):
            if sig==target:
                hit={'at':idx,'expression':render(e)}; break
        if hit:
            found[name]=hit; family_stats[family]['solved']+=1; family_stats[family]['effort']=max(family_stats[family]['effort'],hit['at'])
        else:
            family_stats[family]['effort']=len(exprs)+1
    solved=len(found); total=len(suite); effort=sum(x['effort'] for x in family_stats.values())
    return {'success':solved==total,'solved':solved,'task_count':total,'aggregate_family_effort':effort,'family_stats':family_stats,'found':found,'cap':cap}

def parent_policy(): return {'policy_id':'I_PARENT','family_config':{'polynomial':'BASE','piecewise':'BASE','absolute':'BASE'}}
def candidate_policy(): return {'policy_id':'I_CANDIDATE','family_config':{'polynomial':'MUL_FIRST','piecewise':'PIECEWISE_FIRST','absolute':'BASE'}}

def compare(parent=None,candidate=None):
    parent=parent or parent_policy(); candidate=candidate or candidate_policy()
    p=benchmark_policy(parent); c=benchmark_policy(candidate)
    regressions=[]
    for fam in p['family_stats']:
        if c['family_stats'][fam]['solved']<p['family_stats'][fam]['solved']: regressions.append(fam+':SOLVED')
        if c['family_stats'][fam]['effort']>p['family_stats'][fam]['effort']: regressions.append(fam+':EFFORT')
    promote=bool(c['success'] and p['success'] and not regressions and c['aggregate_family_effort']<p['aggregate_family_effort'])
    return {'schema':'tukuyo.v961.improver_comparison/1','parent':p,'candidate':c,'family_regressions':regressions,'decision':'PROMOTE_BOUNDED_META_POLICY' if promote else 'REJECT','same_compute_cap':True,'frozen_unseen_suite':True,'code_self_rewrite':False,'general_l6':False}
