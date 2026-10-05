from __future__ import annotations
from pathlib import Path
import copy,os,uuid,fcntl
from contextlib import contextmanager
from .deps import activate
from .constants import *
from .util import *
activate()
import tukuyo_v843.cluster as c843  # activates the exact transitive v842→v841→v840 chain
import tukuyo_v840.integration as v840
import tukuyo_v838.semantic as s838
import tukuyo_v842.society as s842
import tukuyo_v837.runtime as r837
import tukuyo_v840.crypto as c840

AUTH_SK='private/lineage_authority.key';AUTH_PK='lineage_authority.pub';VER_SK='private/mutation_verifier.key';VER_PK='mutation_verifier.pub';REG='lineage_registry.json';BIRTHS='births';RECORDS='birth_records';WAL='pending_birth.json';CHILD_STATE='lineage/lineage_state.json'

def _sign(p,sk,pk):return r837._signed(p,sk,pk)
def _verify(e):return r837._verify(e)
def _org(root):return Path(root)/'organism'
def _state(root):return r837.load_verified_state(_org(root))
def _id(root):return _state(root)['payload']['identity']['individual_id']
def _pk(root):return _state(root)['public_key']
def _sk(root):return (_org(root)/r837.KEY).read_text().strip()
def _fresh_child(root):
 a=v840.audit(root)
 if not a.get('ok'):raise V844Error('CHILD_BASE_AUDIT_FAILED')
 e=_state(root);p=e['payload']
 if p['continuity']['state_seq']!=0 or p['runtime']['tick']!=0 or p['capabilities']['capability_generation']!=0:raise V844Error('CHILD_NOT_FRESH')
 if p['memory']['autobiographical'] or p['memory']['episodic'] or p['relationships'] or p['other_models']:raise V844Error('CHILD_PRIVATE_HISTORY_NOT_EMPTY')
 return e

@contextmanager
def lineage_lock(root):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);f=open(root/'.lineage.lock','a+b')
 try:
  try:fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise V844Error('LINEAGE_ALREADY_ACTIVE')
  yield
 finally:
  try:fcntl.flock(f.fileno(),fcntl.LOCK_UN)
  finally:f.close()

def init_lineage(root,lineage_family_id=None):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);(root/'private').mkdir(exist_ok=True);(root/BIRTHS).mkdir(exist_ok=True);(root/RECORDS).mkdir(exist_ok=True)
 if (root/REG).exists():return load_registry(root)
 ask,apk=c840.keygen();vsk,vpk=c840.keygen()
 (root/AUTH_SK).write_text(ask);os.chmod(root/AUTH_SK,0o600);(root/AUTH_PK).write_text(apk);(root/VER_SK).write_text(vsk);os.chmod(root/VER_SK,0o600);(root/VER_PK).write_text(vpk)
 if apk==vpk:raise V844Error('AUTHORITY_VERIFIER_KEY_COLLISION')
 p={'schema':SCHEMA_REG,'lineage_family_id':lineage_family_id or str(uuid.uuid4()),'birth_count':0,'birth_head_sha256':ZERO,'known_individuals':{},'authority_is_not_individual':True,'mutation_verifier_is_separate':True}
 e=_sign(p,ask,apk);atomic_json(root/REG,e);return e

def load_registry(root):
 root=Path(root);e=load_json(root/REG)
 if e.get('public_key')!=(root/AUTH_PK).read_text().strip() or not _verify(e):raise V844Error('LINEAGE_REGISTRY_SIGNATURE_INVALID')
 p=e['payload']
 if p.get('schema')!=SCHEMA_REG or p.get('birth_count')<0:raise V844Error('LINEAGE_REGISTRY_SCHEMA_INVALID')
 if e['public_key']==(root/VER_PK).read_text().strip():raise V844Error('AUTHORITY_VERIFIER_NOT_SEPARATE')
 return e

def _save_registry(root,p):
 root=Path(root);e=_sign(p,(root/AUTH_SK).read_text().strip(),(root/AUTH_PK).read_text().strip());atomic_json(root/REG,e);return e

