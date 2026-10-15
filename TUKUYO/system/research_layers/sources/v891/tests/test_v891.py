import json,subprocess,sys,os
from pathlib import Path
def test_summary():
 r=Path(__file__).parents[1]; s=json.load(open(r/'evidence/V891_SUMMARY.json')); assert s['verified_wrong']==0 and s['candidate_absent_all'] and s['strict_gain_suites']>=1
def test_no_cache():
 r=Path(__file__).parents[1]; assert not list(r.rglob('*.pyc'))
def test_reproduction_stable():
 r=Path(__file__).parents[1]; before=(r/'evidence/V891_SUMMARY.json').read_bytes(); env=os.environ.copy(); env['PYTHONDONTWRITEBYTECODE']='1'; subprocess.check_call([sys.executable,str(r/'tools/reproduce_v891.py')],cwd=r,env=env); assert before==(r/'evidence/V891_SUMMARY.json').read_bytes()
