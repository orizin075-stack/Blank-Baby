import json,pathlib
from tukuyo_v907.evaluator import evaluate
def test_good():
 R=pathlib.Path(__file__).parents[1];o=evaluate((R/'candidate/CANDIDATE_SOURCE.py').read_text(),json.loads((R/'evaluator_only/HIDDEN_ROWS.json').read_text()));assert o['wrong']==0 and o['accepted']
def test_malicious():
 R=pathlib.Path(__file__).parents[1];o=evaluate((R/'candidate/MALICIOUS_SOURCE.py').read_text(),json.loads((R/'evaluator_only/HIDDEN_ROWS.json').read_text()));assert not o['accepted'] and o['reason']=='FORBIDDEN_SOURCE'
