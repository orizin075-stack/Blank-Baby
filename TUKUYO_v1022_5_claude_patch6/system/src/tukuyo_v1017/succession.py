"""TUKUYO v1017 bounded Parent -> Successor -> Grandchild lineage.

The succession package is deliberately narrower than a state copy.  It carries a
signed lineage proof, a bounded/attenuated value profile and public capability
identifiers.  Private keys, autobiographical/episodic memory, soul-event history,
working memory, relation notes and raw private state never enter the package.

This is a functional successor-lineage model.  It is not a biological reproduction,
consciousness, literal soul transfer or resurrection claim.
"""
from __future__ import annotations
import base64, copy, hashlib, json, time, uuid
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from tukuyo_common.atomic_fs import atomic_write_bytes, atomic_write_text
from tukuyo_v977.whole_state import canon, sha_obj, _live_identity, load_soul

VERSION='v1017'
STATE_SCHEMA='tukuyo.v1017.succession_state/1'
EVENT_SCHEMA='tukuyo.v1017.succession_event/1'
PACKAGE_SCHEMA='tukuyo.v1017.successor_package/1'
PAYLOAD_SCHEMA='tukuyo.v1017.successor_package_payload/1'
ZERO='0'*64
DEFAULT_VALUES={'survival':0.8,'integrity':0.8,'curiosity':0.5,'truthfulness':0.65,'relationship':0.4}
ATTENUATION=0.65
PROHIBITED_TOKENS=(
    'secret','autobiograph','episodic','working_memory','event_history',
    'soul_events','conversation_events','private_notes','relation_note','raw_memory'
)

def root(data): return Path(data)/'v1017'
def state_path(data): return root(data)/'SUCCESSION_STATE.json'
def events_dir(data): return root(data)/'events'
def key_path(data): return root(data)/'private'/'succession.key'
def pub_path(data): return root(data)/'succession.pub'
def issued_dir(data): return root(data)/'issued'

def _read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def _sha_bytes(b): return hashlib.sha256(b).hexdigest()
def _event_file(data,seq): return events_dir(data)/(f'{int(seq):012d}.json')

def _ensure_key(data):
    skp,pkp=key_path(data),pub_path(data);skp.parent.mkdir(parents=True,exist_ok=True)
    if skp.is_file():
        raw=skp.read_text(encoding='utf-8').strip();sk=Ed25519PrivateKey.from_private_bytes(base64.b64decode(raw,validate=True))
        pub=base64.b64encode(sk.public_key().public_bytes_raw()).decode()
        if pkp.is_file() and pkp.read_text(encoding='utf-8').strip()!=pub: raise ValueError('V1017_KEYPAIR_MISMATCH')
        if not pkp.is_file(): atomic_write_text(pkp,pub)
        return sk,pub
    sk=Ed25519PrivateKey.generate();raw=base64.b64encode(sk.private_bytes_raw()).decode();pub=base64.b64encode(sk.public_key().public_bytes_raw()).decode()
    atomic_write_text(skp,raw,mode=0o600);atomic_write_text(pkp,pub);return sk,pub

def public_key(data): return _ensure_key(data)[1]

def export_public_key(data,out):
    p=Path(out);p.parent.mkdir(parents=True,exist_ok=True);atomic_write_text(p,public_key(data)+'\n')
    return {'ok':True,'version':VERSION,'public_key_file':str(p),'public_key_sha256':hashlib.sha256(public_key(data).encode()).hexdigest()}

def _base(data):
    ident=_live_identity(data);_,pub=_ensure_key(data)
    return {'schema':STATE_SCHEMA,'version':VERSION,'individual_id':ident['individual_id'],'identity_lineage_id':ident['lineage_id'],'branch_id':ident['branch_id'],
            'succession_public_key':pub,'role':'UNBOUND','family_lineage_id':None,'generation':None,'parent_individual_id':None,
            'parent_identity_lineage_id':None,'parent_succession_public_key':None,'inherited_value_profile':None,
            'inherited_public_capability_ids':[],'lineage_proof_chain':[],'issued_successors':[],
            'event_count':0,'event_head_sha256':ZERO}

def _event_hash(e):
    z=dict(e);z.pop('event_sha256',None);return sha_obj(z)

def _scan_events(data):
    d=events_dir(data);out=[]
    if not d.is_dir():return out
    for p in sorted(d.glob('*.json')):out.append(_read(p))
    return out

