import json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py'
sys.path.insert(0,str(ROOT/'src'))
from tukuyo_v978.heart_loop import process_experience
from tukuyo_v983.homeostasis import assess as homeostasis_assess
from tukuyo_v977.whole_state import sync as whole_sync


def run(data,*args,ok=True):
 p=subprocess.run([sys.executable,'-B',str(CLI),'--data',str(data),*map(str,args)],cwd=ROOT,text=True,capture_output=True,timeout=180)
 if ok and p.returncode!=0:raise AssertionError(p.stdout+p.stderr)
 try:return json.loads(p.stdout)
 except Exception:raise AssertionError(p.stdout+p.stderr)


def prime_knowledge(d):
 for i in range(12):process_experience(d,'discovery',1.0,1.0,f'unknown_{i%3}','')
 homeostasis_assess(d);whole_sync(d)
 p=run(d,'purpose-integrate');assert p['active_purpose']=='SEEK_KNOWLEDGE'
 return p


def test_v986_compiles_bounded_long_horizon_plan_and_detects_tamper():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'data';run(d,'init','--individual-id','V986-TEST');prime_knowledge(d)
  x=run(d,'plan-compile','--horizon-cycles','3')
  assert x['ok'] and x['active_purpose']=='SEEK_KNOWLEDGE' and x['step_count']==9
  assert x['first_action']=='WHOLE_AUDIT' and x['claim_boundary']['bounded_internal_action_space']
  assert run(d,'plan-audit')['ok'];assert run(d,'whole-audit')['ok']
  pp=d/'v986'/'LONG_HORIZON_PLAN.json';q=json.loads(pp.read_text());q['steps'][0]['action']='UNBOUNDED_EXTERNAL_ACTION';pp.write_text(json.dumps(q))
  assert not run(d,'plan-audit',ok=False)['ok'];assert not run(d,'whole-audit',ok=False)['ok']


def test_v987_executes_plan_in_bounded_internal_space_and_records_outcomes():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'data';run(d,'init','--individual-id','V987-TEST');prime_knowledge(d);run(d,'plan-compile','--horizon-cycles','2')
  x=run(d,'plan-execute')
  assert x['ok'] and x['complete'] and x['executed_steps']==6 and x['success_rate']==1.0
  assert all(t['action'] in {'WHOLE_AUDIT','EVIDENCE_REFLECT','PURPOSE_REEVALUATE'} for t in x['trace'])
  assert run(d,'plan-execution-audit')['ok'];assert run(d,'whole-audit')['ok']
  ep=d/'v987'/'PLAN_EXECUTION_STATE.json';q=json.loads(ep.read_text());q['trace'][0]['utility']=999;ep.write_text(json.dumps(q))
  assert not run(d,'plan-execution-audit',ok=False)['ok'];assert not run(d,'whole-audit',ok=False)['ok']


def test_v988_empirical_strategy_learning_changes_future_plan_order():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'data';run(d,'init','--individual-id','V988-TEST');prime_knowledge(d)
  a=run(d,'plan-compile','--horizon-cycles','1');assert a['first_action']=='WHOLE_AUDIT'
  e=run(d,'plan-execute');assert e['ok']
  l=run(d,'strategy-learn');assert l['ok'] and l['purpose']=='SEEK_KNOWLEDGE'
  assert l['preference'][0]=='EVIDENCE_REFLECT' and l['action_stats']['EVIDENCE_REFLECT']['mean_utility']>l['action_stats']['WHOLE_AUDIT']['mean_utility']
  again=run(d,'strategy-learn');assert again['ok'] and again['idempotent'] and again['action_stats']==l['action_stats']
  # Purpose is still knowledge; re-integrate to make the source fresh, then compile again.
  run(d,'purpose-integrate')
  b=run(d,'plan-compile','--horizon-cycles','1');assert b['first_action']=='EVIDENCE_REFLECT'
  assert run(d,'strategy-audit')['ok'];assert run(d,'plan-audit')['ok'];assert run(d,'whole-audit')['ok']
  sp=d/'v988'/'STRATEGY_STATE.json';q=json.loads(sp.read_text());q['purpose_preferences']['SEEK_KNOWLEDGE']=['WHOLE_AUDIT'];sp.write_text(json.dumps(q))
  assert not run(d,'strategy-audit',ok=False)['ok'];assert not run(d,'whole-audit',ok=False)['ok']
