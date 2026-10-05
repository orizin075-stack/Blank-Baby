import json
from pathlib import Path
def test_multigen():
 s=json.load(open(Path(__file__).parents[1]/'evidence/V899_SUMMARY.json')); assert s['three_generation_chains']==8 and s['total_promotions']>=1 and s['verified_wrong']==0