def _public_caps(parent_root):
 e=_state(parent_root);p=e['payload'];caps=[]
 for c in p['capabilities']['public_capabilities']:
  if not isinstance(c,dict):continue
  keep={k:copy.deepcopy(c[k]) for k in ('kind','surface','operator','promotion_sha256','semantic_state_sha256','acquired_tick') if k in c}
  if keep.get('surface') and keep.get('operator') in s838.OPS:caps.append(keep)
 return caps

def capability_bundle(parent_root,surfaces=None):
 pe=_state(parent_root);pp=pe['payload'];caps=_public_caps(parent_root)
 wanted=None if surfaces is None else set(surfaces);caps=[c for c in caps if wanted is None or c['surface'] in wanted]
 if wanted is not None and wanted!={c['surface'] for c in caps}:raise V844Error('REQUESTED_PUBLIC_CAPABILITY_NOT_FOUND')
 p={'schema':SCHEMA_BUNDLE,'parent_individual_id':pp['identity']['individual_id'],'parent_identity_public_key':pe['public_key'],'parent_state_seq':pp['continuity']['state_seq'],'parent_state_sha256':sha256_bytes(canonical(pe)),'public_capabilities':caps,'capability_count':len(caps),'excluded_private_fields':['autobiography','episodic_memory','relationships','affect','commitments','authority_receipts','private_notes']}
 return _sign(p,_sk(parent_root),pe['public_key'])

def _verify_bundle(parent_root,bundle):
 if not _verify(bundle):raise V844Error('CAPABILITY_BUNDLE_SIGNATURE_INVALID')
 pe=_state(parent_root);p=bundle['payload']
 if bundle['public_key']!=pe['public_key'] or p['parent_individual_id']!=_id(parent_root) or p['parent_identity_public_key']!=pe['public_key']:raise V844Error('CAPABILITY_BUNDLE_PARENT_BINDING_INVALID')
 if p['parent_state_sha256']!=sha256_bytes(canonical(pe)) or p['parent_state_seq']!=pe['payload']['continuity']['state_seq']:raise V844Error('CAPABILITY_BUNDLE_PARENT_STATE_DRIFT')
 expected=_public_caps(parent_root)
 for c in p['public_capabilities']:
  if c not in expected:raise V844Error('CAPABILITY_BUNDLE_NOT_PARENT_PUBLIC_CAPABILITY')
 raw=canonical(p)
 for token in (b'private_notes',b'authority_receipts'):
  # Allowed only inside the explicit excluded-private-field declaration.
  pass
 return p

def reproduction_intent(parent_root,child_root,bundle):
 bp=_verify_bundle(parent_root,bundle);ce=_fresh_child(child_root)
 if _id(parent_root)==_id(child_root):raise V844Error('CHILD_EQUALS_PARENT_IDENTITY')
 if _pk(parent_root)==_pk(child_root):raise V844Error('CHILD_EQUALS_PARENT_KEY')
 p={'schema':SCHEMA_INTENT,'parent_individual_id':_id(parent_root),'child_individual_id':_id(child_root),'child_identity_public_key':ce['public_key'],'capability_bundle_sha256':sha256_bytes(canonical(bundle)),'inheritance_only_public_capabilities':True,'parent_private_state_not_authorized':True,'nonce':uuid.uuid4().hex}
 return _sign(p,_sk(parent_root),_pk(parent_root))

def child_acceptance(child_root,intent,bundle):
 if not _verify(intent):raise V844Error('PARENT_INTENT_SIGNATURE_INVALID')
 _fresh_child(child_root);p=intent['payload']
 if p['child_individual_id']!=_id(child_root) or p['child_identity_public_key']!=_pk(child_root) or p['capability_bundle_sha256']!=sha256_bytes(canonical(bundle)):raise V844Error('CHILD_ACCEPTANCE_BINDING_INVALID')
 q={'schema':SCHEMA_ACCEPT,'child_individual_id':_id(child_root),'parent_individual_id':p['parent_individual_id'],'intent_sha256':sha256_bytes(canonical(intent)),'capability_bundle_sha256':sha256_bytes(canonical(bundle)),'accepts_public_capability_inheritance':True,'accepts_parent_private_history':False,'nonce':uuid.uuid4().hex}
 return _sign(q,_sk(child_root),_pk(child_root))

