"""An ecological *model* owned by a runtime, not a substitute for its identity.

All resource and energy accounting uses integer units. Model offspring are not
v1018 successor identities, and model deaths never kill a source runtime.
"""
from __future__ import annotations
import base64, copy, hashlib, json, math, shutil, tempfile
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from tukuyo_common.atomic_fs import atomic_write_bytes
from tukuyo_v977.whole_state import canon, sha_obj, _live_identity
from tukuyo_v1018 import succession as s18
from tukuyo_v1019 import evolution as e19
from tukuyo_v1019.lifecycle import require_alive
from tukuyo_v1019.transaction import transactional, TAG

VERSION='v1020'
ZERO='0'*64
INITIAL_ENERGY=12000
BIRTH_ENERGY=6000
BIRTH_COST=3000
BIRTH_THRESHOLD=24000
MAX_TICKS=512
MAX_FAMILIES=8
CLAIMS={'bounded_population_ecology':True,'resource_conservation':True,
        'model_births_are_runtime_successors':False,'model_deaths_kill_source_runtime':False,
        'natural_selection_established':False,'open_ended_evolution_established':False,'general_l5':False}


def root(data): return Path(data)/'v1020'
def state_path(data): return root(data)/'ECOLOGY_STATE.json'
def _read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def _fail(code): raise ValueError('V1020_'+code)
def _keys(obj, names):
    if type(obj) is not dict or set(obj)!=set(names.split()): _fail('FIELDS')
def _int(n, lo, hi):
    if type(n) is not int or not lo<=n<=hi: _fail('INTEGER_BOUNDS')
    return n

def _profile(p):
    _keys(p,' '.join(e19.TRAITS))
    if any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1 for v in p.values()): _fail('PROFILE')
    # Reject sub-micro-unit values: inheritance uses an exact integer trait budget.
    if any(abs(v*1000000-round(v*1000000))>0.000001 for v in p.values()): _fail('PROFILE_PRECISION')
    if sum(round(v*1000000) for v in p.values())!=round(e19.TRAIT_BUDGET*1000000): _fail('TRAIT_BUDGET')
    return {k:round(p[k],6) for k in e19.TRAITS}

def _verify_sig(pub,sig,payload):
    try:
        Ed25519PublicKey.from_public_bytes(base64.b64decode(pub,validate=True)).verify(base64.b64decode(sig,validate=True),canon(payload))
    except Exception as ex: raise ValueError('V1020_SIGNATURE') from ex

def _verify_source(proof, trusted):
    _keys(proof,'schema public_key payload signature')
    if proof['schema']!='tukuyo.v1020.source_attestation/1' or proof['public_key']!=trusted: _fail('SOURCE_TRUST')
    p=proof['payload'];_keys(p,'individual_id family_lineage_id generation profile source_evolution_state_sha256')
    if any(type(p[k]) is not str or not p[k] or len(p[k])>256 for k in ('individual_id','family_lineage_id')): _fail('SOURCE_IDENTITY')
    _int(p['generation'],0,1000000);_profile(p['profile'])
    h=p['source_evolution_state_sha256']
    if type(h) is not str or len(h)!=64 or any(c not in '0123456789abcdef' for c in h): _fail('SOURCE_HASH')
    _verify_sig(trusted,proof['signature'],p)
    return p

