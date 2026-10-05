"""v946 externally-authorized primitive promotion receipts."""
from __future__ import annotations
import base64,hashlib,json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
from tukuyo_v944.gap import OPS,shaobj
from tukuyo_v945.primitive import eval_proposal

def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def _key(p):
 s=Path(p).read_text().strip();b=base64.b64decode(s,validate=True)
 if len(b)!=32:raise ValueError('KEY_LENGTH')
 return s
def check(env,key):
 if set(env)!={'payload','public_key','signature'} or env['public_key']!=key:raise ValueError('TRUSTED_KEY_MISMATCH')
 try:Ed25519PublicKey.from_public_bytes(base64.b64decode(key,validate=True)).verify(base64.b64decode(env['signature'],validate=True),canon(env['payload']))
 except (InvalidSignature,ValueError,TypeError) as e:raise ValueError('SIGNATURE_INVALID') from e
 return env['payload']
def rows_hash(rows):return shaobj(rows)
def metrics(proposal,rows):
 cand_wrong=sum(eval_proposal(proposal,r['x'],r['y'])!=r['expected'] for r in rows)
 base={name:sum(f(r['x'],r['y'])!=r['expected'] for r in rows) for name,f in OPS.items()}
 return {'rows':len(rows),'candidate_wrong':cand_wrong,'best_known_wrong':min(base.values()),'known_wrong':base}
def expected_evaluation(proposal,hidden_rows,transfer_domains):
 if len(hidden_rows)<20:raise ValueError('HOLDOUT_TOO_SMALL')
 hm=metrics(proposal,hidden_rows);tm={name:metrics(proposal,rows) for name,rows in sorted(transfer_domains.items())}
 return {'schema':'tukuyo.v946.external_evaluation/1','candidate_sha256':proposal['candidate_sha256'],
         'hidden_rows_sha256':rows_hash(hidden_rows),'hidden':hm,
         'transfer_domains':{name:{'rows_sha256':rows_hash(transfer_domains[name]),'metrics':tm[name]} for name in sorted(tm)},
         'requirements':{'hidden_candidate_wrong_max':0,'hidden_strict_gain':True,'transfer_domain_count_min':2,'transfer_each_strict_gain':True}}
def verify_and_promote(proposal,hidden_rows,transfer_domains,evaluator_env,authority_env,evaluator_pub,authority_pub):
 if evaluator_pub==authority_pub:raise ValueError('ROLE_KEYS_NOT_INDEPENDENT')
 ep=check(evaluator_env,evaluator_pub);expected=expected_evaluation(proposal,hidden_rows,transfer_domains)
 if ep!=expected:raise ValueError('EVALUATION_NOT_RECOMPUTABLE')
 if ep['hidden']['candidate_wrong']>0 or ep['hidden']['candidate_wrong']>=ep['hidden']['best_known_wrong']:raise ValueError('HIDDEN_GATE_FAIL')
 if len(ep['transfer_domains'])<2:raise ValueError('TRANSFER_COUNT_FAIL')
 for d in ep['transfer_domains'].values():
  m=d['metrics']
  if m['candidate_wrong']>=m['best_known_wrong']:raise ValueError('TRANSFER_GAIN_FAIL')
 eval_sha=shaobj(evaluator_env)
 ap=check(authority_env,authority_pub)
 required={'schema':'tukuyo.v946.promotion_authority/1','candidate_sha256':proposal['candidate_sha256'],'evaluation_receipt_sha256':eval_sha,
           'hidden_rows_sha256':ep['hidden_rows_sha256'],'transfer_domain_hashes':{k:v['rows_sha256'] for k,v in ep['transfer_domains'].items()},'decision':'PROMOTE'}
 if ap!=required:raise ValueError('AUTHORITY_BINDING')
 return {'schema':'tukuyo.v946.promoted_primitive/1','candidate_sha256':proposal['candidate_sha256'],'expression':proposal['expression'],
         'evaluation_receipt_sha256':eval_sha,'authority_receipt_sha256':shaobj(authority_env),'scope':'EXTERNALLY_VERIFIED_BOUNDED_PRIMITIVE',
         'global_generalization_claim':False}
