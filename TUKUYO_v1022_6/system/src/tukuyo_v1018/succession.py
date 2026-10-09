"""TUKUYO v1018 scalable successor lineage.

v1018 removes recursive ancestor-package embedding.  Every generation emits a
small signed edge certificate; successor packages carry a flat certificate
chain.  This keeps proof growth linear, binds each package to the intended
child's succession key, records one-time imports, and keeps inherited values
available to live decision systems through effective_values().
"""
from __future__ import annotations
import base64, hashlib, json, time, uuid, math
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from tukuyo_common.atomic_fs import atomic_write_bytes, atomic_write_text
from tukuyo_v977.whole_state import canon, sha_obj, _live_identity, load_soul

VERSION='v1018'
STATE_SCHEMA='tukuyo.v1018.succession_state/1'
EVENT_SCHEMA='tukuyo.v1018.succession_event/1'
CERT_SCHEMA='tukuyo.v1018.lineage_certificate/1'
CERT_PAYLOAD_SCHEMA='tukuyo.v1018.lineage_certificate_payload/1'
PACKAGE_SCHEMA='tukuyo.v1018.successor_package/1'
ZERO='0'*64
DEFAULT_VALUES={'survival':0.8,'integrity':0.8,'curiosity':0.5,'truthfulness':0.65,'relationship':0.4}
ATTENUATION=0.65
PROHIBITED_TOKENS=('secret','autobiograph','episodic','working_memory','event_history','soul_events','conversation_events','private_notes','relation_note','raw_memory')

def root(data): return Path(data)/'v1018'
def state_path(data): return root(data)/'SUCCESSION_STATE.json'
def events_dir(data): return root(data)/'events'
def key_path(data): return root(data)/'private'/'succession.key'
def pub_path(data): return root(data)/'succession.pub'
def issued_dir(data): return root(data)/'issued'
def used_dir(data): return root(data)/'used_packages'

def _read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def _event_file(data,seq): return events_dir(data)/(f'{int(seq):012d}.json')
def _event_hash(e):
    z=dict(e);z.pop('event_sha256',None);return sha_obj(z)

def _ensure_key(data):
    skp,pkp=key_path(data),pub_path(data);skp.parent.mkdir(parents=True,exist_ok=True)
    if skp.is_file():
        sk=Ed25519PrivateKey.from_private_bytes(base64.b64decode(skp.read_text().strip(),validate=True))
        pub=base64.b64encode(sk.public_key().public_bytes_raw()).decode()
        if pkp.is_file() and pkp.read_text().strip()!=pub: raise ValueError('V1018_KEYPAIR_MISMATCH')
        if not pkp.is_file(): atomic_write_text(pkp,pub)
        return sk,pub
    # A public key without its private half means key loss, not a new identity epoch.
    if pkp.is_file(): raise ValueError('V1018_SUCCESSION_PRIVATE_KEY_MISSING')
    if state_path(data).is_file() or any(events_dir(data).glob('*.json')) or any(issued_dir(data).glob('*.json')): raise ValueError('V1018_SUCCESSION_PRIVATE_KEY_MISSING')
    sk=Ed25519PrivateKey.generate();pub=base64.b64encode(sk.public_key().public_bytes_raw()).decode()
    atomic_write_text(skp,base64.b64encode(sk.private_bytes_raw()).decode(),mode=0o600);atomic_write_text(pkp,pub)
    return sk,pub

def public_key(data): return _ensure_key(data)[1]

def export_public_key(data,out):
    pub=public_key(data);p=Path(out);p.parent.mkdir(parents=True,exist_ok=True);atomic_write_text(p,pub+'\n')
    return {'ok':True,'version':VERSION,'public_key_file':str(p),'public_key_sha256':hashlib.sha256(pub.encode()).hexdigest()}

def _assert_public_payload(o,path='root'):
    if isinstance(o,dict):
        for k,v in o.items():
            lk=str(k).lower()
            if not path.endswith('claim_boundary') and any(t in lk for t in PROHIBITED_TOKENS): raise ValueError('V1018_PRIVATE_FIELD:'+path+'.'+str(k))
            _assert_public_payload(v,path+'.'+str(k))
    elif isinstance(o,list):
        for i,v in enumerate(o): _assert_public_payload(v,path+f'[{i}]')

