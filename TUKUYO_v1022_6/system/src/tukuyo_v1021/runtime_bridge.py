from __future__ import annotations
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
from tukuyo_common.atomic_fs import atomic_write_bytes,maybe_crash
from tukuyo_v977 import whole_state as whole
from tukuyo_v1018 import succession as s18
from tukuyo_v1019 import evolution as e19
from tukuyo_v1019.transaction import ACTIVE,transactional
from tukuyo_v1020 import ecology as eco

SCHEMA='tukuyo.v1021.runtime_ecology_bridge/1'
CLAIMS={'bounded_runtime_succession_bridge':True,'every_model_agent_has_runtime':False,
        'living_parent_reproduction':False,'model_profile_is_runtime_inherited_profile':False,
        'natural_selection_established':False,'open_ended_evolution_established':False,
        'autonomous_code_modification':False,'wall_clock_24h':False}

def root(data):return Path(data)/'v1021'
def state_path(data):return root(data)/'BRIDGE_STATE.json'
def _read(p):return json.loads(Path(p).read_text())
def _path(data,rid):
    if not re.fullmatch(r'R[0-9]{6}',rid):raise ValueError('V1021_RUNTIME_ID')
    return root(data)/'runtimes'/rid
def _cli(data,rid,*args):
    # The child owns its data and keys; the whole directory is staged by the
    # owner transaction. Child fault injection is separate from bridge faults.
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    env.pop('TUKUYO_CRASH_POINT',None)
    runtime=Path(__file__).resolve().parents[2]
    p=subprocess.run([sys.executable,'-B',str(runtime/'run_tukuyo.py'),
        '--runtime-trust-file',str(root(data)/'RUNTIME_TRUST.txt'),
        '--data',str(_path(data,rid)),*map(str,args)],env=env,capture_output=True,text=True,timeout=180)
    try:r=json.loads(p.stdout)
    except Exception:raise ValueError('V1021_CHILD_OUTPUT')
    if p.returncode or not r.get('ok'):raise ValueError('V1021_CHILD_COMMAND:'+str(r.get('error',args[0])))
    return r
def _snapshot(data,rid):
    d=_path(data,rid)
    if not whole.audit(d).get('ok'):raise ValueError('V1021_CHILD_AUDIT:'+rid)
    ss=s18.ensure_state(d)[0];ev=e19.ensure_state(d)
    life=_read(d/'v1007/ORGANISM2_STATE.json') if (d/'v1007/ORGANISM2_STATE.json').is_file() else {'lifecycle':'ALIVE'}
    return {'individual_id':whole._live_identity(d)['individual_id'],
        'family_lineage_id':ss['family_lineage_id'],'generation':ss['generation'],
        'succession_public_key':s18.public_key(d),
        'whole_public_key':whole._key_paths(d)[1].read_text().strip(),
        'whole_sha256':hashlib.sha256(whole.state_path(d).read_bytes()).hexdigest(),
        'soul_sha256':hashlib.sha256((d/'v977/SOUL_CORE.json').read_bytes()).hexdigest(),
        'heart_sha256':hashlib.sha256((d/'v978/HEART_STATE.json').read_bytes()).hexdigest(),
        'lifecycle':life['lifecycle'],'evolution_profile':ev['current_evolution_profile']}
def _fresh(data,st):
    if st['next_runtime']>=64:raise ValueError('V1021_RUNTIME_LIMIT')
    rid=f"R{st['next_runtime']:06d}";st['next_runtime']+=1
    ident=whole._live_identity(data)['individual_id']+'-bridge-'+rid
    _cli(data,rid,'init','--individual-id',ident)
    return rid,ident
def _validate(st):
    if st.get('schema')!=SCHEMA or type(st.get('next_runtime')) is not int or not 0<=st['next_runtime']<=64:raise ValueError('V1021_STATE')
    if len(st['runtimes'])!=st['next_runtime'] or len(st['bindings'])>8:raise ValueError('V1021_POPULATION')
    for rid in st['runtimes']:_path('.',rid)
    if not set(st['bindings'].values())<=set(st['runtimes']):raise ValueError('V1021_BINDINGS')
    if len(set(st['bindings'].values()))!=len(st['bindings']):raise ValueError('V1021_DUPLICATE_BINDING')
    if not all(re.fullmatch(r'E[0-9]{6}',k) for k in st['bindings']):raise ValueError('V1021_MODEL_ID')
    if st['claim_boundary']!=CLAIMS:raise ValueError('V1021_CLAIMS')
def _save(data,st):
    _validate(st);cd=root(data)/'commits';paths=sorted(cd.glob('*.json'))
    prev=whole.sha_obj(_read(paths[-1])) if paths else whole.ZERO
    pl={'schema':'tukuyo.v1021.bridge_commit/1','seq':len(paths)+1,
        'previous_commit_sha256':prev,'state':st}
    env=whole._sign(data,pl)
    atomic_write_bytes(cd/f"{pl['seq']:012d}.json",whole.canon(env)+b'\n')
    cached={'schema':'tukuyo.v1021.bridge_cache/1','state':st,'head_sha256':whole.sha_obj(env)}
    atomic_write_bytes(state_path(data),whole.canon(cached)+b'\n')
    whole.sync(data)
    return cached
