import json
from pathlib import Path
def test_meta(): assert json.load(open(Path(__file__).parents[1]/'evidence/V898_SUMMARY.json'))['strict_gain_suites']>=1
