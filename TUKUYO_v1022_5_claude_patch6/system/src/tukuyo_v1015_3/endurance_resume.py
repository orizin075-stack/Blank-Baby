from __future__ import annotations
import base64, hashlib, json, os, time
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from tukuyo_common.atomic_fs import atomic_write_json, atomic_write_bytes
from tukuyo_v977.whole_state import canon, sha_obj
from tukuyo_v1015_2 import endurance_execution as base

VERSION='v1015.3'
SCHEMA='tukuyo.v1015_3.endurance_resume/1'
EVENT_SCHEMA='tukuyo.v1015_3.endurance_resume_event/1'
FAILURE_SCHEMA='tukuyo.v1015_3.failure_evidence/1'
FAILURE_AUDIT_SCHEMA='tukuyo.v1015_3.failure_evidence_audit/1'
ZERO='0'*64


def root(data): return Path(data)/'v1015_3'
def state_path(data): return root(data)/'RESUME_STATE.json'
def events_dir(data): return root(data)/'events'
def failure_path(data): return root(data)/'FAILURE_EVIDENCE.json'
def _event_file(data,seq): return events_dir(data)/f'{seq:08d}.json'
def _read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def _file_sha(p):
    p=Path(p); return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None

def _package_root(): return Path(__file__).resolve().parents[2]
def _release_binding():
    r=_package_root(); mp=r/'META'/'RELEASE_MANIFEST.json'; rp=r/'META'/'RELEASE_RECEIPT.json'
    m=_read(mp); rec=_read(rp)
    return {
        'manifest_sha256':_file_sha(mp),
        'receipt_sha256':_file_sha(rp),
        'manifest_version':m.get('version'),
        'manifest_file_count':m.get('file_count'),
        'release_public_key':rec.get('public_key'),
        'receipt_manifest_sha256':(rec.get('payload') or {}).get('manifest_sha256'),
    }

def _binding_errors(saved):
    cur=_release_binding(); errs=[]
    for k in ('manifest_sha256','receipt_sha256','manifest_version','manifest_file_count','release_public_key','receipt_manifest_sha256'):
        if saved.get(k)!=cur.get(k): errs.append('RELEASE_BINDING_CHANGED:'+k)
    return errs,cur

def _session_token(): return os.environ.get('TUKUYO_ENDURANCE_RUNNER_SESSION') or 'unmanaged-cli'

def _repair(data):
    st=_read(state_path(data)); events_dir(data).mkdir(parents=True,exist_ok=True)
    count=int(st.get('event_count',0)); head=str(st.get('event_head_sha256',ZERO))
    while True:
        p=_event_file(data,count+1)
        if not p.is_file(): break
        ev=_read(p)
        if ev.get('schema')!=EVENT_SCHEMA or int(ev.get('seq',-1))!=count+1 or ev.get('previous_event_sha256')!=head:
            raise ValueError('V1015_3_PENDING_EVENT_DIVERGENCE')
        count+=1; head=sha_obj(ev)
    if count!=int(st.get('event_count',0)) or head!=st.get('event_head_sha256'):
        st['event_count']=count; st['event_head_sha256']=head; atomic_write_json(state_path(data),st)
    return st

def _append(data,kind,detail=None,st=None):
    st=dict(st or _repair(data)); seq=int(st.get('event_count',0))+1; prev=st.get('event_head_sha256',ZERO)
    ev={'schema':EVENT_SCHEMA,'seq':seq,'kind':kind,'utc_ns':time.time_ns(),'pid':os.getpid(),'runner_session_id':_session_token(),
        'previous_event_sha256':prev,'detail':detail or {}}
    events_dir(data).mkdir(parents=True,exist_ok=True); atomic_write_json(_event_file(data,seq),ev)
    st['event_count']=seq; st['event_head_sha256']=sha_obj(ev); st['last_activity_utc_ns']=ev['utc_ns']; atomic_write_json(state_path(data),st)
    return ev,st

