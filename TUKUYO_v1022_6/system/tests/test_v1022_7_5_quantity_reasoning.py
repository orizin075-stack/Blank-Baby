"""Check actual CLI answers, conservation, source binding and refusal boundaries."""
import ast
import copy
from pathlib import Path
import pytest
from test_v1022_5_fusion import run
from tukuyo_v1022 import cognition,proofs,quantity_verify,semantic_coverage

POSITIVE=[
    ('1箱8個入りを5箱買い、2箱返品。残り何個？','24'),
    ('1箱12個入りが4箱あります。5個売って7個仕入れました。残り何個？','50'),
    ('2Lの水から250mLと0.5Lを使いました。残りは何mL？','1250'),
    ('ある数の3倍に2を足すと17です。その数は？','5'),
    ('袋Aにりんごが8個、袋Bに6個あります。AからBへ3個移しました。Bは何個？','9'),
    ('3人で同じ額ずつ払って合計1200円でした。1人何円？','400'),
    ('6kmを40分で歩きました。平均の速さは時速何km？','9'),
]

@pytest.mark.parametrize('query,expected',POSITIVE)
def test_public_quantity_answers_have_complete_separate_input_check(tmp_path,query,expected):
    d=tmp_path/'d';run(d,'init','--individual-id','QUANTITY-75')
    for command in ('think','verified-query'):
        result=run(d,command,query)
        assert not result['uncertain'] and result['answer']==expected,result
        proof=result['proof'];assert proofs.check(proof,expected)
        audit=result['verification_evidence']['input_coverage']
        assert audit['ok'] and audit['recognized'] and audit['graph']==proof['semantic_graph']
        assert audit['covered_numeric_ids']==list(range(audit['numeric_token_count']))
        assert audit['parser_separate_from_producer'] and not audit['complete_semantic_independence']
    assert run(d,'whole-audit')['ok']

NEGATIVE=[
    '1箱8個入りが5箱あります。2箱返品。残り何個？',
    '1箱8個入りを5箱買い、2箱返品する予定です。残り何個？',
    '1箱8個入りを5箱買い、6箱返品。残り何個？',
    '1箱8個入りを5箱買い、2箱返品。9個忘れました。残り何個？',
    '1箱12個入りが4箱あります。5個売って7個仕入れていません。残り何個？',
    '1箱12個入りが4箱あります。5個売って7個仕入れる予定です。残り何個？',
    '1箱12個入りが4箱あります。5個売って7個仕入れました。残り何箱？',
    '1箱12個入りが4箱あります。50個売って7個仕入れました。残り何個？',
    '1箱12個入りが4箱あります。5個売って7枚仕入れました。残り何個？',
    '1箱12個入りが4箱あります。5個売って7個仕入れました。8個行方不明です。残り何個？',
    '2Lの水から250mLと0.5kgを使いました。残りは何mL？',
    '2Lの水から250mLと0.5Lを使いませんでした。残りは何mL？',
    '2Lの水から250mLと0.5Lを使う予定です。残りは何mL？',
    '2Lの水から250mLと3Lを使いました。残りは何mL？',
    '2Lの水から250mLと0.5Lを使いました。牛乳は何mL？',
    'ある数の0倍に2を足すと2です。その数は？',
    'ある数の3倍に2を足すと17か18です。その数は？',
    'ある整数の3倍に2を足すと18です。その数は？',
    'ある正の数の3倍に20を足すと17です。その数は？',
    'ある数の3倍に2を足すと17です。4でもあるらしい。その数は？',
    '袋Aにりんごが8個、袋Bに6個あります。AからBへ9個移しました。Bは何個？',
    '袋Aにりんごが8個、袋Bに6個あります。AからCへ3個移しました。Bは何個？',
    '袋Aにりんごが8個、袋Bに6個あります。AからBへ3個移す予定です。Bは何個？',
    '袋Aにりんごが8個、袋Bに6個あります。AからBへ3個移しませんでした。Bは何個？',
    '袋Aにりんごが8個、袋Aに6個あります。AからBへ3個移しました。Bは何個？',
    '3人で払って合計1200円でした。1人何円？',
    '3人で同じ額ずつ払う予定で合計1200円です。1人何円？',
    '0人で同じ額ずつ払って合計1200円でした。1人何円？',
    '3人で同じ額ずつ払って合計1200円でした。2人何円？',
    '6kmを0分で歩きました。平均の速さは時速何km？',
    '6kmを40分で歩けます。平均の速さは時速何km？',
    '6kmを40分で歩きませんでした。平均の速さは時速何km？',
    '6kmを40分で歩きました。10分休みました。平均の速さは時速何km？',
]

