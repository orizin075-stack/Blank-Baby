import json,pathlib
s=json.loads(pathlib.Path('evidence/SUMMARY.json').read_text());r=json.loads(pathlib.Path('evidence/MULTIGEN_RUNS.json').read_text());ok=(len(r)==3 and s['final_verified_wrong']==0 and s['accepted_generations']>=3 and s['final_coverage']>0.60)
print(json.dumps({'ok':ok,**s},sort_keys=True));raise SystemExit(0 if ok else 1)
