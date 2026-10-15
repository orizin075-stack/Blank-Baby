"""Cross-branch regressions: roles, exact values and shared live cognition."""
import copy
from test_v1022_5_fusion import run
from tukuyo_v1022 import cognition, proofs, semantic_gate, semantic_coverage


def test_exact_independent_fraction_rejects_rounding_and_sign_loss():
    q='時速5kmで3時間40分歩きました。距離は何km？'
    p={'kind':'arithmetic','expression':'5*(3+40/60)'}
    assert semantic_gate.audit(q,'55/3',p)['independent_parser']=='AGREE'
    assert not semantic_gate.audit(q,'18.3333333333',p)['ok']
    assert not semantic_gate.audit(q,'-55/3',p)['ok']


def test_group_role_accounts_for_excluded_content_without_ignoring_clauses():
    q='3 boxes with 7 apples each. How many boxes in total?'
    assert semantic_gate.audit(q,'3',{'kind':'arithmetic','expression':'3'})['ok']
    assert not semantic_gate.audit(q,'21',{'kind':'arithmetic','expression':'3*7'})['ok']
    q2=q.replace(' each.', ' each. There are 11 loose apples.')
    assert semantic_gate.parser_b(q2) is None
    assert not semantic_gate.audit(q2,'3',{'kind':'arithmetic','expression':'3'})['ok']


def test_independent_reading_distinguishes_percent_of_and_price_after():
    assert semantic_coverage.inspect('2500円の20%は？','500')['ok']
    assert not semantic_coverage.inspect('2500円の20%は？','2000')['ok']
    assert semantic_coverage.inspect('2500円の商品を20%引きしました。最終価格は？','2000')['ok']
    assert not semantic_coverage.inspect('2500円の商品を20%引きしました。最終価格は？','500')['ok']


def test_both_parent_cognition_paths_in_one_live_individual(tmp_path):
    d=tmp_path/'d';run(d,'init','--individual-id','FUSED-CROSS-PATHS')
    cases=[('りんごが12個あります。妹に5個あげました。あげたのは何個？','5'),
           ('1箱に8個入りが5箱あります。2箱仕入先へ返品しました。残りは何個？','24'),
           ('底辺が10cm、高さが6cmの三角形の面積は何cm²ですか？','30'),
           ('制約: A+B=18。B=2*A。Aは何？','6')]
    for q,a in cases:
        r=run(d,'think',q);assert r['answer']==a and not r['uncertain']
        assert proofs.check(r['proof'],a)
        p=copy.deepcopy(r['proof']);p['source_query']=q.replace('12個','18個').replace('18。','24。').replace('10cm','12cm').replace('5箱','6箱')
        assert not proofs.check(p,a)
    assert run(d,'whole-audit')['ok']


def test_scene_producer_fault_is_blocked_by_role_aware_parser_b(monkeypatch):
    q='りんごが12個あります。妹に5個あげました。あげたのは何個？'
    fake={'ok':True,'answer':'7','uncertain':False,'confidence':.99,
          'proof':{'kind':'situation','source_query':q,'expression':'12-5'}}
    monkeypatch.setattr(cognition,'_solve_core',lambda *args,**kw:fake)
    r=cognition.solve('/unused',q)
    assert r['answer'] is None and r['uncertain']
    assert r['semantic_gate']['reason']=='INDEPENDENT_PARSER_DISAGREES'


def test_metabolic_inventory_context_retains_learned_causality(tmp_path):
    q='1箱に5個入りが6箱、今の在庫としてあります。3個売った。今の在庫の残りは何個？'
    d=tmp_path/'trained';run(d,'init')
    r=run(d,'think',q)
    assert r['answer']=='27' and not r['uncertain']
    assert r['verification_evidence']['input_coverage']['graph']['events'][0]['direction']==-1
    assert proofs.check(r['proof'],'27')
    blank=tmp_path/'blank';run(blank,'init','--blank-learning')
    assert run(blank,'think',q)['uncertain']
