import json,pathlib,sys
s=json.loads(pathlib.Path('evidence/SUMMARY.json').read_text());r=json.loads(pathlib.Path('evidence/SUITES.json').read_text());ok=(len(r)==12 and all(x['chain_valid'] for x in r) and s['verified_wrong']==0 and s['invalid_output']==0 and s['coverage']>0.80)
print(json.dumps({'ok':ok,**s},sort_keys=True));raise SystemExit(0 if ok else 1)
