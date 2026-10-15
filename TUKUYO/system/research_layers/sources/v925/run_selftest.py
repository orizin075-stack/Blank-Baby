import json,pathlib
r=json.loads(pathlib.Path('evidence/ADVERSARIAL_SECURITY.json').read_text());ok=(r['attacks_total']>=20 and r['blocked']==r['attacks_total'] and r['benign_allowed'])
print(json.dumps({'ok':ok,**r},sort_keys=True));raise SystemExit(0 if ok else 1)
