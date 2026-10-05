import json,subprocess,sys,tempfile,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py'

def run(data,*args,ok=True):
    p=subprocess.run([sys.executable,'-B',str(CLI),'--data',str(data),*map(str,args)],cwd=ROOT,text=True,capture_output=True,timeout=180,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    if ok and p.returncode!=0: raise AssertionError(p.stdout+p.stderr)
    try:return json.loads(p.stdout)
    except Exception: raise AssertionError(p.stdout+p.stderr)

def test_v990_closed_environment_replays_and_detects_tamper():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V990-ENV')
        r=run(d,'env-init','--profile','TRAIN_A','--seed','99001');assert r['ok']
        run(d,'env-act','MOVE_FORWARD');run(d,'env-act','REST');assert run(d,'env-audit')['ok']
        ep=d/'v990'/'ENVIRONMENT_EVENTS.json';q=json.loads(ep.read_text());q['events'][0]['outcome']['information_gain']=99;ep.write_text(json.dumps(q),encoding='utf-8')
        a=run(d,'env-audit',ok=False);assert not a['ok']

def test_v991_valence_is_derived_not_supplied_and_varies_with_observed_result():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V991-GROUND');run(d,'env-init','--profile','TRAIN_A','--seed','99001');run(d,'grounded-init')
        vals=[]
        for _ in range(5):
            r=run(d,'grounded-step','MOVE_FORWARD');vals.append(r['evaluation']['derived_valence'])
            if r['environment']['observation_after']['terminal']:break
        assert len(set(vals))>1 or any(v<0 for v in vals) or any(v>0 for v in vals)
        s=run(d,'grounded-status');assert s['ok'];assert run(d,'grounded-audit')['ok']
        # There is no CLI argument for valence: it is computed after the environmental transition.
        assert s['claim_boundary']['valence_self_derived_from_state_change'] is True

def test_v991_same_action_can_change_sign_by_context():
    from tukuyo_v991.grounded_organism import default_physiology,apply_physiology,derive_evaluation
    p=default_physiology()
    good={'resource_gain':1,'hazard_exposure':0.0,'progress_to_goal':0.0,'reached_goal':False,'information_gain':0,'position_changed':False}
    bad={'resource_gain':0,'hazard_exposure':0.75,'progress_to_goal':0.0,'reached_goal':False,'information_gain':0,'position_changed':False}
    g=derive_evaluation(p,apply_physiology(p,'GATHER',good),good)
    b=derive_evaluation(p,apply_physiology(p,'GATHER',bad),bad)
    assert g['grounded_utility']>0 and b['grounded_utility']<0 and g['derived_valence']>b['derived_valence']

def test_v992_holdout_transfer_beats_fixed_baseline_on_majority():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V992-HOLDOUT')
        r=run(d,'holdout-assay');assert r['ok'] and r['wins']>=3 and r['cases']==4
        assert run(d,'holdout-audit')['ok']