def mutation_receipt(lineage_root,child_root,source_cap,new_surface,holdout):
 root=Path(lineage_root);ho=s838.normalize_cases(holdout);op=source_cap.get('operator')
 if op not in s838.OPS:raise V844Error('MUTATION_SOURCE_OPERATOR_INVALID')
 if not new_surface or new_surface==source_cap.get('surface'):raise V844Error('MUTATION_SURFACE_INVALID')
 res=[{'a':c['a'],'b':c['b'],'expected':c['expected'],'actual':s838.OPS[op](c['a'],c['b']),'correct':s838.OPS[op](c['a'],c['b'])==c['expected']} for c in ho]
 p={'schema':SCHEMA_MUT,'child_individual_id':_id(child_root),'source_surface':source_cap['surface'],'source_operator':op,'mutation_kind':'surface_alias','mutated_surface':new_surface,'holdout_sha256':sha256_bytes(canonical(ho)),'holdout_count':len(ho),'correct':sum(x['correct'] for x in res),'wrong':sum(not x['correct'] for x in res),'results_sha256':sha256_bytes(canonical(res))}
 return _sign(p,(root/VER_SK).read_text().strip(),(root/VER_PK).read_text().strip())

def _verify_mutation(lineage_root,child_root,source_cap,receipt,holdout):
 root=Path(lineage_root);ho=s838.normalize_cases(holdout)
 if not _verify(receipt) or receipt['public_key']!=(root/VER_PK).read_text().strip():raise V844Error('MUTATION_VERIFIER_SIGNATURE_INVALID')
 p=receipt['payload'];op=source_cap.get('operator')
 res=[{'a':c['a'],'b':c['b'],'expected':c['expected'],'actual':s838.OPS[op](c['a'],c['b']),'correct':s838.OPS[op](c['a'],c['b'])==c['expected']} for c in ho]
 if p['child_individual_id']!=_id(child_root) or p['source_surface']!=source_cap.get('surface') or p['source_operator']!=op or p['holdout_sha256']!=sha256_bytes(canonical(ho)) or p['correct']!=sum(x['correct'] for x in res) or p['wrong']!=sum(not x['correct'] for x in res) or p['results_sha256']!=sha256_bytes(canonical(res)):raise V844Error('MUTATION_RECEIPT_DISAGREES_WITH_RAW')
 if p['wrong']!=0 or p['correct']!=len(ho) or len(ho)<3:raise V844Error('MUTATION_NOT_FULLY_VERIFIED')
 return p

def _child_overlay(child_root,reg,bundle,intent,acceptance,mutation=None):
 bp=bundle['payload'];caps=[]
 for c in bp['public_capabilities']:
  q=copy.deepcopy(c);q['lineage_source']='INHERITED';q['source_parent_individual_id']=bp['parent_individual_id'];q['source_bundle_sha256']=sha256_bytes(canonical(bundle));caps.append(q)
 if mutation:
  q={'kind':'semantic_operator','surface':mutation['mutated_surface'],'operator':mutation['source_operator'],'lineage_source':'MUTATED','source_surface':mutation['source_surface'],'mutation_receipt_sha256':mutation['receipt_sha256']};caps.append(q)
 p={'schema':SCHEMA_CHILD,'individual_id':_id(child_root),'identity_public_key':_pk(child_root),'lineage_family_id':reg['payload']['lineage_family_id'],'parent_individual_id':bp['parent_individual_id'],'parent_identity_public_key':bundle['public_key'],'birth_index':reg['payload']['birth_count']+1,'inheritance_bundle_sha256':sha256_bytes(canonical(bundle)),'reproduction_intent_sha256':sha256_bytes(canonical(intent)),'child_acceptance_sha256':sha256_bytes(canonical(acceptance)),'capabilities':caps,'inherited_count':sum(c['lineage_source']=='INHERITED' for c in caps),'mutated_count':sum(c['lineage_source']=='MUTATED' for c in caps),'private_history_inherited':False,'created_from_fresh_child':True}
 return _sign(p,_sk(child_root),_pk(child_root))

