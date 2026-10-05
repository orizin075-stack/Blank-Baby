#!/usr/bin/env python3
from __future__ import annotations
import argparse,base64,json,time,os
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def _inside(child,parent):
    try:Path(child).resolve().relative_to(Path(parent).resolve());return True
    except ValueError:return False

def sign_one(req_path,key_path,out_path,data_root=None):
    if data_root and _inside(key_path,data_root):raise ValueError('WITNESS_PRIVATE_KEY_MUST_BE_OUTSIDE_DATA_ROOT')
    req=json.loads(Path(req_path).read_text(encoding='utf-8'));sk=Ed25519PrivateKey.from_private_bytes(base64.b64decode(Path(key_path).read_text().strip(),validate=True));pub=base64.b64encode(sk.public_key().public_bytes_raw()).decode()
    payload={'schema':'tukuyo.v1013.witness_payload/1','run_id':req['run_id'],'identity':req['identity'],'seq':req['seq'],'head_sha256':req['head_sha256'],'request_sha256':req['request_sha256'],'witnessed_utc_ns':time.time_ns()}
    env={'schema':'tukuyo.v1013.witness_receipt/1','payload':payload,'public_key':pub,'signature':base64.b64encode(sk.sign(canon(payload))).decode()};out_path=Path(out_path);out_path.parent.mkdir(parents=True,exist_ok=True);tmp=out_path.with_name(out_path.name+'.tmp');tmp.write_bytes(canon(env)+b'\n');os.replace(tmp,out_path);return out_path

def main():
    p=argparse.ArgumentParser(description='External witness agent for TUKUYO v1015.2. Keep the private key outside the TUKUYO data root.')
    s=p.add_subparsers(dest='cmd',required=True)
    k=s.add_parser('keygen');k.add_argument('--out-dir',type=Path,required=True)
    q=s.add_parser('sign');q.add_argument('request',type=Path);q.add_argument('--private-key',type=Path,required=True);q.add_argument('--out',type=Path,required=True);q.add_argument('--data-root',type=Path)
    w=s.add_parser('watch');w.add_argument('--request-dir',type=Path,required=True);w.add_argument('--receipt-dir',type=Path,required=True);w.add_argument('--private-key',type=Path,required=True);w.add_argument('--data-root',type=Path,required=True);w.add_argument('--poll-seconds',type=float,default=1.0);w.add_argument('--once',action='store_true')
    a=p.parse_args()
    if a.cmd=='keygen':
        a.out_dir.mkdir(parents=True,exist_ok=True);sk=Ed25519PrivateKey.generate();(a.out_dir/'endurance_witness.key').write_text(base64.b64encode(sk.private_bytes_raw()).decode());(a.out_dir/'endurance_witness.pub').write_text(base64.b64encode(sk.public_key().public_bytes_raw()).decode());print(json.dumps({'ok':True,'private_key':str(a.out_dir/'endurance_witness.key'),'public_key':str(a.out_dir/'endurance_witness.pub')}));return
    if a.cmd=='sign':
        try:out=sign_one(a.request,a.private_key,a.out,a.data_root);print(json.dumps({'ok':True,'receipt':str(out)}));return
        except Exception as e:print(json.dumps({'ok':False,'error':type(e).__name__+':'+str(e)}));raise SystemExit(1)
    if _inside(a.private_key,a.data_root):raise SystemExit('WITNESS_PRIVATE_KEY_MUST_BE_OUTSIDE_DATA_ROOT')
    a.receipt_dir.mkdir(parents=True,exist_ok=True);seen=set()
    while True:
        did=0
        for req in sorted(a.request_dir.glob('*.json')):
            try:r=json.loads(req.read_text());key=r.get('request_sha256') or req.stem
            except Exception:continue
            out=a.receipt_dir/f'{key}.receipt.json'
            if key not in seen and not out.exists():sign_one(req,a.private_key,out,a.data_root);seen.add(key);did+=1
        if a.once:print(json.dumps({'ok':True,'signed':did}));return
        time.sleep(max(.05,a.poll_seconds))
if __name__=='__main__':main()
