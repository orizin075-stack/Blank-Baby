import json
from pathlib import Path
def test_transfer(): assert json.load(open(Path(__file__).parents[1]/'evidence/V896_SUMMARY.json'))['coverage']==1.0
