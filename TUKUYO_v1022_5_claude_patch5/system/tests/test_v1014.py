import json,os,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py'

def run(d,*a,ok=True):
 env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
 p=subprocess.run([sys.executable,'-B',str(CLI),'--data',str(d),*map(str,a)],cwd=ROOT,text=True,capture_output=True,env=env,timeout=240)
 try:r=json.loads(p.stdout)
 except Exception:raise AssertionError((p.returncode,p.stdout,p.stderr))
 if ok and (p.returncode!=0 or not r.get('ok',False)):raise AssertionError((p.returncode,r,p.stderr))
 if not ok and p.returncode==0 and r.get('ok',True):raise AssertionError(('expected fail',r))
 return r

def test_v1014_corruption_dryrun_then_restore():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V1014-REC');run(d,'realtime-start','--target-seconds','60');run(d,'realtime-tick')
  cp=run(d,'recovery-checkpoint','--note','before corruption');cpp=Path(cp['path'])
  # Corrupt a signed whole-state file. Restore must still be callable even though live prechecks now fail.
  target=d/'v977/WHOLE_STATE.json';target.write_text('{"corrupt":true}\n')
  dry=run(d,'recovery-restore',cpp,'--dry-run');assert dry['dry_run'] and dry['checkpoint_id']==cp['checkpoint_id']
  rr=run(d,'recovery-restore',cpp);assert rr['restored']
  assert run(d,'whole-audit')['ok'] and run(d,'realtime-audit')['ok']

def test_v1014_external_anchor_blocks_old_checkpoint_rollback():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';anchor=Path(td)/'external_anchor.json';run(d,'init','--individual-id','V1014-ROLL');run(d,'realtime-start','--target-seconds','60');run(d,'realtime-tick')
  cp=run(d,'recovery-checkpoint');cpp=Path(cp['path'])
  run(d,'realtime-tick','--note','newer state');run(d,'realtime-anchor-export','--out',anchor)
  r=run(d,'recovery-restore',cpp,'--anchor-file',anchor,'--dry-run',ok=False)
  assert 'EXTERNAL_ANCHOR_ROLLBACK_OR_FORK' in r.get('errors',[]) or 'EXTERNAL_ANCHOR_BINDING' in r.get('errors',[])

def test_v1014_tampered_checkpoint_rejected():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V1014-TAMPER');run(d,'realtime-start','--target-seconds','60')
  cp=run(d,'recovery-checkpoint');src=Path(cp['path']);bad=Path(td)/'bad.json';o=json.loads(src.read_text());o['payload']['note']='tampered';bad.write_text(json.dumps(o))
  r=run(d,'recovery-audit',bad,ok=False);assert any(x.startswith('CHECKPOINT_SIGNATURE') for x in r['errors'])
