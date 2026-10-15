from __future__ import annotations
from pathlib import Path
import copy,json,os,uuid,fcntl
from contextlib import contextmanager
from .deps import activate
from .constants import *
from .util import *
activate()
import tukuyo_v841.social as s841
import tukuyo_v840.integration as v840
import tukuyo_v840.crypto as c840
import tukuyo_v837.runtime as r837

SOC_SK='private/society.key';SOC_PK='society.pub';REG='society_registry.json'

def _signed(payload,sk,pk):return r837._signed(payload,sk,pk)
def _verify(env):return r837._verify(env)
def _org(root):return Path(root)/'organism'
def _state(root):return r837.load_verified_state(_org(root))
def _id(root):return _state(root)['payload']['identity']['individual_id']
def _sk(root):return (_org(root)/r837.KEY).read_text().strip()
def _pk(root):return _state(root)['public_key']

@contextmanager
def society_lock(root):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);f=open(root/'.society.lock','a+b')
 try:
  try:fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise V842Error('SOCIETY_ALREADY_ACTIVE')
  yield
 finally:
  try:fcntl.flock(f.fileno(),fcntl.LOCK_UN)
  finally:f.close()

def _keygen():return c840.keygen()

def init_society(root,members:dict[str,str],society_id='TUKUYO-v842-society-001'):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);(root/'private').mkdir(exist_ok=True);(root/TRANSFER_LEDGER).mkdir(exist_ok=True);(root/ANNOUNCEMENTS).mkdir(exist_ok=True);(root/BIDS).mkdir(exist_ok=True)
 if (root/REG).exists():return load_registry(root)
 if not (3<=len(members)<=10):raise V842Error('MEMBER_COUNT_OUT_OF_RANGE')
 pins={}
 for name,r in members.items():
  a=s841.audit(r)
  if not a.get('ok'):raise V842Error('MEMBER_AUDIT_FAILED:'+name)
  e=_state(r);pid=e['payload']['identity']['individual_id']
  if pid in pins:raise V842Error('DUPLICATE_INDIVIDUAL_ID')
  if e['public_key'] in [x['identity_public_key'] for x in pins.values()]:raise V842Error('DUPLICATE_IDENTITY_KEY')
  pins[pid]={'label':str(name),'root_hint':str(Path(r).resolve()),'identity_public_key':e['public_key'],'lineage_id':e['payload']['identity']['lineage_id'],'branch_id':e['payload']['identity']['branch_id']}
 sk,pk=_keygen();atomic_bytes(root/SOC_SK,sk.encode());os.chmod(root/SOC_SK,0o600);atomic_bytes(root/SOC_PK,pk.encode())
 payload={'schema':SCHEMA_REGISTRY,'society_id':society_id,'members':pins,'member_count':len(pins),'transfer_head_sha256':'0'*64,'transfer_count':0,'announcement_count':0,'task_receipt_count':0,'note':'coordinator is orchestration authority, not evaluation authority'}
 env=_signed(payload,sk,pk);atomic_json(root/REG,env);return env

def load_registry(root):
 root=Path(root);e=load_json(root/REG);pk=(root/SOC_PK).read_text().strip()
 if e.get('public_key')!=pk or not _verify(e):raise V842Error('SOCIETY_REGISTRY_SIGNATURE_INVALID')
 p=e['payload']
 if p.get('schema')!=SCHEMA_REGISTRY or p.get('member_count')!=len(p.get('members',{})):raise V842Error('SOCIETY_REGISTRY_SCHEMA_INVALID')
 return e

def _save_registry(root,p):
 root=Path(root);sk=(root/SOC_SK).read_text().strip();pk=(root/SOC_PK).read_text().strip();e=_signed(p,sk,pk);atomic_json(root/REG,e);return e

def _member(root,individual_id):
 p=load_registry(root)['payload'];m=p['members'].get(individual_id)
 if not m:raise V842Error('UNKNOWN_SOCIETY_MEMBER')
 return m

def _validate_member_root(society_root,agent_root):
 env=_state(agent_root);pid=env['payload']['identity']['individual_id'];m=_member(society_root,pid)
 if env['public_key']!=m['identity_public_key'] or env['payload']['identity']['branch_id']!=m['branch_id'] or env['payload']['identity']['lineage_id']!=m['lineage_id']:raise V842Error('MEMBER_IDENTITY_DRIFT')
 return pid,env

