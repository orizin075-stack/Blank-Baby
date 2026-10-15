"""Opt-in canonical history witness: one pinned shared ledger, not global identity."""
from __future__ import annotations
import base64,contextlib,contextvars,threading,uuid,json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from tukuyo_common.atomic_fs import atomic_write_bytes,maybe_crash
from tukuyo_v977 import whole_state as whole
from tukuyo_v1019.transaction import _writer_lock
NS='identity_ledger';COMPONENT='external_identity_binding';ZERO='0'*64
_locks={};_locks_lock=threading.Lock();_held=contextvars.ContextVar('identity_ledger_lock',default=None)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,obj):atomic_write_bytes(Path(p),whole.canon(obj)+b'\n')
def _outside(data,path):
    d=Path(data).resolve();p=Path(path).resolve()
    if p==d or p.is_relative_to(d) or d.is_relative_to(p):raise ValueError('IDENTITY_LEDGER_MUST_BE_OUTSIDE_INDIVIDUAL')
    return p
@contextlib.contextmanager
def locked(path):
    p=Path(path).resolve()
    if _held.get()==str(p):yield;return
    if not p.is_dir():raise ValueError('IDENTITY_LEDGER_UNAVAILABLE')
    with _locks_lock:lock=_locks.setdefault(str(p),threading.RLock())
    with lock:
        import fcntl
        with (p/'LOCK').open('a+b') as f:
            fcntl.flock(f.fileno(),fcntl.LOCK_EX);t=_held.set(str(p))
            try:yield
            finally:_held.reset(t);fcntl.flock(f.fileno(),fcntl.LOCK_UN)
def _sign(path,obj):
    k=Ed25519PrivateKey.from_private_bytes(base64.b64decode((Path(path)/'private/witness.key').read_text().strip(),validate=True))
    pub=base64.b64encode(k.public_key().public_bytes_raw()).decode()
    if pub!=(Path(path)/'witness.pub').read_text().strip():raise ValueError('IDENTITY_LEDGER_KEY_MISMATCH')
    return {'payload':obj,'public_key':pub,'signature':base64.b64encode(k.sign(whole.canon(obj))).decode()}
def create(path):
    p=Path(path).resolve()
    if p.exists():raise ValueError('IDENTITY_LEDGER_ALREADY_EXISTS')
    p.mkdir(parents=True);(p/'private').mkdir(mode=0o700)
    k=Ed25519PrivateKey.generate();pub=base64.b64encode(k.public_key().public_bytes_raw()).decode()
    atomic_write_bytes(p/'private/witness.key',base64.b64encode(k.private_bytes_raw())+b'\n',mode=0o600)
    atomic_write_bytes(p/'witness.pub',pub.encode()+b'\n');lid='identity-ledger-'+uuid.uuid4().hex
    write(p/'REGISTRY.json',_sign(p,{'schema':'tukuyo.identity_ledger.registry/1','ledger_id':lid}))
    atomic_write_bytes(p/'JOURNAL.jsonl',b'')
    write(p/'HEAD.json',_sign(p,{'schema':'tukuyo.identity_ledger.head/1','ledger_id':lid,'seq':0,'head_sha256':ZERO}))
    return {'ok':True,'ledger_id':lid,'trust_file':str(p/'witness.pub'),'real_world_witness_independence':False}
def _checked(env,pub):
    if not isinstance(env,dict) or set(env)!={'payload','public_key','signature'} or not whole._verify(env,pub):raise ValueError('IDENTITY_LEDGER_SIGNATURE')
    return env['payload']
