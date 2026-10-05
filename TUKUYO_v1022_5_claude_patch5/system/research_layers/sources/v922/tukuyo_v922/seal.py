import hashlib,json,secrets
def canon(o): return json.dumps(o,sort_keys=True,separators=(',',':')).encode()
def commitment(payload,salt): return hashlib.sha256(salt.encode()+b'|'+canon(payload)).hexdigest()
def freeze(candidate_source,holdout_commitment):
 return {'schema':'tukuyo.candidate_freeze.v2','candidate_sha256':hashlib.sha256(candidate_source.encode()).hexdigest(),'holdout_commitment':holdout_commitment}
def verify_chain(commit_obj,freeze_obj,reveal_obj):
 p=reveal_obj['payload']; s=reveal_obj['salt']
 return commitment(p,s)==commit_obj['commitment_sha256'] and freeze_obj['holdout_commitment']==commit_obj['commitment_sha256'] and reveal_obj['candidate_freeze_sha256']==hashlib.sha256(canon(freeze_obj)).hexdigest()
