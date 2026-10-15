from __future__ import annotations
import base64, copy, hashlib, json, time, math
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from tukuyo_common.atomic_fs import atomic_write_bytes, atomic_write_text
from tukuyo_v977.whole_state import canon, sha_obj, _live_identity
from tukuyo_v1018 import succession as s18

VERSION='v1019'
STATE_SCHEMA='tukuyo.v1019.evolution_state/1'
PACKAGE_SCHEMA='tukuyo.v1019.evolved_successor_package/2'
CAPSULE_SCHEMA='tukuyo.v1019.evolution_capsule/2'
TRAITS=('survival','integrity','curiosity','truthfulness','relationship')
DEFAULT_VALUES=dict(s18.DEFAULT_VALUES)
ATTENUATION=float(s18.ATTENUATION)
MAX_MUTATION=0.12
TRAIT_BUDGET=round(sum(DEFAULT_VALUES.values()),6)
MIN_POP=3
MAX_POP=64
ENVIRONMENTS={
 'resource':{'survival':0.40,'integrity':0.25,'curiosity':0.05,'truthfulness':0.15,'relationship':0.15},
 'research':{'survival':0.10,'integrity':0.15,'curiosity':0.35,'truthfulness':0.30,'relationship':0.10},
 'social':{'survival':0.10,'integrity':0.20,'curiosity':0.10,'truthfulness':0.20,'relationship':0.40},
 'volatile':{'survival':0.25,'integrity':0.20,'curiosity':0.25,'truthfulness':0.20,'relationship':0.10},
}
ZERO='0'*64

def root(data): return Path(data)/'v1019'
def state_path(data): return root(data)/'EVOLUTION_STATE.json'
def issued_dir(data): return root(data)/'issued'
def used_dir(data): return root(data)/'used_packages'
def _read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def _norm(p): return {k:round(max(0.0,min(1.0,float((p or {}).get(k,DEFAULT_VALUES[k])))),6) for k in TRAITS}
def _state_hash(st):
    z=copy.deepcopy(st);z.pop('state_sha256',None);return sha_obj(z)
def _fitness(profile,env):
    p=_norm(profile); w=ENVIRONMENTS[env]
    score=sum(w[k]*p[k] for k in TRAITS)+0.03*min(p['integrity'],p['truthfulness'])
    return round(score,9)
def _phenotype(p):
    p=_norm(p); lead=sorted(p,key=lambda k:(-p[k],k))[0]
    action={'survival':'conserve','integrity':'stabilize','curiosity':'explore','truthfulness':'verify','relationship':'cooperate'}[lead]
    return {'dominant_trait':lead,'bounded_action_bias':action,'profile':p}
def _unit(seed): return int(hashlib.sha256(seed.encode()).hexdigest()[:16],16)/(16**16-1)
def _base_profile(data):
    s=s18.ensure_state(data)[0]
    # An imported v1019 state carries the exact selected parent profile for the
    # next evolutionary round; v1018 keeps the attenuated runtime values.
    if state_path(data).is_file():
        try:
            old=_read(state_path(data))
            if old.get('schema')==STATE_SCHEMA and old.get('individual_id')==_live_identity(data)['individual_id']:
                return _norm(old.get('current_evolution_profile'))
        except Exception: pass
    return _norm(s18.effective_values(data,s))
def _blank(data):
    ident=_live_identity(data); ss=s18.ensure_state(data)[0]
    st={'schema':STATE_SCHEMA,'version':VERSION,'individual_id':ident['individual_id'],'identity_lineage_id':ident['lineage_id'],
        'family_lineage_id':ss.get('family_lineage_id'),'generation':ss.get('generation'),'source_succession_state_sha256':ss.get('state_sha256'),
        'current_evolution_profile':_norm(DEFAULT_VALUES),'inherited_evolution_profile':None,
        'parent_selection_sha256':None,'selection_seq':0,'selection':None,'imported_package_sha256':None,'issued_successor_packages':[],'used_package_sha256':[],
        'bounds':{'max_abs_mutation':MAX_MUTATION,'trait_budget':TRAIT_BUDGET,'population_min':MIN_POP,'population_max':MAX_POP,'fixed_environments':sorted(ENVIRONMENTS)},
        'claim_boundary':{'bounded_generational_evolution':True,'natural_selection_established':False,'literal_genetic_evolution_established':False,
                          'open_ended_evolution_established':False,'general_l5':False}}
    st['state_sha256']=_state_hash(st); return st
