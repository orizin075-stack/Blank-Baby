"""Public regressions for uncertain event scope and late restored-file drift."""
import copy
from pathlib import Path
import pytest
from test_v1022_5_fusion import run
from tukuyo_v1022 import cognition, proofs, semantic_coverage
from tukuyo_v1014_1.semantic_verifier import verify_bounded_semantics


@pytest.mark.parametrize('event', [
    '3個食べたわけではありません', '3個食べたわけじゃありません',
    '3個食べなかったわけではありません。実際に何個食べたかは不明です',
    '3個食べたとは限りません', '3個食べたかは分かりません',
    '3個食べたと断定できません', '食べた個数は未確認です',
])
def test_uncertain_event_cannot_be_committed_or_rescued(tmp_path, event):
    d=tmp_path/'data';run(d,'init','--individual-id','SCOPE-74')
    q=f'りんごが10個あります。{event}。残りは何個？'
    for command in ('think','verified-query'):
        r=run(d,command,q)
        assert r['uncertain'], (q,command,r)
    for bad in ('7','10'):
        v=verify_bounded_semantics(q,bad)
        assert not v['decidable'] and not v['supported'],v


@pytest.mark.parametrize('event,expected', [
    ('3個食べました','7'), ('3個食べていません','10'),
    ('3個食べなかった','10'), ('明日3個食べる予定です','10'),
    ('3個食べました。2個もらいました','9'),
])
def test_plain_inventory_has_independent_complete_input_binding(tmp_path,event,expected):
    d=tmp_path/'data';run(d,'init','--individual-id','PLAIN-74')
    q=f'りんごが10個あります。{event}。残りは何個？'
    for command in ('think','verified-query'):
        r=run(d,command,q)
        assert not r['uncertain'] and r['answer']==expected,r
        coverage=r['verification_evidence']['input_coverage']
        assert coverage['recognized'] and coverage['ok'] and coverage['graph']
        assert proofs.check(r['proof'],expected)
        p=copy.deepcopy(r['proof']);p['source_query']=q.replace('10個','11個')
        assert not proofs.check(p,expected)


def test_unknown_numeric_free_clause_is_not_a_question():
    r=cognition.inventory('りんごが10個あります。実際に何個食べたかは不明です。残りは何個？',
                          {'event_rules':{},'aliases':{}})
    assert r['uncertain']


@pytest.mark.parametrize('query,expected',[
    ('午後1時50分から1時間25分後は何時何分？','午後3時15分'),
    ('昨日は12個ありました。今日は昨日より3個少ない。今日は何個？','9'),
    ('りんごが12個あります。妹に5個あげました。残りは何個ですか？','7'),
])
def test_scope_guard_preserves_temporal_and_recipient_readings(tmp_path,query,expected):
    d=tmp_path/'data';run(d,'init','--individual-id','SCOPE-POSITIVE-74')
    for command in ('think','verified-query'):
        r=run(d,command,query)
        assert not r['uncertain'] and r['answer']==expected,r