def _scan_events(data):
    out=[]
    if not events_dir(data).is_dir(): return out
    for p in sorted(events_dir(data).glob('*.json')):
        try: out.append(_read(p))
        except Exception: out.append({'_malformed':p.name})
    return out

def _base_state(data): return _read(base.state_path(data))
def _write_base_state(data,st): atomic_write_json(base.state_path(data),st)

def _new_state(data):
    bs=_base_state(data); now=time.time_ns(); tok=_session_token()
    return {
        'schema':SCHEMA,'version':VERSION,'parent_execution_version':'v1015.2','run_id':bs.get('run_id'),'profile':bs.get('profile'),
        'release_binding':_release_binding(),'terminal_state':'ACTIVE','failure_reasons':[],'session_count':1,'resume_count':0,
        'last_session_id':tok,'last_session_start_utc_ns':now,'last_activity_utc_ns':now,'event_count':0,'event_head_sha256':ZERO,
        'failure_evidence':None,'claim_boundary':{'24h_completed':False,'72h_completed':False,'7day_completed':False,
        'terminal_failure_is_irreversible':True,'resume_requires_same_release_binding':True,'failed_campaign_cannot_be_promoted':True}
    }

def _ensure(data):
    if not state_path(data).is_file():
        root(data).mkdir(parents=True,exist_ok=True); events_dir(data).mkdir(parents=True,exist_ok=True)
        st=_new_state(data); atomic_write_json(state_path(data),st); _,st=_append(data,'RESUME_LAYER_INITIALIZED',{'release_binding':st['release_binding']},st)
        return st
    return _repair(data)

def _touch_session(data,st,note=''):
    tok=_session_token()
    if tok==st.get('last_session_id'): return st,False
    now=time.time_ns(); gap=(now-int(st.get('last_activity_utc_ns',now)))/1e9
    st['session_count']=int(st.get('session_count',0))+1; st['resume_count']=int(st.get('resume_count',0))+1
    st['last_session_id']=tok; st['last_session_start_utc_ns']=now
    ev,st=_append(data,'RUNNER_SESSION_RESUME',{'resume_gap_seconds':gap,'note':str(note)[:240]},st)
    return st,True

def _deadline_failures(data):
    bs=_base_state(data); phase=bs.get('phase'); now=time.time_ns(); errs=[]
    if phase in ('RUNNING','RUNNING_INVALID','FINAL_WITNESS_PENDING'):
        last=bs.get('last_pump_utc_ns')
        if last:
            max_tick=max(5,int(bs.get('tick_seconds',300))*2)
            if now-int(last)>max_tick*1_000_000_000: errs.append('RESUME_TICK_GAP_EXCEEDED')
        if bs.get('pending_request') and bs.get('last_witness_accept_utc_ns'):
            max_w=max(15,int(bs.get('tick_seconds',300))*2)
            if now-int(bs['last_witness_accept_utc_ns'])>max_w*1_000_000_000: errs.append('RESUME_WITNESS_GAP_EXCEEDED')
    return errs

def _propagate_failure(data,reason):
    try: bs=base._repair_state_head(data)
    except Exception: bs=_base_state(data)
    xs=list(bs.get('invalid_reasons') or []); tag='V1015_3:'+reason
    if tag not in xs: xs.append(tag)
    bs['invalid_reasons']=xs; bs['phase']='FAILED'; _write_base_state(data,bs)

def _requests(data):
    rows=[]; seen=set()
    dirs=[Path(data)/'v1014_4'/'witness_requests',Path(data)/'v1015_2'/'witness_outbox']
    for d in dirs:
        if not d.is_dir(): continue
        for p in sorted(d.glob('*.json')):
            try: x=_read(p)
            except Exception: continue
            k=x.get('request_sha256') or sha_obj(x)
            if k not in seen: rows.append(x); seen.add(k)
    return rows

