from __future__ import annotations
import copy, json, random
from pathlib import Path
from tukuyo_v977.whole_state import canon, sha_obj, _live_identity

SCHEMA='tukuyo.v990.closed_environment/1'; EVENT_SCHEMA='tukuyo.v990.environment_events/1'; ZERO='0'*64
ACTIONS=('MOVE_FORWARD','MOVE_BACK','GATHER','REST','SHIELD')
PROFILES=('TRAIN_A','TRAIN_B','HOLDOUT_A','HOLDOUT_B')

def _read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def _write(p,o): p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')
def root(data): return Path(data)/'v990'
def state_path(data): return root(data)/'ENVIRONMENT_STATE.json'
def origin_path(data): return root(data)/'ENVIRONMENT_ORIGIN.json'
def events_path(data): return root(data)/'ENVIRONMENT_EVENTS.json'

def make_world(profile='TRAIN_A',seed=99001):
    if profile not in PROFILES: raise ValueError('V990_PROFILE')
    if type(seed) is not int or seed<0 or seed>2**31-1: raise ValueError('V990_SEED')
    r=random.Random((seed<<8) ^ sum(map(ord,profile)))
    size={'TRAIN_A':7,'TRAIN_B':8,'HOLDOUT_A':9,'HOLDOUT_B':10}[profile]
    candidates=list(range(1,size-1));r.shuffle(candidates)
    nr=2 if profile in ('TRAIN_A','TRAIN_B') else 3
    nh=2 if profile in ('TRAIN_A','HOLDOUT_A') else 3
    resources={str(x):1 for x in sorted(candidates[:nr])}
    hazards={str(x):round(0.25+0.5*r.random(),6) for x in sorted(candidates[nr:nr+nh])}
    # Ensure at least one position can teach each abstract context without overlapping labels.
    for k in list(resources): hazards.pop(k,None)
    return {'schema':SCHEMA,'profile':profile,'seed':seed,'size':size,'position':0,'goal_position':size-1,
            'resources':resources,'hazards':hazards,'visited':[0],'tick':0,'terminal':False,
            'source':'SIMULATED_CLOSED_ENVIRONMENT','deterministic_dynamics':True}

def observation(world):
    pos=int(world['position']);return {
      'source':'SIMULATED_CLOSED_ENVIRONMENT','logical_tick':int(world['tick']),'uncertainty':0.0,
      'position':pos,'goal_direction':0 if pos==world['goal_position'] else (1 if pos<world['goal_position'] else -1),
      'distance_to_goal':abs(int(world['goal_position'])-pos),
      'resource_here':int(world['resources'].get(str(pos),0)),
      'hazard_here':float(world['hazards'].get(str(pos),0.0)),
      'visited_before':pos in world.get('visited',[]),'terminal':bool(world.get('terminal',False))}

def context_class(obs):
    if obs.get('terminal'): return 'GOAL'
    if float(obs.get('hazard_here',0))>0: return 'HAZARD'
    if int(obs.get('resource_here',0))>0: return 'RESOURCE'
    return 'EMPTY'

def transition(world,action):
    if action not in ACTIONS: raise ValueError('V990_ACTION')
    if world.get('terminal'): raise ValueError('V990_TERMINAL')
    w=copy.deepcopy(world);before=observation(w);oldpos=w['position'];old_dist=before['distance_to_goal'];resource_gain=0
    if action=='MOVE_FORWARD': w['position']=min(w['goal_position'],w['position']+1)
    elif action=='MOVE_BACK': w['position']=max(0,w['position']-1)
    elif action=='GATHER':
        key=str(w['position']);resource_gain=int(w['resources'].get(key,0));w['resources'][key]=max(0,int(w['resources'].get(key,0))-resource_gain)
    elif action=='SHIELD': w['position']=min(w['goal_position'],w['position']+1)
    w['tick']+=1
    first_visit=w['position'] not in w['visited']
    if first_visit:w['visited'].append(w['position']);w['visited'].sort()
    raw_hazard=float(w['hazards'].get(str(w['position']),0.0))
    hazard_exposure=round(raw_hazard*(0.15 if action=='SHIELD' else 1.0),6)
    reached=w['position']==w['goal_position'];w['terminal']=bool(reached)
    after=observation(w);new_dist=after['distance_to_goal'];den=max(1,w['size']-1)
    out={'resource_gain':resource_gain,'hazard_exposure':hazard_exposure,'progress_to_goal':round((old_dist-new_dist)/den,6),
         'reached_goal':reached,'information_gain':1 if first_visit else 0,'position_changed':oldpos!=w['position']}
    return w,before,after,out

