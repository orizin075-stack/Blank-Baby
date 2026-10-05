import concurrent.futures,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
from test_v1019 import run,init
from test_v1019_1 import fingerprint
from tukuyo_v1012.core_reasoning import reason
from tukuyo_v1014_1.semantic_verifier import verify_bounded_semantics
from tukuyo_v1021 import runtime_bridge as bridge

def test_package_event_polarity_units_and_signed_counts():
    cases=[
        ('3個食べていません','32'),('3個食べなかった','32'),
        ('3個捨てていません','32'),('3個渡しませんでした','32'),
        ('2箱返却しました','16'),('2個使ってから1箱使った','22'),
        ('2個食べ、3個捨てました','27'),('1箱開けました','32'),
        ('もし3個食べれば','29')]
    for clause,expected in cases:
        query='1箱に8個入りが4箱あります。'+clause+'。残りは何個？'
        r=reason(query);v=verify_bounded_semantics(query,r.get('answer'))
        assert r['ok'] and r['answer']==expected and v['supported'],(query,r,v)
    for clause,question in [
        ('-3個使いました','残りは何個？'),('3個食べる予定です','残りは何個？'),
        ('3個食べたかどうか不明です','残りは何個？'),('3個食べないとは言えない','残りは何個？'),
        ('','全部で何円？'),('','全部で何kg？')]:
        query='1箱に8個入りが4箱あります。'+clause+'。'+question
        assert not reason(query)['ok']
        assert not verify_bounded_semantics(query,'29')['decidable']

def test_polarity_transfers_to_other_counts_and_container_units():
    for unit,container,per,count,used in [('枚','袋',9,5,4),('本','ケース',7,6,5),('個','パック',11,3,2)]:
        for neg in ['食べていません','捨てなかった','渡しませんでした']:
            query=f'{per}{unit}入りの{container}を{count}{container}。{used}{unit}{neg}。残りは何{unit}？'
            r=reason(query);assert r['answer']==str(per*count)
            assert verify_bounded_semantics(query,r['answer'])['supported']

def test_evolution_prefix_cannot_be_reauthorized_by_any_cli_command():
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'P';init(d,'P');run(d,'evolution-select','research','--seed','old')
        old=(d/'v1019/EVOLUTION_STATE.json').read_bytes()
        names={p.name for p in (d/'v1019/commits').glob('*.json')}
        run(d,'evolution-select','social','--seed','new')
        for p in (d/'v1019/commits').glob('*.json'):
            if p.name not in names:p.unlink()
        for missing in [False,True]:
            if missing:(d/'v1019/EVOLUTION_STATE.json').unlink()
            else:(d/'v1019/EVOLUTION_STATE.json').write_bytes(old)
            before=fingerprint(d)
            for args in [('evolution-select','volatile'),('whole-sync',),('evolution-audit',)]:
                r,_=run(d,*args,ok=False)
                assert 'V1019_RECOVERY_HEAD' in r['error'] and fingerprint(d)==before

def test_cli_locks_startup_reads_and_updates_on_same_runtime():
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'P';init(d,'P');run(d,'population-init','--regeneration','240000')
        def worker(i):
            for j in range(4):
                if i%2:run(d,'population-status')
                run(d,'population-step','resource')
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            list(ex.map(worker,range(4)))
        assert run(d,'population-status')[0]['summary']['tick']==16
        assert run(d,'whole-audit')[0]['ok']

def test_abandoned_stage_cleanup_cannot_reuse_or_block_live_runtime():
    from unittest.mock import patch
    from tukuyo_v1019 import transaction as tx,evolution as ev
    from tukuyo_v977 import whole_state as whole
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'P';init(d,'P')
        # Preserve a stale copy carrying a conflicting identity. A failed
        # cleanup must leave it unused, rather than resume it as work.
        stale=d/tx.TAG/'work';shutil.copytree(d,stale,ignore=shutil.ignore_patterns(tx.TAG))
        marker=stale/'uncommitted-sentinel';marker.write_text('must-never-be-committed')
        real=shutil.rmtree
        def stalled(path,*args,**kw):
            if Path(path)==d/tx.TAG:
                if kw.get('ignore_errors'):return
                raise OSError(39,'Directory not empty',str(path))
            return real(path,*args,**kw)
        with patch.object(tx.shutil,'rmtree',side_effect=stalled):
            assert tx.recover(d)['cleanup_pending']
            r=ev.select(d,'research',seed='cleanup')
            assert r['ok'] and whole.audit(d)['ok']
            assert marker.exists() and not (d/'uncommitted-sentinel').exists()
            assert len(list((d/tx.TAG).glob('work-*')))==1

def setup_bridge(td,families=4):
    d=Path(td)/'owner';init(d,'BRIDGE')
    run(d,'runtime-ecology-init','--families',str(families))
    return d

