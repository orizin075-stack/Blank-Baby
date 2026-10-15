from __future__ import annotations
import copy,json
from pathlib import Path
from tukuyo_v977.whole_state import canon,sha_obj,_live_identity
from tukuyo_v990.closed_environment import make_world,observation,context_class,transition,ACTIONS
from tukuyo_v991.grounded_organism import default_physiology,apply_physiology,derive_evaluation,needs,burden

SCHEMA='tukuyo.v992.holdout_assay/1'
def _write(p,o):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')
def result_path(data):return Path(data)/'v992'/'HOLDOUT_ASSAY.json'

def _run_episode(profile,seed,policy,max_steps=28):
    w=make_world(profile,seed);p=default_physiology();trace=[]
    for t in range(max_steps):
        obs=observation(w)
        if w['terminal']:break
        action=policy(obs,p,t)
        nw,o0,o1,out=transition(w,action);np=apply_physiology(p,action,out);ev=derive_evaluation(p,np,out)
        trace.append({'step':t+1,'context':context_class(o0),'action':action,'outcome':out,'evaluation':ev})
        w,p=nw,np
    n=needs(p);score=round(float(p['goal_achievement'])*2.0 + p['integrity']/100 + min(1,p['energy']/60) - burden(n),6)
    return {'profile':profile,'seed':seed,'reached_goal':bool(w['terminal']),'steps':len(trace),'final_physiology':p,'final_needs':n,'measured_score':score,'trace':trace}

def _train():
    # Empirical intervention trials: clone observed simulated states, execute one bounded action,
    # and learn from the resulting state delta. No action receives a preset reward.
    stats={}
    worlds=[make_world('TRAIN_A',99011),make_world('TRAIN_A',99012),make_world('TRAIN_B',99021),make_world('TRAIN_B',99022)]
    for w0 in worlds:
        for pos in range(w0['size']-1):
            base=copy.deepcopy(w0);base['position']=pos;base['terminal']=False;base['visited']=sorted(set(base.get('visited',[])+[pos]))
            obs=observation(base);ctx=context_class(obs)
            for energy in (28.0,60.0):
                p0=default_physiology();p0['energy']=energy
                for a in ACTIONS:
                    try:nw,o0,o1,out=transition(base,a)
                    except ValueError:continue
                    p1=apply_physiology(p0,a,out);ev=derive_evaluation(p0,p1,out)
                    k=ctx+'|'+a;z=stats.setdefault(k,{'count':0,'utility_sum':0.0,'mean_utility':0.0})
                    z['count']+=1;z['utility_sum']=round(z['utility_sum']+ev['grounded_utility'],6);z['mean_utility']=round(z['utility_sum']/z['count'],6)
    return stats

def _policy_from(stats):
    def policy(obs,p,t):
        ctx=context_class(obs);rows=[]
        for a in ACTIONS:
            z=stats.get(ctx+'|'+a)
            if z and z['count']>0:rows.append((z['mean_utility'],z['count'],a))
        if rows:return sorted(rows,reverse=True)[0][2]
        return 'MOVE_FORWARD'
    return policy

def _baseline(obs,p,t):return 'MOVE_FORWARD'

def run(data):
    ident=_live_identity(data);stats=_train();policy=_policy_from(stats);cases=[];wins=0
    holdouts=[('HOLDOUT_A',99201),('HOLDOUT_A',99202),('HOLDOUT_B',99211),('HOLDOUT_B',99212)]
    for profile,seed in holdouts:
        learned=_run_episode(profile,seed,policy,36);base=_run_episode(profile,seed,_baseline,36);win=learned['measured_score']>base['measured_score'];wins+=int(win)
        cases.append({'profile':profile,'seed':seed,'learned':learned,'baseline':base,'learned_better':win})
    r={'schema':SCHEMA,'individual_id':ident['individual_id'],'training_profiles':['TRAIN_A','TRAIN_B'],'holdout_profiles':['HOLDOUT_A','HOLDOUT_B'],'training_stats':stats,
       'holdout_cases':cases,'wins':wins,'cases':len(cases),'pass':wins>=3,'claim_boundary':{'fresh_layout_transfer_within_same_closed_world_family':True,'predefined_observation_abstractions':True,'finite_action_set':True,'cross_domain_generalization':False,'real_world_generalization':False}}
    r['result_sha256']=sha_obj(r);_write(result_path(data),r);return {'ok':r['pass'],'version':'v992','wins':wins,'cases':len(cases),'holdout_summary':[{'profile':x['profile'],'seed':x['seed'],'learned_score':x['learned']['measured_score'],'baseline_score':x['baseline']['measured_score'],'learned_better':x['learned_better']} for x in cases],'claim_boundary':r['claim_boundary']}

def audit(data):
    p=result_path(data)
    if not p.is_file():return {'ok':False,'version':'v992','errors':['V992_RESULT_MISSING']}
    r=json.loads(p.read_text(encoding='utf-8'));q=dict(r);got=q.pop('result_sha256',None);errs=[]
    if r.get('schema')!=SCHEMA or got!=sha_obj(q):errs.append('V992_RESULT_HASH')
    if r.get('individual_id')!=_live_identity(data)['individual_id']:errs.append('V992_IDENTITY')
    if any(x.get('profile') not in ('HOLDOUT_A','HOLDOUT_B') for x in r.get('holdout_cases',[])):errs.append('V992_HOLDOUT_SCOPE')
    return {'ok':not errs and bool(r.get('pass')),'version':'v992','errors':errs,'wins':r.get('wins'),'cases':r.get('cases'),'claim_boundary':r.get('claim_boundary',{})}
