#!/usr/bin/env python3
from pathlib import Path
import argparse,base64,hashlib,json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_v957.novel_primitive import eval_proposal
from tukuyo_v958.promotion import canon,sha_obj,adapt_domain_b,verify_proposal

def main():
 p=argparse.ArgumentParser();p.add_argument('proposal',type=Path);p.add_argument('domain_a',type=Path);p.add_argument('domain_b',type=Path);p.add_argument('--private-key',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 prop=json.loads(a.proposal.read_text()); verify_proposal(prop)
 rawA=json.loads(a.domain_a.read_text()); rawB=json.loads(a.domain_b.read_text())
 if rawA.get('schema')!='tukuyo.v958.numeric_holdout/1' or rawA.get('generator_id')!='numeric_holdout_v958': raise SystemExit('BAD_DOMAIN_A')
 if rawB.get('schema')!='tukuyo.v958.state_transition_suite/1' or rawB.get('generator_id')!='state_machine_v958': raise SystemExit('BAD_DOMAIN_B')
 domains=[]
 for domain_id,raw,adapter,schema in [('numeric_hidden',rawA,lambda x:x,'tukuyo.v958.numeric_case/1'),('state_transition',rawB,adapt_domain_b,'tukuyo.v958.state_transition/1')]:
  src=raw['records']; rows=[adapter(x) for x in src]; rec=[]
  for r in rows:
   try: pred=eval_proposal(prop,r['a'],r['b']); invalid=False
   except Exception as e: pred=None;invalid=True
   rec.append({'input':{'a':r['a'],'b':r['b']},'expected':r['expected'],'prediction':pred,'correct':(not invalid and pred==r['expected']),'invalid':invalid})
  correct=sum(x['correct'] for x in rec);invalid=sum(x['invalid'] for x in rec)
  domains.append({'domain_id':domain_id,'source_schema':schema,'generator_id':raw['generator_id'],'source_sha256':hashlib.sha256(a.domain_a.read_bytes() if domain_id=='numeric_hidden' else a.domain_b.read_bytes()).hexdigest(),'rows_sha256':sha_obj(rows),'rows':len(rows),'correct':correct,'wrong':len(rows)-correct-invalid,'invalid':invalid,'row_evidence_sha256':sha_obj(rec)})
 pay={'schema':'tukuyo.v958.evaluator_receipt/1','candidate_sha256':prop['candidate_sha256'],'proposal_sha256':sha_obj(prop),'domains':domains,'evaluation_policy':'ZERO_WRONG_ZERO_INVALID_BOTH_DOMAINS'}
 priv=Ed25519PrivateKey.from_private_bytes(base64.b64decode(a.private_key.read_text().strip()));pub=base64.b64encode(priv.public_key().public_bytes_raw()).decode();env={'payload':pay,'public_key':pub,'signature':base64.b64encode(priv.sign(canon(pay))).decode()};a.out.write_bytes(canon(env)+b'\n')
 print(json.dumps(pay,indent=2))
if __name__=='__main__':main()
