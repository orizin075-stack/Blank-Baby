from __future__ import annotations
import base64,hashlib,json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from tukuyo_v965.family_synthesis import evaluate,sha,canon

def sha_obj(o): return hashlib.sha256(canon(o)).hexdigest()
def _verify(env,pubfile):
    want=Path(pubfile).read_text().strip()
    if env.get('public_key')!=want: raise ValueError('TRUST_ROOT_MISMATCH')
    Ed25519PublicKey.from_public_bytes(base64.b64decode(want)).verify(base64.b64decode(env['signature']),canon(env['payload']))
    return env['payload']

def verify_evaluator(receipt,proposal,pubfile):
    p=_verify(receipt,pubfile)
    if p.get('schema')!='tukuyo.v966.evaluator_receipt/1': raise ValueError('EVALUATOR_SCHEMA')
    if p.get('candidate_sha256')!=proposal.get('candidate_sha256') or p.get('proposal_sha256')!=sha_obj(proposal): raise ValueError('CANDIDATE_BINDING')
    ds=p.get('domains',[])
    if len(ds)<3: raise ValueError('THREE_DOMAINS_REQUIRED')
    if len({d.get('generator_id') for d in ds})<3 or len({d.get('source_schema') for d in ds})<3: raise ValueError('INDEPENDENT_GENERATORS_REQUIRED')
    for d in ds:
        if d.get('wrong')!=0 or d.get('invalid')!=0 or d.get('correct')!=d.get('rows') or d.get('rows',0)<20: raise ValueError('DOMAIN_NOT_CLEAN')
        for k in ('rows_sha256','generator_source_sha256'):
            if not isinstance(d.get(k),str) or len(d[k])!=64: raise ValueError('HASH_BINDING')
    return p

def verify_promotion(receipt,proposal,evaluator_receipt,evaluator_pub,authority_pub):
    ep=verify_evaluator(evaluator_receipt,proposal,evaluator_pub); ap=_verify(receipt,authority_pub)
    if ap.get('schema')!='tukuyo.v966.promotion_receipt/1': raise ValueError('PROMOTION_SCHEMA')
    if ap.get('candidate_sha256')!=proposal['candidate_sha256'] or ap.get('evaluator_receipt_sha256')!=sha_obj(evaluator_receipt): raise ValueError('PROMOTION_BINDING')
    if ap.get('decision')!='PROMOTE_BOUNDED_FAMILY' or ap.get('scope')!='V966_RESIDUAL_DERIVED_FAMILY_THREE_DOMAIN': raise ValueError('NOT_PROMOTED')
    return {'evaluator':ep,'authority':ap}
