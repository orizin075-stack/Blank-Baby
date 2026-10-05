from __future__ import annotations
from pathlib import Path
import copy,json,os,shutil,tempfile,fcntl
from contextlib import contextmanager
from .deps import activate
from .constants import V837_LAYER_SHA256,V838_LAYER_SHA256,V839_COMPLETE_SHA256,ZERO,SCHEMA
from .util import canonical,load_json,sha256_bytes,sha256_file,atomic_json,atomic_bytes,V840Error
from .crypto import keygen,pub,sign,verify
activate()
import tukuyo_v837.runtime as r837
from tukuyo_v838 import semantic as s838

ISTATE='integration_state.json';IHEAD='integration_head.json';IWAL='pending_learning.json';ISK='private/integration.key';IPK='integration.pub';ILEDGER='learning_ledger'

@contextmanager
def integration_lock(root):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);f=open(root/'.integration.lock','a+b')
 try:
  try:fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise V840Error('INTEGRATION_ALREADY_ACTIVE')
  yield
 finally:
  try:fcntl.flock(f.fileno(),fcntl.LOCK_UN)
  finally:f.close()

def _signed(payload,sk,pk):return {'payload':payload,'public_key':pk,'signature':sign(sk,payload)}
def _verify(env):return verify(env['public_key'],env['payload'],env['signature'])
def _ledger_path(root,seq):return Path(root)/ILEDGER/f'{seq:012d}.json'
def _organism(root):return Path(root)/'organism'
def _semantic(root):return Path(root)/'semantic'
def _sha_json(p):return sha256_bytes(canonical(load_json(p)))
def _current_component(root):
 org=r837.load_verified_state(_organism(root));sem=s838.load_state(_semantic(root));return org,sem

def _make_head(env,entry_sha,sk,pk):
 p=env['payload'];return _signed({'schema':'tukuyo.v840.integration_head/1','integration_seq':p['integration_seq'],'integration_state_sha256':sha256_bytes(canonical(env)),'learning_head_sha256':entry_sha},sk,pk)

def init(root,individual_id='TUKUYO-v840-organism-001',initial_energy=100.0,initial_reserve=2200.0,experience_profile='balanced'):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);(root/'private').mkdir(exist_ok=True);(root/ILEDGER).mkdir(exist_ok=True)
 if (root/ISTATE).exists():return load(root)
 r837.init_runtime(_organism(root),individual_id=individual_id,initial_energy=initial_energy,initial_reserve=initial_reserve,experience_profile=experience_profile)
 s838.init(_semantic(root));sk,pk=keygen();atomic_bytes(root/ISK,sk.encode());os.chmod(root/ISK,0o600);atomic_bytes(root/IPK,pk.encode())
 org,sem=_current_component(root);op=org['payload'];sp=sem['payload']
 payload={'schema':SCHEMA,'individual_id':individual_id,'lineage_id':op['identity']['lineage_id'],'branch_id':op['identity']['branch_id'],'integration_seq':0,'learning_head_sha256':ZERO,'organism_anchor_state_seq':op['continuity']['state_seq'],'organism_anchor_state_sha256':sha256_bytes(canonical(org)),'semantic_state_seq':sp['state_seq'],'semantic_state_sha256':sha256_bytes(canonical(sem)),'capability_generation':op['capabilities']['capability_generation'],'total_learning_costs':{'energy':0.0,'compute':0.0,'storage':0.0},'learning_events':0,'v837_layer_sha256':V837_LAYER_SHA256,'v838_layer_sha256':V838_LAYER_SHA256,'v839_parent_complete_sha256':V839_COMPLETE_SHA256,'accelerated_time_is_not_wall_clock':True}
 env=_signed(payload,sk,pk);head=_make_head(env,ZERO,sk,pk);atomic_json(root/ISTATE,env);atomic_json(root/IHEAD,head);return env

def load(root):
 root=Path(root);recover(root);env=load_json(root/ISTATE);head=load_json(root/IHEAD);pk=(root/IPK).read_text().strip()
 if env.get('public_key')!=pk or not _verify(env):raise V840Error('INTEGRATION_STATE_SIGNATURE_INVALID')
 if head.get('public_key')!=pk or not _verify(head):raise V840Error('INTEGRATION_HEAD_SIGNATURE_INVALID')
 p=env['payload'];hp=head['payload']
 if hp['integration_seq']!=p['integration_seq'] or hp['integration_state_sha256']!=sha256_bytes(canonical(env)) or hp['learning_head_sha256']!=p['learning_head_sha256']:raise V840Error('INTEGRATION_STATE_ROLLBACK_OR_HEAD_MISMATCH')
 return env