def test_quantity_checker_does_not_import_producer():
    import ast
    tree=ast.parse(Path(semantic_coverage.__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node,ast.ImportFrom):assert not (node.module or '').startswith('tukuyo')
        if isinstance(node,ast.Import):assert all(not x.name.startswith('tukuyo') for x in node.names)


def test_whole_audit_rechecks_late_frontier_extras(tmp_path,monkeypatch):
    from test_v1022_7_3_restore_frontier import setup
    from tukuyo_v977 import whole_state as whole
    d=tmp_path/'data';setup(d);old=whole._audit_once;calls=[]
    p=d/'v1022_ecology/commits/000000000999.json'
    def external_late_write(data):
        if not calls:
            p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{"future":true}')
            calls.append(True)
            return {'ok':False,'errors':['SIMULATED_LATE_EXTRA']}
        return old(data)
    monkeypatch.setattr(whole,'_audit_once',external_late_write)
    result=whole.audit(d)
    assert result['ok'] and not p.exists(),result
    assert list((d/'v1014/private/restore_quarantine').glob('*/v1022_ecology/commits/000000000999.json'))


def test_whole_audit_does_not_repair_authenticated_byte_drift(tmp_path):
    from test_v1022_7_3_restore_frontier import setup
    from test_v1022_7_evidence_bound_soul import file_bytes
    from tukuyo_v977 import whole_state as whole
    d=tmp_path/'data';setup(d);(d/'v977/SOUL_CORE.json').write_text('{}')
    before=file_bytes(d);result=whole.audit(d)
    assert not result['ok'] and any('BYTE_DRIFT' in e for e in result['errors'])
    assert file_bytes(d)==before


def test_whole_audit_has_bounded_retry_for_continuing_external_writes(tmp_path,monkeypatch):
    from test_v1022_7_3_restore_frontier import setup
    from tukuyo_v977 import whole_state as whole
    d=tmp_path/'data';setup(d);calls=[]
    def never_stable(data):
        p=d/'future.json';p.write_text(str(len(calls)));calls.append(True)
        return {'ok':True,'errors':[]}
    monkeypatch.setattr(whole,'_audit_once',never_stable)
    result=whole.audit(d)
    assert not result['ok'] and len(calls)==4


def test_new_decision_root_cannot_reset_same_claim_budget(tmp_path):
    from test_v1022_7_2_grounded_sensor import setup,observation
    from test_v1022_7_3_evidence_decision import decide
    from test_v1022_7_evidence_bound_soul import file_bytes
    from tukuyo_v1022 import grounded_sensor as gs
    d=tmp_path/'data';devices,_,_=setup(d)
    first=gs.observe(d,observation(devices,values=(10,10,40),nonce='budget-1',tick=10))
    parent=decide(d,first)
    second=gs.observe(d,observation(devices,values=(10,10,40),nonce='budget-2',tick=11))
    before=file_bytes(d)
    with pytest.raises(ValueError,match='CLAIM_BUDGET_RESET'):decide(d,second)
    assert file_bytes(d)==before
    continued=decide(d,second,parent['decision_sha256'])
    assert continued['assessment']['remaining_acquisitions']==1 and gs.audit(d)['ok']


def test_frontier_retires_future_private_only_and_empty_runtimes(tmp_path):
    from test_v1022_7_3_restore_frontier import setup
    from tukuyo_v1014 import recovery as rec
    d=tmp_path/'data';setup(d)
    empty=d/'v1022_ecology/runtimes/R000998/v1022/commits';empty.mkdir(parents=True)
    secret=d/'v1022_ecology/runtimes/R000999/private/stale.key';secret.parent.mkdir(parents=True);secret.write_bytes(b'test-owned-old-key')
    result=rec.enforce_restore_frontier(d)
    assert len(result['retired_future_runtimes'])==2 and not empty.exists() and not secret.exists()
    saved=list((d/'v1014/private/retired_runtimes').glob('*/v1022_ecology/R000999-*/private/stale.key'))
    assert len(saved)==1 and saved[0].read_bytes()==b'test-owned-old-key'
    assert run(d,'whole-audit')['ok']


def test_frontier_prunes_empty_optional_commit_directory(tmp_path):
    from test_v1022_7_3_restore_frontier import setup
    from tukuyo_v1014 import recovery as rec
    d=tmp_path/'data';setup(d);p=d/'v1022_ecology/commits';p.mkdir(parents=True)
    result=rec.enforce_restore_frontier(d)
    assert 'v1022_ecology/commits' in result['pruned_empty_directories'] and not p.exists()
    assert run(d,'whole-audit')['ok']


def test_unregistered_newborn_collision_does_not_reuse_old_private_material(tmp_path):
    from tukuyo_v1022 import metabolism as m
    from tukuyo_v977 import whole_state as whole
    d=tmp_path/'data';run(d,'init','--individual-id','COLLISION-74')
    run(d,'metabolism-init','--families','2','--max-age','64','--reservoir','50000','--no-actions')
    s=m.preflight(d);p=m.child(d,'R000002')
    (p/'v1022/commits').mkdir(parents=True);key=p/'private/stale.key';key.parent.mkdir();key.write_bytes(b'test-owned-never-import')
    rid,_=m._fresh(d,s)
    assert rid=='R000002' and not key.exists() and whole.audit(p)['ok']
    archived=list((m.root(d)/'private/newborn_collision_archive').glob('R000002-*/runtime/private/stale.key'))
    assert len(archived)==1 and archived[0].read_bytes()==b'test-owned-never-import'
