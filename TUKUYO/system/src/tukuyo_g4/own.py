"""generation 4: what the child learned is its own.

Its stores - the readings it learned (g4/learned.json), the answers its parents agreed on (g4/remembered.json), the
record of its life (g4/life.json), the disagreements it keeps to look back on (g4/unresolved.json) and the problems it
could not read alone (g4/unread.json) - are signed with the individual's own key (the v977 whole-state key) and bound to its
id, and the whole state (v977 UNIFIED_STATE) records their hashes. A store changed by hand, or taken from another child,
is refused when it is read, and whole-audit reports it.

Each signature also names the version of the store the whole state had recorded when it was written (base). A store
the whole state did not record is taken only when it names the recorded one: written by this individual after it,
before the whole state was synced (a stop between the two). An older version of its own store put back in place of the
recorded one names an older base, and is refused like a store changed by hand (<KIND>_ROLLED_BACK); the next start does
not take it in either (unsynced). The same idea as the signed commit chains of the v1022 runtime (tukuyo_v1022.store,
tukuyo_g4.runtime_store), without a chain: one link back to the version the whole state holds.

This leaves a window (the fusion limits round, evidence_gen4/LIMITS_2026-10-13.md §6): a store written twice before the
whole state was synced may be put back to the first of the two writes, and nothing in the data directory can tell, as
whoever puts files back can put the whole state back too. Each signature now carries a number (seq) that grows with
every write of that store. An owner who keeps a witness outside the data directory (TUKUYO_G4_WITNESS, a directory: one
file per individual, signed with its key) has the number of each store's last write noted there after the write; a store
with a smaller number than the witness noted, or missing when the witness noted one, is refused (<KIND>_ROLLED_BACK). The
witness is as safe as the place it is kept: on the same disk, a restore of the disk puts it back too. The last write before
a stop, before the witness was told, is not covered (as if the stop had come before that write).

A store written before stores were signed (generation 4 of 2026-10-09, before this module) is read only when the whole
state recorded that very file; the next save signs it. An unsigned store the whole state never recorded is not taken:
before, one put into an individual that had not used generation 4 yet (its whole state had recorded nothing about it)
was read and then signed, so remembered answers or a record of its life could be planted from outside (v1022.6.5 had
already refused this for what it learned, runtime_store.py). Outside a live individual (tools, tests) a store is
sealed with its sha256 only, as before.
The key lives with the individual: this guards against changes made without it, not against someone who uses it.
"""
from __future__ import annotations
import hashlib,json,os
from contextvars import ContextVar
from pathlib import Path

SCHEMA='tukuyo.g4.own/1';WITNESS_SCHEMA='tukuyo.g4.witness/1';WITNESS_ENV='TUKUYO_G4_WITNESS'
KINDS={'learned':'g4/learned.json','remembered':'g4/remembered.json','life':'g4/life.json','unresolved':'g4/unresolved.json','unread':'g4/unread.json'}
COMPONENTS={'g4_'+k:v for k,v in KINDS.items()}

