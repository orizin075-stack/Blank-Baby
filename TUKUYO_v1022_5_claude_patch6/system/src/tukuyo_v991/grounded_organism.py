from __future__ import annotations
import copy,json,math
from pathlib import Path
from tukuyo_v977.whole_state import canon,sha_obj,_live_identity
from tukuyo_v978.heart_loop import process_experience
from tukuyo_v990.closed_environment import act as env_act,audit as env_audit,events_path as env_events_path,state_path as env_state_path

SCHEMA='tukuyo.v991.grounded_organism/1'; EVENT_SCHEMA='tukuyo.v991.grounded_events/1'; ZERO='0'*64

def _read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def _write(p,o):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')
def root(data):return Path(data)/'v991'
def state_path(data):return root(data)/'GROUNDED_ORGANISM_STATE.json'
def origin_path(data):return root(data)/'GROUNDED_ORGANISM_ORIGIN.json'
def events_path(data):return root(data)/'GROUNDED_EVENTS.json'

def default_physiology():return {'energy':60.0,'integrity':100.0,'fatigue':0.10,'threat':0.0,'reserve':40.0,'uncertainty':0.65,'goal_achievement':0.0}
def needs(p):
    return {'energy_deficit':round(max(0,(50-p['energy'])/50),6),'integrity_deficit':round(max(0,(100-p['integrity'])/100),6),
            'fatigue':round(max(0,min(1,p['fatigue'])),6),'threat':round(max(0,min(1,p['threat'])),6),'reserve_deficit':round(max(0,(30-p['reserve'])/30),6),
            'uncertainty':round(max(0,min(1,p['uncertainty'])),6)}
def burden(n):return round(sum(float(n[k])*w for k,w in {'energy_deficit':.22,'integrity_deficit':.30,'fatigue':.12,'threat':.18,'reserve_deficit':.10,'uncertainty':.08}.items()),6)

def apply_physiology(p,action,outcome):
    q=copy.deepcopy(p);effort={'MOVE_FORWARD':2.5,'MOVE_BACK':2.0,'GATHER':1.0,'REST':0.0,'SHIELD':1.5}[action]
    q['energy']=max(0.0,q['energy']-effort+float(outcome.get('resource_gain',0))*12.0+(5.0 if action=='REST' else 0.0))
    q['reserve']=max(0.0,q['reserve']-effort*.30+float(outcome.get('resource_gain',0))*4.0)
    q['integrity']=max(0.0,q['integrity']-float(outcome.get('hazard_exposure',0))*18.0)
    q['fatigue']=max(0.0,min(1.0,q['fatigue']+effort*.025-(.18 if action=='REST' else 0.0)))
    q['threat']=max(0.0,min(1.0,q['threat']*.72+float(outcome.get('hazard_exposure',0))*.65))
    q['uncertainty']=max(0.0,min(1.0,q['uncertainty']-float(outcome.get('information_gain',0))*.12))
    if outcome.get('reached_goal'):q['goal_achievement']=1.0
    return {k:round(v,6) for k,v in q.items()}

def derive_evaluation(before,after,outcome):
    nb,na=needs(before),needs(after);homeo=round(burden(nb)-burden(na),6)
    task=round(float(outcome.get('progress_to_goal',0))*.90+float(bool(outcome.get('reached_goal')))*.75+float(outcome.get('information_gain',0))*.08,6)
    observed=round(float(outcome.get('resource_gain',0))*.08-float(outcome.get('hazard_exposure',0))*.45,6)
    utility=round(max(-1,min(1,homeo+task+observed)),6);valence=round(max(-1,min(1,math.tanh(utility*1.75))),6)
    importance=round(max(.05,min(1,abs(utility)+float(outcome.get('hazard_exposure',0))*.5+float(bool(outcome.get('reached_goal')))*.35)),6)
    if float(outcome.get('hazard_exposure',0))>0:meaning='SELF_INTEGRITY_THREAT';kind='harm'
    elif outcome.get('reached_goal'):meaning='GOAL_ATTAINMENT';kind='discovery'
    elif float(outcome.get('resource_gain',0))>0:meaning='RESOURCE_RECOVERY';kind='recovery'
    elif float(outcome.get('information_gain',0))>0:meaning='NOVEL_OBSERVATION';kind='discovery'
    else:meaning='EFFORT_WITHOUT_OBSERVED_GAIN';kind='grounded_action'
    return {'homeostatic_delta':homeo,'task_delta':task,'observed_environment_delta':observed,'grounded_utility':utility,'derived_valence':valence,'derived_importance':importance,'meaning':meaning,'heart_kind':kind,
            'formula':'burden_before-burden_after + .90*progress + .75*goal + .08*information + .08*resource - .45*hazard','needs_before':nb,'needs_after':na}

