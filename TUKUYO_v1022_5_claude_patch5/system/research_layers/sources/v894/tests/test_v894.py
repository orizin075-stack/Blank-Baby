import json
from pathlib import Path
def test_prop():
 s=json.load(open(Path(__file__).parents[1]/'evidence/V894_SUMMARY.json')); assert s['verified_wrong']==0 and s['coverage']>0.9