def _source(data, trusted):
    # Audit a snapshot so source cache reconstruction cannot mutate a peer.
    data=Path(data).resolve()
    if not (data/'state/integration_state.json').is_file() or not e19.state_path(data).is_file(): _fail('SOURCE_NOT_INITIALIZED')
    with tempfile.TemporaryDirectory(prefix='tukuyo-ecology-source-') as td:
        snap=Path(td)/'data'
        if any(p.is_symlink() for p in data.rglob('*')): _fail('SOURCE_SYMLINK')
        shutil.copytree(data,snap,ignore=shutil.ignore_patterns(TAG))
        require_alive(snap)
        from tukuyo_v977.whole_state import audit as whole_audit
        if not s18.audit(snap)['ok'] or not e19.audit(snap)['ok'] or not whole_audit(snap)['ok']: _fail('SOURCE_AUDIT')
        ss=s18.ensure_state(snap)[0];st=e19.ensure_state(snap)
        if ss['role']=='UNBOUND': _fail('SOURCE_UNBOUND')
        if s18.public_key(snap)!=trusted: _fail('SOURCE_TRUST')
        payload={'individual_id':_live_identity(snap)['individual_id'],'family_lineage_id':ss['family_lineage_id'],
                 'generation':ss['generation'],'profile':_profile(st['current_evolution_profile']),
                 'source_evolution_state_sha256':st['state_sha256']}
        sk,pub=s18._ensure_key(snap)
        proof={'schema':'tukuyo.v1020.source_attestation/1','public_key':pub,'payload':payload,
               'signature':base64.b64encode(sk.sign(canon(payload))).decode()}
        _verify_source(proof,trusted)
        return proof

