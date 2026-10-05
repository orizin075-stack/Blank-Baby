from __future__ import annotations
import hashlib, json, os, time, shutil
from pathlib import Path
from tukuyo_common.atomic_fs import atomic_write_json, atomic_write_bytes
from tukuyo_v977.whole_state import canon, sha_obj, audit as whole_audit, sync as whole_sync
from tukuyo_v1014_4.long_run_campaign import (
    start as campaign_start, step as campaign_step, witness_request as campaign_witness_request,
    record_witness as campaign_record_witness, end_request as campaign_end_request,
    audit as campaign_audit, state_path as campaign_state_path,
)
from tukuyo_v1015.living_continuity import episode as living_episode, audit as living_audit
from tukuyo_v1015_1.evidence_authenticity import export_bundle, audit_bundle

SCHEMA='tukuyo.v1015_2.endurance_execution/1'
EVENT_SCHEMA='tukuyo.v1015_2.endurance_execution_event/1'
AUDIT_SCHEMA='tukuyo.v1015_2.endurance_execution_audit/1'
ZERO='0'*64
PROFILES={'24h':86400,'72h':259200,'7d':604800}


def root(data): return Path(data)/'v1015_2'
def state_path(data): return root(data)/'EXECUTION_STATE.json'
def events_dir(data): return root(data)/'events'
def outbox_dir(data): return root(data)/'witness_outbox'
def evidence_dir(data): return root(data)/'evidence'
def receipts_dir(data): return root(data)/'witness_receipts'

def _read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def _sha_file(p):
    p=Path(p); return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None

def _copy_atomic(src,dst):
    src=Path(src);dst=Path(dst);dst.parent.mkdir(parents=True,exist_ok=True);atomic_write_bytes(dst,src.read_bytes());return dst

def _event_file(data,seq): return events_dir(data)/f'{seq:08d}.json'

def _repair_state_head(data):
    st=_read(state_path(data));events_dir(data).mkdir(parents=True,exist_ok=True)
    count=int(st.get('event_count',0));head=str(st.get('event_head_sha256',ZERO))
    while True:
        p=_event_file(data,count+1)
        if not p.is_file(): break
        ev=_read(p)
        if ev.get('schema')!=EVENT_SCHEMA or int(ev.get('seq',-1))!=count+1 or ev.get('previous_event_sha256')!=head:
            raise ValueError('V1015_2_PENDING_EVENT_DIVERGENCE')
        count+=1;head=sha_obj(ev)
    if count!=int(st.get('event_count',0)) or head!=st.get('event_head_sha256'):
        st['event_count']=count;st['event_head_sha256']=head;atomic_write_json(state_path(data),st)
    return st

def _append(data,kind,detail=None,st=None):
    data=Path(data);st=dict(st or _repair_state_head(data));events_dir(data).mkdir(parents=True,exist_ok=True)
    seq=int(st.get('event_count',0))+1;prev=st.get('event_head_sha256',ZERO)
    ev={'schema':EVENT_SCHEMA,'seq':seq,'kind':kind,'utc_ns':time.time_ns(),'pid':os.getpid(),'previous_event_sha256':prev,'detail':detail or {}}
    atomic_write_json(_event_file(data,seq),ev)
    st['event_count']=seq;st['event_head_sha256']=sha_obj(ev);atomic_write_json(state_path(data),st)
    return ev,st

def _receipt_payload(path):
    try:return (_read(path).get('payload') or {})
    except Exception:return {}

def _trust_fingerprint(path):
    s=Path(path).read_text(encoding='utf-8').strip();return hashlib.sha256(s.encode()).hexdigest()

def _request_to_outbox(src,dst):
    return str(_copy_atomic(src,dst))

def _campaign_request(data):
    p=Path(data)/'v1014_4'/'witness_requests'/'start_request.json'
    if not p.is_file(): raise ValueError('START_WITNESS_REQUEST_MISSING')
    return p

def _challenge_binding(st):
    b=st.get('challenge_binding')
    return dict(b) if isinstance(b,dict) and b.get('challenge_payload_sha256') else None

def _bind_request_challenge(path,binding):
    if not binding:return _read(path)
    path=Path(path);rq=_read(path);rq.pop('request_sha256',None)
    rq['challenge_binding']={
      'challenge_id':binding.get('challenge_id'),
      'challenge_payload_sha256':binding.get('challenge_payload_sha256'),
      'challenge_public_key_sha256':binding.get('challenge_public_key_sha256'),
    }
    rq['request_sha256']=sha_obj(rq);atomic_write_bytes(path,canon(rq)+b'\n');return rq

