import json,os,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py';WIT=ROOT/'tools/realtime_witness.py'

def run(d,*a,ok=True,crash=None):
 env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
 if crash:env['TUKUYO_CRASH_POINT']=crash
 else:env.pop('TUKUYO_CRASH_POINT',None)
 p=subprocess.run([sys.executable,'-B',str(CLI),'--data',str(d),*map(str,a)],cwd=ROOT,text=True,capture_output=True,env=env,timeout=240)
 if crash:
  assert p.returncode!=0,(p.returncode,p.stdout,p.stderr);return p
 try:r=json.loads(p.stdout)
 except Exception:raise AssertionError((p.returncode,p.stdout,p.stderr))
 if ok and (p.returncode!=0 or not r.get('ok',False)):raise AssertionError((p.returncode,r,p.stderr))
 if not ok and p.returncode==0 and r.get('ok',True):raise AssertionError(('expected fail',r))
 return r

def wit(*a):
 p=subprocess.run([sys.executable,'-B',str(WIT),*map(str,a)],cwd=ROOT,text=True,capture_output=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},timeout=60)
 if p.returncode:raise AssertionError(p.stdout+p.stderr)
 return json.loads(p.stdout)

def test_v1014_3_short_external_witness_gate_and_evidence():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';w=Path(td)/'w';sr=Path(td)/'sr.json';er=Path(td)/'er.json';endreq=Path(td)/'endreq.json';bundle=Path(td)/'bundle.json'
  run(d,'init','--individual-id','V10143-WIT')
  s=run(d,'continuity-campaign-start','--target-seconds','1','--tick-seconds','1','--checkpoint-seconds','1','--note','short-gate')
  wit('keygen','--out-dir',w);wit('sign',Path(s['start_witness_request']),'--private-key',w/'realtime_witness.key','--out',sr)
  time.sleep(1.05)
  x=run(d,'continuity-campaign-step','--force-checkpoint','--note','fresh-process-step');assert x['distinct_process_instances']>=2 and x['checkpoint_created']
  e=run(d,'continuity-campaign-end-request','--out',endreq);wit('sign',endreq,'--private-key',w/'realtime_witness.key','--out',er)
  a=run(d,'continuity-campaign-audit','--start-witness',sr,'--end-witness',er,'--witness-trust-file',w/'realtime_witness.pub','--require-complete')
  assert a['claim_boundary']['formal_duration_complete'] and not a['claim_boundary']['24h_completed']
  b=run(d,'continuity-campaign-evidence','--out',bundle,'--start-witness',sr,'--end-witness',er,'--witness-trust-file',w/'realtime_witness.pub','--require-complete')
  assert b['ok'] and bundle.is_file();obj=json.loads(bundle.read_text());assert obj['audit']['ok'] and obj['bundle_sha256']

def test_v1014_3_restart_checkpoint_and_resource_sampling():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10143-RUN')
  run(d,'continuity-campaign-start','--target-seconds','60','--checkpoint-seconds','9999')
  for i in range(3):run(d,'continuity-campaign-step','--note',f'step-{i}')
  a=run(d,'continuity-campaign-status');assert a['ok'] and a['steps']==3 and a['realtime']['distinct_process_instances']>=4
  assert a['resource_summary']['samples']>=4 and a['resource_summary']['rss_peak_bytes']
  assert a['checkpoints']==1 and a['recovery_checkpoint_count']==1

def test_v1014_3_captures_startup_crash_recovery_actions():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10143-CRASH');run(d,'continuity-campaign-start','--target-seconds','60')
  run(d,'realtime-tick','--note','campaign injected crash',crash='realtime:after_event')
  x=run(d,'continuity-campaign-step','--note','recover-after-crash')
  assert any('REALTIME_PENDING_COMPLETED' in a for a in x['startup_recovery_actions'])
  a=run(d,'continuity-campaign-status');assert a['ok'] and a['crash_recovery_observations']>=1 and a['whole_audit_ok']
