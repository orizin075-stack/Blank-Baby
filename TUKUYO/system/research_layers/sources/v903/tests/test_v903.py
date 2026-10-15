import json,pathlib
def test_promoted_is_code():
 r=pathlib.Path(__file__).parents[1]; s=json.loads((r/'evidence/V903_SUMMARY.json').read_text()); assert s['promoted']['name']=='joint'; assert (r/'evidence/PROMOTED_CONTROLLER.py').read_text().startswith('def choose')
def test_wrong_zero():
 r=pathlib.Path(__file__).parents[1]; s=json.loads((r/'evidence/V903_SUMMARY.json').read_text()); assert s['verified_wrong']==0
