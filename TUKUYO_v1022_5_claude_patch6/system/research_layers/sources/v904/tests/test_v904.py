import json,pathlib
def test_chain():
 s=json.loads((pathlib.Path(__file__).parents[1]/'evidence/V904_SUMMARY.json').read_text()); assert len(s['generations'])==3; assert s['verified_wrong']==0; assert s['generations'][-1]['candidate_correct']>=s['generations'][-1]['parent_correct']
