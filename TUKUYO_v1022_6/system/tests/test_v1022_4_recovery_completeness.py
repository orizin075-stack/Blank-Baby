import json, shutil, tempfile
from pathlib import Path
import pytest
from test_v1019 import run
from test_v1019_1 import crash, fingerprint
from tukuyo_v1022 import meta_reasoning as meta
from tukuyo_v1022.meta_reasoning_verify import verify


def test_ninth_dependency_strategy_is_compared():
    q='。'.join(['A=1']*8+['A=2','G=A','Gは何?'])
    r=meta.solve(q)
    assert r['answer'] is None and r['reason']=='META_STRATEGY_CONFLICT'
    assert not verify(q,'1')['supported']


def test_overflow_never_reports_strategy_agreement():
    q='。'.join(['G=1']*32+['G=999','Gは何?'])
    r=meta.solve(q)
    assert r['answer'] is None and r['reason']=='META_SEARCH_INCOMPLETE'
    assert not r['search_complete'] and not verify(q,'1')['supported']


def test_depth_overflow_cannot_hide_conflicting_alternative():
    q='。'.join(['G=1','G=A0']+[f'A{i}=A{i+1}' for i in range(19)]+['A19=999','Gは何?'])
    assert meta.solve(q)['reason']=='META_SEARCH_INCOMPLETE'
    assert verify(q,'1')['reason']=='VERIFY_SEARCH_INCOMPLETE'


def test_checker_does_not_sample_eight_dependency_values():
    # The first eight numeric values make a zero product, the ninth conflicts.
    expr='*'.join(f'(A-{i})' for i in range(8))
    q='。'.join([f'A={i}' for i in range(9)]+[f'G={expr}','Gは何?'])
    assert meta.solve(q)['answer'] is None
    assert not verify(q,'0')['supported']


def test_checker_enforces_its_own_numeric_and_search_limits():
    assert not verify('A=100000000000000000000000000000000000。Aは何?','100000000000000000000000000000000000')['supported']
    q='。'.join([f'A={i}' for i in range(33)]+['G=A*0','Gは何?'])
    assert verify(q,'0')['reason']=='VERIFY_SEARCH_INCOMPLETE'


@pytest.mark.parametrize('damage',['stage_bytes','marker','missing_stage'])
def test_crashed_restore_never_replays_unverified_or_missing_afterimage(damage):
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'d';run(d,'init','--individual-id','RESTORE-INTEGRITY')
        run(d,'realtime-start');cp=run(d,'recovery-checkpoint')[0]
        run(d,'verified-query','8たす9は？')
        crash(d,'restore:after_txn_marker','recovery-restore',cp['path'])
        marker=d/'v1014/private/RESTORE_TXN.json';tx=json.loads(marker.read_text())
        stage=d.parent/tx['stage_dir']/'stage'
        if damage=='stage_bytes':(stage/'v977/SOUL_CORE.json').write_text('{}')
        elif damage=='marker':
            tx['files']=[];marker.write_text(json.dumps(tx))
        else:shutil.rmtree(stage.parent)
        before=fingerprint(d)
        r=run(d,'whole-audit',ok=False)[0]
        expected={'stage_bytes':'RESTORE_STAGE_HASH','marker':'RESTORE_TXN_AUTHENTICATION','missing_stage':'RESTORE_STAGE_MISSING'}[damage]
        assert expected in r['error'],r
        assert marker.is_file() and fingerprint(d)==before


def test_explicit_restore_recovers_damaged_nested_runtime_without_live_preflight():
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'d';run(d,'init','--individual-id','RESTORE-CHILD')
        run(d,'metabolism-init','--families','2','--no-actions','--reservoir','0')
        run(d,'realtime-start');cp=run(d,'recovery-checkpoint')[0]
        p=d/'v1022_ecology/runtimes/R000000/v978/HEART_STATE.json';p.write_text('{}')
        before=fingerprint(d)
        assert run(d,'recovery-restore',cp['path'],'--trust-file',d/'v1014/recovery.pub','--dry-run')[0]['ok']
        assert fingerprint(d)==before
        assert run(d,'recovery-restore',cp['path'],'--trust-file',d/'v1014/recovery.pub')[0]['ok']
        assert run(d,'metabolism-audit')[0]['ok'] and run(d,'whole-audit')[0]['ok']