def _base(data):
    ident=_live_identity(data);_,pub=_ensure_key(data)
    return {'schema':STATE_SCHEMA,'version':VERSION,'individual_id':ident['individual_id'],'identity_lineage_id':ident['lineage_id'],'branch_id':ident['branch_id'],
            'succession_public_key':pub,'role':'UNBOUND','family_lineage_id':None,'generation':None,'parent_individual_id':None,
            'parent_identity_lineage_id':None,'parent_succession_public_key':None,'inherited_value_profile':None,
            'inherited_public_capability_ids':[],'inherited_evolution_selection_sha256':None,'lineage_certificates':[],'issued_successors':[],'used_package_sha256':[],
            'event_count':0,'event_head_sha256':ZERO}

def _scan_events(data):
    d=events_dir(data)
    if not d.is_dir(): return []
    return [_read(p) for p in sorted(d.glob('*.json'))]

def _verify_cert(cert):
    if not isinstance(cert,dict) or cert.get('schema')!=CERT_SCHEMA: raise ValueError('V1018_CERT_SCHEMA')
    if set(cert)!={'schema','version','public_key','payload','signature','certificate_sha256'} or cert.get('version')!=VERSION: raise ValueError('V1018_CERT_FIELDS')
    p=cert.get('payload') or {}; pub=cert.get('public_key')
    if p.get('schema')!=CERT_PAYLOAD_SCHEMA or p.get('version')!=VERSION: raise ValueError('V1018_CERT_PAYLOAD_SCHEMA')
    z=dict(cert);got=z.pop('certificate_sha256',None)
    if got!=sha_obj(z): raise ValueError('V1018_CERT_HASH')
    try: Ed25519PublicKey.from_public_bytes(base64.b64decode(pub,validate=True)).verify(base64.b64decode(cert.get('signature',''),validate=True),canon(p))
    except Exception as e: raise ValueError('V1018_CERT_SIGNATURE') from e
    if p.get('parent_succession_public_key')!=pub: raise ValueError('V1018_CERT_PARENT_KEY_BINDING')
    allowed={'schema','version','family_lineage_id','parent_individual_id','child_individual_id','parent_generation','child_generation','parent_identity_lineage_id','parent_branch_id','parent_succession_public_key','child_succession_public_key','previous_certificate_sha256','inherited_value_profile','inherited_public_capability_ids','mortality_commitment','claim_boundary'}
    if 'evolution_commitment' in p: allowed.add('evolution_commitment')
    if set(p)!=allowed: raise ValueError('V1018_CERT_FIELDS')
    for k in ('parent_generation','child_generation'):
        if type(p[k]) is not int or p[k]<0: raise ValueError('V1018_CERT_GENERATION')
    for k in ('family_lineage_id','parent_individual_id','child_individual_id','parent_identity_lineage_id','parent_branch_id'):
        if not isinstance(p[k],str) or not p[k]: raise ValueError('V1018_CERT_IDENTITY')
    prof=p['inherited_value_profile']
    if not isinstance(prof,dict) or set(prof)!=set(DEFAULT_VALUES) or any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1 for v in prof.values()): raise ValueError('V1018_CERT_PROFILE')
    for k in ('parent_succession_public_key','child_succession_public_key'):
        if len(base64.b64decode(p[k],validate=True))!=32: raise ValueError('V1018_CERT_KEY')
    m=p['mortality_commitment']
    if not isinstance(m,dict) or set(m)!={'schema','individual_id','state_sha256','lifecycle','death_irreversible'} or m['individual_id']!=p['parent_individual_id'] or m['lifecycle']!='DEAD' or m['death_irreversible'] is not True: raise ValueError('V1018_CERT_MORTALITY')
    cb=p['claim_boundary']
    if cb!={'resurrection':False,'private_memory_transferred':False,'private_keys_transferred':False,'bounded_lineage':True}: raise ValueError('V1018_CERT_CLAIM')
    if not isinstance(p['inherited_public_capability_ids'],list) or any(not isinstance(x,str) for x in p['inherited_public_capability_ids']): raise ValueError('V1018_CERT_CAPABILITIES')
    if 'evolution_commitment' in p:
        from tukuyo_v1019.evolution import _profile,_runtime_child_profile,MAX_MUTATION
        ec=p['evolution_commitment']
        if not isinstance(ec,dict) or set(ec)!={'selection_sha256','baseline_profile','selected_profile'}: raise ValueError('V1018_EVOLUTION_COMMITMENT_FIELDS')
        a=_profile(ec['baseline_profile']);b=_profile(ec['selected_profile'])
        if max(abs(a[k]-b[k]) for k in a)>MAX_MUTATION+1e-8 or p['inherited_value_profile']!=_runtime_child_profile(b): raise ValueError('V1018_EVOLUTION_COMMITMENT_PROFILE')
    _assert_public_payload(p); return p

