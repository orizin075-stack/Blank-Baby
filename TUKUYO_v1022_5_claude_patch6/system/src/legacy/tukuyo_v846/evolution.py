from __future__ import annotations
from pathlib import Path
import copy,os,hashlib,fcntl
from contextlib import contextmanager
from .deps import activate
from .constants import *
from .util import *
activate()
import tukuyo_v845.ecology as e845  # activates exact v844 and transitive organism chain
import tukuyo_v844.lineage as l844
import tukuyo_v841.social as s841
import tukuyo_v840.crypto as c840
import tukuyo_v837.runtime as r837

def _sign(p,sk,pk):return r837._signed(p,sk,pk)
def _verify(e):return r837._verify(e)
def _id(root):return l844._id(root)
def _pk(root):return l844._pk(root)
def _sk(root):return l844._sk(root)

def _norm(node):
 if not isinstance(node,dict) or 'op' not in node:raise V846Error('GENOME_NODE_INVALID')
 op=node['op']
 if op=='x':return {'op':'x'}
 if op=='const':
  v=node.get('value')
  if not isinstance(v,int) or not -3<=v<=3:raise V846Error('GENOME_CONSTANT_RANGE')
  return {'op':'const','value':v}
 if op in ('abs','neg'):
  return {'op':op,'arg':_norm(node.get('arg'))}
 if op in ('add','sub','mul','max','min'):
  return {'op':op,'left':_norm(node.get('left')),'right':_norm(node.get('right'))}
 raise V846Error('GENOME_OPERATOR_INVALID:'+str(op))

def _stats(n):
 n=_norm(n);op=n['op']
 if op in ('x','const'):return (1,1)
 if op in ('abs','neg'):
  c,d=_stats(n['arg']);return c+1,d+1
 a,da=_stats(n['left']);b,db=_stats(n['right']);return a+b+1,max(da,db)+1

def normalize_genome(g):
 n=_norm(g);nodes,depth=_stats(n)
 if nodes>31 or depth>6:raise V846Error('GENOME_COMPLEXITY_LIMIT')
 return n

def shape_genome(n):
 n=normalize_genome(n);op=n['op']
 if op=='x':return {'op':'x'}
 if op=='const':return {'op':'const','value':'#'}
 if op in ('abs','neg'):return {'op':op,'arg':shape_genome(n['arg'])}
 return {'op':op,'left':shape_genome(n['left']),'right':shape_genome(n['right'])}

def genome_sha(g):return sha256_bytes(canonical(normalize_genome(g)))
def shape_sha(g):return sha256_bytes(canonical(shape_genome(g)))

def execute(g,x):
 n=normalize_genome(g)
 def ev(q):
  op=q['op']
  if op=='x':return int(x)
  if op=='const':return q['value']
  if op=='abs':v=abs(ev(q['arg']))
  elif op=='neg':v=-ev(q['arg'])
  else:
   a=ev(q['left']);b=ev(q['right'])
   if op=='add':v=a+b
   elif op=='sub':v=a-b
   elif op=='mul':v=a*b
   elif op=='max':v=max(a,b)
   else:v=min(a,b)
  if v>1000:return 1000
  if v<-1000:return -1000
  return int(v)
 return ev(n)

OPS=('identity','wrap_abs','add_plus1','add_minus1','mul2','negate','add_var','prune')
def mutation_seed(master_seed,generation,parent_genome_sha,parent_id):
 return hashlib.sha256(f'{master_seed}|{generation}|{parent_genome_sha}|{parent_id}'.encode()).hexdigest()
def mutation_op(seed):return OPS[int(hashlib.sha256(seed.encode()).hexdigest(),16)%len(OPS)]
def mutate(parent,seed):
 p=normalize_genome(parent);op=mutation_op(seed)
 if op=='identity':c=p
 elif op=='wrap_abs':c={'op':'abs','arg':p}
 elif op=='add_plus1':c={'op':'add','left':p,'right':{'op':'const','value':1}}
 elif op=='add_minus1':c={'op':'add','left':p,'right':{'op':'const','value':-1}}
 elif op=='mul2':c={'op':'mul','left':p,'right':{'op':'const','value':2}}
 elif op=='negate':c={'op':'neg','arg':p}
 elif op=='add_var':c={'op':'add','left':p,'right':{'op':'x'}}
 else:
  if p['op'] in ('abs','neg'):c=p['arg']
  elif p['op'] in ('add','sub','mul','max','min'):c=p['left']
  else:c=p
 try:c=normalize_genome(c)
 except V846Error:
  c=p;op='identity_complexity_guard'
 return c,op

