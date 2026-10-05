#!/usr/bin/env python3
from __future__ import annotations
import argparse,base64,json,time
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def main():
 p=argparse.ArgumentParser();s=p.add_subparsers(dest='cmd',required=True)
 k=s.add_parser('keygen');k.add_argument('--out-dir',type=Path,required=True)
 q=s.add_parser('sign');q.add_argument('request',type=Path);q.add_argument('--private-key',type=Path,required=True);q.add_argument('--out',type=Path,required=True)
 a=p.parse_args()
 if a.cmd=='keygen':
  a.out_dir.mkdir(parents=True,exist_ok=True);sk=Ed25519PrivateKey.generate();pub=base64.b64encode(sk.public_key().public_bytes_raw()).decode();(a.out_dir/'realtime_witness.key').write_text(base64.b64encode(sk.private_bytes_raw()).decode());(a.out_dir/'realtime_witness.pub').write_text(pub);print(json.dumps({'ok':True,'public_key_file':str(a.out_dir/'realtime_witness.pub')}));return
 req=json.loads(a.request.read_text(encoding='utf-8'));sk=Ed25519PrivateKey.from_private_bytes(base64.b64decode(a.private_key.read_text().strip(),validate=True));pub=base64.b64encode(sk.public_key().public_bytes_raw()).decode();payload={'schema':'tukuyo.v1013.witness_payload/1','run_id':req['run_id'],'identity':req['identity'],'seq':req['seq'],'head_sha256':req['head_sha256'],'request_sha256':req['request_sha256'],'witnessed_utc_ns':time.time_ns()};env={'schema':'tukuyo.v1013.witness_receipt/1','payload':payload,'public_key':pub,'signature':base64.b64encode(sk.sign(canon(payload))).decode()};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_bytes(canon(env)+b'\n');print(json.dumps({'ok':True,'receipt':str(a.out),'witnessed_utc_ns':payload['witnessed_utc_ns']}))
if __name__=='__main__':main()