def ensure_state(data,*,repair=False,persist=True):
    paths=sorted((root(data)/'commits').glob('*.json'));prev=whole.ZERO;st=None
    if not paths:raise ValueError('V1021_JOURNAL_MISSING')
    if set((root(data)/'commits').rglob('*'))!=set(paths):raise ValueError('V1021_JOURNAL_FILES')
    pub=whole._key_paths(data)[1].read_text().strip()
    for i,p in enumerate(paths,1):
        env=_read(p);pl=env.get('payload',{})
        if p.name!=f'{i:012d}.json' or not whole._verify(env,pub):raise ValueError('V1021_COMMIT_SIGNATURE')
        if pl.get('schema')!='tukuyo.v1021.bridge_commit/1' or pl.get('seq')!=i or pl.get('previous_commit_sha256')!=prev:raise ValueError('V1021_COMMIT_CHAIN')
        st=pl['state'];_validate(st);prev=whole.sha_obj(env)
    cached={'schema':'tukuyo.v1021.bridge_cache/1','state':st,'head_sha256':prev}
    p=state_path(data);encoded=whole.canon(cached)+b'\n'
    if not repair and p.exists() and _read(p)!=cached:raise ValueError('V1021_CACHE_MISMATCH')
    env=_read(whole.state_path(data));pl=env.get('payload',{})
    if not whole._verify(env,pub) or pl.get('schema')!=whole.SCHEMA or pl.get('identity')!=whole._live_identity(data):raise ValueError('V1021_WHOLE_ANCHOR')
    if pl.get('component_hashes',{}).get('runtime_ecology_bridge_v1021')!=hashlib.sha256(encoded).hexdigest():raise ValueError('V1021_RECOVERY_HEAD')
    if persist and (not p.exists() or repair):
        atomic_write_bytes(p,encoded)
        if p.read_bytes()!=encoded:raise ValueError('V1021_CACHE_WRITE_VERIFY')
    return cached

def recover_cache(data):
    # Explicit recovery may discard an untrusted cache, but never chooses a
    # journal head without its exact binding in the retained signed Whole State.
    # Validate all child heads before writing; do not sign or change any head.
    p=state_path(data);before=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    whole_before=whole.state_path(data).read_bytes()
    cached=ensure_state(data,repair=True,persist=False)
    _check_runtimes(data,cached['state'])
    encoded=whole.canon(cached)+b'\n';atomic_write_bytes(p,encoded)
    if p.read_bytes()!=encoded or whole.state_path(data).read_bytes()!=whole_before:raise ValueError('V1021_CACHE_RECOVERY_WRITE_VERIFY')
    return {**summary(cached['state']),'cache_recovery':{'before_sha256':before,
        'after_sha256':hashlib.sha256(encoded).hexdigest(),'whole_preserved':True,
        'verified_journal_and_whole_head':True}}
def _check_runtimes(data,st):
    public=set();whole_keys=set()
    for rid,row in st['runtimes'].items():
        now=_snapshot(data,rid)
        if now!=row:raise ValueError('V1021_RUNTIME_DRIFT:'+rid)
        if now['succession_public_key'] in public or now['whole_public_key'] in whole_keys:raise ValueError('V1021_SHARED_KEY')
        public.add(now['succession_public_key']);whole_keys.add(now['whole_public_key'])
    model=eco.ensure_state(data)['state']
    if not set(st['bindings'])<=set(model['agents']):raise ValueError('V1021_BINDING_DEAD_MODEL')
    if st['tick']!=model['tick']:raise ValueError('V1021_TICK_BINDING')
    for mid,rid in st['bindings'].items():
        if st['runtimes'][rid]['lifecycle']=='DEAD':raise ValueError('V1021_LIVE_BINDING_DEAD_RUNTIME')
        if st['runtimes'][rid]['family_lineage_id']!=model['agents'][mid]['family']:raise ValueError('V1021_FAMILY_BINDING')
def preflight(data):
    cached=ensure_state(data);_check_runtimes(data,cached['state']);return cached
def summary(st):
    return {'ok':True,'version':'v1021','tick':st['tick'],'active_runtime_count':len(st['bindings']),
        'total_runtime_count':len(st['runtimes']),'actual_successions':len(st['successions']),
        'max_actual_generation':max((r['generation'] for r in st['runtimes'].values()),default=0),
        'bindings':st['bindings'],'runtimes':st['runtimes'],'claim_boundary':CLAIMS}