def _verify_envelope(env,expected_pub=None):
    if not isinstance(env,dict) or env.get('schema')!=PACKAGE_SCHEMA or env.get('version')!=VERSION:raise ValueError('V1017_PACKAGE_SCHEMA')
    pub=env.get('public_key')
    if expected_pub is not None and pub!=expected_pub:raise ValueError('V1017_PARENT_TRUST_ROOT')
    p=env.get('payload') or {}
    if p.get('schema')!=PAYLOAD_SCHEMA or p.get('version')!=VERSION:raise ValueError('V1017_PACKAGE_PAYLOAD_SCHEMA')
    z=dict(env);got=z.pop('package_sha256',None)
    if got!=sha_obj(z):raise ValueError('V1017_PACKAGE_HASH')
    try:Ed25519PublicKey.from_public_bytes(base64.b64decode(pub,validate=True)).verify(base64.b64decode(env.get('signature',''),validate=True),canon(p))
    except Exception as e:raise ValueError('V1017_PACKAGE_SIGNATURE') from e
    if p.get('parent_succession_public_key')!=pub:raise ValueError('V1017_PACKAGE_PARENT_KEY_BINDING')
    _assert_public_payload(p)
    _verify_mortality_proof(p.get('mortality_state') or {},p.get('parent_individual_id'))
    return p

def _assert_public_payload(o,path='root'):
    if isinstance(o,dict):
        for k,v in o.items():
            lk=str(k).lower()
            if not path.endswith('claim_boundary') and any(t in lk for t in PROHIBITED_TOKENS):raise ValueError('V1017_PRIVATE_FIELD:'+path+'.'+str(k))
            _assert_public_payload(v,path+'.'+str(k))
    elif isinstance(o,list):
        for i,v in enumerate(o):_assert_public_payload(v,path+f'[{i}]')

def _verify_mortality_proof(s,parent_id):
    if s.get('schema')!='tukuyo.v1007.organism2/1':raise ValueError('V1017_MORTALITY_SCHEMA')
    q=dict(s);h=q.pop('state_sha256',None)
    if h!=sha_obj(q):raise ValueError('V1017_MORTALITY_HASH')
    if s.get('individual_id')!=parent_id:raise ValueError('V1017_MORTALITY_ID')
    if not s.get('death_irreversible') or s.get('lifecycle')!='DEAD':raise ValueError('V1017_PARENT_NOT_IRREVERSIBLY_DEAD')
    return True

def _verify_proof_chain(proofs,family_id=None,current_child=None):
    if not isinstance(proofs,list):raise ValueError('V1017_PROOF_CHAIN_TYPE')
    prev_child=None;seen=[];fam=family_id
    for i,env in enumerate(proofs):
        p=_verify_envelope(env)
        if int(p.get('parent_generation',-1))!=i or int(p.get('child_generation',-1))!=i+1:raise ValueError('V1017_PROOF_GENERATION')
        if fam is None:fam=p.get('family_lineage_id')
        if p.get('family_lineage_id')!=fam:raise ValueError('V1017_PROOF_FAMILY')
        if prev_child is not None and p.get('parent_individual_id')!=prev_child:raise ValueError('V1017_PROOF_LINK')
        if p.get('prior_lineage_proofs')!=proofs[:i]:raise ValueError('V1017_PROOF_PREFIX')
        pid,cid=p.get('parent_individual_id'),p.get('child_individual_id')
        if not pid or not cid or pid==cid:raise ValueError('V1017_PROOF_IDENTITY_REUSE')
        if i==0:
            if pid in seen:raise ValueError('V1017_PROOF_IDENTITY_REUSE')
            seen.append(pid)
        elif pid!=prev_child:
            raise ValueError('V1017_PROOF_LINK')
        if cid in seen:raise ValueError('V1017_PROOF_IDENTITY_REUSE')
        seen.append(cid);prev_child=cid
    if current_child is not None and proofs and prev_child!=current_child:raise ValueError('V1017_PROOF_CURRENT_CHILD')
    return fam,seen

