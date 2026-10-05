"""Copy-on-write lineage transactions; a durable redo record precedes live writes.

The existing runtime is a single-writer CLI. These transactions additionally
serialize lineage writers. Before prepare, SIGKILL leaves the live tree intact;
after prepare, startup replays the same bytes, including the unified signature.
"""
from __future__ import annotations
import base64, functools, hashlib, inspect, json, os, shutil, tempfile
from pathlib import Path
from contextvars import ContextVar
from contextlib import contextmanager
from tukuyo_common.atomic_fs import atomic_write_bytes, durable_unlink, maybe_crash
from tukuyo_v977.whole_state import canon, sha_obj
ACTIVE=ContextVar('lineage_transaction',default=False)
LOCKED_ROOTS=ContextVar('runtime_locked_roots',default=frozenset())
TAG='.lineage_transaction'

def _reject_symlinks(data):
    # copytree follows directory links by default. Refuse them before recovery
    # or staging can read/write a tree outside the requested runtime root.
    for path in Path(data).rglob('*'):
        if path.is_symlink():raise ValueError('LINEAGE_TXN_SYMLINK:'+path.relative_to(data).as_posix())

@contextmanager
def _writer_lock(data):
    data=Path(data).resolve()
    if data.parent.name=='runtimes' and data.parent.parent.name in ('v1021','v1022_ecology'):
        owner=data.parent.parent.parent;tp=owner/'v1022_ecology/private/delegation.token'
        delegated=tp.is_file() and os.environ.get('TUKUYO_OWNER_DELEGATION','')==tp.read_text().strip()
        if not delegated and str(owner) not in LOCKED_ROOTS.get():
            with _writer_lock(owner):
                with _writer_lock(data):yield
            return
    key=str(Path(data).resolve())
    held=LOCKED_ROOTS.get()
    if key in held:
        yield
        return
    token=LOCKED_ROOTS.set(held|{key})
    lock=Path(tempfile.gettempdir())/('tukuyo-lineage-'+hashlib.sha256(str(Path(data).resolve()).encode()).hexdigest()+'.lock')
    try:
      with lock.open('a+b') as handle:
        if os.name=='nt':
            import msvcrt
            handle.seek(0,2)
            if handle.tell()==0:handle.write(b'0');handle.flush()
            handle.seek(0);msvcrt.locking(handle.fileno(),msvcrt.LK_LOCK,1)
            try:
                _reject_symlinks(data)
                yield
            finally:handle.seek(0);msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)
        else:
            import fcntl
            fcntl.flock(handle,fcntl.LOCK_EX)
            try:
                _reject_symlinks(data)
                yield
            finally:fcntl.flock(handle,fcntl.LOCK_UN)
    finally: LOCKED_ROOTS.reset(token)

def _files(data):
    return {p.relative_to(data).as_posix():p for p in Path(data).rglob('*')
            if p.is_file() and TAG not in p.relative_to(data).parts and '.tukuyo-atomic-' not in p.name}

def _apply(data,tx):
    if tx.get('schema')!='tukuyo.v1019.1.lineage_transaction/1': raise ValueError('LINEAGE_TXN_SCHEMA')
    z=dict(tx);h=z.pop('sha256',None)
    if h!=sha_obj(z): raise ValueError('LINEAGE_TXN_HASH')
    rows=[]
    for r in tx['writes']:
        rel=Path(r['path'])
        if rel.is_absolute() or '..' in rel.parts or TAG in rel.parts: raise ValueError('LINEAGE_TXN_PATH')
        p=Path(data)/rel
        if any((Path(data)/Path(*rel.parts[:n])).is_symlink() for n in range(1,len(rel.parts)+1)): raise ValueError('LINEAGE_TXN_SYMLINK')
        b=base64.b64decode(r['bytes'],validate=True) if r['bytes'] is not None else None
        if b is not None and hashlib.sha256(b).hexdigest()!=r['sha256']: raise ValueError('LINEAGE_TXN_BYTES')
        rows.append((p,b,r['mode']))
    for i,(p,b,mode) in enumerate(rows):
        for attempt in range(3):
            if b is None:durable_unlink(p)
            else:atomic_write_bytes(p,b,mode=mode)
            if (not p.exists()) if b is None else (p.is_file() and p.read_bytes()==b):break
        else:raise ValueError('LINEAGE_TXN_WRITE_VERIFY:'+str(p.relative_to(data)))
        maybe_crash('lineage:apply:'+str(i))
    for r in tx.get('outputs',[]):
        b=base64.b64decode(r['bytes'],validate=True)
        if hashlib.sha256(b).hexdigest()!=r['sha256']: raise ValueError('LINEAGE_TXN_OUTPUT')
        atomic_write_bytes(Path(r['path']),b)
    maybe_crash('lineage:after_apply')
    # Do not acknowledge a transaction merely because replace() returned. Keep
    # the redo record until every after-image and the signed component binding
    # can be read back from the live tree.
    for p,b,_ in rows:
        if (p.exists() if b is None else (not p.is_file() or p.read_bytes()!=b)):
            raise ValueError('LINEAGE_TXN_WRITE_VERIFY:'+str(p.relative_to(data)))
    for r in tx.get('outputs',[]):
        p=Path(r['path'])
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=r['sha256']:
            raise ValueError('LINEAGE_TXN_OUTPUT_VERIFY')
    if (Path(data)/'state/integration_state.json').is_file():
        from tukuyo_v977.whole_state import quick_audit
        checked=quick_audit(data)
        if not checked.get('ok'):raise ValueError('LINEAGE_TXN_WHOLE_VERIFY:'+','.join(checked.get('errors',[])))
        if (Path(data)/'v1022_ecology/commits').exists():
            from tukuyo_v1022.metabolism import preflight
            token=ACTIVE.set(False)
            try:preflight(data)
            finally:ACTIVE.reset(token)
    durable_unlink(Path(data)/TAG/'PREPARED.json')

