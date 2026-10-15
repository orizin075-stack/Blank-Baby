import argparse,json,base64
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_v954.provenance import canon,load,sign,sha_obj,pub
p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True)
k=sub.add_parser('keygen');k.add_argument('--out',type=Path,required=True)
s=sub.add_parser('sign');s.add_argument('--private-key',type=Path,required=True);s.add_argument('--request',type=Path,required=True);s.add_argument('--out',type=Path,required=True)
a=p.parse_args()
if a.cmd=='keygen':
 a.out.mkdir(parents=True,exist_ok=True);priv=Ed25519PrivateKey.generate();(a.out/'capability_authority.key').write_text(base64.b64encode(priv.private_bytes_raw()).decode());(a.out/'capability_authority.pub').write_text(pub(priv));print(json.dumps({'ok':True,'public_key_file':str(a.out/'capability_authority.pub')}))
else:
 priv=Ed25519PrivateKey.from_private_bytes(base64.b64decode(a.private_key.read_text().strip()));req=load(a.request);pl={'schema':'tukuyo.v954.capability_authority_receipt/1','request_sha256':sha_obj(req),'individual_id':req['individual_id'],'surface':req['surface'],'operator':req['operator'],'promotion_sha256':req['promotion_sha256']};env=sign(priv,pl);a.out.write_bytes(canon(env)+b'\n');print(json.dumps({'ok':True,'receipt':str(a.out)}))
