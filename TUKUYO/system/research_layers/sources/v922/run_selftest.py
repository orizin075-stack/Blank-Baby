import json,pathlib
from tukuyo_v922.seal import verify_chain
c=json.loads(pathlib.Path('evidence/HOLDOUT_COMMITMENT.json').read_text());f=json.loads(pathlib.Path('evidence/CANDIDATE_FREEZE.json').read_text());r=json.loads(pathlib.Path('evidence/HOLDOUT_REVEAL.json').read_text());ok=verify_chain(c,f,r)
# tamper controls
r2=json.loads(json.dumps(r));r2['payload']['holdout_seed']+=1
tamper_blocked=not verify_chain(c,f,r2)
ok=ok and tamper_blocked
print(json.dumps({'ok':ok,'hash_chain_valid':verify_chain(c,f,r),'tamper_blocked':tamper_blocked,'external_time_anchor':False},sort_keys=True));raise SystemExit(0 if ok else 1)