def _learning_cost(ntraining,nholdout,nsteps):
 return {'energy':round(1.5+0.20*ntraining+0.15*nholdout+0.30*nsteps,6),'compute':round(4.0+2.0*ntraining+1.0*nholdout+2.0*nsteps,6),'storage':round(0.04+0.01*(ntraining+nholdout+nsteps),6)}

def _select_observation(cands,available):
 for c in available:
  vals={op:s838.OPS[op](c['a'],c['b']) for op in cands}
  if len(set(vals.values()))>1:return c
 return None

def _semantic_plan(root,surface,observations,holdout):
 live=_semantic(root);tmp=Path(tempfile.mkdtemp(prefix='tukuyo_v840_sem_'))/'semantic';shutil.copytree(live,tmp)
 try:
  if s838.evaluate(tmp,f"{observations[0]['a']} {surface} {observations[0]['b']}")['status']!='OPEN':raise V840Error('CAPABILITY_ALREADY_PRESENT')
  commitment=s838.holdout_commitment(tmp,surface,holdout);avail=[dict(x) for x in observations];training=[avail.pop(0)];steps=[]
  while True:
   prop=s838.make_proposal(surface,training,commitment);steps.append({'training':copy.deepcopy(training),'candidates':list(prop['candidates']),'probe':prop.get('discriminating_probe')})
   if prop.get('unique_operator'):break
   nxt=_select_observation(prop.get('candidates') or [],avail)
   if nxt is None:raise V840Error('NO_DISCRIMINATING_OBSERVATION')
   training.append(nxt);avail.remove(nxt)
  receipt=s838.verifier_receipt(tmp,prop,holdout,commitment);new_env=s838.promote(tmp,prop,holdout,commitment,receipt);a=s838.audit(tmp)
  if not a.get('ok'):raise V840Error('SEMANTIC_TARGET_AUDIT_FAILED')
  seq=new_env['payload']['state_seq'];changed={'semantic_state.json':load_json(tmp/'semantic_state.json'),'promotion_head.json':load_json(tmp/'promotion_head.json'),f'promotions/{seq:012d}.json':load_json(tmp/'promotions'/f'{seq:012d}.json')}
  return {'target_env':new_env,'changed':changed,'operator':prop['unique_operator'],'training':training,'steps':steps,'proposal':prop,'holdout':holdout,'commitment':commitment,'receipt':receipt,'audit':a}
 finally:shutil.rmtree(tmp.parent,ignore_errors=True)