def _receipts(data):
    rows=[]; seen=set(); d=Path(data)/'v1015_2'/'witness_receipts'
    if d.is_dir():
        for p in sorted(d.glob('*.json')):
            try:x=_read(p)
            except Exception:continue
            k=(x.get('payload') or {}).get('request_sha256') or sha_obj(x)
            if k not in seen: rows.append(x);seen.add(k)
    return rows

def _read_jsonl(path):
    p=Path(path); out=[]
    if not p.is_file(): return out
    for line in p.read_text(encoding='utf-8').splitlines():
        if line.strip():
            try: out.append(json.loads(line))
            except Exception: out.append({'_malformed':True})
    return out

def _campaign_events(data):
    d=Path(data)/'v1014_4'/'events'; out=[]
    if d.is_dir():
        for p in sorted(d.glob('*.json')):
            try:out.append(_read(p))
            except Exception:out.append({'_malformed':p.name})
    return out

def _base_events(data):
    d=Path(data)/'v1015_2'/'events';out=[]
    if d.is_dir():
        for p in sorted(d.glob('*.json')):
            try:out.append(_read(p))
            except Exception:out.append({'_malformed':p.name})
    return out

def _make_failure_bundle(data,st):
    data=Path(data); obj={
        'schema':FAILURE_SCHEMA,'version':VERSION,'terminal_state':'FAILED','failure_reasons':list(st.get('failure_reasons') or []),
        'release_binding':st.get('release_binding'),'resume_state':st,'resume_events':_scan_events(data),
        'execution_state':_read(base.state_path(data)) if base.state_path(data).is_file() else None,'execution_events':_base_events(data),
        'campaign_state':_read(data/'v1014_4'/'CAMPAIGN_STATE.json') if (data/'v1014_4'/'CAMPAIGN_STATE.json').is_file() else None,
        'campaign_events':_campaign_events(data),
        'realtime_state':_read(data/'v1013'/'REALTIME_RUN.json') if (data/'v1013'/'REALTIME_RUN.json').is_file() else None,
        'realtime_events':_read_jsonl(data/'v1013'/'REALTIME_EVENTS.jsonl'),
        'realtime_public_key':(data/'v1013'/'realtime.pub').read_text(encoding='utf-8').strip() if (data/'v1013'/'realtime.pub').is_file() else None,
        'witness_requests':_requests(data),'witness_receipts':_receipts(data),
        'claim_boundary':{'protocol_success':False,'24h_completed':False,'72h_completed':False,'7day_completed':False,
                          'failure_bundle_is_not_success_evidence':True,'terminal_failure_is_irreversible':True}
    }
    obj['bundle_sha256']=sha_obj(obj); p=failure_path(data); p.parent.mkdir(parents=True,exist_ok=True); atomic_write_bytes(p,canon(obj)+b'\n'); return p

def _terminal_fail(data,st,reasons):
    reasons=[str(x) for x in reasons if x]
    xs=list(st.get('failure_reasons') or [])
    for r in reasons:
        if r not in xs: xs.append(r)
    st['failure_reasons']=xs; st['terminal_state']='FAILED'; atomic_write_json(state_path(data),st)
    for r in reasons: _propagate_failure(data,r)
    ev,st=_append(data,'TERMINAL_FAILURE',{'reasons':reasons},st)
    p=_make_failure_bundle(data,st); st=_repair(data); st['failure_evidence']=str(p); atomic_write_json(state_path(data),st)
    return st

def _preflight(data,note=''):
    st=_ensure(data)
    if st.get('terminal_state')=='FAILED': return st,['TERMINAL_FAILURE_ALREADY_RECORDED']
    berr,_=_binding_errors(st.get('release_binding') or {})
    st,resumed=_touch_session(data,st,note)
    gaps=_deadline_failures(data)
    errs=berr+gaps
    if errs: st=_terminal_fail(data,st,errs)
    return st,errs

