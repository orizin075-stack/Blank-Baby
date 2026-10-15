from __future__ import annotations
from pathlib import Path
import copy,os,uuid
from .deps import activate
from .constants import SCHEMA_PACKET,SCHEMA_ACK,SOCIAL_WAL,PRIVATE_FORBIDDEN_KEYS
from .util import canonical,load_json,sha256_bytes,atomic_json,V841Error
activate()
import tukuyo_v840.integration as v840
import tukuyo_v837.runtime as r837

PACKET_KEYS={'schema','sender_individual_id','sender_lineage_id','sender_branch_id','recipient_individual_id','identity_public_key','sender_state_seq','sender_tick','source_state_sha256','packet_nonce','public_capabilities','public_observations','public_message','privacy_classification'}
ACK_KEYS={'schema','ack_sender_individual_id','ack_sender_lineage_id','ack_sender_branch_id','ack_sender_public_key','original_sender_individual_id','packet_sha256','receiver_state_seq','status'}
CAP_KEYS={'kind','surface','operator','semantic_state_sha256','promotion_sha256','acquired_tick'}
OBS_KEYS={'topic','value','confidence','provenance_sha256'}
SOCIAL_COST={'energy':0.03,'compute':0.15,'storage':0.005}

def _oroot(root):return Path(root)/'organism'
def init(root,individual_id,**kwargs):
 env=v840.init(root,individual_id=individual_id,**kwargs);a=audit(root)
 if not a['ok']:raise V841Error('INIT_AUDIT_FAILED:'+','.join(a['errors']))
 return env

def _signed(payload,sk,pk):return r837._signed(payload,sk,pk)
def _verify(env):return r837._verify(env)
def _packet_sha(packet):return sha256_bytes(canonical(packet))
def _contains_forbidden_key(obj):
 if isinstance(obj,dict):
  for k,v in obj.items():
   if str(k).lower() in PRIVATE_FORBIDDEN_KEYS:return str(k)
   bad=_contains_forbidden_key(v)
   if bad:return bad
 elif isinstance(obj,list):
  for v in obj:
   bad=_contains_forbidden_key(v)
   if bad:return bad
 return None

def _sanitize_caps(caps):
 out=[]
 for c in caps:
  if not isinstance(c,dict):continue
  z={k:c[k] for k in CAP_KEYS if k in c}
  if z:out.append(z)
 return out

def _sanitize_obs(obs):
 if obs is None:return []
 if not isinstance(obs,list):raise V841Error('PUBLIC_OBSERVATIONS_MUST_BE_LIST')
 out=[]
 for x in obs:
  if not isinstance(x,dict) or set(x)-OBS_KEYS:raise V841Error('PUBLIC_OBSERVATION_SCHEMA_INVALID')
  z=dict(x)
  if 'confidence' in z and not (0<=float(z['confidence'])<=1):raise V841Error('PUBLIC_OBSERVATION_CONFIDENCE_INVALID')
  out.append(z)
 return out

def _load_org(root):
 v840.recover(root);return r837.load_verified_state(_oroot(root))

def make_public_packet(root,recipient_individual_id,*,public_message='',public_observations=None):
 root=Path(root);a=v840.audit(root)
 if not a.get('ok'):raise V841Error('BASE_AUDIT_FAILED')
 env=_load_org(root);p=env['payload'];sid=p['identity']['individual_id']
 if recipient_individual_id==sid:raise V841Error('SELF_RECIPIENT_FORBIDDEN')
 msg=str(public_message)
 if len(msg.encode())>2048:raise V841Error('PUBLIC_MESSAGE_TOO_LARGE')
 payload={
  'schema':SCHEMA_PACKET,'sender_individual_id':sid,'sender_lineage_id':p['identity']['lineage_id'],'sender_branch_id':p['identity']['branch_id'],
  'recipient_individual_id':str(recipient_individual_id),'identity_public_key':env['public_key'],'sender_state_seq':p['continuity']['state_seq'],'sender_tick':p['runtime']['tick'],
  'source_state_sha256':sha256_bytes(canonical(env)),'packet_nonce':uuid.uuid4().hex,'public_capabilities':_sanitize_caps(p['capabilities']['public_capabilities']),
  'public_observations':_sanitize_obs(public_observations),'public_message':msg,'privacy_classification':'PUBLIC_ONLY'
 }
 # Defensive structural scan. Explicit public_message is intentionally allowed as caller-selected public content.
 probe={k:v for k,v in payload.items() if k!='public_message'}
 bad=_contains_forbidden_key(probe)
 if bad:raise V841Error('PRIVATE_FIELD_LEAK:'+bad)
 sk=(_oroot(root)/r837.KEY).read_text().strip();return _signed(payload,sk,env['public_key'])

