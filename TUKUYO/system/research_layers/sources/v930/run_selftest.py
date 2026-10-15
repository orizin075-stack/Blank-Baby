import json,pathlib
l=json.loads(pathlib.Path('evidence/CAPABILITY_LEDGER.json').read_text());b=json.loads(pathlib.Path('evidence/OPEN_BLOCKERS.json').read_text());d=json.loads(pathlib.Path('evidence/DEPRECATED_CLAIMS.json').read_text());ok='general L6' in l['not_established'] and len(b)==6 and len(d['items'])>=3
print(json.dumps({'ok':ok,'l6_claim_eligible':False,'open_blockers':len(b),'deprecated_claim_groups':len(d['items'])},sort_keys=True));raise SystemExit(0 if ok else 1)