def test_owner_transaction_does_not_waive_child_whole_anchor():
    from tukuyo_v1022 import metabolism, cognition, store
    from tukuyo_v1019.transaction import ACTIVE
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'d';run(d,'init','--individual-id','ANCHOR-OWNER')
        run(d,'metabolism-init','--families','2','--no-learning')
        p=metabolism.child(d,'R000000')
        whole_file=p/'v977/UNIFIED_STATE.json';old=whole_file.read_bytes()
        # A blank founder has no learner journal in its signed head. Adding a
        # legitimate learner commit then restoring that head tests omission.
        s=cognition.state(p);store.save(p,cognition.NS,cognition.COMPONENT,s)
        whole_file.write_bytes(old)
        token=ACTIVE.set(True)
        try:
            with pytest.raises(ValueError,match='V1022_CHILD_AUDIT'):metabolism._snapshot(d,'R000000')
        finally:ACTIVE.reset(token)


def test_multigeneration_restore_then_new_process_resume():
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'d';run(d,'init','--individual-id','RESTORE-GEN3')
        run(d,'metabolism-init','--families','2','--reservoir','100000','--regeneration','1800','--max-age','4')
        s=run(d,'metabolism-step','--ticks','12')[0]
        assert s['max_generation']==3 and s['total_runtime_count']==8
        run(d,'realtime-start');cp=run(d,'recovery-checkpoint')[0]
        keys={p.relative_to(d):p.read_bytes() for p in d.rglob('*.key')}
        for _ in range(3):
            future=run(d,'metabolism-step','--ticks','4')[0]
            assert future['max_generation']==4
            run(d,'recovery-restore',cp['path'],'--trust-file',d/'v1014/recovery.pub')
            assert run(d,'metabolism-audit')[0]['tick']==12
            assert run(d,'whole-audit')[0]['ok']
            assert all((d/k).read_bytes()==v for k,v in keys.items())
            assert len(list((d/'v1022_ecology/runtimes').iterdir()))==8
        quarantined=list((d/'v1014/private/retired_runtimes').rglob('succession.key'))
        assert len(quarantined)==6
        assert len({p.read_bytes() for p in quarantined})==6
        assert run(d,'metabolism-step','--ticks','1')[0]['tick']==13


def test_runtime_rebind_requires_previous_pin_and_preserves_individual_keys():
    import os
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'d';run(d,'init','--individual-id','REBIND')
        run(d,'metabolism-init','--families','2','--no-actions')
        pin=d/'v1022_ecology/RUNTIME_TRUST.txt'
        previous=Path(t)/'old.pub';previous.write_text('OLD-PUBLIC-PIN')
        before=fingerprint(d)
        assert 'PREVIOUS_PIN_MISMATCH' in run(d,'runtime-trust-rebind','--previous-trust-file',previous,ok=False)[0]['error']
        assert fingerprint(d)==before
        keys={p.relative_to(d):p.read_bytes() for p in d.rglob('*.key')}
        pin.write_bytes(previous.read_bytes())
        r=run(d,'runtime-trust-rebind','--previous-trust-file',previous)[0]
        assert r['updated_forests']==['v1022_ecology']
        assert pin.read_text().strip()==Path(os.environ['TUKUYO_TEST_RUNTIME_ANCHOR']).read_text().strip()
        assert all((d/k).read_bytes()==v for k,v in keys.items())
        assert run(d,'metabolism-step','--ticks','1')[0]['ok']


