import json,pathlib
def test_no_overclaim():
 R=pathlib.Path(__file__).parents[1];s=json.loads((R/'STATUS.json').read_text());b=json.loads((R/'evidence/OPEN_BLOCKERS.json').read_text());assert not s['l6_established'] and not s['l6_claim_eligible'];assert len(b['blockers'])==4
