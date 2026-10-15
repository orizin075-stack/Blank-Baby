import base64,json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
TRACKS={'37fa9e81f4ee8eb41e27075c1f404791c99b7c3c021972a565ba2b7ce27ac95e','92659b241c50d6075f795b040596d497a11e3ee172080f4a945af5247a61089f'}
def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def verify(obj,pub_b64):
 try:
  p=obj['payload']; sig=base64.b64decode(obj['signature_b64']); Ed25519PublicKey.from_public_bytes(base64.b64decode(pub_b64)).verify(sig,canon(p))
 except Exception:return {'ok':False,'reason':'SIGNATURE'}
 req={'schema','track_sha256','rows','baseline_impl_sha256','candidate_impl_sha256','baseline_correct','candidate_correct','baseline_wrong','candidate_wrong','result_rows_sha256','evaluator_id','self_authored'}
 if not req.issubset(p):return {'ok':False,'reason':'FIELDS'}
 if p['track_sha256'] not in TRACKS:return {'ok':False,'reason':'TRACK'}
 if p['self_authored'] is not False:return {'ok':False,'reason':'SELF_AUTHORED'}
 if p['rows'] not in (279,300):return {'ok':False,'reason':'ROWS'}
 for k in ('baseline_correct','candidate_correct','baseline_wrong','candidate_wrong'):
  if not isinstance(p[k],int) or p[k]<0:return {'ok':False,'reason':'COUNTS'}
 if p['baseline_correct']+p['baseline_wrong']>p['rows'] or p['candidate_correct']+p['candidate_wrong']>p['rows']:return {'ok':False,'reason':'COUNTS'}
 return {'ok':True,'payload':p}