def _save_state(data,st):
    commits=root(data)/'commits';commits.mkdir(parents=True,exist_ok=True)
    previous=sorted(commits.glob('*.json'))
    prev=_read(previous[-1])['commit_sha256'] if previous else ZERO
    rec={'schema':'tukuyo.v1019.1.evolution_commit/1','seq':len(previous)+1,'previous_commit_sha256':prev,'state':st}
    sk,pub=s18._ensure_key(data);rec['public_key']=pub;rec['signature']=base64.b64encode(sk.sign(canon(rec))).decode()
    rec['commit_sha256']=sha_obj(rec)
    atomic_write_bytes(commits/(f'{rec["seq"]:012d}.json'),canon(rec)+b'\n')
    atomic_write_bytes(state_path(data),canon(st)+b'\n')

def _committed_state(data):
    prev=ZERO;last=None
    for i,p in enumerate(sorted((root(data)/'commits').glob('*.json')),1):
        rec=_read(p);z=dict(rec);h=z.pop('commit_sha256',None)
        if rec.get('schema')!='tukuyo.v1019.1.evolution_commit/1' or rec.get('seq')!=i or rec.get('previous_commit_sha256')!=prev or sha_obj(z)!=h: raise ValueError('V1019_COMMIT_CHAIN')
        signed=dict(z);sig=signed.pop('signature',None)
        if signed.get('public_key')!=s18.public_key(data): raise ValueError('V1019_COMMIT_KEY')
        try: Ed25519PublicKey.from_public_bytes(base64.b64decode(signed['public_key'],validate=True)).verify(base64.b64decode(sig,validate=True),canon(signed))
        except Exception as ex: raise ValueError('V1019_COMMIT_SIGNATURE') from ex
        last=rec['state']
        if last.get('state_sha256')!=_state_hash(last): raise ValueError('V1019_COMMIT_STATE')
        prev=h
    return last

def _require_whole_binding(data,st):
    from tukuyo_v977 import whole_state as whole
    p=whole.state_path(data)
    if not p.is_file(): raise ValueError('V1019_RECOVERY_WHOLE_MISSING')
    envelope=_read(p)
    if not whole._verify(envelope,whole._key_paths(data)[1].read_text().strip()): raise ValueError('V1019_RECOVERY_WHOLE_SIGNATURE')
    pl=envelope.get('payload',{})
    if pl.get('schema')!=whole.SCHEMA: raise ValueError('V1019_RECOVERY_WHOLE_SCHEMA')
    if pl.get('identity')!=_live_identity(data): raise ValueError('V1019_RECOVERY_IDENTITY')
    expected=pl.get('component_hashes',{}).get('evolution_state_v1019')
    if expected is None: raise ValueError('V1019_RECOVERY_HEAD_MISSING')
    if hashlib.sha256(canon(st)+b'\n').hexdigest()!=expected: raise ValueError('V1019_RECOVERY_HEAD')

def ensure_state(data):
    p=state_path(data); ident=_live_identity(data); ss=s18.ensure_state(data)[0]
    if not p.is_file():
        st=_committed_state(data)
        if st is None: st=_blank(data);_save_state(data,st)
        else:
            from tukuyo_v1019.transaction import ACTIVE
            if not ACTIVE.get(): _require_whole_binding(data,st)
            atomic_write_bytes(p,canon(st)+b'\n')
        return st
    st=_read(p)
    committed=_committed_state(data)
    if committed is not None and st!=committed: raise ValueError('V1019_COMMITTED_STATE_MISMATCH')
    from tukuyo_v1019.transaction import ACTIVE
    if committed is not None and not ACTIVE.get(): _require_whole_binding(data,st)
    if st.get('schema')!=STATE_SCHEMA: raise ValueError('V1019_STATE_SCHEMA')
    if st.get('state_sha256')!=_state_hash(st): raise ValueError('V1019_STATE_HASH')
    if st.get('individual_id')!=ident['individual_id'] or st.get('identity_lineage_id')!=ident['lineage_id']: raise ValueError('V1019_STATE_IDENTITY')
    # Fresh init can create this state before a successor package is imported.
    if (st.get('generation')!=ss.get('generation') or st.get('family_lineage_id')!=ss.get('family_lineage_id')) and int(st.get('selection_seq',0))==0 and not st.get('imported_package_sha256'):
        st=copy.deepcopy(st);st['family_lineage_id']=ss.get('family_lineage_id');st['generation']=ss.get('generation');st['source_succession_state_sha256']=ss.get('state_sha256');st['current_evolution_profile']=_norm(st.get('current_evolution_profile') or DEFAULT_VALUES);st['state_sha256']=_state_hash(st);_save_state(data,st)
    return st

