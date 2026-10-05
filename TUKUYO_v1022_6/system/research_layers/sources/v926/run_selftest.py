import json,pathlib
s=json.loads(pathlib.Path('evidence/SUMMARY.json').read_text());r=json.loads(pathlib.Path('evidence/TRANSFER_RUNS.json').read_text());ok=(len(r)==6 and s['verified_wrong']==0 and s['coverage']>0.70 and all(len(x['distributions'])==5 for x in r))
print(json.dumps({'ok':ok,**s},sort_keys=True));raise SystemExit(0 if ok else 1)
