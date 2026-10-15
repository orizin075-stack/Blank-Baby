import base64,json,hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
CANON={'37fa9e81f4ee8eb41e27075c1f404791c99b7c3c021972a565ba2b7ce27ac95e','92659b241c50d6075f795b040596d497a11e3ee172080f4a945af5247a61089f'}
RELEASE_FP='714de2ffd8692f52e210425b270356029ddea1689a2998f2c676e642509f6aaa'
def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def fp(pub_b64):return hashlib.sha256(base64.b64decode(pub_b64)).hexdigest()
def decide(receipt,evaluator_pub_b64,expected_candidate_sha):
 if fp(evaluator_pub_b64)==RELEASE_FP:return {'promote':False,'reason':'SELF_AUTHORITY'}
 try:p=receipt['payload'];Ed25519PublicKey.from_public_bytes(base64.b64decode(evaluator_pub_b64)).verify(base64.b64decode(receipt['signature_b64']),canon(p))
 except Exception:return {'promote':False,'reason':'SIGNATURE'}
 if p.get('self_authored') is not False:return {'promote':False,'reason':'SELF_AUTHORED'}
 if p.get('track_sha256') not in CANON:return {'promote':False,'reason':'TRACK'}
 if p.get('candidate_impl_sha256')!=expected_candidate_sha:return {'promote':False,'reason':'IMPL_BINDING'}
 if p.get('candidate_wrong')!=0:return {'promote':False,'reason':'VERIFIED_WRONG'}
 if p.get('candidate_correct',-1)<=p.get('baseline_correct',-1):return {'promote':False,'reason':'NO_STRICT_GAIN'}
 return {'promote':True,'reason':'PASS'}