def _load(path,trust):
    p=Path(path);pub=Path(trust).read_text().strip()
    if pub!=(p/'witness.pub').read_text().strip():raise ValueError('IDENTITY_LEDGER_TRUST_PIN')
    reg=_checked(read(p/'REGISTRY.json'),pub)
    if reg.get('schema')!='tukuyo.identity_ledger.registry/1':raise ValueError('IDENTITY_LEDGER_REGISTRY')
    raw=(p/'JOURNAL.jsonl').read_bytes()
    if raw and not raw.endswith(b'\n'):raise ValueError('IDENTITY_LEDGER_TRUNCATED_JOURNAL')
    rows=[json.loads(line) for line in raw.splitlines()];prev=ZERO
    for n,env in enumerate(rows,1):
        q=_checked(env,pub)
        if q.get('schema')!='tukuyo.identity_ledger.event/1' or q.get('ledger_id')!=reg['ledger_id'] or type(q.get('seq')) is not int or q['seq']!=n or q.get('previous')!=prev:raise ValueError('IDENTITY_LEDGER_CHAIN')
        prev=whole.sha_obj(env)
    head=_checked(read(p/'HEAD.json'),pub);pending=p/'PREPARED.json'
    if pending.exists():
        env=read(pending);q=_checked(env,pub)
        if q.get('ledger_id')!=reg['ledger_id'] or q.get('schema')!='tukuyo.identity_ledger.event/1':raise ValueError('IDENTITY_LEDGER_PREPARED')
        digest=whole.sha_obj(env)
        if q.get('seq')==len(rows)+1 and q.get('previous')==prev:
            atomic_write_bytes(p/'JOURNAL.jsonl',raw+whole.canon(env)+b'\n');rows.append(env);prev=digest
        elif not (rows and prev==digest and q.get('seq')==len(rows)):raise ValueError('IDENTITY_LEDGER_PREPARED_CONFLICT')
        write(p/'HEAD.json',_sign(p,{'schema':'tukuyo.identity_ledger.head/1','ledger_id':reg['ledger_id'],'seq':len(rows),'head_sha256':prev}))
        pending.unlink();head=_checked(read(p/'HEAD.json'),pub)
    if head!={'schema':'tukuyo.identity_ledger.head/1','ledger_id':reg['ledger_id'],'seq':len(rows),'head_sha256':prev}:raise ValueError('IDENTITY_LEDGER_HEAD')
    return reg,pub,rows,head
def _append(path,reg,rows,head,kind,key,snapshot,**extra):
    q={'schema':'tukuyo.identity_ledger.event/1','ledger_id':reg['ledger_id'],'seq':len(rows)+1,'previous':head['head_sha256'],'kind':kind,'identity_key':key,'snapshot':snapshot,**extra}
    env=_sign(path,q);write(Path(path)/'PREPARED.json',env);maybe_crash('identity_ledger:after_prepare')
    atomic_write_bytes(Path(path)/'JOURNAL.jsonl',(Path(path)/'JOURNAL.jsonl').read_bytes()+whole.canon(env)+b'\n');maybe_crash('identity_ledger:after_journal')
    write(Path(path)/'HEAD.json',_sign(path,{'schema':'tukuyo.identity_ledger.head/1','ledger_id':reg['ledger_id'],'seq':q['seq'],'head_sha256':whole.sha_obj(env)}))
    (Path(path)/'PREPARED.json').unlink();return env
def _latest(rows,key):return next((r for r in reversed(rows) if r['payload']['identity_key']==key and r['payload']['kind'] in ('ENROLL','ADVANCE','DEATH','BRANCH')),None)
def _identity_key(identity,pub):return whole.sha_obj({'identity':identity,'whole_public_key':pub})
def _registration_available(rows,snap):
    for row in rows:
        if row['payload']['kind'] not in ('ENROLL','ADVANCE','DEATH','BRANCH'):continue
        old=row['payload']['snapshot']
        if old['identity']['individual_id']==snap['identity']['individual_id'] or old['whole_public_key']==snap['whole_public_key']:raise ValueError('IDENTITY_LEDGER_ID_OR_KEY_ALREADY_REGISTERED')
def requires(data):
    if (Path(data)/NS).exists():return True
    p=whole.state_path(data)
    if not p.exists():return False
    try:return COMPONENT in read(p)['payload'].get('component_hashes',{})
    except (ValueError,KeyError):return True
def binding(data):
    p=Path(data)/NS/'BINDING.json'
    if not p.is_file():raise ValueError('IDENTITY_LEDGER_BINDING_MISSING')
    env=read(p);q=_checked(env,env.get('public_key'));pub=whole._key_paths(data)[1].read_text().strip()
    if q.get('schema')!='tukuyo.identity_ledger.binding/1' or q.get('identity')!=whole._live_identity(data) or q.get('whole_public_key')!=pub:raise ValueError('IDENTITY_LEDGER_BINDING')
    return env
def binding_audit(data):
    try:binding(data);return {'ok':True}
    except (ValueError,KeyError,OSError,TypeError) as e:return {'ok':False,'errors':[str(e)]}
