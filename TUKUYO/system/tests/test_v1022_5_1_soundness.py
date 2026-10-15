"""Externally reported failures, independent numerical variants and injected
producer faults. Provider fixtures exercise grounding only, not AI capability.
"""
import ast,json,sys,tempfile
from pathlib import Path
import pytest
from test_v1022_5_fusion import run,ROOT
from tukuyo_v1022 import cognition,semantic_coverage
from tukuyo_v1022_llm.answer_grounding import check as grounding

@pytest.mark.parametrize('query,answer',[
 ('時速6kmで2時間30分歩きました。何km進みましたか？','15'),
 ('時速9kmで1時間20分歩きました。距離は何km？','12'),
 ('分速120mで2分30秒歩きました。何m進みましたか？','300'),
 ('時速5kmで3時間40分歩きました。距離は何km？','55/3'),
 ('2000円の商品を20%引きし、さらに25%引きし、その後10%値上げしました。最終価格は？','1320'),
 ('3600円の商品を25%引きし、さらに10%引きし、その後20%値上げしました。最終価格は？','2916'),
 ('3 boxes with 7 apples each. How many boxes in total?','3'),
 ('1箱に8個入りが4箱あります。箱の数は？','4'),
 ('18 cookies shared equally among 6 children. How many children are there?','6'),
 ('There are 4 red balls and 6 blue balls. How many red balls in total?','4'),
])
def test_reported_quantity_roles_through_public_commands(query,answer):
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'d';run(d,'init','--individual-id','SOUNDNESS-QUANTITIES')
        r=run(d,'think',query);assert r['answer']==answer and not r['uncertain'],r
        r=run(d,'verified-query',query);assert r['answer']==answer and not r['uncertain'],r
        assert run(d,'whole-audit')['ok']

@pytest.mark.parametrize('query',[
 '2000円の商品Aを20%引きし、商品Bを25%引きし、その後10%値上げしました。最終価格は？',
 '2000円の商品を20%引きし、さらに25%調整しました。最終価格は？',
 '時速6kmで2時間30分歩き、さらに30を調整しました。何km進みましたか？',
 'もし太郎が走るならベルが鳴る。太郎は走れる。ベルが鳴りますか？',
 'もし太郎が泳ぐならベルが鳴る。太郎は泳げる。ベルが鳴りますか？',
 'もし太郎が食べるならベルが鳴る。太郎は食べたい。ベルが鳴りますか？',
 'Tom is 12 years old. Amy is 4 cm shorter than Tom. How tall is Amy?',
 '3 bags with 6 apples each. How many oranges in total?',
 '30本のペンを5人で分けました。1人何本ですか？',
 '12 cookies shared among 3 children. How many does each child get?',
 '-3 boxes with 7 apples each. How many apples in total?',
 '時速6kmで2時間30分休憩しました。何km進みましたか？',
 '時速6kmで2時間30分停車しました。何km進みましたか？',
 '時速6kmで2時間30分眠りました。何km進みましたか？',
 '時速6kmで2時間休憩し、その後時速4kmで1時間進みました。合計何km？',
 '時速6kmで2時間30分歩きました。距離は何kmで時間は何時間？',
])
def test_incomplete_or_unestablished_inputs_cannot_be_certain(query):
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'d';run(d,'init','--individual-id','SOUNDNESS-REFUSAL')
        assert run(d,'think',query)['uncertain']
        assert run(d,'verified-query',query)['uncertain']

def test_independent_audit_rejects_an_injected_same_error(monkeypatch):
    fake={'ok':True,'recognized':True,'uncertain':False,'answer':'12','confidence':.99,
          'proof':{'kind':'arithmetic','expression':'6*2'},'verification_evidence':{'independent':True}}
    monkeypatch.setattr(cognition,'_solve_core',lambda *args,**kwargs:fake)
    r=cognition.solve(Path('/unused'),'時速6kmで2時間30分歩きました。何km進みましたか？')
    assert r['uncertain'] and r['answer'] is None
    a=r['verification_evidence']['input_coverage'];assert a['expected']=='15' and len(a['covered_numeric_ids'])==3
    # Equal-valued occurrences still have different identities.
    a=semantic_coverage.inspect('時速30kmで2時間30分歩きました。何km進みましたか？','60')
    assert not a['ok'] and a['numeric_token_count']==3 and a['expected']=='75'

def test_independent_module_import_boundary():
    tree=ast.parse(Path(semantic_coverage.__file__).read_text())
    modules=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]+[a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
    assert set(modules)<= {'fractions','re','unicodedata'}

@pytest.mark.parametrize('mode,query,status',[
 ('fiction','北丘町の人口は何人？','unverified'),
 ('append','17*19','unverified'),
 ('small','北丘町の人口は何人？','unverified'),
 ('honest','17*19','verified'),
])
def test_true_claim_cannot_certify_unrelated_or_added_answer(mode,query,status):
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'d';run(d,'init','--individual-id','SOUNDNESS-GROUNDING')
        env={'TUKUYO_LLM_COMMAND':f'{sys.executable} -B {ROOT}/tools/mock_grounding_attack.py {mode}'}
        r=run(d,'llm-ask','--no-local-first',query,extra=env)
        assert r['status']==status,r
        assert r['uncertain']==(status!='verified')
        assert r['attempts'][-1]['answer_grounding']['ok']==(status=='verified')
        assert run(d,'llm-audit')['ok'] and run(d,'whole-audit')['ok']
