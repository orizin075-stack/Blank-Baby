from __future__ import annotations
import json
from pathlib import Path
from tukuyo_v977.whole_state import canon,sha_obj,_live_identity
from tukuyo_v986.long_horizon_plan import state_path as plan_path
from tukuyo_v987.plan_executor import state_path as execution_path,audit as execution_audit

SCHEMA='tukuyo.v988.strategy_state/1';EVENT_SCHEMA='tukuyo.v988.strategy_events/1';ZERO='0'*64

def _read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def _write(p,o):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')
def state_path(data):return Path(data)/'v988'/'STRATEGY_STATE.json'
def events_path(data):return Path(data)/'v988'/'STRATEGY_EVENTS.json'

def _append_event(data,event):
 p=events_path(data);ident=_live_identity(data);box=_read(p) if p.exists() else {'schema':EVENT_SCHEMA,'individual_id':ident['individual_id'],'events':[]}
 prev=box['events'][-1]['event_sha256'] if box['events'] else ZERO
 e=dict(event);e['seq']=len(box['events'])+1;e['prev_sha256']=prev;e['event_sha256']=sha_obj(e);box['events'].append(e);_write(p,box);return e

def learn(data):
 ea=execution_audit(data)
 if not ea.get('ok'):raise ValueError('V988_EXECUTION_AUDIT')
 exe=_read(execution_path(data));plan=exe.get('source_plan_snapshot') or _read(plan_path(data));purpose=plan['active_purpose']
 old=_read(state_path(data)) if state_path(data).exists() else None
 consumed=list(old.get('consumed_execution_state_sha256s',[])) if old else []
 if exe['state_sha256'] in consumed:
  return {'ok':True,'version':'v988','idempotent':True,'purpose':purpose,'preference':old.get('purpose_preferences',{}).get(purpose,[]),
          'revision_count':old.get('revision_count',0),'action_stats':old.get('action_stats',{}),'claim_boundary':old.get('claim_boundary',{})}
 stats=dict(old.get('action_stats',{})) if old else {}
 # one execution state represents one bounded observed episode; update each action once per occurrence.
 for t in exe.get('trace',[]):
  a=t['action'];z=dict(stats.get(a,{'count':0,'successes':0,'utility_sum':0.0,'mean_utility':0.0}))
  z['count']=int(z['count'])+1;z['successes']=int(z['successes'])+int(bool(t.get('ok')));z['utility_sum']=round(float(z['utility_sum'])+float(t.get('utility',0)),6)
  z['mean_utility']=round(z['utility_sum']/z['count'],6);z['success_rate']=round(z['successes']/z['count'],6);stats[a]=z
 purpose_actions=sorted({t['action'] for t in exe.get('trace',[]) if t['action']!='PURPOSE_REEVALUATE'})
 ranked=sorted(purpose_actions,key=lambda a:(float(stats[a].get('success_rate',0)),float(stats[a].get('mean_utility',0)),a),reverse=True)
 if any(t['action']=='PURPOSE_REEVALUATE' for t in exe.get('trace',[])):ranked.append('PURPOSE_REEVALUATE')
 prefs=dict(old.get('purpose_preferences',{})) if old else {};prior=prefs.get(purpose);prefs[purpose]=ranked
 revision_count=int(old.get('revision_count',0)) if old else 0
 if prior is not None and prior!=ranked:revision_count+=1
 elif prior is None:revision_count+=1
 ident=_live_identity(data);state={'schema':SCHEMA,'individual_id':ident['individual_id'],'lineage_id':ident['lineage_id'],'branch_id':ident['branch_id'],
  'source_execution_state_sha256':exe['state_sha256'],'source_plan_sha256':plan['plan_sha256'],'consumed_execution_state_sha256s':(consumed+[exe['state_sha256']])[-256:],
  'action_stats':stats,'purpose_preferences':prefs,'revision_count':revision_count,'last_purpose':purpose,
  'claim_boundary':{'empirical_strategy_adaptation':True,'outcome_history_changes_future_plan_order':True,'bounded_internal_action_space':True,
                    'self_modifying_code':False,'autonomous_external_action':False,'open_ended_goal_invention':False,'consciousness_established':False}}
 state['state_sha256']=sha_obj(state);_write(state_path(data),state)
 ev=_append_event(data,{'type':'STRATEGY_LEARNED','purpose':purpose,'preference':ranked,'revision_count':revision_count,
                         'source_execution_state_sha256':exe['state_sha256'],'state_sha256':state['state_sha256']})
 return {'ok':True,'version':'v988','purpose':purpose,'preference':ranked,'revision_count':revision_count,'action_stats':stats,'event':ev,'claim_boundary':state['claim_boundary']}

def audit(data):
 p=state_path(data)
 if not p.exists():return {'ok':False,'version':'v988','errors':['V988_STRATEGY_MISSING']}
 errs=[];x=_read(p);q=dict(x);got=q.pop('state_sha256',None)
 if x.get('schema')!=SCHEMA or got!=sha_obj(q):errs.append('V988_STATE_HASH')
 ident=_live_identity(data)
 if any(x.get(k)!=ident[k] for k in ('individual_id','lineage_id','branch_id')):errs.append('V988_IDENTITY')
 consumed=x.get('consumed_execution_state_sha256s',[])
 if len(consumed)!=len(set(consumed)) or x.get('source_execution_state_sha256') not in consumed:errs.append('V988_CONSUMPTION_LEDGER')
 ep=events_path(data);prev=ZERO
 if ep.exists():
  box=_read(ep)
  if box.get('schema')!=EVENT_SCHEMA or box.get('individual_id')!=ident['individual_id']:errs.append('V988_EVENT_HEADER')
  for i,e in enumerate(box.get('events',[]),1):
   if e.get('seq')!=i or e.get('prev_sha256')!=prev:errs.append('V988_EVENT_CHAIN');break
   z=dict(e);h=z.pop('event_sha256',None)
   if h!=sha_obj(z):errs.append('V988_EVENT_HASH');break
   prev=h
 return {'ok':not errs,'version':'v988','errors':errs,'revision_count':x.get('revision_count'),'last_purpose':x.get('last_purpose'),
         'purpose_preferences':x.get('purpose_preferences',{}),'claim_boundary':x.get('claim_boundary',{})}

def status(data):
 a=audit(data)
 if not a.get('ok'):return a
 x=_read(state_path(data));return {'ok':True,'version':'v988','revision_count':x['revision_count'],'last_purpose':x['last_purpose'],
  'purpose_preferences':x['purpose_preferences'],'action_stats':x['action_stats'],'claim_boundary':x['claim_boundary']}