def init(data,profile='TRAIN_A',seed=99001):
    ident=_live_identity(data);w=make_world(profile,seed);box={'schema':'tukuyo.v990.environment_origin/1','individual_id':ident['individual_id'],'world':w};box['origin_sha256']=sha_obj(box)
    _write(origin_path(data),box);_write(state_path(data),w);_write(events_path(data),{'schema':EVENT_SCHEMA,'individual_id':ident['individual_id'],'events':[]})
    return {'ok':True,'version':'v990','profile':profile,'seed':seed,'observation':observation(w),'world_sha256':sha_obj(w)}

def observe(data):
    if not state_path(data).is_file(): raise ValueError('V990_ENV_NOT_INITIALIZED')
    w=_read(state_path(data));return {'ok':True,'version':'v990','observation':observation(w),'world_sha256':sha_obj(w)}

def act(data,action):
    if not state_path(data).is_file(): raise ValueError('V990_ENV_NOT_INITIALIZED')
    ident=_live_identity(data);before_world=_read(state_path(data));after_world,obs0,obs1,out=transition(before_world,action)
    box=_read(events_path(data));prev=box['events'][-1]['event_sha256'] if box['events'] else ZERO
    e={'seq':len(box['events'])+1,'individual_id':ident['individual_id'],'action':action,'pre_world_sha256':sha_obj(before_world),
       'post_world_sha256':sha_obj(after_world),'observation_before':obs0,'observation_after':obs1,'outcome':out,'prev_sha256':prev}
    e['event_sha256']=sha_obj(e);box['events'].append(e);_write(state_path(data),after_world);_write(events_path(data),box)
    return {'ok':True,'version':'v990','action':action,'observation_before':obs0,'observation_after':obs1,'outcome':out,'event':e}

def audit(data):
    errs=[]
    try:
      ident=_live_identity(data);origin=_read(origin_path(data));box=_read(events_path(data));live=_read(state_path(data))
      q=dict(origin);got=q.pop('origin_sha256',None)
      if got!=sha_obj(q) or origin.get('individual_id')!=ident['individual_id']:errs.append('V990_ORIGIN')
      w=copy.deepcopy(origin['world']);prev=ZERO
      for i,e in enumerate(box.get('events',[]),1):
        if e.get('seq')!=i or e.get('individual_id')!=ident['individual_id'] or e.get('prev_sha256')!=prev:errs.append('V990_EVENT_CHAIN');break
        z=dict(e);h=z.pop('event_sha256',None)
        if h!=sha_obj(z):errs.append('V990_EVENT_HASH');break
        if e.get('pre_world_sha256')!=sha_obj(w):errs.append('V990_PRE_STATE');break
        try:nw,o0,o1,out=transition(w,e.get('action'))
        except Exception:errs.append('V990_REPLAY_ACTION');break
        if e.get('observation_before')!=o0 or e.get('observation_after')!=o1 or e.get('outcome')!=out or e.get('post_world_sha256')!=sha_obj(nw):errs.append('V990_REPLAY_MISMATCH');break
        w=nw;prev=h
      if sha_obj(w)!=sha_obj(live):errs.append('V990_LIVE_STATE_DRIFT')
    except Exception as exc:errs.append(type(exc).__name__+':'+str(exc))
    return {'ok':not errs,'version':'v990','errors':errs,'claim_boundary':{'closed_simulated_environment':True,'sensor_is_simulated_not_physical':True,'observations_provenanced':True,'external_world_grounding':False}}
