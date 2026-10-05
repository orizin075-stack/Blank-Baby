from __future__ import annotations
import itertools,json
from pathlib import Path
from tukuyo_v977.whole_state import canon,sha_obj,_live_identity
from tukuyo_v990.closed_environment import make_world,observation,transition
from tukuyo_v991.grounded_organism import default_physiology,apply_physiology,needs,burden
SCHEMA='tukuyo.v999.adaptive_policy_assay/1'
def _write(p,o):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')
def path(data):return Path(data)/'v999'/'ADAPTIVE_POLICY_ASSAY.json'

def _episode(profile,seed,policy,max_steps=40):
    w=make_world(profile,seed);p=default_physiology();acts=[]
    for t in range(max_steps):
        if w['terminal']:break
        obs=observation(w);a=policy(obs,p,t);acts.append(a);w,_,_,out=transition(w,a);p=apply_physiology(p,a,out)
    score=round(float(p['goal_achievement'])*2.0+p['integrity']/100+min(1,p['energy']/60)-burden(needs(p)),6)
    return {'score':score,'reached_goal':bool(w['terminal']),'steps':len(acts),'actions':acts,'distinct_actions':sorted(set(acts))}

def _candidate(spec):
    def policy(obs,p,t):
        if p['energy']<spec['rest_below']:return 'REST'
        if obs['resource_here']>0 and obs['distance_to_goal']>spec['gather_min_distance']:return spec['resource_action']
        if obs['hazard_here']>0:return spec['hazard_action']
        return spec['empty_action']
    return policy

def search_policy():
    # Bounded policy-structure search. Candidate parameters are evaluated only by measured
    # episode outcomes in training worlds; no candidate is assigned a preset score.
    worlds=[('TRAIN_A',99011),('TRAIN_A',99012),('TRAIN_B',99021),('TRAIN_B',99022),('TRAIN_B',99023),('TRAIN_A',99024)]
    rows=[]
    for gather_min,resource_action,hazard_action,empty_action,rest_below in itertools.product(
        (0,1,2,3,4),('GATHER','SHIELD'),('SHIELD','MOVE_FORWARD'),('SHIELD','MOVE_FORWARD'),(0,18,24)):
        spec={'gather_min_distance':gather_min,'resource_action':resource_action,'hazard_action':hazard_action,'empty_action':empty_action,'rest_below':rest_below}
        pol=_candidate(spec);eps=[_episode(p,s,pol) for p,s in worlds]
        mean=round(sum(x['score'] for x in eps)/len(eps),6);div=len(set(a for e in eps for a in e['distinct_actions']))
        rows.append({'spec':spec,'mean_training_score':mean,'action_diversity':div,'all_goal':all(e['reached_goal'] for e in eps)})
    # Prefer measured score; diversity only breaks exact score ties.
    best=max(rows,key=lambda x:(x['mean_training_score'],x['action_diversity'],json.dumps(x['spec'],sort_keys=True)))
    return best,rows

def _forward(obs,p,t):return 'MOVE_FORWARD'
def _shield(obs,p,t):return 'SHIELD'
def _rule(obs,p,t):
    if obs['resource_here']>0:return 'GATHER'
    if obs['hazard_here']>0:return 'SHIELD'
    if p['energy']<24:return 'REST'
    return 'MOVE_FORWARD'

def run(data):
    best,search=search_policy();pol=_candidate(best['spec']);cases=[];wins={'always_forward':0,'always_shield':0,'hand_rule':0};distinct=set()
    holdouts=[('HOLDOUT_A',99201),('HOLDOUT_A',99202),('HOLDOUT_B',99211),('HOLDOUT_B',99212),('HOLDOUT_B',99213),('HOLDOUT_A',99214)]
    for profile,seed in holdouts:
        learned=_episode(profile,seed,pol);forward=_episode(profile,seed,_forward);shield=_episode(profile,seed,_shield);rule=_episode(profile,seed,_rule);distinct.update(learned['distinct_actions'])
        baselines={'always_forward':forward,'always_shield':shield,'hand_rule':rule}
        for k,v in baselines.items():wins[k]+=int(learned['score']>v['score'])
        cases.append({'profile':profile,'seed':seed,'learned':learned,**baselines})
    passed=(wins['always_forward']>=5 and wins['always_shield']>=5 and wins['hand_rule']>=4 and len(distinct)>=2 and best['action_diversity']>=2)
    out={'schema':SCHEMA,'individual_id':_live_identity(data)['individual_id'],'selected_policy':best,'candidate_count':len(search),'wins':wins,'distinct_holdout_actions':sorted(distinct),'cases':cases,'pass':passed,
         'claim_boundary':{'bounded_policy_structure_search':True,'policy_selected_by_measured_training_outcomes':True,'constant_policy_baselines_included':True,'hand_rule_baseline_included':True,'state_dependent_policy_required':True,'same_world_family_only':True,'cross_domain_generalization':False}}
    out['result_sha256']=sha_obj(out);_write(path(data),out)
    return {'ok':passed,'version':'v999','selected_policy':best,'candidate_count':len(search),'wins':wins,'distinct_holdout_actions':sorted(distinct),'cases':cases,'claim_boundary':out['claim_boundary']}

def audit(data):
    p=path(data)
    if not p.is_file():return {'ok':False,'version':'v999','errors':['V999_RESULT_MISSING']}
    x=json.loads(p.read_text(encoding='utf-8'));q=dict(x);h=q.pop('result_sha256',None);errs=[]
    if h!=sha_obj(q):errs.append('V999_HASH')
    if x.get('individual_id')!=_live_identity(data)['individual_id']:errs.append('V999_IDENTITY')
    if len(x.get('distinct_holdout_actions',[]))<2:errs.append('V999_CONSTANT_POLICY')
    if x.get('wins',{}).get('always_shield',0)<5:errs.append('V999_SHIELD_BASELINE_NOT_BEATEN')
    if x.get('wins',{}).get('hand_rule',0)<4:errs.append('V999_RULE_BASELINE_NOT_BEATEN')
    return {'ok':not errs and bool(x.get('pass')),'version':'v999','errors':errs,'selected_policy':x.get('selected_policy'),'wins':x.get('wins'),'distinct_holdout_actions':x.get('distinct_holdout_actions')}