def _validate_packet(packet):
 if not isinstance(packet,dict) or set(packet)!={'payload','public_key','signature'}:raise V841Error('PACKET_ENVELOPE_INVALID')
 if not _verify(packet):raise V841Error('PACKET_SIGNATURE_INVALID')
 p=packet['payload']
 if set(p)!=PACKET_KEYS or p.get('schema')!=SCHEMA_PACKET:raise V841Error('PACKET_SCHEMA_INVALID')
 if p['identity_public_key']!=packet['public_key']:raise V841Error('PACKET_KEY_BINDING_INVALID')
 for c in p['public_capabilities']:
  if not isinstance(c,dict) or set(c)-CAP_KEYS:raise V841Error('PUBLIC_CAPABILITY_SCHEMA_INVALID')
 for x in p['public_observations']:
  if not isinstance(x,dict) or set(x)-OBS_KEYS:raise V841Error('PUBLIC_OBSERVATION_SCHEMA_INVALID')
 bad=_contains_forbidden_key({k:v for k,v in p.items() if k!='public_message'})
 if bad:raise V841Error('FORBIDDEN_PRIVATE_FIELD_IN_PACKET:'+bad)
 if p['privacy_classification']!='PUBLIC_ONLY':raise V841Error('PACKET_PRIVACY_CLASS_INVALID')
 return p

def _validate_ack(ack):
 if not isinstance(ack,dict) or set(ack)!={'payload','public_key','signature'}:raise V841Error('ACK_ENVELOPE_INVALID')
 if not _verify(ack):raise V841Error('ACK_SIGNATURE_INVALID')
 p=ack['payload']
 if set(p)!=ACK_KEYS or p.get('schema')!=SCHEMA_ACK:raise V841Error('ACK_SCHEMA_INVALID')
 if p['ack_sender_public_key']!=ack['public_key']:raise V841Error('ACK_KEY_BINDING_INVALID')
 if p['status']!='ACCEPTED':raise V841Error('ACK_STATUS_INVALID')
 return p

def _pin_peer(p,peer_id,peer_key,peer_lineage,peer_branch):
 if peer_id==p['identity']['individual_id']:raise V841Error('SELF_AS_PEER_FORBIDDEN')
 for oid,m in p['other_models'].items():
  if oid!=peer_id and m.get('identity_public_key')==peer_key:raise V841Error('PEER_KEY_REUSED_FOR_DIFFERENT_ID')
 old=p['other_models'].get(peer_id)
 if old:
  if old.get('identity_public_key')!=peer_key:raise V841Error('PEER_KEY_CONFLICT')
  if old.get('branch_id')!=peer_branch:raise V841Error('PEER_BRANCH_DRIFT')
  if old.get('lineage_id')!=peer_lineage:raise V841Error('PEER_LINEAGE_DRIFT')
 return old

def _write_checked(path,obj,previous_sha=None):
 p=Path(path);target=sha256_bytes(canonical(obj));current=sha256_bytes(p.read_bytes()) if p.exists() else None
 if current==target:return
 if previous_sha=='ABSENT':
  if current is not None:raise V841Error('RECOVERY_CONFLICT:'+str(p))
 elif previous_sha is not None and current!=previous_sha:raise V841Error('RECOVERY_CONFLICT:'+str(p))
 atomic_json(p,obj)