def score_genome(g,cases):
 rows=[]
 for c in cases:
  a=execute(g,c['x']);rows.append({'id':c['id'],'x':c['x'],'expected':c['expected'],'actual':a,'correct':a==c['expected']})
 return {'correct':sum(r['correct'] for r in rows),'wrong':sum(not r['correct'] for r in rows),'total':len(rows),'rows_sha256':sha256_bytes(canonical(rows)),'rows':rows}

@contextmanager
def evolution_lock(root):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);f=open(root/'.evolution.lock','a+b')
 try:
  try:fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise V846Error('EVOLUTION_ALREADY_ACTIVE')
  yield
 finally:
  try:fcntl.flock(f.fileno(),fcntl.LOCK_UN)
  finally:f.close()

def _genome_state(root,genome,parent_id=None,mutation=None,innovation_ids=None):
 p={'schema':'tukuyo.v846.genome_state/1','individual_id':_id(root),'identity_public_key':_pk(root),'genome':normalize_genome(genome),'genome_sha256':genome_sha(genome),'shape_sha256':shape_sha(genome),'parent_individual_id':parent_id,'mutation':copy.deepcopy(mutation),'innovation_ids':list(innovation_ids or [])}
 return _sign(p,_sk(root),_pk(root))
def _write_genome_state(root,e):
 p=Path(root)/'evolution'/'genome_state.json';p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  if sha256_bytes(p.read_bytes())!=sha256_bytes(canonical(e)):raise V846Error('GENOME_STATE_CONFLICT')
  return
 atomic_json(p,e)
def load_genome_state(root):
 p=Path(root)/'evolution'/'genome_state.json';e=load_json(p)
 if not _verify(e) or e['public_key']!=_pk(root) or e['payload']['individual_id']!=_id(root):raise V846Error('GENOME_STATE_INVALID')
 if e['payload']['genome_sha256']!=genome_sha(e['payload']['genome']) or e['payload']['shape_sha256']!=shape_sha(e['payload']['genome']):raise V846Error('GENOME_STATE_HASH_INVALID')
 return e