def install_challenge_binding(data,binding):
    """Attach an externally verified challenge before START witness acceptance."""
    data=Path(data);st=_repair_state_head(data)
    if st.get('phase')!='WAITING_START_WITNESS' or st.get('witness_receipts',0):raise ValueError('CHALLENGE_MUST_BIND_BEFORE_START_WITNESS')
    if st.get('challenge_binding') and st.get('challenge_binding')!=binding:raise ValueError('CHALLENGE_ALREADY_BOUND')
    st['challenge_binding']=dict(binding)
    original=_campaign_request(data);rq=_bind_request_challenge(original,binding)
    out=Path(st['start_witness_request']);_copy_atomic(original,out)
    st['pending_request']={'kind':'START','path':str(out),'request_sha256':rq.get('request_sha256'),'created_utc_ns':time.time_ns()}
    atomic_write_json(state_path(data),st)
    ev,st=_append(data,'CHALLENGE_BOUND',{'challenge_binding':binding,'request_sha256':rq.get('request_sha256')},st)
    return {'ok':True,'version':st.get('version','v1015.2'),'challenge_binding':binding,'start_witness_request':str(out),'request_sha256':rq.get('request_sha256'),'event_seq':ev['seq']}

def start(data,profile='24h',target_seconds=None,tick_seconds=300,checkpoint_seconds=3600,witness_seconds=None,living_seconds=3600,note=''):
    data=Path(data)
    if state_path(data).exists(): raise ValueError('ENDURANCE_EXECUTION_ALREADY_EXISTS')
    if profile not in PROFILES: raise ValueError('UNKNOWN_PROFILE')
    target=PROFILES[profile] if target_seconds is None else int(target_seconds)
    if target<1: raise ValueError('TARGET_MIN_1S')
    tick=max(1,int(tick_seconds));checkpoint=max(1,int(checkpoint_seconds));living=max(1,int(living_seconds))
    witness=max(1,int(witness_seconds if witness_seconds is not None else tick))
    # Keep witness requests strictly inside the formal witness-gap ceiling.
    witness=min(witness,max(1,tick))
    cr=campaign_start(data,profile,target,tick,checkpoint,note or 'v1015.2 endurance execution start')
    now=time.time_ns();r=root(data);r.mkdir(parents=True,exist_ok=True);events_dir(data).mkdir(parents=True,exist_ok=True);outbox_dir(data).mkdir(parents=True,exist_ok=True);evidence_dir(data).mkdir(parents=True,exist_ok=True);receipts_dir(data).mkdir(parents=True,exist_ok=True)
    start_req=_campaign_request(data);out_req=outbox_dir(data)/'00000000_START_REQUEST.json';_request_to_outbox(start_req,out_req)
    rq=_read(start_req)
    st={'schema':SCHEMA,'version':'v1015.2','profile':profile,'target_seconds':target,'tick_seconds':tick,'checkpoint_seconds':checkpoint,
        'witness_seconds':witness,'living_seconds':living,'run_id':cr.get('run_id'),'phase':'WAITING_START_WITNESS','created_utc_ns':now,
        'start_witness_request':str(out_req),'start_witness_receipt':None,'end_witness_receipt':None,'pending_request':{'kind':'START','path':str(out_req),'request_sha256':rq.get('request_sha256'),'created_utc_ns':now},
        'witness_trust_sha256':None,'external_start_utc_ns':None,'last_witness_utc_ns':None,'last_witness_seq':0,'last_witness_accept_utc_ns':None,'last_pump_utc_ns':None,'next_step_due_ns':None,'next_witness_due_ns':None,'next_living_due_ns':None,
        'local_target_due_ns':None,'pumps':0,'living_episodes':0,'witness_receipts':0,'receipt_archive':[],'deadline_misses':0,'invalid_reasons':[],
        'event_count':0,'event_head_sha256':ZERO,'evidence_bundle':None,'evidence_audit':None,
        'claim_boundary':{'runner_has_no_witness_private_key':True,'profile_completion_requires_v1015_1_reverification':True,'24h_completed':False,'72h_completed':False,'7day_completed':False}}
    atomic_write_json(state_path(data),st)
    ev,st=_append(data,'EXECUTION_START',{'campaign':cr,'start_request':str(out_req),'note':str(note)[:240]},st)
    return {'ok':True,'version':'v1015.2','phase':st['phase'],'run_id':st['run_id'],'profile':profile,'target_seconds':target,'start_witness_request':str(out_req),'event_seq':ev['seq']}

