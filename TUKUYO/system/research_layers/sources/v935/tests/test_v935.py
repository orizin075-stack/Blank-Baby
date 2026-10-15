import json,pathlib,sys,subprocess,tempfile,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tukuyo_v935.evidence_chain import verify

def test_evidence_chain():assert verify(ROOT)['ok']
def test_final_holdout_is_strong_but_not_perfect():
 d=json.loads((ROOT/'evidence/HOLDOUT_RESULT.json').read_text());assert d['final']['correct']>d['baseline']['correct'];assert d['final']['correct']+d['final']['wrong']==4000
def test_status_keeps_blockers():
 s=json.loads((ROOT/'STATUS.json').read_text());assert s['l6_established'] is False and s['independent_evaluator']=='PENDING' and s['wallclock30_two_fork']=='NOT_INITIALIZED'
