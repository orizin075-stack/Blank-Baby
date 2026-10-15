from __future__ import annotations
import base64,json,os
from datetime import datetime,timezone
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey
from tukuyo_v977.whole_state import canon,sha_obj,_live_identity,audit as whole_audit,quick_audit as whole_quick_audit,state_path as whole_state_path,soul_path
from tukuyo_v978.heart_loop import audit as heart_audit,state_path as heart_state_path
from tukuyo_v979.deep_core import audit as deep_audit,path as deep_path
from tukuyo_common.atomic_fs import atomic_write_bytes

SCHEMA='tukuyo.v982.continuity_checkpoint/1';ZERO='0'*64

def root(data):return Path(data)/'v982'
def _key_paths(data):return root(data)/'private'/'continuity.key',root(data)/'continuity.pub'
def _read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def _write(p,o):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);atomic_write_bytes(p,canon(o)+b'\n')
def _file_sha(p):p=Path(p);return __import__('hashlib').sha256(p.read_bytes()).hexdigest() if p.is_file() else None

def _ensure_key(data):
    skp,pkp=_key_paths(data);skp.parent.mkdir(parents=True,exist_ok=True)
    if skp.exists() and pkp.exists():return skp.read_text().strip(),pkp.read_text().strip()
    sk=Ed25519PrivateKey.generate();a=base64.b64encode(sk.private_bytes_raw()).decode();b=base64.b64encode(sk.public_key().public_bytes_raw()).decode()
    skp.write_text(a);os.chmod(skp,0o600);pkp.write_text(b);return a,b

def _components(data):
    return {'whole_state':_file_sha(whole_state_path(data)),'soul_core':_file_sha(soul_path(data)),'heart_state':_file_sha(heart_state_path(data)),'deep_soul_core':_file_sha(deep_path(data))}

def checkpoint(data,note=''):
    if len(str(note))>240:raise ValueError('CONTINUITY_NOTE_TOO_LONG')
    wa=whole_quick_audit(data);ha=heart_audit(data);da=deep_audit(data)
    if not wa.get('ok') or not ha.get('ok') or not da.get('ok'):raise ValueError('CONTINUITY_PRECHECK_FAILED')
    ident=_live_identity(data);d=root(data)/'checkpoints';d.mkdir(parents=True,exist_ok=True);hp=root(data)/'HEAD.json'
    if hp.is_file():
        h=_read(hp);last_seq=int(h.get('seq',0));prev=str(h.get('checkpoint_sha256',ZERO));last=d/f'{last_seq:08d}.json'
        if last_seq<1 or not last.is_file() or sha_obj(_read(last))!=prev:raise ValueError('CONTINUITY_HEAD_DIVERGED')
        seq=last_seq+1
    else:
        seq=1;prev=ZERO
    payload={'schema':SCHEMA,'seq':seq,'identity':ident,'previous_checkpoint_sha256':prev,'components':_components(data),
      'observed_utc_unanchored':datetime.now(timezone.utc).isoformat(),'note':str(note),
      'claim_boundary':{'process_restart_continuity':True,'external_time_anchor':False,'long_wallclock_proven':False,'consciousness_established':False}}
    sk64,pub=_ensure_key(data);sk=Ed25519PrivateKey.from_private_bytes(base64.b64decode(sk64));env={'payload':payload,'public_key':pub,'signature':base64.b64encode(sk.sign(canon(payload))).decode()}
    _write(d/f'{seq:08d}.json',env);_write(root(data)/'HEAD.json',{'seq':seq,'checkpoint_sha256':sha_obj(env)})
    return {'ok':True,'version':'v982','seq':seq,'checkpoint_sha256':sha_obj(env),'observed_utc_unanchored':payload['observed_utc_unanchored']}

def quick_audit(data,require_current=False):
    errs=[];d=root(data)/'checkpoints';hp=root(data)/'HEAD.json'
    if not hp.is_file():return {'ok':False,'version':'v1014.4','errors':['HEAD_MISSING'],'checkpoints':0}
    try:
        h=_read(hp);seq=int(h.get('seq',0));head=str(h.get('checkpoint_sha256',ZERO));p=d/f'{seq:08d}.json'
        if seq<1 or not p.is_file():errs.append('LATEST_MISSING')
        else:
            env=_read(p);q=env['payload'];pub=_key_paths(data)[1].read_text().strip();pk=Ed25519PublicKey.from_public_bytes(base64.b64decode(pub,validate=True))
            if env.get('public_key')!=pub:errs.append('PUBKEY')
            try:pk.verify(base64.b64decode(env['signature'],validate=True),canon(q))
            except Exception:errs.append('SIGNATURE')
            if q.get('schema')!=SCHEMA or int(q.get('seq',-1))!=seq:errs.append('SCHEMA_SEQ')
            if sha_obj(env)!=head:errs.append('HEAD_HASH')
            if q.get('identity')!=_live_identity(data):errs.append('IDENTITY')
            if require_current and q.get('components')!=_components(data):errs.append('CURRENT_STATE_DIVERGED_FROM_CHECKPOINT')
    except Exception as e:errs.append('MALFORMED:'+type(e).__name__)
    return {'ok':not errs,'version':'v1014.4','errors':errs,'checkpoints':seq if 'seq' in locals() else 0,'head_sha256':head if 'head' in locals() else ZERO}