def reproduce(lineage_root,parent_root,child_root,surfaces=None,mutation_spec=None,birth_id=None):
 root=Path(lineage_root);birth_id=birth_id or uuid.uuid4().hex
 with lineage_lock(root):
  recover_birth(root)
  if (root/BIRTHS/f'{birth_id}.json').exists():raise V844Error('BIRTH_REPLAY')
  reg=load_registry(root);bundle=capability_bundle(parent_root,surfaces);intent=reproduction_intent(parent_root,child_root,bundle);accept=child_acceptance(child_root,intent,bundle)
  mut=None;mut_receipt=None
  if mutation_spec:
   source=next((c for c in bundle['payload']['public_capabilities'] if c['surface']==mutation_spec['source_surface']),None)
   if not source:raise V844Error('MUTATION_SOURCE_NOT_IN_INHERITANCE_BUNDLE')
   mut_receipt=mutation_receipt(root,child_root,source,mutation_spec['new_surface'],mutation_spec['holdout']);mp=_verify_mutation(root,child_root,source,mut_receipt,mutation_spec['holdout']);mut=dict(mp);mut['receipt_sha256']=sha256_bytes(canonical(mut_receipt))
  child_state=_child_overlay(child_root,reg,bundle,intent,accept,mut)
  public_record={'schema':'tukuyo.v844.public_birth_record/1','birth_id':birth_id,'capability_bundle':bundle,'reproduction_intent':intent,'child_acceptance':accept,'mutation_receipt':mut_receipt,'child_lineage_state':child_state}
  record_sha=sha256_bytes(canonical(public_record))
  cp=child_state['payload'];certp={'schema':SCHEMA_CERT,'birth_id':birth_id,'birth_index':cp['birth_index'],'lineage_family_id':cp['lineage_family_id'],'parent_individual_id':cp['parent_individual_id'],'parent_identity_public_key':cp['parent_identity_public_key'],'child_individual_id':cp['individual_id'],'child_identity_public_key':cp['identity_public_key'],'capability_bundle_sha256':cp['inheritance_bundle_sha256'],'reproduction_intent_sha256':cp['reproduction_intent_sha256'],'child_acceptance_sha256':cp['child_acceptance_sha256'],'child_lineage_state_sha256':sha256_bytes(canonical(child_state)),'mutation_receipt_sha256':None if mut_receipt is None else sha256_bytes(canonical(mut_receipt)),'public_birth_record_sha256':record_sha,'previous_birth_head_sha256':reg['payload']['birth_head_sha256'],'parent_private_state_copied':False}
  cert=_sign(certp,(root/AUTH_SK).read_text().strip(),(root/AUTH_PK).read_text().strip())
  rp=copy.deepcopy(reg['payload']);rp['birth_count']+=1;rp['birth_head_sha256']=sha256_bytes(canonical(cert));rp['known_individuals'][cp['parent_individual_id']]={'role':'parent','identity_public_key':cp['parent_identity_public_key']};rp['known_individuals'][cp['individual_id']]={'role':'child','identity_public_key':cp['identity_public_key'],'parent_individual_id':cp['parent_individual_id'],'birth_id':birth_id};newreg=_sign(rp,(root/AUTH_SK).read_text().strip(),(root/AUTH_PK).read_text().strip())
  walp={'schema':SCHEMA_WAL,'birth_id':birth_id,'parent_root_hint':str(Path(parent_root).resolve()),'child_root_hint':str(Path(child_root).resolve()),'bundle':bundle,'intent':intent,'acceptance':accept,'mutation_receipt':mut_receipt,'child_lineage_state':child_state,'public_birth_record':public_record,'birth_certificate':cert,'previous_registry_sha256':sha256_bytes(canonical(reg)),'target_registry':newreg};wal=_sign(walp,(root/AUTH_SK).read_text().strip(),(root/AUTH_PK).read_text().strip());atomic_json(root/WAL,wal)
  if os.environ.get('TUKUYO_V844_CRASH_AFTER')=='wal':os._exit(201)
  _apply_birth(root,walp);return cert

