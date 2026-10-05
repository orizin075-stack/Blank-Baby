from pathlib import Path
import hashlib,json
from tukuyo_common.atomic_fs import atomic_write_bytes
from tukuyo_v977 import whole_state as whole
from tukuyo_v1019.transaction import ACTIVE

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def path(data,ns):return Path(data)/ns/'STATE.json'
def save(data,ns,component,state):
    rows=sorted((Path(data)/ns/'commits').glob('*.json'));prev=whole.sha_obj(read(rows[-1])) if rows else whole.ZERO
    pl={'schema':'tukuyo.v1022.commit/1','namespace':ns,'seq':len(rows)+1,'previous':prev,'state':state};env=whole._sign(data,pl)
    atomic_write_bytes(Path(data)/ns/'commits'/f'{len(rows)+1:012d}.json',whole.canon(env)+b'\n')
    cached={'schema':'tukuyo.v1022.cache/1','state':state,'head':whole.sha_obj(env)}
    atomic_write_bytes(path(data,ns),whole.canon(cached)+b'\n');whole.sync(data);return cached
def load(data,ns,component,validate):
    rows=sorted((Path(data)/ns/'commits').glob('*.json'))
    if not rows:raise ValueError('V1022_COMMIT_MISSING:'+ns)
    pub=whole._key_paths(data)[1].read_text().strip();prev=whole.ZERO
    for i,p in enumerate(rows,1):
        env=read(p);pl=env.get('payload',{})
        if p.name!=f'{i:012d}.json' or not whole._verify(env,pub):raise ValueError('V1022_COMMIT_SIGNATURE')
        if pl.get('schema')!='tukuyo.v1022.commit/1' or pl.get('namespace')!=ns or pl.get('seq')!=i or pl.get('previous')!=prev:raise ValueError('V1022_COMMIT_CHAIN')
        validate(pl['state']);prev=whole.sha_obj(env)
    cached={'schema':'tukuyo.v1022.cache/1','state':pl['state'],'head':prev};b=whole.canon(cached)+b'\n';p=path(data,ns)
    if p.exists() and p.read_bytes()!=b:raise ValueError('V1022_CACHE_MISMATCH:'+ns)
    if not ACTIVE.get():
        env=read(whole.state_path(data));q=env.get('payload',{})
        if not whole._verify(env,pub) or q.get('identity')!=whole._live_identity(data):raise ValueError('V1022_WHOLE_ANCHOR')
        if q.get('component_hashes',{}).get(component)!=hashlib.sha256(b).hexdigest():raise ValueError('V1022_RECOVERY_HEAD:'+ns)
    if not p.exists():
        atomic_write_bytes(p,b)
        if p.read_bytes()!=b:raise ValueError('V1022_CACHE_WRITE_VERIFY')
    return pl['state']