def init_evolution(root,lineage_root,founders:dict[str,str],founder_genomes:dict[str,dict],*,evolution_id='TUKUYO-v846-evolution',population_size=4,master_seed='v846-synthetic-coverage-seed-0',cases=None):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);(root/'private').mkdir(exist_ok=True);(root/LEDGER).mkdir(exist_ok=True);(root/GENOMES).mkdir(exist_ok=True);(root/'agents').mkdir(exist_ok=True)
 if (root/REG).exists():return load_registry(root)
 if len(founders)!=population_size or not (3<=population_size<=10):raise V846Error('FOUNDER_POPULATION_SIZE_INVALID')
 l844.load_registry(lineage_root)
 ask,apk=c840.keygen();vask,vapk=c840.keygen();nsk,npk=c840.keygen();esk,epk=c840.keygen()
 keys=[apk,vapk,npk,epk]
 if len(set(keys))!=4:raise V846Error('ROLE_KEY_COLLISION')
 for rel,val in ((AUTH_SK,ask),(VAR_SK,vask),(NOV_SK,nsk),(ENV_SK,esk)):
  p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(val);os.chmod(p,0o600)
 for rel,val in ((AUTH_PK,apk),(VAR_PK,vapk),(NOV_PK,npk),(ENV_PK,epk)):(root/rel).write_text(val)
 members={};identity_keys=set();archive_genomes=set();archive_shapes=set()
 for label,rp in sorted(founders.items()):
  r=Path(rp);iid=_id(r);pk=_pk(r)
  if iid in members or pk in identity_keys or pk in keys:raise V846Error('FOUNDER_IDENTITY_COLLISION')
  g=normalize_genome(founder_genomes[label]);gs=_genome_state(r,g);_write_genome_state(r,gs)
  members[iid]={'individual_id':iid,'identity_public_key':pk,'root_hint':str(r.resolve()),'generation':0,'parent_individual_id':None,'genome':g,'genome_sha256':genome_sha(g),'shape_sha256':shape_sha(g),'status':'selected','innovation_ids':[],'founder_label':label}
  identity_keys.add(pk);archive_genomes.add(genome_sha(g));archive_shapes.add(shape_sha(g))
 if cases is None:cases=[{'id':f'C{i+1:02d}','x':x,'expected':2*abs(x)} for i,x in enumerate(range(-6,7))]
 cases=[{'id':str(c['id']),'x':int(c['x']),'expected':int(c['expected'])} for c in cases]
 if len({c['id'] for c in cases})!=len(cases) or len(cases)<7:raise V846Error('ENVIRONMENT_CASES_INVALID')
 varp={'schema':'tukuyo.v846.variation_commitment/1','master_seed':master_seed,'derivation':'sha256(master_seed|generation|parent_genome_sha|parent_id)','mutation_ops':list(OPS),'committed_before_generation':True}
 var=_sign(varp,vask,vapk);atomic_json(root/VAR_COMMIT,var)
 envp={'schema':'tukuyo.v846.environment_commitment/1','cases':cases,'case_count':len(cases),'cases_sha256':sha256_bytes(canonical(cases)),'selection_rule':'max correct; candidate before incumbent on exact tie; genome sha lexical tie','committed_before_generation':True}
 env=_sign(envp,esk,epk);atomic_json(root/ENV_COMMIT,env)
 founder_scores={iid:score_genome(m['genome'],cases)['correct'] for iid,m in members.items()}
 p={'schema':'tukuyo.v846.evolution_registry/1','evolution_id':evolution_id,'lineage_root_hint':str(Path(lineage_root).resolve()),'generation':0,'generation_head_sha256':ZERO,'birth_count':0,'population_size':population_size,'selected_ids':sorted(members),'members':members,'archive_genome_sha256':sorted(archive_genomes),'archive_shape_sha256':sorted(archive_shapes),'structural_innovation_count':0,'founder_best_correct':max(founder_scores.values()),'founder_scores':founder_scores,'variation_commitment_sha256':sha256_bytes(canonical(var)),'environment_commitment_sha256':sha256_bytes(canonical(env))}
 e=_sign(p,ask,apk);atomic_json(root/REG,e);return e

def load_registry(root):
 root=Path(root);e=load_json(root/REG)
 if e.get('public_key')!=(root/AUTH_PK).read_text().strip() or not _verify(e):raise V846Error('EVOLUTION_REGISTRY_SIGNATURE_INVALID')
 if e['payload'].get('schema')!='tukuyo.v846.evolution_registry/1':raise V846Error('EVOLUTION_REGISTRY_SCHEMA_INVALID')
 return e

def _load_commitments(root):
 root=Path(root);v=load_json(root/VAR_COMMIT);e=load_json(root/ENV_COMMIT)
 if not _verify(v) or v['public_key']!=(root/VAR_PK).read_text().strip():raise V846Error('VARIATION_COMMITMENT_INVALID')
 if not _verify(e) or e['public_key']!=(root/ENV_PK).read_text().strip():raise V846Error('ENVIRONMENT_COMMITMENT_INVALID')
 return v,e

def _classify(candidate,archive_g,archive_s):
 gh=genome_sha(candidate);sh=shape_sha(candidate)
 if gh in archive_g:return 'duplicate'
 if sh in archive_s:return 'parameter_only'
 return 'structural_novelty'

def _novelty_receipt(root,cand,archive_g,archive_s):
 root=Path(root);cls=_classify(cand['genome'],set(archive_g),set(archive_s));p={'schema':'tukuyo.v846.novelty_receipt/1','candidate_id':cand['candidate_id'],'parent_individual_id':cand['parent_individual_id'],'parent_genome_sha256':cand['parent_genome_sha256'],'candidate_genome_sha256':genome_sha(cand['genome']),'candidate_shape_sha256':shape_sha(cand['genome']),'classification':cls,'archive_genome_count':len(archive_g),'archive_shape_count':len(archive_s),'archive_genome_sha256':sha256_bytes(canonical(sorted(archive_g))),'archive_shape_sha256':sha256_bytes(canonical(sorted(archive_s)))}
 return _sign(p,(root/NOV_SK).read_text().strip(),(root/NOV_PK).read_text().strip())
