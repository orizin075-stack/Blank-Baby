import json
from pathlib import Path
def test_cycle():
 s=json.load(open(Path(__file__).parents[1]/'evidence/V900_SUMMARY.json')); assert s['cycles']==40 and s['accepted_interventions']>=1 and s['verified_wrong']==0 and not s['external_promotion']
