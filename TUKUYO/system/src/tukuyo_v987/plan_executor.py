from __future__ import annotations
import json
from pathlib import Path
from tukuyo_v977.whole_state import canon,sha_obj,_live_identity,audit as whole_audit,sync as whole_sync
from tukuyo_v978.heart_loop import load as load_heart,audit as heart_audit
from tukuyo_v983.homeostasis import assess as homeostasis_assess,audit as homeostasis_audit
from tukuyo_v985.narrative_purpose import integrate as purpose_integrate
from tukuyo_v986.long_horizon_plan import state_path as plan_path,audit as plan_audit,ALLOWED_ACTIONS

SCHEMA='tukuyo.v987.plan_execution_state/1';EVENT_SCHEMA='tukuyo.v987.execution_events/1';ZERO='0'*64

def _read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def _write(p,o):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')
def state_path(data):return Path(data)/'v987'/'PLAN_EXECUTION_STATE.json'
def events_path(data):return Path(data)/'v987'/'EXECUTION_EVENTS.json'
def _plan_sha(data):return _read(plan_path(data)).get('plan_sha256')

def _append_event(data,event):
 p=events_path(data);ident=_live_identity(data);box=_read(p) if p.exists() else {'schema':EVENT_SCHEMA,'individual_id':ident['individual_id'],'events':[]}
 prev=box['events'][-1]['event_sha256'] if box['events'] else ZERO
 e=dict(event);e['seq']=len(box['events'])+1;e['prev_sha256']=prev;e['event_sha256']=sha_obj(e);box['events'].append(e);_write(p,box);return e

def _execute_action(data,action):
 if action not in ALLOWED_ACTIONS:raise ValueError('V987_ACTION_NOT_ALLOWED')
 if action=='WHOLE_AUDIT':
  r=whole_audit(data);return bool(r.get('ok')),0.25 if r.get('ok') else -1.0,{'errors':r.get('errors',[])}
 if action=='HOMEOSTASIS_ASSESS':
  r=homeostasis_assess(data);whole_sync(data);a=homeostasis_audit(data);pressure=max([float(v) for v in r.get('needs',{}).values()]+[0.0])
  return bool(a.get('ok')),round(0.2+0.8*pressure,6),{'intent':r.get('maintenance_intent'),'pressure':round(pressure,6)}
 if action=='EVIDENCE_REFLECT':
  h=load_heart(data);n=len(h.get('episodic_meanings',[]));themes=len({(e.get('theme') or e.get('meaning')) for e in h.get('episodic_meanings',[])})
  utility=min(1.0,0.08*n+0.03*themes);return n>0,round(utility if n>0 else -0.2,6),{'episodes':n,'themes':themes}
 if action=='RELATIONSHIP_REVIEW':
  h=load_heart(data);rels=[e.get('relation') for e in h.get('episodic_meanings',[]) if e.get('relation')];trust=float(h.get('emotion',{}).get('trust',0.5))
  utility=min(1.0,0.15+0.08*len(set(rels))+abs(trust-0.5));return True,round(utility,6),{'relations':len(set(rels)),'trust':trust}
 if action=='HEART_AUDIT':
  r=heart_audit(data);return bool(r.get('ok')),0.25 if r.get('ok') else -1.0,{'errors':r.get('errors',[])}
 if action=='PURPOSE_REEVALUATE':
  r=purpose_integrate(data);whole_sync(data);return bool(r.get('ok')),0.35,{'active_purpose':r.get('active_purpose'),'revision_count':r.get('revision_count')}
 raise ValueError('V987_ACTION_UNREACHABLE')