def _environment_receipt(root,entry,cases):
 root=Path(root);sc=score_genome(entry['genome'],cases);p={'schema':'tukuyo.v846.environment_receipt/1','entry_id':entry['entry_id'],'genome_sha256':genome_sha(entry['genome']),'cases_sha256':sha256_bytes(canonical(cases)),'correct':sc['correct'],'wrong':sc['wrong'],'total':sc['total'],'rows_sha256':sc['rows_sha256']}
 return _sign(p,(root/ENV_SK).read_text().strip(),(root/ENV_PK).read_text().strip())

def _verify_receipts(root,cand,nov,env,cases,archive_g,archive_s):
 root=Path(root)
 if not _verify(nov) or nov['public_key']!=(root/NOV_PK).read_text().strip():raise V846Error('NOVELTY_RECEIPT_SIGNATURE_INVALID')
 if nov['public_key'] in ((root/AUTH_PK).read_text().strip(),(root/ENV_PK).read_text().strip(),(root/VAR_PK).read_text().strip()):raise V846Error('NOVELTY_VERIFIER_KEY_NOT_INDEPENDENT')
 exp=_classify(cand['genome'],set(archive_g),set(archive_s));p=nov['payload']
 if p['candidate_id']!=cand['candidate_id'] or p['parent_genome_sha256']!=cand['parent_genome_sha256'] or p['candidate_genome_sha256']!=genome_sha(cand['genome']) or p['candidate_shape_sha256']!=shape_sha(cand['genome']) or p['classification']!=exp or p['archive_genome_count']!=len(archive_g) or p['archive_shape_count']!=len(archive_s) or p['archive_genome_sha256']!=sha256_bytes(canonical(sorted(archive_g))) or p['archive_shape_sha256']!=sha256_bytes(canonical(sorted(archive_s))):raise V846Error('NOVELTY_RECEIPT_DISAGREES_WITH_RAW')
 if not _verify(env) or env['public_key']!=(root/ENV_PK).read_text().strip():raise V846Error('ENVIRONMENT_RECEIPT_SIGNATURE_INVALID')
 if env['public_key'] in ((root/AUTH_PK).read_text().strip(),(root/NOV_PK).read_text().strip(),(root/VAR_PK).read_text().strip()):raise V846Error('ENVIRONMENT_VERIFIER_KEY_NOT_INDEPENDENT')
 sc=score_genome(cand['genome'],cases);q=env['payload']
 if q['entry_id']!=cand['candidate_id'] or q['genome_sha256']!=genome_sha(cand['genome']) or q['cases_sha256']!=sha256_bytes(canonical(cases)) or q['correct']!=sc['correct'] or q['wrong']!=sc['wrong'] or q['total']!=sc['total'] or q['rows_sha256']!=sc['rows_sha256']:raise V846Error('ENVIRONMENT_RECEIPT_DISAGREES_WITH_RAW')
 return exp,sc

