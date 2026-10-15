"""Source meaning, projection, time, modality and proof forgery regressions."""
import ast,copy,json,random
from pathlib import Path
import pytest
from tukuyo_g4 import api,episodic_reader,episodic_verify
from tukuyo_v1022 import cognition,proofs
from test_v1022_5_fusion import run,ROOT

@pytest.mark.parametrize('text,answer',[
 ('Nora has some pencils. Iris has 7 pencils. Nora gives Iris 5 pencils. How many pencils does Iris have now?','12'),
 ('凛は鉛筆を何本か持っていました。葵は鉛筆を7本持っていました。凛は葵に鉛筆を5本渡しました。今、葵は鉛筆を何本持っていますか？','12'),
 ('Nora had an unknown number of pencils. Nora buys 5 pencils. Nora now has 17 pencils. How many pencils did Nora have at first?','12'),
 ('凛ははじめに鉛筆を何本か持っていました。凛は鉛筆を5本買いました。今、凛は鉛筆を17本持っています。はじめに、凛は鉛筆を何本持っていましたか？','12'),
 ('Nora has 17 pencils. Iris has 7 pencils. Nora gives Iris some pencils. How many pencils do Nora and Iris have in total?','24'),
 ('凛は鉛筆を17本持っています。葵は鉛筆を7本持っています。凛は葵に鉛筆を何本か渡しました。凛と葵の鉛筆は合わせて何本ですか？','24'),
 ('Nora has 17 pencils. Iris has 7 pencils. Nora may have given Iris 5 pencils. How many pencils do Nora and Iris have in total?','24'),
 ('Nora has 17 pencils. Nora has some apples. Nora buys 5 pencils. How many pencils does Nora have now?','22'),
 ('She had 4 books. She bought 3 new books. How many new books did she buy?','3')])
def test_known_target_is_not_blocked_by_unrelated_unknowns(text,answer):
    assert api.solve(text,llm='off')['answer']==answer

@pytest.mark.parametrize('phase,want',[('now','19'),('at first','17'),('after buying','22'),('before eating','22')])
def test_query_time_changes_the_target(phase,want):
    text=f'Nora had 17 pencils. Nora buys 5 pencils. Nora eats 3 pencils. How many pencils did Nora have {phase}?'
    result=api.solve(text,llm='off');assert result['answer']==want

@pytest.mark.parametrize('event,want',[
 ('Nora buys 5 pencils','22'),('Nora will buy 5 pencils tomorrow','17'),
 ('Nora did not buy 5 pencils','17'),('Nora can buy 5 pencils','17'),
 ('Nora may have bought 5 pencils',None),('Nora buys some pencils',None)])
def test_nonexecuted_and_uncertain_events_are_distinguished(event,want):
    text=f'Nora had 17 pencils. {event}. How many pencils does Nora have now?'
    assert api.solve(text,llm='off')['answer']==want

@pytest.mark.parametrize('text',[
 'Nora has 17 pencils. Nora buys 5 pencils. Nora now has 19 pencils. How many pencils does Nora have now?',
 'Nora has 2 pencils. Iris has 7 pencils. Nora gives Iris 5 pencils. How many pencils does Iris have now?',
 'Nora has 17 pencils. Iris has 7 pencils. She buys 5 pencils. How many pencils does Nora have now?',
 'Nora has 17 pencils. Nora buys 5 pencils. Nora buys 3 pencils. How many pencils did Nora have after buying?',
 'Nora has 17 pencils. How many pencils do Nora and Nora have in total?',
 'Nora has 17 pencils. Nora gives Iris 5 pencils. How many pencils did Iris lose?'])
def test_contradiction_impossibility_and_unstated_actions_do_not_become_answers(text):
    assert api.solve(text,llm='off')['answer'] is None

@pytest.mark.parametrize('text',[
 'Nora has 17 pencils. Nora may have given Iris 5 pencils. Nora now has 14 pencils. How many pencils does Nora have now?',
 'Nora has 17 pencils. Nora may have given Iris 3 pencils. Nora may have given Iris 5 pencils. Nora now has 15 pencils. How many pencils does Nora have now?'])
def test_uncertain_occurrence_is_zero_or_the_stated_amount(text):
    r=episodic_verify.inspect(text)
    assert not r['ok'] and r['reason']=='EPISODIC_IMPOSSIBLE_EVENT_OCCURRENCE'
    assert api.solve(text,llm='off')['answer'] is None

def test_bound_pronoun_is_invalidated_by_a_subject_change():
    assert api.solve('Mike had 34 peaches. He gave Tom 10 peaches. How many peaches does he have now?',llm='off')['answer']=='24'
    assert api.solve('Mike had 34 peaches. He gave Tom 10 peaches. Tom buys 5 peaches. How many peaches does he have now?',llm='off')['answer'] is None

def test_unknown_count_without_an_explicit_counter_does_not_crash():
    text='凛は鉛筆をいくつか持っています。凛は鉛筆を5本買いました。今、凛は鉛筆を何本持っていますか？'
    assert api.solve(text,llm='off')['answer'] is None

