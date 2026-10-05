from __future__ import annotations
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from tukuyo_v957.novel_primitive import eval_proposal


def canon(o):
    return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_obj(o): return sha_bytes(canon(o))
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def _pub(path): return Ed25519PublicKey.from_public_bytes(base64.b64decode(Path(path).read_text().strip()))
def _verify_signed(env,pubfile):
    if not isinstance(env,dict) or set(env)!= {'payload','public_key','signature'}: raise ValueError('SIGNED_ENVELOPE_SCHEMA')
    want=Path(pubfile).read_text().strip()
    if env['public_key']!=want: raise ValueError('TRUST_ROOT_MISMATCH')
    _pub(pubfile).verify(base64.b64decode(env['signature']),canon(env['payload']))
    return env['payload']

def verify_proposal(p):
    # eval_proposal checks schema/hash. Execute once on harmless input to force verification.
    eval_proposal(p,0,0)
    return p['candidate_sha256']

def freeze_proposal(proposal):
    c=verify_proposal(proposal)
    return {'schema':'tukuyo.v958.candidate_freeze/1','candidate_sha256':c,'proposal_sha256':sha_obj(proposal),'primitive':proposal['primitive'],'expression':proposal['expression']}

def adapt_domain_b(record):
    if record.get('schema')!='tukuyo.v958.state_transition/1': raise ValueError('DOMAIN_B_SCHEMA')
    before=record.get('before'); event=record.get('event'); observed=record.get('observed')
    if not all(isinstance(x,dict) for x in (before,event,observed)): raise ValueError('DOMAIN_B_FIELDS')
    a=before.get('counter'); b=event.get('batch'); expected=observed.get('bucket_plus_batch')
    if not all(type(x) is int for x in (a,b,expected)): raise ValueError('DOMAIN_B_TYPES')
    return {'a':a,'b':b,'expected':expected}

def verify_evaluator_receipt(receipt, proposal, evaluator_pubfile):
    payload=_verify_signed(receipt,evaluator_pubfile)
    if payload.get('schema')!='tukuyo.v958.evaluator_receipt/1': raise ValueError('EVALUATOR_SCHEMA')
    cand=verify_proposal(proposal)
    if payload.get('candidate_sha256')!=cand or payload.get('proposal_sha256')!=sha_obj(proposal): raise ValueError('CANDIDATE_BINDING')
    domains=payload.get('domains')
    if not isinstance(domains,list) or len(domains)<2: raise ValueError('TWO_DOMAINS_REQUIRED')
    ids=[d.get('domain_id') for d in domains]
    if len(ids)!=len(set(ids)): raise ValueError('DUPLICATE_DOMAIN')
    schemas=[d.get('source_schema') for d in domains]
    generators=[d.get('generator_id') for d in domains]
    if len(set(schemas))<2 or len(set(generators))<2: raise ValueError('INDEPENDENT_GENERATOR_REQUIRED')
    for d in domains:
        if d.get('wrong')!=0 or d.get('invalid')!=0 or d.get('correct')!=d.get('rows') or d.get('rows',0)<16: raise ValueError('DOMAIN_NOT_CLEAN')
        if not isinstance(d.get('source_sha256'),str) or len(d['source_sha256'])!=64: raise ValueError('SOURCE_HASH')
        if not isinstance(d.get('rows_sha256'),str) or len(d['rows_sha256'])!=64: raise ValueError('ROWS_HASH')
    return payload

def verify_promotion_receipt(receipt,proposal,evaluator_receipt,evaluator_pubfile,authority_pubfile):
    ep=verify_evaluator_receipt(evaluator_receipt,proposal,evaluator_pubfile)
    ap=_verify_signed(receipt,authority_pubfile)
    if ap.get('schema')!='tukuyo.v958.promotion_receipt/1': raise ValueError('PROMOTION_SCHEMA')
    if ap.get('candidate_sha256')!=proposal['candidate_sha256']: raise ValueError('PROMOTION_CANDIDATE')
    if ap.get('evaluator_receipt_sha256')!=sha_obj(evaluator_receipt): raise ValueError('PROMOTION_EVALUATOR_BINDING')
    if ap.get('decision')!='PROMOTE_BOUNDED': raise ValueError('NOT_PROMOTED')
    if ap.get('scope')!='V958_BOUNDED_SYNTHETIC_TWO_DOMAIN': raise ValueError('PROMOTION_SCOPE')
    return {'evaluator':ep,'authority':ap}

def registry_path(data): return Path(data)/'research_registry_v958'/'ACTIVE_PRIMITIVES.json'
def install(data,proposal,evaluator_receipt,promotion_receipt,evaluator_pubfile,authority_pubfile):
    verified=verify_promotion_receipt(promotion_receipt,proposal,evaluator_receipt,evaluator_pubfile,authority_pubfile)
    p=registry_path(data); p.parent.mkdir(parents=True,exist_ok=True)
    state={'schema':'tukuyo.v958.primitive_registry/1','entries':[]}
    if p.exists(): state=json.loads(p.read_text(encoding='utf-8'))
    if state.get('schema')!='tukuyo.v958.primitive_registry/1': raise ValueError('REGISTRY_SCHEMA')
    cand=proposal['candidate_sha256']
    if any(x.get('candidate_sha256')==cand for x in state['entries']): raise ValueError('DUPLICATE_PROMOTION')
    entry={'candidate_sha256':cand,'proposal':proposal,'proposal_sha256':sha_obj(proposal),'evaluator_receipt_sha256':sha_obj(evaluator_receipt),'promotion_receipt_sha256':sha_obj(promotion_receipt),'promotion_scope':verified['authority']['scope'],'status':'ACTIVE_BOUNDED_RESEARCH','domains':[d['domain_id'] for d in verified['evaluator']['domains']]}
    state['entries'].append(entry)
    p.write_bytes(canon(state)+b'\n')
    return entry

def audit_registry(data):
    p=registry_path(data)
    if not p.exists(): return {'ok':True,'entries':0,'status':'EMPTY'}
    s=json.loads(p.read_text(encoding='utf-8'))
    if s.get('schema')!='tukuyo.v958.primitive_registry/1' or not isinstance(s.get('entries'),list): raise ValueError('REGISTRY_SCHEMA')
    seen=set()
    for e in s['entries']:
        if e.get('candidate_sha256') in seen: raise ValueError('DUPLICATE_CANDIDATE')
        seen.add(e['candidate_sha256'])
        p0=e.get('proposal')
        if sha_obj(p0)!=e.get('proposal_sha256') or verify_proposal(p0)!=e.get('candidate_sha256'): raise ValueError('REGISTRY_PROPOSAL_BINDING')
        if e.get('status')!='ACTIVE_BOUNDED_RESEARCH': raise ValueError('REGISTRY_STATUS')
    return {'ok':True,'entries':len(s['entries']),'candidate_sha256s':sorted(seen)}

def evaluate_registry(data,candidate_sha256,a,b):
    s=json.loads(registry_path(data).read_text(encoding='utf-8'))
    matches=[e for e in s['entries'] if e.get('candidate_sha256')==candidate_sha256]
    if len(matches)!=1: raise ValueError('CANDIDATE_NOT_ACTIVE')
    e=matches[0]
    return {'ok':True,'status':'RESOLVED_BOUNDED_RESEARCH','candidate_sha256':candidate_sha256,'answer':eval_proposal(e['proposal'],int(a),int(b)),'scope':e['promotion_scope']}
