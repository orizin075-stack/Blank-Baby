import json,os,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py'

def run(d,*a,ok=True):
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    cmd=[sys.executable,'-B',str(CLI)]
    if anchor: cmd += ['--runtime-trust-file',anchor]
    cmd += ['--data',str(d),*map(str,a)]
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,env=env,timeout=240)
    try:r=json.loads(p.stdout)
    except Exception:raise AssertionError(p.stdout+p.stderr)
    if ok and (p.returncode or not r.get('ok',False)):raise AssertionError(p.stdout+p.stderr)
    return r

def test_v1009_mixed_history_stress_and_fresh_process_reopen():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','V1009-LONG')
        r=run(d,'long-life-assay','--cycles','1')
        assert r['ok'] and r['transition_delta']>=6 and r['end_lifecycle']!='DEAD'
        assert all(r['checks'].values())
        # run() always launches a fresh Python process, so this is a true reopen/audit.
        a=run(d,'long-life-audit');assert a['ok'] and a['historical_assay_preserved']
        assert run(d,'whole-audit')['ok']

def test_v1009_future_lawful_growth_does_not_invalidate_historical_assay():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','V1009-GROW')
        run(d,'long-life-assay','--cycles','0')
        run(d,'heart-experience','discovery','1','.7','--theme','later_growth')
        a=run(d,'long-life-audit');assert a['ok'] and a['historical_assay_preserved']

def test_v1009_history_truncation_is_detected():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','V1009-TAMPER')
        run(d,'long-life-assay','--cycles','0')
        # the chain is an append-only journal (one transition per line): drop the last transition
        p=d/'v989'/'SOUL_TRANSITIONS.jsonl';ls=p.read_text().splitlines();p.write_text(''.join(x+'\n' for x in ls[:-1]),encoding='utf-8')
        a=run(d,'long-life-audit',ok=False);assert not a['ok']