def capability_announcement(society_root,agent_root):
 root=Path(society_root);pid,env=_validate_member_root(root,agent_root);p=env['payload']
 caps=copy.deepcopy(p['capabilities']['public_capabilities'])
 payload={'schema':SCHEMA_ANNOUNCEMENT,'society_id':load_registry(root)['payload']['society_id'],'individual_id':pid,'identity_public_key':env['public_key'],'source_state_seq':p['continuity']['state_seq'],'source_state_sha256':sha256_bytes(canonical(env)),'capability_generation':p['capabilities']['capability_generation'],'public_capabilities':caps,'announcement_nonce':uuid.uuid4().hex}
 e=_signed(payload,_sk(agent_root),env['public_key']);atomic_json(root/ANNOUNCEMENTS/f'{pid}.json',e)
 rp=copy.deepcopy(load_registry(root)['payload']);rp['announcement_count']=sum(1 for _ in (root/ANNOUNCEMENTS).glob('*.json'));_save_registry(root,rp);return e

def load_announcements(root):
 root=Path(root);reg=load_registry(root)['payload'];out={}
 for f in sorted((root/ANNOUNCEMENTS).glob('*.json')):
  e=load_json(f)
  if not _verify(e):raise V842Error('ANNOUNCEMENT_SIGNATURE_INVALID')
  p=e['payload'];pid=p['individual_id'];m=reg['members'].get(pid)
  if not m or e['public_key']!=m['identity_public_key'] or p['identity_public_key']!=e['public_key']:raise V842Error('ANNOUNCEMENT_IDENTITY_BINDING_INVALID')
  old=out.get(pid)
  if old and int(p['source_state_seq'])<int(old['payload']['source_state_seq']):raise V842Error('ANNOUNCEMENT_ROLLBACK')
  out[pid]=e
 return out

def _transfer_marker(root,peer,kind,txid):
 try:r=s841.peer_model(root,peer,include_private=True)['relationship'] or {}
 except Exception:return False
 return txid in r.get(kind,[])

def _apply_transfer_side(agent_root,peer,amount,txid,outgoing):
 kind='society_outgoing_transfer_ids' if outgoing else 'society_incoming_transfer_ids'
 if _transfer_marker(agent_root,peer,kind,txid):return False
 def mutate(nxt,nt):
  rel=nxt['relationships'].get(peer)
  if not rel:raise V842Error('TRANSFER_REQUIRES_KNOWN_PEER')
  ids=list(rel.get(kind,[]))
  if txid in ids:return
  if outgoing:
   if float(nxt['resources']['compute_credit'])<float(amount):raise V842Error('INSUFFICIENT_COMPUTE_FOR_TRANSFER')
   nxt['resources']['compute_credit']=round(float(nxt['resources']['compute_credit'])-float(amount),9)
  else:nxt['resources']['compute_credit']=round(float(nxt['resources']['compute_credit'])+float(amount),9)
  ids.append(txid);rel[kind]=ids[-256:]
 s841._social_tx(agent_root,'society_transfer_out' if outgoing else 'society_transfer_in',peer,txid,mutate,{'transfer_id':txid,'principal_compute':float(amount),'direction':'out' if outgoing else 'in'})
 return True

def transfer_compute(society_root,sender_root,receiver_root,amount,transfer_id=None):
 root=Path(society_root);amount=float(amount)
 if amount<=0:raise V842Error('TRANSFER_AMOUNT_INVALID')
 sid,_=_validate_member_root(root,sender_root);rid,_=_validate_member_root(root,receiver_root)
 if sid==rid:raise V842Error('SELF_TRANSFER_FORBIDDEN')
 txid=transfer_id or uuid.uuid4().hex
 with society_lock(root):
  recover_transfers(root)
  ledger=root/TRANSFER_LEDGER/f'{txid}.json'
  if ledger.exists():raise V842Error('TRANSFER_REPLAY')
  regp=load_registry(root)['payload'];payload={'schema':SCHEMA_TRANSFER,'society_id':regp['society_id'],'transfer_id':txid,'sender_individual_id':sid,'receiver_individual_id':rid,'principal_compute':amount,'sender_root_hint':str(Path(sender_root).resolve()),'receiver_root_hint':str(Path(receiver_root).resolve()),'previous_transfer_head_sha256':regp['transfer_head_sha256']}
  sk=(root/SOC_SK).read_text().strip();pk=(root/SOC_PK).read_text().strip();wal=_signed(payload,sk,pk);atomic_json(root/TRANSFER_WAL,wal)
  if os.environ.get('TUKUYO_V842_CRASH_AFTER')=='wal':os._exit(181)
  _apply_transfer_side(sender_root,rid,amount,txid,True)
  if os.environ.get('TUKUYO_V842_CRASH_AFTER')=='sender':os._exit(182)
  _apply_transfer_side(receiver_root,sid,amount,txid,False)
  if os.environ.get('TUKUYO_V842_CRASH_AFTER')=='receiver':os._exit(183)
  receipt={'payload':payload,'sender_after_state_sha256':sha256_bytes(canonical(_state(sender_root))),'receiver_after_state_sha256':sha256_bytes(canonical(_state(receiver_root)))}
  receipt=_signed(receipt,sk,pk);atomic_json(ledger,receipt)
  if os.environ.get('TUKUYO_V842_CRASH_AFTER')=='ledger':os._exit(184)
  _commit_transfer_registry(root,receipt)
  if os.environ.get('TUKUYO_V842_CRASH_AFTER')=='registry':os._exit(185)
  p=root/TRANSFER_WAL
  if p.exists():p.unlink()
  return receipt