def _write_exact(path,obj,previous=None):
 p=Path(path);target=sha256_bytes(canonical(obj));cur=sha256_bytes(p.read_bytes()) if p.exists() else None
 if cur==target:return False
 if previous=='ABSENT':
  if cur is not None:raise V844Error('BIRTH_RECOVERY_CONFLICT:'+str(p))
 elif previous is not None and cur!=previous:raise V844Error('BIRTH_RECOVERY_CONFLICT:'+str(p))
 atomic_json(p,obj);return True

def _apply_birth(root,p):
 root=Path(root);child=Path(p['child_root_hint']);parent=Path(p['parent_root_hint'])
 _verify_bundle(parent,p['bundle']);_fresh_child(child)
 if p['intent']['public_key']!=_pk(parent) or not _verify(p['intent']):raise V844Error('RECOVERY_PARENT_INTENT_INVALID')
 if p['acceptance']['public_key']!=_pk(child) or not _verify(p['acceptance']):raise V844Error('RECOVERY_CHILD_ACCEPTANCE_INVALID')
 _write_exact(root/RECORDS/f"{p['birth_id']}.json",p['public_birth_record'],'ABSENT')
 if os.environ.get('TUKUYO_V844_CRASH_AFTER')=='record':os._exit(202)
 _write_exact(child/CHILD_STATE,p['child_lineage_state'],'ABSENT')
 if os.environ.get('TUKUYO_V844_CRASH_AFTER')=='child_state':os._exit(203)
 _write_exact(root/BIRTHS/f"{p['birth_id']}.json",p['birth_certificate'],'ABSENT')
 if os.environ.get('TUKUYO_V844_CRASH_AFTER')=='certificate':os._exit(204)
 _write_exact(root/REG,p['target_registry'],p['previous_registry_sha256'])
 if os.environ.get('TUKUYO_V844_CRASH_AFTER')=='registry':os._exit(205)
 wp=root/WAL
 if wp.exists():wp.unlink()

def recover_birth(root):
 root=Path(root);wp=root/WAL
 if not wp.exists():return False
 wal=load_json(wp)
 if wal.get('public_key')!=(root/AUTH_PK).read_text().strip() or not _verify(wal):raise V844Error('BIRTH_WAL_SIGNATURE_INVALID')
 _apply_birth(root,wal['payload']);return True

def load_child_lineage(child_root):
 p=Path(child_root)/CHILD_STATE
 if not p.exists():raise V844Error('CHILD_LINEAGE_STATE_MISSING')
 e=load_json(p)
 if not _verify(e) or e['public_key']!=_pk(child_root) or e['payload']['individual_id']!=_id(child_root):raise V844Error('CHILD_LINEAGE_STATE_INVALID')
 return e

def evaluate(child_root,query):
 base=v840.evaluate(child_root,query)
 if base.get('status')=='RESOLVED':return dict(base,source='SELF_LEARNED_OR_BUILTIN')
 try:e=load_child_lineage(child_root)
 except V844Error:return base
 a,s,b=s838.parse_query(query)
 cap=next((c for c in e['payload']['capabilities'] if c.get('surface')==s),None)
 if not cap:return base
 op=cap['operator'];return {'status':'RESOLVED','surface':s,'operator':op,'answer':s838.OPS[op](a,b),'source':cap['lineage_source'],'source_parent_individual_id':cap.get('source_parent_individual_id')}

