#!/usr/bin/env python3
"""External challenge authority for TUKUYO v1015.5. Imports no TUKUYO modules."""
import argparse,base64,hashlib,json,secrets,time
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey

def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha_obj(x):return hashlib.sha256(canon(x)).hexdigest()
def keygen(priv,pub):
    sk=Ed25519PrivateKey.generate();Path(priv).write_text(base64.b64encode(sk.private_bytes_raw()).decode());Path(pub).write_text(base64.b64encode(sk.public_key().public_bytes_raw()).decode())
def load_sk(path):return Ed25519PrivateKey.from_private_bytes(base64.b64decode(Path(path).read_text().strip(),validate=True))
def issue(priv,out,profile,manifest_sha,ttl,subject=''):
    sk=load_sk(priv);now=time.time_ns();p={'schema':'tukuyo.v1015_5.challenge_payload/1','nonce':secrets.token_hex(32),'issued_utc_ns':now,'expires_utc_ns':now+int(ttl*1e9),'profile':profile,'release_manifest_sha256':manifest_sha,'subject':subject}
    p['challenge_id']=sha_obj(p);pub=base64.b64encode(sk.public_key().public_bytes_raw()).decode();env={'schema':'tukuyo.v1015_5.challenge/1','payload':p,'public_key':pub,'signature':base64.b64encode(sk.sign(canon(p))).decode()};Path(out).write_bytes(canon(env)+b'\n');return env

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True)
    k=sp.add_parser('keygen');k.add_argument('--private-key',required=True);k.add_argument('--public-key',required=True)
    i=sp.add_parser('issue');i.add_argument('--private-key',required=True);i.add_argument('--out',required=True);i.add_argument('--profile',choices=['24h','72h','7d'],required=True);i.add_argument('--release-manifest-sha256',required=True);i.add_argument('--ttl-seconds',type=int,default=3600);i.add_argument('--subject',default='')
    a=ap.parse_args()
    if a.cmd=='keygen':keygen(a.private_key,a.public_key);print(json.dumps({'ok':True,'private_key':a.private_key,'public_key':a.public_key}));return
    e=issue(a.private_key,a.out,a.profile,a.release_manifest_sha256,a.ttl_seconds,a.subject);print(json.dumps({'ok':True,'out':a.out,'challenge_id':e['payload']['challenge_id']},sort_keys=True))
if __name__=='__main__':main()