def _derive(data):
    st=_base(data);prev=ZERO
    for i,e in enumerate(_scan_events(data),1):
        if e.get('schema')!=EVENT_SCHEMA or int(e.get('seq',-1))!=i:raise ValueError('V1017_EVENT_SCHEMA_SEQ')
        if e.get('previous_event_sha256')!=prev or e.get('event_sha256')!=_event_hash(e):raise ValueError('V1017_EVENT_CHAIN')
        if e.get('individual_id')!=st['individual_id']:raise ValueError('V1017_EVENT_IDENTITY')
        kind=e.get('kind');d=e.get('detail') or {}
        if kind=='FOUNDER_BOUND':
            if st['role']!='UNBOUND':raise ValueError('V1017_FOUNDER_REBIND')
            st.update({'role':'FOUNDER','family_lineage_id':d['family_lineage_id'],'generation':0,'parent_individual_id':None,'parent_identity_lineage_id':None,'parent_succession_public_key':None,'inherited_value_profile':None,'inherited_public_capability_ids':[],'lineage_proof_chain':[]})
        elif kind=='SUCCESSOR_IMPORTED':
            if st['role']!='UNBOUND':raise ValueError('V1017_IMPORT_REBIND')
            proof=d['package_envelope'];p=_verify_envelope(proof,d['parent_succession_public_key'])
            if p.get('child_individual_id')!=st['individual_id']:raise ValueError('V1017_WRONG_CHILD')
            chain=list(p.get('prior_lineage_proofs') or [])+[proof]
            _verify_proof_chain(chain,p.get('family_lineage_id'),st['individual_id'])
            st.update({'role':'SUCCESSOR','family_lineage_id':p['family_lineage_id'],'generation':int(p['child_generation']),
                       'parent_individual_id':p['parent_individual_id'],'parent_identity_lineage_id':p['parent_identity_lineage_id'],
                       'parent_succession_public_key':d['parent_succession_public_key'],'inherited_value_profile':p['inherited_value_profile'],
                       'inherited_public_capability_ids':sorted(set(p.get('inherited_public_capability_ids') or [])),
                       'lineage_proof_chain':chain})
        elif kind=='SUCCESSOR_PACKAGE_ISSUED':
            if st['role']=='UNBOUND':raise ValueError('V1017_EXPORT_UNBOUND')
            row={'child_individual_id':d['child_individual_id'],'package_sha256':d['package_sha256'],'issued_utc_ns':d['issued_utc_ns']}
            if row not in st['issued_successors']:st['issued_successors'].append(row)
        else:raise ValueError('V1017_EVENT_KIND')
        prev=e['event_sha256'];st['event_count']=i;st['event_head_sha256']=prev
    st['state_sha256']=sha_obj({k:v for k,v in st.items() if k!='state_sha256'})
    return st

def _write_state(data,st):
    atomic_write_bytes(state_path(data),canon(st)+b'\n')

def ensure_state(data):
    exp=_derive(data);p=state_path(data);repaired=False
    if not p.is_file() or _read(p)!=exp:_write_state(data,exp);repaired=True
    return exp,repaired

def repair_startup(data):
    data=Path(data)
    if not (data/'state/integration_state.json').is_file():return {'ok':True,'recovered':False,'action':None}
    _,rep=ensure_state(data);return {'ok':True,'recovered':rep,'action':'V1017_SUCCESSION_STATE_REMATERIALIZED' if rep else None}

def _append(data,kind,detail):
    st,_=ensure_state(data);seq=int(st['event_count'])+1;ev={'schema':EVENT_SCHEMA,'seq':seq,'kind':kind,'individual_id':st['individual_id'],'utc_ns':time.time_ns(),'previous_event_sha256':st['event_head_sha256'],'detail':detail};ev['event_sha256']=_event_hash(ev)
    events_dir(data).mkdir(parents=True,exist_ok=True);atomic_write_bytes(_event_file(data,seq),canon(ev)+b'\n')
    return ensure_state(data)[0],ev

def founder_init(data):
    st,_=ensure_state(data)
    if st['role']!='UNBOUND':raise ValueError('V1017_ALREADY_BOUND')
    fam='fam-'+uuid.uuid4().hex
    st,ev=_append(data,'FOUNDER_BOUND',{'family_lineage_id':fam})
    from tukuyo_v977.whole_state import sync as whole_sync;whole_sync(data)
    return {'ok':True,'version':VERSION,'family_lineage_id':fam,'generation':0,'individual_id':st['individual_id'],'event_sha256':ev['event_sha256']}

