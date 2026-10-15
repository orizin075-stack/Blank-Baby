#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,subprocess,sys,time
from pathlib import Path

def _call(base,args,allow_fail=False):
    cp=subprocess.run(base+list(map(str,args)),capture_output=True,text=True)
    try:r=json.loads(cp.stdout) if cp.stdout.strip() else {'ok':False,'errors':['NO_OUTPUT']}
    except Exception:r={'ok':False,'raw':cp.stdout,'stderr':cp.stderr}
    if cp.returncode and not allow_fail:
        print(json.dumps(r,ensure_ascii=False,sort_keys=True),flush=True);print(cp.stderr.strip(),file=sys.stderr);raise SystemExit(cp.returncode)
    return r,cp.returncode

def main():
    p=argparse.ArgumentParser(description='Fresh-process endurance runner. Holds only witness PUBLIC trust and automatically consumes externally produced receipts.')
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--data',type=Path,required=True);p.add_argument('--runtime-trust-file',type=Path)
    p.add_argument('--witness-trust-file',type=Path,required=True);p.add_argument('--witness-receipt-dir',type=Path,required=True)
    p.add_argument('--poll-seconds',type=float,default=1.0);p.add_argument('--max-seconds',type=float);p.add_argument('--once',action='store_true')
    a=p.parse_args();start=time.monotonic();a.witness_receipt_dir.mkdir(parents=True,exist_ok=True)
    base=[sys.executable,str(a.root/'run_tukuyo.py'),'--data',str(a.data)]
    if a.runtime_trust_file:base+=['--runtime-trust-file',str(a.runtime_trust_file)]
    while True:
        status,_=_call(base,['endurance-exec-status','--witness-trust-file',a.witness_trust_file],allow_fail=True)
        st=status.get('state') or {};pend=st.get('pending_request') or {}
        if pend.get('request_sha256'):
            rec=a.witness_receipt_dir/f"{pend['request_sha256']}.receipt.json"
            if rec.is_file():
                acc,rc=_call(base,['endurance-exec-accept-witness',rec,'--witness-trust-file',a.witness_trust_file],allow_fail=True)
                print(json.dumps({'action':'accept_witness','result':acc},ensure_ascii=False,sort_keys=True),flush=True)
                if acc.get('phase') in ('PROTOCOL_COMPLETE','FAILED'):return
        pump,rc=_call(base,['endurance-exec-pump'],allow_fail=True)
        print(json.dumps({'action':'pump','result':pump},ensure_ascii=False,sort_keys=True),flush=True)
        if pump.get('phase') in ('PROTOCOL_COMPLETE','FAILED'):return
        if a.once:return
        if a.max_seconds is not None and time.monotonic()-start>=a.max_seconds:return
        time.sleep(max(.05,a.poll_seconds))
if __name__=='__main__':main()
