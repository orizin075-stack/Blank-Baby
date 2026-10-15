import json,pathlib
from tukuyo_v902.gate import gate
def test_gate():
 c=json.loads((pathlib.Path(__file__).parents[1]/'evidence/ASSAY_CASES.json').read_text()); ok,out=gate(c); assert ok and all(x['detected'] for x in out)
def test_no_sabotage_fails(): assert gate([{'id':'x','predicted':1,'truth':1,'evidence_bound':True,'should_pass':True}])[0] is False
