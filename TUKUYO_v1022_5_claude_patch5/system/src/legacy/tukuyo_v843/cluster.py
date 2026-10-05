from __future__ import annotations
from pathlib import Path
import copy,uuid
from .deps import activate
from .constants import *
from .util import *
activate()
import tukuyo_v842.society as s842
import tukuyo_v841.social as s841
import tukuyo_v840.integration as v840
import tukuyo_v840.crypto as c840
import tukuyo_v837.runtime as r837

def keygen():return c840.keygen()
def _sign(payload,sk,pk):return r837._signed(payload,sk,pk)
def _verify(e):return r837._verify(e)
def _state(r):return s842._state(r)
def _id(r):return s842._id(r)
def _sk(r):return s842._sk(r)
def _pk(r):return s842._pk(r)

def create_role_manifest(path,society_root,member_roots,role_map,executor_pool,authority_sk,authority_pk):
 reg=s842.load_registry(society_root);members=reg['payload']['members'];member_keys={m['identity_public_key'] for m in members.values()}
 if authority_pk in member_keys:raise V843Error('ROLE_AUTHORITY_IS_MEMBER_KEY')
 if set(role_map)!=set(ROLES):raise V843Error('ROLE_SET_INVALID')
 ids=list(role_map.values())+list(executor_pool)
 if len(ids)!=len(set(ids)):raise V843Error('ROLE_OR_EXECUTOR_ID_REUSED')
 if not executor_pool or len(executor_pool)<2:raise V843Error('EXECUTOR_POOL_TOO_SMALL')
 for pid in ids:
  if pid not in members:raise V843Error('ROLE_MEMBER_NOT_IN_SOCIETY:'+pid)
 payload={'schema':'tukuyo.v843.role_manifest/1','society_id':reg['payload']['society_id'],'society_registry_sha256':sha256_bytes(canonical(reg)),'roles':dict(role_map),'executor_pool':list(executor_pool),'authority_is_external_to_members':True}
 e=_sign(payload,authority_sk,authority_pk);atomic_json(path,e);return e

def load_role_manifest(path,society_root):
 e=load_json(path)
 if not _verify(e):raise V843Error('ROLE_MANIFEST_SIGNATURE_INVALID')
 p=e['payload'];reg=s842.load_registry(society_root)
 if p.get('society_id')!=reg['payload']['society_id'] or p.get('society_registry_sha256')!=sha256_bytes(canonical(reg)):raise V843Error('ROLE_MANIFEST_SOCIETY_BINDING_INVALID')
 ids=list(p['roles'].values())+list(p['executor_pool'])
 if set(p['roles'])!=set(ROLES) or len(ids)!=len(set(ids)):raise V843Error('ROLE_SEPARATION_INVALID')
 if e['public_key'] in {m['identity_public_key'] for m in reg['payload']['members'].values()}:raise V843Error('ROLE_AUTHORITY_NOT_EXTERNAL')
 return e

def _role_env(agent_root,role,task_id,payload):
 return _sign({'schema':'tukuyo.v843.role_receipt/1','role':role,'task_id':task_id,'individual_id':_id(agent_root),'body':payload,'nonce':uuid.uuid4().hex},_sk(agent_root),_pk(agent_root))

def _check_role(e,role,pid,reg):
 if not _verify(e):raise V843Error('ROLE_RECEIPT_SIGNATURE_INVALID:'+role)
 p=e['payload']
 if p.get('role')!=role or p.get('individual_id')!=pid:raise V843Error('ROLE_RECEIPT_BINDING_INVALID:'+role)
 if e['public_key']!=reg['members'][pid]['identity_public_key']:raise V843Error('ROLE_RECEIPT_KEY_INVALID:'+role)
 return p

