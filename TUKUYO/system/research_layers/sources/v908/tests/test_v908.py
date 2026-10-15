import json,pathlib
def test_heldout():
 s=json.loads((pathlib.Path(__file__).parents[1]/'evidence/V908_SUMMARY.json').read_text());assert s['selected']['name']=='joint';assert s['heldout_correct']==s['heldout_total']