def verify_lineage(root,parent_roots=None,child_roots=None):
 root=Path(root);errors=[]
 try:recover_birth(root);reg=load_registry(root)
 except Exception as e:return {'ok':False,'errors':[str(e)]}
 rp=reg['payload'];prev=ZERO;births=[]
 birth_files=[]
 for f in (root/BIRTHS).glob('*.json'):
  e=load_json(f); birth_files.append((int(e.get('payload',{}).get('birth_index',10**18)),f,e))
 for expected_index,(idx,f,e) in enumerate(sorted(birth_files,key=lambda x:x[0]),1):
  if not _verify(e) or e['public_key']!=(root/AUTH_PK).read_text().strip():errors.append('BIRTH_CERT_SIGNATURE:'+f.name);break
  p=e['payload']
  recp=root/RECORDS/f.name
  if not recp.exists():errors.append('BIRTH_PUBLIC_RECORD_MISSING:'+f.name);break
  rec=load_json(recp)
  if sha256_bytes(canonical(rec))!=p.get('public_birth_record_sha256'):errors.append('BIRTH_PUBLIC_RECORD_HASH:'+f.name);break
  try:
   if not _verify(rec['capability_bundle']) or not _verify(rec['reproduction_intent']) or not _verify(rec['child_acceptance']):raise V844Error('PUBLIC_RECORD_SIGNATURE_INVALID')
   if rec['child_lineage_state']['payload']['individual_id']!=p['child_individual_id']:raise V844Error('PUBLIC_RECORD_CHILD_BINDING_INVALID')
   if sha256_bytes(canonical(rec['capability_bundle']))!=p['capability_bundle_sha256'] or sha256_bytes(canonical(rec['reproduction_intent']))!=p['reproduction_intent_sha256'] or sha256_bytes(canonical(rec['child_acceptance']))!=p['child_acceptance_sha256'] or sha256_bytes(canonical(rec['child_lineage_state']))!=p['child_lineage_state_sha256']:raise V844Error('PUBLIC_RECORD_CERT_BINDING_INVALID')
   if rec.get('mutation_receipt') is None:
    if p.get('mutation_receipt_sha256') is not None:raise V844Error('PUBLIC_RECORD_MUTATION_BINDING_INVALID')
   elif sha256_bytes(canonical(rec['mutation_receipt']))!=p.get('mutation_receipt_sha256') or not _verify(rec['mutation_receipt']):raise V844Error('PUBLIC_RECORD_MUTATION_BINDING_INVALID')
  except Exception as ex:errors.append(str(ex));break
  if idx!=expected_index:errors.append('BIRTH_INDEX_GAP:'+f.name);break
  if p['previous_birth_head_sha256']!=prev:errors.append('BIRTH_CHAIN:'+f.name);break
  if p['parent_individual_id']==p['child_individual_id'] or p['parent_identity_public_key']==p['child_identity_public_key']:errors.append('PARENT_CHILD_IDENTITY_COLLISION:'+f.name)
  if p.get('parent_private_state_copied') is not False:errors.append('PRIVATE_STATE_COPY_FLAG:'+f.name)
  prev=sha256_bytes(canonical(e));births.append(p)
 if len(births)!=rp['birth_count']:errors.append('BIRTH_COUNT_MISMATCH')
 if prev!=rp['birth_head_sha256']:errors.append('BIRTH_HEAD_MISMATCH')
 if parent_roots and child_roots:
  proots={_id(x):Path(x) for x in parent_roots};croots={_id(x):Path(x) for x in child_roots}
  for p in births:
   if p['parent_individual_id'] not in proots or p['child_individual_id'] not in croots:continue
   try:
    pe=_state(proots[p['parent_individual_id']]);ce=_state(croots[p['child_individual_id']]);le=load_child_lineage(croots[p['child_individual_id']])
    if pe['public_key']!=p['parent_identity_public_key'] or ce['public_key']!=p['child_identity_public_key']:errors.append('LIVE_IDENTITY_BINDING')
    cp=ce['payload']
    # A child is expected to build its own private history after birth. The lineage invariant is
    # that parent private history was never inherited, not that the child must remain memoryless.
    if le['payload']['private_history_inherited'] is not False or le['payload'].get('created_from_fresh_child') is not True:errors.append('CHILD_PRIVATE_INHERITANCE_FLAG')
   except Exception as ex:errors.append(str(ex))
 return {'ok':not errors,'errors':errors,'lineage_family_id':rp['lineage_family_id'],'birth_count':rp['birth_count'],'birth_head_sha256':rp['birth_head_sha256'],'births':births}