def plan_generation(root):
 root=Path(root);reg=load_registry(root);rp=reg['payload'];var,envc=_load_commitments(root);cases=envc['payload']['cases'];g=int(rp['generation'])+1;archive_g=set(rp['archive_genome_sha256']);archive_s=set(rp['archive_shape_sha256']);master=var['payload']['master_seed']
 candidates=[]
 for pid in rp['selected_ids']:
  par=rp['members'][pid];seed=mutation_seed(master,g,par['genome_sha256'],pid);child,op=mutate(par['genome'],seed);cid=f'G{g}:{pid}:{seed[:12]}';c={'candidate_id':cid,'entry_id':cid,'kind':'candidate','parent_individual_id':pid,'parent_genome_sha256':par['genome_sha256'],'parent_shape_sha256':par['shape_sha256'],'variation_seed':seed,'mutation_op':op,'genome':child,'genome_sha256':genome_sha(child),'shape_sha256':shape_sha(child),'inherited_innovation_ids':list(par.get('innovation_ids',[]))};nov=_novelty_receipt(root,c,archive_g,archive_s);ev=_environment_receipt(root,c,cases);cls,sc=_verify_receipts(root,c,nov,ev,cases,archive_g,archive_s);c['novelty_receipt']=nov;c['environment_receipt']=ev;c['novelty_class']=cls;c['score']=sc['correct'];c['wrong']=sc['wrong'];candidates.append(c)
 incumbents=[]
 for pid in rp['selected_ids']:
  m=rp['members'][pid];eid='INC:'+pid;sc=score_genome(m['genome'],cases);incumbents.append({'entry_id':eid,'kind':'incumbent','individual_id':pid,'genome':m['genome'],'genome_sha256':m['genome_sha256'],'shape_sha256':m['shape_sha256'],'score':sc['correct'],'wrong':sc['wrong'],'generation':m['generation'],'innovation_ids':list(m.get('innovation_ids',[]))})
 pool=incumbents+[{'entry_id':c['entry_id'],'kind':'candidate','candidate_id':c['candidate_id'],'parent_individual_id':c['parent_individual_id'],'genome':c['genome'],'genome_sha256':c['genome_sha256'],'shape_sha256':c['shape_sha256'],'score':c['score'],'wrong':c['wrong'],'novelty_class':c['novelty_class'],'inherited_innovation_ids':c['inherited_innovation_ids']} for c in candidates]
 # Candidate wins an exact score tie, encouraging generational turnover without a novelty bonus.
 ranked=sorted(pool,key=lambda x:(-x['score'],0 if x['kind']=='candidate' else 1,x['genome_sha256'],x['entry_id']))
 selected=ranked[:int(rp['population_size'])]
 return {'schema':'tukuyo.v846.generation_plan/1','generation':g,'previous_registry_sha256':sha256_bytes(canonical(reg)),'archive_genome_sha256_before':sorted(archive_g),'archive_shape_sha256_before':sorted(archive_s),'variation_commitment_sha256':rp['variation_commitment_sha256'],'environment_commitment_sha256':rp['environment_commitment_sha256'],'candidates':candidates,'incumbents':incumbents,'ranking':ranked,'selected_entries':selected,'cases_sha256':sha256_bytes(canonical(cases))}

def _recompute_plan(root,plan):
 root=Path(root);reg=load_registry(root);rp=reg['payload'];var,envc=_load_commitments(root);cases=envc['payload']['cases'];errors=[];g=plan['generation'];ag=plan['archive_genome_sha256_before'];ash=plan['archive_shape_sha256_before']
 if plan['previous_registry_sha256']!=sha256_bytes(canonical(reg)):errors.append('PREVIOUS_REGISTRY_BINDING')
 if plan['variation_commitment_sha256']!=rp['variation_commitment_sha256'] or plan['environment_commitment_sha256']!=rp['environment_commitment_sha256'] or plan['cases_sha256']!=sha256_bytes(canonical(cases)):errors.append('COMMITMENT_BINDING')
 expected=[]
 for pid in rp['selected_ids']:
  par=rp['members'][pid];seed=mutation_seed(var['payload']['master_seed'],g,par['genome_sha256'],pid);child,op=mutate(par['genome'],seed);cid=f'G{g}:{pid}:{seed[:12]}';expected.append((pid,seed,op,genome_sha(child),shape_sha(child),cid))
 got=[(c['parent_individual_id'],c['variation_seed'],c['mutation_op'],c['genome_sha256'],c['shape_sha256'],c['candidate_id']) for c in plan['candidates']]
 if got!=expected:errors.append('VARIATION_RECOMPUTE_MISMATCH')
 for c in plan['candidates']:
  try:_verify_receipts(root,c,c['novelty_receipt'],c['environment_receipt'],cases,ag,ash)
  except Exception as e:errors.append(str(e))
 # recompute ranking independently
 inc=[]
 for pid in rp['selected_ids']:
  m=rp['members'][pid];sc=score_genome(m['genome'],cases);inc.append({'entry_id':'INC:'+pid,'kind':'incumbent','individual_id':pid,'genome':m['genome'],'genome_sha256':m['genome_sha256'],'shape_sha256':m['shape_sha256'],'score':sc['correct'],'wrong':sc['wrong'],'generation':m['generation'],'innovation_ids':list(m.get('innovation_ids',[]))})
 cps=[{'entry_id':c['entry_id'],'kind':'candidate','candidate_id':c['candidate_id'],'parent_individual_id':c['parent_individual_id'],'genome':c['genome'],'genome_sha256':c['genome_sha256'],'shape_sha256':c['shape_sha256'],'score':score_genome(c['genome'],cases)['correct'],'wrong':score_genome(c['genome'],cases)['wrong'],'novelty_class':_classify(c['genome'],set(ag),set(ash)),'inherited_innovation_ids':c['inherited_innovation_ids']} for c in plan['candidates']]
 rank=sorted(inc+cps,key=lambda x:(-x['score'],0 if x['kind']=='candidate' else 1,x['genome_sha256'],x['entry_id']))
 if rank!=plan['ranking'] or rank[:int(rp['population_size'])]!=plan['selected_entries']:errors.append('SELECTION_RECOMPUTE_MISMATCH')
 return {'ok':not errors,'errors':errors,'candidate_count':len(plan['candidates']),'structural_novel_candidates':sum(c['novelty_class']=='structural_novelty' for c in plan['candidates']),'best_candidate_correct':max(c['score'] for c in plan['candidates']),'best_selected_correct':max(x['score'] for x in plan['selected_entries'])}