def _apply_social_wal(root,wpayload):
 oroot=_oroot(root);tx=wpayload['organism_tx']
 _write_checked(oroot/tx['event_rel'],tx['event_env'],'ABSENT')
 if os.environ.get('TUKUYO_V841_CRASH_AFTER')=='event':os._exit(142)
 _write_checked(oroot/r837.STATE,tx['state_env'],tx['previous_state_sha256'])
 if os.environ.get('TUKUYO_V841_CRASH_AFTER')=='state':os._exit(143)
 _write_checked(oroot/tx['commit_rel'],tx['commit_env'],'ABSENT')
 if os.environ.get('TUKUYO_V841_CRASH_AFTER')=='commit':os._exit(144)
 _write_checked(oroot/r837.HEAD,tx['head_env'],tx['previous_head_sha256'])
 if os.environ.get('TUKUYO_V841_CRASH_AFTER')=='head':os._exit(145)
 if tx['checkpoint']:r837._checkpoint(oroot,tx['state_env'])
 p=Path(root)/SOCIAL_WAL
 if p.exists():p.unlink()

def _recover_social_unlocked(root):
 p=Path(root)/SOCIAL_WAL
 if not p.exists():return False
 wal=load_json(p)
 if not _verify(wal):raise V841Error('SOCIAL_WAL_SIGNATURE_INVALID')
 # A crash can leave STATE ahead of HEAD. Validate the current state signature/key
 # without rollback enforcement, then restore the signed WAL to a coherent head.
 oroot=_oroot(root);raw=load_json(oroot/r837.STATE)
 try:verified=r837._verify_state_env(oroot,raw,rollback=False)
 except Exception as e:raise V841Error('SOCIAL_RECOVERY_STATE_INVALID:'+str(e))
 cur=verified['payload']['identity']['individual_id']
 if wal['payload'].get('individual_id')!=cur:raise V841Error('SOCIAL_WAL_IDENTITY_MISMATCH')
 _apply_social_wal(root,wal['payload'])
 # Recovery is not complete until normal rollback-aware verification succeeds.
 r837.load_verified_state(oroot)
 return True

def recover_social(root):
 root=Path(root);oroot=_oroot(root)
 with v840.integration_lock(root):
  with r837.writer_lock(oroot):
   v840.recover(root);r837.recover(oroot);return _recover_social_unlocked(root)

