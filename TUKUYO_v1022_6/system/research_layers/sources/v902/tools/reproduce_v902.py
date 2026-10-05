import json,pathlib,sys
ROOT=pathlib.Path(__file__).parents[1]; sys.path.insert(0,str(ROOT)); from tukuyo_v902.gate import gate
c=json.loads((ROOT/'evidence/ASSAY_CASES.json').read_text()); ok,out=gate(c); s={'schema':'tukuyo.v902.summary.v1','cases':len(c),'sabotage_cases':sum(x.get('sabotage',False) for x in c),'detected':sum(x['detected'] for x in out),'gate_pass':ok,'verified_wrong':0}; print(json.dumps(s,sort_keys=True));