@pytest.mark.parametrize('attack',['values','source','program','owner','status','unit'])
def test_source_bound_proof_cannot_be_changed_without_rejection(tmp_path,attack):
    root=tmp_path/'d';run(root,'init');text='Nora has 17 pencils. Iris has 7 pencils. Nora gives Iris 5 pencils. How many pencils does Iris have now?'
    result=cognition.solve(root,text);assert result['answer']=='12'
    assert proofs.check(result['proof'],'12');p=copy.deepcopy(result['proof'])
    if attack=='values':p['values'][p['spec']['ask']]='99'
    if attack=='source':p['source_query']=text.replace('5 pencils','6 pencils')
    if attack=='program':p['spec']['episodic_program']['rows'].pop()
    if attack=='owner':p['spec']['episodic_program']['query']['actors']=['nora']
    if attack=='status':p['spec']['episodic_program']['rows'][2]['status']='planned'
    if attack=='unit':p['spec']['answer_unit']='apple'
    assert not proofs.check(p,'12')

def test_teacher_only_formal_correct_arithmetic_cannot_override_query_time(monkeypatch):
    text='Nora had 17 pencils. Nora buys 5 pencils. How many pencils did Nora have at first?'
    sp={'schema':'tukuyo.g4.fpl/1','lang':'en','text':text,'quantities':[{'name':n,'unit':'pencil','integer':True} for n in ('start','gain','result')],
        'facts':[{'eq':'start = 17','span':'17 pencils'},{'eq':'gain = 5','span':'5 pencils'}, {'eq':'result = start + gain','span':'Nora buys 5 pencils'}],'ask':'result','answer_unit':'pencil','unused':[]}
    assert api.evaluate(sp,'llm_story')['ok']  # formal algebra alone is insufficient
    monkeypatch.setattr(api,'_own',lambda text:None)
    monkeypatch.setattr(api.L,'parents',lambda:['claude'])
    monkeypatch.setattr(api.L,'read',lambda *a,**kw:{'ok':True,'spec':copy.deepcopy(sp)})
    result=api.solve(text,llm='on');assert result['answer'] is None and result['reason']=='EPISODIC_ANSWER_DISAGREEMENT'

def test_it_reports_which_initial_quantity_is_missing():
    text='Nora has a few pencils. Nora buys 5 pencils. How many pencils does Nora have now?'
    r=api.solve(text,llm='off');assert r['answer'] is None
    assert r['information_request']['dependencies']==[{'kind':'initial_stock','owner':'nora','item':'pencil','unit':'pencil'}]

def test_two_teachers_agreeing_on_a_wrong_answer_unit_are_refused(monkeypatch):
    text='Nora has 5 pencils. How many pencils does Nora have?'
    sp={'schema':'tukuyo.g4.fpl/1','text':text,'quantities':[{'name':'amount','unit':'dollar','integer':True}],
        'facts':[{'eq':'amount = 5','span':'5 pencils'}],'ask':'amount','unused':[]}
    monkeypatch.setattr(api,'_own',lambda text:None);monkeypatch.setattr(api.L,'parents',lambda:['claude','gemini'])
    monkeypatch.setattr(api.L,'read',lambda *a,**kw:{'ok':True,'spec':copy.deepcopy(sp)})
    r=api.solve(text,llm='on',learn=False)
    assert r['answer'] is None and r['reason']=='EPISODIC_ANSWER_UNIT_MISMATCH'

def test_separate_checker_has_no_producer_or_runtime_imports():
    tree=ast.parse((ROOT/'src/tukuyo_g4/episodic_verify.py').read_text())
    imports=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):imports.extend(n.name for n in node.names)
        if isinstance(node,ast.ImportFrom):imports.append(node.module)
    assert set(imports)<={'copy','hashlib','re','unicodedata','fractions'}

@pytest.mark.parametrize('text,expected',[
 ('Ana has 4 dollars. How many cents does she have?','400'),
 ('Ana has 4 dollars. How many dollars does she have?','4'),
 ('Jo has 2 yards of ribbon. How many feet of ribbon does Jo have?','6')])
def test_typed_unit_conversion_is_delegated_to_the_existing_reader(text,expected):
    assert episodic_reader.parse(text) is None and episodic_verify.interpret(text) is None
    assert api.solve(text,llm='off')['answer']==expected

def test_new_parser_does_not_claim_old_parser_experience():
    from tukuyo_g4.life import skill_of
    text='Nora had 30 shells. She gave 8 shells to Ann. How many shells does she have left?'
    sp=episodic_reader.read(text)['spec'];r=api.evaluate(sp,'own')
    assert r['ok'] and skill_of(r)=='episodic_reader:stock_flow'

def test_numeric_transfer_family_and_conservation_extend_to_new_values():
    rng=random.Random(182031)
    for _ in range(40):
        a=rng.randrange(40,800);b=rng.randrange(1,70);c=rng.randrange(1,30)
        text=f'Oscar has {a} marbles. Mira has {b} marbles. Oscar gives Mira {c} marbles. '
        for question,value in [(f'How many marbles does Oscar have now?',a-c),(f'How many marbles does Mira have now?',b+c),(f'How many marbles do Oscar and Mira have in total?',a+b)]:
            result=api.solve(text+question,llm='off');assert result['answer']==str(value)

def test_public_cli_keeps_g4_whole_and_soul_audits(tmp_path):
    d=tmp_path/'d';run(d,'init')
    q='凛ははじめに鉛筆を何本か持っていました。凛は鉛筆を5本買いました。現在、凛は鉛筆を17本持っています。はじめに、凛は鉛筆を何本持っていましたか？'
    assert run(d,'g4-solve',q,'--llm','off')['answer']=='12'
    assert run(d,'think',q,'--llm','off')['answer']=='12'
    assert run(d,'g4-audit')['ok'] and run(d,'whole-audit')['ok']