def _social_tx(root,action,peer_id,packet_sha,mutator,detail=None):
 root=Path(root);oroot=_oroot(root)
 with v840.integration_lock(root):
  with r837.writer_lock(oroot):
   v840.recover(root);r837.recover(oroot);_recover_social_unlocked(root)
   cur=r837.load_verified_state(oroot);p=cur['payload'];sk=(oroot/r837.KEY).read_text().strip();pk=cur['public_key']
   if p['lifecycle']['status']!='alive':raise V841Error('ORGANISM_NOT_ALIVE')
   if p['resources']['energy']<SOCIAL_COST['energy']+0.5:raise V841Error('INSUFFICIENT_ENERGY_FOR_SOCIAL_ACTION')
   if p['resources']['compute_credit']<SOCIAL_COST['compute'] or p['resources']['storage_credit']<SOCIAL_COST['storage']:raise V841Error('INSUFFICIENT_RESOURCE_FOR_SOCIAL_ACTION')
   nxt=copy.deepcopy(p);nt=p['runtime']['tick']+1
   nxt['resources']['energy']=round(nxt['resources']['energy']-SOCIAL_COST['energy'],9);nxt['resources']['compute_credit']=round(nxt['resources']['compute_credit']-SOCIAL_COST['compute'],9);nxt['resources']['storage_credit']=round(nxt['resources']['storage_credit']-SOCIAL_COST['storage'],9)
   nxt['metabolism']['cumulative_costs']['energy_burn']=round(nxt['metabolism']['cumulative_costs']['energy_burn']+SOCIAL_COST['energy'],9);nxt['metabolism']['cumulative_costs']['compute']=round(nxt['metabolism']['cumulative_costs']['compute']+SOCIAL_COST['compute'],9);nxt['metabolism']['cumulative_costs']['storage']=round(nxt['metabolism']['cumulative_costs']['storage']+SOCIAL_COST['storage'],9);nxt['metabolism']['last_cost']=dict(SOCIAL_COST);nxt['metabolism']['last_decision_reason']=action
   nxt['runtime']['tick']=nt;nxt['runtime']['simulated_seconds']=nt*nxt['runtime']['tick_seconds'];nxt['runtime']['action_counts'][action]=int(nxt['runtime']['action_counts'].get(action,0))+1
   mutator(nxt,nt)
   episode={'tick':nt,'action':action,'decision_reason':'other_agent_interaction','peer_id':peer_id,'packet_sha256':packet_sha,'experienced_value':0.2,'prediction_error':0.1,'origin_individual_id':p['identity']['individual_id']}
   nxt['memory']['episodic'].append(episode);nxt['memory']['episodic']=nxt['memory']['episodic'][-256:]
   nxt['continuity']['state_seq']=p['continuity']['state_seq']+1;nxt['continuity']['previous_state_sha256']=sha256_bytes(canonical(cur));seq=nxt['continuity']['state_seq']
   evp={'schema':'tukuyo.organism_event.v841.social/1','individual_id':p['identity']['individual_id'],'branch_id':p['identity']['branch_id'],'state_seq':seq,'runtime_tick':nt,'previous_event_sha256':p['continuity']['event_head_sha256'],'action':action,'peer_id':peer_id,'packet_sha256':packet_sha,'detail':detail or {},'post_energy':nxt['resources']['energy'],'post_health':nxt['health']['integrity']}
   evenv=r837._signed(evp,sk,pk);evsha=sha256_bytes(canonical(evenv));nxt['continuity']['event_head_sha256']=evsha
   if not r837._verify_invariants(nxt):raise V841Error('SOCIAL_STATE_INVARIANT_FAILED')
   stenv=r837._signed(nxt,sk,pk);prevhead=r837._read_head(oroot);commit=r837._commit_env_for(stenv,prevhead['payload']['commit_sha256'],sk,pk);head=r837._head_env_for(stenv,commit,sk,pk)
   tx={'event_rel':f'events/{seq:012d}.json','event_env':evenv,'state_env':stenv,'commit_rel':f'state_commits/{seq:012d}.json','commit_env':commit,'head_env':head,'previous_state_sha256':sha256_bytes(canonical(cur)),'previous_head_sha256':sha256_bytes(canonical(prevhead)),'checkpoint':bool(seq%nxt['runtime']['checkpoint_interval']==0)}
   wp={'schema':'tukuyo.v841.social_wal/1','individual_id':p['identity']['individual_id'],'organism_tx':tx};wal=r837._signed(wp,sk,pk);atomic_json(root/SOCIAL_WAL,wal)
   if os.environ.get('TUKUYO_V841_CRASH_AFTER')=='wal':os._exit(141)
   _apply_social_wal(root,wp);return stenv

