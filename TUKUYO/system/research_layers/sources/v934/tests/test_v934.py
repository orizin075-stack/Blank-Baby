import json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tukuyo_v934.evidence_chain import verify

def test_chain():assert verify(ROOT)['ok']
def test_boundary_holdout_gain():
 d=json.loads((ROOT/'evidence/HOLDOUT_RESULT.json').read_text());assert d['v934']['correct']>d['v933']['correct'];assert d['v934']['wrong']>0
def test_stress_nonregression_most_distributions():
 d=json.loads((ROOT/'evidence/STRESS_RESULTS.json').read_text());assert all(sum(x['v934_correct'] for x in vs)>=sum(x['v933_correct'] for x in vs) for k,vs in d.items())