def run_cluster_task(society_root,role_manifest_path,member_roots,task):
 rm=load_role_manifest(role_manifest_path,society_root)['payload'];reg=s842.load_registry(society_root)['payload'];roots={_id(r):r for r in member_roots.values()};roles=rm['roles']
 # Observer extracts surface only; no expected answer is exposed to the cluster pipeline.
 surface=s842._surface(task['query']);obs=_role_env(roots[roles['observer']],'observer',task['id'],{'query':task['query'],'surface':surface})
 anns=s842.load_announcements(society_root);candidates=[]
 for pid in rm['executor_pool']:
  a=anns.get(pid)
  if a and any(c.get('surface')==surface for c in a['payload']['public_capabilities']):candidates.append(pid)
 analyst=_role_env(roots[roles['analyst']],'analyst',task['id'],{'observation_sha256':sha256_bytes(canonical(obs)),'candidate_executors':sorted(candidates)})
 selected=sorted(candidates)[0] if candidates else None
 designer=_role_env(roots[roles['designer']],'designer',task['id'],{'analyst_sha256':sha256_bytes(canonical(analyst)),'selected_executor':selected})
 coordinator=_role_env(roots[roles['coordinator']],'coordinator',task['id'],{'design_sha256':sha256_bytes(canonical(designer)),'authorized_executor':selected})
 if selected is None:
  answer={'payload':{'task_id':task['id'],'query':task['query'],'status':'OPEN','output':None,'responder_individual_id':None},'public_key':None,'signature':None}
 else:answer=s842._answer(roots[selected],task)
 # Internal verifier only verifies structure/route; it never receives expected answer.
 structure_ok=(answer['payload']['task_id']==task['id'] and answer['payload']['query']==task['query'] and (selected is None or (answer['payload']['responder_individual_id']==selected and _verify(answer))))
 verifier=_role_env(roots[roles['verifier']],'verifier',task['id'],{'coordinator_sha256':sha256_bytes(canonical(coordinator)),'answer_sha256':sha256_bytes(canonical(answer)),'structure_ok':bool(structure_ok),'correctness_checked':False})
 archivist=_role_env(roots[roles['archivist']],'archivist',task['id'],{'verifier_sha256':sha256_bytes(canonical(verifier)),'answer_sha256':sha256_bytes(canonical(answer))})
 return {'task_id':task['id'],'observer':obs,'analyst':analyst,'designer':designer,'coordinator':coordinator,'answer':answer,'verifier':verifier,'archivist':archivist}

def verify_cluster_bundle(society_root,role_manifest_path,tasks,bundle):
 rm=load_role_manifest(role_manifest_path,society_root)['payload'];reg=s842.load_registry(society_root)['payload'];by={t['id']:t for t in tasks};seen=set();correct=wrong=abstain=0;errors=[]
 for row in bundle:
  tid=row.get('task_id');t=by.get(tid)
  if not t or tid in seen:errors.append('TASK_BINDING:'+str(tid));continue
  seen.add(tid);roles=rm['roles']
  try:
   op=_check_role(row['observer'],'observer',roles['observer'],reg);ap=_check_role(row['analyst'],'analyst',roles['analyst'],reg);dp=_check_role(row['designer'],'designer',roles['designer'],reg);cp=_check_role(row['coordinator'],'coordinator',roles['coordinator'],reg);vp=_check_role(row['verifier'],'verifier',roles['verifier'],reg);rp=_check_role(row['archivist'],'archivist',roles['archivist'],reg)
   if op['task_id']!=tid or op['body']['query']!=t['query']:raise V843Error('OBSERVER_TASK_BINDING')
   if ap['body']['observation_sha256']!=sha256_bytes(canonical(row['observer'])):raise V843Error('ANALYST_CHAIN')
   if dp['body']['analyst_sha256']!=sha256_bytes(canonical(row['analyst'])):raise V843Error('DESIGNER_CHAIN')
   if cp['body']['design_sha256']!=sha256_bytes(canonical(row['designer'])):raise V843Error('COORDINATOR_CHAIN')
   selected=cp['body']['authorized_executor'];ans=row['answer'];p=ans['payload']
   if selected is None:
    if p['responder_individual_id'] is not None or p['status']!='OPEN':raise V843Error('UNROUTED_ANSWER_INVALID')
   else:
    if selected not in rm['executor_pool'] or p['responder_individual_id']!=selected or ans['public_key']!=reg['members'][selected]['identity_public_key'] or not _verify(ans):raise V843Error('EXECUTOR_BINDING_INVALID')
   if vp['body']['coordinator_sha256']!=sha256_bytes(canonical(row['coordinator'])) or vp['body']['answer_sha256']!=sha256_bytes(canonical(ans)) or not vp['body']['structure_ok'] or vp['body']['correctness_checked'] is not False:raise V843Error('INTERNAL_VERIFIER_BOUNDARY_INVALID')
   if rp['body']['verifier_sha256']!=sha256_bytes(canonical(row['verifier'])) or rp['body']['answer_sha256']!=sha256_bytes(canonical(ans)):raise V843Error('ARCHIVIST_CHAIN')
   if p['status']!='RESOLVED':abstain+=1
   elif p.get('output')==t['expected']:correct+=1
   else:wrong+=1
  except Exception as e:errors.append(str(e))
 if len(seen)!=len(tasks):errors.append('TASK_COUNT_MISMATCH')
 return {'ok':not errors,'errors':errors,'total':len(tasks),'correct':correct,'wrong':wrong,'abstain':abstain,'coverage':correct/len(tasks) if tasks else 0.0}

