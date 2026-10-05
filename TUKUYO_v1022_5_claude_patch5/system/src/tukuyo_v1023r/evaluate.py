"""Held-out evaluation for the V1023r research preview (claude-patch5).

Worlds are drawn from a key and seeds that were never used while the agent was
developed (development used key 'devkey' and seeds 1000-1013).  Every policy
lives in exactly the same worlds.
"""
from __future__ import annotations
import collections,hashlib,json,time
from .worlds import DeviceWorld
from .ecology import run_episode,POLICIES,REGIMES

KEY='v1023r-heldout-2026-10-05'
def compare(start=50000,seeds=10,key=KEY):
    t=time.time();rows=[];agg=collections.defaultdict(collections.Counter)
    for reg,econ in REGIMES.items():
        for s in range(start,start+seeds):
            for tier in (1,2,3,4):
                for noise in (0.0,0.05,0.1):
                    for pol in POLICIES:
                        r=run_episode(DeviceWorld(key,s,tier,noise),pol,econ=econ,seed=s)
                        c=agg[f'{reg}|{pol}|{tier}'];c['n']+=1;c['alive']+=int(r['alive']);c['energy']+=r['final_energy'];c['ledger_violations']+=int(not r['ledger_conserved'])
                        for k in ('law_claimed','law_correct','wrong_law_claimed','unexplained'):c[k]+=int(bool(r.get(k)))
                        c['claim_bound_violations']+=int(r.get('claim_bound_held') is False);c['experiments']+=r['actions']['probe']+r['actions']['trial']
                        rows.append({'regime':reg,'policy':pol,'seed':s,'tier':tier,'noise':noise,**{k:r.get(k) for k in ('alive','final_energy','law_claimed','law_correct','wrong_law_claimed','unexplained','status','method')}})
                        # Second visit to the same world: with the confirmed law remembered vs starting blank.
                        if pol=='research' and r.get('law_claimed'):
                            for mem in (True,False):
                                r2=run_episode(DeviceWorld(key,s,tier,noise,stream='visit2'),'research',econ=econ,seed=s+7,prior_claim=r['claim'] if mem else None)
                                c2=agg[f'{reg}|second_visit_{"remembered" if mem else "blank"}|{tier}'];c2['n']+=1;c2['alive']+=int(r2['alive']);c2['energy']+=r2['final_energy']
                                c2['wrong_law_claimed']+=int(bool(r2.get('wrong_law_claimed')));c2['law_claimed']+=int(bool(r2.get('law_claimed')));c2['law_correct']+=int(bool(r2.get('law_correct')))
                                c2['refuted']+=int('REFUTED' in r2.get('events',[]));c2['experiments']+=r2['actions']['probe']+r2['actions']['trial']
    summary={}
    for k,c in sorted(agg.items()):
        n=c['n'];summary[k]={'n':n,'alive':c['alive'],'mean_final_energy':round(c['energy']/n,2),'mean_experiments':round(c['experiments']/n,2),
            **{x:c[x] for x in ('law_claimed','law_correct','wrong_law_claimed','unexplained','claim_bound_violations','ledger_violations','refuted') if x in c or x!='refuted'}}
    out={'schema':'tukuyo.v1023r.heldout_eval/1','key_sha256':hashlib.sha256(key.encode()).hexdigest(),'seeds':[start,start+seeds-1],
         'econ':REGIMES,'policies':list(POLICIES),'summary':summary,'episodes':rows,'seconds':round(time.time()-t,1)}
    out['result_sha256']=hashlib.sha256(json.dumps({k:v for k,v in out.items() if k!='seconds'},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return out