def _snapshot(data):
    d=Path(data);a=whole.audit(d)
    if not a.get('ok'):raise ValueError('IDENTITY_LEDGER_LOCAL_AUDIT:'+','.join(a.get('errors',[])))
    env=read(whole.state_path(d));pub=whole._key_paths(d)[1].read_text().strip();identity=whole._live_identity(d)
    if not whole._verify(env,pub):raise ValueError('IDENTITY_LEDGER_WHOLE_SIGNATURE')
    from tukuyo_common.journal import load_events
    events=load_events(whole.event_path(d)) if whole.event_path(d).is_file() else []
    org=read(d/'v1007/ORGANISM2_STATE.json') if (d/'v1007/ORGANISM2_STATE.json').is_file() else {}
    dead=org.get('death_irreversible') or org.get('lifecycle')=='DEAD' or env['payload'].get('lifecycle')=='DEAD'
    return {'identity':identity,'whole_public_key':pub,'whole_head_sha256':whole.sha_obj(env),'soul_heads':[e['event_sha256'] for e in events],'lifecycle':'DEAD' if dead else 'ALIVE','local_proof':env,'global_unique_individual_proven':False}
def _local_receipt(data,pub):
    p=Path(data)/NS/'RECEIPT.json'
    if not p.is_file():raise ValueError('IDENTITY_LEDGER_RECEIPT_MISSING')
    env=read(p);_checked(env,pub);return env
def _preflight(data,reg,pub,rows,allow_ahead=False):
    b=binding(data)
    if b['public_key']!=pub or b['payload']['ledger_id']!=reg['ledger_id']:raise ValueError('IDENTITY_LEDGER_WRONG_LEDGER')
    key=_identity_key(b['payload']['identity'],b['payload']['whole_public_key']);last=_latest(rows,key)
    if not last:raise ValueError('IDENTITY_LEDGER_NOT_ENROLLED')
    snap=_snapshot(data)
    if last['payload']['snapshot']['lifecycle']=='DEAD' and snap['lifecycle']!='DEAD':raise ValueError('IDENTITY_LEDGER_DEAD_RESTORE')
    if _local_receipt(data,pub)!=last:
        old=last['payload']['snapshot']['soul_heads'];cur=snap['soul_heads']
        if cur[:len(old)]!=old and len(cur)>=len(old):reason='HISTORY_FORK'
        elif any(r['payload']['identity_key']==key and r['payload']['snapshot']['whole_head_sha256']==snap['whole_head_sha256'] for r in rows):reason='RESTORED_OR_ROLLED_BACK_HEAD'
        else:reason='STALE_COPY_OR_UNANCHORED_BRANCH'
        raise ValueError('IDENTITY_LEDGER_'+reason)
    if not allow_ahead and snap['whole_head_sha256']!=last['payload']['snapshot']['whole_head_sha256']:raise ValueError('IDENTITY_LEDGER_UNPUBLISHED_STATE:use identity-ledger-publish')
    old=last['payload']['snapshot']['soul_heads']
    if snap['soul_heads'][:len(old)]!=old:raise ValueError('IDENTITY_LEDGER_HISTORY_FORK')
    return key,last,snap
def enroll(data,path,trust):
    p=_outside(data,path);_outside(data,trust)
    with locked(p),_writer_lock(data):
        reg,pub,rows,head=_load(p,trust);snap=_snapshot(data);key=_identity_key(snap['identity'],snap['whole_public_key'])
        if _latest(rows,key):raise ValueError('IDENTITY_LEDGER_IDENTITY_ALREADY_ENROLLED')
        _registration_available(rows,snap);b={'schema':'tukuyo.identity_ledger.binding/1','ledger_id':reg['ledger_id'],'identity':snap['identity'],'whole_public_key':snap['whole_public_key']}
        if requires(data):
            old=binding(data)
            if old['payload']!=b or old['public_key']!=pub:raise ValueError('IDENTITY_LEDGER_BINDING_CONFLICT')
        else:write(Path(data)/NS/'BINDING.json',_sign(p,b));whole.sync(data)
        env=_append(p,reg,rows,head,'ENROLL',key,_snapshot(data));write(Path(data)/NS/'RECEIPT.json',env)
        return {'ok':True,'ledger_id':reg['ledger_id'],'receipt_sha256':whole.sha_obj(env),'global_unique_individual_proven':False}
