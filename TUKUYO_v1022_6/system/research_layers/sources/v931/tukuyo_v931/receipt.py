import base64,json,hashlib
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
TRACK_ROWS={
 '37fa9e81f4ee8eb41e27075c1f404791c99b7c3c021972a565ba2b7ce27ac95e':300,
 '92659b241c50d6075f795b040596d497a11e3ee172080f4a945af5247a61089f':279,
}
def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def verify(obj,pub_b64,result_rows_path=None):
    try:
        p=obj['payload']; Ed25519PublicKey.from_public_bytes(base64.b64decode(pub_b64)).verify(base64.b64decode(obj['signature_b64']),canon(p))
    except Exception:return {'ok':False,'reason':'SIGNATURE'}
    req={'schema','track_sha256','rows','baseline_impl_sha256','candidate_impl_sha256','baseline_correct','candidate_correct','baseline_wrong','candidate_wrong','result_rows_sha256','evaluator_id','self_authored'}
    if not req.issubset(p):return {'ok':False,'reason':'FIELDS'}
    if p['track_sha256'] not in TRACK_ROWS:return {'ok':False,'reason':'TRACK'}
    if p['rows'] != TRACK_ROWS[p['track_sha256']]:return {'ok':False,'reason':'TRACK_ROWS_MISMATCH'}
    if p['self_authored'] is not False:return {'ok':False,'reason':'SELF_AUTHORED'}
    if any(not isinstance(p[k],int) or p[k]<0 for k in ('baseline_correct','candidate_correct','baseline_wrong','candidate_wrong')):return {'ok':False,'reason':'COUNTS'}
    if p['baseline_correct']+p['baseline_wrong'] != p['rows'] or p['candidate_correct']+p['candidate_wrong'] != p['rows']:return {'ok':False,'reason':'COUNTS_NOT_EXHAUSTIVE'}
    if result_rows_path is None:return {'ok':False,'reason':'RESULT_ROWS_REQUIRED'}
    b=Path(result_rows_path).read_bytes()
    if hashlib.sha256(b).hexdigest()!=p['result_rows_sha256']:return {'ok':False,'reason':'RESULT_ROWS_HASH'}
    try: rows=json.loads(b)
    except Exception:return {'ok':False,'reason':'RESULT_ROWS_FORMAT'}
    if not isinstance(rows,list) or len(rows)!=p['rows']:return {'ok':False,'reason':'RESULT_ROWS_COUNT'}
    bc=sum(1 for x in rows if x.get('baseline_correct') is True); cc=sum(1 for x in rows if x.get('candidate_correct') is True)
    if (bc,p['rows']-bc,cc,p['rows']-cc)!=(p['baseline_correct'],p['baseline_wrong'],p['candidate_correct'],p['candidate_wrong']):return {'ok':False,'reason':'RESULT_ROWS_COUNTS'}
    return {'ok':True,'payload':p}