def export_anchor(data,out):
    r=audit(data)
    if not r.get('ok'):raise ValueError('CONTINUITY_AUDIT_REQUIRED')
    ident=_live_identity(data);pub=_key_paths(data)[1].read_text().strip();a={'schema':'tukuyo.v982.external_anchor/1','identity':ident,'seq':r['checkpoints'],'head_sha256':r['head_sha256'],'public_key':pub}
    a['anchor_sha256']=sha_obj(a);_write(out,a);return {'ok':True,'version':'v982','anchor_file':str(out),'anchor_sha256':a['anchor_sha256'],'seq':a['seq']}

def audit(data,require_current=False,anchor_file=None):
    errs=[];d=root(data)/'checkpoints';files=sorted(d.glob('*.json')) if d.exists() else []
    if not files:return {'ok':False,'version':'v982','errors':['NO_CONTINUITY_CHECKPOINTS'],'checkpoints':0}
    try:pub=_key_paths(data)[1].read_text().strip();pk=Ed25519PublicKey.from_public_bytes(base64.b64decode(pub,validate=True))
    except Exception as e:return {'ok':False,'version':'v982','errors':['KEY:'+type(e).__name__],'checkpoints':len(files)}
    prev=ZERO;last=None;times=[]
    for i,p in enumerate(files,1):
        try:
            env=_read(p);q=env['payload'];sig=base64.b64decode(env['signature'],validate=True)
            if env.get('public_key')!=pub:errs.append(f'PUBKEY:{i}')
            try:pk.verify(sig,canon(q))
            except Exception:errs.append(f'SIGNATURE:{i}')
            if q.get('schema')!=SCHEMA or q.get('seq')!=i:errs.append(f'SCHEMA_SEQ:{i}')
            if q.get('previous_checkpoint_sha256')!=prev:errs.append(f'CHAIN:{i}')
            if q.get('identity')!=_live_identity(data):errs.append(f'IDENTITY:{i}')
            times.append(q.get('observed_utc_unanchored'));prev=sha_obj(env);last=q
        except Exception as e:errs.append(f'MALFORMED:{i}:{type(e).__name__}')
    hp=root(data)/'HEAD.json'
    if not hp.exists():errs.append('HEAD_MISSING')
    else:
        h=_read(hp)
        if h.get('seq')!=len(files) or h.get('checkpoint_sha256')!=prev:errs.append('HEAD_MISMATCH')
    if require_current and last and last.get('components')!=_components(data):errs.append('CURRENT_STATE_DIVERGED_FROM_CHECKPOINT')
    external=False
    if anchor_file is not None:
        external=True
        try:
            a=_read(anchor_file);z=dict(a);got=z.pop('anchor_sha256',None)
            if a.get('schema')!='tukuyo.v982.external_anchor/1' or got!=sha_obj(z):errs.append('EXTERNAL_ANCHOR_HASH')
            if a.get('identity')!=_live_identity(data):errs.append('EXTERNAL_ANCHOR_IDENTITY')
            if a.get('public_key')!=pub:errs.append('EXTERNAL_ANCHOR_KEY')
            if a.get('seq')!=len(files) or a.get('head_sha256')!=prev:errs.append('EXTERNAL_ANCHOR_HEAD')
        except Exception as e:errs.append('EXTERNAL_ANCHOR_MALFORMED:'+type(e).__name__)
    return {'ok':not errs,'version':'v982','errors':errs,'checkpoints':len(files),'head_sha256':prev,'observed_times_unanchored':times,
      'claim_boundary':{'process_restart_continuity':True,'cryptographic_checkpoint_chain':True,'external_integrity_anchor_verified':external,'external_time_anchor':False,'long_wallclock_proven':False,'consciousness_established':False}}

def resume(data,anchor_file=None):
    r=audit(data,require_current=True,anchor_file=anchor_file);r['resume']='PASS' if r['ok'] else 'BLOCKED';return r
