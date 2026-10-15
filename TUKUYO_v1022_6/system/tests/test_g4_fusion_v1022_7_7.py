"""the fusion of v1022.7.7 (the experiential soul line) with generation 4 round 6: where the two sides met, checked
together. Each test names what one side brought and what the other side found in it. Offline; no parent is asked."""
import json,os,subprocess,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_g4 import api,fpl,llm,memory,own,voice
from tukuyo_v977 import whole_state as W
from tukuyo_v1022.semantic_gate import parser_b

def _cli():
    env={k:v for k,v in os.environ.items() if not k.startswith(('TUKUYO_ANTHROPIC','TUKUYO_OPENAI','TUKUYO_GEMINI','TUKUYO_LLM','TUKUYO_CRASH','TUKUYO_CHATGPT'))}
    env['PYTHONDONTWRITEBYTECODE']='1';cmd=[sys.executable,'-B',str(ROOT/'run_tukuyo.py')];anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if anchor:cmd+=['--runtime-trust-file',anchor]
    def cli(d,*a):
        p=subprocess.run(cmd+['--data',str(d),*a],cwd=ROOT,env=env,capture_output=True,text=True,timeout=300)
        try:return json.loads(p.stdout)
        except ValueError:return {'ok':False,'rc':p.returncode,'stderr':p.stderr[-400:]}
    return cli

BAGS='Lena had fifty-four marbles. She put them into bags with six marbles in each bag. How many bags did she fill?'

def test_the_independent_parser_reads_how_many_containers():
    # parser B (v1022.6) read every 'with K ... in each' story as a product: 42 pieces put into bags of 7 were 294 bags.
    # The v1022.7.7 gate in think then held back the child's right answer (4 ASDiv dev answers). What is asked decides
    assert parser_b(BAGS)==('value','9')
    assert parser_b('The coach put 36 players into teams with 4 players on each team. How many teams were there?')==('value','9')
    assert parser_b('There are 6 boxes with 8 crayons in each box. How many crayons are there?')==('value','48')   # the things in them
    assert parser_b('Ada had 10 cookies. She put them in bags with 4 cookies in each bag. How many bags did she fill?') is None  # not whole

def test_own_readings_go_through_the_input_checks_but_three_that_refuse_a_kind_of_wording():
    # the v1022.5.2 independent input audit holds back stories told with 'If ...' (EVENT_NOT_ESTABLISHED), '... so each
    # friend got the same amount' (EQUAL_SHARING_NOT_ESTABLISHED) and one more: on ASDiv dev these held back 34 right
    # answers of the child's own reader and none of its wrong ones. They are set aside for its own readings; every other
    # check applies (an asked entity that is not the one declared, the v1022.7.4 event-scope guard). A reading that only
    # parents gave goes through all of them
    t='Uncle Rob bought 96 pretzels. If he wants to give them to his 8 cousins equally, how many pretzels can each cousin get?'
    assert api.solve(t,llm='off')['answer']=='12'
    assert api._input_coverage(t,'12',mine=True)=={'recognized':False,'ok':True,'set_aside':'EVENT_NOT_ESTABLISHED'}
    assert api._input_coverage(t,'12')['reason']=='EVENT_NOT_ESTABLISHED'
    balls='There are 4 red balls and 6 blue apples. How many red balls in total?'
    r=api.solve(balls,llm='off');assert r['answer'] is None and r['reason']=='QUERY_ENTITY_MISMATCH'
    ja='りんごが10個ありました。5個食べたわけではありません。りんごは何個ありますか。'
    assert api._input_coverage(ja,'5',mine=True)['reason']=='UNRESOLVED_EVENT_SCOPE'

def test_a_size_or_age_word_of_the_question_must_be_told_of_the_asked_thing():
    # found while merging (the v1022.5.2 test of '4 red balls and 6 blue apples'): the reader drops 'big', 'small', 'new',
    # 'old' ... with 'more' and 'left', so it answered 3 to 'How many small dogs' about 3 big dogs and 2 small cats
    for t in ('Sam has 3 big dogs and 2 small cats. How many small dogs does Sam have?',
              'Ann has 5 old books and 3 new pens. How many new books does Ann have?'):
        r=api.solve(t,llm='off');assert r['answer'] is None and any('ASKED_KIND_NOT_TOLD' in str(x.get('reason')) for x in r['readings']),t
        assert 'that the story does not tell of' in voice.explain(t,r,None)['said']                  # and it says why
    for t,a in (('She had 4 books. She bought 3 new books. How many new books did she buy?','3'),
                ('Tom had 50 old stamps. He sold 20 old stamps. How many old stamps does he have left?','30'),
                ('There are 4 small boxes with 6 pens in each box. How many pens are there?','24')):
        assert api.solve(t,llm='off')['answer']==a,t