def _budget(profile): return round(sum(_norm(profile).values()),6)
def _transfer(base,recipient,donor,amount):
    p=dict(_norm(base)); amount=max(0.0,min(MAX_MUTATION,float(amount),1.0-p[recipient],p[donor]))
    p[recipient]=round(p[recipient]+amount,6);p[donor]=round(p[donor]-amount,6)
    return p,round(amount,6)
def _candidates(base,environment,population,seed,family,generation):
    if environment not in ENVIRONMENTS: raise ValueError('V1019_UNKNOWN_ENVIRONMENT')
    population=int(population)
    if population<MIN_POP or population>MAX_POP: raise ValueError('V1019_POPULATION_BOUNDS')
    base=_norm(base)
    if abs(_budget(base)-TRAIT_BUDGET)>1e-5: raise ValueError('V1019_TRAIT_BUDGET')
    out=[{'candidate_id':'C000_BASE','profile':base,'max_abs_mutation':0.0,'origin':'BASELINE'}]
    w=ENVIRONMENTS[environment]; recipient=max(TRAITS,key=lambda k:(w[k],k)); donor=min((k for k in TRAITS if k!=recipient),key=lambda k:(w[k],k))
    guided,amt=_transfer(base,recipient,donor,MAX_MUTATION)
    out.append({'candidate_id':'C001_GUIDED','profile':guided,'max_abs_mutation':amt,'origin':'BOUNDED_BUDGET_TRANSFER'})
    for i in range(2,population):
        ri=int(_unit(f'{seed}|{family}|{generation}|{i}|recipient')*len(TRAITS))%len(TRAITS)
        di=int(_unit(f'{seed}|{family}|{generation}|{i}|donor')*(len(TRAITS)-1))%(len(TRAITS)-1)
        recipient=TRAITS[ri]; donors=[k for k in TRAITS if k!=recipient]; donor=donors[di]
        amount=(0.15+0.85*_unit(f'{seed}|{family}|{generation}|{i}|amount'))*MAX_MUTATION
        pp,amt=_transfer(base,recipient,donor,amount)
        out.append({'candidate_id':f'C{i:03d}','profile':pp,'max_abs_mutation':amt,'origin':'BOUNDED_DETERMINISTIC_TRANSFER'})
    for c in out:
        if abs(_budget(c['profile'])-TRAIT_BUDGET)>1e-5: raise ValueError('V1019_CANDIDATE_BUDGET')
        c['fitness']=_fitness(c['profile'],environment);c['profile_sha256']=sha_obj(c['profile'])
    return out