def final_gate(root,plan):
 v=_recompute_plan(root,plan)
 if not v['ok']:raise V846Error('GENERATION_PLAN_NOT_VERIFIED:'+','.join(v['errors']))
 return v

def _child_name(g,cand,serial):return f'TUKUYO-v846-g{g}-c{serial}-{cand["genome_sha256"][:8]}'
def _birth_id(g,serial,cand):return f'V846-G{g}-B{serial}-{cand["genome_sha256"][:8]}'

def prepare_transaction(root):
 root=Path(root);reg=load_registry(root);rp=reg['payload'];plan=plan_generation(root);check=final_gate(root,plan);g=plan['generation'];lineage=Path(rp['lineage_root_hint']);selected_candidates=[x for x in plan['selected_entries'] if x['kind']=='candidate'];materialized=[];serial=0
 cmap={c['candidate_id']:c for c in plan['candidates']}
 # Create fresh child identities before transaction seal. They are not committed until WAL exists.
 for sel in selected_candidates:
  serial+=1;c=cmap[sel['candidate_id']];child=root/'agents'/_child_name(g,c,serial);s841.init(child,_child_name(g,c,serial),initial_energy=100,initial_reserve=2200)
  innovation_ids=list(c['inherited_innovation_ids']);innovation_id=None
  if c['novelty_class']=='structural_novelty':
   innovation_id='INNOV-'+sha256_bytes(canonical({'g':g,'genome':c['genome_sha256'],'parent':c['parent_individual_id']}))[:16];innovation_ids=innovation_ids+[innovation_id]
  mut={'seed':c['variation_seed'],'operator':c['mutation_op'],'novelty_class':c['novelty_class'],'parent_genome_sha256':c['parent_genome_sha256'],'innovation_id':innovation_id}
  gs=_genome_state(child,c['genome'],c['parent_individual_id'],mut,innovation_ids)
  materialized.append({'candidate_id':c['candidate_id'],'parent_individual_id':c['parent_individual_id'],'child_root_hint':str(child.resolve()),'child_individual_id':_id(child),'child_identity_public_key':_pk(child),'birth_id':_birth_id(g,serial,c),'genome_state':gs,'innovation_ids':innovation_ids,'innovation_id':innovation_id})
 # Build target registry.
 target=copy.deepcopy(rp);target['generation']=g;members=copy.deepcopy(rp['members']);selected_ids=[];matmap={m['candidate_id']:m for m in materialized}
 for m in members.values():
  if m['status']=='selected':m['status']='retired'
 for sel in plan['selected_entries']:
  if sel['kind']=='incumbent':
   pid=sel['individual_id'];members[pid]['status']='selected';selected_ids.append(pid)
  else:
   mm=matmap[sel['candidate_id']];c=cmap[sel['candidate_id']];pid=mm['child_individual_id'];members[pid]={'individual_id':pid,'identity_public_key':mm['child_identity_public_key'],'root_hint':mm['child_root_hint'],'generation':g,'parent_individual_id':c['parent_individual_id'],'genome':c['genome'],'genome_sha256':c['genome_sha256'],'shape_sha256':c['shape_sha256'],'status':'selected','innovation_ids':mm['innovation_ids'],'founder_label':None};selected_ids.append(pid)
 target['selected_ids']=sorted(selected_ids);target['members']=members;target['birth_count']=int(rp['birth_count'])+len(materialized)
 ag=set(rp['archive_genome_sha256']);ash=set(rp['archive_shape_sha256'])
 for c in plan['candidates']:ag.add(c['genome_sha256']);ash.add(c['shape_sha256'])
 target['archive_genome_sha256']=sorted(ag);target['archive_shape_sha256']=sorted(ash);target['structural_innovation_count']=int(rp['structural_innovation_count'])+sum(m['innovation_id'] is not None for m in materialized)
 entryp={'schema':'tukuyo.v846.generation_entry/1','generation':g,'previous_generation_sha256':rp['generation_head_sha256'],'plan':plan,'verification_summary':check,'materialized_children':[{k:copy.deepcopy(m[k]) for k in ('candidate_id','parent_individual_id','child_individual_id','child_identity_public_key','birth_id','genome_state','innovation_ids','innovation_id')} for m in materialized]};entry=_sign(entryp,(root/AUTH_SK).read_text().strip(),(root/AUTH_PK).read_text().strip());target['generation_head_sha256']=sha256_bytes(canonical(entry));targetenv=_sign(target,(root/AUTH_SK).read_text().strip(),(root/AUTH_PK).read_text().strip())
 wp={'schema':'tukuyo.v846.generation_wal/1','plan':plan,'entry':entry,'materialized_children':materialized,'previous_registry_sha256':sha256_bytes(canonical(reg)),'target_registry':targetenv};return _sign(wp,(root/AUTH_SK).read_text().strip(),(root/AUTH_PK).read_text().strip())

