#!/usr/bin/env python3
import argparse,base64,json,secrets,sys,hashlib
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_v956.blind_gap import canon,validate_suite,SC,RS
p=argparse.ArgumentParser();sp=p.add_subparsers(dest='cmd',required=True)
k=sp.add_parser('keygen');k.add_argument('--out',type=Path,required=True)
c=sp.add_parser('commit');c.add_argument('--private-key',type=Path,required=True);c.add_argument('--suite',type=Path,required=True);c.add_argument('--commitment-out',type=Path,required=True);c.add_argument('--reveal-out',type=Path,required=True)
a=p.parse_args()
if a.cmd=='keygen':
 a.out.mkdir(parents=True,exist_ok=True);q=Ed25519PrivateKey.generate();(a.out/'blind_gap_authority.key').write_text(base64.b64encode(q.private_bytes_raw()).decode());(a.out/'blind_gap_authority.pub').write_text(base64.b64encode(q.public_key().public_bytes_raw()).decode());print(json.dumps({'ok':True,'public_key_file':str(a.out/'blind_gap_authority.pub')}))
else:
 suite=json.loads(a.suite.read_text());rows=validate_suite(suite);salt=secrets.token_hex(32);pre={'suite':suite,'salt':salt};priv=Ed25519PrivateKey.from_private_bytes(base64.b64decode(a.private_key.read_text().strip()));pub=base64.b64encode(priv.public_key().public_bytes_raw()).decode();pay={'schema':SC,'suite_id':suite['suite_id'],'case_count':len(rows),'commitment_sha256':hashlib.sha256(canon(pre)).hexdigest()};env={'payload':pay,'public_key':pub,'signature':base64.b64encode(priv.sign(canon(pay))).decode()};rev={'schema':RS,'suite':suite,'salt':salt};a.commitment_out.write_bytes(canon(env)+b'\n');a.reveal_out.write_bytes(canon(rev)+b'\n');print(json.dumps({'ok':True,'commitment':str(a.commitment_out),'reveal':str(a.reveal_out)}))
