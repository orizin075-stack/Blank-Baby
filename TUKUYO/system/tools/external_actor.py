#!/usr/bin/env python3
"""Standalone example signing utility; actor private keys must be kept OUTSIDE releases/data.
Use separate people/hardware for genuinely independent third-party attestation.
"""
from pathlib import Path
import argparse,base64,json,os,sys
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tukuyo_v943.epistemic import canon,sign

def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True)
 g=sub.add_parser('generate');g.add_argument('--private-out',type=Path,required=True);g.add_argument('--public-out',type=Path,required=True)
 s=sub.add_parser('sign');s.add_argument('--private',type=Path,required=True);s.add_argument('--payload',type=Path,required=True);s.add_argument('--out',type=Path,required=True)
 a=p.parse_args()
 if a.cmd=='generate':
  if a.private_out.parent==Path(__file__).parent or a.private_out.resolve().is_relative_to(Path(__file__).resolve().parents[1]):raise ValueError('PRIVATE_KEY_MUST_BE_OUTSIDE_RELEASE')
  k=Ed25519PrivateKey.generate();priv=base64.b64encode(k.private_bytes(serialization.Encoding.Raw,serialization.PrivateFormat.Raw,serialization.NoEncryption()))
  pub=base64.b64encode(k.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw))
  a.private_out.parent.mkdir(parents=True,exist_ok=True);fd=os.open(a.private_out,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,'wb') as f:f.write(priv+b'\n')
  with a.public_out.open('xb') as f:f.write(pub+b'\n')
  print(json.dumps({'ok':True,'public':str(a.public_out)}));return
 k=Ed25519PrivateKey.from_private_bytes(base64.b64decode(a.private.read_text().strip(),validate=True))
 body=json.loads(a.payload.read_text());a.out.write_bytes(canon(sign(k,body))+b'\n');print(json.dumps({'ok':True,'signed':str(a.out)}))
if __name__=='__main__':main()
