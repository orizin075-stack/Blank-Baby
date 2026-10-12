"""Source binding, separate input graphs, selective quantities and learned transfer."""
import copy,tempfile
from fractions import Fraction
from pathlib import Path
import pytest
from test_v1022_5_fusion import run
from tukuyo_v1022 import cognition,proofs,semantic_coverage,wordprob

@pytest.mark.parametrize('q,a',[
 ('There are 4 red balls and 6 blue balls. How many red balls in total?','4'),
 ('There are 4 red balls and 6 blue balls. How many blue balls in total?','6'),
 ('There are 4 red balls and 6 blue balls. How many balls in total?','10'),
 ('There are 7 green apples, 3 red apples and 5 blue apples. How many green apples in total?','7'),
 ('1箱に9個入りが5箱あります。4個売った。残りは何個？','41'),
 ('1箱に12個入りが4箱あります。5個売った。7個仕入れた。残りは何個？','50'),
 ('1箱に8個入りが5箱あります。2箱仕入先へ返品しました。残りは何個？','24'),
 ('1箱に8個入りが5箱あります。2箱仕入先へ返品しました。残りは何箱？','3'),
 ('1箱に8個入りが4箱あります。3個売った。3個補充した。残りは何個？','32'),
 ('1箱に8個入りが4箱あります。3個返品されて戻りました。残りは何個？','35'),
 ('2Lの水があります。250mL飲みました。0.5L使いました。残りは何mL？','1250'),
 ('2Lの水があります。250mL飲みました。0.5L使いました。残りは何L？','1.25'),
 ('750mLの水があります。0.25L使いました。残りは何L？','0.5'),
 ('2Lの水があります。250mL使い、さらに0.5L使いました。残りは何mL？','1250'),
 ('牛乳が1リットルあって、250ミリリットル飲んだ。残りは何ミリリットル？','750'),
 ('水が2リットルあって、500ミリリットル飲んだ。残りは何ミリリットル？','1500'),
 ('1袋に12個入りのあめが4袋。あめは全部で何個？','48'),
 ('1箱に8個入りが4箱あります。3個食べたが足りないです。残りは何個？','29'),
])
def test_public_quantity_graphs(q,a):
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'data';run(d,'init','--individual-id','INDEPENDENT-52')
        for cmd in ('think','verified-query'):
            r=run(d,cmd,q);assert not r['uncertain'] and Fraction(r['answer'])==Fraction(a),r
            b=r['verification_evidence']['input_coverage'];assert b['ok'] and b['recognized'] and b['graph']
            assert b['covered_numeric_ids']==list(range(b['numeric_token_count']))
            assert proofs.check(r['proof'],r['answer'])
        assert run(d,'whole-audit')['ok']

@pytest.mark.parametrize('q',[
 'There are 4 red balls and 6 red balls. How many red balls in total?',
 'There are 4 red balls including 2 blue balls. How many red balls in total?',
 'There are 4 red balls and 6 blue balls. How many green balls in total?',
 'There are 4 red balls and 6 blue apples. How many red balls in total?',
 '2Lの水があります。250mLの油を加えました。残りの水は何mL？',
 '2Lの水があります。2.5L使いました。1L加えました。残りは何mL？',
 '2Lの水があります。250mL飲む予定です。残りは何mL？',
 '1箱に8個入りが4箱あります。3個売った。残りは何箱？',
 '1箱に8個入りが4箱あります。3個売ったと言われました。残りは何個？',
 '1箱に8個入りが4箱あります。40個売った。2箱仕入れた。残りは何個？',
 '1箱に8個入りが4箱あります。3個売る予定ではなく売った。残りは何個？',
 '1袋に12個入りのあめが4袋。ガムは全部で何個？',
 '牛乳が1Lあって、250mL飲んだ。残りの水は何mL？',
])
def test_unknown_scope_overlap_and_transient_debt_are_withheld(q):
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'data';run(d,'init','--individual-id','INDEPENDENT-REFUSAL-52')
        assert run(d,'think',q)['uncertain'];assert run(d,'verified-query',q)['uncertain']

@pytest.mark.parametrize('q,bad,a',[
 ('There are 4 red balls and 6 blue balls. How many red balls in total?','10','4'),
 ('1箱に9個入りが5箱あります。4個売った。残りは何個？','45','41'),
 ('2Lの水があります。250mL飲みました。0.5L使いました。残りは何mL？','1750','1250'),
])
def test_a_fault_in_producer_cannot_change_independent_expected(monkeypatch,q,bad,a):
    fake={'ok':True,'recognized':True,'uncertain':False,'answer':bad,'confidence':.99,'proof':{'kind':'arithmetic','expression':bad}}
    monkeypatch.setattr(cognition,'_solve_core',lambda *args,**kwargs:fake)
    monkeypatch.setattr(wordprob,'solve',lambda query:{'value':Fraction(bad)})
    r=cognition.solve(Path('/unused'),q)
    assert r['uncertain'] and r['answer'] is None and r['verification_evidence']['input_coverage']['expected']==a

def test_subset_proof_binds_selected_and_excluded_quantities():
    q='There are 4 red balls and 6 blue balls. How many red balls in total?'
    w=wordprob.solve(q);r=cognition._word_answer({**w,'source_query':q});p=r['proof']
    assert proofs.check(p,'4')
    forged=copy.deepcopy(p);forged['semantic_graph']['quantities'][1]['role']='selected';assert not proofs.check(forged,'4')
    forged=copy.deepcopy(p);forged['source_query']=q.replace('4 red','9 red');assert not proofs.check(forged,'4')
    forged=copy.deepcopy(p);forged.pop('semantic_graph');assert not proofs.check(forged,'4')
    b=semantic_coverage.inspect(q,'4');assert len(b['graph']['quantities'])==2 and b['covered_numeric_ids']==[0,1]

def test_inventory_proof_binds_events_even_when_errors_cancel():
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'data';run(d,'init','--individual-id','BOUND-PROOF-52')
        q='1箱に8個入りが4箱あります。3個売った。3個補充した。残りは何個？'
        r=run(d,'think',q);p=r['proof'];assert proofs.check(p,'32')
        forged=copy.deepcopy(p)
        for e in forged['events']:e['quantity']=5
        assert not proofs.check(forged,'32')
        forged=copy.deepcopy(p);forged['source_query']=q.replace('3個売った','5個売った');assert not proofs.check(forged,'32')
        forged=copy.deepcopy(p);forged['independent_input_graph']['events'][0]['direction']=1;assert not proofs.check(forged,'32')

def test_lexical_transfer_requires_learned_skill_support():
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'data';run(d,'init','--blank-learning','--individual-id','BLANK-52')
        for q in ['1箱に9個入りが5箱あります。4個売った。残りは何個？',
                  '1箱に9個入りが5箱あります。4個仕入れた。残りは何個？']:
            assert run(d,'think',q)['uncertain']
