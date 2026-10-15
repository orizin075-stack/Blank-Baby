import json
from pathlib import Path
import pytest
from test_v1022_5_fusion import run
from test_v1022_7_evidence_bound_soul import file_bytes
from tukuyo_v1014 import recovery as rec


def setup(data):
    run(data,'init','--individual-id','RESTORE-FRONTIER')
    run(data,'realtime-start');cp=run(data,'recovery-checkpoint')['path']
    run(data,'verified-query','8たす9は？')
    run(data,'recovery-restore',cp,'--trust-file',data/'v1014/recovery.pub')
    return cp


def test_reappearing_extra_files_are_quarantined_with_signed_evidence(tmp_path):
    d=tmp_path/'data';setup(d);keys={str(p.relative_to(d)):p.read_bytes() for p in d.rglob('*.key')}
    p=d/'v1022_ecology/commits/000000000999.json';p.parent.mkdir(parents=True);raw=b'{"future":true}\n';p.write_bytes(raw)
    result=rec.enforce_restore_frontier(d)
    assert result['active'] and result['quarantined_files'][0]['path']=='v1022_ecology/commits/000000000999.json'
    assert not p.exists()
    quarantined=list((d/'v1014/private/restore_quarantine').glob('*/v1022_ecology/commits/*.json'))
    assert len(quarantined)==1 and quarantined[0].read_bytes()==raw
    assert {str(p.relative_to(d)):p.read_bytes() for p in d.rglob('*.key')}==keys
    assert run(d,'whole-audit')['ok']


def test_frontier_refuses_changed_checkpoint_bytes_without_resigning(tmp_path):
    d=tmp_path/'data';cp=setup(d);(d/'v977/SOUL_CORE.json').write_text('{}');before=file_bytes(d)
    with pytest.raises(ValueError,match='FRONTIER_BYTE_DRIFT'):rec.enforce_restore_frontier(d)
    assert file_bytes(d)==before
    assert run(d,'recovery-restore',cp,'--trust-file',d/'v1014/recovery.pub')['ok']
    assert run(d,'whole-audit')['ok']


def test_old_frontier_does_not_undo_a_later_legitimate_head(tmp_path):
    d=tmp_path/'data';setup(d);run(d,'verified-query','9たす10は？')
    p=d/'later-file.txt';p.write_text('legitimate later branch');before=file_bytes(d)
    result=rec.enforce_restore_frontier(d)
    assert result['head_advanced'] and not result['active'] and file_bytes(d)==before


def test_frontier_signature_tamper_is_rejected_without_mutation(tmp_path):
    d=tmp_path/'data';setup(d);p=d/'v1014/private/RESTORE_FRONTIER.json';control=json.loads(p.read_text())
    control['body']['file_metadata']={};p.write_text(json.dumps(control));before=file_bytes(d)
    with pytest.raises(ValueError,match='FRONTIER_AUTHENTICATION'):rec.enforce_restore_frontier(d)
    assert file_bytes(d)==before


def test_frontier_defers_to_durable_prepared_redo(tmp_path):
    from test_v1019_1 import crash
    d=tmp_path/'data';setup(d)
    crash(d,'lineage:after_prepare','evolution-select','research')
    assert rec.enforce_restore_frontier(d)['prepared_redo_deferred']
    assert run(d,'evolution-audit')['ok'] and run(d,'whole-audit')['ok']