def _hash_int(seed,*parts): return int.from_bytes(hashlib.sha256(canon([seed,*parts])).digest(),'big')
def _allocate(total, weights, seed, tag):
    """Largest-remainder proportional allocation, with reproducible fair ties."""
    total=_int(total,0,10**15)
    if not weights: return {}
    if any(type(v) is not int or v<0 for v in weights.values()): _fail('ALLOCATION_WEIGHT')
    demand=sum(weights.values())
    if total>=demand: return dict(weights)
    if not demand: return {k:0 for k in weights}
    out={k:total*w//demand for k,w in weights.items()}
    order=sorted(weights,key=lambda k:(-(total*weights[k]%demand),_hash_int(seed,tag,k)))
    for k in order[:total-sum(out.values())]: out[k]+=1
    assert sum(out.values())==total and all(0<=out[k]<=weights[k] for k in out)
    return out

def _mutate(profile, seed, tick, child_id):
    p={k:round(v*1000000) for k,v in profile.items()};traits=e19.TRAITS
    h=_hash_int(seed,'mutation',tick,child_id)
    recipient=traits[h%5];donors=[k for k in traits if k!=recipient];donor=donors[(h//5)%4]
    amount=min(120000,1000000-p[recipient],p[donor],18000+(h//20)%102001)
    p[recipient]+=amount;p[donor]-=amount
    return _profile({k:p[k]/1000000 for k in traits})

def _join(st, command):
    _keys(command,'kind source source_trust founders')
    if st['tick']!=0: _fail('ADMISSION_CLOSED')
    p=_verify_source(command['source'],command['source_trust']);n=_int(command['founders'],1,8)
    fam=p['family_lineage_id']
    if fam in st['families'] or any(x['source']['public_key']==command['source_trust'] or x['source']['payload']['individual_id']==p['individual_id'] for x in st['families'].values()): _fail('DUPLICATE_FAMILY')
    if len(st['families'])>=MAX_FAMILIES or len(st['agents'])+n>st['config']['max_population']: _fail('POPULATION_BOUNDS')
    if st['resource']<INITIAL_ENERGY*n: _fail('INSUFFICIENT_GENESIS_RESOURCE')
    st['families'][fam]={'source':command['source'],'admission_trust':command['source_trust'],'introduced':n,
                         'births':0,'deaths':0,'max_generation':0}
    for _ in range(n):
        ident=f"E{st['next_agent']:06d}";st['next_agent']+=1
        st['agents'][ident]={'id':ident,'family':fam,'parent':None,'generation':0,'age':0,'energy':INITIAL_ENERGY,'profile':p['profile']}
    st['resource']-=INITIAL_ENERGY*n
    st['metrics']['introduced']+=n
    return {'admitted_family':fam,'introduced':n}

def _tick(st, environment):
    if environment not in e19.ENVIRONMENTS: _fail('ENVIRONMENT')
    if st['tick']>=MAX_TICKS: _fail('TICK_LIMIT')
    cfg=st['config'];agents=st['agents'];seed=st['seed_sha256'];t=st['tick']+1
    before=st['resource']+sum(a['energy'] for a in agents.values())
    regeneration=cfg['regeneration']*(6 if environment=='volatile' else 10)//10
    regenerated=min(cfg['capacity']-st['resource'],regeneration);st['resource']+=regenerated
    requests={};charges={};cooperators=[]
    for ident,a in sorted(agents.items()):
        p=a['profile']
        if environment=='resource':claim=3200+round(3000*p['survival']+500*p['curiosity'])
        elif environment=='research':claim=2700+round(4200*p['curiosity']+1800*p['truthfulness'])
        elif environment=='social':claim=3000+round(3500*p['relationship']+1800*p['integrity'])
        else:claim=2500+round(2000*p['survival']+2000*p['curiosity'])+_hash_int(seed,'weather',t,ident)%1501
        requests[ident]=claim
        charges[ident]=2400+round(400*p['curiosity'])+(600 if environment=='volatile' else 0)
        if cfg['cooperation'] and _hash_int(seed,'cooperate',t,ident)%1000000<round(p['relationship']*1000000):cooperators.append(ident)
    demand=sum(requests.values());intake=_allocate(min(st['resource'],demand),requests,seed,['intake',t])
    st['resource']-=sum(intake.values())
    for ident,a in agents.items():a['energy']+=intake[ident];a['age']+=1
    donations={ident:intake[ident]//5 for ident in cooperators}
    for ident,n in donations.items():agents[ident]['energy']-=n
    need={ident:max(0,charges[ident]+BIRTH_ENERGY-agents[ident]['energy']) for ident in cooperators}
    grants=_allocate(min(sum(donations.values()),sum(need.values())),need,seed,['sharing',t])
    for ident,n in grants.items():agents[ident]['energy']+=n
    # Attribute every grant to actual donors without creating energy. Transfers
    # to oneself are excluded from cooperation statistics.
    remaining=dict(donations);cross=0;shared=0
    for ident,n in sorted(grants.items()):
        funding=_allocate(n,remaining,seed,['funding',t,ident])
        for donor,units in funding.items():
            remaining[donor]-=units
            if donor!=ident:shared+=units
            if agents[donor]['family']!=agents[ident]['family']:cross+=units
    for ident,n in remaining.items():agents[ident]['energy']+=n
    burned=0;overflow=0;deaths=[];births=[]
    for ident,a in list(sorted(agents.items())):
        maintenance=min(a['energy'],charges[ident]);a['energy']-=maintenance;burned+=maintenance
        reason='STARVATION' if maintenance<charges[ident] else ('AGE' if a['age']>=cfg['max_age'] else None)
        if reason:
            returned=min(a['energy'],cfg['capacity']-st['resource']);st['resource']+=returned;overflow+=a['energy']-returned
            deaths.append({'id':ident,'family':a['family'],'generation':a['generation'],'reason':reason})
            st['families'][a['family']]['deaths']+=1;del agents[ident]
    eligible=sorted((ident for ident,a in agents.items() if a['energy']>=BIRTH_THRESHOLD),key=lambda ident:_hash_int(seed,'birth-slot',t,ident))
    for ident in eligible[:cfg['max_population']-len(agents)]:
        a=agents[ident];child=f"E{st['next_agent']:06d}";st['next_agent']+=1
        p=_mutate(a['profile'],seed,t,child);a['energy']-=BIRTH_COST+BIRTH_ENERGY;burned+=BIRTH_COST
        agents[child]={'id':child,'family':a['family'],'parent':ident,'generation':a['generation']+1,'age':0,'energy':BIRTH_ENERGY,'profile':p}
        fam=st['families'][a['family']];fam['births']+=1;fam['max_generation']=max(fam['max_generation'],a['generation']+1)
        births.append({'id':child,'parent':ident,'family':a['family'],'generation':a['generation']+1,
                       'profile':p,'parent_profile':a['profile'],'max_abs_mutation':round(max(abs(p[k]-a['profile'][k]) for k in e19.TRAITS),6)})
    after=st['resource']+sum(a['energy'] for a in agents.values())
    if before+regenerated!=after+burned+overflow: _fail('RESOURCE_CONSERVATION')
    st['tick']=t;st['environment']=environment
    metrics=st['metrics'];metrics['regenerated']+=regenerated;metrics['burned']+=burned;metrics['overflow']+=overflow
    metrics['births']+=len(births);metrics['deaths']+=len(deaths);metrics['shared']+=shared;metrics['cross_family_shared']+=cross
    if sum(intake.values())<demand:metrics['scarcity_ticks']+=1
    report={'tick':t,'environment':environment,'population':len(agents),'resource':st['resource'],
            'requested':demand,'allocated':sum(intake.values()),'regenerated':regenerated,'burned':burned,'overflow':overflow,
            'shared':shared,'cross_family_shared':cross,'births':births,'deaths':deaths,
            'conservation':{'before':before,'after':after,'balanced':True}}
    st['last_tick']=report
    return report

def _transition(old, command, owner):
    if type(command) is not dict: _fail('COMMAND')
    kind=command.get('kind');st=copy.deepcopy(old)
    if kind=='INIT':
        _keys(command,'kind owner_id config seed_sha256 source source_trust founders')
        if old is not None: _fail('REINITIALIZATION')
        if command['owner_id']!=owner: _fail('OWNER')
        cfg=command['config'];_keys(cfg,'capacity regeneration max_population max_age cooperation')
        _int(cfg['capacity'],12000,10000000);_int(cfg['regeneration'],0,cfg['capacity'])
        _int(cfg['max_population'],2,64);_int(cfg['max_age'],3,64)
        if type(cfg['cooperation']) is not bool: _fail('COOPERATION')
        sd=command['seed_sha256']
        if type(sd) is not str or len(sd)!=64 or any(c not in '0123456789abcdef' for c in sd):_fail('SEED')
        st={'schema':'tukuyo.v1020.ecology_model/1','owner_id':owner,'config':cfg,'seed_sha256':sd,'tick':0,'event_seq':0,
            'resource':cfg['capacity'],'next_agent':0,'families':{},'agents':{},'environment':None,'last_tick':None,
            'metrics':{'introduced':0,'births':0,'deaths':0,'regenerated':0,'burned':0,'overflow':0,'shared':0,'cross_family_shared':0,'scarcity_ticks':0}}
        sub={k:command[k] for k in ('source','source_trust','founders')};sub['kind']='JOIN';result=_join(st,sub)
    elif kind=='JOIN':
        if st is None: _fail('NOT_INITIALIZED')
        result=_join(st,command)
    elif kind=='TICK':
        _keys(command,'kind environment')
        if st is None: _fail('NOT_INITIALIZED')
        result=_tick(st,command['environment'])
    else: _fail('COMMAND_KIND')
    st['event_seq']+=1
    if not 0<=st['resource']<=st['config']['capacity'] or len(st['agents'])>st['config']['max_population']: _fail('STATE_BOUNDS')
    if st['config']['capacity']+st['metrics']['regenerated']!=st['resource']+sum(a['energy'] for a in st['agents'].values())+st['metrics']['burned']+st['metrics']['overflow']: _fail('CUMULATIVE_CONSERVATION')
    for fam,row in st['families'].items():
        if row['introduced']+row['births']-row['deaths']!=sum(a['family']==fam for a in st['agents'].values()): _fail('POPULATION_LEDGER')
    return st,result

def was_initialized(data):
    from tukuyo_v977.whole_state import state_path as whole_path
    wp=whole_path(data)
    return root(data).exists() or (wp.is_file() and _read(wp).get('payload',{}).get('component_hashes',{}).get('population_ecology_v1020') is not None)

def _cache(state, head):return {'schema':'tukuyo.v1020.ecology_cache/1','head_sha256':head,'state':state}
def _replay(data):
    owner=_live_identity(data)['individual_id'];pub=s18.public_key(data);prev=ZERO;state=None
    cd=root(data)/'commits';paths=sorted(cd.glob('*.json'))
    if not paths: _fail('JOURNAL_MISSING')
    if set(cd.rglob('*'))!=set(paths): _fail('JOURNAL_FILES')
    for i,path in enumerate(paths,1):
        if path.name!=f'{i:012d}.json': _fail('COMMIT_SEQUENCE')
        rec=_read(path);_keys(rec,'schema seq previous_commit_sha256 command state_sha256 public_key signature commit_sha256')
        if rec['schema']!='tukuyo.v1020.ecology_commit/1' or type(rec['seq']) is not int or rec['seq']!=i or rec['previous_commit_sha256']!=prev: _fail('COMMIT_CHAIN')
        z=dict(rec);head=z.pop('commit_sha256')
        if sha_obj(z)!=head or rec['public_key']!=pub: _fail('COMMIT_BINDING')
        signed=dict(z);sig=signed.pop('signature');_verify_sig(pub,sig,signed)
        state,_=_transition(state,rec['command'],owner)
        if sha_obj(state)!=rec['state_sha256']: _fail('REPLAY_STATE')
        prev=head
    return _cache(state,prev)

def ensure_state(data):
    cached=_replay(data);p=state_path(data)
    if p.is_file():
        seen=_read(p)
        if seen!=cached:
            _fail('COMMITTED_STATE_MISMATCH:cache_tick='+str(seen.get('state',{}).get('tick'))+':journal_tick='+str(cached['state']['tick']))
    # Replay proves internal consistency, not freshness. Bind every read to the
    # last signed whole-state head, including a present cache rolled back along
    # with its journal. Losing that anchor is not permission to accept a prefix.
    from tukuyo_v977 import whole_state as whole
    up=whole.state_path(data)
    if not up.is_file():_fail('RECOVERY_WHOLE_MISSING')
    envelope=_read(up)
    if not whole._verify(envelope,whole._key_paths(data)[1].read_text().strip()):_fail('RECOVERY_WHOLE_SIGNATURE')
    payload=envelope.get('payload',{})
    if payload.get('schema')!=whole.SCHEMA:_fail('RECOVERY_WHOLE_SCHEMA')
    if payload.get('identity')!=_live_identity(data):_fail('RECOVERY_IDENTITY')
    expected=payload.get('component_hashes',{}).get('population_ecology_v1020')
    if expected is None:_fail('RECOVERY_HEAD_MISSING')
    encoded=canon(cached)+b'\n'
    if hashlib.sha256(encoded).hexdigest()!=expected:_fail('RECOVERY_HEAD')
    if not p.is_file():
        # Retry only an already-authorized reconstruction of a missing cache.
        # Existing divergent caches above remain errors, never silent repairs.
        for attempt in range(3):
            atomic_write_bytes(p,encoded)
            if p.is_file() and p.read_bytes()==encoded:break
        else:_fail('CACHE_WRITE_VERIFY')
    return cached

def _commit(data,old,command):
    owner=_live_identity(data)['individual_id'];st,result=_transition(None if old is None else old['state'],command,owner)
    rec={'schema':'tukuyo.v1020.ecology_commit/1','seq':st['event_seq'],'previous_commit_sha256':ZERO if old is None else old['head_sha256'],
         'command':command,'state_sha256':sha_obj(st)}
    sk,pub=s18._ensure_key(data);rec['public_key']=pub;rec['signature']=base64.b64encode(sk.sign(canon(rec))).decode();rec['commit_sha256']=sha_obj(rec)
    atomic_write_bytes(root(data)/'commits'/f'{rec["seq"]:012d}.json',canon(rec)+b'\n')
    cached=_cache(st,rec['commit_sha256']);atomic_write_bytes(state_path(data),canon(cached)+b'\n')
    return cached,result

@transactional()
def init(data, seed='v1020', capacity=240000, regeneration=50000, max_population=24, max_age=18, cooperation=True, founders=3):
    require_alive(data)
    if was_initialized(data): _fail('REINITIALIZATION')
    # Bind the owner once; subsequent imports must already have bound sources.
    if s18.ensure_state(data)[0]['role']=='UNBOUND':s18.founder_init(data)
    e19.ensure_state(data)
    from tukuyo_v977.whole_state import sync
    sync(data)
    pub=s18.public_key(data)
    command={'kind':'INIT','owner_id':_live_identity(data)['individual_id'],
             'config':{'capacity':capacity,'regeneration':regeneration,'max_population':max_population,'max_age':max_age,'cooperation':cooperation},
             'seed_sha256':hashlib.sha256(str(seed).encode()).hexdigest(),'source':_source(data,pub),'source_trust':pub,'founders':founders}
    cached,result=_commit(data,None,command)
    return {'ok':True,'version':VERSION,'admission':result,'summary':_summary(cached),'claim_boundary':CLAIMS}

@transactional()
def join(data, source_data, source_trust_file, founders=3):
    require_alive(data);old=ensure_state(data)
    if old['state']['tick']!=0: _fail('ADMISSION_CLOSED')
    source=Path(source_data).resolve();trusted=Path(source_trust_file).read_text(encoding='utf-8').strip()
    command={'kind':'JOIN','source':_source(source,trusted),'source_trust':trusted,'founders':founders}
    cached,result=_commit(data,old,command)
    return {'ok':True,'version':VERSION,'admission':result,'summary':_summary(cached),'claim_boundary':CLAIMS}

@transactional()
def step(data, environment='resource', ticks=1):
    require_alive(data);_int(ticks,1,64)
    if environment not in e19.ENVIRONMENTS: _fail('ENVIRONMENT')
    cached=ensure_state(data)
    if cached['state']['tick']+ticks>MAX_TICKS:_fail('TICK_LIMIT')
    reports=[]
    for _ in range(ticks):cached,report=_commit(data,cached,{'kind':'TICK','environment':environment});reports.append(report)
    return {'ok':True,'version':VERSION,'ticks':reports,'summary':_summary(cached),'claim_boundary':CLAIMS}

def _summary(cached):
    st=cached['state'];families={}
    for fam,row in st['families'].items():
        aa=[a for a in st['agents'].values() if a['family']==fam]
        families[fam]={'source_individual':row['source']['payload']['individual_id'],'living':len(aa),'births':row['births'],'deaths':row['deaths'],
                       'max_generation':row['max_generation'],'mean_profile':{k:round(sum(a['profile'][k] for a in aa)/len(aa),6) for k in e19.TRAITS} if aa else None}
    profiles={tuple(a['profile'][k] for k in e19.TRAITS) for a in st['agents'].values()}
    return {'tick':st['tick'],'head_sha256':cached['head_sha256'],'population':len(st['agents']),'resource':st['resource'],
            'living_families':sum(row['living']>0 for row in families.values()),'families':families,'distinct_living_profiles':len(profiles),'metrics':st['metrics']}

def audit(data):
    try:
        cached=ensure_state(data)
        return {'ok':True,'version':VERSION,'errors':[],'summary':_summary(cached),'claim_boundary':CLAIMS}
    except Exception as ex:return {'ok':False,'version':VERSION,'errors':[str(ex)],'claim_boundary':CLAIMS}

def status(data):
    cached=ensure_state(data)
    return {'ok':True,'version':VERSION,'summary':_summary(cached),'state':cached,'claim_boundary':CLAIMS}
