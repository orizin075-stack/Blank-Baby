import json
from pathlib import Path
def test_gate():
 s=json.load(open(Path(__file__).parents[1]/'evidence/V892_SUMMARY.json')); assert s['verified_wrong']==0 and s['strict_gain_suites']>=1
