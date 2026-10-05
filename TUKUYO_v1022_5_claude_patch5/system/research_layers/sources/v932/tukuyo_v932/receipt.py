import base64,json,hashlib
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
TRACK_ROWS={'37fa9e81f4ee8eb41e27075c1f404791c99b7c3c021972a565ba2b7ce27ac95e':300,'92659b241c50d6075f795b040596d497a11e3ee172080f4a945af5247a61089f':279}
def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def H(b):return hashlib.sha256(b).hexdigest()
def _track_rows(path):
 b=Path(path).read_bytes();txt=b.decode('utf-8');
 try:
  x=json.loads(txt)
  if isinstance(x,list):return b,x
  if isinstance(x,dict) and isinstance(x.get('rows'),list):return b,x['rows']
 except Exception:pass
 rows=[json.loads(z) for z in txt.splitlines() if z.strip()];return b,rows
def verify(obj,evaluator_pub_b64,result_rows_path,track_path,expected_candidate_sha,expected_baseline_sha,forbidden_release_pub_b64):
 bad=[]
 try:
  p=obj['payload'];pubraw=base64.b64decode(evaluator_pub_b64);Ed25519PublicKey.from_public_bytes(pubraw).verify(base64.b64decode(obj['signature_b64']),canon(p))
 except Exception:return {'ok':False,'reason':'SIGNATURE'}
 req={'schema','track_sha256','rows','baseline_impl_sha256','candidate_impl_sha256','baseline_correct','candidate_correct','baseline_wrong','candidate_wrong','result_rows_sha256','evaluator_public_key_sha256','self_authored'}
 if not req.issubset(p):return {'ok':False,'reason':'FIELDS'}
 if H(pubraw)!=p['evaluator_public_key_sha256']:return {'ok':False,'reason':'EVALUATOR_KEY_BINDING'}
 if forbidden_release_pub_b64 and H(base64.b64decode(forbidden_release_pub_b64))==H(pubraw):return {'ok':False,'reason':'SELF_AUTHORITY'}
 if p['self_authored'] is not False:return {'ok':False,'reason':'SELF_AUTHORED'}
 if p['track_sha256'] not in TRACK_ROWS:return {'ok':False,'reason':'TRACK'}
 try:tb,trows=_track_rows(track_path)
 except Exception:return {'ok':False,'reason':'TRACK_FORMAT'}
 if H(tb)!=p['track_sha256']:return {'ok':False,'reason':'TRACK_HASH'}
 if len(trows)!=TRACK_ROWS[p['track_sha256']] or p['rows']!=len(trows):return {'ok':False,'reason':'TRACK_ROWS'}
 if p['candidate_impl_sha256']!=expected_candidate_sha:return {'ok':False,'reason':'CANDIDATE_BINDING'}
 if p['baseline_impl_sha256']!=expected_baseline_sha:return {'ok':False,'reason':'BASELINE_BINDING'}
 rb=Path(result_rows_path).read_bytes()
 if H(rb)!=p['result_rows_sha256']:return {'ok':False,'reason':'RESULT_ROWS_HASH'}
 try:rr=json.loads(rb)
 except Exception:return {'ok':False,'reason':'RESULT_ROWS_FORMAT'}
 if not isinstance(rr,list) or len(rr)!=len(trows):return {'ok':False,'reason':'RESULT_ROWS_COUNT'}
 bc=cc=0
 for i,(case,row) in enumerate(zip(trows,rr)):
  if row.get('case_index')!=i:return {'ok':False,'reason':f'CASE_INDEX:{i}'}
  if row.get('case_sha256')!=H(canon(case)):return {'ok':False,'reason':f'CASE_HASH:{i}'}
  b=(row.get('baseline_prediction')==row.get('truth'));c=(row.get('candidate_prediction')==row.get('truth'))
  if row.get('baseline_correct') is not b or row.get('candidate_correct') is not c:return {'ok':False,'reason':f'ROW_CORRECTNESS:{i}'}
  bc+=b;cc+=c
 counts=(bc,len(rr)-bc,cc,len(rr)-cc)
 if counts!=(p['baseline_correct'],p['baseline_wrong'],p['candidate_correct'],p['candidate_wrong']):return {'ok':False,'reason':'COUNTS'}
 return {'ok':True,'payload':p}