def _write_exact(path,obj,previous=None):
 p=Path(path);target=sha256_bytes(canonical(obj));cur=sha256_bytes(p.read_bytes()) if p.exists() else None
 if cur==target:return False
 if previous=='ABSENT':
  if cur is not None:raise V846Error('RECOVERY_CONFLICT:'+str(p))
 elif previous is not None and cur!=previous:raise V846Error('RECOVERY_CONFLICT:'+str(p))
 atomic_json(p,obj);return True

def _apply(root,wp):
 root=Path(root);p=wp['payload'];reg=load_registry(root);lineage=Path(reg['payload']['lineage_root_hint'])
 # births through exact v844, then signed genome state
 for m in p['materialized_children']:
  child=Path(m['child_root_hint']);parent=Path(reg['payload']['members'][m['parent_individual_id']]['root_hint']);cert=lineage/l844.BIRTHS/f"{m['birth_id']}.json"
  if not cert.exists():l844.reproduce(lineage,parent,child,[],birth_id=m['birth_id'])
  if _id(child)!=m['child_individual_id'] or _pk(child)!=m['child_identity_public_key']:raise V846Error('CHILD_IDENTITY_DRIFT')
 if os.environ.get('TUKUYO_V846_CRASH_AFTER')=='births':os._exit(231)
 for m in p['materialized_children']:_write_genome_state(Path(m['child_root_hint']),m['genome_state'])
 if os.environ.get('TUKUYO_V846_CRASH_AFTER')=='genomes':os._exit(232)
 g=p['plan']['generation'];lp=root/LEDGER/f'{g:06d}.json';_write_exact(lp,p['entry'],'ABSENT')
 if os.environ.get('TUKUYO_V846_CRASH_AFTER')=='ledger':os._exit(233)
 cur=load_registry(root);cursha=sha256_bytes(canonical(cur));target=p['target_registry'];targetsha=sha256_bytes(canonical(target))
 if cursha!=targetsha:
  if cursha!=p['previous_registry_sha256']:raise V846Error('REGISTRY_RECOVERY_CONFLICT')
  atomic_json(root/REG,target)
 if os.environ.get('TUKUYO_V846_CRASH_AFTER')=='registry':os._exit(234)
 if (root/WAL).exists():(root/WAL).unlink()

def recover_generation(root):
 root=Path(root);wp=root/WAL
 if not wp.exists():return False
 wal=load_json(wp)
 if not _verify(wal) or wal['public_key']!=(root/AUTH_PK).read_text().strip():raise V846Error('GENERATION_WAL_INVALID')
 _apply(root,wal);return True

def step_generation(root):
 root=Path(root)
 with evolution_lock(root):
  recover_generation(root);wal=prepare_transaction(root);atomic_json(root/WAL,wal)
  if os.environ.get('TUKUYO_V846_CRASH_AFTER')=='wal':os._exit(230)
  _apply(root,wal);return wal['payload']['entry']

