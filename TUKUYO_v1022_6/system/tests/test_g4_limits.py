"""generation 4: the limits named after the v1022.7.7 fusion, measured and strengthened (evidence_gen4/LIMITS_2026-10-13.md).
Offline: no parent is asked; the parents are fixtures."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tools'))
from tukuyo_g4 import api,check,fpl,learn,llm,reader
from tukuyo_v1022.semantic_gate import parser_b
import limits_probes

def _cli():
    env={k:v for k,v in os.environ.items() if not k.startswith(('TUKUYO_ANTHROPIC','TUKUYO_OPENAI','TUKUYO_GEMINI','TUKUYO_LLM','TUKUYO_CRASH','TUKUYO_CHATGPT'))}
    env['PYTHONDONTWRITEBYTECODE']='1';cmd=[sys.executable,'-B',str(ROOT/'run_tukuyo.py')];anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if anchor:cmd+=['--runtime-trust-file',anchor]
    def cli(d,*a):
        p=subprocess.run(cmd+['--data',str(d),*a],cwd=ROOT,env=env,capture_output=True,text=True,timeout=300)
        try:return json.loads(p.stdout)
        except ValueError:return {'ok':False,'rc':p.returncode,'stderr':p.stderr[-400:]}
    return cli

def test_what_did_not_happen_is_not_read_as_done():
    # before: 'he would have bought 9' read as bought, 'might buy 4 more' as bought, 'gave them back' unseen, 'shared,
    # but not equally' as equal shares (5 wrong answers of 48 probes; the input audit passed all 5 as outside its schemas)
    for t in ('If Ann gave away 4 of her shells, she would have 11 shells left. How many shells does Ann have?',
              'If Ben had bought 2 more books, he would have bought 9 books. How many books did Ben buy?',
              'Omar has 9 toy cars. He might buy 4 more toy cars next week. How many toy cars does Omar have now?',
              'Rita had 15 shells. She gave 5 shells to Ann, but Ann gave them back. How many shells does Rita have now?',
              '30 candies were shared among 5 kids, but not equally. How many candies did each kid get?'):
        assert api.solve(t,llm='off')['answer'] is None,t
    # what the story says will happen, asked about, is still read; so is a hypothetical problem
    assert api.solve('Eva has 14 pencils. If she gives 5 pencils to Sam, how many pencils will she have?',llm='off')['answer']=='9'
    assert api.solve('If Rosa saves 5 dollars every week, how many dollars will she save in 8 weeks?',llm='off')['answer']=='40'

def test_the_probes_give_no_wrong_answer():
    for cat,ps in limits_probes.PROBES.items():
        for t,want,_ in ps:
            a=api.solve(t,llm='off')['answer']
            assert a is None or (want is not None and limits_probes.grade(a,want,True)=='right'),(cat,t,a)
            b=parser_b(t)
            assert b is None or (want is not None and str(b[1])==want),('parser B',cat,t,b)

def test_size_and_age_words_tell_kinds_apart():
    for t,a in (('Ana has 7 big apples. She ate 2 big apples. How many big apples does she have left?','5'),
                ('Ana has 7 big apples and 3 small apples. How many apples does she have in all?','10'),
                ('Ben has 6 old coins and 5 new coins. How many new coins does Ben have?','5'),
                ('There are 8 little ducks and 2 big ducks. How many ducks are there?','10')):
        assert api.solve(t,llm='off')['answer']==a,t
    assert api.solve('Sam has 3 big dogs and 2 small cats. How many small dogs does Sam have?',llm='off')['answer'] is None

def test_parser_b_leaves_undone_events_and_item_totals_undecided():
    assert parser_b('Max has 12 marbles. He is going to lose 5 marbles in a game later. How many marbles does Max have now?') is None   # was 7
    assert parser_b('Ben did not buy 6 boxes of pens with 4 pens in each box. How many pens did Ben buy?') is None                    # was 24
    assert parser_b('Jack puts 24 cookies on plates with 6 cookies on each plate. How many cookies are there?')==('value','24')       # was 144
    assert parser_b('There are 5 vans with 7 kids in each van. How many kids are there?')==('value','35')
    assert parser_b('Tom has 9 apples. He ate 4 apples. How many apples does he have left?')==('value','5')

def test_parents_quote_and_name_units_loosely():
    t='Kim saw 4 cats in the morning. Later she saw 3 more cats. How many cats did she see in all?'
    sp=reader.read(t)['spec']
    for f in sp['facts']:
        if f.get('span'):f['span']=f['span'].lower().rstrip('.')+'.'               # 'kim saw 4 cats in the morning.'
    for q in sp['quantities']:
        if q.get('unit')=='cat':q['unit']='Cats'
    r=api.evaluate(sp,'parent');assert r['ok'] and r['value']=='7',r.get('reason')
    bad=json.loads(json.dumps(sp));bad['facts'][0]['span']='Kim saw 4 dogs in the morning'   # not a quote of the text
    assert not api.evaluate(bad,'parent')['ok']
    assert check._locate('He has 5 apples and 3 pears.','5 APPLES.') and not check._locate('He has 5 apples.','5 apple pies')
    assert fpl.parse_unit('cookies')==fpl.parse_unit('cookie')=={'cookie':1} and fpl.parse_unit('candies')=={'candy':1}
    assert not api._different_things('item','groups') and api._different_things('apple','orange')
    # a unit in its English plural next to a rate in the singular: before, 'loaves' and 'dollar/loaf' clashed in the unit
    # check and the reading was refused (21 of 505 readings written with English plurals)
    for t,unit,plural,value in (('A bakery sells each loaf of bread for 4 dollars. Ann buys 6 loaves of bread. How many dollars does she pay?','loaf','loaves','24'),
                                ('Each ticket costs 3 dollars per person. There are 5 people. How many dollars do they pay in all?','person','people','15'),
                                ('There are 5 buses. Each bus carries 40 children. How many children are there?','bus','buses','200')):
        sp=reader.read(t)['spec']
        for q in sp['quantities']:
            if q.get('unit')==unit:q['unit']=plural
        r=api.evaluate(sp,'parent');assert r['ok'] and r['value']==value,(t,r.get('reason'))
    assert fpl.parse_unit('t-shirts')==fpl.parse_unit('T-shirt') and fpl.parse_unit('pieces of candy')==fpl.parse_unit('piece of candy')
    assert fpl.parse_unit('gloves')=={'glove':1} and not api._different_things('barbie','barbies') and api._different_things('person','dollar')

def test_a_refusal_for_a_kind_of_wording_asks_both_ways(monkeypatch):
    # a reading only parents gave, refused for 'If he wants to give them ...' (EVENT_NOT_ESTABLISHED): each family that
    # agreed reads it the other way too, and the child answers only when every reading agrees
    t='Uncle Rob bought 96 pretzels. If he wants to give them to his 8 cousins equally, how many pretzels can each cousin get?'
    right=reader.read(t)['spec'];wrong=json.loads(json.dumps(right))
    for f in wrong['facts']:f['eq']=f['eq'].replace('*','+')                 # another reading: per group + groups
    monkeypatch.setattr(api,'_own',lambda text:None);monkeypatch.setattr(llm,'parents',lambda:['claude','gemini'])
    asked=[]
    def read(text,view,parent):
        asked.append((parent,view));return {'ok':True,'spec':wrong if (parent,view)==('gemini','goal') and bad else right}
    monkeypatch.setattr(llm,'read',read)
    bad=False;r=api.solve(t,llm='on',learn=False)
    assert r['answer']=='12' and sorted(asked)==[('claude','goal'),('claude','story'),('gemini','goal'),('gemini','story')]
    asked.clear();bad=True;r=api.solve(t,llm='on',learn=False)
    assert r['answer'] is None and r['reason']=='EVENT_NOT_ESTABLISHED'
    monkeypatch.setattr(llm,'parents',lambda:['claude']);asked.clear();bad=False   # one family: not enough to ask more
    assert api.solve(t,llm='on',learn=False)['answer'] is None

def test_an_individual_from_before_signing_takes_its_stores_back(tmp_path):
    cli=_cli();d=tmp_path/'old';assert cli(d,'init','--individual-id','LEGACY-TEST')['ok']
    g=d/'g4';g.mkdir();sha=lambda o:hashlib.sha256(json.dumps(o,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    t='Tom has 3 boxes of pens. There are 6 pens in each box. He gives away 4 pens. How many pens does Tom have now?'
    tpl=learn.template(reader.read(t)['spec']);tid=hashlib.sha256(tpl['key'].encode()).hexdigest()[:24]
    tpls={tid:{**tpl,'example':t,'provenance':{'route':'claude+gemini','parents':['claude','gemini']},'seen':1,'learned_utc':'2026-10-08T00:00:00Z'}}
    (g/'learned.json').write_text(json.dumps({'schema':learn.SCHEMA,'templates':tpls,'sha256':sha(tpls)},indent=1,sort_keys=True))
    ent={'k':{'question':'What is the capital of France?','answer':'Paris','parents':['claude','gemini'],'models':['m'],'utc':'2026-10-09T00:00:00Z','confirmed':1}}
    (g/'remembered.json').write_text(json.dumps({'schema':'tukuyo.g4.remembered/1','entries':ent,'seal':sha(ent)},sort_keys=True))
    (g/'life.json').write_text(json.dumps({'first_alone':[tid]}))
    r=cli(d,'g4-self');assert not r['ok'] and r['error'].endswith('G4_LEARNING_UNSIGNED_LEGACY') and 'g4-adopt-legacy' in r['advice']
    look=cli(d,'g4-adopt-legacy');assert look['ok'] and look['adopted'] is None
    assert look['would_adopt']['learned']['examples']==[t] and look['would_adopt']['remembered']['answers']==1
    assert cli(d,'g4-self')['ok'] is False                                        # looking changes nothing
    assert cli(d,'g4-adopt-legacy','--yes')['adopted']=={'learned':1,'remembered':1,'life':1}
    me=cli(d,'g4-self');assert me['ok'] and me['templates_learned']==1 and me['remembered_answers']==1 and not me.get('refused')
    v=t.replace('3 boxes','5 boxes').replace('6 pens','8 pens').replace('4 pens','7 pens')
    assert cli(d,'g4-solve','--llm','off','--',v)['answer']=='33' and cli(d,'whole-audit')['ok'] and cli(d,'g4-audit')['ok']
    assert cli(d,'g4-adopt-legacy')['would_adopt']=={}
    # a store whose body does not match its seal is not adopted
    e=tmp_path/'bad';assert cli(e,'init','--individual-id','LEGACY-BAD')['ok'];(e/'g4').mkdir()
    (e/'g4'/'remembered.json').write_text(json.dumps({'schema':'tukuyo.g4.remembered/1','entries':ent,'seal':'0'*64}))
    r=cli(e,'g4-adopt-legacy','--yes');assert not r['ok'] and r['error'].endswith('REMEMBERED_STORE_SEAL')

def test_a_witness_outside_tells_a_store_put_back(tmp_path,monkeypatch):
    # the rollback window (LIMITS §6): a store written twice before the whole state was synced, then put back to the first
    # of the two writes; nothing in the data directory can tell. A witness the owner keeps outside it can
    from tukuyo_g4 import memory,own
    from tukuyo_v977 import whole_state as W
    from tukuyo_v1019.transaction import transactional
    cli=_cli();P=lambda a:[{'parent':'claude','answer':a},{'parent':'gemini','answer':a}]
    for n in ('a','b','c'):assert cli(tmp_path/n,'init','--individual-id','WITNESS-'+n.upper())['ok']
    def put_back(d):
        m=memory.Memory(d);m.remember('Q1?',P('one'));W.sync(d)
        m.remember('Q2?',P('two'));v2=(d/'g4'/'remembered.json').read_bytes()
        m.remember('Q3?',P('three'));(d/'g4'/'remembered.json').write_bytes(v2);return m
    m=put_back(tmp_path/'a');assert own.unsynced(tmp_path/'a') and m.recall('Q2?') and not m.recall('Q3?')     # without: taken in
    w=tmp_path/'witness';monkeypatch.setenv('TUKUYO_G4_WITNESS',str(w))
    m=put_back(tmp_path/'b');assert own.witnessed(tmp_path/'b')=={'remembered':3}
    with pytest.raises(ValueError,match='REMEMBERED_ROLLED_BACK'):m.load()
    assert not own.unsynced(tmp_path/'b') and own.behind_witness(tmp_path/'b')==['remembered']
    (tmp_path/'b'/'g4'/'remembered.json').unlink()                                       # taken away
    with pytest.raises(ValueError,match='REMEMBERED_ROLLED_BACK'):m.load()
    # a transaction that stops before it is applied does not move the witness; one that is applied does
    c=tmp_path/'c'
    @transactional()
    def remember(data,q,fail):
        memory.Memory(data).remember(q,P('nine'))
        if fail:raise RuntimeError('stop')
    with pytest.raises(RuntimeError):remember(c,'Q9?',True)
    assert own.witnessed(c)=={} and memory.Memory(c).recall('Q9?') is None
    remember(c,'Q8?',False);assert own.witnessed(c)=={'remembered':1} and memory.Memory(c).recall('Q8?')
    # a witness kept inside the data directory, or another individual's, is refused
    monkeypatch.setenv('TUKUYO_G4_WITNESS',str(c/'g4'))
    with pytest.raises(ValueError,match='G4_WITNESS_INSIDE_DATA'):own.witnessed(c)
    monkeypatch.setenv('TUKUYO_G4_WITNESS',str(w));f=own._witness_file(c);f.write_bytes(own._witness_file(tmp_path/'b').read_bytes())
    with pytest.raises(ValueError,match='G4_WITNESS_NOT_ITS_OWN'):own.witnessed(c)
    # the whole data directory put back to an earlier copy: the whole state agrees with it, the witness does not
    monkeypatch.delenv('TUKUYO_G4_WITNESS');d=tmp_path/'d';assert cli(d,'init','--individual-id','WITNESS-D')['ok']
    monkeypatch.setenv('TUKUYO_G4_WITNESS',str(w));cliw=_cli()
    hard='Ivy has some shells. Kai has 7 more shells than Ivy. How many shells does Kai have?'
    assert cliw(d,'g4-solve','--llm','off','--',hard)['answer'] is None
    import shutil;shutil.copytree(d,tmp_path/'copy')
    assert cliw(d,'g4-solve','--llm','off','--',hard.replace('7','8'))['answer'] is None and cliw(d,'whole-audit')['ok']
    shutil.rmtree(d);shutil.copytree(tmp_path/'copy',d)
    assert cli(d,'whole-audit')['ok']                                                    # without the witness: nothing tells
    r=cliw(d,'whole-audit');assert not r['ok'] and r['errors']==['G4_WITNESS_AHEAD:g4_unread'],r
    assert cliw(d,'g4-self')['refused']=={'unread':'UNREAD_ROLLED_BACK'}
