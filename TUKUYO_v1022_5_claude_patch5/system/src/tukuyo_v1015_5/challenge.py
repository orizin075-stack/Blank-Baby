from __future__ import annotations
import base64,hashlib,json,time
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from tukuyo_common.atomic_fs import atomic_write_json,atomic_write_bytes
from tukuyo_v977.whole_state import canon,sha_obj
from tukuyo_v1015_3 import endurance_resume as resume
from tukuyo_v1015_2 import endurance_execution as execution
from tukuyo_v1015_4 import reproduction

VERSION='v1015.5'
CHALLENGE_SCHEMA='tukuyo.v1015_5.challenge/1'
PAYLOAD_SCHEMA='tukuyo.v1015_5.challenge_payload/1'
STATE_SCHEMA='tukuyo.v1015_5.challenge_state/1'
PORTABLE_SCHEMA='tukuyo.v1015_5.challenge_reproduction_bundle/1'

def _read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def _sha_bytes(b):return hashlib.sha256(b).hexdigest()
def _key_text(path):return Path(path).read_text(encoding='utf-8').strip()
def _package_root():return Path(__file__).resolve().parents[2]
def state_path(data):return Path(data)/'v1015_5'/'CHALLENGE_STATE.json'

def current_manifest_sha256():
    return _sha_bytes((_package_root()/'META'/'RELEASE_MANIFEST.json').read_bytes())

def verify_challenge(challenge_file,challenge_trust_file,profile=None,now_ns=None):
    errs=[];cf=Path(challenge_file);tf=Path(challenge_trust_file)
    try:obj=_read(cf)
    except Exception as e:return {'ok':False,'version':VERSION,'errors':['CHALLENGE_MALFORMED:'+type(e).__name__]}
    try:
        trust=_key_text(tf);kb=base64.b64decode(trust,validate=True);pk=Ed25519PublicKey.from_public_bytes(kb)
    except Exception as e:return {'ok':False,'version':VERSION,'errors':['CHALLENGE_TRUST_INVALID:'+type(e).__name__]}
    p=obj.get('payload') or {}
    if obj.get('schema')!=CHALLENGE_SCHEMA:errs.append('CHALLENGE_SCHEMA')
    if p.get('schema')!=PAYLOAD_SCHEMA:errs.append('CHALLENGE_PAYLOAD_SCHEMA')
    if obj.get('public_key')!=trust:errs.append('CHALLENGE_TRUST_ROOT_MISMATCH')
    try:pk.verify(base64.b64decode(obj.get('signature',''),validate=True),canon(p))
    except Exception:errs.append('CHALLENGE_SIGNATURE')
    nonce=str(p.get('nonce',''))
    if len(nonce)!=64:
        errs.append('CHALLENGE_NONCE_LENGTH')
    else:
        try:bytes.fromhex(nonce)
        except Exception:errs.append('CHALLENGE_NONCE_HEX')
    cid=p.get('challenge_id')
    z=dict(p);z.pop('challenge_id',None)
    exp_id=sha_obj(z)
    if cid!=exp_id:errs.append('CHALLENGE_ID')
    now=int(time.time_ns() if now_ns is None else now_ns)
    issued=int(p.get('issued_utc_ns',0) or 0);expires=int(p.get('expires_utc_ns',0) or 0)
    if issued<=0 or expires<=issued:errs.append('CHALLENGE_TIME_RANGE')
    if now<issued-5_000_000_000:errs.append('CHALLENGE_NOT_YET_VALID')
    if now>=expires:errs.append('CHALLENGE_EXPIRED')
    if profile and p.get('profile')!=profile:errs.append('CHALLENGE_PROFILE_MISMATCH')
    if p.get('release_manifest_sha256')!=current_manifest_sha256():errs.append('CHALLENGE_RELEASE_MISMATCH')
    raw=cf.read_bytes()
    binding={'challenge_id':cid,'challenge_payload_sha256':sha_obj(p),'challenge_envelope_sha256':_sha_bytes(raw),
             'challenge_public_key_sha256':hashlib.sha256(trust.encode()).hexdigest(),'profile':p.get('profile'),
             'issued_utc_ns':issued,'expires_utc_ns':expires,'release_manifest_sha256':p.get('release_manifest_sha256')}
    return {'ok':not errs,'version':VERSION,'errors':errs,'challenge':obj,'binding':binding,'trust_public_key':trust}

