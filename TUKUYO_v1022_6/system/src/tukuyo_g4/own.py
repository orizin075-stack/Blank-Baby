"""generation 4: what the child learned is its own.

Its stores - the readings it learned (g4/learned.json), the answers its parents agreed on (g4/remembered.json) and the
record of its life (g4/life.json) - are signed with the individual's own key (the v977 whole-state key) and bound to its
id, and the whole state (v977 UNIFIED_STATE) records their hashes. A store changed by hand, or taken from another child,
is refused when it is read, and whole-audit reports it.

A store written before stores were signed is still read, as long as the whole state never recorded another version of
it; the next save signs it. Outside a live individual (tools, tests) a store is sealed with its sha256 only, as before.
The key lives with the individual: this guards against changes made without it, not against someone who uses it.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path

SCHEMA='tukuyo.g4.own/1'
KINDS={'learned':'g4/learned.json','remembered':'g4/remembered.json','life':'g4/life.json'}
COMPONENTS={'g4_'+k:v for k,v in KINDS.items()}

def body_sha(o):return hashlib.sha256(json.dumps(o,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

def individual(data):
    """the id of the live individual in data, or None"""
    if data is None:return None
    p=Path(data)/'state'/'integration_state.json'
    if not p.is_file():return None
    try:return json.loads(p.read_text(encoding='utf-8'))['payload']['individual_id']
    except (OSError,ValueError,KeyError,TypeError):return None

def sign(data,kind,sha):
    """the signature for a store body of this individual, or None outside a live individual"""
    ident=individual(data)
    if ident is None:return None
    from tukuyo_v977.whole_state import _sign
    return _sign(data,{'schema':SCHEMA,'kind':kind,'individual_id':ident,'sha256':sha})

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
    """raises ValueError (<KIND>_NOT_ITS_OWN, <KIND>_NOT_SIGNED) when this store of the individual in data is not its own"""
    ident=individual(data)
    if ident is None:return
    if signed is None:
        # unsigned: only the very file the whole state recorded, or one it never recorded anything about (before signing)
        rec=_recorded(data,kind)
        if rec is not NOT_RECORDED and rec!=_file_sha(Path(data)/KINDS[kind]):raise ValueError(kind.upper()+'_NOT_SIGNED')
        return
    from tukuyo_v977.whole_state import _verify,_key_paths
    pub=_key_paths(data)[1];q=signed.get('payload') if isinstance(signed,dict) else None
    if (not pub.is_file() or not isinstance(q,dict) or not _verify(signed,pub.read_text().strip()) or q.get('schema')!=SCHEMA
            or q.get('kind')!=kind or q.get('individual_id')!=ident or q.get('sha256')!=sha):
        raise ValueError(kind.upper()+'_NOT_ITS_OWN')

def body(kind,o):
    """the signed part of each store"""
    if kind=='learned':return o['templates']
    if kind=='remembered':return o['entries']
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
