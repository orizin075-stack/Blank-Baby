from __future__ import annotations
import base64, json, os, time, uuid
from pathlib import Path
from datetime import datetime, timezone
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from tukuyo_v977.whole_state import canon, sha_obj, _live_identity, audit as whole_audit, quick_audit as whole_quick_audit, state_path as whole_state_path
from tukuyo_v989.temporal_identity import audit as identity_audit
from tukuyo_v982.continuity_ledger import checkpoint as continuity_checkpoint, audit as continuity_audit, quick_audit as continuity_quick_audit
from tukuyo_common.atomic_fs import atomic_write_bytes,atomic_write_text,atomic_write_json,durable_unlink,maybe_crash

SCHEMA='tukuyo.v1013.realtime_continuity/1'
EVENT_SCHEMA='tukuyo.v1013.realtime_event/1'
ANCHOR_SCHEMA='tukuyo.v1013.external_integrity_anchor/1'
WITNESS_REQ_SCHEMA='tukuyo.v1013.witness_request/1'
WITNESS_RECEIPT_SCHEMA='tukuyo.v1013.witness_receipt/1'
PENDING_SCHEMA='tukuyo.v1014_2.realtime_pending/1'
ZERO='0'*64
PROCESS_INSTANCE_ID=str(uuid.uuid4())
PROFILES={'24h':86400,'72h':259200,'7d':604800}

def root(data): return Path(data)/'v1013'
def state_path(data): return root(data)/'REALTIME_RUN.json'
def event_path(data): return root(data)/'REALTIME_EVENTS.jsonl'
def head_path(data): return root(data)/'REALTIME_EVENT_HEAD.json'
def pending_path(data): return root(data)/'private'/'REALTIME_PENDING.json'
def _key_paths(data): return root(data)/'private'/'realtime.key', root(data)/'realtime.pub'
def _read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def _write(p,o,crashpoint=None): atomic_write_bytes(p,canon(o)+b'\n',crashpoint=crashpoint)
def _file_sha(p):
    import hashlib
    p=Path(p);return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None

def _ensure_key(data):
    skp,pkp=_key_paths(data);skp.parent.mkdir(parents=True,exist_ok=True)
    if skp.exists():
        a=skp.read_text().strip()
        try:sk=Ed25519PrivateKey.from_private_bytes(base64.b64decode(a,validate=True))
        except Exception as e:raise ValueError('REALTIME_PRIVATE_KEY_INVALID:'+type(e).__name__)
        b=base64.b64encode(sk.public_key().public_bytes_raw()).decode()
        if pkp.exists() and pkp.read_text().strip()!=b:raise ValueError('REALTIME_KEYPAIR_MISMATCH')
        if not pkp.exists():atomic_write_text(pkp,b)
        os.chmod(skp,0o600);return a,b
    if pkp.exists():raise ValueError('REALTIME_PRIVATE_KEY_MISSING')
    sk=Ed25519PrivateKey.generate();a=base64.b64encode(sk.private_bytes_raw()).decode();b=base64.b64encode(sk.public_key().public_bytes_raw()).decode()
    atomic_write_text(skp,a,mode=0o600);atomic_write_text(pkp,b);return a,b

def _sign(data,payload):
    sk64,pub=_ensure_key(data);sk=Ed25519PrivateKey.from_private_bytes(base64.b64decode(sk64));return {'payload':payload,'public_key':pub,'signature':base64.b64encode(sk.sign(canon(payload))).decode()}

def _verify(env,pub):
    try:
        if env.get('public_key')!=pub:return False
        Ed25519PublicKey.from_public_bytes(base64.b64decode(pub,validate=True)).verify(base64.b64decode(env['signature'],validate=True),canon(env['payload']));return True
    except Exception:return False

def _events(data):
    p=event_path(data)
    if not p.is_file(): return []
    out=[]
    for line in p.read_text(encoding='utf-8').splitlines():
        if line.strip(): out.append(json.loads(line))
    return out

def _last_jsonl_env(path):
    p=Path(path)
    if not p.is_file() or p.stat().st_size==0:return None
    with p.open('rb') as f:
        f.seek(0,2);pos=f.tell();buf=b''
        while pos>0:
            step=min(8192,pos);pos-=step;f.seek(pos);buf=f.read(step)+buf
            lines=[x for x in buf.splitlines() if x.strip()]
            if len(lines)>=2 or (pos==0 and lines):
                try:return json.loads(lines[-1].decode('utf-8'))
                except Exception:return None
    return None

