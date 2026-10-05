from __future__ import annotations
import base64,hashlib,json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
from tukuyo_v944.gap import search_evidence,classify,shaobj,OPS
SC='tukuyo.v956.blind_gap_commitment/1';RS='tukuyo.v956.blind_gap_reveal/1';SU='tukuyo.v956.blind_gap_suite/1'
def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def h(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def validate_suite(s):
 if not isinstance(s,dict) or s.get('schema')!=SU or set(s)!={'schema','suite_id','cases'}:raise ValueError('SUITE_SCHEMA')
 if not isinstance(s['suite_id'],str) or not s['suite_id'] or len(s['suite_id'])>80:raise ValueError('SUITE_ID')
 rows=s['cases']
 if not isinstance(rows,list) or not 1<=len(rows)<=500:raise ValueError('SUITE_CASE_COUNT')
 for i,r in enumerate(rows):
  if not isinstance(r,dict) or set(r)!={'a','b','expected'} or any(type(r[k]) is not int or abs(r[k])>10000 for k in r):raise ValueError('SUITE_ROW:'+str(i))
 if len({(r['a'],r['b']) for r in rows})!=len(rows):raise ValueError('SUITE_DUPLICATE_INPUT')
 return [dict(r) for r in rows]
def verify_reveal(commitment,reveal,trust_file):
 c=load(commitment) if isinstance(commitment,(str,Path)) else commitment;r=load(reveal) if isinstance(reveal,(str,Path)) else reveal;key=Path(trust_file).read_text().strip()
 if c.get('public_key')!=key:raise ValueError('BLIND_GAP_TRUST_ROOT_MISMATCH')
 p=c.get('payload',{})
 if p.get('schema')!=SC:raise ValueError('COMMITMENT_SCHEMA')
 try:Ed25519PublicKey.from_public_bytes(base64.b64decode(key,validate=True)).verify(base64.b64decode(c['signature'],validate=True),canon(p))
 except (InvalidSignature,ValueError,TypeError) as e:raise ValueError('COMMITMENT_SIGNATURE_INVALID') from e
 if r.get('schema')!=RS or set(r)!={'schema','suite','salt'}:raise ValueError('REVEAL_SCHEMA')
 rows=validate_suite(r['suite']);salt=r['salt']
 if not isinstance(salt,str) or len(salt)<32:raise ValueError('REVEAL_SALT')
 pre={'suite':r['suite'],'salt':salt}
 if p.get('commitment_sha256')!=h(canon(pre)):raise ValueError('REVEAL_PREIMAGE_MISMATCH')
 if p.get('suite_id')!=r['suite']['suite_id'] or p.get('case_count')!=len(rows):raise ValueError('REVEAL_METADATA_MISMATCH')
 return {'commitment':c,'reveal':r,'rows':rows,'commitment_env_sha256':h(canon(c)),'suite_sha256':h(canon(r['suite']))}
def classify_committed(commitment,reveal,trust_file,budget=None):
 v=verify_reveal(commitment,reveal,trust_file);rows=v['rows'];ev=search_evidence(rows,budget=budget)
 if budget is not None and int(budget)<len(OPS):
  result={'state':'SEARCH_INSUFFICIENT','reason':'known hypothesis budget not exhausted','budget':int(budget),'known_operator_count':len(OPS)}
 else:result=classify(rows,ev)
 known={'operators':sorted(OPS),'operator_count':len(OPS)}
 return {'ok':True,'schema':'tukuyo.v956.blind_gap_result/1','suite_id':v['reveal']['suite']['suite_id'],'commitment_env_sha256':v['commitment_env_sha256'],'suite_sha256':v['suite_sha256'],'known_hypothesis_class_sha256':shaobj(known),'search_evidence_sha256':shaobj(ev),'classification':result,'row_count':len(rows),'authority':'EXTERNALLY_COMMITTED_SUITE_LOCALLY_RECOMPUTED_SEARCH'}
