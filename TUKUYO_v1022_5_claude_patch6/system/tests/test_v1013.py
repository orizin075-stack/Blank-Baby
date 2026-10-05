import json,os,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py';WIT=ROOT/'tools/realtime_witness.py'

def run(d,*a,ok=True):
 env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
 cmd=[sys.executable,'-B',str(CLI),'--data',str(d),*map(str,a)]
 p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,env=env,timeout=240)
 try:r=json.loads(p.stdout)
 except Exception:raise AssertionError((p.returncode,p.stdout,p.stderr))
 if ok and (p.returncode!=0 or not r.get('ok',False)):raise AssertionError((p.returncode,r,p.stderr))
 if not ok and p.returncode==0 and r.get('ok',True):raise AssertionError(('expected fail',r))
 return r

def wit(*a):
 p=subprocess.run([sys.executable,'-B',str(WIT),*map(str,a)],cwd=ROOT,text=True,capture_output=True,timeout=60)
 if p.returncode:raise AssertionError(p.stdout+p.stderr)
 return json.loads(p.stdout)

def test_v1013_fresh_process_restart_chain_and_whole_audit():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V1013-RESTART');run(d,'realtime-start','--target-seconds','60','--note','start')
  run(d,'realtime-tick','--note','fresh process 1');run(d,'realtime-tick','--note','fresh process 2')
  a=run(d,'realtime-audit');assert a['events']==3 and a['distinct_process_instances']>=3 and a['claim_boundary']['restart_continuity_observed']
  assert run(d,'whole-audit')['ok']

def test_v1013_external_integrity_anchor_detects_rollback():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';ext=Path(td)/'anchor.json';run(d,'init','--individual-id','V1013-ROLL');run(d,'realtime-start','--target-seconds','60');run(d,'realtime-tick');run(d,'realtime-anchor-export','--out',ext)
  # Roll the signed event ledger and local head/state back by one event. The external anchor must reject it.
  ep=d/'v1013/REALTIME_EVENTS.jsonl';lines=ep.read_text().splitlines();lines=lines[:-1];ep.write_text('\n'.join(lines)+'\n')
  env=json.loads(lines[-1]);head=env
  import hashlib
  def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
  h=hashlib.sha256(canon(env)).hexdigest();(d/'v1013/REALTIME_EVENT_HEAD.json').write_text(json.dumps({'schema':'tukuyo.v1013.realtime_head/1','run_id':env['payload']['run_id'],'seq':env['payload']['seq'],'event_sha256':h},sort_keys=True,separators=(',',':'))+'\n')
  st=json.loads((d/'v1013/REALTIME_RUN.json').read_text());st['last_event_seq']=env['payload']['seq'];st['last_event_sha256']=h;st['last_observed_utc_ns']=env['payload']['observed_utc_ns'];(d/'v1013/REALTIME_RUN.json').write_text(json.dumps(st,sort_keys=True,separators=(',',':'))+'\n')
  r=run(d,'realtime-audit','--anchor-file',ext,ok=False);assert 'EXTERNAL_ANCHOR_ROLLBACK_OR_FORK' in r['errors']

def test_v1013_external_witness_pair_is_required_for_formal_duration_gate():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';wdir=Path(td)/'w';sreq=Path(td)/'start_req.json';ereq=Path(td)/'end_req.json';sr=Path(td)/'start_receipt.json';er=Path(td)/'end_receipt.json'
  run(d,'init','--individual-id','V1013-WIT');run(d,'realtime-start','--target-seconds','1');run(d,'realtime-witness-request','--out',sreq)
  wit('keygen','--out-dir',wdir);wit('sign',sreq,'--private-key',wdir/'realtime_witness.key','--out',sr)
  # Local elapsed alone must not satisfy the formal gate.
  time.sleep(1.05);run(d,'realtime-tick');x=run(d,'realtime-audit','--require-complete',ok=False);assert 'FORMAL_DURATION_GATE_INCOMPLETE' in x['errors']
  run(d,'realtime-witness-request','--out',ereq);wit('sign',ereq,'--private-key',wdir/'realtime_witness.key','--out',er)
  a=run(d,'realtime-audit','--start-witness',sr,'--end-witness',er,'--witness-trust-file',wdir/'realtime_witness.pub','--require-complete')
  assert a['externally_anchored_complete'] and a['external_witness_elapsed_seconds']>=1