@pytest.mark.parametrize('query',NEGATIVE)
def test_ambiguous_incomplete_or_inconsistent_quantity_is_not_rescued(tmp_path,query):
    d=tmp_path/'d';run(d,'init','--individual-id','QUANTITY-REFUSE-75')
    for command in ('think','verified-query'):
        result=run(d,command,query)
        assert result['uncertain'],(query,command,result)


@pytest.mark.parametrize('query,expected',[
    ('袋Aにりんごが8個、袋Bに6個あります。AからBへ3個移しました。BからAへ2個移しました。袋Aは何個？','7'),
    ('1袋9本入りを7袋買い、3袋返品。残り何袋？','4'),
    ('3Lの牛乳から200mLと0.4Lと1dLを飲みました。残りは何L？','23/10'),
    ('ある数の4倍から3を引くと10です。その数は？','13/4'),
    ('2人で均等に払って合計1円でした。1人何円？','1/2'),
    ('240mを2分で走りました。平均の速さは秒速何m？','2'),
])
def test_compositions_targets_and_exact_rational_answers(tmp_path,query,expected):
    d=tmp_path/'d';run(d,'init','--individual-id','QUANTITY-COMPOSE-75')
    result=run(d,'verified-query',query)
    from fractions import Fraction
    assert not result['uncertain'] and Fraction(result['answer'])==Fraction(expected),result
    assert proofs.check(result['proof'],result['answer'])


def test_new_inventory_syntax_keeps_learned_skill_causal(tmp_path):
    blank=tmp_path/'blank';seed=tmp_path/'seed'
    run(blank,'init','--individual-id','QUANTITY-BLANK','--blank-learning')
    run(seed,'init','--individual-id','QUANTITY-SEED')
    for query,expected in POSITIVE[:2]:
        assert run(blank,'think',query)['uncertain']
        assert run(seed,'think',query)['answer']==expected
    assert run(blank,'think',POSITIVE[3][0])['answer']=='5'


def test_quantity_proof_binds_every_source_and_operation_node(tmp_path):
    d=tmp_path/'d';run(d,'init','--individual-id','QUANTITY-CERT-75')
    query=POSITIVE[4][0];result=run(d,'think',query);p=result['proof'];answer=result['answer']
    for mutate in ('source','amount','target','expression','unit','edge'):
        bad=copy.deepcopy(p)
        if mutate=='source':bad['source_query']=query.replace('3個移しました','4個移しました')
        elif mutate=='amount':bad['semantic_graph']['transfers'][0]['quantity']='4'
        elif mutate=='target':bad['semantic_graph']['target']='A'
        elif mutate=='expression':bad['expression']='9'
        elif mutate=='unit':bad['unit']='枚'
        else:bad['semantic_graph']['transfers'][0]['to']='A'
        assert not proofs.check(bad,answer),(mutate,bad)
    # A valid arithmetic equality must not independently endorse a wrong interpretation.
    check=quantity_verify.inspect(query,'8',p)
    assert check['recognized'] and not check['ok']


def test_new_checker_has_no_producer_or_shared_parser_imports():
    tree=ast.parse(Path(quantity_verify.__file__).read_text())
    allowed={'fractions','re','unicodedata'}
    for node in ast.walk(tree):
        if isinstance(node,ast.ImportFrom):assert node.level==0 and node.module in allowed
        if isinstance(node,ast.Import):assert all(x.name in allowed for x in node.names)


def test_independent_checker_rejects_fractional_package_without_exception():
    r=semantic_coverage.inspect('1箱8.5個入りを5箱買い、2箱返品。残り何個？','25.5')
    assert r['recognized'] and not r['ok']
