import json, tempfile
from pathlib import Path
from tukuyo_v1012.core_reasoning import reason
from tukuyo_v1007.organism2 import init as org_init, update as org_update
from tukuyo_v1018 import succession as s

def test_basic_reasoning_regressions():
    a=reason('りんごを3個持っていて2個もらった。全部で何個？')
    assert a['ok'] and a['answer']=='5',a
    b=reason('1箱に8個入りが4箱あります。3箱使いました。残りは何個？')
    assert b['ok'] and b['answer']=='8',b

def test_irreversible_death_init_guard(monkeypatch,tmp_path):
    import tukuyo_v1007.organism2 as o
    monkeypatch.setattr(o,'_live_identity',lambda d:{'individual_id':'X'})
    r=o.init(tmp_path);assert r['ok']
    o.update(tmp_path,'INJURY',1.0);o.update(tmp_path,'INJURY',1.0)
    r=o.init(tmp_path);assert not r['ok'] and 'REINIT_FORBIDDEN' in r['error']

def test_key_loss_is_not_silent(monkeypatch,tmp_path):
    monkeypatch.setattr(s,'_live_identity',lambda d:{'individual_id':'X','lineage_id':'L','branch_id':'B'})
    s.public_key(tmp_path);s.key_path(tmp_path).unlink()
    try:s.public_key(tmp_path)
    except ValueError as e: assert 'PRIVATE_KEY_MISSING' in str(e)
    else: raise AssertionError('key loss silently regenerated')