def _verify_chain(certs,family=None,current_child=None):
    if not isinstance(certs,list): raise ValueError('V1018_CERT_CHAIN_TYPE')
    prev_hash=ZERO; prev_child=None; prev_key=None; previous_profile=dict(DEFAULT_VALUES); seen=set(); fam=family
    for i,cert in enumerate(certs):
        p=_verify_cert(cert)
        if int(p.get('parent_generation',-1))!=i or int(p.get('child_generation',-1))!=i+1: raise ValueError('V1018_CERT_GENERATION')
        if p.get('previous_certificate_sha256')!=prev_hash: raise ValueError('V1018_CERT_HASH_LINK')
        if fam is None: fam=p.get('family_lineage_id')
        if p.get('family_lineage_id')!=fam: raise ValueError('V1018_CERT_FAMILY')
        ec=p.get('evolution_commitment')
        if ec and ec['baseline_profile']!=previous_profile: raise ValueError('V1018_EVOLUTION_BASELINE_PROVENANCE')
        previous_profile=ec['selected_profile'] if ec else dict(DEFAULT_VALUES)
        pid,cid=p.get('parent_individual_id'),p.get('child_individual_id')
        if not pid or not cid or pid==cid or pid in seen and pid!=prev_child or cid in seen: raise ValueError('V1018_CERT_IDENTITY_REUSE')
        if prev_child is not None and pid!=prev_child: raise ValueError('V1018_CERT_LINK')
        if prev_key is not None and p['parent_succession_public_key']!=prev_key: raise ValueError('V1018_CERT_KEY_LINK')
        prev_key=p['child_succession_public_key']
        seen.add(pid);seen.add(cid);prev_child=cid;prev_hash=cert['certificate_sha256']
    if current_child is not None and certs and prev_child!=current_child: raise ValueError('V1018_CERT_CURRENT_CHILD')
    return fam,prev_hash

def _derive(data,extra_event=None):
    st=_base(data);prev=ZERO
    for i,e in enumerate(_scan_events(data)+([extra_event] if extra_event else []),1):
        if e.get('schema')!=EVENT_SCHEMA or int(e.get('seq',-1))!=i or e.get('previous_event_sha256')!=prev or e.get('event_sha256')!=_event_hash(e): raise ValueError('V1018_EVENT_CHAIN')
        if e.get('individual_id')!=st['individual_id']: raise ValueError('V1018_EVENT_IDENTITY')
        d=e.get('detail') or {};kind=e.get('kind')
        if kind=='FOUNDER_BOUND':
            if st['role']!='UNBOUND': raise ValueError('V1018_FOUNDER_REBIND')
            st.update(role='FOUNDER',family_lineage_id=d['family_lineage_id'],generation=0,lineage_certificates=[])
        elif kind=='SUCCESSOR_IMPORTED':
            if st['role']!='UNBOUND': raise ValueError('V1018_IMPORT_REBIND')
            st.update(role='SUCCESSOR',family_lineage_id=d['family_lineage_id'],generation=d['generation'],parent_individual_id=d['parent_individual_id'],
                      parent_identity_lineage_id=d['parent_identity_lineage_id'],parent_succession_public_key=d['parent_succession_public_key'],
                      inherited_value_profile=d['inherited_value_profile'],inherited_public_capability_ids=d['inherited_public_capability_ids'],
                      lineage_certificates=d['lineage_certificates'],used_package_sha256=[d['package_sha256']])
        elif kind=='SUCCESSOR_PACKAGE_ISSUED':
            st['issued_successors'].append({'child_individual_id':d['child_individual_id'],'child_succession_public_key':d['child_succession_public_key'],'package_sha256':d['package_sha256']})
        elif kind=='EVOLUTION_PROFILE_APPLIED':
            if st['role']!='SUCCESSOR': raise ValueError('V1018_EVOLUTION_PROFILE_ROLE')
            prof=d.get('inherited_value_profile') or {}
            if set(prof)!=set(DEFAULT_VALUES): raise ValueError('V1018_EVOLUTION_PROFILE_KEYS')
            st['inherited_value_profile']={k:round(max(0,min(1,float(prof[k]))),6) for k in DEFAULT_VALUES}
            st['inherited_evolution_selection_sha256']=d.get('selection_sha256')
        else: raise ValueError('V1018_EVENT_KIND')
        prev=e['event_sha256'];st['event_count']=i;st['event_head_sha256']=prev
    st['state_sha256']=sha_obj({k:v for k,v in st.items() if k!='state_sha256'});return st

