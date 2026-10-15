from __future__ import annotations
import json
from pathlib import Path
from tukuyo_v977.whole_state import canon,sha_obj,_live_identity
from tukuyo_v985.narrative_purpose import state_path as purpose_state_path,audit as purpose_audit

SCHEMA='tukuyo.v986.long_horizon_plan/1';EVENT_SCHEMA='tukuyo.v986.plan_events/1';ZERO='0'*64
ALLOWED_ACTIONS=('WHOLE_AUDIT','HOMEOSTASIS_ASSESS','EVIDENCE_REFLECT','RELATIONSHIP_REVIEW','HEART_AUDIT','PURPOSE_REEVALUATE')
TEMPLATES={
 'PRESERVE_INTEGRITY':['WHOLE_AUDIT','HOMEOSTASIS_ASSESS','PURPOSE_REEVALUATE'],
 'SEEK_KNOWLEDGE':['WHOLE_AUDIT','EVIDENCE_REFLECT','PURPOSE_REEVALUATE'],
 'MAINTAIN_RELATIONSHIPS':['WHOLE_AUDIT','RELATIONSHIP_REVIEW','HEART_AUDIT','PURPOSE_REEVALUATE'],
 'SELF_MAINTENANCE':['WHOLE_AUDIT','HOMEOSTASIS_ASSESS','PURPOSE_REEVALUATE'],
 'PRESERVE_TRUTH':['WHOLE_AUDIT','EVIDENCE_REFLECT','PURPOSE_REEVALUATE'],
}

def _read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def _write(p,o):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')
def state_path(data):return Path(data)/'v986'/'LONG_HORIZON_PLAN.json'
def events_path(data):return Path(data)/'v986'/'PLAN_EVENTS.json'
def _strategy_path(data):return Path(data)/'v988'/'STRATEGY_STATE.json'

def _source_sha(data):
 x=_read(purpose_state_path(data));return x.get('state_sha256') or sha_obj(x)

def _strategy_order(data,purpose,actions):
 p=_strategy_path(data)
 if not p.exists():return list(actions),None
 try:x=_read(p)
 except Exception:return list(actions),None
 if x.get('schema')!='tukuyo.v988.strategy_state/1':return list(actions),None
 prefs=x.get('purpose_preferences',{}).get(purpose,[])
 rank={a:i for i,a in enumerate(prefs)}
 # PURPOSE_REEVALUATE stays last because it may legitimately stale the source purpose.
 fixed=[a for a in actions if a!='PURPOSE_REEVALUATE']
 fixed.sort(key=lambda a:(rank.get(a,10_000),actions.index(a)))
 if 'PURPOSE_REEVALUATE' in actions:fixed.append('PURPOSE_REEVALUATE')
 return fixed,x.get('state_sha256')

def _append_event(data,event):
 p=events_path(data);ident=_live_identity(data)
 box=_read(p) if p.exists() else {'schema':EVENT_SCHEMA,'individual_id':ident['individual_id'],'events':[]}
 prev=box['events'][-1]['event_sha256'] if box['events'] else ZERO
 e=dict(event);e['seq']=len(box['events'])+1;e['prev_sha256']=prev;e['event_sha256']=sha_obj(e);box['events'].append(e);_write(p,box);return e