def select(data,environment,population=11,seed='v1019'):
    if environment not in ENVIRONMENTS: raise ValueError('V1019_UNKNOWN_ENVIRONMENT')
    if type(population) is not int or not MIN_POP<=population<=MAX_POP: raise ValueError('V1019_POPULATION_BOUNDS')
    from tukuyo_v1019.lifecycle import require_alive
    require_alive(data)
    data=Path(data);st=ensure_state(data);ss=s18.ensure_state(data)[0]
    if ss.get('role')=='UNBOUND': s18.founder_init(data); ss=s18.ensure_state(data)[0]; st=ensure_state(data)
    base=_norm(st['current_evolution_profile']);seed_digest=hashlib.sha256(str(seed).encode()).hexdigest();cand=_candidates(base,environment,population,seed_digest,ss.get('family_lineage_id'),ss.get('generation'))
    winner=max(cand,key=lambda c:(c['fitness'],c['candidate_id'])); baseline=cand[0]
    sel={'schema':'tukuyo.v1019.selection/2','family_lineage_id':ss.get('family_lineage_id'),'individual_id':st['individual_id'],'generation':ss.get('generation'),
         'environment':environment,'seed_sha256':seed_digest,'population':len(cand),'baseline_profile':base,
         'baseline_fitness':baseline['fitness'],'selected_candidate_id':winner['candidate_id'],'selected_profile':winner['profile'],
         'selected_fitness':winner['fitness'],'fitness_gain':round(winner['fitness']-baseline['fitness'],9),'max_abs_mutation':winner['max_abs_mutation'],'trait_budget':TRAIT_BUDGET,'baseline_budget':_budget(base),'selected_budget':_budget(winner['profile']),
         'candidate_commitment_sha256':sha_obj([{'id':c['candidate_id'],'profile_sha256':c['profile_sha256'],'fitness':c['fitness']} for c in cand])}
    sel['selection_sha256']=sha_obj(sel)
    st=copy.deepcopy(st);st['family_lineage_id']=ss.get('family_lineage_id');st['generation']=ss.get('generation');st['source_succession_state_sha256']=ss.get('state_sha256');st['selection_seq']=int(st.get('selection_seq',0))+1;st['selection']=sel;st['state_sha256']=_state_hash(st)
    _save_state(data,st)
    from tukuyo_v977.whole_state import sync as whole_sync;whole_sync(data)
    return {'ok':True,'version':VERSION,'selection':sel,'phenotype':_phenotype(winner['profile']),
            'claim_boundary':{'bounded_selection':True,'fixed_trait_budget_tradeoff':True,'natural_selection_established':False,'open_ended_evolution_established':False}}

def _runtime_child_profile(selected):
    p=_norm(selected);return {k:round(max(0,min(1,DEFAULT_VALUES[k]+(p[k]-DEFAULT_VALUES[k])*ATTENUATION)),6) for k in TRAITS}
def _capsule_sign(data,payload):
    sk,pub=s18._ensure_key(data);sig=base64.b64encode(sk.sign(canon(payload))).decode();return pub,sig
def _verify_capsule(capsule,parent_trust):
    if capsule.get('schema')!=CAPSULE_SCHEMA or capsule.get('version')!=VERSION: raise ValueError('V1019_CAPSULE_SCHEMA')
    _keys(capsule,'schema version public_key payload signature capsule_sha256','CAPSULE')
    z=dict(capsule);got=z.pop('capsule_sha256',None)
    if got!=sha_obj(z): raise ValueError('V1019_CAPSULE_HASH')
    if capsule.get('public_key')!=parent_trust: raise ValueError('V1019_PARENT_TRUST_ROOT')
    try: Ed25519PublicKey.from_public_bytes(base64.b64decode(parent_trust,validate=True)).verify(base64.b64decode(capsule['signature'],validate=True),canon(capsule['payload']))
    except Exception as e: raise ValueError('V1019_CAPSULE_SIGNATURE') from e
    return capsule['payload']

