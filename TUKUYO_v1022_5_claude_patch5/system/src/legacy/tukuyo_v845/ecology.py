from __future__ import annotations
from pathlib import Path
import copy,os,uuid,fcntl,hashlib
from contextlib import contextmanager
from .deps import activate
from .constants import *
from .util import *
activate()
import tukuyo_v844.lineage as l844
import tukuyo_v841.social as s841
import tukuyo_v840.crypto as c840
import tukuyo_v837.runtime as r837

def _sign(p,sk,pk):return r837._signed(p,sk,pk)
def _verify(e):return r837._verify(e)
def _id(r):return l844._id(r)
def _pk(r):return l844._pk(r)

def _member_public(m):
 return {k:copy.deepcopy(m[k]) for k in ('individual_id','identity_public_key','efficiency','cooperation','balance','status','generation','parent_individual_id','trait_origin')}
def _public_members(ms):return {k:_member_public(v) for k,v in ms.items()}

@contextmanager
def ecology_lock(root):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);f=open(root/'.ecology.lock','a+b')
 try:
  try:fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise V845Error('ECOLOGY_ALREADY_ACTIVE')
  yield
 finally:
  try:fcntl.flock(f.fileno(),fcntl.LOCK_UN)
  finally:f.close()

def init_ecology(root,lineage_root,founders:dict[str,str],traits:dict[str,dict],*,ecology_id='TUKUYO-v845-ecology',resource_pool=500.0,harvest_budget=100.0,maintenance_cost=12.0,birth_threshold=30.0,child_seed=10.0,max_population=10):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);(root/'private').mkdir(exist_ok=True);(root/LEDGER).mkdir(exist_ok=True);(root/'agents').mkdir(exist_ok=True)
 if (root/REG).exists():return load_registry(root)
 l844.load_registry(lineage_root)
 if not (3<=len(founders)<=10):raise V845Error('FOUNDER_COUNT_OUT_OF_RANGE')
 ask,apk=c840.keygen();vsk,vpk=c840.keygen()
 if apk==vpk:raise V845Error('AUTHORITY_VERIFIER_KEY_COLLISION')
 (root/AUTH_SK).write_text(ask);os.chmod(root/AUTH_SK,0o600);(root/AUTH_PK).write_text(apk);(root/VER_SK).write_text(vsk);os.chmod(root/VER_SK,0o600);(root/VER_PK).write_text(vpk)
 members={};keys=set()
 for label,rp in founders.items():
  r=Path(rp);a=l844.v840.audit(r)
  if not a.get('ok'):raise V845Error('FOUNDER_AUDIT_FAILED:'+label)
  pid=_id(r);pk=_pk(r)
  if pid in members or pk in keys:raise V845Error('FOUNDER_IDENTITY_DUPLICATE')
  tr=traits[label];eff=float(tr['efficiency']);coop=float(tr.get('cooperation',0.0))
  if not (0<eff<=5 and 0<=coop<=1):raise V845Error('TRAIT_RANGE_INVALID')
  members[pid]={'individual_id':pid,'identity_public_key':pk,'root_hint':str(r.resolve()),'efficiency':eff,'cooperation':coop,'balance':0.0,'status':'alive','generation':0,'parent_individual_id':None,'trait_origin':pid}
  keys.add(pk)
 if apk in keys or vpk in keys:raise V845Error('ECOLOGY_AUTHORITY_OR_VERIFIER_IS_MEMBER_KEY')
 p={'schema':'tukuyo.v845.ecology_registry/1','ecology_id':ecology_id,'lineage_root_hint':str(Path(lineage_root).resolve()),'generation':0,'generation_head_sha256':ZERO,'resource_pool':float(resource_pool),'initial_resource_total':float(resource_pool),'cumulative_maintenance_burn':0.0,'birth_count':0,'death_count':0,'members':members,'parameters':{'harvest_budget':float(harvest_budget),'maintenance_cost':float(maintenance_cost),'birth_threshold':float(birth_threshold),'child_seed':float(child_seed),'max_population':int(max_population)}}
 e=_sign(p,ask,apk);atomic_json(root/REG,e);return e

def load_registry(root):
 root=Path(root);e=load_json(root/REG)
 if e.get('public_key')!=(root/AUTH_PK).read_text().strip() or not _verify(e):raise V845Error('ECOLOGY_REGISTRY_SIGNATURE_INVALID')
 p=e['payload']
 if p.get('schema')!='tukuyo.v845.ecology_registry/1':raise V845Error('ECOLOGY_REGISTRY_SCHEMA_INVALID')
 return e

def _save_registry(root,p):
 root=Path(root);e=_sign(p,(root/AUTH_SK).read_text().strip(),(root/AUTH_PK).read_text().strip());atomic_json(root/REG,e);return e

