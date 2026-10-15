#!/usr/bin/env python3
from pathlib import Path
import argparse,base64,json,sys
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_v958.promotion import canon,sha_obj,verify_evaluator_receipt

def main():
 p=argparse.ArgumentParser();p.add_argument('proposal',type=Path);p.add_argument('evaluator_receipt',type=Path);p.add_argument('--evaluator-pubkey',type=Path,required=True);p.add_argument('--private-key',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 prop=json.loads(a.proposal.read_text());er=json.loads(a.evaluator_receipt.read_text());ep=verify_evaluator_receipt(er,prop,a.evaluator_pubkey)
 pay={'schema':'tukuyo.v958.promotion_receipt/1','candidate_sha256':prop['candidate_sha256'],'evaluator_receipt_sha256':sha_obj(er),'decision':'PROMOTE_BOUNDED','scope':'V958_BOUNDED_SYNTHETIC_TWO_DOMAIN','domain_ids':[d['domain_id'] for d in ep['domains']]}
 priv=Ed25519PrivateKey.from_private_bytes(base64.b64decode(a.private_key.read_text().strip()));pub=base64.b64encode(priv.public_key().public_bytes_raw()).decode();env={'payload':pay,'public_key':pub,'signature':base64.b64encode(priv.sign(canon(pay))).decode()};a.out.write_bytes(canon(env)+b'\n');print(json.dumps(pay,indent=2))
if __name__=='__main__':main()
