import json
from pathlib import Path
def test_loop(): assert json.load(open(Path(__file__).parents[1]/'evidence/V897_SUMMARY.json'))['strict_gain_suites']==8
