import json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py'
sys.path.insert(0,str(ROOT/'src'))
from tukuyo_v978.heart_loop import process_experience
from tukuyo_v977.whole_state import sync as whole_sync
from tukuyo_v983.homeostasis import assess as homeostasis_assess


def run(data,*args,ok=True):
    p=subprocess.run([sys.executable,'-B',str(CLI),'--data',str(data),*map(str,args)],cwd=ROOT,text=True,capture_output=True,timeout=180)
    if ok and p.returncode!=0:raise AssertionError(p.stdout+p.stderr)
    try:return json.loads(p.stdout)
    except Exception:raise AssertionError(p.stdout+p.stderr)


def test_v984_full_runtime_fork_uses_separate_processes_and_diverges_whole_state():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V984-TEST')
        x=run(d,'full-runtime-fork-assay')
        assert x['ok'];c=x['checks']
        assert c['common_origin_snapshot'] and c['separate_processes_executed'] and c['both_whole_audits_pass']
        assert c['whole_state_diverged'] and c['organism_state_diverged'] and c['heart_state_diverged'] and c['soul_state_diverged']
        assert c['choice_diverged'] and c['homeostasis_intent_diverged']
        assert x['claim_boundary']['bounded_full_runtime_fork_divergence_tested']
        assert run(d,'full-runtime-fork-audit')['ok'];assert run(d,'whole-audit')['ok']
        rp=d/'v984'/'FULL_RUNTIME_FORK_ASSAY.json';q=json.loads(rp.read_text());q['checks']['choice_diverged']=False;rp.write_text(json.dumps(q))
        assert not run(d,'full-runtime-fork-audit',ok=False)['ok']
        assert not run(d,'whole-audit',ok=False)['ok']


def test_v985_experience_meaning_purpose_loop_revises_from_accumulated_evidence():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V985-TEST')
        for i in range(12):process_experience(d,'discovery',1.0,1.0,f'unknown_{i%3}','')
        homeostasis_assess(d);whole_sync(d)
        a=run(d,'purpose-integrate');assert a['ok'];assert a['active_purpose']=='SEEK_KNOWLEDGE';assert a['claim_boundary']['experience_to_meaning_to_purpose_loop']
        for i in range(7):process_experience(d,'betrayal',-1.0,1.0,f'trust_{i%2}','peer')
        # Deplete the organism to make maintenance evidence real rather than synthetic metadata.
        run(d,'tick','100');homeostasis_assess(d);whole_sync(d)
        b=run(d,'purpose-integrate');assert b['ok'];assert b['active_purpose']!='SEEK_KNOWLEDGE';assert b['revision_count']>=1
        s=run(d,'purpose-status');assert s['ok'] and not s['stale_sources'];assert run(d,'purpose-audit')['ok'];assert run(d,'whole-audit')['ok']
        sp=d/'v985'/'NARRATIVE_PURPOSE_STATE.json';q=json.loads(sp.read_text());q['active_purpose']='SEEK_KNOWLEDGE';sp.write_text(json.dumps(q))
        assert not run(d,'purpose-audit',ok=False)['ok'];assert not run(d,'whole-audit',ok=False)['ok']