def external_verifier_receipt(society_root,role_manifest_path,tasks,bundle,external_sk,external_pk):
 reg=s842.load_registry(society_root)['payload']
 if external_pk in {m['identity_public_key'] for m in reg['members'].values()}:raise V843Error('EXTERNAL_VERIFIER_IS_CLUSTER_MEMBER')
 rm=load_role_manifest(role_manifest_path,society_root)
 if external_pk==rm['public_key']:raise V843Error('EXTERNAL_VERIFIER_EQUALS_ROLE_AUTHORITY')
 v=verify_cluster_bundle(society_root,role_manifest_path,tasks,bundle)
 p={'schema':'tukuyo.v843.external_verifier_receipt/1','society_id':reg['society_id'],'role_manifest_sha256':sha256_bytes(canonical(rm)),'tasks_sha256':sha256_bytes(canonical(tasks)),'bundle_sha256':sha256_bytes(canonical(bundle)),'summary':{k:v[k] for k in ('total','correct','wrong','abstain','coverage')},'pass':bool(v['ok'] and v['wrong']==0)}
 return _sign(p,external_sk,external_pk)

def final_gate(society_root,role_manifest_path,tasks,bundle,receipt):
 if not _verify(receipt):raise V843Error('EXTERNAL_RECEIPT_SIGNATURE_INVALID')
 reg=s842.load_registry(society_root)['payload'];rm=load_role_manifest(role_manifest_path,society_root)
 if receipt['public_key'] in {m['identity_public_key'] for m in reg['members'].values()} or receipt['public_key']==rm['public_key']:raise V843Error('EXTERNAL_VERIFIER_NOT_INDEPENDENT_KEY')
 p=receipt['payload'];v=verify_cluster_bundle(society_root,role_manifest_path,tasks,bundle)
 if p['tasks_sha256']!=sha256_bytes(canonical(tasks)) or p['bundle_sha256']!=sha256_bytes(canonical(bundle)) or p['role_manifest_sha256']!=sha256_bytes(canonical(rm)):raise V843Error('EXTERNAL_RECEIPT_BINDING_INVALID')
 if p['summary']!={k:v[k] for k in ('total','correct','wrong','abstain','coverage')}:raise V843Error('EXTERNAL_SUMMARY_DISAGREES_WITH_RAW')
 if not v['ok']:raise V843Error('CLUSTER_BUNDLE_INVALID')
 if v['wrong']!=0:raise V843Error('VERIFIED_WRONG_NONZERO')
 if not p['pass']:raise V843Error('EXTERNAL_RECEIPT_NOT_PASS')
 return v
