import json,pathlib
s=json.loads(pathlib.Path('evidence/SUMMARY.json').read_text());r=json.loads(pathlib.Path('evidence/CEGIS_RUNS.json').read_text());monotonic=sum(x['final']['verified_wrong']<=x['first']['verified_wrong'] for x in r);ok=(len(r)==8 and monotonic==8 and s['final_wrong']<=s['first_wrong'])
print(json.dumps({'ok':ok,'monotonic_wrong_nonincrease':monotonic,**s},sort_keys=True));raise SystemExit(0 if ok else 1)