def audit(root):
 root=Path(root);errors=[]
 try:recover_generation(root);reg=load_registry(root);var,env=_load_commitments(root)
 except Exception as e:return {'ok':False,'errors':[str(e)]}
 rp=reg['payload'];prev=ZERO;innovation_first={};innovation_seen={};parent_of={}
 for g in range(1,int(rp['generation'])+1):
  f=root/LEDGER/f'{g:06d}.json'
  if not f.exists():errors.append('MISSING_GENERATION:'+str(g));break
  e=load_json(f)
  if not _verify(e) or e['public_key']!=(root/AUTH_PK).read_text().strip():errors.append('GENERATION_SIGNATURE:'+str(g));break
  p=e['payload']
  if p['generation']!=g or p['previous_generation_sha256']!=prev:errors.append('GENERATION_CHAIN:'+str(g));break
  try:
   # audit against the historical pre-state embedded in plan instead of current registry
   ag=set(p['plan']['archive_genome_sha256_before']);ash=set(p['plan']['archive_shape_sha256_before']);cases=env['payload']['cases']
   for c in p['plan']['candidates']:_verify_receipts(root,c,c['novelty_receipt'],c['environment_receipt'],cases,ag,ash)
  except Exception as ex:errors.append(str(ex));break
  for m in p['materialized_children']:
   iid=m['child_individual_id'];parent_of[iid]=m['parent_individual_id']
   for inv in m.get('innovation_ids',[]):
    innovation_first.setdefault(inv,g);innovation_seen.setdefault(inv,set()).add(g)
   if m.get('innovation_id'):innovation_first.setdefault(m['innovation_id'],g)
  prev=sha256_bytes(canonical(e))
 if prev!=rp['generation_head_sha256']:errors.append('GENERATION_HEAD_MISMATCH')
 ledger_nums=sorted(int(f.stem) for f in (root/LEDGER).glob('*.json') if f.stem.isdigit())
 expected_nums=list(range(1,int(rp['generation'])+1))
 if ledger_nums!=expected_nums:errors.append('REGISTRY_LEDGER_GENERATION_SET_MISMATCH')
 if len(rp['selected_ids'])!=rp['population_size'] or len(set(rp['selected_ids']))!=len(rp['selected_ids']):errors.append('SELECTED_POPULATION_INVALID')
 # live genome states and identity bindings
 for pid in rp['selected_ids']:
  m=rp['members'].get(pid)
  if not m or m['status']!='selected':errors.append('SELECTED_MEMBER_STATUS:'+pid);continue
  try:
   gs=load_genome_state(m['root_hint']);q=gs['payload']
   if q['genome_sha256']!=m['genome_sha256'] or q['shape_sha256']!=m['shape_sha256'] or q['identity_public_key']!=m['identity_public_key']:errors.append('LIVE_GENOME_BINDING:'+pid)
  except Exception as ex:errors.append(str(ex))
 selected_scores={pid:score_genome(rp['members'][pid]['genome'],env['payload']['cases'])['correct'] for pid in rp['selected_ids']}
 selected_innov=set(i for pid in rp['selected_ids'] for i in rp['members'][pid].get('innovation_ids',[]))
 # Innovation is heritable if some child carries an innovation id already present in its parent.
 heritable=[]
 for iid,m in rp['members'].items():
  par=m.get('parent_individual_id')
  if not par or par not in rp['members']:continue
  shared=set(m.get('innovation_ids',[])) & set(rp['members'][par].get('innovation_ids',[]))
  heritable+=sorted(shared)
 return {'ok':not errors,'errors':errors,'generation':rp['generation'],'population_size':rp['population_size'],'birth_count':rp['birth_count'],'archive_genome_count':len(rp['archive_genome_sha256']),'archive_shape_count':len(rp['archive_shape_sha256']),'structural_innovation_count':rp['structural_innovation_count'],'founder_best_correct':rp['founder_best_correct'],'selected_scores':selected_scores,'selected_best_correct':max(selected_scores.values()),'selected_innovation_ids':sorted(selected_innov),'heritable_innovation_ids':sorted(set(heritable)),'selected_ids':rp['selected_ids'],'members':{k:{q:copy.deepcopy(v[q]) for q in ('individual_id','generation','parent_individual_id','genome_sha256','shape_sha256','status','innovation_ids')} for k,v in rp['members'].items()}}