def test_explicit_checkpoint_supersedes_future_prepared_lineage_redo():
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'d';run(d,'init','--individual-id','DISCARD-FUTURE-REDO')
        run(d,'realtime-start');cp=run(d,'recovery-checkpoint')[0]
        baseline={k:v for k,v in fingerprint(d).items() if k.startswith('v1019/')}
        crash(d,'lineage:after_prepare','evolution-select','resource')
        assert (d/'.lineage_transaction/PREPARED.json').is_file()
        run(d,'recovery-restore',cp['path'])
        assert not (d/'.lineage_transaction').exists()
        for _ in range(3):assert run(d,'whole-audit')[0]['ok']
        assert {k:v for k,v in fingerprint(d).items() if k.startswith('v1019/')}==baseline


def test_restore_verifies_deletion_even_if_io_reports_success(monkeypatch):
    from tukuyo_v1014 import recovery
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'d';run(d,'init','--individual-id','DELETE-READBACK')
        run(d,'realtime-start');cp=run(d,'recovery-checkpoint')[0]
        extra=d/'FUTURE_BYTES.json';extra.write_text('{}')
        original=recovery.durable_unlink;seen=[]
        def interrupted_unlink(p):
            if p.name==extra.name:
                seen.append(p)
                if len(seen)==1:return True
            return original(p)
        monkeypatch.setattr(recovery,'durable_unlink',interrupted_unlink)
        assert recovery.restore(d,cp['path'])['ok']
        assert len(seen)==2 and not extra.exists()


def test_historical_seed_key_is_explicitly_pinned_and_signature_checked():
    from tukuyo_v1022 import cognition,store
    from tukuyo_v977 import whole_state
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    import base64
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'d';run(d,'init','--individual-id','SEED-TRUST')
        s=cognition.state(d);seed=s['seed_provenance']
        # A valid signature under an arbitrary new key is not historical trust.
        key=Ed25519PrivateKey.generate()
        seed['public_key']=base64.b64encode(key.public_key().public_bytes_raw()).decode()
        seed['signature']=base64.b64encode(key.sign(whole_state.canon(seed['payload']))).decode()
        store.save(d,cognition.NS,cognition.COMPONENT,s)
        assert cognition.audit(d)['errors']==['V1022_SEED_SIGNATURE']


def test_gate_distinguishes_actual_keys_from_disposable_stage_copies():
    import importlib.util
    script=Path(__file__).resolve().parents[1]/'tools/recovery_stress.py'
    spec=importlib.util.spec_from_file_location('recovery_gate',script)
    gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)
        for name in ['v977/private/whole_state.key','v1022_ecology/runtimes/R000000/v1018/private/succession.key',
                     '.lineage_transaction/work-old/v977/private/whole_state.key',
                     'v1014/private/retired_runtimes/rc-old/v1022_ecology/R000004/v1018/private/succession.key']:
            p=d/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('generated-test-key')
        assert set(gate.key_hashes(d))=={'v977/private/whole_state.key','v1022_ecology/runtimes/R000000/v1018/private/succession.key'}


@pytest.mark.parametrize('point',['restore:before_namespace_swap','restore:mid_commit','restore:after_namespace_swap'])
def test_namespace_swap_resumes_before_between_and_after_renames(point):
    from tukuyo_v1014.recovery import _swap_marker
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'d';run(d,'init','--individual-id','DIRECTORY-SWAP')
        run(d,'realtime-start');cp=run(d,'recovery-checkpoint')[0]
        old_inode=d.stat().st_ino
        run(d,'verified-query','8たす9は？')
        crash(d,point,'recovery-restore',cp['path'])
        assert _swap_marker(d).is_file()
        if point=='restore:mid_commit':assert not d.exists()
        assert run(d,'whole-audit')[0]['ok']
        assert d.stat().st_ino!=old_inode
        assert not _swap_marker(d).exists()
        assert not (d/'v1005/LAST_VERIFIED_REASONING.json').exists()


def test_namespace_sidecar_cannot_authorize_modified_image_hashes():
    from tukuyo_v1014.recovery import _swap_marker
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'d';run(d,'init','--individual-id','DIRECTORY-AUTH')
        run(d,'realtime-start');cp=run(d,'recovery-checkpoint')[0]
        crash(d,'restore:before_namespace_swap','recovery-restore',cp['path'])
        marker=_swap_marker(d);control=json.loads(marker.read_text())
        control['body']['image_file_hashes']['v977/SOUL_CORE.json']='0'*64
        marker.write_text(json.dumps(control))
        before=fingerprint(d)
        r=run(d,'whole-audit',ok=False)[0]
        assert 'RESTORE_SWAP_AUTHENTICATION' in r['error']
        assert fingerprint(d)==before and marker.exists()