def _build_organism_tx(root,surface,operator,cost,semantic_target_sha,semantic_promotion_sha):
 oroot=_organism(root);cur=r837.load_verified_state(oroot);p=cur['payload'];sk=(oroot/r837.KEY).read_text().strip();pk=cur['public_key']
 if p['lifecycle']['status']!='alive':raise V840Error('ORGANISM_NOT_ALIVE')
 if p['resources']['energy'] < cost['energy']+2:raise V840Error('INSUFFICIENT_ENERGY_FOR_LEARNING')
 if p['resources']['compute_credit'] < cost['compute']:raise V840Error('INSUFFICIENT_COMPUTE_FOR_LEARNING')
 if p['resources']['storage_credit'] < cost['storage']:raise V840Error('INSUFFICIENT_STORAGE_FOR_LEARNING')
 nxt=copy.deepcopy(p);nxt['resources']['energy']=round(nxt['resources']['energy']-cost['energy'],9);nxt['resources']['compute_credit']=round(nxt['resources']['compute_credit']-cost['compute'],9);nxt['resources']['storage_credit']=round(nxt['resources']['storage_credit']-cost['storage'],9)
 nxt['metabolism']['cumulative_costs']['energy_burn']=round(nxt['metabolism']['cumulative_costs']['energy_burn']+cost['energy'],9);nxt['metabolism']['cumulative_costs']['compute']=round(nxt['metabolism']['cumulative_costs']['compute']+cost['compute'],9);nxt['metabolism']['cumulative_costs']['storage']=round(nxt['metabolism']['cumulative_costs']['storage']+cost['storage'],9);nxt['metabolism']['last_cost']=cost; nxt['metabolism']['last_decision_reason']='semantic_capability_research'
 nxt['runtime']['tick']=p['runtime']['tick']+1;nxt['runtime']['simulated_seconds']=nxt['runtime']['tick']*nxt['runtime']['tick_seconds'];nxt['runtime']['action_counts']['semantic_learning']=int(nxt['runtime']['action_counts'].get('semantic_learning',0))+1
 # Consolidate ordinary pre-learning episodes before recording the capability acquisition itself.
 r837._consolidate_autobiography(nxt)
 nxt['capabilities']['capability_generation']=int(p['capabilities']['capability_generation'])+1;cap={'kind':'semantic_operator','surface':surface,'operator':operator,'semantic_state_sha256':semantic_target_sha,'promotion_sha256':semantic_promotion_sha,'acquired_tick':nxt['runtime']['tick']};nxt['capabilities']['public_capabilities'].append(cap);nxt['capabilities']['learned_repairs'].append(cap);nxt['memory']['semantic'][surface]=cap
 episode={'tick':nxt['runtime']['tick'],'action':'semantic_learning','decision_reason':'capability_gap','surface':surface,'operator':operator,'experienced_value':0.9,'prediction_error':0.9,'origin_individual_id':p['identity']['individual_id']};nxt['memory']['episodic'].append(episode);nxt['memory']['episodic']=nxt['memory']['episodic'][-256:]
 rec={'schema':'tukuyo.autobiographical_record.v840.1','start_tick':nxt['runtime']['tick'],'end_tick':nxt['runtime']['tick'],'action_stats':{'semantic_learning':{'count':1,'value_sum':0.9}},'mean_prediction_error':0.9,'experience_profile':nxt['world_model']['experience_profile'],'capability':cap};nxt['memory']['autobiographical'].append(rec);nxt['memory']['autobiographical']=nxt['memory']['autobiographical'][-128:];nxt['self_model']['last_consolidated_tick']=nxt['runtime']['tick'];r837._recompute_self_model(nxt)
 nxt['continuity']['state_seq']=p['continuity']['state_seq']+1;nxt['continuity']['previous_state_sha256']=sha256_bytes(canonical(cur));seq=nxt['continuity']['state_seq']
 ev_payload={'schema':'tukuyo.organism_event.v840.learning/1','individual_id':p['identity']['individual_id'],'branch_id':p['identity']['branch_id'],'state_seq':seq,'runtime_tick':nxt['runtime']['tick'],'previous_event_sha256':p['continuity']['event_head_sha256'],'action':'semantic_learning','surface':surface,'operator':operator,'learning_cost':cost,'semantic_state_sha256':semantic_target_sha,'promotion_sha256':semantic_promotion_sha,'post_energy':nxt['resources']['energy'],'post_reserve':nxt['resources']['metabolic_reserve'],'post_health':nxt['health']['integrity']}
 ev_env=r837._signed(ev_payload,sk,pk);ev_sha=sha256_bytes(canonical(ev_env));nxt['continuity']['event_head_sha256']=ev_sha
 if not r837._verify_invariants(nxt):raise V840Error('ORGANISM_INVARIANT_AFTER_LEARNING')
 st_env=r837._signed(nxt,sk,pk);previous_head=r837._read_head(oroot);commit_env=r837._commit_env_for(st_env,previous_head['payload']['commit_sha256'],sk,pk);head_env=r837._head_env_for(st_env,commit_env,sk,pk)
 return {'seq':seq,'event_env':ev_env,'state_env':st_env,'commit_env':commit_env,'head_env':head_env,'event_rel':f'events/{seq:012d}.json','commit_rel':f'state_commits/{seq:012d}.json','previous_state_sha256':sha256_bytes(canonical(cur)),'previous_head_sha256':sha256_bytes(canonical(previous_head))}

