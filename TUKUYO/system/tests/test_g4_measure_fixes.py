"""generation 4: faults found by measuring (tools/g4_measure.py) stay fixed. The wording is our own."""
import json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_g4 import api,check,fpl,learn,numbers as N,reader,solve

def test_sharing_among_zero_is_no_reading_not_a_crash():
    # fuzzing: 'into 0 bags' divided by zero inside the reader and broke solve(), think() and ask()
    t='Ted has 12 candy bars. He wants to put them into 0 bags so there are the same number of candy bars in each bag. How many candy bars should go in each bag?'
    assert reader.read(t)['spec'] is None
    assert api.solve(t,llm='off')['answer'] is None and api.ask(t,llm='off')['answer'] is None

def test_equations_from_outside_are_bounded():
    # a parent may return anything: deep nesting or a very long chain overflowed the recursive parser
    base={'schema':'tukuyo.g4.fpl/1','lang':'en','text':'x','ask':'x','unused':[],
          'quantities':[{'name':'x','unit':'1','integer':False,'signed':False,'about':''}]}
    for eq,why in (('x = '+'('*400+'1'+')'*400,'TOO'),('x = 2'+' * 2'*3000,'TOO')):
        r=api.evaluate({**base,'facts':[{'eq':eq,'span':'x'}]},'test')
        assert not r['ok'] and why in r['reason'],r['reason']
    c=check.check({**base,'facts':[{'eq':'x = '+'('*40+'1'+')'*40,'span':'x'}]},{'x':1})
    assert not c['ok'] and 'EQUATION_TOO_DEEP' in c['failures']
    try:fpl.parse_expr('('*40+'1'+')'*40);raise AssertionError('not refused')
    except fpl.FPLError as e:assert str(e)=='TOO_DEEP'

def test_a_template_is_not_learned_when_two_numbers_of_a_span_are_equal():
    # learning: '2 red and 2 blue' tied both bindings to the first 2, so '3 red and 1 blue' was answered 6
    t='A box has 2 red pens, 13 blue pens and 2 green pens. How many pens are in the box?'
    rd=reader.read(t);assert rd['spec'] and api.evaluate(rd['spec'],'own')['value']=='17'
    assert learn.template(rd['spec']) is None
    d=Path(tempfile.mkdtemp());st=learn.Store(d/'g4');st.add(rd['spec'],{'route':'test'})
    assert st.find('A box has 3 red pens, 12 blue pens and 1 green pens. How many pens are in the box?') is None

def test_a_one_that_counts_must_be_read():
    # the checker took every 1 as a number a reading may leave out: '1 green pen' could be dropped silently
    t='A box has 3 red pens and 1 green pen. How many pens are in the box?'
    q=[{'name':n,'unit':'pen','integer':True,'signed':False,'about':''} for n in ('red','total')]
    spec={'schema':'tukuyo.g4.fpl/1','lang':'en','text':t,'ask':'total','unused':[],'quantities':q,
          'facts':[{'eq':'red = 3','span':'3 red pens'},{'eq':'total = red','span':'How many pens are in the box?'}]}
    r=api.evaluate(spec,'test');assert not r['ok'] and 'NUMBER_NOT_ACCOUNTED:1' in r['reason']
    one=lambda text:[N.optional(n,text) for n in N.find(text) if n.value==1]
    assert one('If one pack costs 11 dollars, how much do 4 packs cost?')==[True]          # the base of a price
    assert one('1日に8ページずつ読みます。')==[True] and one('1個あたり50円です。')==[True] and one('the price per 1 kg')==[True]
    assert one('He was told by one of the pickers.')==[True]
    assert one('Later she saw one more cat.')==[False] and one('りんごが1個あります。')==[False] and one('Each bag holds 1 apple.')==[False]

def test_an_empty_question_is_no_answer(tmp_path):
    # the v1022 core raised IndexError on an empty or blank query, so think stopped with an error
    from tukuyo_v1022 import cognition
    for q in ('','   ','\n'):
        b=cognition.solve(str(tmp_path),q)
        assert b['answer'] is None and b['reason']=='EMPTY_QUERY'
        assert api.think(str(tmp_path),q,b,llm='off')['answer'] is None