def start(data,challenge_file,challenge_trust_file,profile='24h',target_seconds=None,tick_seconds=300,checkpoint_seconds=3600,witness_seconds=None,living_seconds=3600,note=''):
    a=verify_challenge(challenge_file,challenge_trust_file,profile)
    if not a.get('ok'):return a
    r=resume.start(data,profile,target_seconds,tick_seconds,checkpoint_seconds,witness_seconds,living_seconds,note or 'v1015.5 challenged endurance start')
    if not r.get('ok'):return r
    b=a['binding']
    br=execution.install_challenge_binding(data,b)
    rs=json.loads(resume.state_path(data).read_text(encoding='utf-8'));rs['challenge_binding']=b;atomic_write_json(resume.state_path(data),rs)
    _,rs=resume._append(data,'EXTERNAL_CHALLENGE_BOUND',{'challenge_binding':b},rs)
    root=state_path(data).parent;root.mkdir(parents=True,exist_ok=True)
    st={'schema':STATE_SCHEMA,'version':VERSION,'run_id':r.get('run_id'),'profile':profile,'challenge_binding':b,
        'challenge_envelope':a['challenge'],'challenge_public_key':a['trust_public_key'],'bound_utc_ns':time.time_ns(),
        'start_witness_request_sha256':br.get('request_sha256'),'claim_boundary':{'challenge_must_predate_start_witness':True,'replay_of_prior_bundle_under_new_challenge_rejected':True}}
    atomic_write_json(state_path(data),st)
    out=dict(r);out.update({'version':VERSION,'challenge_binding':b,'start_witness_request':br.get('start_witness_request'),'challenge_bound':True})
    return out

def audit(data,challenge_trust_file=None):
    p=state_path(data);errs=[]
    if not p.is_file():return {'ok':False,'version':VERSION,'errors':['CHALLENGE_STATE_MISSING']}
    st=_read(p);b=st.get('challenge_binding') or {};es=_read(execution.state_path(data));rs=_read(resume.state_path(data))
    if es.get('challenge_binding')!=b:errs.append('EXECUTION_CHALLENGE_BINDING')
    if rs.get('challenge_binding')!=b:errs.append('RESUME_CHALLENGE_BINDING')
    if challenge_trust_file:
        tmp=p.parent/'_challenge_audit_tmp.json';atomic_write_bytes(tmp,canon(st.get('challenge_envelope'))+b'\n')
        try:a=verify_challenge(tmp,challenge_trust_file,st.get('profile'))
        finally:
            try:tmp.unlink()
            except Exception:pass
        if not a.get('ok'):errs.extend('CHALLENGE:'+x for x in a.get('errors',[]))
        elif a.get('binding')!=b:errs.append('CHALLENGE_BINDING_RECOMPUTE')
    return {'ok':not errs,'version':VERSION,'errors':errs,'challenge_binding':b,'run_id':st.get('run_id')}

def export_bundle(data,out,witness_trust_file,challenge_trust_file):
    a=audit(data,challenge_trust_file)
    if not a.get('ok'):raise ValueError('CHALLENGE_AUDIT_REQUIRED:'+','.join(a.get('errors',[])))
    out=Path(out);tmp=out.with_suffix(out.suffix+'.v1015_4.tmp')
    reproduction.export_bundle(data,tmp,witness_trust_file)
    base=_read(tmp)
    try:tmp.unlink()
    except Exception:pass
    st=_read(state_path(data));obj={'schema':PORTABLE_SCHEMA,'version':VERSION,'outcome':base.get('outcome'),
      'generated_utc_ns':time.time_ns(),'base_reproduction_bundle':base,'challenge_envelope':st.get('challenge_envelope'),
      'challenge_binding':st.get('challenge_binding'),'challenge_public_key':st.get('challenge_public_key'),
      'claim_boundary':{'portable_no_data_root_required':True,'fresh_external_challenge_required':True,'prior_bundle_replay_under_new_challenge_rejected':True,'human_third_party_reproduction_completed':False}}
    obj['bundle_sha256']=sha_obj(obj);out.parent.mkdir(parents=True,exist_ok=True);atomic_write_bytes(out,canon(obj)+b'\n')
    return {'ok':True,'version':VERSION,'outcome':obj['outcome'],'path':str(out),'bundle_sha256':obj['bundle_sha256'],'challenge_id':(obj.get('challenge_binding') or {}).get('challenge_id')}
