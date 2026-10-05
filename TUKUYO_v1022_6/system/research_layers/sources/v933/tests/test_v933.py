import json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tukuyo_v933.evidence_chain import verify

def test_evidence_chain():assert verify(ROOT)['ok']
def test_synth_has_no_oracle_import_or_exact_constants():
 s=(ROOT/'tukuyo_v933/synth.py').read_text();assert 'oracle' not in s.lower();assert '0.70' not in s and '0.15' not in s
def test_holdout_strict_gain():
 d=json.loads((ROOT/'evidence/HOLDOUT_RESULT.json').read_text());assert d['candidate']['correct']>d['base']['correct'];assert d['candidate']['wrong']<d['base']['wrong'];assert d['candidate']['wrong']>0
def test_negative_controls_are_worse():
 d=json.loads((ROOT/'evidence/NEGATIVE_CONTROLS.json').read_text());assert all(x['holdout_correct']<d['real_candidate_correct'] for x in d['label_corruption_proxies'])