def _recover(data):
    d=Path(data)/TAG;p=d/'PREPARED.json';recovered=False
    if p.is_file(): _apply(data,json.loads(p.read_text()));recovered=True
    # Without PREPARED, all remaining files are disposable staging material.
    # A transient cleanup failure must not make a valid live head unavailable.
    # Never reuse the abandoned path; each subsequent stage is freshly named.
    if d.exists(): shutil.rmtree(d,ignore_errors=True)
    return {'recovered':recovered,'cleanup_pending':d.exists()}

def recover(data):
    with _writer_lock(data): return _recover(data)

def transactional(out_parameter=None):
    def decorate(fn):
        @functools.wraps(fn)
        def wrapper(data,*args,**kwargs):
            if ACTIVE.get(): return fn(data,*args,**kwargs)
            data=Path(data).resolve()
            with _writer_lock(data):
                _recover(data)
                # Check freshness in the live tree before a mutable stage can
                # advance histories and create a new whole-state signature.
                from tukuyo_v1019.evolution import ensure_state
                if (data/'v1019/commits').is_dir(): ensure_state(data)
                from tukuyo_v1020.ecology import was_initialized,ensure_state as population_state
                if was_initialized(data): population_state(data)
                if (data/'v1021').exists():
                    from tukuyo_v1021.runtime_bridge import preflight
                    preflight(data)
                if (data/'v1022/commits').exists():
                    from tukuyo_v1022.cognition import state as cognition_state
                    cognition_state(data)
                if (data/'v1022_ecology/commits').exists():
                    from tukuyo_v1022.metabolism import preflight as metabolism_preflight
                    metabolism_preflight(data)
                td=data/TAG;td.mkdir(parents=True,exist_ok=True)
                stage=Path(tempfile.mkdtemp(prefix='work-',dir=td))
                shutil.copytree(data,stage,ignore=shutil.ignore_patterns(TAG),dirs_exist_ok=True)
                bound=inspect.signature(fn).bind(stage,*args,**kwargs)
                output=None
                if out_parameter:
                    output=Path(bound.arguments[out_parameter]).resolve()
                    bound.arguments[out_parameter]=td/'output.json'
                token=ACTIVE.set(True)
                try:
                    result=fn(*bound.args,**bound.kwargs)
                    from tukuyo_v1019.evolution import ensure_state
                    ensure_state(stage)
                    from tukuyo_v977.whole_state import sync
                    sync(stage)
                    before=_files(data);after=_files(stage);writes=[]
                    for name in sorted(set(before)|set(after)):
                        old=before[name].read_bytes() if name in before else None
                        new=after[name].read_bytes() if name in after else None
                        if old==new: continue
                        writes.append({'path':name,'bytes':None if new is None else base64.b64encode(new).decode(),
                                       'sha256':None if new is None else hashlib.sha256(new).hexdigest(),
                                       'mode':after[name].stat().st_mode & 0o777 if name in after else 0o600})
                    outputs=[]
                    if output is not None:
                        b=Path(bound.arguments[out_parameter]).read_bytes()
                        outputs=[{'path':str(output),'bytes':base64.b64encode(b).decode(),'sha256':hashlib.sha256(b).hexdigest()}]
                    tx={'schema':'tukuyo.v1019.1.lineage_transaction/1','operation':fn.__name__,'writes':writes,'outputs':outputs}
                    tx['sha256']=sha_obj(tx)
                    maybe_crash('lineage:before_prepare')
                    atomic_write_bytes(td/'PREPARED.json',canon(tx)+b'\n',mode=0o600)
                    maybe_crash('lineage:after_prepare')
                    _apply(data,tx)
                    if output is not None and isinstance(result,dict):result['package_file']=str(output)
                    return result
                finally:
                    ACTIVE.reset(token)
                    # A prepared record is kept on ordinary I/O failure for restart.
                    if not (td/'PREPARED.json').exists(): shutil.rmtree(td,ignore_errors=True)
        return wrapper
    return decorate