def quick_audit(data,subaudits=True):
    data=Path(data);errs=[]
    if not state_path(data).is_file():return {'ok':False,'version':'v1014.4','errors':['REALTIME_RUN_MISSING'],'events':0}
    try:st=_read(state_path(data));pub=_key_paths(data)[1].read_text().strip()
    except Exception:return {'ok':False,'version':'v1014.4','errors':['REALTIME_STATE_OR_KEY_MISSING'],'events':0}
    seq=int(st.get('last_event_seq',0));head=str(st.get('last_event_sha256',ZERO));hp=head_path(data)
    if not hp.is_file():errs.append('REALTIME_HEAD_MISSING')
    else:
        h=_read(hp)
        if int(h.get('seq',-1))!=seq or h.get('event_sha256')!=head:errs.append('REALTIME_HEAD_MISMATCH')
    if seq:
        env=_last_jsonl_env(event_path(data))
        if not env:errs.append('REALTIME_LAST_EVENT_MISSING')
        else:
            pl=env.get('payload',{})
            if sha_obj(env)!=head:errs.append('REALTIME_LAST_EVENT_HASH')
            if not _verify(env,pub):errs.append('REALTIME_LAST_EVENT_SIGNATURE')
            if int(pl.get('seq',-1))!=seq or pl.get('run_id')!=st.get('run_id'):errs.append('REALTIME_LAST_EVENT_BINDING')
            if pl.get('identity')!=st.get('identity'):errs.append('REALTIME_LAST_EVENT_IDENTITY')
    if subaudits:
        try:
            if not identity_audit(data).get('ok'):errs.append('TEMPORAL_IDENTITY_AUDIT')
            if not whole_audit(data).get('ok'):errs.append('WHOLE_AUDIT')
            if (data/'v982'/'HEAD.json').exists() and not continuity_quick_audit(data).get('ok'):errs.append('CONTINUITY_LEDGER_AUDIT')
        except Exception as e:errs.append('SUBAUDIT:'+type(e).__name__)
    return {'ok':not errs,'version':'v1014.4','errors':errs,'run_id':st.get('run_id'),'events':seq,'head_sha256':head,
            'local_elapsed_seconds':max(0.0,(time.time_ns()-int(st.get('started_utc_ns',time.time_ns())))/1e9),
            'distinct_process_instances':int(st.get('distinct_process_instances',0))}

def repair(data):
    """Complete or safely abandon a realtime operation interrupted by process death."""
    data=Path(data);pp=pending_path(data)
    if not pp.is_file():return {'ok':True,'version':'v1014.2','repaired':False}
    tx=_read(pp)
    if tx.get('schema')!=PENDING_SCHEMA:raise ValueError('REALTIME_PENDING_SCHEMA')
    phase=tx.get('phase')
    if phase=='PREPARING':
        # A continuity checkpoint may have committed, but the realtime event did not.
        # Keep that durable checkpoint and resync Whole State at startup.
        durable_unlink(pp);return {'ok':True,'version':'v1014.2','repaired':True,'action':'ABANDONED_UNCOMMITTED_EVENT'}
    if phase!='COMMITTING':raise ValueError('REALTIME_PENDING_PHASE')
    if not state_path(data).is_file():raise ValueError('REALTIME_PENDING_STATE_MISSING')
    env=tx['event_env'];line=canon(env)+b'\n';p=event_path(data);existing=p.read_bytes() if p.is_file() else b''
    target_hash=sha_obj(env);seq=int(env['payload']['seq']);previous_size=int(tx.get('previous_size',len(existing)))
    if len(existing)<previous_size:raise ValueError('REALTIME_PENDING_JOURNAL_TRUNCATED')
    prefix=existing[:previous_size];tail=existing[previous_size:]
    if tail==line:
        pass
    elif line.startswith(tail):
        # Interrupted append: restore the exact pre-append prefix, then durably append the canonical line.
        with p.open('wb') as f:f.write(prefix);f.flush();os.fsync(f.fileno())
        with p.open('ab') as f:f.write(line);f.flush();os.fsync(f.fileno())
    else:
        raise ValueError('REALTIME_PENDING_JOURNAL_DIVERGENCE')
    st=tx['new_state'];_write(head_path(data),{'schema':'tukuyo.v1013.realtime_head/1','run_id':st['run_id'],'seq':seq,'event_sha256':target_hash});_write(state_path(data),st)
    durable_unlink(pp);return {'ok':True,'version':'v1014.2','repaired':True,'action':'COMPLETED_PENDING_EVENT','seq':seq}

