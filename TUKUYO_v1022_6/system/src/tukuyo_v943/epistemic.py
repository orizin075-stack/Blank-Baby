"""Bounded, audited epistemic revision adapter for the v941 living runtime.

Only the CLI/facade is gated: the immutable v840 native promotion remains in its
original signed history. Observer/evaluator/authority are DISTINCT external keys.
No evaluator secrets or external trust roots are distributed in a release.
"""
from __future__ import annotations
import base64, hashlib, json, os, tempfile
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

ZERO='0'*64
OPS={'ADD':lambda a,b:a+b,'MUL':lambda a,b:a*b,'SUB':lambda a,b:a-b,'MAX':max,'MIN':min}
SCHEMA='tukuyo.v943.epistemic.event/1'
def canon(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def objsha(o):return sha(canon(o))
def load(p):return json.loads(Path(p).read_bytes())
def write_once(p, b):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
def atomic(p,b):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(prefix='tmp_',dir=p.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  os.replace(tmp,p)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def public(sk):return base64.b64encode(sk.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode()
def secret_bytes(sk):return sk.private_bytes(serialization.Encoding.Raw,serialization.PrivateFormat.Raw,serialization.NoEncryption())
def sign(sk,payload):return {'payload':payload,'public_key':public(sk),'signature':base64.b64encode(sk.sign(canon(payload))).decode()}
def check(env,key):
 if not isinstance(env,dict) or set(env)!={'payload','public_key','signature'} or env['public_key']!=key:raise ValueError('TRUSTED_KEY_MISMATCH')
 try:Ed25519PublicKey.from_public_bytes(base64.b64decode(key,validate=True)).verify(base64.b64decode(env['signature'],validate=True),canon(env['payload']))
 except (InvalidSignature,ValueError) as exc:raise ValueError('SIGNATURE_INVALID') from exc
 return env['payload']
def keyfile(p):
 k=Path(p).read_text(encoding='ascii').strip()
 if len(base64.b64decode(k,validate=True))!=32:raise ValueError('KEY_INVALID')
 return k

def roots(data):return Path(data).resolve()/'epistemic'
def _key(root):return Ed25519PrivateKey.from_private_bytes(base64.b64decode((root/'private/local.key').read_bytes()))
def _core(data):
 state=Path(data)/'state'
 env=load(state/'integration_state.json');p=env['payload']
 return {'individual_id':p['individual_id'],'lineage_id':p['lineage_id'],'branch_id':p['branch_id'],
         'state_sequence':p['integration_seq'],'native_source_sha256':sha((state/'semantic/semantic_state.json').read_bytes()),
         'native_promotions':load(state/'semantic/semantic_state.json')['payload']['promotions'],
         'native_learning_ledger':state/'learning_ledger'}
def _native(data,surface):
 c=_core(data);m=c['native_promotions'].get(surface)
 if not m:raise ValueError('UNLEARNED_SURFACE')
 native=next((load(f) for f in sorted(c['native_learning_ledger'].glob('*.json')) if load(f)['payload'].get('surface')==surface),None)
 if native is None:raise ValueError('NO_NATIVE_LEARNING_EVENT')
 p=native['payload'];n={'surface':surface,'operator':m['operator'],'native_learning_sha256':objsha(native),
                      'native_promotion_sha256':m['promotion_sha256'],'individual_id':c['individual_id'],
                      'branch_id':c['branch_id'],'lineage_id':c['lineage_id'],
                      'native_verified_training':p['steps'][-1]['training'],
                      'native_holdout_raw_available':False}
 if p['semantic_promotion_sha256']!=m['promotion_sha256'] or p['operator']!=m['operator'] or p['individual_id']!=c['individual_id']:
  raise ValueError('NATIVE_PROVENANCE_MISMATCH')
 return n

def init(data,public_export):
 root=roots(data)
 if root.exists():
  if not (root/'private/local.key').is_file():raise ValueError('PARTIAL_ROOT')
 else:
  root.mkdir(parents=True,exist_ok=False);(root/'private').mkdir();(root/'events').mkdir();(root/'objects').mkdir()
  sk=Ed25519PrivateKey.generate();write_once(root/'private/local.key',base64.b64encode(secret_bytes(sk)))
  os.chmod(root/'private/local.key',0o600)
  write_once(root/'local.pub',(public(sk)+'\n').encode())
  head={'schema':'tukuyo.v943.epistemic.head/1','sequence':0,'entry_sha256':ZERO}
  atomic(root/'HEAD.json',canon(sign(sk,head))+b'\n')
 out=Path(public_export)
 if out.resolve().is_relative_to(Path(data).resolve()):raise ValueError('PIN_OUTSIDE_DATA_ROOT_REQUIRED')
 if out.exists() and out.read_text().strip()!=keyfile(root/'local.pub'):raise ValueError('EXTERNAL_LOCAL_PIN_MISMATCH')
 if not out.exists():write_once(out,(keyfile(root/'local.pub')+'\n').encode())
 return {'ok':True,'local_public_key':keyfile(root/'local.pub'),'external_pin':str(out)}

def _trust(trust):
 trust=Path(trust);keys={x:keyfile(trust/(x+'.pub')) for x in ('local','observer','evaluator','authority')}
 if len(set(keys.values()))!=4:raise ValueError('TRUST_ROLES_NOT_INDEPENDENT')
 return keys

def _put(root,obj):
 d=objsha(obj);p=root/'objects'/(d+'.json')
 if not p.exists():write_once(p,canon(obj)+b'\n')
 elif load(p)!=obj:raise ValueError('CONTENT_ADDRESS_CONFLICT')
 return d

def _get(root,d):
 if type(d)!=str or len(d)!=64 or any(c not in '0123456789abcdef' for c in d):raise ValueError('BAD_CONTENT_HASH')
 p=root/'objects'/(d+'.json')
 if not p.exists():raise ValueError('MISSING_OBJECT:'+d)
 o=load(p)
 if objsha(o)!=d:raise ValueError('OBJECT_HASH_MISMATCH:'+d)
 return o

def _append(root,kind,body,local):
 head=check(load(root/'HEAD.json'),local);seq=head['sequence']+1
 p={'schema':SCHEMA,'seq':seq,'prev_sha256':head['entry_sha256'],'kind':kind,'body':body}
 env=sign(_key(root),p);h=objsha(env)
 write_once(root/'events'/(f'{seq:012d}.json'),canon(env)+b'\n')
 atomic(root/'HEAD.json',canon(sign(_key(root),{'schema':'tukuyo.v943.epistemic.head/1','sequence':seq,'entry_sha256':h}))+b'\n')
 return h

def _query(operators,excluded):
 for a in range(-5,7):
  for b in range(-5,7):
   if (a,b) in excluded:continue
   predictions={o:OPS[o](a,b) for o in operators}
   if len(set(predictions.values()))==len(predictions):return {'a':a,'b':b,'predictions':predictions}
 raise ValueError('NO_DISCRIMINATING_QUERY')

def audit(data,trust,require_core=True):
 root=roots(data);keys=_trust(trust)
 if keyfile(root/'local.pub')!=keys['local']:raise ValueError('LOCAL_ANCHOR_MISMATCH')
 head=check(load(root/'HEAD.json'),keys['local'])
 if head.get('schema')!='tukuyo.v943.epistemic.head/1' or type(head.get('sequence')) is not int or head['sequence']<0:raise ValueError('BAD_HEAD')
 if set(x.name for x in (root/'events').iterdir())!={f'{j:012d}.json' for j in range(1,head['sequence']+1)}:raise ValueError('EVENT_SET_MISMATCH')
 surfaces={};used_observations=set();used_evaluations=set();used_approvals=set();prev=ZERO
 referenced=set()
 def get(d):
  o=_get(root,d);referenced.add(d);return o
 core=_core(data) if require_core else None
 for i in range(1,head['sequence']+1):
  env=load(root/'events'/(f'{i:012d}.json'));p=check(env,keys['local']);h=objsha(env)
  if set(p)!={'schema','seq','prev_sha256','kind','body'} or p['schema']!=SCHEMA or p['seq']!=i or p['prev_sha256']!=prev:raise ValueError('EVENT_CHAIN_INVALID')
  kind=p['kind'];b=p['body'];s=b.get('surface'); prior=surfaces.get(s)
  if kind=='IMPORT':
   if prior:raise ValueError('DUPLICATE_IMPORT')
   n=get(b['native_sha256'])
   if n['surface']!=s or n['individual_id']!=b['individual_id']:raise ValueError('IMPORT_BINDING')
   if core is not None and _native(data,s)!=n:raise ValueError('CORE_PROVENANCE_CHANGED')
   surfaces[s]={'status':'ACTIVE','native':n,'event_sha256':h}
  elif kind=='CHALLENGE':
   if not prior or prior['status']!='ACTIVE':raise ValueError('CHALLENGE_STATE')
   n=prior['native'];c=get(b['contradiction_sha256']);prop=get(b['proposal_sha256']);q=get(b['query_sha256'])
   if set(c)!={'a','b','expected'} or any(type(c[k])!=int or abs(c[k])>10000 for k in c):raise ValueError('CONTRADICTION_SCHEMA')
   if OPS[n['operator']](c['a'],c['b'])==c['expected']:raise ValueError('NOT_CONTRADICTION')
   alternative=sorted(o for o in OPS if o!=n['operator'] and OPS[o](c['a'],c['b'])==c['expected'])
   if any(r['a']==c['a'] and r['b']==c['b'] for r in n['native_verified_training']):raise ValueError('CONFLICTS_WITH_NATIVE_TRAINING_NEEDS_ADJUDICATION')
   if not alternative or prop!={'schema':'tukuyo.v943.proposal/1','native':n,'contradiction_sha256':b['contradiction_sha256'],'candidates':[n['operator']]+alternative}:raise ValueError('PROPOSAL_INVALID')
   if q!=_query(prop['candidates'][:2],{(c['a'],c['b'])}):raise ValueError('QUERY_INVALID')
   if b['origin_sha256']!=prior['event_sha256']:raise ValueError('CROSS_CAPABILITY_PROVENANCE')
   surfaces[s]={**prior,'status':'CHALLENGED','challenge_sha256':h,'challenge_body':b,'query':q,'proposal':prop}
  elif kind=='OBSERVATION':
   if not prior or prior['status']!='CHALLENGED' or b['challenge_sha256']!=prior['challenge_sha256']:raise ValueError('OBSERVATION_STATE')
   obs=get(b['observation_sha256']);op=check(obs,keys['observer']);q=prior['query']
   if op!={'schema':'tukuyo.v943.observation/1','challenge_sha256':prior['challenge_sha256'],'query_sha256':prior['challenge_body']['query_sha256'],'a':q['a'],'b':q['b'],'observed':op.get('observed'),'individual_id':prior['native']['individual_id']}:raise ValueError('OBSERVATION_BINDING')
   if type(op['observed'])!=int or abs(op['observed'])>100000000 or op['observed'] not in q['predictions'].values():raise ValueError('OBSERVATION_UNSUPPORTED')
   if b['observation_sha256'] in used_observations:raise ValueError('REPLAYED_OBSERVATION')
   used_observations.add(b['observation_sha256']);surfaces[s]={**prior,'status':'OBSERVED','observation_sha256':b['observation_sha256'],'observation':op}
  elif kind=='REVISE':
   if not prior or prior['status']!='OBSERVED' or b['challenge_sha256']!=prior['challenge_sha256'] or b['observation_sha256']!=prior['observation_sha256']:raise ValueError('REVISION_STATE')
   n=prior['native'];c=get(prior['challenge_body']['contradiction_sha256']);q=prior['query'];ob=prior['observation'];new=b['new_operator']
   if new==n['operator'] or new not in prior['proposal']['candidates'] or OPS[new](c['a'],c['b'])!=c['expected'] or OPS[new](q['a'],q['b'])!=ob['observed']:raise ValueError('UNSUPPORTED_REVISION')
   ev=get(b['evaluator_receipt_sha256']);ep=check(ev,keys['evaluator'])
   required={'schema':'tukuyo.v943.evaluation/1','challenge_sha256':prior['challenge_sha256'],'observation_sha256':prior['observation_sha256'],'proposal_sha256':prior['challenge_body']['proposal_sha256'],'new_operator':new,'individual_id':n['individual_id'],'sample_count':2,'wrong':0}
   if ep!=required:raise ValueError('EVALUATION_BINDING')
   authority=get(b['authority_receipt_sha256']);ap=check(authority,keys['authority'])
   if ap!={'schema':'tukuyo.v943.promotion_authority/1','challenge_sha256':prior['challenge_sha256'],'observation_sha256':prior['observation_sha256'],'evaluator_receipt_sha256':b['evaluator_receipt_sha256'],'new_operator':new,'individual_id':n['individual_id']}:raise ValueError('AUTHORITY_BINDING')
   if b['evaluator_receipt_sha256'] in used_evaluations or b['authority_receipt_sha256'] in used_approvals:raise ValueError('REUSED_RECEIPT')
   used_evaluations.add(b['evaluator_receipt_sha256']);used_approvals.add(b['authority_receipt_sha256'])
   surfaces[s]={**prior,'status':'REVISED_BOUNDED','new_operator':new,'revision_event_sha256':h,'approved_cases':[(c['a'],c['b']),(q['a'],q['b'])]}
  else:raise ValueError('UNKNOWN_EVENT_TYPE')
  if s!=prior['native']['surface'] if prior and kind!='IMPORT' else False:raise ValueError('SURFACE_MISMATCH')
  prev=h
 actual={p.name for p in (root/'objects').iterdir()}
 expected={d+'.json' for d in referenced}
 if actual!=expected:raise ValueError('OBJECT_SET_MISMATCH')
 if head['entry_sha256']!=prev:raise ValueError('HEAD_MISMATCH')
 return {'ok':True,'events':head['sequence'],'head_sha256':prev,'surfaces':surfaces,'external_roles_verified':bool(used_approvals)}

def status(data,trust):
 a=audit(data,trust);return {'ok':True,'events':a['events'],'head_sha256':a['head_sha256'],'surfaces':{s:{'status':x['status'],'native_operator':x['native']['operator'],'facade_operator':x.get('new_operator'),'approved_cases':len(x.get('approved_cases',[]))} for s,x in a['surfaces'].items()}}

def import_native(data,trust,surface):
 a=audit(data,trust);root=roots(data);local=_trust(trust)['local'];n=_native(data,surface)
 if surface in a['surfaces']:raise ValueError('ALREADY_IMPORTED')
 d=_put(root,n);h=_append(root,'IMPORT',{'surface':surface,'native_sha256':d,'individual_id':n['individual_id']},local)
 audit(data,trust);return {'ok':True,'event_sha256':h,'native_status':'LOCAL_VERIFIED_NOT_THIRD_PARTY'}

def challenge(data,trust,surface,row):
 a=audit(data,trust);root=roots(data);local=_trust(trust)['local'];old=a['surfaces'].get(surface)
 if not old or old['status']!='ACTIVE':raise ValueError('NO_ACTIVE_IMPORTED_CAPABILITY')
 if set(row)!={'a','b','expected'} or any(type(row[k])!=int or abs(row[k])>10000 for k in row):raise ValueError('BAD_CHALLENGE_ROW')
 native=old['native'];alts=sorted(o for o in OPS if o!=native['operator'] and OPS[o](row['a'],row['b'])==row['expected'])
 if any(r['a']==row['a'] and r['b']==row['b'] for r in native['native_verified_training']):raise ValueError('CONFLICTS_WITH_NATIVE_TRAINING_NEEDS_ADJUDICATION')
 if not alts or OPS[native['operator']](row['a'],row['b'])==row['expected']:raise ValueError('NO_ALTERNATIVE_CONTRADICTION')
 rh=_put(root,row);proposal={'schema':'tukuyo.v943.proposal/1','native':native,'contradiction_sha256':rh,'candidates':[native['operator']]+alts};ph=_put(root,proposal)
 query=_query(proposal['candidates'][:2],{(row['a'],row['b'])});qh=_put(root,query)
 h=_append(root,'CHALLENGE',{'surface':surface,'origin_sha256':old['event_sha256'],'contradiction_sha256':rh,'proposal_sha256':ph,'query_sha256':qh},local)
 audit(data,trust)
 return {'ok':True,'status':'CHALLENGED','challenge_sha256':h,'query_sha256':qh,'query':query,'individual_id':native['individual_id'],'external_observation_required':True}

def observation(data,trust,surface,obs_file):
 a=audit(data,trust);root=roots(data);local=_trust(trust)['local'];old=a['surfaces'].get(surface)
 if not old or old['status']!='CHALLENGED':raise ValueError('NO_OPEN_CHALLENGE')
 obs=load(obs_file);op=check(obs,_trust(trust)['observer']);q=old['query']
 if op.get('challenge_sha256')!=old['challenge_sha256'] or (op.get('a'),op.get('b'))!=(q['a'],q['b']) or op.get('query_sha256')!=old['challenge_body']['query_sha256'] or op.get('individual_id')!=old['native']['individual_id']:raise ValueError('WRONG_OBSERVATION_BINDING')
 if op.get('observed') is None:return {'ok':True,'status':'CHALLENGED','result':'EXTERNAL_OBSERVER_ABSTAINED','state_modified':False}
 d=_put(root,obs);h=_append(root,'OBSERVATION',{'surface':surface,'challenge_sha256':old['challenge_sha256'],'observation_sha256':d},local)
 audit(data,trust);return {'ok':True,'status':'OBSERVED','event_sha256':h,'observation_sha256':d}

def expected_receipts(data,trust,surface):
 a=audit(data,trust);s=a['surfaces'].get(surface)
 if not s or s['status']!='OBSERVED':raise ValueError('OBSERVATION_REQUIRED')
 c=s['challenge_sha256'];o=s['observation_sha256'];n=s['native'];q=s['query'];ob=s['observation'];row=_get(roots(data),s['challenge_body']['contradiction_sha256'])
 valid=[x for x in s['proposal']['candidates'] if x!=n['operator'] and OPS[x](row['a'],row['b'])==row['expected'] and OPS[x](q['a'],q['b'])==ob['observed']]
 return [{'schema':'tukuyo.v943.evaluation/1','challenge_sha256':c,'observation_sha256':o,'proposal_sha256':s['challenge_body']['proposal_sha256'],'new_operator':x,'individual_id':n['individual_id'],'sample_count':2,'wrong':0} for x in valid]

def revise(data,trust,surface,eval_file,approval_file):
 options=expected_receipts(data,trust,surface);root=roots(data);local=_trust(trust)['local'];ev=load(eval_file);ep=check(ev,_trust(trust)['evaluator'])
 if len(options)!=1:raise ValueError('HYPOTHESIS_AMBIGUOUS')
 if ep not in options:raise ValueError('EVALUATION_NOT_MATCHING_RECOMPUTATION')
 auth=load(approval_file);ap=check(auth,_trust(trust)['authority']);ed=objsha(ev)
 if ap!={'schema':'tukuyo.v943.promotion_authority/1','challenge_sha256':ep['challenge_sha256'],'observation_sha256':ep['observation_sha256'],'evaluator_receipt_sha256':ed,'new_operator':ep['new_operator'],'individual_id':ep['individual_id']}:raise ValueError('AUTHORITY_PAYLOAD_MISMATCH')
 eh=_put(root,ev);ah=_put(root,auth)
 h=_append(root,'REVISE',{'surface':surface,'challenge_sha256':ep['challenge_sha256'],'observation_sha256':ep['observation_sha256'],'evaluator_receipt_sha256':eh,'authority_receipt_sha256':ah,'new_operator':ep['new_operator']},local)
 audit(data,trust);return {'ok':True,'status':'REVISED_BOUNDED','event_sha256':h,'new_operator':ep['new_operator'],'native_history_unchanged':True,'global_operator_override':False}

def gated_evaluate(data,trust,query,native_eval):
 a=audit(data,trust)
 parts=query.strip().split()
 if len(parts)<3:return native_eval()
 surface=' '.join(parts[1:-1]);s=a['surfaces'].get(surface)
 if not s:return native_eval()
 if s['status'] in ('CHALLENGED','OBSERVED'):
  return {'status':'OPEN','surface':surface,'reason':'CAPABILITY_SUSPENDED_PENDING_VERIFICATION'}
 if s['status']=='REVISED_BOUNDED':
  try:x,y=int(parts[0]),int(parts[-1])
  except ValueError:return {'status':'OPEN','surface':surface,'reason':'REVISED_INPUT_UNSUPPORTED'}
  if (x,y) not in s['approved_cases']:return {'status':'OPEN','surface':surface,'reason':'OUTSIDE_REVISED_EVIDENCE'}
  return {'status':'RESOLVED','surface':surface,'operator':s['new_operator'],'answer':OPS[s['new_operator']](x,y),'authority':'EXTERNALLY_SIGNED_BOUNDED_REVISION','native_history_preserved':True,'global_operator_override':False}
 return native_eval()