def _mark_invalid(st,reason):
    xs=list(st.get('invalid_reasons',[]))
    if reason not in xs: xs.append(reason)
    st['invalid_reasons']=xs;st['deadline_misses']=int(st.get('deadline_misses',0))+1
    if st.get('phase') not in ('PROTOCOL_COMPLETE','FAILED'): st['phase']='RUNNING_INVALID'
    return st

def _check_deadlines(st,now):
    pend=st.get('pending_request') or {}
    if pend and st.get('last_witness_accept_utc_ns'):
        max_gap=max(15,int(st.get('tick_seconds',300))*2)
        if now-int(st['last_witness_accept_utc_ns'])>max_gap*1_000_000_000:
            _mark_invalid(st,'WITNESS_DEADLINE_MISSED')
    last=st.get('last_pump_utc_ns')
    if last:
        max_tick=max(5,int(st.get('tick_seconds',300))*2)
        if now-int(last)>max_tick*1_000_000_000:
            _mark_invalid(st,'PUMP_TICK_DEADLINE_MISSED')
    return st

def _realtime_seq(data):
    try:return int(_read(Path(data)/'v1013'/'REALTIME_RUN.json').get('last_event_seq',0))
    except Exception:return 0

def _augment_bundle_receipts(bundle,archive_paths):
    bundle=Path(bundle);obj=_read(bundle);rows=list(obj.get('witness_receipts') or []);seen={(r.get('payload') or {}).get('request_sha256') for r in rows}
    for p in archive_paths or []:
        try:r=_read(p)
        except Exception:continue
        k=(r.get('payload') or {}).get('request_sha256')
        if k and k not in seen:rows.append(r);seen.add(k)
    rows.sort(key=lambda r:int((r.get('payload') or {}).get('witnessed_utc_ns',0)))
    obj['witness_receipts']=rows;obj.pop('bundle_sha256',None);obj['bundle_sha256']=sha_obj(obj);atomic_write_bytes(bundle,canon(obj)+b'\n');return obj

def pump(data,note=''):
    data=Path(data);st=_repair_state_head(data);now=time.time_ns();st=_check_deadlines(st,now)
    phase=st.get('phase')
    if phase=='WAITING_START_WITNESS':
        atomic_write_json(state_path(data),st);return {'ok':not st.get('invalid_reasons'),'version':'v1015.2','phase':phase,'waiting_for':st.get('pending_request')}
    if phase in ('PROTOCOL_COMPLETE','FAILED'):
        return {'ok':phase=='PROTOCOL_COMPLETE' and not st.get('invalid_reasons'),'version':'v1015.2','phase':phase,'invalid_reasons':st.get('invalid_reasons',[])}
    # Keep heartbeat cadence even while a witness receipt is pending.
    did_step=did_living=did_request=False;step_res=living_res=req_res=None
    due=st.get('next_step_due_ns')
    if due is None or now>=int(due):
        step_res=campaign_step(data,note or f'v1015.2-pump-{int(st.get("pumps",0))+1}')
        did_step=True;st['next_step_due_ns']=time.time_ns()+int(st['tick_seconds']*1e9)
        if not step_res.get('ok'): _mark_invalid(st,'CAMPAIGN_STEP_FAILED')
    now=time.time_ns();ldue=st.get('next_living_due_ns')
    if ldue is None or now>=int(ldue):
        living_res=living_episode(data,'observation',0.0,0.2,'endurance_runtime','','',None,'v1015.2 scheduled operational observation')
        did_living=True;st['living_episodes']=int(st.get('living_episodes',0))+1;st['next_living_due_ns']=time.time_ns()+int(st['living_seconds']*1e9)
        if not living_res.get('ok'): _mark_invalid(st,'LIVING_EPISODE_FAILED')
    now=time.time_ns();wdue=st.get('next_witness_due_ns');pend=st.get('pending_request');cur_seq=_realtime_seq(data)
    # A witness is meaningful only after realtime evidence has advanced beyond the previous accepted witness.
    if not pend and (wdue is None or now>=int(wdue)) and (st.get('local_target_due_ns') is None or now<int(st['local_target_due_ns'])) and cur_seq>int(st.get('last_witness_seq',0)):
        out=outbox_dir(data)/f'{int(st.get("event_count",0))+1:08d}_MID_REQUEST.json';req_res=campaign_witness_request(data,out);rq=_bind_request_challenge(out,_challenge_binding(st))
        st['pending_request']={'kind':'MID','path':str(out),'request_sha256':rq.get('request_sha256'),'created_utc_ns':time.time_ns()};did_request=True
    # At the target boundary force one final realtime advance when necessary, so END can never reuse the previous witness seq.
    now=time.time_ns()
    if not st.get('pending_request') and st.get('local_target_due_ns') is not None and now>=int(st['local_target_due_ns']) and st.get('phase') not in ('FINAL_WITNESS_PENDING','PROTOCOL_COMPLETE'):
        cur_seq=_realtime_seq(data)
        if cur_seq<=int(st.get('last_witness_seq',0)):
            final_step=campaign_step(data,note or 'v1015.2-final-boundary-tick');whole_sync(data);step_res=final_step;did_step=True
            st['next_step_due_ns']=time.time_ns()+int(st['tick_seconds']*1e9);cur_seq=_realtime_seq(data)
            if not final_step.get('ok'):_mark_invalid(st,'FINAL_BOUNDARY_STEP_FAILED')
        out=outbox_dir(data)/f'{int(st.get("event_count",0))+1:08d}_END_REQUEST.json';req_res=campaign_end_request(data,out);rq=_bind_request_challenge(out,_challenge_binding(st))
        st['pending_request']={'kind':'END','path':str(out),'request_sha256':rq.get('request_sha256'),'created_utc_ns':time.time_ns()};st['phase']='FINAL_WITNESS_PENDING';did_request=True
    st['pumps']=int(st.get('pumps',0))+1;st['last_pump_utc_ns']=time.time_ns()
    ev,st=_append(data,'PUMP',{'did_step':did_step,'did_living':did_living,'did_request':did_request,'step':step_res,'living':living_res,'request':req_res,'note':str(note)[:240]},st)
    whole_sync(data)
    return {'ok':not st.get('invalid_reasons'),'version':'v1015.2','phase':st['phase'],'pump':st['pumps'],'campaign_step':did_step,'living_episode':did_living,'witness_request':(st.get('pending_request') or {}).get('path'),'event_seq':ev['seq'],'invalid_reasons':st.get('invalid_reasons',[])}