def receive_packet(root,packet):
 pp=_validate_packet(packet);root=Path(root);cur=_load_org(root);selfp=cur['payload'];sid=pp['sender_individual_id']
 if pp['recipient_individual_id']!=selfp['identity']['individual_id']:raise V841Error('PACKET_WRONG_RECIPIENT')
 _pin_peer(selfp,sid,packet['public_key'],pp['sender_lineage_id'],pp['sender_branch_id']);psha=_packet_sha(packet)
 old=selfp['other_models'].get(sid,{});oldrel=selfp['relationships'].get(sid,{})
 if psha in oldrel.get('seen_packet_sha256',[]):raise V841Error('PACKET_REPLAY')
 if old and int(pp['sender_state_seq'])<int(old.get('source_state_seq',0)):raise V841Error('PEER_STATE_ROLLBACK')
 before_gen=int(selfp['capabilities']['capability_generation'])
 def mutate(nxt,nt):
  prev=nxt['other_models'].get(sid,{});rel=nxt['relationships'].get(sid,{})
  trust=min(0.95,float(prev.get('interaction_trust_score',0.5))+0.02)
  nxt['other_models'][sid]={'individual_id':sid,'lineage_id':pp['sender_lineage_id'],'branch_id':pp['sender_branch_id'],'identity_public_key':packet['public_key'],'interaction_trust_score':round(trust,4),'interaction_count':int(prev.get('interaction_count',0))+1,'public_capabilities':copy.deepcopy(pp['public_capabilities']),'public_observations':copy.deepcopy(pp['public_observations']),'last_public_message':pp['public_message'],'source_state_seq':pp['sender_state_seq'],'source_state_sha256':pp['source_state_sha256'],'first_seen_tick':int(prev.get('first_seen_tick',nt)),'last_seen_tick':nt,'last_packet_sha256':psha}
  seen=list(rel.get('seen_packet_sha256',[]));seen.append(psha);seen=seen[-128:]
  hist=list(rel.get('shared_history_sha256',[]));hist.append(psha);hist=hist[-128:]
  nxt['relationships'][sid]={'status':'known','interaction_trust_score':round(trust,4),'first_seen_tick':int(rel.get('first_seen_tick',nt)),'last_seen_tick':nt,'seen_packet_sha256':seen,'seen_ack_sha256':list(rel.get('seen_ack_sha256',[])),'shared_history_sha256':hist,'private_notes':list(rel.get('private_notes',[]))}
  if int(nxt['capabilities']['capability_generation'])!=before_gen:raise V841Error('SELF_CAPABILITY_CHANGED_BY_PEER_OBSERVATION')
 st=_social_tx(root,'social_receive',sid,psha,mutate,{'sender_state_seq':pp['sender_state_seq']})
 sp=st['payload'];ackp={'schema':SCHEMA_ACK,'ack_sender_individual_id':sp['identity']['individual_id'],'ack_sender_lineage_id':sp['identity']['lineage_id'],'ack_sender_branch_id':sp['identity']['branch_id'],'ack_sender_public_key':st['public_key'],'original_sender_individual_id':sid,'packet_sha256':psha,'receiver_state_seq':sp['continuity']['state_seq'],'status':'ACCEPTED'}
 sk=(_oroot(root)/r837.KEY).read_text().strip();return _signed(ackp,sk,st['public_key'])

def receive_ack(root,original_packet,ack):
 pp=_validate_packet(original_packet);ap=_validate_ack(ack);root=Path(root);cur=_load_org(root);selfp=cur['payload'];selfid=selfp['identity']['individual_id'];peer=ap['ack_sender_individual_id'];psha=_packet_sha(original_packet);asha=_packet_sha(ack)
 if pp['sender_individual_id']!=selfid or pp['recipient_individual_id']!=peer:raise V841Error('ACK_ORIGINAL_PACKET_NOT_OWN_SEND')
 if ap['original_sender_individual_id']!=selfid or ap['packet_sha256']!=psha:raise V841Error('ACK_PACKET_BINDING_INVALID')
 _pin_peer(selfp,peer,ack['public_key'],ap['ack_sender_lineage_id'],ap['ack_sender_branch_id']);rel=selfp['relationships'].get(peer,{})
 if asha in rel.get('seen_ack_sha256',[]):raise V841Error('ACK_REPLAY')
 def mutate(nxt,nt):
  prev=nxt['other_models'].get(peer,{})
  trust=min(0.95,float(prev.get('interaction_trust_score',0.5))+0.02)
  if not prev:
   nxt['other_models'][peer]={'individual_id':peer,'lineage_id':ap['ack_sender_lineage_id'],'branch_id':ap['ack_sender_branch_id'],'identity_public_key':ack['public_key'],'interaction_trust_score':round(trust,4),'interaction_count':1,'public_capabilities':[],'public_observations':[],'last_public_message':'','source_state_seq':ap['receiver_state_seq'],'source_state_sha256':None,'first_seen_tick':nt,'last_seen_tick':nt,'last_packet_sha256':None}
  else:
   prev['interaction_trust_score']=round(trust,4);prev['interaction_count']=int(prev.get('interaction_count',0))+1;prev['last_seen_tick']=nt;prev['source_state_seq']=max(int(prev.get('source_state_seq',0)),int(ap['receiver_state_seq']))
  rr=nxt['relationships'].get(peer,{});acks=list(rr.get('seen_ack_sha256',[]));acks.append(asha);hist=list(rr.get('shared_history_sha256',[]));hist.append(psha)
  nxt['relationships'][peer]={'status':'known','interaction_trust_score':round(trust,4),'first_seen_tick':int(rr.get('first_seen_tick',nt)),'last_seen_tick':nt,'seen_packet_sha256':list(rr.get('seen_packet_sha256',[])),'seen_ack_sha256':acks[-128:],'shared_history_sha256':hist[-128:],'private_notes':list(rr.get('private_notes',[]))}
 _social_tx(root,'social_ack',peer,psha,mutate,{'ack_sha256':asha});return True