def body_sha(o):return hashlib.sha256(json.dumps(o,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

# ----------------------------------------------------------------------------- the witness outside the data directory
def _witness_file(data):
    """the witness file of the live individual in data, or None when no witness is kept (TUKUYO_G4_WITNESS unset)"""
    d=os.environ.get(WITNESS_ENV,'').strip()
    if not d:return None
    ident=individual(data)
    if ident is None:return None
    d=Path(d).resolve();root=Path(data).resolve()
    if root.parent.name=='.lineage_transaction':root=root.parent.parent      # a transaction's working copy
    if d==root or root in d.parents:raise ValueError('G4_WITNESS_INSIDE_DATA')
    return d/(hashlib.sha256(ident.encode()).hexdigest()[:24]+'.witness.json')

def witnessed(data):
    """{kind: the number of the last write the witness noted}; {} when no witness is kept. ValueError when the witness
    is not this individual's"""
    f=_witness_file(data)
    if f is None or not f.is_file():return {}
    from tukuyo_v977.whole_state import _verify,_key_paths
    try:env=json.loads(f.read_text(encoding='utf-8'));q=env['payload'];pub=_key_paths(data)[1].read_text().strip()
    except (OSError,ValueError,KeyError,TypeError):raise ValueError('G4_WITNESS_NOT_ITS_OWN') from None
    if (not isinstance(q,dict) or q.get('schema')!=WITNESS_SCHEMA or q.get('individual_id')!=individual(data) or not _verify(env,pub)
            or not isinstance(q.get('seq'),dict)):raise ValueError('G4_WITNESS_NOT_ITS_OWN')
    return {k:int(v) for k,v in q['seq'].items()}

# inside a transaction (tukuyo_v1019.transaction) the stores are written to a working copy, which is applied to the live
# data only at its end, or not at all: the witness is told only once it was applied (a witness ahead of the data would
# refuse the data as rolled back)
_PENDING=ContextVar('g4_witness_pending',default=None)
def witness_begin():
    _PENDING.set(None)
def witness_after_apply(data):
    p=_PENDING.get();_PENDING.set(None)
    for kind,seq in (p or {}).items():_note(data,kind,seq,now=True)

def _note(data,kind,seq,now=False):
    """tell the witness that this store was written with this number (after the write)"""
    f=_witness_file(data)
    if f is None:return
    from tukuyo_v1019.transaction import ACTIVE
    if ACTIVE.get() and not now:
        p=_PENDING.get()
        if p is None:p={};_PENDING.set(p)
        p[kind]=max(p.get(kind,0),seq);return
    seqs=witnessed(data)
    if seqs.get(kind,0)>=seq:return
    seqs[kind]=seq
    from tukuyo_v977.whole_state import _sign,canon
    from tukuyo_common.atomic_fs import atomic_write_bytes
    f.parent.mkdir(parents=True,exist_ok=True)
    atomic_write_bytes(f,canon(_sign(data,{'schema':WITNESS_SCHEMA,'individual_id':individual(data),'seq':seqs}))+b'\n')

def _seq_on_disk(data,kind):
    try:return int(json.loads((Path(data)/KINDS[kind]).read_text(encoding='utf-8'))['signed']['payload'].get('seq') or 0)
    except (OSError,ValueError,KeyError,TypeError,AttributeError):return 0

def written(data,kind):
    """after a store was written: the witness, if one is kept, notes the number of this write"""
    if _witness_file(data) is not None:_note(data,kind,_seq_on_disk(data,kind))

def absent(data,kind):
    """a store that is not there: ValueError when the witness noted a write of it (it was taken away)"""
    if witnessed(data).get(kind,0)>0:raise ValueError(kind.upper()+'_ROLLED_BACK')

def note_learned(data,commits):
    """what it learned lives in a chain of commits (runtime_store.py): the witness notes how many"""
    if _witness_file(data) is not None:_note(data,'learned',commits)

def check_learned(data,commits):
    if commits<witnessed(data).get('learned',0):raise ValueError('G4_LEARNING_ROLLED_BACK')

def witness_reset(data):
    """the owner said this copy is the individual (a backup put back: identity-canon-adopt --yes): the witness notes the
    numbers of its stores as they are now, smaller ones included. Nothing when no witness is kept"""
    f=_witness_file(data)
    if f is None:return None
    witnessed(data)                                   # a witness that is not this individual's is not overwritten
    seqs={k:_seq_on_disk(data,k) for k in KINDS if k!='learned' and (Path(data)/KINDS[k]).is_file()}
    n=len(list((Path(data)/'g4'/'commits').glob('*.json')))
    if n:seqs['learned']=n
    from tukuyo_v977.whole_state import _sign,canon
    from tukuyo_common.atomic_fs import atomic_write_bytes
    f.parent.mkdir(parents=True,exist_ok=True)
    atomic_write_bytes(f,canon(_sign(data,{'schema':WITNESS_SCHEMA,'individual_id':individual(data),'seq':seqs}))+b'\n')
    return seqs

def behind_witness(data):
    """the stores older than the last write the witness outside noted (put back, or taken away), for whole-audit: when
    the whole data directory is put back, the whole state agrees with them and only the witness can tell. [] when no
    witness is kept"""
    seen=witnessed(data)
    if not seen:return []
    out=[]
    for kind in KINDS:
        n=len(list((Path(data)/'g4'/'commits').glob('*.json'))) if kind=='learned' else _seq_on_disk(data,kind)
        if n<seen.get(kind,0):out.append(kind)
    return out

def individual(data):
    """the id of the live individual in data, or None"""
    if data is None:return None
    p=Path(data)/'state'/'integration_state.json'
    if not p.is_file():return None
    try:return json.loads(p.read_text(encoding='utf-8'))['payload']['individual_id']
    except (OSError,ValueError,KeyError,TypeError):return None

def sign(data,kind,sha):
    """the signature for a store body of this individual, or None outside a live individual. It names the version of the
    store the whole state recorded when it was written (base: its hash, None when recorded as absent or not at all)"""
    ident=individual(data)
    if ident is None:return None
    from tukuyo_v977.whole_state import _sign
    rec=_recorded(data,kind);seq=max(_seq_on_disk(data,kind),witnessed(data).get(kind,0))+1
    return _sign(data,{'schema':SCHEMA,'kind':kind,'individual_id':ident,'sha256':sha,'base':None if rec is NOT_RECORDED else rec,'seq':seq})

NOT_RECORDED=object()
def _recorded(data,kind):
    """the hash the whole state recorded for this store (None: recorded as absent), or NOT_RECORDED"""
    p=Path(data)/'v977'/'UNIFIED_STATE.json'
    if not p.is_file():return NOT_RECORDED
    try:return json.loads(p.read_text(encoding='utf-8'))['payload'].get('component_hashes',{}).get('g4_'+kind,NOT_RECORDED)
    except (OSError,ValueError,KeyError,TypeError,AttributeError):return NOT_RECORDED

def _file_sha(p):
    p=Path(p);return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None

def check(data,kind,sha,signed):
    """raises ValueError (<KIND>_NOT_ITS_OWN, <KIND>_NOT_SIGNED, <KIND>_ROLLED_BACK) when this store of the individual in
    data is not its own, or is an older version of it than the one the whole state recorded"""
    ident=individual(data)
    if ident is None:return
    if signed is None:
        # unsigned (written before stores were signed): only the very file the whole state recorded
        rec=_recorded(data,kind)
        if rec is NOT_RECORDED or rec!=_file_sha(Path(data)/KINDS[kind]):raise ValueError(kind.upper()+'_NOT_SIGNED')
        absent(data,kind)                                   # the witness noted a signed write after it
        return
    from tukuyo_v977.whole_state import _verify,_key_paths
    pub=_key_paths(data)[1];q=signed.get('payload') if isinstance(signed,dict) else None
    if (not pub.is_file() or not isinstance(q,dict) or not _verify(signed,pub.read_text().strip()) or q.get('schema')!=SCHEMA
            or q.get('kind')!=kind or q.get('individual_id')!=ident or q.get('sha256')!=sha):
        raise ValueError(kind.upper()+'_NOT_ITS_OWN')
    # not the version the whole state recorded: only one written after it (it names it) is taken
    rec=_recorded(data,kind)
    if rec is not NOT_RECORDED and rec!=_file_sha(Path(data)/KINDS[kind]) and ('base' not in q or q['base']!=rec):
        raise ValueError(kind.upper()+'_ROLLED_BACK')
    # older than the last write the witness outside noted (only when one is kept)
    if int(q.get('seq') or 0)<witnessed(data).get(kind,0):raise ValueError(kind.upper()+'_ROLLED_BACK')

def not_its_own(data):
    """the components ('g4_learned', ...) whose store in this individual is not its own: refused when read (changed by
    hand, or taken from another child). The whole state does not take them in (v977 whole_state.sync)"""
    if individual(data) is None:return []
    from .learn import Store
    from .memory import Memory
    from .life import _life
    from .hindsight import Unresolved
    from .growth import Unread
    load={'learned':lambda:Store(Path(data)/'g4').load(),'remembered':lambda:Memory(data).load(),'life':lambda:_life(data),
          'unresolved':lambda:Unresolved(data).load(),'unread':lambda:Unread(data).load()}
    out=[]
    for kind,rel in KINDS.items():
        if not (Path(data)/rel).is_file():continue
        try:load[kind]()
        except (OSError,ValueError,KeyError,TypeError,AttributeError):out.append('g4_'+kind)
    return out

def body(kind,o):
    """the signed part of each store"""
    if kind=='learned':return o['templates']
    if kind in ('remembered','unresolved','unread'):return o['entries']
    return o['life'] if 'life' in o else {'first_alone':o.get('first_alone',[])}

def unsynced(data):
    """True when the only drift of the whole state is generation-4 stores this individual signed itself (written, then the
    process stopped before the whole state was synced, or written by a tool): the next start may sync them. Anything else
    is left to the audits"""
    if individual(data) is None:return False
    p=Path(data)/'v977'/'UNIFIED_STATE.json'
    try:rec=json.loads(p.read_text(encoding='utf-8'))['payload'].get('component_hashes',{})
    except (OSError,ValueError,KeyError,TypeError,AttributeError):return False
    drift=[k for k,rel in COMPONENTS.items() if k in rec and rec[k]!=_file_sha(Path(data)/rel)]
    if not drift:return False
    from tukuyo_v977.whole_state import quick_audit
    if sorted(quick_audit(data).get('errors') or [])!=sorted('COMPONENT_DRIFT:'+k for k in drift):return False
    for k in drift:
        kind=k[3:];f=Path(data)/KINDS[kind]
        if not f.is_file():return False
        try:
            o=json.loads(f.read_text(encoding='utf-8'))
            if o.get('signed') is None:return False
            check(data,kind,body_sha(body(kind,o)),o['signed'])
        except (OSError,ValueError,KeyError,TypeError):return False
    return True