def export_successor(data,child_id,out,child_public_key_file):
    data=Path(data);st=ensure_state(data);sel=st.get('selection')
    if not sel: raise ValueError('V1019_SELECTION_REQUIRED')
    _verify_selection(sel)
    tmp=root(data)/'staging'/('base-'+hashlib.sha256((str(child_id)+str(time.time_ns())).encode()).hexdigest()[:12]+'.json');tmp.parent.mkdir(parents=True,exist_ok=True)
    base=s18.export_successor(data,child_id,tmp,child_public_key_file,evolution_selection=sel);bp=_read(tmp);tmp.unlink(missing_ok=True)
    child_pub=bp['child_succession_public_key'];runtime=_runtime_child_profile(sel['selected_profile'])
    payload={'schema':'tukuyo.v1019.evolution_capsule_payload/2','version':VERSION,'base_successor_package_sha256':bp['package_sha256'],
             'family_lineage_id':bp['family_lineage_id'],'parent_individual_id':st['individual_id'],'child_individual_id':str(child_id),
             'child_succession_public_key':child_pub,'parent_generation':st.get('generation'),'child_generation':int(st.get('generation') or 0)+1,
             'parent_identity_lineage_id':bp['lineage_certificates'][-1]['payload']['parent_identity_lineage_id'],'selection_proof':sel,'selection_sha256':sel['selection_sha256'],'environment':sel['environment'],'baseline_fitness':sel['baseline_fitness'],'selected_fitness':sel['selected_fitness'],
             'fitness_gain':sel['fitness_gain'],'max_abs_mutation':sel['max_abs_mutation'],'trait_budget':TRAIT_BUDGET,'selected_evolution_profile':_norm(sel['selected_profile']),
             'runtime_inherited_value_profile':runtime,'claim_boundary':{'same_identity':False,'private_memory_transferred':False,'private_keys_transferred':False,'bounded_mutation':True}}
    pub,sig=_capsule_sign(data,payload);cap={'schema':CAPSULE_SCHEMA,'version':VERSION,'public_key':pub,'payload':payload,'signature':sig};cap['capsule_sha256']=sha_obj(cap)
    pkg={'schema':PACKAGE_SCHEMA,'version':VERSION,'base_successor_package':bp,'evolution_capsule':cap,'created_utc_ns':time.time_ns()};pkg['package_sha256']=sha_obj(pkg)
    p=Path(out);p.parent.mkdir(parents=True,exist_ok=True);atomic_write_bytes(p,canon(pkg)+b'\n');issued_dir(data).mkdir(parents=True,exist_ok=True);atomic_write_bytes(issued_dir(data)/(pkg['package_sha256']+'.json'),canon(pkg)+b'\n')
    st=ensure_state(data);st=copy.deepcopy(st);st['issued_successor_packages']=list(st.get('issued_successor_packages') or [])+[{'package_sha256':pkg['package_sha256'],'child_individual_id':str(child_id),'selection_sha256':sel['selection_sha256']}];st['source_succession_state_sha256']=s18.ensure_state(data)[0].get('state_sha256');st['state_sha256']=_state_hash(st);_save_state(data,st)
    from tukuyo_v977.whole_state import sync as whole_sync;whole_sync(data)
    return {'ok':True,'version':VERSION,'package_file':str(p),'package_sha256':pkg['package_sha256'],'base_package_sha256':bp['package_sha256'],'selection_sha256':sel['selection_sha256'],'child_generation':payload['child_generation'],'package_bytes':p.stat().st_size}

def _keys(o,expected,label):
    if not isinstance(o,dict) or set(o)!=set(expected.split()): raise ValueError('V1019_'+label+'_FIELDS')

def _profile(p):
    if not isinstance(p,dict) or set(p)!=set(TRAITS): raise ValueError('V1019_PROFILE_FIELDS')
    if any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1 for v in p.values()): raise ValueError('V1019_PROFILE_RANGE')
    if abs(sum(p.values())-TRAIT_BUDGET)>1e-5: raise ValueError('V1019_TRAIT_BUDGET')
    return dict(p)

def _number(n):
    if type(n) not in (int,float) or not math.isfinite(n): raise ValueError('V1019_NONFINITE_NUMBER')
    return n

def _equal_number(a,b,label):
    if abs(_number(a)-b)>1e-8: raise ValueError('V1019_'+label)

