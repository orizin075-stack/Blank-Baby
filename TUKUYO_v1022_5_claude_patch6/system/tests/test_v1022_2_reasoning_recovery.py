import json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_v1022 import hypothesis,proofs
from tukuyo_v1022.hypothesis_verify import verify as verify_hypothesis
from tukuyo_v1014.recovery import _clear_private_ephemera
from tukuyo_common.journal import prefix_last_event


def test_hypothesis_generation_unique_affine_and_independent_verify():
    q='x=1のときy=3、x=2のときy=5、x=4のときy=9。x=7のときyは何？'
    r=hypothesis.solve(q)
    assert r['answer']=='15' and len(r['candidates'])==1,r
    assert proofs.check(r['proof'],'15')
    v=verify_hypothesis(q,'15');assert v['recognized'] and v['decidable'] and v['supported'],v
    assert not verify_hypothesis(q,'14')['supported']


def test_hypothesis_counterexample_search_refuses_underdetermined_rule():
    q='x=0のときy=1、x=1のときy=2。x=2のときyは何？'
    r=hypothesis.solve(q)
    assert r['answer'] is None and r['reason']=='HYPOTHESIS_UNDERDETERMINED',r
    assert len(r['candidates'])>=2 and r['counterexample'] is not None,r
    preds={x['y'] for x in r['counterexample']['predictions']};assert len(preds)>=2


def test_hypothesis_tamper_rejected():
    r=hypothesis.solve('入力1->出力4、入力2->出力7、入力3->出力10。入力5の出力は何？')
    assert r['answer']=='16',r
    p=json.loads(json.dumps(r['proof']));p['model']['coefficients'][1]='4'
    assert not proofs.check(p,'16')


def test_plan_alternatives_and_replan_after_action_loss():
    t={'initial':{'place':'A'},'goal':{'place':'D'},'actions':[
        {'id':'ab','pre':{'place':'A'},'set':{'place':'B'},'cost':1},
        {'id':'bd','pre':{'place':'B'},'set':{'place':'D'},'cost':1},
        {'id':'bc','pre':{'place':'B'},'set':{'place':'C'},'cost':2},
        {'id':'cd','pre':{'place':'C'},'set':{'place':'D'},'cost':2},
        {'id':'ad','pre':{'place':'A'},'set':{'place':'D'},'cost':9}]}
    rows=proofs.alternative_plans(t)
    assert rows[0]['route']==['ab','bd'] and rows[0]['cost']==2,rows
    assert any(r['route']==['ad'] for r in rows),rows
    rp=proofs.replan(t,{'place':'B'},['bd'])
    assert rp['route']==['bc','cd'] and rp['cost']==4,rp


def test_private_ephemeral_cleanup_preserves_keys_and_tokens():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td);files={
            'v1013/private/realtime.key':'secret','v1013/private/REALTIME_PENDING.json':'{}',
            'v1015/private/EPISODE_TXN.json':'{}','v1014_4/private/CONVERSATION_TXN.json':'{}',
            'v1022_ecology/private/delegation.token':'token','v1018/private/succession.key':'key'}
        for rel,val in files.items():p=d/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(val)
        removed=_clear_private_ephemera(d)
        assert 'v1013/private/REALTIME_PENDING.json' in removed
        assert 'v1015/private/EPISODE_TXN.json' in removed
        assert not (d/'v1013/private/REALTIME_PENDING.json').exists()
        assert (d/'v1013/private/realtime.key').read_text()=='secret'
        assert (d/'v1022_ecology/private/delegation.token').read_text()=='token'
        assert (d/'v1018/private/succession.key').read_text()=='key'


def test_journal_prefix_detects_future_and_divergent_cache_anchor():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'j.jsonl';rows=[{'seq':1,'event_sha256':'a'*64},{'seq':2,'event_sha256':'b'*64}]
        raw=''.join(json.dumps(x,separators=(',',':'))+'\n' for x in rows).encode();p.write_bytes(raw)
        first=(json.dumps(rows[0],separators=(',',':'))+'\n').encode()
        assert prefix_last_event(p,len(first))['event_sha256']=='a'*64
        try:prefix_last_event(p,len(raw)+1)
        except ValueError as e:assert str(e)=='JOURNAL_OFFSET_AHEAD'
        else:raise AssertionError('future offset accepted')


def test_counterexample_observation_refines_hypothesis_to_unique_rule():
    r=hypothesis.solve('x=0のときy=1、x=1のときy=2。x=7のときyは何？')
    assert r['answer'] is None and len(r['candidates'])>=2,r
    # The new x=2 -> y=3 observation eliminates the square-offset continuation.
    z=hypothesis.refine(r,2,3)
    assert z['answer']=='8' and z['reason']=='COUNTEREXAMPLE_REFINED',z
    assert z['eliminated'] and proofs.check(z['proof'],'8')


def test_plan_robustness_checks_one_action_failures():
    t={'initial':{'place':'A'},'goal':{'place':'D'},'actions':[
        {'id':'ab','pre':{'place':'A'},'set':{'place':'B'},'cost':1},
        {'id':'bd','pre':{'place':'B'},'set':{'place':'D'},'cost':1},
        {'id':'ac','pre':{'place':'A'},'set':{'place':'C'},'cost':3},
        {'id':'cd','pre':{'place':'C'},'set':{'place':'D'},'cost':3},
        {'id':'ad','pre':{'place':'A'},'set':{'place':'D'},'cost':9}]}
    r=proofs.assess_plan_robustness(t)
    assert r['ok'] and r['base']['route']==['ab','bd'],r
    assert r['single_action_survival']==1.0 and r['all_single_action_failures_survivable']
    assert all(x['viable'] for x in r['contingencies'])