def start(data,profile='24h',target_seconds=None,tick_seconds=300,checkpoint_seconds=3600,witness_seconds=None,living_seconds=3600,note=''):
    r=base.start(data,profile,target_seconds,tick_seconds,checkpoint_seconds,witness_seconds,living_seconds,note)
    st=_ensure(data); ev,st=_append(data,'EXECUTION_BOUND_TO_RELEASE',{'base_result':r,'release_binding':st['release_binding']},st)
    out=dict(r); out.update({'version':VERSION,'resume_layer':True,'release_binding':st['release_binding'],'runner_session_count':st['session_count']}); return out

def resume(data,witness_trust_file=None,note=''):
    st,errs=_preflight(data,note or 'explicit resume')
    if errs or st.get('terminal_state')=='FAILED':
        return {'ok':False,'version':VERSION,'terminal_state':'FAILED','errors':errs or st.get('failure_reasons',[]),'failure_evidence':st.get('failure_evidence')}
    bs=_base_state(data)
    ev,st=_append(data,'RESUME_CHECKPOINT',{'base_phase':bs.get('phase'),'base_event_head':bs.get('event_head_sha256'),'note':str(note)[:240]},st)
    return {'ok':True,'version':VERSION,'terminal_state':st['terminal_state'],'phase':bs.get('phase'),'run_id':bs.get('run_id'),
            'runner_session_count':st.get('session_count'),'resume_count':st.get('resume_count'),'event_seq':ev['seq']}

def pump(data,note=''):
    st,errs=_preflight(data,note or 'pump')
    if errs or st.get('terminal_state')=='FAILED': return {'ok':False,'version':VERSION,'phase':'FAILED','errors':errs or st.get('failure_reasons',[]),'failure_evidence':st.get('failure_evidence')}
    r=base.pump(data,note)
    if r.get('phase')=='FAILED' or r.get('invalid_reasons') or not r.get('ok',False):
        reasons=['BASE_EXECUTION_FAILED']+list(r.get('invalid_reasons') or [])
        st=_terminal_fail(data,_repair(data),reasons)
    elif r.get('phase')=='PROTOCOL_COMPLETE':
        st=_repair(data); st['terminal_state']='SUCCEEDED'; atomic_write_json(state_path(data),st); _,st=_append(data,'TERMINAL_SUCCESS',{'base_phase':r.get('phase')},st)
    out=dict(r); out['version']=VERSION; out['terminal_state']=_repair(data).get('terminal_state'); return out

def accept_witness(data,receipt,witness_trust_file):
    st,errs=_preflight(data,'accept witness')
    if errs or st.get('terminal_state')=='FAILED': return {'ok':False,'version':VERSION,'phase':'FAILED','errors':errs or st.get('failure_reasons',[]),'failure_evidence':st.get('failure_evidence')}
    r=base.accept_witness(data,receipt,witness_trust_file)
    if not r.get('ok',False) and r.get('phase')=='FAILED': st=_terminal_fail(data,_repair(data),['BASE_WITNESS_FINALIZATION_FAILED'])
    elif r.get('phase')=='PROTOCOL_COMPLETE':
        st=_repair(data); st['terminal_state']='SUCCEEDED'; atomic_write_json(state_path(data),st); _,st=_append(data,'TERMINAL_SUCCESS',{'base_phase':'PROTOCOL_COMPLETE'},st)
    out=dict(r); out['version']=VERSION; out['terminal_state']=_repair(data).get('terminal_state'); return out

def abort(data,reason='OPERATOR_ABORT'):
    st=_ensure(data)
    if st.get('terminal_state')=='SUCCEEDED': return {'ok':False,'version':VERSION,'errors':['ALREADY_SUCCEEDED_CANNOT_ABORT']}
    if st.get('terminal_state')!='FAILED': st=_terminal_fail(data,st,['OPERATOR_ABORT:'+str(reason)[:200]])
    return {'ok':True,'version':VERSION,'terminal_state':'FAILED','failure_reasons':st.get('failure_reasons'),'failure_evidence':st.get('failure_evidence')}