def _write_state(data,st): atomic_write_bytes(state_path(data),canon(st)+b'\n')
def ensure_state(data):
    exp=_derive(data);p=state_path(data);repaired=False
    if not p.is_file() or _read(p)!=exp:_write_state(data,exp);repaired=True
    return exp,repaired

def _append(data,kind,detail):
    st,_=ensure_state(data)
    if kind=='SUCCESSOR_IMPORTED' and st['role']!='UNBOUND': raise ValueError('V1018_IMPORT_REBIND')
    if kind=='FOUNDER_BOUND' and st['role']!='UNBOUND': raise ValueError('V1018_FOUNDER_REBIND')
    seq=st['event_count']+1;e={'schema':EVENT_SCHEMA,'version':VERSION,'seq':seq,'individual_id':st['individual_id'],'kind':kind,'detail':detail,'previous_event_sha256':st['event_head_sha256'],'utc_ns':time.time_ns()};e['event_sha256']=_event_hash(e)
    n=_derive(data,extra_event=e)
    p=_event_file(data,seq);p.parent.mkdir(parents=True,exist_ok=True);atomic_write_bytes(p,canon(e)+b'\n');_write_state(data,n);return n,e

def founder_init(data):
    st,_=ensure_state(data)
    if st['role']=='FOUNDER': return {'ok':True,'version':VERSION,'family_lineage_id':st['family_lineage_id'],'generation':0,'already_bound':True}
    if st['role']!='UNBOUND': raise ValueError('V1018_ALREADY_SUCCESSOR')
    fam='fam-'+uuid.uuid4().hex;st,e=_append(data,'FOUNDER_BOUND',{'family_lineage_id':fam})
    return {'ok':True,'version':VERSION,'family_lineage_id':fam,'generation':0,'event_sha256':e['event_sha256']}

def _fresh_child(data):
    reasons=[];d=Path(data)
    try:
        integ=_read(d/'state/integration_state.json')['payload']
        if int(integ.get('learning_events',0))!=0 or int(integ.get('integration_seq',0))!=0: reasons.append('LEARNING_HISTORY')
    except Exception: reasons.append('INTEGRATION_STATE')
    try:
        if int(load_soul(d).get('update_seq',0))!=0: reasons.append('SOUL_HISTORY')
    except Exception: reasons.append('SOUL_STATE')
    op=d/'v1007/ORGANISM2_STATE.json'
    if op.is_file() and int(_read(op).get('seq',0))!=0: reasons.append('ORGANISM_HISTORY')
    hp=d/'v978/HEART_STATE.json'
    if hp.is_file() and int(_read(hp).get('seq',0))!=0: reasons.append('HEART_HISTORY')
    return not reasons,reasons

def effective_values(data,st=None,native=None):
    # native: the values of the soul being judged (default: the live soul). A counterfactual soul (v980's control without
    # this individual's experience) must be judged by its own values, not by the live ones
    st=st or ensure_state(data)[0];native=native if native is not None else (load_soul(data).get('core_values') or {})
    if st.get('role')=='SUCCESSOR' and isinstance(st.get('inherited_value_profile'),dict):
        return {k:round(max(0,min(1,float(st['inherited_value_profile'].get(k,b))+float(native.get(k,b))-b)),6) for k,b in DEFAULT_VALUES.items()}
    return {k:round(float(native.get(k,b)),6) for k,b in DEFAULT_VALUES.items()}

def _child_profile(data,st):
    eff=effective_values(data,st);return {k:round(max(0,min(1,b+(eff[k]-b)*ATTENUATION)),6) for k,b in DEFAULT_VALUES.items()}

def _public_capability_ids(st): return sorted(set(st.get('inherited_public_capability_ids') or []))