def _verify_selection(sel):
    _keys(sel,'schema family_lineage_id individual_id generation environment seed_sha256 population baseline_profile baseline_fitness selected_candidate_id selected_profile selected_fitness fitness_gain max_abs_mutation trait_budget baseline_budget selected_budget candidate_commitment_sha256 selection_sha256','SELECTION')
    if sel['schema']!='tukuyo.v1019.selection/2': raise ValueError('V1019_SELECTION_SCHEMA')
    z=dict(sel);h=z.pop('selection_sha256')
    if sha_obj(z)!=h: raise ValueError('V1019_SELECTION_HASH')
    env=sel['environment'];pop=sel['population'];generation=sel['generation']
    if env not in ENVIRONMENTS or type(pop) is not int or not MIN_POP<=pop<=MAX_POP or type(generation) is not int or generation<0: raise ValueError('V1019_SELECTION_PARAMETERS')
    if not isinstance(sel['seed_sha256'],str) or len(sel['seed_sha256'])!=64 or any(c not in '0123456789abcdef' for c in sel['seed_sha256']): raise ValueError('V1019_SEED_DIGEST')
    base=_profile(sel['baseline_profile']);selected=_profile(sel['selected_profile'])
    actual=max(abs(selected[k]-base[k]) for k in TRAITS)
    if actual>MAX_MUTATION+1e-8: raise ValueError('V1019_MUTATION_BOUND')
    for field,value in (('max_abs_mutation',actual),('baseline_fitness',_fitness(base,env)),('selected_fitness',_fitness(selected,env)),('fitness_gain',round(_fitness(selected,env)-_fitness(base,env),9)),('trait_budget',TRAIT_BUDGET),('baseline_budget',sum(base.values())),('selected_budget',sum(selected.values()))): _equal_number(sel[field],value,field.upper())
    cand=_candidates(base,env,pop,sel['seed_sha256'],sel['family_lineage_id'],generation)
    winner=max(cand,key=lambda c:(c['fitness'],c['candidate_id']))
    if winner['profile']!=selected or winner['candidate_id']!=sel['selected_candidate_id']: raise ValueError('V1019_SELECTION_WINNER')
    commitment=sha_obj([{'id':c['candidate_id'],'profile_sha256':c['profile_sha256'],'fitness':c['fitness']} for c in cand])
    if commitment!=sel['candidate_commitment_sha256']: raise ValueError('V1019_CANDIDATE_COMMITMENT')
    return sel

def _verify_evolution_payload(pl,bp):
    _keys(pl,'schema version base_successor_package_sha256 family_lineage_id parent_individual_id parent_identity_lineage_id child_individual_id child_succession_public_key parent_generation child_generation selection_proof selection_sha256 environment baseline_fitness selected_fitness fitness_gain max_abs_mutation trait_budget selected_evolution_profile runtime_inherited_value_profile claim_boundary','CAPSULE_PAYLOAD')
    if pl['schema']!='tukuyo.v1019.evolution_capsule_payload/2' or pl['version']!=VERSION: raise ValueError('V1019_PAYLOAD_SCHEMA')
    sel=_verify_selection(pl['selection_proof']);certs=bp.get('lineage_certificates') or []
    if not certs: raise ValueError('V1019_EMPTY_CHAIN')
    s18._verify_chain(certs,bp['family_lineage_id'],bp['child_individual_id']);lp=certs[-1]['payload']
    z=dict(bp);h=z.pop('package_sha256',None)
    if h!=sha_obj(z) or pl['base_successor_package_sha256']!=h: raise ValueError('V1019_BASE_PACKAGE_BINDING')
    for k in ('family_lineage_id','parent_individual_id','parent_identity_lineage_id','child_individual_id','child_succession_public_key','parent_generation','child_generation'):
        if pl[k]!=lp[k] or (k in ('parent_generation','child_generation') and type(pl[k]) is not int): raise ValueError('V1019_LINEAGE_BINDING')
    if (sel['family_lineage_id'],sel['individual_id'],sel['generation'])!=(lp['family_lineage_id'],lp['parent_individual_id'],lp['parent_generation']): raise ValueError('V1019_SELECTION_LINEAGE')
    for k in ('selection_sha256','environment','baseline_fitness','selected_fitness','fitness_gain','max_abs_mutation','trait_budget'):
        if k in ('baseline_fitness','selected_fitness','fitness_gain','max_abs_mutation','trait_budget'):_equal_number(pl[k],sel[k],'SELECTION_CAPSULE_BINDING')
        elif pl[k]!=sel[k]: raise ValueError('V1019_SELECTION_CAPSULE_BINDING')
    selected=_profile(pl['selected_evolution_profile'])
    if selected!=sel['selected_profile']: raise ValueError('V1019_SELECTED_PROFILE_BINDING')
    runtime=pl['runtime_inherited_value_profile']
    if runtime!=_runtime_child_profile(selected) or runtime!=lp['inherited_value_profile']: raise ValueError('V1019_RUNTIME_ATTENUATION_BINDING')
    if lp.get('evolution_commitment')!={'selection_sha256':sel['selection_sha256'],'baseline_profile':sel['baseline_profile'],'selected_profile':selected}: raise ValueError('V1019_CERT_SELECTION_BINDING')
    prev=certs[-2]['payload'].get('evolution_commitment') if len(certs)>1 else None
    baseline=prev['selected_profile'] if prev else DEFAULT_VALUES
    if sel['baseline_profile']!=baseline: raise ValueError('V1019_BASELINE_PROVENANCE')
    if pl['claim_boundary']!={'same_identity':False,'private_memory_transferred':False,'private_keys_transferred':False,'bounded_mutation':True}: raise ValueError('V1019_CLAIM_FIELDS')
    return selected,runtime