def record_private_note(root,peer_id,note):
 root=Path(root);cur=_load_org(root);p=cur['payload']
 if peer_id==p['identity']['individual_id']:raise V841Error('SELF_PRIVATE_RELATION_NOTE_FORBIDDEN')
 if peer_id not in p['relationships']:raise V841Error('UNKNOWN_PEER_FOR_PRIVATE_NOTE')
 note=str(note)
 if len(note.encode())>4096:raise V841Error('PRIVATE_NOTE_TOO_LARGE')
 nh=sha256_bytes(note.encode())
 def mutate(nxt,nt):
  rel=nxt['relationships'][peer_id];notes=list(rel.get('private_notes',[]));notes.append({'created_tick':nt,'note':note,'note_sha256':nh});rel['private_notes']=notes[-32:]
 _social_tx(root,'social_private_note',peer_id,nh,mutate,{'note_sha256':nh});return nh

def peer_model(root,peer_id,*,include_private=False):
 env=_load_org(root);p=env['payload'];m=copy.deepcopy(p['other_models'].get(peer_id));r=copy.deepcopy(p['relationships'].get(peer_id))
 if not include_private and r:r.pop('private_notes',None)
 return {'model':m,'relationship':r}

def audit(root):
 root=Path(root);errors=[]
 try:recover_social(root)
 except Exception as e:errors.append(str(e))
 base=v840.audit(root)
 if not base.get('ok'):errors.append('V840_AUDIT_FAILED:'+','.join(base.get('errors',[])))
 try:env=_load_org(root)
 except Exception as e:return {'ok':False,'errors':errors+[str(e)]}
 p=env['payload'];sid=p['identity']['individual_id'];keys={}
 if sid in p['other_models'] or sid in p['relationships']:errors.append('SELF_PRESENT_AS_OTHER')
 for pid,m in p['other_models'].items():
  if m.get('individual_id')!=pid:errors.append('PEER_ID_KEY_MISMATCH:'+pid)
  k=m.get('identity_public_key')
  if k in keys and keys[k]!=pid:errors.append('PEER_KEY_REUSE:'+pid)
  keys[k]=pid
  if 'private_notes' in m:errors.append('PRIVATE_NOTE_IN_OTHER_MODEL:'+pid)
  rel=p['relationships'].get(pid)
  if rel and rel.get('interaction_trust_score')!=m.get('interaction_trust_score'):errors.append('TRUST_DIVERGENCE:'+pid)
  if rel and len(rel.get('seen_packet_sha256',[]))!=len(set(rel.get('seen_packet_sha256',[]))):errors.append('PACKET_HISTORY_DUPLICATE:'+pid)
  if rel and len(rel.get('seen_ack_sha256',[]))!=len(set(rel.get('seen_ack_sha256',[]))):errors.append('ACK_HISTORY_DUPLICATE:'+pid)
 return {'ok':not errors,'errors':errors,'individual_id':sid,'peer_count':len(p['other_models']),'relationship_count':len(p['relationships']),'runtime_tick':p['runtime']['tick'],'state_seq':p['continuity']['state_seq'],'capability_generation':p['capabilities']['capability_generation'],'policy_wrong':p['runtime']['policy_wrong'],'invariant_violations':p['runtime']['invariant_violations']}
