#!/usr/bin/env python3
"""Standalone v1015.5 challenge verifier. Imports no TUKUYO package modules."""
import argparse,base64,hashlib,importlib.util,json,sys,time
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
BUNDLE='tukuyo.v1015_5.challenge_reproduction_bundle/1';CH='tukuyo.v1015_5.challenge/1';CP='tukuyo.v1015_5.challenge_payload/1'
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha_obj(x):return hashlib.sha256(canon(x)).hexdigest()
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def load_pub(path):
 s=Path(path).read_text().strip();return s,Ed25519PublicKey.from_public_bytes(base64.b64decode(s,validate=True))
def challenge_errors(env,trust_file,expected=None,release_manifest_sha=None,first_witness_ns=None):
 errs=[]
 try:trust,pk=load_pub(trust_file);p=env.get('payload') or {}
 except Exception as e:return ['CHALLENGE_TRUST_INVALID:'+type(e).__name__],{}
 if env.get('schema')!=CH or p.get('schema')!=CP:errs.append('CHALLENGE_SCHEMA')
 if env.get('public_key')!=trust:errs.append('CHALLENGE_TRUST_ROOT_MISMATCH')
 try:pk.verify(base64.b64decode(env.get('signature',''),validate=True),canon(p))
 except Exception:errs.append('CHALLENGE_SIGNATURE')
 z=dict(p);cid=z.pop('challenge_id',None)
 if cid!=sha_obj(z):errs.append('CHALLENGE_ID')
 if release_manifest_sha and p.get('release_manifest_sha256')!=release_manifest_sha:errs.append('CHALLENGE_RELEASE_BINDING')
 if expected is not None and env!=expected:errs.append('EXPECTED_CHALLENGE_MISMATCH')
 if first_witness_ns is not None:
  if int(first_witness_ns)<int(p.get('issued_utc_ns',0)):errs.append('CHALLENGE_AFTER_START_WITNESS')
  if int(first_witness_ns)>int(p.get('expires_utc_ns',0)):errs.append('CHALLENGE_EXPIRED_BEFORE_START_WITNESS')
 return errs,p
def load_base_verifier():
 p=Path(__file__).with_name('v1015_4_independent_verifier.py');spec=importlib.util.spec_from_file_location('v1015_4_independent_verifier_standalone',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def verify(bundle,publisher,witness,challenge_trust,expected_challenge):
 errs=[]
 try:o=read(bundle)
 except Exception as e:return {'ok':False,'version':'v1015.5','errors':['BUNDLE_MALFORMED:'+type(e).__name__]}
 if o.get('schema')!=BUNDLE or o.get('version')!='v1015.5':errs.append('BUNDLE_SCHEMA')
 z=dict(o);got=z.pop('bundle_sha256',None)
 if got!=sha_obj(z):errs.append('BUNDLE_HASH')
 base=o.get('base_reproduction_bundle') or {};tmp=Path(bundle).with_suffix('.base_verify_tmp.json');tmp.write_bytes(canon(base)+b'\n')
 try:br=load_base_verifier().verify(tmp,publisher,witness)
 finally:
  try:tmp.unlink()
  except Exception:pass
 if not br.get('ok'):errs += ['BASE:'+x for x in br.get('errors',[])]
 exp=read(expected_challenge);env=o.get('challenge_envelope') or {}
 source=base.get('source_evidence') or {};receipts=source.get('witness_receipts') or []
 first=min([int((r.get('payload') or {}).get('witnessed_utc_ns',0)) for r in receipts if int((r.get('payload') or {}).get('witnessed_utc_ns',0))>0] or [0])
 # Manifest SHA comes from exact embedded manifest bytes in base bundle.
 try:msha=sha_bytes(base64.b64decode(base.get('release_manifest_bytes_b64',''),validate=True))
 except Exception:msha=None;errs.append('RELEASE_MANIFEST_BYTES')
 ce,cp=challenge_errors(env,challenge_trust,exp,msha,first if first else None);errs+=ce
 trust=Path(challenge_trust).read_text().strip();bind=o.get('challenge_binding') or {}
 expected_bind={'challenge_id':cp.get('challenge_id'),'challenge_payload_sha256':sha_obj(cp),'challenge_envelope_sha256':sha_bytes(Path(expected_challenge).read_bytes()),'challenge_public_key_sha256':hashlib.sha256(trust.encode()).hexdigest(),'profile':cp.get('profile'),'issued_utc_ns':cp.get('issued_utc_ns'),'expires_utc_ns':cp.get('expires_utc_ns'),'release_manifest_sha256':cp.get('release_manifest_sha256')}
 if bind!=expected_bind:errs.append('CHALLENGE_BINDING')
 if o.get('challenge_public_key')!=trust:errs.append('CHALLENGE_PUBLIC_KEY')
 # Require challenge binding in execution/resume states and every signed witness request used by the source evidence.
 for name,st in [('EXECUTION',base.get('execution_state') or {}),('RESUME',base.get('resume_state') or {})]:
  if st.get('challenge_binding')!=bind:errs.append(name+'_CHALLENGE_BINDING')
 reqs=source.get('witness_requests') or []
 if not reqs:errs.append('CHALLENGE_WITNESS_REQUESTS_MISSING')
 for i,rq in enumerate(reqs,1):
  rb=rq.get('challenge_binding') or {}
  if rb.get('challenge_id')!=bind.get('challenge_id') or rb.get('challenge_payload_sha256')!=bind.get('challenge_payload_sha256') or rb.get('challenge_public_key_sha256')!=bind.get('challenge_public_key_sha256'):errs.append(f'WITNESS_REQUEST_CHALLENGE:{i}')
 # Require all receipts to point to challenge-bound requests.
 reqmap={r.get('request_sha256'):r for r in reqs}
 for i,r in enumerate(receipts,1):
  if (r.get('payload') or {}).get('request_sha256') not in reqmap:errs.append(f'RECEIPT_CHALLENGE_REQUEST:{i}')
 return {'ok':not errs,'version':'v1015.5','schema':'tukuyo.v1015_5.independent_challenge_audit/1','errors':errs,'outcome':o.get('outcome') if not errs else None,'challenge_id':bind.get('challenge_id') if not errs else None,'base_audit':br,'claim_boundary':{'24h_completed':bool((br.get('claim_boundary') or {}).get('24h_completed')) if not errs else False,'72h_completed':bool((br.get('claim_boundary') or {}).get('72h_completed')) if not errs else False,'7day_completed':bool((br.get('claim_boundary') or {}).get('7day_completed')) if not errs else False,'fresh_external_challenge_verified':not errs,'prior_bundle_replay_under_new_challenge_rejected':True,'human_third_party_reproduction_completed':False}}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('bundle');ap.add_argument('--publisher-trust-file',required=True);ap.add_argument('--witness-trust-file',required=True);ap.add_argument('--challenge-trust-file',required=True);ap.add_argument('--expected-challenge-file',required=True);a=ap.parse_args();r=verify(a.bundle,a.publisher_trust_file,a.witness_trust_file,a.challenge_trust_file,a.expected_challenge_file);print(json.dumps(r,ensure_ascii=False,sort_keys=True));raise SystemExit(0 if r['ok'] else 1)
if __name__=='__main__':main()
