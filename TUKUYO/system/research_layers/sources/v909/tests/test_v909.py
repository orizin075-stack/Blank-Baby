import json,pathlib
def test_r2():
 s=json.loads((pathlib.Path(__file__).parents[1]/'evidence/V909_SUMMARY.json').read_text());assert len(s['generations'])==3;assert s['net_correct_gain']>=0;assert s['verified_wrong']==0
