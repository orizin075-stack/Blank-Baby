import json,os,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py';ANCHOR=ROOT/'_TEST_ANCHOR_PATH.txt'
def run(d,*a,ok=True):
 env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'};anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR');cmd=[sys.executable,'-B',str(CLI)]
 if anchor:cmd += ['--runtime-trust-file',anchor]
 cmd += ['--data',str(d),*map(str,a)];p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,env=env,timeout=180)
 r=json.loads(p.stdout)
 if ok and (p.returncode or not r.get('ok',False)):raise AssertionError(p.stdout+p.stderr)
 return r
def test_verified_reasoning_and_research():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','T1008A');assert run(d,'verified-query','19*(3+2)')['answer']=='95';r=run(d,'research-agent-assay');assert r['passed']==r['total']==6
def test_self_preservation_changes_with_injury():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','T1008B');run(d,'organism2-init');run(d,'organism2-update','INJURY','--amount','.5');p=Path(td)/'o.json';p.write_text(json.dumps([{'id':'risky','reward':2,'destruction_risk':.9,'need_relief':.2},{'id':'safe','reward':.6,'destruction_risk':.05,'need_relief':.1}]))
  assert run(d,'organism2-preserve',p)['chosen']=='safe'
def test_death_is_irreversible_for_same_identity():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','T1008C');run(d,'organism2-init');run(d,'organism2-update','INJURY','--amount','1');r=run(d,'organism2-update','INJURY','--amount','1');assert r['state']['lifecycle']=='DEAD';x=run(d,'living-cycle','--query','2+2',ok=False);assert x['error']=='ENTITY_DEAD'
def test_integrated_living_cycle():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','T1008D');r=run(d,'living-cycle','--query','12*(5+4)');assert r['reasoning']['answer']=='108' and r['research']['passed']==6 and not r['external_action_taken'];assert run(d,'living-audit')['ok'];assert run(d,'whole-audit')['ok']