def learn(root,surface,observations,holdout,*,protocol_test_fixture=False):
 root=Path(root)
 with integration_lock(root):
  recover(root);ienv=load(root);ip=ienv['payload'];org,sem=_current_component(root)
  if org['payload']['identity']['individual_id']!=ip['individual_id']:raise V840Error('INDIVIDUAL_BINDING_MISMATCH')
  plan=_semantic_plan(root,surface,observations,holdout);target_sem=plan['target_env'];semantic_target_sha=sha256_bytes(canonical(target_sem));seq_sem=target_sem['payload']['state_seq'];promotion_obj=plan['changed'][f'promotions/{seq_sem:012d}.json'];promotion_sha=sha256_bytes(canonical(promotion_obj));cost=_learning_cost(len(plan['training']),len(holdout),len(plan['steps']))
  otx=_build_organism_tx(root,surface,plan['operator'],cost,semantic_target_sha,promotion_sha);sk=(root/ISK).read_text().strip();pk=(root/IPK).read_text().strip();iseq=ip['integration_seq']+1
  entry_payload={'schema':'tukuyo.v840.learning_entry/1','integration_seq':iseq,'individual_id':ip['individual_id'],'previous_learning_sha256':ip['learning_head_sha256'],'surface':surface,'operator':plan['operator'],'learning_cost':cost,'semantic_state_sha256':semantic_target_sha,'semantic_promotion_sha256':promotion_sha,'organism_target_state_sha256':sha256_bytes(canonical(otx['state_env'])),'organism_target_state_seq':otx['seq'],'training_count':len(plan['training']),'holdout_count':len(holdout),'steps':plan['steps'],'protocol_test_fixture':bool(protocol_test_fixture)};entry=_signed(entry_payload,sk,pk);entry_sha=sha256_bytes(canonical(entry))
  newp=copy.deepcopy(ip);newp['integration_seq']=iseq;newp['learning_head_sha256']=entry_sha;newp['organism_anchor_state_seq']=otx['seq'];newp['organism_anchor_state_sha256']=sha256_bytes(canonical(otx['state_env']));newp['semantic_state_seq']=target_sem['payload']['state_seq'];newp['semantic_state_sha256']=semantic_target_sha;newp['capability_generation']=otx['state_env']['payload']['capabilities']['capability_generation'];newp['learning_events']=ip['learning_events']+1
  for k in ('energy','compute','storage'):newp['total_learning_costs'][k]=round(float(ip['total_learning_costs'][k])+float(cost[k]),9)
  newenv=_signed(newp,sk,pk);newhead=_make_head(newenv,entry_sha,sk,pk)
  walp={'schema':'tukuyo.v840.cross_component_wal/1','previous_integration_state_sha256':sha256_bytes(canonical(ienv)),'previous_integration_head_sha256':sha256_bytes(canonical(load_json(root/IHEAD))),'semantic_previous_state_sha256':sha256_bytes(canonical(sem)),'semantic_previous_head_sha256':sha256_bytes(canonical(load_json(_semantic(root)/'promotion_head.json'))),'semantic_changed':plan['changed'],'organism_tx':otx,'learning_entry':entry,'integration_state':newenv,'integration_head':newhead};wal=_signed(walp,sk,pk);atomic_json(root/IWAL,wal)
  if os.environ.get('TUKUYO_V840_CRASH_AFTER')=='wal':os._exit(101)
  _apply_wal(root,walp)
  return {'integration_state':newenv,'learning_entry':entry,'operator':plan['operator'],'cost':cost,'semantic_provenance':{'proposal':plan['proposal'],'holdout':plan['holdout'],'commitment':plan['commitment'],'receipt':plan['receipt']}}

def _write_checked(path,obj,previous_sha=None):
 p=Path(path);target=sha256_bytes(canonical(obj));current=sha256_bytes(p.read_bytes()) if p.exists() else None
 if current==target:return
 if previous_sha=='ABSENT':
  if current is not None:raise V840Error('RECOVERY_CONFLICT:'+str(p))
 elif previous_sha is not None and current!=previous_sha:raise V840Error('RECOVERY_CONFLICT:'+str(p))
 atomic_json(p,obj)

def _apply_wal(root,p):
 root=Path(root);sroot=_semantic(root);oroot=_organism(root)
 for rel,obj in p['semantic_changed'].items():
  pp=sroot/rel
  if rel=='semantic_state.json':prev=p['semantic_previous_state_sha256']
  elif rel=='promotion_head.json':prev=p['semantic_previous_head_sha256']
  else:prev='ABSENT'
  _write_checked(pp,obj,prev)
 if os.environ.get('TUKUYO_V840_CRASH_AFTER')=='semantic':os._exit(102)
 ot=p['organism_tx'];_write_checked(oroot/ot['event_rel'],ot['event_env'],'ABSENT')
 if os.environ.get('TUKUYO_V840_CRASH_AFTER')=='event':os._exit(103)
 _write_checked(oroot/r837.STATE,ot['state_env'],ot['previous_state_sha256'])
 if os.environ.get('TUKUYO_V840_CRASH_AFTER')=='state':os._exit(104)
 _write_checked(oroot/ot['commit_rel'],ot['commit_env'],'ABSENT')
 if os.environ.get('TUKUYO_V840_CRASH_AFTER')=='commit':os._exit(105)
 _write_checked(oroot/r837.HEAD,ot['head_env'],ot['previous_head_sha256'])
 if os.environ.get('TUKUYO_V840_CRASH_AFTER')=='head':os._exit(106)
 entry=p['learning_entry'];seq=entry['payload']['integration_seq'];_write_checked(_ledger_path(root,seq),entry,'ABSENT');_write_checked(root/ISTATE,p['integration_state'],p['previous_integration_state_sha256']);_write_checked(root/IHEAD,p['integration_head'],p['previous_integration_head_sha256'])
 if os.environ.get('TUKUYO_V840_CRASH_AFTER')=='integration':os._exit(107)
 wp=root/IWAL
 if wp.exists():wp.unlink()