def _commit_transfer_registry(root,receipt):
 root=Path(root);rp=copy.deepcopy(load_registry(root)['payload']);q=receipt['payload']['payload'];rsha=sha256_bytes(canonical(receipt));prev=q['previous_transfer_head_sha256']
 if rp['transfer_head_sha256']==rsha:return False
 if rp['transfer_head_sha256']!=prev:raise V842Error('TRANSFER_LEDGER_HEAD_CONFLICT')
 rp['previous_transfer_head_sha256']=prev;rp['transfer_head_sha256']=rsha;rp['transfer_count']=int(rp['transfer_count'])+1;_save_registry(root,rp);return True

def recover_transfers(root):
 root=Path(root);p=root/TRANSFER_WAL
 if not p.exists():return False
 wal=load_json(p);reg=load_registry(root);pk=reg['public_key']
 if wal.get('public_key')!=pk or not _verify(wal):raise V842Error('TRANSFER_WAL_SIGNATURE_INVALID')
 q=wal['payload'];sid=q['sender_individual_id'];rid=q['receiver_individual_id'];m1=_member(root,sid);m2=_member(root,rid)
 sr=Path(q['sender_root_hint']);rr=Path(q['receiver_root_hint'])
 # Exact pinned identity is rechecked; path hints are not trusted as identity.
 _validate_member_root(root,sr);_validate_member_root(root,rr)
 txid=q['transfer_id'];amount=q['principal_compute'];ledger=root/TRANSFER_LEDGER/f'{txid}.json'
 _apply_transfer_side(sr,rid,amount,txid,True);_apply_transfer_side(rr,sid,amount,txid,False)
 if not ledger.exists():
  sk=(root/SOC_SK).read_text().strip();receipt=_signed({'payload':q,'sender_after_state_sha256':sha256_bytes(canonical(_state(sr))),'receiver_after_state_sha256':sha256_bytes(canonical(_state(rr)))},sk,pk);atomic_json(ledger,receipt)
 else:
  receipt=load_json(ledger)
  if receipt.get('public_key')!=pk or not _verify(receipt) or receipt.get('payload',{}).get('payload')!=q:raise V842Error('TRANSFER_RECEIPT_INVALID')
 _commit_transfer_registry(root,receipt)
 p.unlink();return True

def _surface(query):
 parts=str(query).strip().split()
 return parts[1] if len(parts)>=3 else ''

def _answer(agent_root,task):
 r=v840.evaluate(agent_root,task['query']);out={'task_id':task['id'],'query':task['query'],'status':r.get('status'),'output':r.get('answer') if r.get('status')=='RESOLVED' else None,'responder_individual_id':_id(agent_root),'responder_state_sha256':sha256_bytes(canonical(_state(agent_root)))}
 return _signed(out,_sk(agent_root),_pk(agent_root))

def solo_run(agent_root,tasks):return [_answer(agent_root,t) for t in tasks]

def cluster_run(society_root,member_roots:dict[str,str],tasks):
 anns=load_announcements(society_root);capmap={}
 for pid,e in anns.items():
  for c in e['payload']['public_capabilities']:
   s=c.get('surface')
   if s:capmap.setdefault(s,[]).append(pid)
 roots={_id(r):r for r in member_roots.values()};answers=[]
 for t in tasks:
  candidates=sorted(capmap.get(_surface(t['query']),[]))
  if not candidates:
   answers.append({'payload':{'task_id':t['id'],'query':t['query'],'status':'OPEN','output':None,'responder_individual_id':None,'responder_state_sha256':None},'public_key':None,'signature':None});continue
  answers.append(_answer(roots[candidates[0]],t))
 return answers

