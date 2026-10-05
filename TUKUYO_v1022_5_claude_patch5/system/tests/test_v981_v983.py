import json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py'
def run(data,*args,ok=True):
 p=subprocess.run([sys.executable,'-B',str(CLI),'--data',str(data),*map(str,args)],cwd=ROOT,text=True,capture_output=True)
 if ok and p.returncode!=0:raise AssertionError(p.stdout+p.stderr)
 try:return json.loads(p.stdout)
 except Exception:raise AssertionError(p.stdout+p.stderr)

def prep(d):
 run(d,'init','--individual-id','V983-TEST')
 run(d,'heart-experience','vow','0.9','1','--theme','preserve_truth')
 run(d,'heart-experience','betrayal','-1','1','--theme','trust_boundary','--relation','peer')
 run(d,'soul-consolidate')

def test_v981_functional_fork_diverges_without_mutating_parent():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'data';prep(d);x=run(d,'soul-fork-assay')
  assert x['ok'];assert x['checks']['common_origin'];assert x['checks']['state_diverged'];assert x['checks']['choice_diverged'];assert x['checks']['parent_soul_unchanged'];assert not x['claim_boundary']['full_runtime_fork_divergence_tested']
  assert run(d,'soul-fork-audit')['ok'];assert run(d,'whole-audit')['ok']
  bp=d/'v981'/'branches'/'branch_discovery.json';q=json.loads(bp.read_text());q['bias']['curiosity']=0.0;bp.write_text(json.dumps(q))
  assert not run(d,'soul-fork-audit',ok=False)['ok'];assert not run(d,'whole-audit',ok=False)['ok']

def test_v982_checkpoint_survives_separate_process_and_blocks_drift():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'data';prep(d);run(d,'whole-sync');c=run(d,'continuity-checkpoint','--note','restart-boundary');assert c['ok']
  anchor=Path(td)/'external_anchor.json';run(d,'continuity-anchor-export','--out',anchor)
  assert run(d,'continuity-resume','--anchor-file',anchor)['ok']
  run(d,'heart-experience','discovery','1','1','--theme','new_fact')
  z=run(d,'continuity-resume',ok=False);assert not z['ok'];assert 'CURRENT_STATE_DIVERGED_FROM_CHECKPOINT' in z['errors']
  run(d,'continuity-checkpoint','--note','after-change');assert run(d,'continuity-resume')['ok']
  anchor2=Path(td)/'external_anchor2.json';run(d,'continuity-anchor-export','--out',anchor2);assert run(d,'continuity-audit','--anchor-file',anchor2)['ok']
  cp=d/'v982'/'checkpoints'/'00000002.json';q=json.loads(cp.read_text());q['payload']['note']='tampered';cp.write_text(json.dumps(q))
  assert not run(d,'continuity-audit','--anchor-file',anchor2,ok=False)['ok']

def test_v983_homeostasis_tracks_real_organism_and_is_high_level_only():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'data';prep(d);a=run(d,'homeostasis-assess');assert a['maintenance_intent']=='OBSERVE_AND_LEARN'
  run(d,'tick','100');b=run(d,'homeostasis-assess');assert b['maintenance_intent']=='PRIORITIZE_MAINTENANCE';assert b['needs']['maintenance_pressure']>0
  q=run(d,'homeostasis-audit');assert q['ok'];assert not q['claim_boundary']['direct_motor_override'];assert run(d,'whole-audit')['ok']