def _mortality_state(data):
    from tukuyo_v1007.organism2 import audit as mort_audit
    p=Path(data)/'v1007/ORGANISM2_STATE.json'
    if not p.is_file(): raise ValueError('V1018_MORTALITY_STATE_REQUIRED')
    a=mort_audit(data)
    if not a.get('ok'): raise ValueError('V1018_MORTALITY_AUDIT')
    s=_read(p)
    if s.get('individual_id')!=_live_identity(data)['individual_id'] or not s.get('death_irreversible') or s.get('lifecycle')!='DEAD': raise ValueError('V1018_PARENT_NOT_IRREVERSIBLY_DEAD')
    return {'schema':s.get('schema'),'individual_id':s.get('individual_id'),'state_sha256':s.get('state_sha256'),'lifecycle':'DEAD','death_irreversible':True}

def _make_cert(data,st,child_id,child_pub,evolution_selection=None):
    ident=_live_identity(data);sk,pub=_ensure_key(data);certs=list(st.get('lineage_certificates') or []);_,prev=_verify_chain(certs,st.get('family_lineage_id'),ident['individual_id'] if certs else None)
    payload={'schema':CERT_PAYLOAD_SCHEMA,'version':VERSION,'family_lineage_id':st['family_lineage_id'],'parent_individual_id':ident['individual_id'],'child_individual_id':str(child_id),
             'parent_generation':int(st['generation']),'child_generation':int(st['generation'])+1,'parent_identity_lineage_id':ident['lineage_id'],'parent_branch_id':ident['branch_id'],
             'parent_succession_public_key':pub,'child_succession_public_key':child_pub,'previous_certificate_sha256':prev,
             'inherited_value_profile':_child_profile(data,st),'inherited_public_capability_ids':_public_capability_ids(st),'mortality_commitment':_mortality_state(data),
             'claim_boundary':{'resurrection':False,'private_memory_transferred':False,'private_keys_transferred':False,'bounded_lineage':True}}
    if evolution_selection is not None:
        from tukuyo_v1019.evolution import _runtime_child_profile
        payload['inherited_value_profile']=_runtime_child_profile(evolution_selection['selected_profile'])
        payload['evolution_commitment']={'selection_sha256':evolution_selection['selection_sha256'],'baseline_profile':evolution_selection['baseline_profile'],'selected_profile':evolution_selection['selected_profile']}
    _assert_public_payload(payload);sig=base64.b64encode(sk.sign(canon(payload))).decode();cert={'schema':CERT_SCHEMA,'version':VERSION,'public_key':pub,'payload':payload,'signature':sig};cert['certificate_sha256']=sha_obj(cert);return cert

def export_successor(data,child_id,out,child_public_key_file,evolution_selection=None):
    st,_=ensure_state(data)
    if st['role']=='UNBOUND': raise ValueError('V1018_FAMILY_NOT_BOUND')
    child_pub=Path(child_public_key_file).read_text().strip()
    try:
        if len(base64.b64decode(child_pub,validate=True))!=32: raise ValueError
    except Exception: raise ValueError('V1018_CHILD_PUBLIC_KEY_INVALID')
    cert=_make_cert(data,st,child_id,child_pub,evolution_selection);certs=list(st.get('lineage_certificates') or [])+[cert]
    package={'schema':PACKAGE_SCHEMA,'version':VERSION,'family_lineage_id':st['family_lineage_id'],'child_individual_id':str(child_id),'child_succession_public_key':child_pub,
             'lineage_certificates':certs,'package_created_utc_ns':time.time_ns()};package['package_sha256']=sha_obj(package)
    p=Path(out);p.parent.mkdir(parents=True,exist_ok=True);atomic_write_bytes(p,canon(package)+b'\n');internal=issued_dir(data)/(package['package_sha256']+'.json');internal.parent.mkdir(parents=True,exist_ok=True);atomic_write_bytes(internal,canon(package)+b'\n')
    _append(data,'SUCCESSOR_PACKAGE_ISSUED',{'child_individual_id':str(child_id),'child_succession_public_key':child_pub,'package_sha256':package['package_sha256']})
    return {'ok':True,'version':VERSION,'package_file':str(p),'package_sha256':package['package_sha256'],'generation':len(certs),'certificate_count':len(certs),'package_bytes':p.stat().st_size}

