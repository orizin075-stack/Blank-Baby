#!/usr/bin/env python3
import argparse,base64,json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def skload(p):
 raw=base64.b64decode(Path(p).read_text().strip(),validate=True)
 if len(raw)!=32:raise ValueError('PRIVATE_KEY_LENGTH')
 return Ed25519PrivateKey.from_private_bytes(raw)
def pub(sk):return base64.b64encode(sk.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode()
def main():
 a=argparse.ArgumentParser();a.add_argument('payload');a.add_argument('--private-key',required=True);a.add_argument('--out',required=True);x=a.parse_args()
 sk=skload(x.private_key);p=json.loads(Path(x.payload).read_text());env={'payload':p,'public_key':pub(sk),'signature':base64.b64encode(sk.sign(canon(p))).decode()}
 Path(x.out).write_text(json.dumps(env,sort_keys=True,separators=(',',':'))+'\n')
if __name__=='__main__':main()