def _child_id(ecology_id,g,parent_id,serial):
 h=hashlib.sha256(f'{ecology_id}|{g}|{parent_id}|{serial}'.encode()).hexdigest()[:10]
 return f'TUKUYO-v845-g{g}-b{serial}-{h}'

def _compute_numeric(pre_members,pool,params,generation,birth_count):
 members=copy.deepcopy(pre_members);active=[members[k] for k in sorted(members) if members[k]['status']=='alive'];budget=round(min(float(pool),float(params['harvest_budget'])),6);weights=sum(float(m['efficiency']) for m in active);allocs=[];remaining=budget
 for i,m in enumerate(active):
  share=round(remaining,6) if i==len(active)-1 else round(budget*float(m['efficiency'])/weights,6)
  if i<len(active)-1:remaining=round(remaining-share,6)
  m['balance']=round(float(m['balance'])+share,6);allocs.append({'individual_id':m['individual_id'],'amount':share})
 pool_after=round(float(pool)-budget,6);burns=[];deaths=[]
 for m in active:
  required=float(params['maintenance_cost']);burn=round(min(float(m['balance']),required),6);m['balance']=round(float(m['balance'])-burn,6);burns.append({'individual_id':m['individual_id'],'amount':burn})
  if burn+1e-9<required:
   m['status']='dead';deaths.append({'individual_id':m['individual_id'],'reason':'resource_exhaustion','generation':generation})
 # Cooperation: deterministic small transfer from cooperative individuals to lowest-balance living peer.
 transfers=[];alive=[members[k] for k in sorted(members) if members[k]['status']=='alive']
 for donor in alive:
  if float(donor['cooperation'])<=0 or float(donor['balance'])<=8:continue
  targets=[x for x in alive if x['individual_id']!=donor['individual_id']]
  if not targets:continue
  target=min(targets,key=lambda x:(float(x['balance']),x['individual_id']))
  amt=round(min(2.0*float(donor['cooperation']),max(0.0,float(donor['balance'])-8.0)),6)
  if amt<=0:continue
  donor['balance']=round(float(donor['balance'])-amt,6);target['balance']=round(float(target['balance'])+amt,6);transfers.append({'sender':donor['individual_id'],'receiver':target['individual_id'],'amount':amt})
 births=[];parents=[members[k] for k in sorted(members) if members[k]['status']=='alive'];serial=birth_count
 for par in parents:
  if len(members)+len(births)>=int(params['max_population']):break
  if float(par['balance'])+1e-9<float(params['birth_threshold']):continue
  serial+=1;cid=_child_id('ECO',generation,par['individual_id'],serial);seed=float(params['child_seed']);par['balance']=round(float(par['balance'])-seed,6)
  child={'individual_id':cid,'identity_public_key':None,'efficiency':float(par['efficiency']),'cooperation':float(par['cooperation']),'balance':seed,'status':'alive','generation':int(par['generation'])+1,'parent_individual_id':par['individual_id'],'trait_origin':par['trait_origin']}
  births.append(child)
 for c in births:members[c['individual_id']]=c
 return {'members':members,'resource_pool':pool_after,'allocation_budget':budget,'allocations':allocs,'maintenance_burns':burns,'maintenance_burn_total':round(sum(x['amount'] for x in burns),6),'cooperation_transfers':transfers,'births':births,'deaths':deaths}

def _public_reg_payload(p):
 return {'ecology_id':p['ecology_id'],'generation':p['generation'],'resource_pool':p['resource_pool'],'initial_resource_total':p['initial_resource_total'],'cumulative_maintenance_burn':p['cumulative_maintenance_burn'],'birth_count':p['birth_count'],'death_count':p['death_count'],'members':_public_members(p['members']),'parameters':copy.deepcopy(p['parameters']),'generation_head_sha256':p['generation_head_sha256']}