def import_successor(data,package_file,parent_trust_file):
    package=_read(package_file)
    if set(package)!={'schema','version','family_lineage_id','child_individual_id','child_succession_public_key','lineage_certificates','package_created_utc_ns','package_sha256'}: raise ValueError('V1018_PACKAGE_FIELDS')
    z=dict(package);got=z.pop('package_sha256',None)
    if package.get('schema')!=PACKAGE_SCHEMA or package.get('version')!=VERSION or got!=sha_obj(z): raise ValueError('V1018_PACKAGE_HASH')
    ident=_live_identity(data);pub=public_key(data)
    if package.get('child_individual_id')!=ident['individual_id']: raise ValueError('V1018_WRONG_CHILD')
    if package.get('child_succession_public_key')!=pub: raise ValueError('V1018_CHILD_KEY_BINDING')
    used=used_dir(data)/(got+'.used')
    if used.exists(): raise ValueError('V1018_PACKAGE_REPLAY')
    fresh,reasons=_fresh_child(data)
    if not fresh: raise ValueError('V1018_CHILD_NOT_FRESH:'+','.join(reasons))
    certs=package.get('lineage_certificates') or [];fam,_=_verify_chain(certs,package.get('family_lineage_id'),ident['individual_id'])
    if not certs: raise ValueError('V1018_EMPTY_CHAIN')
    last=certs[-1];lp=_verify_cert(last);trust=Path(parent_trust_file).read_text().strip()
    if last.get('public_key')!=trust: raise ValueError('V1018_PARENT_TRUST_ROOT')
    if lp.get('child_succession_public_key')!=pub: raise ValueError('V1018_CHILD_KEY_BINDING')
    st,_=ensure_state(data)
    if got in st['used_package_sha256']: raise ValueError('V1018_PACKAGE_REPLAY')
    if st['role']!='UNBOUND': raise ValueError('V1018_IMPORT_REBIND')
    used.parent.mkdir(parents=True,exist_ok=True);atomic_write_text(used,str(time.time_ns()))
    detail={'family_lineage_id':fam,'generation':int(lp['child_generation']),'parent_individual_id':lp['parent_individual_id'],'parent_identity_lineage_id':lp['parent_identity_lineage_id'],
            'parent_succession_public_key':last['public_key'],'inherited_value_profile':lp['inherited_value_profile'],'inherited_public_capability_ids':lp.get('inherited_public_capability_ids') or [],
            'lineage_certificates':certs,'package_sha256':got}
    st,e=_append(data,'SUCCESSOR_IMPORTED',detail)
    return {'ok':True,'version':VERSION,'individual_id':ident['individual_id'],'family_lineage_id':fam,'generation':st['generation'],'inherited_value_profile':st['inherited_value_profile'],'event_sha256':e['event_sha256']}

def status(data):
    st,_=ensure_state(data);fresh,reasons=_fresh_child(data) if st['role']=='UNBOUND' else (False,['BOUND'])
    return {'ok':True,'version':VERSION,'state':st,'effective_value_profile':effective_values(data,st),'fresh_successor_candidate':fresh,'freshness_reasons':reasons}

def audit(data):
    errs=[]
    try: st,_=ensure_state(data)
    except Exception as e: return {'ok':False,'version':VERSION,'errors':['STATE:'+str(e)]}
    ident=_live_identity(data)
    try:
        if st['succession_public_key']!=public_key(data): errs.append('V1018_KEY_BINDING')
    except Exception as e: errs.append(str(e))
    certs=st.get('lineage_certificates') or []
    if st['role']=='SUCCESSOR':
        try:
            fam,_=_verify_chain(certs,st['family_lineage_id'],ident['individual_id'])
            if len(certs)!=st['generation'] or fam!=st['family_lineage_id']: errs.append('V1018_GENERATION')
            lp=_verify_cert(certs[-1])
            if lp.get('child_succession_public_key')!=st.get('succession_public_key'): errs.append('V1018_CHILD_KEY_BINDING')
        except Exception as e: errs.append('V1018_CHAIN:'+str(e))
    elif st['role']=='FOUNDER' and (st['generation']!=0 or certs): errs.append('V1018_FOUNDER_STATE')
    elif st['role']=='UNBOUND' and (st['generation'] is not None or certs): errs.append('V1018_UNBOUND_STATE')
    # Issued package archive is part of the audit surface. Silent repair is not allowed.
    for row in st.get('issued_successors') or []:
        pp=issued_dir(data)/(str(row.get('package_sha256'))+'.json')
        if not pp.is_file(): errs.append('V1018_ISSUED_PACKAGE_MISSING'); continue
        try:
            q=_read(pp); z=dict(q); ph=z.pop('package_sha256',None)
            if ph!=row.get('package_sha256') or ph!=sha_obj(z): errs.append('V1018_ISSUED_PACKAGE_TAMPER')
        except Exception: errs.append('V1018_ISSUED_PACKAGE_MALFORMED')
    return {'ok':not errs,'version':VERSION,'errors':errs,'individual_id':ident['individual_id'],'role':st['role'],'generation':st['generation'],'certificate_count':len(certs),'lineage_head_sha256':certs[-1]['certificate_sha256'] if certs else ZERO,
            'claim_boundary':{'linear_lineage_proof':True,'child_key_binding':True,'one_time_package_import':True,'irreversible_death_enforced':True,'literal_reproduction_established':False,'generational_evolution_established':False}}

