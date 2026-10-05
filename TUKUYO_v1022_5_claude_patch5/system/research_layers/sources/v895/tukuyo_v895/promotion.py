import base64,json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
def canon(o): return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def verify_external_promotion(receipt,trusted_external_pubkey_b64,candidate_sha256):
 try:
  pub=Ed25519PublicKey.from_public_bytes(base64.b64decode(trusted_external_pubkey_b64)); pub.verify(base64.b64decode(receipt['signature_b64']),canon(receipt['payload']))
 except Exception:return False
 p=receipt['payload']; return p.get('candidate_sha256')==candidate_sha256 and p.get('decision')=='PROMOTE' and p.get('evaluator_role')=='external'
