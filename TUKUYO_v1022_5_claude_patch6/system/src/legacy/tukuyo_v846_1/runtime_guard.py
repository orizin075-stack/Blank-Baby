from __future__ import annotations
from pathlib import Path
import json,time
from .deps import activate
activate()
import tukuyo_v846.evolution as e846  # activate transitive chain
import tukuyo_v837.runtime as r837

_INSTALLED=False
_ORIG={}
QUAR='quarantine/runtime_audit_quarantine.json'

def _quarantine(root,reason,detail=None):
 root=Path(root);q=root/QUAR;q.parent.mkdir(parents=True,exist_ok=True)
 payload={'schema':'tukuyo.v846_1.runtime_quarantine/1','reason':str(reason),'detail':str(detail or ''),'unix_ns':time.time_ns(),'organism_auditable':False}
 try:
  sk=(root/r837.KEY).read_text().strip();pk=(root/r837.PUB).read_text().strip();env=r837._signed(payload,sk,pk);r837.atomic_write(q,r837.canonical(env))
 except Exception:
  # A corrupt identity/state may prevent signing. This local marker is still fail-closed,
  # but is not evidence-eligible by itself.
  q.write_text(json.dumps({'payload':payload,'signature_status':'UNAVAILABLE'},sort_keys=True))
 return q

def _guarded_load_json(p):
 try:return json.loads(Path(p).read_text())
 except (json.JSONDecodeError,UnicodeDecodeError) as ex:raise r837.RuntimeError837('LEDGER_UNREADABLE') from ex

def verify_event_head(root):
 root=Path(root);st=r837.load_verified_state(root);p=st['payload'];seq=int(p['continuity']['state_seq'])
 if seq==0:
  if p['continuity']['event_head_sha256']!=r837.ZERO:raise r837.RuntimeError837('EVENT_HEAD_ZERO_MISMATCH')
  return {'ok':True,'state_seq':0,'event_head_sha256':r837.ZERO}
 ep=r837._event_path(root,seq)
 if not ep.exists():raise r837.RuntimeError837('EVENT_HEAD_MISSING')
 env=r837._load_json(ep)
 if not r837._verify(env):raise r837.RuntimeError837('EVENT_HEAD_SIGNATURE_INVALID')
 q=env['payload']
 if int(q.get('state_seq',-1))!=seq:raise r837.RuntimeError837('EVENT_HEAD_SEQ_MISMATCH')
 if q.get('individual_id')!=p['identity']['individual_id'] or q.get('branch_id')!=p['identity']['branch_id']:raise r837.RuntimeError837('EVENT_HEAD_IDENTITY_MISMATCH')
 h=r837.sha256_bytes(r837.canonical(env))
 if h!=p['continuity']['event_head_sha256']:raise r837.RuntimeError837('EVENT_HEAD_HASH_MISMATCH')
 return {'ok':True,'state_seq':seq,'event_head_sha256':h}

def verify_commit_head(root):
 root=Path(root);st=r837.load_verified_state(root);p=st['payload'];seq=int(p['continuity']['state_seq'])
 head=r837._read_head(root);commit=r837._tail_commit(root)
 if int(head['payload']['state_seq'])!=seq:raise r837.RuntimeError837('COMMIT_HEAD_SEQ_MISMATCH')
 if head['payload']['state_sha256']!=r837.sha256_bytes(r837.canonical(st)):raise r837.RuntimeError837('COMMIT_HEAD_STATE_HASH_MISMATCH')
 if int(commit['payload']['state_seq'])!=seq:raise r837.RuntimeError837('COMMIT_TAIL_SEQ_MISMATCH')
 if commit['payload']['state_sha256']!=r837.sha256_bytes(r837.canonical(st)):raise r837.RuntimeError837('COMMIT_TAIL_STATE_HASH_MISMATCH')
 return {'ok':True,'state_seq':seq,'commit_sha256':head['payload']['commit_sha256']}

def audit_checked(root):
 root=Path(root)
 if (root/QUAR).exists():return {'ok':False,'organism_auditable':False,'quarantined':True,'errors':['ORGANISM_QUARANTINED']}
 try:
  verify_event_head(root);verify_commit_head(root)
  a=_ORIG['audit'](root)
  a=dict(a);a['organism_auditable']=bool(a.get('ok'));a['quarantined']=False
  return a
 except Exception as ex:
  _quarantine(root,'AUDIT_FAILED',ex)
  return {'ok':False,'organism_auditable':False,'quarantined':True,'errors':[str(ex)]}

def recover_checked(root):
 root=Path(root)
 if (root/QUAR).exists():raise r837.RuntimeError837('ORGANISM_QUARANTINED')
 try:
  recovered=_ORIG['recover'](root)
  verify_event_head(root);verify_commit_head(root)
  a=_ORIG['audit'](root)
  if not a.get('ok'):raise r837.RuntimeError837('RECOVERY_AUDIT_FAILED:'+','.join(a.get('errors',[])))
  return {'ok':True,'recovered':bool(recovered),'organism_auditable':True,'quarantined':False}
 except Exception as ex:
  _quarantine(root,'RECOVERY_FAILED',ex)
  if isinstance(ex,r837.RuntimeError837):raise
  raise r837.RuntimeError837('LEDGER_UNREADABLE') from ex

def tick_once_checked(root):
 root=Path(root)
 if (root/QUAR).exists():raise r837.RuntimeError837('ORGANISM_QUARANTINED')
 try:
  verify_event_head(root);verify_commit_head(root)
  return _ORIG['tick_once'](root)
 except Exception as ex:
  _quarantine(root,'TICK_PRECHECK_OR_EXECUTION_FAILED',ex)
  if isinstance(ex,r837.RuntimeError837):raise
  raise r837.RuntimeError837('LEDGER_UNREADABLE') from ex

def install():
 global _INSTALLED
 if _INSTALLED:return
 _ORIG.update(load_json=r837._load_json,recover=r837.recover,tick_once=r837.tick_once,audit=r837.audit)
 r837._load_json=_guarded_load_json
 # preserve legacy return value for parent callers while enforcing post-recovery audit
 def compat_recover(root):return recover_checked(root)['recovered']
 r837.recover=compat_recover
 r837.tick_once=tick_once_checked
 r837.audit=audit_checked
 _INSTALLED=True

install()