def gate_summary(parent,child,grandchild):
    roots=[Path(parent),Path(child),Path(grandchild)];sts=[ensure_state(x)[0] for x in roots];aud=[audit(x) for x in roots]
    checks={'all_audits_pass':all(a['ok'] for a in aud),'one_family_lineage':len({s['family_lineage_id'] for s in sts})==1,'generations_0_1_2':[s['generation'] for s in sts]==[0,1,2],
            'distinct_individuals':len({s['individual_id'] for s in sts})==3,'distinct_keys':len({s['succession_public_key'] for s in sts})==3,'flat_certificate_depth':[len(s['lineage_certificates']) for s in sts]==[0,1,2]}
    return {'ok':all(checks.values()),'version':VERSION,'checks':checks,'audits':aud}

def run_gate_assay(api,parent_data,child_data,child_id,grandchild_data,grandchild_id):
    from tukuyo_v977.whole_state import sync as whole_sync,experience
    from tukuyo_v1007.organism2 import init as org_init,update as org_update
    from tukuyo_v989.temporal_identity import sync_transitions
    from tukuyo_v1015.living_continuity import ensure_state as living_ensure
    from tukuyo_v1016.society import ensure_state as society_ensure
    parent_data,child_data,grandchild_data=map(Path,(parent_data,child_data,grandchild_data))
    def init_child(d,i):
        api['bridge'].init(api,d,str(i));whole_sync(d);sync_transitions(d);living_ensure(d);society_ensure(d);ensure_state(d);whole_sync(d)
    init_child(child_data,child_id);init_child(grandchild_data,grandchild_id)
    if ensure_state(parent_data)[0]['role']=='UNBOUND': founder_init(parent_data)
    secret='PRIVATE_V1018_GATE_'+uuid.uuid4().hex;experience(parent_data,'learning',0.9,1.0,secret,'');whole_sync(parent_data)
    org_init(parent_data);org_update(parent_data,'INJURY',1.0);org_update(parent_data,'INJURY',1.0);whole_sync(parent_data)
    gd=root(parent_data)/'gate_artifacts';gd.mkdir(parents=True,exist_ok=True)
    ppub=gd/'parent.pub';cpub=gd/'child.pub';gpub=gd/'grand.pub';p2c=gd/'p2c.json';c2g=gd/'c2g.json'
    export_public_key(parent_data,ppub);export_public_key(child_data,cpub);export_successor(parent_data,child_id,p2c,cpub);whole_sync(parent_data);import_successor(child_data,p2c,ppub);whole_sync(child_data)
    org_init(child_data);org_update(child_data,'INJURY',1.0);org_update(child_data,'INJURY',1.0);whole_sync(child_data);export_public_key(grandchild_data,gpub);export_successor(child_data,grandchild_id,c2g,gpub);whole_sync(child_data);import_successor(grandchild_data,c2g,cpub);whole_sync(grandchild_data)
    gs=gate_summary(parent_data,child_data,grandchild_data);gs['private_marker_in_packages']=secret in p2c.read_text() or secret in c2g.read_text();gs['package_bytes']=[p2c.stat().st_size,c2g.stat().st_size];gs['linear_growth_observed']=gs['package_bytes'][1] < gs['package_bytes'][0]*3
    gs['ok']=gs['ok'] and not gs['private_marker_in_packages'] and gs['linear_growth_observed'];return gs

# Stage all multi-file lineage writes before any live publication.
from tukuyo_v1019.transaction import transactional
founder_init=transactional()(founder_init)
export_successor=transactional('out')(export_successor)
import_successor=transactional()(import_successor)