def test_matching_symlink_image_cannot_redirect_the_live_root():
    from tukuyo_v1014.recovery import _swap_marker
    with tempfile.TemporaryDirectory() as t:
        td=Path(t);d=td/'d';run(d,'init','--individual-id','IMAGE-ROOT-LINK')
        run(d,'realtime-start');cp=run(d,'recovery-checkpoint')[0]
        crash(d,'restore:before_namespace_swap','recovery-restore',cp['path'])
        control=json.loads(_swap_marker(d).read_text())
        image=td/control['body']['transaction']['stage_dir']/'live';foreign=td/'foreign-image'
        image.rename(foreign);image.symlink_to(foreign,target_is_directory=True)
        before=fingerprint(d);foreign_before=fingerprint(foreign)
        r=run(d,'whole-audit',ok=False)[0]
        assert 'RESTORE_IMAGE_ROOT_SYMLINK' in r['error']
        assert not d.is_symlink() and fingerprint(d)==before
        assert fingerprint(foreign)==foreign_before and _swap_marker(d).exists()


@pytest.mark.parametrize('damage',['missing','partial','backup_partial'])
def test_verified_published_root_does_not_require_disposable_image(damage):
    from tukuyo_v1014 import recovery
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'d';run(d,'init','--individual-id','PUBLISHED-AFTERIMAGE')
        run(d,'realtime-start');cp=run(d,'recovery-checkpoint')[0]
        crash(d,'restore:after_namespace_swap','recovery-restore',cp['path'])
        control=json.loads(recovery._swap_marker(d).read_text());stage=d.parent/control['body']['transaction']['stage_dir']
        if damage=='missing':shutil.rmtree(stage)
        elif damage=='partial':
            image=stage/'live';image.mkdir();(image/'INVALID.json').write_text('{}')
        else:(d.parent/control['body']['backup_dir']/'v1014/recovery.pub').unlink()
        before=fingerprint(d)
        result=recovery.recover_incomplete_restore(d)
        assert result['already_published_afterimage_verified']
        after=fingerprint(d);assert all(after[k]==v for k,v in before.items())
        assert set(after)-set(before)=={recovery._completion_path(d,control).relative_to(d).as_posix()}
        assert not recovery._swap_marker(d).exists() and not stage.exists()
        assert run(d,'whole-audit')[0]['ok']


@pytest.mark.parametrize('tamper',[False,True])
def test_completed_restore_marker_replay_cannot_undo_later_operation(tamper):
    from tukuyo_v1014 import recovery
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'d';run(d,'init','--individual-id','COMPLETED-REPLAY')
        run(d,'realtime-start');cp=run(d,'recovery-checkpoint')[0]
        crash(d,'restore:after_namespace_swap','recovery-restore',cp['path'])
        marker=recovery._swap_marker(d);raw=marker.read_bytes();control=json.loads(raw)
        assert run(d,'whole-audit')[0]['ok'] and not marker.exists()
        run(d,'verified-query','8たす9は？')
        assert (d/'v1005/LAST_VERIFIED_REASONING.json').is_file()
        marker.write_bytes(raw)
        if tamper:
            p=recovery._completion_path(d,control);ack=json.loads(p.read_text());ack['body']['control_sha256']='0'*64;p.write_text(json.dumps(ack))
        before=fingerprint(d)
        if tamper:
            with pytest.raises(ValueError,match='RESTORE_COMPLETION_AUTHENTICATION'):recovery.recover_incomplete_restore(d)
            assert marker.exists()
        else:
            assert recovery.recover_incomplete_restore(d)['previously_completed_restore']
            assert not marker.exists()
        assert fingerprint(d)==before