def _chain_errors(events,schema,state_count=None,state_head=None,prefix='EVENT'):
    errs=[];prev=ZERO
    for i,ev in enumerate(events,1):
        if ev.get('_malformed'): errs.append(f'{prefix}_MALFORMED:{i}'); continue
        if ev.get('schema')!=schema or int(ev.get('seq',-1))!=i: errs.append(f'{prefix}_SCHEMA_SEQ:{i}')
        if ev.get('previous_event_sha256')!=prev: errs.append(f'{prefix}_CHAIN:{i}')
        prev=sha_obj(ev)
    if state_count is not None and int(state_count)!=len(events): errs.append(prefix+'_STATE_COUNT')
    if state_head is not None and state_head!=prev: errs.append(prefix+'_STATE_HEAD')
    return errs,prev

def _verify_failure_receipts(obj,witness_trust_file):
    errs=[]; receipts=obj.get('witness_receipts') or []
    if not receipts: return errs
    if not witness_trust_file: return ['WITNESS_TRUST_REQUIRED_FOR_FAILURE_AUDIT']
    try:
        trust=Path(witness_trust_file).read_text(encoding='utf-8').strip(); pk=Ed25519PublicKey.from_public_bytes(base64.b64decode(trust,validate=True))
    except Exception:return ['WITNESS_TRUST_INVALID']
    reqs={r.get('request_sha256'):r for r in (obj.get('witness_requests') or []) if r.get('request_sha256')}
    revs=obj.get('realtime_events') or []; heads=[sha_obj(e) for e in revs if isinstance(e,dict) and not e.get('_malformed')]
    for i,r in enumerate(receipts,1):
        try:
            if r.get('public_key')!=trust: raise ValueError('TRUST')
            p=r['payload']; pk.verify(base64.b64decode(r['signature'],validate=True),canon(p)); seq=int(p.get('seq',0))
            if seq<1 or seq>len(heads) or heads[seq-1]!=p.get('head_sha256'): raise ValueError('HEAD')
            rq=reqs.get(p.get('request_sha256'))
            if not rq or rq.get('head_sha256')!=p.get('head_sha256') or int(rq.get('seq',0))!=seq: raise ValueError('REQUEST')
        except Exception as e: errs.append(f'WITNESS_INVALID:{i}:{e}')
    return errs