def compile_plan(data,horizon_cycles=3):
 if type(horizon_cycles) is not int or not 1<=horizon_cycles<=12:raise ValueError('V986_HORIZON_RANGE')
 pa=purpose_audit(data)
 if not pa.get('ok'):raise ValueError('V986_PURPOSE_AUDIT')
 if pa.get('stale_sources'):raise ValueError('V986_PURPOSE_STALE')
 purpose=_read(purpose_state_path(data));active=purpose['active_purpose'];base=TEMPLATES.get(active)
 if not base:raise ValueError('V986_UNKNOWN_PURPOSE')
 actions,strategy_sha=_strategy_order(data,active,base)
 ident=_live_identity(data);source_sha=_source_sha(data)
 steps=[]
 for cycle in range(1,horizon_cycles+1):
  for action in actions:
   sid=f'C{cycle:02d}-{len(steps)+1:03d}-{action}'
   steps.append({'step_id':sid,'cycle':cycle,'action':action,'mode':'INTERNAL_BOUNDED','status':'PENDING',
                 'success_criterion':'ACTION_AUDITABLE_AND_NO_EXTERNAL_SIDE_EFFECT'})
 plan_core={'schema':SCHEMA,'individual_id':ident['individual_id'],'lineage_id':ident['lineage_id'],'branch_id':ident['branch_id'],
   'active_purpose':active,'source_purpose_state_sha256':source_sha,'source_strategy_state_sha256':strategy_sha,
   'horizon_cycles':horizon_cycles,'allowed_actions':list(ALLOWED_ACTIONS),'steps':steps,
   'claim_boundary':{'purpose_to_long_horizon_plan':True,'bounded_internal_action_space':True,'autonomous_external_action':False,
                     'unbounded_goal_generation':False,'consciousness_established':False,'literal_soul_established':False}}
 plan_id=sha_obj(plan_core)[:24];plan_core['plan_id']=plan_id;plan_core['plan_sha256']=sha_obj(plan_core);_write(state_path(data),plan_core)
 ev=_append_event(data,{'type':'PLAN_COMPILED','plan_id':plan_id,'active_purpose':active,'horizon_cycles':horizon_cycles,
                         'source_purpose_state_sha256':source_sha,'source_strategy_state_sha256':strategy_sha,'plan_sha256':plan_core['plan_sha256']})
 return {'ok':True,'version':'v986','plan_id':plan_id,'active_purpose':active,'horizon_cycles':horizon_cycles,'step_count':len(steps),
         'first_action':steps[0]['action'],'steps':steps,'event':ev,'claim_boundary':plan_core['claim_boundary']}

def audit(data):
 p=state_path(data)
 if not p.exists():return {'ok':False,'version':'v986','errors':['V986_PLAN_MISSING']}
 errs=[];x=_read(p);q=dict(x);got=q.pop('plan_sha256',None)
 if x.get('schema')!=SCHEMA or got!=sha_obj(q):errs.append('V986_PLAN_HASH')
 core=dict(q);pid=core.pop('plan_id',None)
 if pid!=sha_obj(core)[:24]:errs.append('V986_PLAN_ID')
 ident=_live_identity(data)
 if any(x.get(k)!=ident[k] for k in ('individual_id','lineage_id','branch_id')):errs.append('V986_IDENTITY')
 if any(s.get('action') not in ALLOWED_ACTIONS for s in x.get('steps',[])):errs.append('V986_ACTION_SPACE')
 ids=[s.get('step_id') for s in x.get('steps',[])]
 if len(ids)!=len(set(ids)) or any(not z for z in ids):errs.append('V986_STEP_IDS')
 ep=events_path(data);prev=ZERO
 if ep.exists():
  box=_read(ep)
  if box.get('schema')!=EVENT_SCHEMA or box.get('individual_id')!=ident['individual_id']:errs.append('V986_EVENT_HEADER')
  for i,e in enumerate(box.get('events',[]),1):
   if e.get('seq')!=i or e.get('prev_sha256')!=prev:errs.append('V986_EVENT_CHAIN');break
   z=dict(e);h=z.pop('event_sha256',None)
   if h!=sha_obj(z):errs.append('V986_EVENT_HASH');break
   prev=h
 stale=False
 try:stale=(x.get('source_purpose_state_sha256')!=_source_sha(data))
 except Exception:stale=True
 return {'ok':not errs,'version':'v986','errors':errs,'plan_id':x.get('plan_id'),'active_purpose':x.get('active_purpose'),
         'step_count':len(x.get('steps',[])),'stale_source_purpose':stale,'claim_boundary':x.get('claim_boundary',{})}

def status(data):
 a=audit(data)
 if not a.get('ok'):return a
 x=_read(state_path(data));return {'ok':True,'version':'v986','plan_id':x['plan_id'],'active_purpose':x['active_purpose'],
  'horizon_cycles':x['horizon_cycles'],'step_count':len(x['steps']),'first_action':x['steps'][0]['action'] if x['steps'] else None,
  'stale_source_purpose':a['stale_source_purpose'],'source_strategy_state_sha256':x.get('source_strategy_state_sha256'),'claim_boundary':x['claim_boundary']}
