import json,os,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py'

def run(d,*a,ok=True,crash=None):
 env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
 if crash:env['TUKUYO_CRASH_POINT']=crash
 else:env.pop('TUKUYO_CRASH_POINT',None)
 p=subprocess.run([sys.executable,'-B',str(CLI),'--data',str(d),*map(str,a)],cwd=ROOT,text=True,capture_output=True,env=env,timeout=240)
 if crash:
  assert p.returncode!=0,(p.returncode,p.stdout,p.stderr)
  return p
 try:r=json.loads(p.stdout)
 except Exception:raise AssertionError((p.returncode,p.stdout,p.stderr))
 if ok and (p.returncode!=0 or not r.get('ok',False)):raise AssertionError((p.returncode,r,p.stderr))
 if not ok and p.returncode==0 and r.get('ok',True):raise AssertionError(('expected failure',r))
 return r

def test_v1014_2_atomic_target_survives_mid_temp_kill():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10142-ATOMIC')
  a=run(d,'verified-query','3たす4は？');assert a['answer']=='7'
  before=json.loads((d/'v1005/LAST_VERIFIED_REASONING.json').read_text())['result_sha256']
  run(d,'verified-query','5たす6は？',crash='verified_result:mid_tmp')
  # Startup repair sees the pending mutation, resynchronizes Whole State and removes orphan tmp.
  assert run(d,'whole-audit')['ok']
  after=json.loads((d/'v1005/LAST_VERIFIED_REASONING.json').read_text())['result_sha256']
  assert before==after
  assert not (d/'v1014/private/PENDING_MUTATION.json').exists()
  assert not any('.tukuyo-atomic-' in p.name for p in d.rglob('*') if p.is_file())
  b=run(d,'verified-query','5たす6は？');assert b['answer']=='11' and not b['uncertain']
  assert run(d,'whole-audit')['ok']

def test_v1014_2_checkpoint_pointer_recovers_after_kill():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10142-CP');run(d,'realtime-start','--target-seconds','60');run(d,'realtime-tick')
  run(d,'recovery-checkpoint','--note','crash-after-checkpoint',crash='checkpoint:after_checkpoint')
  cps=list((d/'v1014/recovery_checkpoints').glob('rc-*.json'));assert len(cps)==1
  assert (d/'v1014/private/CHECKPOINT_TXN.json').exists()
  st=run(d,'recovery-status');assert st['count']==1 and st['checkpoints'][0]['ok']
  latest=json.loads((d/'v1014/LATEST_RECOVERY_CHECKPOINT.json').read_text())
  assert latest['path']==cps[0].name
  assert not (d/'v1014/private/CHECKPOINT_TXN.json').exists()

def test_v1014_2_restore_commit_resumes_after_kill():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10142-RESTORE');run(d,'realtime-start','--target-seconds','60');run(d,'realtime-tick')
  cp=run(d,'recovery-checkpoint','--note','stable-before-change');cpp=Path(cp['path'])
  q=run(d,'verified-query','8たす9は？');assert q['answer']=='17'
  assert (d/'v1005/LAST_VERIFIED_REASONING.json').exists()
  run(d,'recovery-restore',cpp,crash='restore:mid_commit')
  from tukuyo_v1014.recovery import _swap_marker
  assert (d/'v1014/private/RESTORE_TXN.json').exists() or _swap_marker(d).is_file()
  # Any normal next command must finish the idempotent restore before dispatch.
  assert run(d,'whole-audit')['ok']
  assert run(d,'realtime-audit')['ok']
  assert not (d/'v1014/private/RESTORE_TXN.json').exists()
  assert not _swap_marker(d).exists()
  rec=json.loads((d/'v1014/LAST_RECOVERY_RECEIPT.json').read_text());assert rec['atomic_recovery'] is True
  # The post-checkpoint verified answer was not part of the checkpoint snapshot.
  assert not (d/'v1005/LAST_VERIFIED_REASONING.json').exists()

def test_v1014_2_realtime_event_finishes_after_kill():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10142-RT');run(d,'realtime-start','--target-seconds','60')
  run(d,'realtime-tick','--note','kill-after-event',crash='realtime:after_event')
  assert (d/'v1013/private/REALTIME_PENDING.json').exists()
  a=run(d,'realtime-audit');assert a['ok'] and a['events']==2
  assert run(d,'whole-audit')['ok']
  assert not (d/'v1013/private/REALTIME_PENDING.json').exists()
  b=run(d,'realtime-tick','--note','fresh-process');assert b['ok']
  c=run(d,'realtime-audit');assert c['ok'] and c['events']==3 and c['distinct_process_instances']>=2