def _fresh_child(data):
    d=Path(data);st,_=ensure_state(d);reasons=[]
    if st.get('role')!='UNBOUND' or int(st.get('event_count',0))!=0:reasons.append('SUCCESSION_ALREADY_USED')
    try:
        integ=_read(d/'state/integration_state.json')['payload']
        if int(integ.get('learning_events',0))!=0 or int(integ.get('integration_seq',0))!=0:reasons.append('LEARNING_HISTORY')
    except Exception:reasons.append('INTEGRATION_STATE')
    try:
        soul=load_soul(d)
        if int(soul.get('update_seq',0))!=0:reasons.append('SOUL_HISTORY')
    except Exception:reasons.append('SOUL_STATE')
    lp=d/'v1015/LIVING_STATE.json'
    if lp.is_file():
        q=_read(lp)
        if int(q.get('event_count',0)) or int(q.get('completed_episodes',0)) or int(q.get('interrupted_episodes',0)):reasons.append('LIVING_HISTORY')
    sp=d/'v1016/SOCIETY_STATE.json'
    if sp.is_file():
        q=_read(sp)
        if int(q.get('event_count',0)) or q.get('peers'):reasons.append('SOCIETY_HISTORY')
    op=d/'v1007/ORGANISM2_STATE.json'
    if op.is_file() and int(_read(op).get('seq',0))!=0:reasons.append('ORGANISM_HISTORY')
    for p in (d/'v996/CONVERSATION_GROUNDING_EVENTS.jsonl',d/'v998/SEMANTIC_INFERENCE_EVENTS.jsonl'):
        if p.is_file() and p.stat().st_size>0:reasons.append('COGNITIVE_HISTORY:'+p.parent.name)
    return not reasons,reasons

def _effective_values(data,st=None):
    st=st or ensure_state(data)[0];soul=load_soul(data);native=soul.get('core_values') or {}
    if st.get('role')=='SUCCESSOR' and isinstance(st.get('inherited_value_profile'),dict):
        out={}
        for k,b in DEFAULT_VALUES.items():
            inherited=float(st['inherited_value_profile'].get(k,b));own_delta=float(native.get(k,b))-b
            out[k]=round(max(0.0,min(1.0,inherited+own_delta)),6)
        return out
    return {k:round(float(native.get(k,b)),6) for k,b in DEFAULT_VALUES.items()}

def _child_profile(data,st=None):
    eff=_effective_values(data,st);out={}
    for k,b in DEFAULT_VALUES.items():out[k]=round(max(0.0,min(1.0,b+(eff[k]-b)*ATTENUATION)),6)
    return out

def _public_capability_ids(data,st=None):
    d=Path(data);ids=set((st or ensure_state(data)[0]).get('inherited_public_capability_ids') or [])
    for p in (d/'research_registry_v958/ACTIVE_PRIMITIVES.json',d/'inherited_research_v962/PUBLIC_CAPABILITIES.json'):
        if not p.is_file():continue
        try:q=_read(p)
        except Exception:continue
        for e in q.get('entries',[]):
            cand=e.get('candidate_sha256') or (e.get('public_capability') or {}).get('candidate_sha256')
            if cand:ids.add(str(cand))
    return sorted(ids)

def _mortality_state(data):
    from tukuyo_v1007.organism2 import audit as mort_audit
    p=Path(data)/'v1007/ORGANISM2_STATE.json'
    if not p.is_file():raise ValueError('V1017_MORTALITY_STATE_REQUIRED')
    a=mort_audit(data)
    if not a.get('ok'):raise ValueError('V1017_MORTALITY_AUDIT')
    s=_read(p);_verify_mortality_proof(s,_live_identity(data)['individual_id']);return s