def import_successor(data,package_file,parent_trust_file):
    data=Path(data);pkg=_read(package_file)
    _keys(pkg,'schema version base_successor_package evolution_capsule created_utc_ns package_sha256','PACKAGE')
    z=dict(pkg);got=z.pop('package_sha256',None)
    if pkg.get('schema')!=PACKAGE_SCHEMA or pkg.get('version')!=VERSION or got!=sha_obj(z): raise ValueError('V1019_PACKAGE_HASH')
    used=used_dir(data)/(str(got)+'.used')
    if used.exists(): raise ValueError('V1019_PACKAGE_REPLAY')
    trust=Path(parent_trust_file).read_text().strip();cap=pkg['evolution_capsule'];pl=_verify_capsule(cap,trust);bp=pkg['base_successor_package']
    if pl.get('base_successor_package_sha256')!=bp.get('package_sha256'): raise ValueError('V1019_BASE_PACKAGE_BINDING')
    ident=_live_identity(data);pub=s18.public_key(data)
    if pl.get('child_individual_id')!=ident['individual_id'] or pl.get('child_succession_public_key')!=pub: raise ValueError('V1019_WRONG_CHILD')
    selected,runtime=_verify_evolution_payload(pl,bp)
    stage=root(data)/'staging'/'base-import.json';stage.parent.mkdir(parents=True,exist_ok=True);atomic_write_bytes(stage,canon(bp)+b'\n')
    base_res=s18.import_successor(data,stage,parent_trust_file);stage.unlink(missing_ok=True)
    # Apply only the attenuated public heritable profile to live value scoring.
    s18._append(data,'EVOLUTION_PROFILE_APPLIED',{'inherited_value_profile':runtime,'selection_sha256':pl['selection_sha256'],'source_version':VERSION})
    ss=s18.ensure_state(data)[0]
    st=_blank(data);st.update(family_lineage_id=ss.get('family_lineage_id'),generation=ss.get('generation'),source_succession_state_sha256=ss.get('state_sha256'),
        current_evolution_profile=selected,inherited_evolution_profile=selected,parent_selection_sha256=pl['selection_sha256'],imported_package_sha256=got,used_package_sha256=[got])
    st['imported_evolution_package']=pkg
    st['state_sha256']=_state_hash(st);_save_state(data,st);used.parent.mkdir(parents=True,exist_ok=True);atomic_write_text(used,str(time.time_ns()))
    from tukuyo_v977.whole_state import sync as whole_sync;whole_sync(data)
    return {'ok':True,'version':VERSION,'individual_id':ident['individual_id'],'generation':st['generation'],'family_lineage_id':st['family_lineage_id'],'current_evolution_profile':selected,'runtime_inherited_value_profile':runtime,'base_succession':base_res}