def check(data,path,trust):
    p=_outside(data,path);_outside(data,trust)
    with locked(p),_writer_lock(data):
        reg,pub,rows,head=_load(p,trust);key,last,snap=_preflight(data,reg,pub,rows)
        return {'ok':True,'ledger_id':reg['ledger_id'],'canonical_receipt_sha256':whole.sha_obj(last),'observed_lifecycle':snap['lifecycle'],'global_unique_individual_proven':False}
def publish(data,path,trust):
    p=_outside(data,path);_outside(data,trust)
    with locked(p),_writer_lock(data):
        reg,pub,rows,head=_load(p,trust);key,last,snap=_preflight(data,reg,pub,rows,allow_ahead=True)
        if snap['whole_head_sha256']==last['payload']['snapshot']['whole_head_sha256']:return {'ok':True,'unchanged':True}
        env=_append(p,reg,rows,head,'DEATH' if snap['lifecycle']=='DEAD' else 'ADVANCE',key,snap);write(Path(data)/NS/'RECEIPT.json',env)
        return {'ok':True,'receipt_sha256':whole.sha_obj(env),'global_unique_individual_proven':False}
def recover_receipt(data,path,trust):
    p=_outside(data,path);_outside(data,trust)
    with locked(p),_writer_lock(data):
        reg,pub,rows,head=_load(p,trust);b=binding(data)
        if b['public_key']!=pub or b['payload']['ledger_id']!=reg['ledger_id']:raise ValueError('IDENTITY_LEDGER_WRONG_LEDGER')
        key=_identity_key(b['payload']['identity'],b['payload']['whole_public_key']);last=_latest(rows,key)
        if not last or _snapshot(data)!=last['payload']['snapshot']:raise ValueError('IDENTITY_LEDGER_RECOVERY_HEAD')
        write(Path(data)/NS/'RECEIPT.json',last);return {'ok':True,'exact_witnessed_state_required':True}
@contextlib.contextmanager
def guard(data,path,trust):
    p=_outside(data,path);_outside(data,trust)
    with locked(p),_writer_lock(data):check(data,p,trust);yield;publish(data,p,trust)
def register_branch(parent,child,path,trust):
    p=_outside(parent,path);_outside(child,path);_outside(parent,trust);_outside(child,trust)
    with locked(p),_writer_lock(parent),_writer_lock(child):
        reg,pub,rows,head=_load(p,trust);key,last,par=_preflight(parent,reg,pub,rows);chi=_snapshot(child);ckey=_identity_key(chi['identity'],chi['whole_public_key'])
        if par['lifecycle']=='DEAD' or chi['lifecycle']=='DEAD':raise ValueError('IDENTITY_LEDGER_LIVING_BRANCH_REQUIRED')
        if chi['identity']['individual_id']==par['identity']['individual_id'] or chi['whole_public_key']==par['whole_public_key']:raise ValueError('IDENTITY_LEDGER_BRANCH_NEEDS_DISTINCT_ID_AND_KEY')
        if _latest(rows,ckey) or requires(child):raise ValueError('IDENTITY_LEDGER_BRANCH_NOT_FRESH')
        _registration_available(rows,chi)
        declaration={'schema':'tukuyo.identity_ledger.branch/1','parent_receipt_sha256':whole.sha_obj(last),'child_identity':chi['identity'],'child_whole_public_key':chi['whole_public_key'],'private_autobiography_transferred_by_registration':False,'runtime_generated_by_this_registration':False}
        signatures={'parent':whole._sign(parent,declaration),'child':whole._sign(child,declaration)}
        write(Path(child)/NS/'BINDING.json',_sign(p,{'schema':'tukuyo.identity_ledger.binding/1','ledger_id':reg['ledger_id'],'identity':chi['identity'],'whole_public_key':chi['whole_public_key']}));whole.sync(child)
        env=_append(p,reg,rows,head,'BRANCH',ckey,_snapshot(child),branch_declarations=signatures);write(Path(child)/NS/'RECEIPT.json',env)
        return {'ok':True,'branch_receipt_sha256':whole.sha_obj(env),'new_identity_required':True,'death_successor':False}