def _make_package(data,child_id):
    st,_=ensure_state(data)
    if st.get('role')=='UNBOUND':raise ValueError('V1017_FAMILY_NOT_BOUND')
    ident=_live_identity(data);child_id=str(child_id)
    if not child_id or child_id==ident['individual_id']:raise ValueError('V1017_CHILD_ID')
    mort=_mortality_state(data);sk,pub=_ensure_key(data)
    prior=copy.deepcopy(st.get('lineage_proof_chain') or [])
    _verify_proof_chain(prior,st.get('family_lineage_id'),ident['individual_id'] if prior else None)
    payload={'schema':PAYLOAD_SCHEMA,'version':VERSION,'family_lineage_id':st['family_lineage_id'],'parent_individual_id':ident['individual_id'],
             'child_individual_id':child_id,'parent_generation':int(st['generation']),'child_generation':int(st['generation'])+1,
             'parent_identity_lineage_id':ident['lineage_id'],'parent_branch_id':ident['branch_id'],'parent_succession_public_key':pub,
             'mortality_state':mort,'inherited_value_profile':_child_profile(data,st),'value_attenuation':ATTENUATION,
             'inherited_public_capability_ids':_public_capability_ids(data,st),'prior_lineage_proofs':prior,'exported_utc_ns':time.time_ns(),
             'claim_boundary':{'state_copy':False,'private_memory_transferred':False,'private_keys_transferred':False,'soul_event_history_transferred':False,'resurrection':False,'bounded_successor_lineage':True}}
    _assert_public_payload(payload)
    sig=base64.b64encode(sk.sign(canon(payload))).decode();env={'schema':PACKAGE_SCHEMA,'version':VERSION,'public_key':pub,'payload':payload,'signature':sig};env['package_sha256']=sha_obj(env)
    return env

def export_successor(data,child_id,out):
    env=_make_package(data,child_id);p=env['payload'];internal=issued_dir(data)/(env['package_sha256']+'.json');internal.parent.mkdir(parents=True,exist_ok=True);atomic_write_bytes(internal,canon(env)+b'\n')
    st,ev=_append(data,'SUCCESSOR_PACKAGE_ISSUED',{'child_individual_id':str(child_id),'package_sha256':env['package_sha256'],'issued_utc_ns':p['exported_utc_ns']})
    op=Path(out);op.parent.mkdir(parents=True,exist_ok=True);atomic_write_bytes(op,canon(env)+b'\n')
    from tukuyo_v977.whole_state import sync as whole_sync;whole_sync(data)
    return {'ok':True,'version':VERSION,'package_file':str(op),'package_sha256':env['package_sha256'],'family_lineage_id':p['family_lineage_id'],'parent_generation':p['parent_generation'],'child_generation':p['child_generation'],'parent_public_key':env['public_key'],'event_sha256':ev['event_sha256']}

def import_successor(data,package_file,parent_trust_file):
    env=_read(package_file);trust=Path(parent_trust_file).read_text(encoding='utf-8').strip();p=_verify_envelope(env,trust);ident=_live_identity(data)
    if p.get('child_individual_id')!=ident['individual_id']:raise ValueError('V1017_WRONG_CHILD')
    fresh,reasons=_fresh_child(data)
    if not fresh:raise ValueError('V1017_CHILD_NOT_FRESH:'+','.join(reasons))
    prior=list(p.get('prior_lineage_proofs') or [])
    fam,_=_verify_proof_chain(prior,p.get('family_lineage_id'),p.get('parent_individual_id') if prior else None)
    if fam is not None and fam!=p.get('family_lineage_id'):raise ValueError('V1017_FAMILY_MISMATCH')
    if int(p.get('parent_generation',-1))!=len(prior) or int(p.get('child_generation',-1))!=len(prior)+1:raise ValueError('V1017_GENERATION_BINDING')
    _,ev=_append(data,'SUCCESSOR_IMPORTED',{'parent_succession_public_key':trust,'package_envelope':env})
    st,_=ensure_state(data)
    from tukuyo_v977.whole_state import sync as whole_sync;whole_sync(data)
    return {'ok':True,'version':VERSION,'individual_id':ident['individual_id'],'family_lineage_id':st['family_lineage_id'],'generation':st['generation'],'parent_individual_id':st['parent_individual_id'],'inherited_value_profile':st['inherited_value_profile'],'inherited_public_capability_ids':st['inherited_public_capability_ids'],'event_sha256':ev['event_sha256']}

def status(data):
    st,_=ensure_state(data);fresh,reasons=_fresh_child(data) if st.get('role')=='UNBOUND' else (False,['BOUND'])
    return {'ok':True,'version':VERSION,'state':st,'effective_value_profile':_effective_values(data,st),'fresh_successor_candidate':fresh,'freshness_reasons':reasons,
            'claim_boundary':{'bounded_three_generation_lineage_supported':True,'private_memory_transfer':False,'private_key_transfer':False,'resurrection':False,'literal_reproduction_established':False,'general_l5':False}}