def plan_generation(root):
 root=Path(root);reg=load_registry(root);p=reg['payload'];g=int(p['generation'])+1;pre=_public_reg_payload(p);comp=_compute_numeric(pre['members'],pre['resource_pool'],p['parameters'],g,int(p['birth_count']))
 # stage child roots to obtain durable identities before the ecology transaction is committed
 births=[];members=copy.deepcopy(p['members'])
 for b in comp['births']:
  par=members[b['parent_individual_id']];child_root=root/'agents'/b['individual_id'];s841.init(child_root,b['individual_id'],initial_energy=100,initial_reserve=2200)
  b=copy.deepcopy(b);b['identity_public_key']=_pk(child_root);b['root_hint']=str(child_root.resolve());births.append(b)
 # Build target member map using numeric balances/status from computation plus identity/path metadata.
 target={}
 for pid,nm in comp['members'].items():
  if pid in members:
   q=copy.deepcopy(members[pid]);q.update({k:nm[k] for k in ('balance','status','efficiency','cooperation','generation','parent_individual_id','trait_origin')});target[pid]=q
 for b in births:target[b['individual_id']]=copy.deepcopy(b)
 post=copy.deepcopy(p);post['generation']=g;post['resource_pool']=comp['resource_pool'];post['cumulative_maintenance_burn']=round(float(p['cumulative_maintenance_burn'])+comp['maintenance_burn_total'],6);post['birth_count']=int(p['birth_count'])+len(births);post['death_count']=int(p['death_count'])+len(comp['deaths']);post['members']=target
 plan={'schema':'tukuyo.v845.generation_plan/1','generation':g,'previous_registry_sha256':sha256_bytes(canonical(reg)),'pre_public':pre,'numeric_result':{k:comp[k] for k in ('resource_pool','allocation_budget','allocations','maintenance_burns','maintenance_burn_total','cooperation_transfers','deaths')},'births':births,'target_public':_public_reg_payload(post),'lineage_birth_ids':[f'ECO-G{g}-B{i+1+int(p["birth_count"])}' for i in range(len(births))]}
 return plan,post

def _recompute_plan(plan):
 pre=plan['pre_public'];g=plan['generation'];comp=_compute_numeric(pre['members'],pre['resource_pool'],pre['parameters'],g,int(pre['birth_count']))
 # Compare all numeric/ecological decisions. Identity keys/path hints are deliberately excluded.
 expbirth=[{k:b[k] for k in ('individual_id','efficiency','cooperation','balance','status','generation','parent_individual_id','trait_origin')} for b in plan['births']]
 gotbirth=[{k:b[k] for k in ('individual_id','efficiency','cooperation','balance','status','generation','parent_individual_id','trait_origin')} for b in comp['births']]
 errors=[]
 if plan['numeric_result']!={k:comp[k] for k in ('resource_pool','allocation_budget','allocations','maintenance_burns','maintenance_burn_total','cooperation_transfers','deaths')}:errors.append('NUMERIC_RESULT_MISMATCH')
 if expbirth!=gotbirth:errors.append('BIRTH_DECISION_MISMATCH')
 # resource conservation: pool + balances + maintenance sink = initial total
 post=plan['target_public'];lhs=round(float(post['resource_pool'])+sum(float(m['balance']) for m in post['members'].values())+float(post['cumulative_maintenance_burn']),6)
 if abs(lhs-float(post['initial_resource_total']))>1e-5:errors.append('RESOURCE_CONSERVATION')
 return {'ok':not errors,'errors':errors,'maintenance_burn_total':comp['maintenance_burn_total'],'births':len(comp['births']),'deaths':len(comp['deaths']),'alive':sum(m['status']=='alive' for m in post['members'].values()),'population':len(post['members'])}

def external_receipt(root,plan):
 root=Path(root);v=_recompute_plan(plan);p={'schema':'tukuyo.v845.external_ecology_receipt/1','generation':plan['generation'],'plan_sha256':sha256_bytes(canonical(plan)),'summary':v,'pass':bool(v['ok'])};return _sign(p,(root/VER_SK).read_text().strip(),(root/VER_PK).read_text().strip())

def final_gate(root,plan,receipt):
 root=Path(root)
 if not _verify(receipt) or receipt['public_key']!=(root/VER_PK).read_text().strip():raise V845Error('EXTERNAL_RECEIPT_SIGNATURE_INVALID')
 if receipt['public_key']==(root/AUTH_PK).read_text().strip():raise V845Error('ECOLOGY_AUTHORITY_SELF_VERIFICATION_FORBIDDEN')
 v=_recompute_plan(plan);p=receipt['payload']
 if p['plan_sha256']!=sha256_bytes(canonical(plan)) or p['summary']!=v:raise V845Error('EXTERNAL_RECEIPT_DISAGREES_WITH_RAW')
 if not v['ok'] or not p['pass']:raise V845Error('ECOLOGY_GENERATION_NOT_VERIFIED')
 return v

def step_generation(root):
 root=Path(root)
 with ecology_lock(root):
  recover_generation(root);plan,target=plan_generation(root);receipt=external_receipt(root,plan);final_gate(root,plan,receipt);reg=load_registry(root);prev_head=reg['payload']['generation_head_sha256'];entryp={'schema':'tukuyo.v845.generation_entry/1','generation':plan['generation'],'previous_generation_sha256':prev_head,'plan':plan,'external_receipt':receipt};entry=_sign(entryp,(root/AUTH_SK).read_text().strip(),(root/AUTH_PK).read_text().strip());esha=sha256_bytes(canonical(entry));target['generation_head_sha256']=esha;target_env=_sign(target,(root/AUTH_SK).read_text().strip(),(root/AUTH_PK).read_text().strip())
  wp={'schema':'tukuyo.v845.generation_wal/1','plan':plan,'entry':entry,'target_registry':target_env,'previous_registry_sha256':sha256_bytes(canonical(reg))};wal=_sign(wp,(root/AUTH_SK).read_text().strip(),(root/AUTH_PK).read_text().strip());atomic_json(root/WAL,wal)
  if os.environ.get('TUKUYO_V845_CRASH_AFTER')=='wal':os._exit(221)
  _apply_generation(root,wp);return entry

