from __future__ import annotations
import json
from pathlib import Path
from tukuyo_v977.whole_state import canon,sha_obj,_live_identity,load_soul
from tukuyo_v978.heart_loop import load as load_heart

SCHEMA='tukuyo.v983.homeostasis_state/1';ZERO='0'*64

def _read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def _write(p,o):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')
def state_path(data):return Path(data)/'v983'/'HOMEOSTASIS_STATE.json'
def events_path(data):return Path(data)/'v983'/'HOMEOSTASIS_EVENTS.json'
def _organism(data):return _read(Path(data)/'state'/'organism'/'organism_state.json')['payload']

def _derive(org,heart):
    energy=float(org['resources']['energy']);reserve=float(org['resources']['metabolic_reserve']);integrity=float(org['health']['integrity']);debt=float(org['metabolism']['maintenance_debt']);fatigue=float(org['affect']['fatigue']);threat=float(heart['emotion']['threat'])
    needs={'energy_deficit':round(max(0,(40-energy)/40),6),'reserve_deficit':round(max(0,(600-reserve)/600),6),'integrity_deficit':round(max(0,(95-integrity)/95),6),'maintenance_pressure':round(min(1,debt/10),6),'fatigue':round(max(0,min(1,fatigue)),6),'perceived_threat':round(max(0,min(1,threat)),6)}
    if org['lifecycle']['status']!='alive':intent='PRESERVE_TERMINAL_RECORD'
    elif integrity<80 or debt>=6:intent='PRIORITIZE_MAINTENANCE'
    elif energy<30 or reserve<500:intent='CONSERVE_ENERGY'
    elif fatigue>=.65:intent='REST_AND_RECOVER'
    elif threat>=.60:intent='REDUCE_THREAT'
    else:intent='OBSERVE_AND_LEARN'
    return needs,intent

def assess(data):
    ident=_live_identity(data);org=_organism(data);heart=load_heart(data);soul=load_soul(data);needs,intent=_derive(org,heart)
    p=state_path(data);seq=1;prev=ZERO
    if p.exists():
        old=_read(p);seq=int(old['seq'])+1;prev=old['state_sha256']
    x={'schema':SCHEMA,'seq':seq,'individual_id':ident['individual_id'],'lineage_id':ident['lineage_id'],'branch_id':ident['branch_id'],
      'organism_tick':org['runtime']['tick'],'organism_state_seq':org['continuity']['state_seq'],'needs':needs,'maintenance_intent':intent,
      'soul_sha256':sha_obj(soul),'heart_sha256':sha_obj(heart),'previous_state_sha256':prev,
      'claim_boundary':{'functional_homeostasis_layer':True,'high_level_intent_only':True,'direct_motor_override':False,'consciousness_established':False,'literal_life_established':False}}
    x['state_sha256']=sha_obj(x);_write(p,x)
    ep=events_path(data);box=_read(ep) if ep.exists() else {'schema':'tukuyo.v983.homeostasis_events/1','individual_id':ident['individual_id'],'events':[]}
    pe=box['events'][-1]['event_sha256'] if box['events'] else ZERO
    e={'seq':len(box['events'])+1,'state_seq':seq,'organism_tick':org['runtime']['tick'],'maintenance_intent':intent,'needs':needs,'prev_sha256':pe};e['event_sha256']=sha_obj(e);box['events'].append(e);_write(ep,box)
    return {'ok':True,'version':'v983','maintenance_intent':intent,'needs':needs,'state_sha256':x['state_sha256'],'organism_tick':org['runtime']['tick']}

def audit(data):
    errs=[];p=state_path(data)
    if not p.exists():return {'ok':False,'version':'v983','errors':['HOMEOSTASIS_STATE_MISSING']}
    x=_read(p);q=dict(x);got=q.pop('state_sha256',None)
    if x.get('schema')!=SCHEMA or got!=sha_obj(q):errs.append('HOMEOSTASIS_STATE_HASH')
    ident=_live_identity(data)
    if any(x.get(k)!=ident[k] for k in ('individual_id','lineage_id','branch_id')):errs.append('HOMEOSTASIS_IDENTITY')
    ep=events_path(data);prev=ZERO
    if ep.exists():
        box=_read(ep)
        for i,e in enumerate(box.get('events',[]),1):
            if e.get('seq')!=i or e.get('prev_sha256')!=prev:errs.append('HOMEOSTASIS_EVENT_CHAIN');break
            z=dict(e);h=z.pop('event_sha256',None)
            if h!=sha_obj(z):errs.append('HOMEOSTASIS_EVENT_HASH');break
            prev=h
    org=_organism(data);stale=(x.get('organism_state_seq')!=org['continuity']['state_seq'])
    return {'ok':not errs,'version':'v983','errors':errs,'maintenance_intent':x.get('maintenance_intent'),'stale_since_last_assessment':stale,
      'claim_boundary':x.get('claim_boundary',{})}