def test_parents_who_write_the_same_thing_another_way_agree(monkeypatch):
    # v1022.6.5 holds back two readings with the same number of different things ('5 apples', '5 oranges'). It compared
    # the units as written, so parents who wrote 'cookies' did not agree with one who wrote 'cookie', nor '$' with
    # 'dollars' (the recorded parents of the tests all write the same unit, and did not show it)
    def spec(unit):
        return {'schema':fpl.SCHEMA,'text':q,'quantities':[{'name':'amount','unit':unit,'integer':True}],
                'facts':[{'eq':'amount = 5','span':f'5 {item}'}],'ask':'amount','unused':[]}
    monkeypatch.setattr(api,'_own',lambda text:None);monkeypatch.setattr(llm,'parents',lambda:['claude','gemini'])
    # v1022.8 binds the answer unit to the question too. Equivalent dollar
    # spellings are tested on dollars; answering dollars to cookies is refused.
    for a,b,item,agree in (('cookie','cookies','cookies',True),('$','dollars','dollars',True),('pieces of candy','candies','candies',True),('apple','orange','cookies',False),('cent','dollar','cookies',False)):
        q=f'Mia has 5 {item}. How many {item} does Mia have?'
        monkeypatch.setattr(llm,'read',lambda text,view,parent,a=a,b=b:{'ok':True,'spec':spec(a if parent=='claude' else b)})
        r=api.solve(q,llm='on',learn=False)
        assert (r['answer']=='5') if agree else (r['answer'] is None and r['reason']=='UNIT_DISAGREEMENT'),(a,b,r.get('reason'))

def test_think_answers_a_question_about_containers(tmp_path):
    cli=_cli();d=tmp_path/'d';assert cli(d,'init','--individual-id','FUSION-THINK')['ok']
    r=cli(d,'think','--',BAGS)
    assert r['answer']=='9' and not r.get('uncertain') and r['gen4']['route']=='own',r
    assert cli(d,'whole-audit')['ok']

def test_an_older_version_of_what_it_remembered_is_not_taken_back(tmp_path):
    # its parents agreed on an answer, and later agreed on another: the first is contested and no longer used. Putting
    # back the older store (signed by the child itself) brought the contested answer back at the next start, and every
    # audit passed. Now each signature names the version it replaced (own.py, after the v1022 commit chains), and an
    # older one is refused like a store changed by hand
    cli=_cli();d=tmp_path/'d';assert cli(d,'init','--individual-id','FUSION-MEMORY')['ok']
    m=memory.Memory(d);q='What is the capital of Atlantis?'
    assert m.remember(q,[{'parent':'claude','answer':'Poseidonia'},{'parent':'gemini','answer':'Poseidonia'}]);W.sync(d)
    older=(d/'g4'/'remembered.json').read_bytes();assert m.recall(q)['answer']=='Poseidonia'
    assert m.remember(q,[{'parent':'claude','answer':'Atlantica'},{'parent':'chatgpt','answer':'Atlantica'}]) is None and m.status=='contested'
    W.sync(d);assert m.recall(q) is None and W.quick_audit(d)['ok']
    (d/'g4'/'remembered.json').write_bytes(older)
    with pytest.raises(ValueError,match='REMEMBERED_ROLLED_BACK'):m.recall(q)
    assert not own.unsynced(d) and W.quick_audit(d)['errors']==['COMPONENT_DRIFT:g4_remembered']
    W.sync(d);assert W.quick_audit(d)['errors']==['COMPONENT_DRIFT:g4_remembered']          # the whole state does not take it in
    me=cli(d,'g4-self');assert me['ok'] and me['refused']['remembered']=='REMEMBERED_ROLLED_BACK'
    assert cli(d,'whole-audit')['errors']==['COMPONENT_DRIFT:g4_remembered']

def test_an_unsigned_store_put_into_an_individual_is_not_taken(tmp_path):
    # before: an individual that had not used generation 4 yet (its whole state had recorded nothing about it) read an
    # unsigned store put into it as its own, answered from it and signed it at the next save. v1022.6.5 refused this for
    # what it learned; now no generation-4 store is taken unsigned unless the whole state recorded that very file
    cli=_cli();d=tmp_path/'d';assert cli(d,'init','--individual-id','FUSION-PLANT')['ok']
    q='What is the capital of Atlantis?';m=memory.Memory(d)
    entries={m.key(q):{'question':q,'answer':'Poseidonia','parents':['chatgpt','claude'],'models':['x'],'utc':'2026-10-12T00:00:00Z','confirmed':5}}
    (d/'g4').mkdir();(d/'g4'/'remembered.json').write_text(json.dumps({'schema':memory.SCHEMA,'entries':entries,'seal':m._seal(entries)}),encoding='utf-8')
    with pytest.raises(ValueError,match='REMEMBERED_NOT_SIGNED'):m.recall(q)
    r=cli(d,'g4-ask','--llm','off','--',q);assert r['ok'] and r.get('answer') is None and r.get('route')!='remembered',r
    assert cli(d,'g4-self')['refused']['remembered']=='REMEMBERED_NOT_SIGNED'
    assert 'signed' not in json.loads((d/'g4'/'remembered.json').read_text(encoding='utf-8'))      # not signed as its own
