from pathlib import Path
import json, os, subprocess, sys, tempfile
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'run_tukuyo.py'

def run(d,*args,ok=True,env=None):
    e={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT/'src')};e.update(env or {})
    cmd=[sys.executable,'-B',str(RUN)]
    anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if anchor:cmd += ['--runtime-trust-file',anchor]
    cmd += ['--data',str(d),*map(str,args)]
    p=subprocess.run(cmd,cwd=ROOT,env=e,text=True,capture_output=True,timeout=180)
    if p.stdout.strip():
        try:r=json.loads(p.stdout)
        except Exception:raise AssertionError('bad json\n'+p.stdout+'\n'+p.stderr)
    else:
        r={}
    if ok and (p.returncode!=0 or not r.get('ok',False)):raise AssertionError(p.stdout+p.stderr)
    return r,p.returncode

def test_living_episode_causal_chain():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','V1015-EP')
        r,_=run(d,'living-episode','discovery','.9','.8','--theme','unknown_domain','--relation','mentor-A','--query','1袋に8枚入りが3袋。全部で何枚？')
        assert r['causal_checks']['experience_created_meaning'] and r['causal_checks']['action_selected'] and r['whole_audit_ok']
        a,_=run(d,'living-continuity-audit');assert a['ok'] and a['completed_episodes']==1 and a['functional_living_continuity_core_pass'],a
        w,_=run(d,'whole-audit');assert w['ok'],w

def test_living_history_continues_across_fresh_processes():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','V1015-RST')
        run(d,'living-episode','vow','1','.9','--theme','preserve_truth','--query','3たす4は？')
        run(d,'living-episode','support','.8','.7','--theme','cooperation','--relation','peer-A','--query','6個入りパックを5つ。全部で何個？')
        s,_=run(d,'living-continuity-status');a=s['audit'];assert a['completed_episodes']==2 and a['process_instances']>=2 and a['ok'],s

def test_interrupted_episode_is_recovered_and_history_remains_auditable():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','V1015-CRASH')
        _,rc=run(d,'living-episode','learning','.8','.9','--theme','atomic_life','--query','3たす4は？',ok=False,env={'TUKUYO_CRASH_POINT':'v1015:after_experience'})
        assert rc!=0
        a,_=run(d,'living-continuity-audit');assert a['ok'] and a['interrupted_episodes']==1 and not a['pending_episode'],a
        r,_=run(d,'living-episode','discovery','.7','.6','--theme','after_restart','--query','3たす4は？');assert r['ok'],r
        a2,_=run(d,'living-continuity-audit');assert a2['completed_episodes']==1 and a2['interrupted_episodes']==1 and a2['ok'],a2

def test_event_file_commit_crash_repairs_head_without_duplicate():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','V1015-HEAD')
        _,rc=run(d,'living-episode','discovery','.7','.7','--theme','head_repair','--query','3たす4は？',ok=False,env={'TUKUYO_CRASH_POINT':'v1015:after_event_file'})
        assert rc!=0
        a,_=run(d,'living-continuity-audit');assert a['ok'] and a['completed_episodes']==1 and a['events']==1 and not a['pending_episode'],a

def test_gate_assay_passes_functional_core_but_not_electronic_life_gate():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','V1015-GATE')
        r,_=run(d,'living-gate-assay');assert r['ok'] and r['episodes']==5,r
        g,_=run(d,'living-gate-audit');assert g['ok'] and g['functional_living_continuity_gate']=='PASS',g
        assert g['electronic_life_gate']=='PENDING' and not g['claim_boundary']['electronic_life_gate_complete'] and not g['duration']['7day_completed'],g
        m,_=run(d,'memory-compact-audit');assert m['ok'],m

def test_living_history_tamper_is_detected():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','V1015-TAMPER')
        run(d,'living-episode','discovery','.8','.8','--theme','tamper_probe','--query','3たす4は？')
        p=d/'v1015/events/00000001.json';x=json.loads(p.read_text(encoding='utf-8'));x['detail']['spec']['theme']='rewritten';p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf-8')
        a,rc=run(d,'living-continuity-audit',ok=False);assert rc!=0 and not a['ok'] and any('V1015_' in e for e in a['errors']),a