def _apply_generation(root,p):
 root=Path(root);reg=load_registry(root);lineage=Path(reg['payload']['lineage_root_hint']);plan=p['plan']
 # materialize all planned births through v844 exactly once
 for idx,b in enumerate(plan['births']):
  bid=plan['lineage_birth_ids'][idx];cert=lineage/l844.BIRTHS/f'{bid}.json';child=Path(b['root_hint']);parent=Path(reg['payload']['members'][b['parent_individual_id']]['root_hint'])
  if not cert.exists():l844.reproduce(lineage,parent,child,[],birth_id=bid)
  if _id(child)!=b['individual_id'] or _pk(child)!=b['identity_public_key']:raise V845Error('ECOLOGY_CHILD_IDENTITY_DRIFT')
 if os.environ.get('TUKUYO_V845_CRASH_AFTER')=='births':os._exit(222)
 lp=root/LEDGER/f"{plan['generation']:06d}.json";targetsha=sha256_bytes(canonical(p['entry']))
 if lp.exists() and sha256_bytes(lp.read_bytes())!=targetsha:raise V845Error('GENERATION_LEDGER_CONFLICT')
 if not lp.exists():atomic_json(lp,p['entry'])
 if os.environ.get('TUKUYO_V845_CRASH_AFTER')=='ledger':os._exit(223)
 cursha=sha256_bytes(canonical(reg));targetreg=p['target_registry'];targetsha=sha256_bytes(canonical(targetreg))
 if cursha!=targetsha:
  if cursha!=p['previous_registry_sha256']:raise V845Error('GENERATION_REGISTRY_CONFLICT')
  atomic_json(root/REG,targetreg)
 if os.environ.get('TUKUYO_V845_CRASH_AFTER')=='registry':os._exit(224)
 if (root/WAL).exists():(root/WAL).unlink()

def recover_generation(root):
 root=Path(root);wp=root/WAL
 if not wp.exists():return False
 wal=load_json(wp)
 if wal.get('public_key')!=(root/AUTH_PK).read_text().strip() or not _verify(wal):raise V845Error('GENERATION_WAL_SIGNATURE_INVALID')
 _apply_generation(root,wal['payload']);return True

def audit(root):
 root=Path(root);errors=[]
 try:recover_generation(root);reg=load_registry(root)
 except Exception as e:return {'ok':False,'errors':[str(e)]}
 p=reg['payload'];prev=ZERO
 for g in range(1,int(p['generation'])+1):
  f=root/LEDGER/f'{g:06d}.json'
  if not f.exists():errors.append('MISSING_GENERATION:'+str(g));break
  e=load_json(f)
  if not _verify(e) or e['public_key']!=(root/AUTH_PK).read_text().strip():errors.append('GENERATION_SIGNATURE:'+str(g));break
  q=e['payload']
  if q['generation']!=g or q['previous_generation_sha256']!=prev:errors.append('GENERATION_CHAIN:'+str(g));break
  try:final_gate(root,q['plan'],q['external_receipt'])
  except Exception as ex:errors.append(str(ex));break
  prev=sha256_bytes(canonical(e))
 if prev!=p['generation_head_sha256']:errors.append('GENERATION_HEAD_MISMATCH')
 total=round(float(p['resource_pool'])+sum(float(m['balance']) for m in p['members'].values())+float(p['cumulative_maintenance_burn']),6)
 if abs(total-float(p['initial_resource_total']))>1e-5:errors.append('RESOURCE_TOTAL_MISMATCH')
 # dead is irreversible across the ledger chain: a dead member may never appear alive in a later target_public.
 dead=set()
 for g in range(1,int(p['generation'])+1):
  q=load_json(root/LEDGER/f'{g:06d}.json')['payload']['plan']['target_public']['members']
  for pid in list(dead):
   if q.get(pid,{}).get('status')=='alive':errors.append('DEATH_REVERSAL:'+pid)
  dead|={pid for pid,m in q.items() if m['status']=='dead'}
 return {'ok':not errors,'errors':errors,'generation':p['generation'],'population':len(p['members']),'alive':sum(m['status']=='alive' for m in p['members'].values()),'birth_count':p['birth_count'],'death_count':p['death_count'],'resource_pool':p['resource_pool'],'cumulative_maintenance_burn':p['cumulative_maintenance_burn'],'resource_total_recomputed':total,'members':_public_members(p['members'])}
