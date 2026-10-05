import pathlib,json
def test_pending():
 s=json.loads((pathlib.Path(__file__).parents[1]/'evidence/THIRD_PARTY_STATUS.json').read_text()); assert s['completed'] is False and s['receipts']==0