def audit(data):
    errors=[]
    try:st,rep=ensure_state(data)
    except Exception as e:return {'ok':False,'version':VERSION,'errors':['STATE:'+type(e).__name__+':'+str(e)]}
    ident=_live_identity(data);q=dict(st);h=q.pop('state_sha256',None)
    if h!=sha_obj(q):errors.append('V1017_STATE_HASH')
    if st.get('individual_id')!=ident['individual_id'] or st.get('identity_lineage_id')!=ident['lineage_id'] or st.get('branch_id')!=ident['branch_id']:errors.append('V1017_IDENTITY_BINDING')
    if st.get('succession_public_key')!=public_key(data):errors.append('V1017_SUCCESSION_KEY_BINDING')
    role=st.get('role');gen=st.get('generation');proofs=st.get('lineage_proof_chain') or []
    if role=='UNBOUND':
        if gen is not None or st.get('family_lineage_id') is not None or proofs:errors.append('V1017_UNBOUND_STATE')
    elif role=='FOUNDER':
        if gen!=0 or st.get('parent_individual_id') is not None or proofs or not st.get('family_lineage_id'):errors.append('V1017_FOUNDER_STATE')
    elif role=='SUCCESSOR':
        if not isinstance(gen,int) or gen<1 or len(proofs)!=gen:errors.append('V1017_SUCCESSOR_GENERATION')
        try:
            fam,seen=_verify_proof_chain(proofs,st.get('family_lineage_id'),ident['individual_id'])
            if fam!=st.get('family_lineage_id'):errors.append('V1017_SUCCESSOR_FAMILY')
            last=proofs[-1]['payload']
            if st.get('parent_individual_id')!=last.get('parent_individual_id') or st.get('parent_succession_public_key')!=proofs[-1].get('public_key'):errors.append('V1017_PARENT_BINDING')
            if st.get('parent_identity_lineage_id')==ident['lineage_id']:errors.append('V1017_IDENTITY_LINEAGE_REUSE')
        except Exception as e:errors.append('V1017_PROOF:'+str(e))
    else:errors.append('V1017_ROLE')
    if int(st.get('event_count',-1))!=len(_scan_events(data)):errors.append('V1017_EVENT_COUNT')
    # Materialized state and packages may contain only bounded public lineage information.
    raw=json.dumps({'state':st,'issued':[p.name for p in issued_dir(data).glob('*.json')] if issued_dir(data).is_dir() else []},ensure_ascii=False,sort_keys=True).lower()
    if any(t in raw for t in ('private_notes','working_memory','autobiographical_archive','soul_events')):errors.append('V1017_PRIVATE_STATE_LEAK')
    return {'ok':not errors,'version':VERSION,'errors':errors,'individual_id':ident['individual_id'],'role':role,'family_lineage_id':st.get('family_lineage_id'),'generation':gen,'proof_depth':len(proofs),'event_count':st.get('event_count'),
            'claim_boundary':{'parent_successor_grandchild_gate_ready':not errors,'successor_not_resurrection':True,'individual_identity_separation':True,'private_memory_noninheritance':True,'private_key_noninheritance':True,'bounded_value_bias_inheritance':True,'literal_reproduction_established':False,'genetic_evolution_established':False,'24h_generational_ecology_completed':False,'general_l5':False}}

def gate_summary(parent,child,grandchild):
    roots=[Path(parent),Path(child),Path(grandchild)];aud=[audit(x) for x in roots];sts=[ensure_state(x)[0] for x in roots]
    ids=[s['individual_id'] for s in sts];families=[s.get('family_lineage_id') for s in sts];gens=[s.get('generation') for s in sts];keys=[s.get('succession_public_key') for s in sts];identity_lineages=[s.get('identity_lineage_id') for s in sts]
    checks={'all_audits_pass':all(a.get('ok') for a in aud),'three_distinct_individuals':len(set(ids))==3,'three_distinct_identity_lineages':len(set(identity_lineages))==3,'three_distinct_succession_keys':len(set(keys))==3,
            'one_family_lineage':len(set(families))==1 and families[0] is not None,'generations_0_1_2':gens==[0,1,2],
            'child_parent_binding':sts[1].get('parent_individual_id')==ids[0],'grandchild_parent_binding':sts[2].get('parent_individual_id')==ids[1],
            'proof_depth_0_1_2':[len(s.get('lineage_proof_chain') or []) for s in sts]==[0,1,2]}
    return {'ok':all(checks.values()),'version':VERSION,'checks':checks,'individual_ids':ids,'family_lineage_id':families[0] if families else None,'generations':gens,'audits':aud,
            'claim_boundary':{'parent_successor_grandchild_gate_pass':all(checks.values()),'successor_not_resurrection':True,'three_generation_lineage_exercised':True,'literal_reproduction_established':False,'generational_evolution_established':False,'general_l5':False}}