def audit(data):
    errs=[]
    try:
        st=ensure_state(data);ss=s18.ensure_state(data)[0];sa=s18.audit(data)
    except Exception as e:return {'ok':False,'version':VERSION,'errors':['STATE:'+type(e).__name__+':'+str(e)]}
    if not sa.get('ok'): errs.append('V1018_SUCCESSION_AUDIT')
    if st.get('family_lineage_id')!=ss.get('family_lineage_id') or st.get('generation')!=ss.get('generation'): errs.append('V1019_LINEAGE_BINDING')
    sel=st.get('selection')
    if sel:
        try:
            _verify_selection(sel)
            if (sel['individual_id'],sel['family_lineage_id'],sel['generation'])!=(st['individual_id'],ss['family_lineage_id'],ss['generation']): raise ValueError('V1019_SELECTION_LINEAGE')
            if sel['baseline_profile']!=st['current_evolution_profile']: raise ValueError('V1019_BASELINE_STATE')
        except Exception as e: errs.append(str(e))
    if st.get('imported_package_sha256'):
        try:
            pkg=st['imported_evolution_package'];z=dict(pkg);h=z.pop('package_sha256')
            if h!=sha_obj(z) or h!=st['imported_package_sha256']: raise ValueError('V1019_IMPORTED_PACKAGE_HASH')
            pl=_verify_capsule(pkg['evolution_capsule'],ss['parent_succession_public_key'])
            selected,runtime=_verify_evolution_payload(pl,pkg['base_successor_package'])
            if selected!=st['inherited_evolution_profile'] or runtime!=ss['inherited_value_profile'] or pl['selection_sha256']!=ss['inherited_evolution_selection_sha256']: raise ValueError('V1019_IMPORTED_STATE_BINDING')
        except Exception as e:errs.append(str(e))
    for row in st.get('issued_successor_packages') or []:
        pp=issued_dir(data)/(str(row.get('package_sha256'))+'.json')
        if not pp.is_file(): errs.append('V1019_ISSUED_PACKAGE_MISSING'); continue
        try:
            q=_read(pp);z=dict(q);ph=z.pop('package_sha256',None)
            if ph!=row.get('package_sha256') or ph!=sha_obj(z): errs.append('V1019_ISSUED_PACKAGE_TAMPER')
            pl=_verify_capsule(q['evolution_capsule'],s18.public_key(data))
            _verify_evolution_payload(pl,q['base_successor_package'])
        except Exception: errs.append('V1019_ISSUED_PACKAGE_MALFORMED')
    return {'ok':not errs,'version':VERSION,'errors':errs,'individual_id':st['individual_id'],'family_lineage_id':st.get('family_lineage_id'),'generation':st.get('generation'),
            'selection_seq':st.get('selection_seq'),'phenotype':_phenotype((sel or {}).get('selected_profile') or st['current_evolution_profile']),
            'claim_boundary':{'bounded_generational_evolution':not errs,'fixed_trait_budget_tradeoff':True,'natural_selection_established':False,'literal_genetic_evolution_established':False,'open_ended_evolution_established':False,'general_l5':False}}
def status(data):
    st=ensure_state(data);return {'ok':audit(data)['ok'],'version':VERSION,'state':st,'audit':audit(data),'phenotype':_phenotype((st.get('selection') or {}).get('selected_profile') or st['current_evolution_profile'])}
def gate_summary(parent,child,grandchild):
    roots=[Path(parent),Path(child),Path(grandchild)]; sts=[ensure_state(r) for r in roots]; aud=[audit(r) for r in roots]
    sels=[s.get('selection') for s in sts]
    checks={'all_audits_pass':all(a['ok'] for a in aud),'one_family_lineage':len({s.get('family_lineage_id') for s in sts})==1,
            'generation_sequence':[s.get('generation') for s in sts]==[0,1,2],'three_distinct_individuals':len({s['individual_id'] for s in sts})==3,
            'parent_and_child_selected':bool(sels[0]) and bool(sels[1]),'bounded_mutation':all((not x) or float(x.get('max_abs_mutation',99))<=MAX_MUTATION+1e-9 for x in sels),
            'nonregressive_local_selection':all((not x) or float(x.get('selected_fitness',-1))>=float(x.get('baseline_fitness',0)) for x in sels),
            'strict_gain_observed':any(x and float(x.get('fitness_gain',0))>0 for x in sels),'environment_shift':bool(sels[0] and sels[1] and sels[0].get('environment')!=sels[1].get('environment')),
            'trait_distribution_changed':bool(sels[0] and sels[1] and _norm(sels[0].get('selected_profile'))!=_norm(sels[1].get('selected_profile')))}
    return {'ok':all(checks.values()),'version':VERSION,'checks':checks,'audits':aud,'environments':[x.get('environment') if x else None for x in sels],
            'fitness_gains':[x.get('fitness_gain') if x else None for x in sels],
            'claim_boundary':{'bounded_generational_evolution_gate_pass':all(checks.values()),'natural_selection_established':False,'24h_generational_ecology_completed':False,'general_l5':False}}

from tukuyo_v1019.transaction import transactional
select=transactional()(select)
export_successor=transactional('out')(export_successor)
import_successor=transactional()(import_successor)