def failure_audit(evidence,witness_trust_file=None):
    errs=[]
    try: obj=_read(evidence)
    except Exception as e:return {'ok':False,'version':VERSION,'schema':FAILURE_AUDIT_SCHEMA,'errors':['FAILURE_EVIDENCE_MALFORMED:'+type(e).__name__]}
    if obj.get('schema')!=FAILURE_SCHEMA: errs.append('FAILURE_SCHEMA')
    z=dict(obj); got=z.pop('bundle_sha256',None)
    if got!=sha_obj(z): errs.append('FAILURE_BUNDLE_HASH')
    if obj.get('terminal_state')!='FAILED' or not obj.get('failure_reasons'): errs.append('FAILURE_TERMINAL_STATE')
    cb=obj.get('claim_boundary') or {}
    if any(cb.get(k) for k in ('protocol_success','24h_completed','72h_completed','7day_completed')): errs.append('FAILURE_BUNDLE_SUCCESS_CLAIM')
    rs=obj.get('resume_state') or {}; re=obj.get('resume_events') or []
    x,_=_chain_errors(re,EVENT_SCHEMA,rs.get('event_count'),rs.get('event_head_sha256'),'RESUME_EVENT'); errs+=x
    es=obj.get('execution_state') or {}; ee=obj.get('execution_events') or []
    x,_=_chain_errors(ee,base.EVENT_SCHEMA,es.get('event_count'),es.get('event_head_sha256'),'EXECUTION_EVENT'); errs+=x
    # Realtime signed chain and receipt bindings are independently rechecked where present.
    revs=obj.get('realtime_events') or []; pub=obj.get('realtime_public_key'); prev=ZERO
    if revs and pub:
        try: pk=Ed25519PublicKey.from_public_bytes(base64.b64decode(pub,validate=True))
        except Exception: pk=None; errs.append('REALTIME_PUBLIC_KEY')
        for i,env in enumerate(revs,1):
            try:
                p=env['payload']
                if pk is None: raise ValueError('KEY')
                pk.verify(base64.b64decode(env['signature'],validate=True),canon(p))
                if int(p.get('seq',-1))!=i or p.get('previous_event_sha256')!=prev: raise ValueError('CHAIN')
                prev=sha_obj(env)
            except Exception as e: errs.append(f'REALTIME_EVENT_INVALID:{i}:{e}')
        rs2=obj.get('realtime_state') or {}
        if int(rs2.get('last_event_seq',-1))!=len(revs) or rs2.get('last_event_sha256')!=prev: errs.append('REALTIME_STATE_HEAD')
    errs+=_verify_failure_receipts(obj,witness_trust_file)
    return {'ok':not errs,'version':VERSION,'schema':FAILURE_AUDIT_SCHEMA,'errors':errs,'failure_reasons':obj.get('failure_reasons',[]),
            'terminal_state':obj.get('terminal_state'),'claim_boundary':{'protocol_success':False,'24h_completed':False,'72h_completed':False,'7day_completed':False,
            'failure_evidence_is_auditable_not_successful':True}}

def audit(data,witness_trust_file=None):
    data=Path(data)
    if not state_path(data).is_file(): return {'ok':False,'version':VERSION,'errors':['RESUME_LAYER_MISSING']}
    st=_repair(data); errs=[]
    be,_=_binding_errors(st.get('release_binding') or {}); errs+=be
    evs=_scan_events(data); x,_=_chain_errors(evs,EVENT_SCHEMA,st.get('event_count'),st.get('event_head_sha256'),'RESUME_EVENT'); errs+=x
    ba=base.audit(data,witness_trust_file)
    if st.get('terminal_state')=='FAILED':
        fp=st.get('failure_evidence'); fa=failure_audit(fp,witness_trust_file) if fp else {'ok':False,'errors':['FAILURE_EVIDENCE_MISSING']}
        if not fa.get('ok'): errs += ['FAILURE_AUDIT:'+x for x in fa.get('errors',[])]
        return {'ok':False,'record_ok':not errs,'protocol_success':False,'version':VERSION,'errors':errs,'terminal_state':'FAILED','failure_reasons':st.get('failure_reasons',[]),
                'failure_evidence':fp,'failure_audit':fa,'base_audit':ba,'claim_boundary':{'24h_completed':False,'72h_completed':False,'7day_completed':False}}
    if not ba.get('ok'): errs += ['BASE_AUDIT:'+x for x in ba.get('errors',[])]
    success=bool(st.get('terminal_state')=='SUCCEEDED' and ba.get('ok'))
    claims=(ba.get('claim_boundary') or {}) if success else {}
    return {'ok':not errs,'record_ok':not errs,'protocol_success':success,'version':VERSION,'errors':errs,'terminal_state':st.get('terminal_state'),
            'runner_sessions':st.get('session_count'),'resume_count':st.get('resume_count'),'release_binding':st.get('release_binding'),'base_audit':ba,
            'claim_boundary':{k:bool(claims.get(k,False)) for k in ('24h_completed','72h_completed','7day_completed')}}

def status(data,witness_trust_file=None):
    st=_repair(data); return {'ok':True,'version':VERSION,'state':st,'audit':audit(data,witness_trust_file)}