def verify_task_results(society_root,tasks,answers):
 reg=load_registry(society_root)['payload'];byid={x['id']:x for x in tasks};seen=set();correct=wrong=abstain=0;detail=[]
 for a in answers:
  p=a['payload'];tid=p['task_id']
  if tid in seen:raise V842Error('DUPLICATE_TASK_RESULT')
  seen.add(tid);t=byid.get(tid)
  if not t or p['query']!=t['query']:raise V842Error('TASK_RESULT_BINDING_INVALID')
  if p['responder_individual_id'] is None:
   if p['status']!='OPEN' or p['output'] is not None:raise V842Error('ABSTENTION_FORMAT_INVALID')
   abstain+=1;detail.append({'id':tid,'result':'abstain'});continue
  pid=p['responder_individual_id'];m=reg['members'].get(pid)
  if not m or a.get('public_key')!=m['identity_public_key'] or not _verify(a):raise V842Error('TASK_ANSWER_SIGNATURE_INVALID')
  if p['status']!='RESOLVED':abstain+=1;detail.append({'id':tid,'result':'abstain'});continue
  if p['output']==t['expected']:correct+=1;detail.append({'id':tid,'result':'correct','responder':pid})
  else:wrong+=1;detail.append({'id':tid,'result':'wrong','responder':pid})
 missing=set(byid)-seen
 if missing:raise V842Error('MISSING_TASK_RESULTS')
 return {'total':len(tasks),'correct':correct,'wrong':wrong,'abstain':abstain,'coverage':correct/len(tasks) if tasks else 0.0,'detail':detail}

def competition_bid(society_root,agent_root,job_id,cost):
 pid,env=_validate_member_root(society_root,agent_root);cost=float(cost)
 if cost<0:raise V842Error('BID_COST_INVALID')
 p={'schema':SCHEMA_BID,'society_id':load_registry(society_root)['payload']['society_id'],'job_id':str(job_id),'bidder_individual_id':pid,'cost':cost,'bid_nonce':uuid.uuid4().hex}
 return _signed(p,_sk(agent_root),env['public_key'])

def select_bid_winner(society_root,job_id,bids):
 reg=load_registry(society_root)['payload'];valid=[];nonces=set()
 for b in bids:
  if not _verify(b):raise V842Error('BID_SIGNATURE_INVALID')
  p=b['payload'];pid=p['bidder_individual_id']
  if p.get('schema')!=SCHEMA_BID or p.get('society_id')!=reg['society_id'] or p.get('job_id')!=str(job_id):raise V842Error('BID_BINDING_INVALID')
  if pid not in reg['members'] or b['public_key']!=reg['members'][pid]['identity_public_key']:raise V842Error('BID_IDENTITY_INVALID')
  if p['bid_nonce'] in nonces:raise V842Error('BID_REPLAY')
  nonces.add(p['bid_nonce']);valid.append((float(p['cost']),pid,b))
 if not valid:raise V842Error('NO_VALID_BIDS')
 valid.sort(key=lambda x:(x[0],x[1]));return {'winner_individual_id':valid[0][1],'winning_cost':valid[0][0],'bid_sha256':sha256_bytes(canonical(valid[0][2]))}

def audit(society_root,member_roots:dict[str,str]|None=None):
 root=Path(society_root);errors=[]
 try:recover_transfers(root);reg=load_registry(root)
 except Exception as e:return {'ok':False,'errors':[str(e)]}
 p=reg['payload'];keys=set()
 for pid,m in p['members'].items():
  if m['identity_public_key'] in keys:errors.append('DUPLICATE_MEMBER_KEY:'+pid)
  keys.add(m['identity_public_key'])
 if member_roots:
  ids=set()
  for label,r in member_roots.items():
   try:pid,_=_validate_member_root(root,r);a=s841.audit(r)
   except Exception as e:errors.append(label+':'+str(e));continue
   if not a.get('ok'):errors.append(label+':MEMBER_AUDIT_FAILED')
   if pid in ids:errors.append('DUPLICATE_RUNTIME_ID:'+pid)
   ids.add(pid)
 # Verify signed transfer ledger and its hash chain.
 receipts={}
 for f in (root/TRANSFER_LEDGER).glob('*.json'):
  try:
   e=load_json(f)
   if e.get('public_key')!=reg['public_key'] or not _verify(e):errors.append('TRANSFER_RECEIPT_SIGNATURE:'+f.name);continue
   receipts[sha256_bytes(canonical(e))]=e
  except Exception as ex:errors.append('TRANSFER_RECEIPT_READ:'+f.name)
 if len(receipts)!=int(p['transfer_count']):errors.append('TRANSFER_COUNT_MISMATCH')
 h=p['transfer_head_sha256'];walk=0;seen=set()
 while h!='0'*64:
  if h in seen:errors.append('TRANSFER_CHAIN_CYCLE');break
  seen.add(h);e=receipts.get(h)
  if not e:errors.append('TRANSFER_HEAD_OR_LINK_MISSING');break
  h=e['payload']['payload'].get('previous_transfer_head_sha256');walk+=1
 if walk!=int(p['transfer_count']):errors.append('TRANSFER_CHAIN_LENGTH_MISMATCH')
 if (root/TRANSFER_WAL).exists():errors.append('PENDING_TRANSFER_WAL')
 return {'ok':not errors,'errors':errors,'society_id':p['society_id'],'member_count':p['member_count'],'transfer_count':p['transfer_count'],'announcement_count':p['announcement_count']}