def run_gate_assay(api,parent_data,child_data,child_id,grandchild_data,grandchild_id):
    """One-process bounded v1017 integration assay.

    The release startup guard is still exercised by the outer CLI once; the assay then
    creates the two fresh successor roots inside the same verified process so the test
    cost does not scale with repeated full-release verification.
    """
    parent_data,child_data,grandchild_data=map(Path,(parent_data,child_data,grandchild_data))
    if (child_data/'state/integration_state.json').exists() or (grandchild_data/'state/integration_state.json').exists():raise ValueError('V1017_GATE_CHILD_ROOT_MUST_BE_FRESH')
    pi=_live_identity(parent_data)
    if pi['individual_id'] in (str(child_id),str(grandchild_id)) or str(child_id)==str(grandchild_id):raise ValueError('V1017_GATE_DISTINCT_IDS')
    from tukuyo_v977.whole_state import sync as whole_sync,audit as whole_audit,experience
    from tukuyo_v989.temporal_identity import sync_transitions
    from tukuyo_v1015.living_continuity import ensure_state as living_ensure
    from tukuyo_v1016.society import ensure_state as society_ensure
    from tukuyo_v1007.organism2 import init as org_init,update as org_update
    def init_child(d,i):
        api['bridge'].init(api,d,str(i));whole_sync(d);sync_transitions(d);living_ensure(d);society_ensure(d);ensure_state(d);whole_sync(d)
    init_child(child_data,child_id);init_child(grandchild_data,grandchild_id)
    if ensure_state(parent_data)[0]['role']=='UNBOUND':founder_init(parent_data)
    # Give the founder a private marker and a measurable bounded value change.
    secret='PRIVATE_V1017_GATE_'+uuid.uuid4().hex
    experience(parent_data,'vow',0.9,0.9,secret,'peer-private')
    for _ in range(3):experience(parent_data,'learning',0.9,1.0,'founder-learning','')
    whole_sync(parent_data);parent_eff=_effective_values(parent_data)['curiosity']
    org_init(parent_data);org_update(parent_data,'INJURY',1.0);pr=org_update(parent_data,'INJURY',1.0);whole_sync(parent_data)
    if not pr['state']['death_irreversible']:raise ValueError('V1017_GATE_PARENT_DEATH')
    gd=root(parent_data)/'gate_artifacts';gd.mkdir(parents=True,exist_ok=True);ppub=gd/'parent.pub';p2c=gd/'parent_to_child.json';export_public_key(parent_data,ppub);export_successor(parent_data,child_id,p2c)
    private_leak=secret in p2c.read_text(encoding='utf-8');import_successor(child_data,p2c,ppub);child_inherited=ensure_state(child_data)[0]['inherited_value_profile']['curiosity']
    # Child develops independently before becoming the next deceased predecessor.
    experience(child_data,'learning',0.7,0.9,'child-own-learning','');whole_sync(child_data)
    org_init(child_data);org_update(child_data,'INJURY',1.0);cr=org_update(child_data,'INJURY',1.0);whole_sync(child_data)
    if not cr['state']['death_irreversible']:raise ValueError('V1017_GATE_CHILD_DEATH')
    cpub=gd/'child.pub';c2g=gd/'child_to_grandchild.json';export_public_key(child_data,cpub);export_successor(child_data,grandchild_id,c2g);import_successor(grandchild_data,c2g,cpub)
    summary=gate_summary(parent_data,child_data,grandchild_data);summary['checks']['private_history_not_in_package']=not private_leak
    summary['checks']['attenuated_founder_value_profile']=DEFAULT_VALUES['curiosity'] < child_inherited < parent_eff
    summary['checks']['all_whole_audits_pass']=all(whole_audit(x).get('ok') for x in (parent_data,child_data,grandchild_data))
    summary['ok']=all(summary['checks'].values());summary['parent_effective_curiosity']=parent_eff;summary['child_inherited_curiosity']=child_inherited
    summary['claim_boundary']['private_history_noninheritance_exercised']=True;summary['claim_boundary']['bounded_value_attenuation_exercised']=True
    return summary