@transactional()
def init(data,trust_file,families=4,seed='v1021',regeneration=240000,max_age=8):
    if root(data).exists() or eco.was_initialized(data):raise ValueError('V1021_REINITIALIZATION')
    if type(families) is not int or not 2<=families<=8:raise ValueError('V1021_FAMILY_LIMIT')
    if trust_file is None:raise ValueError('V1021_EXTERNAL_RUNTIME_TRUST_REQUIRED')
    from tukuyo_v977.startup_guard import verify_distribution
    verify_distribution(Path(__file__).resolve().parents[2],trust_file)
    atomic_write_bytes(root(data)/'RUNTIME_TRUST.txt',Path(trust_file).read_bytes())
    st={'schema':SCHEMA,'tick':0,'next_runtime':0,'bindings':{},'runtimes':{},
        'successions':[],'claim_boundary':CLAIMS}
    for i in range(families):
        rid,ident=_fresh(data,st)
        _cli(data,rid,'heart-experience','discovery','0','.1','--theme','runtime-bridge-origin')
        _cli(data,rid,'succession-founder-init')
        st['runtimes'][rid]=_snapshot(data,rid)
        proof=eco._source(_path(data,rid),st['runtimes'][rid]['succession_public_key'])
        prior=eco.ensure_state(data) if i else None
        if i:
            command={'kind':'JOIN','source':proof,'source_trust':proof['public_key'],'founders':1}
        else:
            command={'kind':'INIT','owner_id':whole._live_identity(data)['individual_id'],
                'config':{'capacity':240000,'regeneration':regeneration,'max_population':16,'max_age':max_age,'cooperation':True},
                'seed_sha256':hashlib.sha256(str(seed).encode()).hexdigest(),'source':proof,'source_trust':proof['public_key'],'founders':1}
        cached,_=eco._commit(data,prior,command);whole.sync(data)
        mid=max(cached['state']['agents'],key=lambda k:int(k[1:]));st['bindings'][mid]=rid
    _save(data,st);_check_runtimes(data,st);return summary(st)

@transactional()
def step(data,environment='resource',ticks=1):
    if type(ticks) is not int or not 1<=ticks<=16:raise ValueError('V1021_STEP_LIMIT')
    st=preflight(data)['state']
    for _ in range(ticks):
        eco.step(data,environment,1);whole.sync(data)
        model=eco.ensure_state(data)['state'];report=model['last_tick']
        for mid,rid in list(st['bindings'].items()):
            if mid in model['agents']:
                energy=model['agents'][mid]['energy']
                _cli(data,rid,'heart-experience','discovery',str(.1 if energy>=12000 else -.1),'.1','--theme','ecology-'+environment)
                st['runtimes'][rid]=_snapshot(data,rid)
                continue
            # Existing mortality-gated succession is preserved. Model birth
            # alone never kills a parent or authorizes a living-parent export.
            descendants=[(k,a) for k,a in model['agents'].items()
                if a['parent']==mid and k not in st['bindings']]
            parent=_path(data,rid)
            _cli(data,rid,'evolution-select',environment,'--seed',f"bridge-{model['tick']}-{rid}")
            _cli(data,rid,'organism2-update','INJURY','--amount','1')
            _cli(data,rid,'organism2-update','INJURY','--amount','1')
            st['runtimes'][rid]=_snapshot(data,rid);del st['bindings'][mid]
            maybe_crash('bridge:after_parent_death')
            if not descendants:continue
            child_mid,a=max(descendants,key=lambda pair:(pair[1]['energy'],pair[0]))
            child,ident=_fresh(data,st);maybe_crash('bridge:after_spawn')
            cp=root(data)/'packages'/(child+'.pub');pp=root(data)/'packages'/(rid+'.pub')
            pkg=root(data)/'packages'/(rid+'-'+child+'.json')
            _cli(data,child,'succession-pubkey-export','--out',cp)
            _cli(data,rid,'succession-pubkey-export','--out',pp)
            _cli(data,rid,'evolution-export',ident,'--out',pkg,'--child-public-key-file',cp)
            # Export records consumption of the parent's one-use succession.
            # Bind the post-export head, rather than its earlier death head.
            st['runtimes'][rid]=_snapshot(data,rid)
            _cli(data,child,'evolution-import',pkg,'--parent-trust-file',pp)
            maybe_crash('bridge:after_import')
            _cli(data,child,'heart-experience','discovery','0','.1','--theme','runtime-bridge-successor')
            st['runtimes'][child]=_snapshot(data,child);st['bindings'][child_mid]=child
            st['successions'].append({'tick':model['tick'],'model_parent':mid,'model_child':child_mid,
                'runtime_parent':rid,'runtime_child':child,'cause':next(d['reason'] for d in report['deaths'] if d['id']==mid),
                'model_profile':a['profile'],'runtime_evolution_profile':st['runtimes'][child]['evolution_profile'],
                'package_sha256':hashlib.sha256(pkg.read_bytes()).hexdigest()})
        st['tick']=model['tick']
    _save(data,st);_check_runtimes(data,st);return summary(st)

def status(data):return summary(preflight(data)['state'])
def audit(data):
    try:
        r=status(data);return {**r,'errors':[]}
    except Exception as exc:return {'ok':False,'version':'v1021','errors':[str(exc)]}