def recover(root):
 root=Path(root);wp=root/IWAL
 if not wp.exists():return False
 wal=load_json(wp);pk=(root/IPK).read_text().strip()
 if wal.get('public_key')!=pk or not _verify(wal):raise V840Error('INTEGRATION_WAL_SIGNATURE_INVALID')
 _apply_wal(root,wal['payload']);return True

def run_life_ticks(root,n):
 root=Path(root);recover(root);return r837.run_ticks(_organism(root),int(n))

def evaluate(root,query):
 base=s838.evaluate(_semantic(root),query)
 from tukuyo_v954.provenance import gate_state_answer
 return gate_state_answer(root,query,base,os.environ.get('TUKUYO_CAP_TRUST_DIR'))

def audit(root):
 root=Path(root);errors=[]
 try:ienv=load(root)
 except Exception as e:return {'ok':False,'errors':[str(e)]}
 ip=ienv['payload'];oa=r837.audit(_organism(root));sa=s838.audit(_semantic(root))
 if not oa.get('ok'):errors.append('ORGANISM_AUDIT_FAILED:'+','.join(oa.get('errors',[])))
 if not sa.get('ok'):errors.append('SEMANTIC_AUDIT_FAILED:'+','.join(sa.get('errors',[])))
 try:org,sem=_current_component(root)
 except Exception as e:return {'ok':False,'errors':[str(e)]}
 op=org['payload'];sp=sem['payload']
 if op['identity']['individual_id']!=ip['individual_id'] or op['identity']['lineage_id']!=ip['lineage_id'] or op['identity']['branch_id']!=ip['branch_id']:errors.append('INDIVIDUAL_IDENTITY_DRIFT')
 if op['continuity']['state_seq']<ip['organism_anchor_state_seq']:errors.append('ORGANISM_ROLLBACK_BELOW_INTEGRATION_ANCHOR')
 if sp['state_seq']!=ip['semantic_state_seq'] or sha256_bytes(canonical(sem))!=ip['semantic_state_sha256']:errors.append('SEMANTIC_STATE_NOT_AT_INTEGRATION_HEAD')
 prev=ZERO
 for seq in range(1,ip['integration_seq']+1):
  lp=_ledger_path(root,seq)
  if not lp.exists():errors.append(f'MISSING_LEARNING_ENTRY:{seq}');break
  e=load_json(lp)
  if not _verify(e):errors.append(f'LEARNING_ENTRY_SIGNATURE:{seq}');break
  q=e['payload']
  if q['integration_seq']!=seq or q['previous_learning_sha256']!=prev:errors.append(f'LEARNING_CHAIN:{seq}');break
  if q['individual_id']!=ip['individual_id']:errors.append(f'LEARNING_IDENTITY:{seq}');break
  prev=sha256_bytes(canonical(e))
  cap=[x for x in op['capabilities']['public_capabilities'] if x.get('promotion_sha256')==q['semantic_promotion_sha256']]
  if not cap:errors.append(f'LEARNED_CAPABILITY_NOT_IN_ORGANISM:{seq}');break
  if q['surface'] not in op['memory']['semantic']:errors.append(f'SEMANTIC_MEMORY_MISSING:{seq}');break
 if prev!=ip['learning_head_sha256']:errors.append('LEARNING_HEAD_MISMATCH')
 if int(op['capabilities']['capability_generation'])<int(ip['capability_generation']):errors.append('CAPABILITY_GENERATION_ROLLBACK')
 return {'ok':not errors,'errors':errors,'individual_id':ip['individual_id'],'integration_seq':ip['integration_seq'],'organism_state_seq':op['continuity']['state_seq'],'runtime_tick':op['runtime']['tick'],'simulated_seconds':op['runtime']['simulated_seconds'],'lifecycle':op['lifecycle']['status'],'energy':op['resources']['energy'],'reserve':op['resources']['metabolic_reserve'],'health':op['health']['integrity'],'capability_generation':op['capabilities']['capability_generation'],'semantic_state_seq':sp['state_seq'],'learning_events':ip['learning_events'],'total_learning_costs':ip['total_learning_costs'],'autobiographical_records':len(op['memory']['autobiographical']),'policy_wrong':op['runtime']['policy_wrong'],'invariant_violations':op['runtime']['invariant_violations']}
