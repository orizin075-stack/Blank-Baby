"""Authenticated G4 templates for live runtimes; standalone examples keep their checksum format.

A store an earlier generation-4 version signed with the individual's own key (tukuyo_g4.own, before the runtime
commits) is read, verified, and taken over by the next commit; an unsigned or foreign one is refused."""
from pathlib import Path
import hashlib,json
from tukuyo_common.atomic_fs import atomic_write_bytes
from tukuyo_v977 import whole_state as whole
from tukuyo_v1022 import store
from tukuyo_v1019.transaction import transactional

NS='g4';COMPONENT='g4_learning';SCHEMA='tukuyo.g4.runtime_learning/1'

def is_live(data):
    return whole.state_path(data).is_file()

def needs_preflight(data):
    if (Path(data)/NS).exists():return True
    p=whole.state_path(data)
    return p.is_file() and COMPONENT in json.loads(p.read_text()).get('payload',{}).get('component_hashes',{})

def validate(state):
    if state.get('schema')!=SCHEMA:raise ValueError('G4_LEARNING_SCHEMA')
    o=state.get('learned',{})
    body=json.dumps(o.get('templates',{}),ensure_ascii=False,sort_keys=True)
    if o.get('schema')!='tukuyo.g4.learned/1' or o.get('sha256')!=hashlib.sha256(body.encode()).hexdigest():
        raise ValueError('G4_LEARNING_BODY')

def load(data):
    data=Path(data);p=data/NS/'learned.json'
    if not (data/NS/'commits').exists():
        head=json.loads(whole.state_path(data).read_text())
        if COMPONENT in head.get('payload',{}).get('component_hashes',{}):raise ValueError('G4_LEARNING_HISTORY_MISSING')
        if p.exists():
            legacy=_own_signed(data,p)
            if legacy is None:raise ValueError('G4_LEARNING_UNSIGNED_LEGACY')
            return legacy
        return {'schema':'tukuyo.g4.learned/1','templates':{}}
    state=store.load(data,NS,COMPONENT,validate);expected=state['learned']
    if p.exists():
        if json.loads(p.read_text())!=expected:raise ValueError('G4_LEARNING_CACHE_MISMATCH')
    else:atomic_write_bytes(p,whole.canon(expected)+b'\n')
    return expected

def _own_signed(data,p):
    """the templates of a store signed by this individual's own key (tukuyo_g4.own), or None when it carries no such
    signature; ValueError when it does and the seal or the signature is not its own"""
    try:o=json.loads(p.read_text(encoding='utf-8'))
    except (OSError,ValueError):return None
    if not isinstance(o,dict) or o.get('signed') is None:return None
    body=json.dumps(o.get('templates',{}),ensure_ascii=False,sort_keys=True);sha=hashlib.sha256(body.encode()).hexdigest()
    if o.get('schema')!='tukuyo.g4.learned/1' or o.get('sha256')!=sha:raise ValueError('LEARNED_STORE_SEAL')
    from . import own
    own.check(data,'learned',sha,o['signed'])
    return {'schema':'tukuyo.g4.learned/1','templates':o['templates'],'sha256':sha}

@transactional()
def save(data,learned):
    # Validate the old signed head before granting a new signature.
    load(data)
    state={'schema':SCHEMA,'learned':learned};validate(state)
    atomic_write_bytes(Path(data)/NS/'learned.json',whole.canon(learned)+b'\n')
    store.save(data,NS,COMPONENT,state)

def audit(data):
    from .learn import Store
    return Store(Path(data)/NS).audit()
