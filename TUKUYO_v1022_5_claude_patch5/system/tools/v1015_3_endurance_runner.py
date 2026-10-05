#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,subprocess,sys,time,uuid
from pathlib import Path

def _call(base,args,session,allow_fail=False):
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','TUKUYO_ENDURANCE_RUNNER_SESSION':session}
    cp=subprocess.run(base+list(map(str,args)),capture_output=True,text=True,env=env)
    try:r=json.loads(cp.stdout) if cp.stdout.strip() else {'ok':False,'errors':['NO_OUTPUT']}
    except Exception:r={'ok':False,'raw':cp.stdout,'stderr':cp.stderr}
    if cp.returncode and not allow_fail:
        print(json.dumps(r,ensure_ascii=False,sort_keys=True),flush=True);print(cp.stderr.strip(),file=sys.stderr);raise SystemExit(cp.returncode)
    return r,cp.returncode

def main():
    p=argparse.ArgumentParser(description='v1015.3 resumable endurance runner. A new runner process creates a new externally visible runner_session_id.')
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--data',type=Path,required=True);p.add_argument('--runtime-trust-file',type=Path)
    p.add_argument('--witness-trust-file',type=Path,required=True);p.add_argument('--witness-receipt-dir',type=Path,required=True)
    p.add_argument('--poll-seconds',type=float,default=1.0);p.add_argument('--max-seconds',type=float);p.add_argument('--once',action='store_true');p.add_argument('--session-id')
    a=p.parse_args();start=time.monotonic();a.witness_receipt_dir.mkdir(parents=True,exist_ok=True);session=a.session_id or ('runner-'+uuid.uuid4().hex)
    base=[sys.executable,'-B',str(a.root/'run_tukuyo.py'),'--data',str(a.data)]
    if a.runtime_trust_file:base+=['--runtime-trust-file',str(a.runtime_trust_file)]
    rr,_=_call(base,['endurance-exec-resume','--witness-trust-file',a.witness_trust_file,'--note','runner startup'],session,allow_fail=True)
    print(json.dumps({'action':'resume','runner_session_id':session,'result':rr},ensure_ascii=False,sort_keys=True),flush=True)
    if rr.get('terminal_state')=='FAILED':return
    while True:
        status,_=_call(base,['endurance-exec-status','--witness-trust-file',a.witness_trust_file],session,allow_fail=True)
        st=status.get('state') or {};pend=((st.get('base_state') or {}) if 'base_state' in st else st).get('pending_request') or {}
        # v1015.3 status nests resume state; base pending request is available through base audit only, so fall back to direct v1015.2 state on disk.
        if not pend:
            try: pend=json.loads((a.data/'v1015_2'/'EXECUTION_STATE.json').read_text(encoding='utf-8')).get('pending_request') or {}
            except Exception: pend={}
        if pend.get('request_sha256'):
            rec=a.witness_receipt_dir/f"{pend['request_sha256']}.receipt.json"
            if rec.is_file():
                acc,rc=_call(base,['endurance-exec-accept-witness',rec,'--witness-trust-file',a.witness_trust_file],session,allow_fail=True)
                print(json.dumps({'action':'accept_witness','runner_session_id':session,'result':acc},ensure_ascii=False,sort_keys=True),flush=True)
                if acc.get('phase') in ('PROTOCOL_COMPLETE','FAILED') or acc.get('terminal_state') in ('FAILED','SUCCEEDED'):return
        pump,rc=_call(base,['endurance-exec-pump'],session,allow_fail=True)
        print(json.dumps({'action':'pump','runner_session_id':session,'result':pump},ensure_ascii=False,sort_keys=True),flush=True)
        if pump.get('phase') in ('PROTOCOL_COMPLETE','FAILED') or pump.get('terminal_state') in ('FAILED','SUCCEEDED'):return
        if a.once:return
        if a.max_seconds is not None and time.monotonic()-start>=a.max_seconds:return
        time.sleep(max(.05,a.poll_seconds))
if __name__=='__main__':main()