def execute(data,max_steps=None):
 pa=plan_audit(data)
 if not pa.get('ok'):raise ValueError('V987_PLAN_AUDIT')
 if pa.get('stale_source_purpose'):raise ValueError('V987_PLAN_STALE')
 plan=_read(plan_path(data));steps=plan.get('steps',[])
 if max_steps is None:max_steps=len(steps)
 if type(max_steps) is not int or not 1<=max_steps<=len(steps):raise ValueError('V987_MAX_STEPS')
 trace=[];success_count=0;utility_sum=0.0
 for step in steps[:max_steps]:
  ok,utility,obs=_execute_action(data,step['action']);success_count+=int(ok);utility_sum+=float(utility)
  trace.append({'step_id':step['step_id'],'cycle':step['cycle'],'action':step['action'],'ok':bool(ok),'utility':round(float(utility),6),'observation':obs})
 ident=_live_identity(data)
 state={'schema':SCHEMA,'individual_id':ident['individual_id'],'lineage_id':ident['lineage_id'],'branch_id':ident['branch_id'],
  'plan_id':plan['plan_id'],'source_plan_sha256':plan['plan_sha256'],'source_plan_snapshot':plan,'executed_steps':len(trace),'planned_steps':len(steps),
  'success_count':success_count,'success_rate':round(success_count/len(trace),6),'mean_utility':round(utility_sum/len(trace),6),
  'complete':len(trace)==len(steps),'trace':trace,
  'claim_boundary':{'bounded_internal_plan_execution':True,'outcome_accounting':True,'autonomous_external_action':False,
                    'motor_control':False,'consciousness_established':False,'literal_soul_established':False}}
 state['state_sha256']=sha_obj(state);_write(state_path(data),state)
 ev=_append_event(data,{'type':'PLAN_EXECUTED','plan_id':plan['plan_id'],'source_plan_sha256':plan['plan_sha256'],'executed_steps':len(trace),
                        'success_rate':state['success_rate'],'mean_utility':state['mean_utility'],'complete':state['complete'],'state_sha256':state['state_sha256']})
 whole_sync(data)
 return {'ok':success_count==len(trace),'version':'v987','plan_id':plan['plan_id'],'executed_steps':len(trace),'success_rate':state['success_rate'],
         'mean_utility':state['mean_utility'],'complete':state['complete'],'trace':trace,'event':ev,'claim_boundary':state['claim_boundary']}

def audit(data):
 p=state_path(data)
 if not p.exists():return {'ok':False,'version':'v987','errors':['V987_EXECUTION_MISSING']}
 errs=[];x=_read(p);q=dict(x);got=q.pop('state_sha256',None)
 if x.get('schema')!=SCHEMA or got!=sha_obj(q):errs.append('V987_STATE_HASH')
 ident=_live_identity(data)
 if any(x.get(k)!=ident[k] for k in ('individual_id','lineage_id','branch_id')):errs.append('V987_IDENTITY')
 try:
  snap=x.get('source_plan_snapshot') or {}
  qplan=dict(snap);ph=qplan.pop('plan_sha256',None)
  if ph!=sha_obj(qplan) or x.get('source_plan_sha256')!=ph or x.get('plan_id')!=snap.get('plan_id'):errs.append('V987_PLAN_BINDING')
 except Exception:errs.append('V987_PLAN_BINDING')
 for t in x.get('trace',[]):
  if t.get('action') not in ALLOWED_ACTIONS:errs.append('V987_ACTION_SPACE');break
 ep=events_path(data);prev=ZERO
 if ep.exists():
  box=_read(ep)
  if box.get('schema')!=EVENT_SCHEMA or box.get('individual_id')!=ident['individual_id']:errs.append('V987_EVENT_HEADER')
  for i,e in enumerate(box.get('events',[]),1):
   if e.get('seq')!=i or e.get('prev_sha256')!=prev:errs.append('V987_EVENT_CHAIN');break
   z=dict(e);h=z.pop('event_sha256',None)
   if h!=sha_obj(z):errs.append('V987_EVENT_HASH');break
   prev=h
 return {'ok':not errs,'version':'v987','errors':errs,'plan_id':x.get('plan_id'),'success_rate':x.get('success_rate'),
         'mean_utility':x.get('mean_utility'),'complete':x.get('complete'),'claim_boundary':x.get('claim_boundary',{})}

def status(data):
 a=audit(data)
 if not a.get('ok'):return a
 x=_read(state_path(data));return {'ok':True,'version':'v987','plan_id':x['plan_id'],'executed_steps':x['executed_steps'],'planned_steps':x['planned_steps'],
  'success_rate':x['success_rate'],'mean_utility':x['mean_utility'],'complete':x['complete'],'claim_boundary':x['claim_boundary']}