def test_runtime_bridge_independent_keys_mortality_and_exact_recovery():
    with tempfile.TemporaryDirectory() as t:
        d=setup_bridge(t);initial=run(d,'runtime-ecology-status')[0]
        assert initial['active_runtime_count']==4
        old_soul={rid:r['soul_sha256'] for rid,r in initial['runtimes'].items()}
        r,_=run(d,'runtime-ecology-step','resource','--ticks','12')
        assert r['actual_successions']>=4 and r['max_actual_generation']>=1
        rows=list(r['runtimes'].values())
        assert len({x['succession_public_key'] for x in rows})==len(rows)
        assert len({x['whole_public_key'] for x in rows})==len(rows)
        assert sum(x['lifecycle']=='DEAD' for x in rows)>=4
        assert any(r['runtimes'][rid]['soul_sha256']!=h for rid,h in old_soul.items())
        assert run(d,'whole-audit')[0]['ok']
        before=fingerprint(d);run(d,'population-step','resource',ok=False);assert fingerprint(d)==before
        cached=bridge.state_path(d).read_bytes();bridge.state_path(d).unlink()
        run(d,'runtime-ecology-audit');assert bridge.state_path(d).read_bytes()==cached

def test_bridge_partial_rollback_and_child_drift_are_not_resigned():
    with tempfile.TemporaryDirectory() as t:
        d=setup_bridge(t,2);old=bridge.state_path(d).read_bytes()
        run(d,'runtime-ecology-step','resource','--ticks','1')
        for p in (bridge.root(d)/'commits').glob('*.json'):
            if int(p.stem)>1:p.unlink()
        bridge.state_path(d).write_bytes(old);before=fingerprint(d)
        r,_=run(d,'runtime-ecology-step','resource',ok=False)
        assert 'V1021_RECOVERY_HEAD' in r['error'] and fingerprint(d)==before
    with tempfile.TemporaryDirectory() as t:
        d=setup_bridge(t,2);p=bridge.root(d)/'runtimes/R000000/v978/HEART_STATE.json'
        x=json.loads(p.read_text());x['UNAUTHORIZED_FIELD']=True;p.write_text(json.dumps(x))
        before=fingerprint(d);run(d,'runtime-ecology-step','resource',ok=False);assert fingerprint(d)==before

def test_explicit_cache_recovery_requires_current_signed_head_and_valid_children():
    with tempfile.TemporaryDirectory() as t:
        d=setup_bridge(t,2);old=bridge.state_path(d).read_bytes()
        run(d,'runtime-ecology-step','resource','--ticks','2')
        latest=bridge.state_path(d).read_bytes();whole=(d/'v977/UNIFIED_STATE.json').read_bytes()
        bridge.state_path(d).write_bytes(old);before=fingerprint(d)
        run(d,'runtime-ecology-audit',ok=False);assert fingerprint(d)==before
        restored,_=run(d,'runtime-ecology-recover-cache')
        assert restored['tick']==2 and restored['cache_recovery']['whole_preserved']
        assert bridge.state_path(d).read_bytes()==latest and (d/'v977/UNIFIED_STATE.json').read_bytes()==whole
        bridge.state_path(d).write_text('not-json')
        run(d,'runtime-ecology-recover-cache')
        assert bridge.state_path(d).read_bytes()==latest and (d/'v977/UNIFIED_STATE.json').read_bytes()==whole
        # Coherently old cache+journal must never be accepted by recovery.
        for p in (bridge.root(d)/'commits').glob('*.json'):
            if int(p.stem)>1:p.unlink()
        bridge.state_path(d).write_bytes(old);before=fingerprint(d)
        r,_=run(d,'runtime-ecology-recover-cache',ok=False)
        assert 'V1021_RECOVERY_HEAD' in r['error'] and fingerprint(d)==before
    with tempfile.TemporaryDirectory() as t:
        d=setup_bridge(t,2);run(d,'runtime-ecology-step','resource')
        bridge.state_path(d).write_text('{}')
        p=bridge.root(d)/'runtimes/R000000/v978/HEART_STATE.json';p.write_text('{}')
        before=fingerprint(d);run(d,'runtime-ecology-recover-cache',ok=False);assert fingerprint(d)==before

def test_bridge_sigkill_before_prepare_and_prepared_redo():
    root=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as t:
        td=Path(t);initial=setup_bridge(td/'initial',2)
        for point in ['bridge:after_parent_death','bridge:after_import','lineage:after_prepare']:
            d=td/point.replace(':','_');shutil.copytree(initial,d);before=fingerprint(d)
            command=[sys.executable,'-B',str(root/'run_tukuyo.py'),'--data',str(d)]
            command+=['--runtime-trust-file',os.environ['TUKUYO_TEST_RUNTIME_ANCHOR']]
            command+=['runtime-ecology-step','resource','--ticks','8']
            p=subprocess.run(command,env={**os.environ,'TUKUYO_CRASH_POINT':point},capture_output=True,text=True,timeout=180)
            assert p.returncode==-9,(point,p.stdout,p.stderr)
            r,_=run(d,'runtime-ecology-audit');assert r['ok']
            if point.startswith('bridge:'):assert fingerprint(d)==before and r['actual_successions']==0
            else:assert r['tick']==8 and r['actual_successions']==2