def accept_witness(data,receipt,witness_trust_file):
    data=Path(data);st=_repair_state_head(data);pend=st.get('pending_request') or {}
    if not pend: return {'ok':False,'version':'v1015.2','errors':['NO_PENDING_WITNESS_REQUEST']}
    trust_fp=_trust_fingerprint(witness_trust_file)
    if st.get('witness_trust_sha256') and st['witness_trust_sha256']!=trust_fp:
        return {'ok':False,'version':'v1015.2','errors':['WITNESS_TRUST_ROTATION_NOT_AUTHORIZED']}
    payload=_receipt_payload(receipt)
    if payload.get('request_sha256')!=pend.get('request_sha256'):
        return {'ok':False,'version':'v1015.2','errors':['WITNESS_RECEIPT_REQUEST_MISMATCH']}
    rr=campaign_record_witness(data,receipt,witness_trust_file)
    if not rr.get('ok'): return {'ok':False,'version':'v1015.2','errors':['CAMPAIGN_WITNESS_REJECTED']+list(rr.get('errors',[]))}
    seq=int(payload.get('seq',0));stored=Path(data)/'v1014_4'/'witness_receipts'/f'{seq:08d}.json'
    archive=receipts_dir(data)/f'{payload.get("request_sha256")}.json';_copy_atomic(receipt,archive)
    st['witness_trust_sha256']=trust_fp;st['last_witness_utc_ns']=int(payload.get('witnessed_utc_ns',0));st['last_witness_seq']=seq;st['last_witness_accept_utc_ns']=time.time_ns();st['witness_receipts']=int(st.get('witness_receipts',0))+1
    xs=list(st.get('receipt_archive',[]));xs.append(str(archive));st['receipt_archive']=xs
    kind=pend.get('kind')
    if kind=='START':
        st['start_witness_receipt']=str(stored);st['external_start_utc_ns']=int(payload.get('witnessed_utc_ns',0));st['local_target_due_ns']=time.time_ns()+int(st['target_seconds']*1e9)
        st['phase']='RUNNING';st['next_step_due_ns']=time.time_ns();st['next_living_due_ns']=time.time_ns();st['next_witness_due_ns']=time.time_ns()+int(st['witness_seconds']*1e9)
    elif kind=='MID':
        st['next_witness_due_ns']=time.time_ns()+int(st['witness_seconds']*1e9)
    elif kind=='END':
        st['end_witness_receipt']=str(stored)
    st['pending_request']=None
    ev,st=_append(data,'WITNESS_ACCEPTED',{'kind':kind,'seq':seq,'witnessed_utc_ns':payload.get('witnessed_utc_ns'),'stored_receipt':str(stored)},st)
    if kind=='END':
        out=evidence_dir(data)/f'{st["profile"]}_authenticated_endurance.json'
        export_bundle(data,out,Path(st['start_witness_receipt']),stored,witness_trust_file)
        _augment_bundle_receipts(out,st.get('receipt_archive',[]));ea=audit_bundle(out,witness_trust_file,st.get('profile'))
        st=_repair_state_head(data);st['evidence_bundle']=str(out);st['evidence_audit']=ea;st['phase']='PROTOCOL_COMPLETE' if ea.get('ok') and not st.get('invalid_reasons') else 'FAILED'
        cb=ea.get('claim_boundary') or {};st['claim_boundary'].update({k:bool(cb.get(k)) for k in ('24h_completed','72h_completed','7day_completed')});atomic_write_json(state_path(data),st)
        ev,st=_append(data,'PROTOCOL_FINALIZED',{'evidence_bundle':str(out),'evidence_audit':ea},st)
    return {'ok':st.get('phase')!='FAILED' and not st.get('invalid_reasons'),'version':'v1015.2','phase':st['phase'],'kind':kind,'event_seq':ev['seq'],'evidence_bundle':st.get('evidence_bundle'),'evidence_audit':st.get('evidence_audit'),'invalid_reasons':st.get('invalid_reasons',[])}

