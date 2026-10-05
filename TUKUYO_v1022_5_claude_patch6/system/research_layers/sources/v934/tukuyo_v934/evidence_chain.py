import json,hashlib
from pathlib import Path
def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def H(b):return hashlib.sha256(b).hexdigest()
def verify(root):
 r=Path(root);bad=[]
 c=json.loads((r/'evidence/HOLDOUT_COMMITMENT.json').read_text());f=json.loads((r/'evidence/CANDIDATE_FREEZE.json').read_text());v=json.loads((r/'evidence/HOLDOUT_REVEAL.json').read_text())
 pre=v.get('preimage')
 if H(canon(pre))!=c.get('commitment_sha256'):bad.append('COMMITMENT_PREIMAGE')
 if f.get('holdout_commitment_file_sha256')!=H((r/'evidence/HOLDOUT_COMMITMENT.json').read_bytes()):bad.append('FREEZE_COMMITMENT_FILE')
 if v.get('candidate_freeze_file_sha256')!=H((r/'evidence/CANDIDATE_FREEZE.json').read_bytes()):bad.append('REVEAL_FREEZE_FILE')
 if f.get('candidate_impl_sha256')!=H((r/'evidence/EXPECTED_CANDIDATE.py').read_bytes()):bad.append('CANDIDATE_HASH')
 if f.get('search_report_sha256')!=H((r/'evidence/SEARCH_CAUSALITY_MULTI_SEED.json').read_bytes()):bad.append('SEARCH_REPORT_HASH')
 return {'ok':not bad,'bad':bad}
