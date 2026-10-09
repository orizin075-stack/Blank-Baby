import json,subprocess,sys,tempfile,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py'
sys.path.insert(0,str(ROOT/'src'))


def run(data,*args,ok=True):
    p=subprocess.run([sys.executable,'-B',str(CLI),'--data',str(data),*map(str,args)],cwd=ROOT,text=True,capture_output=True,timeout=180,env={**__import__('os').environ,'PYTHONDONTWRITEBYTECODE':'1'})
    if ok and p.returncode!=0:raise AssertionError(p.stdout+p.stderr)
    try:return json.loads(p.stdout)
    except Exception:raise AssertionError(p.stdout+p.stderr)


def test_v989_temporal_identity_accepts_lawful_soul_change_and_memory_loss():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V989-TEMPORAL')
        a=run(d,'soul-identity-status');assert a['ok'] and a['same_identity'] and a['transition_count']==0
        origin=a['origin_soul_sha256']
        run(d,'heart-experience','discovery','1','1','--theme','発見')
        run(d,'heart-experience','betrayal','-1','1','--theme','broken_promise','--relation','peerX')
        b=run(d,'soul-identity-audit');assert b['ok'] and b['same_identity'];assert b['transition_count']==2
        assert b['origin_soul_sha256']==origin and b['current_soul_sha256']!=origin
        run(d,'soul-consolidate');run(d,'soul-forget-surface')
        c=run(d,'soul-identity-audit');assert c['ok'] and c['same_identity'] and c['transition_count']==2
        assert all(c['checks'].values())


def test_v989_detects_and_repairs_unlogged_soul_state_jump():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V989-JUMP')
        run(d,'heart-experience','discovery','1','1','--theme','x')
        sp=d/'v977'/'SOUL_CORE.json';expected=sp.read_bytes();journal=d/'v977'/'SOUL_EVENTS.jsonl';journal_before=journal.read_bytes();transition=d/'v989'/'SOUL_TRANSITIONS.jsonl';transition_before=transition.read_bytes();q=json.loads(sp.read_text());q['core_values']['curiosity']=0.123456;sp.write_text(json.dumps(q),encoding='utf-8')
        from tukuyo_v989.temporal_identity import audit
        a=audit(d);assert not a['ok'] and 'ILLEGAL_STATE_JUMP' in a['errors']
        # Current startup repairs this materialization from the canonical journal.
        a=run(d,'soul-identity-audit');assert a['ok'] and all(a['checks'].values())
        assert sp.read_bytes()==expected and journal.read_bytes()==journal_before and transition.read_bytes()==transition_before
        assert run(d,'whole-audit')['ok']


def test_v989_fork_origin_is_historical_snapshot_not_current_soul_equality():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V989-FORK')
        run(d,'heart-experience','betrayal','-1','1','--theme','boundary','--relation','peer')
        run(d,'soul-consolidate');x=run(d,'soul-fork-assay');assert x['ok'];assert run(d,'soul-fork-audit')['ok']
        # A lawful later experience changes the parent soul but must not rewrite the frozen fork origin.
        op=d/'v981'/'FORK_ORIGIN.json';before=json.loads(op.read_text())['origin_sha256']
        run(d,'heart-experience','discovery','1','1','--theme','later_knowledge')
        after=json.loads(op.read_text())['origin_sha256'];assert before==after
        assert run(d,'soul-fork-audit')['ok'];assert run(d,'soul-identity-audit')['ok']


def test_v989_transition_chain_detects_tamper():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V989-TAMPER')
        run(d,'heart-experience','discovery','1','1','--theme','x')
        # the chain is an append-only journal (one transition per line): change the first transition
        tp=d/'v989'/'SOUL_TRANSITIONS.jsonl';ls=tp.read_text().splitlines();q=json.loads(ls[0]);q['to_soul_sha256']='0'*64;ls[0]=json.dumps(q);tp.write_text('\n'.join(ls)+'\n',encoding='utf-8')
        a=run(d,'soul-identity-audit',ok=False);assert not a['ok'];assert any('CHAIN' in e or 'TRANSITION' in e for e in a['errors'])


def test_v989_chain_is_an_append_only_journal_and_moves_from_the_old_file():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V989-JOURNAL')
        for t in ('a','b'):run(d,'heart-experience','discovery','1','.5','--theme',t)
        jp=d/'v989'/'SOUL_TRANSITIONS.jsonl';before=jp.read_bytes()
        run(d,'heart-experience','learning','.5','.5','--theme','c')
        after=jp.read_bytes();assert after.startswith(before) and after.count(b'\n')==before.count(b'\n')+1   # one line appended
        # an individual from before the journal: the chain as one object; it is read, and the next experience moves it
        from tukuyo_v989.temporal_identity import load_chain
        old=load_chain(d);(d/'v989'/'SOUL_TRANSITIONS.json').write_text(json.dumps(old),encoding='utf-8');jp.unlink()
        assert run(d,'soul-identity-audit')['ok'] and run(d,'whole-audit')['ok']
        run(d,'heart-experience','learning','.5','.5','--theme','d')
        assert jp.is_file() and not (d/'v989'/'SOUL_TRANSITIONS.json').exists()
        new=load_chain(d);assert new['transitions'][:3]==old['transitions'] and new['transition_count']==4
        a=run(d,'soul-identity-audit');assert a['ok'] and a['transition_count']==4