def _scan(data):
    out=[];d=events_dir(data)
    if not d.is_dir(): return out
    for p in sorted(d.glob('*.json')):
        try:out.append(_read(p))
        except Exception:out.append({'_malformed':p.name})
    return out

def audit(data,witness_trust_file=None):
    data=Path(data);errs=[]
    if not state_path(data).is_file():return {'ok':False,'version':'v1015.2','schema':AUDIT_SCHEMA,'errors':['EXECUTION_MISSING']}
    st=_read(state_path(data));evs=_scan(data);prev=ZERO
    for i,ev in enumerate(evs,1):
        if ev.get('_malformed'):errs.append('EXECUTION_EVENT_MALFORMED:'+ev['_malformed']);continue
        if ev.get('schema')!=EVENT_SCHEMA or int(ev.get('seq',-1))!=i:errs.append('EXECUTION_EVENT_SCHEMA_SEQ:'+str(i))
        if ev.get('previous_event_sha256')!=prev:errs.append('EXECUTION_EVENT_CHAIN:'+str(i))
        prev=sha_obj(ev)
    if int(st.get('event_count',-1))!=len(evs) or st.get('event_head_sha256')!=prev:errs.append('EXECUTION_STATE_HEAD')
    if st.get('invalid_reasons'):errs.extend('EXECUTION_INVALID:'+x for x in st.get('invalid_reasons',[]))
    wa=whole_audit(data)
    if not wa.get('ok'):errs.append('WHOLE_AUDIT')
    la=living_audit(data)
    if not la.get('ok'):errs.append('LIVING_AUDIT')
    ca=None
    if st.get('start_witness_receipt') and st.get('end_witness_receipt') and witness_trust_file:
        ca=campaign_audit(data,Path(st['start_witness_receipt']),Path(st['end_witness_receipt']),witness_trust_file,True)
        if not ca.get('ok'):errs.extend('CAMPAIGN:'+x for x in ca.get('errors',[]))
    ea=None
    if st.get('evidence_bundle'):
        if not witness_trust_file:errs.append('WITNESS_TRUST_REQUIRED_FOR_FINAL_AUDIT')
        else:
            ea=audit_bundle(Path(st['evidence_bundle']),witness_trust_file,st.get('profile'))
            if not ea.get('ok'):errs.extend('EVIDENCE:'+x for x in ea.get('errors',[]))
    claims={'24h_completed':False,'72h_completed':False,'7day_completed':False}
    if ea:claims.update({k:bool((ea.get('claim_boundary') or {}).get(k)) for k in claims})
    return {'ok':not errs,'version':'v1015.2','schema':AUDIT_SCHEMA,'errors':errs,'phase':st.get('phase'),'profile':st.get('profile'),'run_id':st.get('run_id'),
        'events':len(evs),'pumps':st.get('pumps',0),'living_episodes':st.get('living_episodes',0),'witness_receipts':st.get('witness_receipts',0),'pending_request':st.get('pending_request'),
        'whole_audit_ok':wa.get('ok',False),'living_audit_ok':la.get('ok',False),'campaign_audit':ca,'evidence_audit':ea,
        'claim_boundary':{**claims,'runner_private_witness_key_present':False,'profile_claim_requires_authenticated_bundle':True,'literal_life_established':False,'literal_soul_established':False,'consciousness_established':False,'general_l5':False}}

def status(data,witness_trust_file=None):
    st=_repair_state_head(data);return {'ok':True,'version':'v1015.2','state':st,'audit':audit(data,witness_trust_file)}
