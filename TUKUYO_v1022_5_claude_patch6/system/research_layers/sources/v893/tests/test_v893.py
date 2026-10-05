import json
from pathlib import Path
def test_gap(): assert json.load(open(Path(__file__).parents[1]/'evidence/V893_SUMMARY.json'))['wrong']==0