def init(data):
    ident=_live_identity(data);p=default_physiology();o={'schema':'tukuyo.v991.grounded_organism_origin/1','individual_id':ident['individual_id'],'physiology':p};o['origin_sha256']=sha_obj(o)
    _write(origin_path(data),o);_write(state_path(data),{'schema':SCHEMA,'individual_id':ident['individual_id'],'step':0,'physiology':p,'last_evaluation':None});_write(events_path(data),{'schema':EVENT_SCHEMA,'individual_id':ident['individual_id'],'events':[]})
    return {'ok':True,'version':'v991','physiology':p,'needs':needs(p)}

def step(data,action):
    if not env_state_path(data).is_file():raise ValueError('V991_ENV_REQUIRED')
    if not state_path(data).is_file():init(data)
    ident=_live_identity(data);s=_read(state_path(data));before=s['physiology'];er=env_act(data,action);after=apply_physiology(before,action,er['outcome']);ev=derive_evaluation(before,after,er['outcome'])
    hr=process_experience(data,ev['heart_kind'],ev['derived_valence'],ev['derived_importance'],ev['meaning'].lower(),'')
    box=_read(events_path(data));prev=box['events'][-1]['event_sha256'] if box['events'] else ZERO
    e={'seq':len(box['events'])+1,'individual_id':ident['individual_id'],'action':action,'environment_event_sha256':er['event']['event_sha256'],
       'physiology_before':before,'physiology_after':after,'environment_outcome':er['outcome'],'evaluation':ev,'heart_event_sha256':hr['event']['event_sha256'],'prev_sha256':prev};e['event_sha256']=sha_obj(e);box['events'].append(e)
    ns={'schema':SCHEMA,'individual_id':ident['individual_id'],'step':e['seq'],'physiology':after,'last_evaluation':ev,'last_environment_event_sha256':er['event']['event_sha256']};_write(state_path(data),ns);_write(events_path(data),box)
    return {'ok':True,'version':'v991','action':action,'environment':er,'physiology_before':before,'physiology_after':after,'evaluation':ev,'grounded_heart_result':hr}

def audit(data):
    errs=[]
    try:
      if not env_audit(data).get('ok'):errs.append('V991_ENV_AUDIT')
      ident=_live_identity(data);origin=_read(origin_path(data));state=_read(state_path(data));box=_read(events_path(data));envbox=_read(env_events_path(data));emap={e['event_sha256']:e for e in envbox.get('events',[])}
      q=dict(origin);got=q.pop('origin_sha256',None)
      if got!=sha_obj(q) or origin.get('individual_id')!=ident['individual_id']:errs.append('V991_ORIGIN')
      p=copy.deepcopy(origin['physiology']);prev=ZERO
      for i,e in enumerate(box.get('events',[]),1):
        if e.get('seq')!=i or e.get('individual_id')!=ident['individual_id'] or e.get('prev_sha256')!=prev:errs.append('V991_EVENT_CHAIN');break
        z=dict(e);h=z.pop('event_sha256',None)
        if h!=sha_obj(z):errs.append('V991_EVENT_HASH');break
        ee=emap.get(e.get('environment_event_sha256'))
        if not ee:errs.append('V991_ENV_BINDING');break
        if e.get('physiology_before')!=p or e.get('environment_outcome')!=ee.get('outcome'):errs.append('V991_SOURCE_MISMATCH');break
        np=apply_physiology(p,e['action'],ee['outcome']);de=derive_evaluation(p,np,ee['outcome'])
        if e.get('physiology_after')!=np or e.get('evaluation')!=de:errs.append('V991_REPLAY_MISMATCH');break
        p=np;prev=h
      if state.get('physiology')!=p or state.get('step')!=len(box.get('events',[])):errs.append('V991_LIVE_STATE_DRIFT')
    except Exception as exc:errs.append(type(exc).__name__+':'+str(exc))
    return {'ok':not errs,'version':'v991','errors':errs,'claim_boundary':{'valence_self_derived_from_state_change':True,'utility_from_observed_outcomes_not_action_constants':True,'simulated_body_only':True,'literal_emotion_established':False,'literal_life_established':False}}

def status(data):
    a=audit(data)
    if not a['ok']:return a
    s=_read(state_path(data));return {'ok':True,'version':'v991','step':s['step'],'physiology':s['physiology'],'needs':needs(s['physiology']),'last_evaluation':s.get('last_evaluation'),'claim_boundary':a['claim_boundary']}