def _append(data,kind,note=''):
    st=_read(state_path(data));seq=int(st.get('last_event_seq',0))+1;prev=str(st.get('last_event_sha256',ZERO))
    ia=identity_audit(data);wa=whole_quick_audit(data)
    if not ia.get('ok') or not wa.get('ok'): raise ValueError('REALTIME_PRECHECK_FAILED')
    _write(pending_path(data),{'schema':PENDING_SCHEMA,'phase':'PREPARING','kind':kind,'seq':seq,'created_utc_ns':time.time_ns()})
    try:
        cc=continuity_checkpoint(data,f'v1013:{kind}:{seq}');cseq=cc.get('seq');chead=cc.get('checkpoint_sha256')
    except Exception:
        cseq=None;chead=None
    now_ns=time.time_ns()
    payload={'schema':EVENT_SCHEMA,'run_id':st['run_id'],'seq':seq,'kind':kind,'note':str(note)[:240],
      'identity':_live_identity(data),'process_instance_id':PROCESS_INSTANCE_ID,'observed_utc_ns':now_ns,
      'elapsed_local_seconds':max(0.0,(now_ns-int(st['started_utc_ns']))/1e9),'previous_event_sha256':prev,
      'whole_state_sha256':_file_sha(whole_state_path(data)),'temporal_identity':{
        'origin_soul_sha256':ia.get('origin_soul_sha256'),'current_soul_sha256':ia.get('current_soul_sha256'),
        'transition_count':ia.get('transition_count'),'transition_head_sha256':ia.get('transition_head_sha256')},
      'continuity_checkpoint_seq':cseq,'continuity_checkpoint_sha256':chead}
    env=_sign(data,payload);new_state=dict(st);new_state['last_event_seq']=seq;new_state['last_event_sha256']=sha_obj(env);new_state['last_observed_utc_ns']=now_ns
    prev_pi=st.get('last_process_instance_id');new_state['last_process_instance_id']=PROCESS_INSTANCE_ID
    new_state['distinct_process_instances']=max(1,int(st.get('distinct_process_instances',0)) + (1 if prev_pi and prev_pi!=PROCESS_INSTANCE_ID else 0))
    p=event_path(data);p.parent.mkdir(parents=True,exist_ok=True);previous_size=p.stat().st_size if p.is_file() else 0
    tx={'schema':PENDING_SCHEMA,'phase':'COMMITTING','kind':kind,'seq':seq,'event_env':env,'new_state':new_state,'previous_size':previous_size,'created_utc_ns':time.time_ns()};_write(pending_path(data),tx)
    line=canon(env)+b'\n'
    with p.open('ab') as f:
        if os.environ.get('TUKUYO_CRASH_POINT')=='realtime_event:mid_append':
            cut=max(1,len(line)//2);f.write(line[:cut]);f.flush();os.fsync(f.fileno());maybe_crash('realtime_event:mid_append')
        f.write(line);f.flush();os.fsync(f.fileno())
    maybe_crash('realtime:after_event')
    _write(head_path(data),{'schema':'tukuyo.v1013.realtime_head/1','run_id':st['run_id'],'seq':seq,'event_sha256':sha_obj(env)})
    _write(state_path(data),new_state);durable_unlink(pending_path(data));return payload

def start(data,profile='24h',target_seconds=None,note=''):
    if state_path(data).exists(): raise ValueError('REALTIME_RUN_ALREADY_EXISTS')
    if profile not in PROFILES and target_seconds is None: raise ValueError('UNKNOWN_REALTIME_PROFILE')
    target=PROFILES.get(profile) if target_seconds is None else int(target_seconds)
    if target<1: raise ValueError('REALTIME_TARGET_MIN_1S')
    ia=identity_audit(data);wa=whole_quick_audit(data)
    if not ia.get('ok') or not wa.get('ok'): raise ValueError('REALTIME_START_PRECHECK_FAILED')
    now=time.time_ns();ident=_live_identity(data);run_id=str(uuid.uuid4())
    st={'schema':SCHEMA,'version':'v1013','run_id':run_id,'profile':profile,'target_seconds':target,'identity':ident,
      'started_utc_ns':now,'started_utc':datetime.fromtimestamp(now/1e9,timezone.utc).isoformat(),'last_event_seq':0,
      'last_event_sha256':ZERO,'last_observed_utc_ns':now,'claim_boundary':{
        'local_clock_elapsed_is_not_external_time_proof':True,'external_witness_required_for_formal_duration_gate':True,
        'process_restart_continuity_harness':True,'literal_life_established':False,'consciousness_established':False}}
    _write(state_path(data),st);_ensure_key(data);p=_append(data,'START',note)
    return {'ok':True,'version':'v1013','run_id':run_id,'profile':profile,'target_seconds':target,'start_event':p,'externally_anchored_complete':False}

def tick(data,note=''):
    if not state_path(data).is_file(): raise ValueError('REALTIME_RUN_MISSING')
    p=_append(data,'TICK',note);return {'ok':True,'version':'v1013','seq':p['seq'],'elapsed_local_seconds':p['elapsed_local_seconds'],'process_instance_id':p['process_instance_id']}

def export_anchor(data,out):
    a=audit(data)
    if not a.get('ok'): raise ValueError('REALTIME_AUDIT_REQUIRED')
    st=_read(state_path(data));pub=_key_paths(data)[1].read_text().strip();obj={'schema':ANCHOR_SCHEMA,'run_id':st['run_id'],'identity':st['identity'],'seq':a['events'],'head_sha256':a['head_sha256'],'public_key':pub};obj['anchor_sha256']=sha_obj(obj);_write(out,obj);return {'ok':True,'version':'v1013','anchor_file':str(out),'anchor_sha256':obj['anchor_sha256'],'seq':obj['seq']}

def witness_request(data,out):
    a=audit(data)
    if not a.get('ok'): raise ValueError('REALTIME_AUDIT_REQUIRED')
    st=_read(state_path(data));obj={'schema':WITNESS_REQ_SCHEMA,'run_id':st['run_id'],'identity':st['identity'],'seq':a['events'],'head_sha256':a['head_sha256'],'requested_utc_ns':time.time_ns()};obj['request_sha256']=sha_obj(obj);_write(out,obj);return {'ok':True,'version':'v1013','request_file':str(out),'request_sha256':obj['request_sha256']}

def _load_witness(path,trust_file):
    r=_read(path);pub=Path(trust_file).read_text().strip();errs=[]
    try:
        if r.get('schema')!=WITNESS_RECEIPT_SCHEMA:errs.append('WITNESS_SCHEMA')
        if r.get('public_key')!=pub:errs.append('WITNESS_TRUST_ROOT')
        p=r['payload'];Ed25519PublicKey.from_public_bytes(base64.b64decode(pub,validate=True)).verify(base64.b64decode(r['signature'],validate=True),canon(p))
        if p.get('schema')!='tukuyo.v1013.witness_payload/1':errs.append('WITNESS_PAYLOAD_SCHEMA')
    except Exception as e:errs.append('WITNESS_INVALID:'+type(e).__name__)
    return r.get('payload',{}),errs

def audit(data,anchor_file=None,start_witness=None,end_witness=None,witness_trust_file=None,require_complete=False,subaudits=True):
    errs=[]
    if not state_path(data).is_file():return {'ok':False,'version':'v1013','errors':['REALTIME_RUN_MISSING'],'events':0}
    st=_read(state_path(data));evs=_events(data)
    try:pub=_key_paths(data)[1].read_text().strip()
    except Exception:return {'ok':False,'version':'v1013','errors':['REALTIME_KEY_MISSING'],'events':len(evs)}
    prev=ZERO;times=[];heads=[];procs=[]
    for i,env in enumerate(evs,1):
        p=env.get('payload',{})
        if not _verify(env,pub):errs.append(f'EVENT_SIGNATURE:{i}')
        if p.get('schema')!=EVENT_SCHEMA or p.get('seq')!=i or p.get('run_id')!=st.get('run_id'):errs.append(f'EVENT_SCHEMA_SEQ:{i}')
        if p.get('previous_event_sha256')!=prev:errs.append(f'EVENT_CHAIN:{i}')
        if p.get('identity')!=st.get('identity'):errs.append(f'EVENT_IDENTITY:{i}')
        t=int(p.get('observed_utc_ns',0));times.append(t);procs.append(p.get('process_instance_id'));prev=sha_obj(env);heads.append(prev)
    if any(b<a for a,b in zip(times,times[1:])):errs.append('LOCAL_CLOCK_REGRESSION')
    hp=head_path(data)
    if not hp.is_file():errs.append('REALTIME_HEAD_MISSING')
    else:
        h=_read(hp)
        if h.get('seq')!=len(evs) or h.get('event_sha256')!=prev:errs.append('REALTIME_HEAD_MISMATCH')
    if st.get('last_event_seq')!=len(evs) or st.get('last_event_sha256')!=prev:errs.append('REALTIME_STATE_HEAD_MISMATCH')
    if subaudits:
        try:
            if not identity_audit(data).get('ok'):errs.append('TEMPORAL_IDENTITY_AUDIT')
            if not whole_audit(data).get('ok'):errs.append('WHOLE_AUDIT')
            if (Path(data)/'v982'/'HEAD.json').exists() and not continuity_audit(data).get('ok'):errs.append('CONTINUITY_LEDGER_AUDIT')
        except Exception as e:errs.append('SUBAUDIT:'+type(e).__name__)
    if anchor_file is not None:
        try:
            a=_read(anchor_file);z=dict(a);got=z.pop('anchor_sha256',None)
            if a.get('schema')!=ANCHOR_SCHEMA or got!=sha_obj(z):errs.append('EXTERNAL_ANCHOR_HASH')
            if a.get('run_id')!=st.get('run_id') or a.get('identity')!=st.get('identity') or a.get('public_key')!=pub:errs.append('EXTERNAL_ANCHOR_BINDING')
            seq=int(a.get('seq',0))
            if seq<1 or seq>len(heads) or heads[seq-1]!=a.get('head_sha256'):errs.append('EXTERNAL_ANCHOR_ROLLBACK_OR_FORK')
        except Exception as e:errs.append('EXTERNAL_ANCHOR_MALFORMED:'+type(e).__name__)
    local_elapsed=max(0.0,((times[-1] if times else time.time_ns())-int(st['started_utc_ns']))/1e9)
    external_elapsed=None;externally_complete=False;witness_errors=[]
    if start_witness or end_witness or witness_trust_file:
        if not (start_witness and end_witness and witness_trust_file):witness_errors.append('WITNESS_PAIR_AND_TRUST_REQUIRED')
        else:
            sw,se=_load_witness(start_witness,witness_trust_file),_load_witness(end_witness,witness_trust_file)
            sp,serr=sw;ep,eerr=se;witness_errors+=serr+eerr
            for tag,p in [('START',sp),('END',ep)]:
                if p.get('run_id')!=st.get('run_id') or p.get('identity')!=st.get('identity'):witness_errors.append('WITNESS_'+tag+'_BINDING')
                seq=int(p.get('seq',0))
                if seq<1 or seq>len(heads) or heads[seq-1]!=p.get('head_sha256'):witness_errors.append('WITNESS_'+tag+'_HEAD')
            if not witness_errors:
                external_elapsed=(int(ep['witnessed_utc_ns'])-int(sp['witnessed_utc_ns']))/1e9
                if external_elapsed<0:witness_errors.append('WITNESS_TIME_REGRESSION')
                externally_complete=(not witness_errors and external_elapsed>=int(st['target_seconds']))
    errs.extend(witness_errors)
    completed_local=local_elapsed>=int(st['target_seconds'])
    if require_complete and not externally_complete:errs.append('FORMAL_DURATION_GATE_INCOMPLETE')
    return {'ok':not errs,'version':'v1013','errors':errs,'run_id':st['run_id'],'profile':st['profile'],'target_seconds':st['target_seconds'],
      'events':len(evs),'head_sha256':prev,'local_elapsed_seconds':round(local_elapsed,6),'local_clock_complete':completed_local,
      'distinct_process_instances':len(set(x for x in procs if x)),'external_witness_elapsed_seconds':external_elapsed,
      'externally_anchored_complete':externally_complete,'claim_boundary':{
        'local_clock_completion_is_not_formal_duration_proof':True,'formal_duration_requires_external_witness_pair':True,
        'restart_continuity_observed':len(set(x for x in procs if x))>=2,'literal_life_established':False,'consciousness_established':False}}

def status(data):return audit(data)
