"""generation 4: noticing its own growth (growth.py). Alone, the child keeps the problems it could not read, knows its
weak spots and says what it wants to learn; when it can read alone what it could not - a wording its parents taught it,
or its own reader reads it now - it notices (one experience in its soul), says so, and that weak spot is gone. Recorded
replies for the parents; the wording is our own."""
import json,os,shutil,subprocess,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_g4 import api,growth,llm,own,voice
from tukuyo_g4.learn import Store
from tukuyo_v977 import whole_state as W

ENV=('TUKUYO_ANTHROPIC_API_KEY','TUKUYO_OPENAI_API_KEY','TUKUYO_GEMINI_API_KEY','TUKUYO_OPENAI_MODEL','TUKUYO_GEMINI_MODEL',
     'TUKUYO_LLM_PARENTS','TUKUYO_LLM_VOICE','TUKUYO_LLM_REPLAY','TUKUYO_LLM_RECORD')
PARENTS=('claude','chatgpt','gemini')
T='When three times a number is decreased by twelve, the result is 30. What is the number?'
T2='When four times a number is decreased by eight, the result is 28. What is the number?'
SAM='Sam is 4 years older than his sister. In 3 years, the sum of their ages will be 30. How old is Sam now?'
MIA='Mia had some shells. She found 4 more shells on the beach. How many shells does she have now?'
BIKE='A bike costs $200. It is on sale for 25% off. How much does the bike cost on sale?'
RUN='Kai ran for 1 hour and 15 minutes on Monday and 40 minutes on Tuesday. How many minutes did he run in all?'
def _q(names):return [{'name':n,'unit':'1','integer':False,'signed':False,'about':n} for n in names]
R={'readable':True,'quantities':_q(('twelve','factor','result','number')),'ask':'number','answer_unit':'','unused':[],
   'facts':[{'eq':'twelve = 12','span':'decreased by twelve','known':''},{'eq':'factor = 3','span':'three times','known':''},
            {'eq':'result = 30','span':'the result is 30','known':''},
            {'eq':'factor * number - twelve = result','span':'When three times a number is decreased by twelve, the result is 30','known':''}]}

@pytest.fixture
def clean(monkeypatch):
    for k in ENV:monkeypatch.delenv(k,raising=False)
    llm._replay_cache.clear();yield monkeypatch;llm._replay_cache.clear()

def _line(parent,text,o):
    return {'parent':parent,'hash':llm.request_hash(llm._kind(parent,'read:story:'+llm.PROMPT_VERSION),llm.system_prompt('story'),'Text: '+text),
            'ok':True,'text':json.dumps(o),'model':'fixture-'+parent}
def _write(path,lines):path.write_text('\n'.join(json.dumps(x) for x in lines)+'\n',encoding='utf-8');return path

def _cli():
    env={k:v for k,v in os.environ.items() if not k.startswith(('TUKUYO_ANTHROPIC','TUKUYO_OPENAI','TUKUYO_GEMINI','TUKUYO_LLM','TUKUYO_CRASH'))}
    env['PYTHONDONTWRITEBYTECODE']='1';cmd=[sys.executable,'-B',str(ROOT/'run_tukuyo.py')];anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if anchor:cmd+=['--runtime-trust-file',anchor]
    def cli(d,*a,replay=None,crash=None):
        e=dict(env,**({'TUKUYO_LLM_REPLAY':str(replay)} if replay else {}),**({'TUKUYO_CRASH_POINT':crash} if crash else {}))
        p=subprocess.run(cmd+['--data',str(d),*a],cwd=ROOT,env=e,capture_output=True,text=True,timeout=300)
        try:return json.loads(p.stdout)
        except ValueError:return {'ok':False,'rc':p.returncode,'stderr':p.stderr[-400:]}
    return cli

def _events(d):
    p=Path(d)/'v977'/'SOUL_EVENTS.jsonl'
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if '"g4:' in x] if p.is_file() else []

def test_what_it_could_not_read_and_why(clean):
    kinds={'EN:QUESTION_FORM':'question','EN:NO_SCHEMA':'story','SOLVE:UNDERDETERMINED:a,b':'missing','EN:VAGUE_EVENT':'missing',
           'EN:PRONOUN_AMBIGUOUS':'who','EN:schema_holding:UNUSED:change:15':'number','SOLVE:INCONSISTENT:fact 2':'wrong','CHECK:UNIT':'wrong',
           'V1022:NO_MATCH':'older','EN:COMPARE_PARTIES':'compare','EN:QUESTION_DIFFERENCE':'compare','EN:PATTERN':'pattern','OWN_UNREAD':'other'}
    assert {k:growth.kind_of(k) for k in kinds}==kinds and all(growth.WORDS[k][0] and growth.WORDS[k][1] for k in kinds.values())
    assert growth.cannot_read(api.solve(T2,llm='off'))=={'why':'question','reason':'EN:QUESTION_FORM','parents':None}
    assert growth.cannot_read(api.solve(MIA,llm='off'))['why']=='missing'
    assert growth.cannot_read(api.solve(BIKE,llm='off')) is None                                     # it read it
    own_fails={'route':'own','ok':False,'reason':'EN:QUESTION_FORM'}
    agreed=[{'route':'llm_story','parent':'claude','ok':True,'value':'9'},{'route':'llm_gemini_story','parent':'gemini','ok':True,'value':'9'}]
    # it read it and held back; it learned it in this thought; what it learned was contested: not kept
    assert growth.cannot_read({'answer':None,'reason':'SELF_DOUBT:x','readings':[{'route':'own','ok':True,'value':'5'}]}) is None
    assert growth.cannot_read({'answer':'9','route':'claude+gemini','learned':'k','readings':[own_fails]+agreed}) is None
    assert growth.cannot_read({'answer':None,'readings':[{'route':'learned','ok':False,'reason':'TEMPLATE_CONTESTED'},own_fails]}) is None
    # its parents read what it could not, and it could not learn the wording: kept, and that they could
    assert growth.cannot_read({'answer':'9','route':'claude+gemini','learned':None,'readings':[own_fails]+agreed})['parents']=='agreed'
    assert growth.cannot_read({'answer':None,'reason':'DISAGREE:1,9','readings':[own_fails,agreed[0],{**agreed[1],'value':'1'}]})['parents']=='disagreed'
    # think: only what was taken as a problem; a question is not a problem
    assert growth.cannot_read({'answer':None,'gen4':{'readings':[own_fails]}}) is None
    assert growth.cannot_read({'answer':None,'gen4':{'readings':[own_fails,agreed[0]]}})['parents']=='one'
    assert growth.cannot_read({'kind':'question','answer':'Paris','readings':[own_fails]}) is None
    # Japanese: the older core cannot tell a problem from a question with a number in it, so only what it was given as a
    # problem (g4-solve), or what a parent read as one, is kept
    older={'route':'v1022','ok':False,'reason':'V1022:MEMORY_PREMISES_MISSING'}
    assert growth.cannot_read({'answer':None,'recognized':False,'gen4':{'readings':[older]}}) is None
    assert growth.cannot_read({'kind':'problem','answer':None,'readings':[older]}) is None
    assert growth.cannot_read({'answer':None,'reason':'NO_VERIFIED_READING','readings':[older]})=={'why':'older','reason':'V1022:MEMORY_PREMISES_MISSING','parents':None}
    assert growth.cannot_read({'answer':None,'gen4':{'readings':[older,agreed[0]]}})['parents']=='one'

def test_what_it_keeps_of_a_problem(tmp_path,monkeypatch):
    u=growth.Unread(tmp_path);k=Store.key_of(T2)
    a=u.keep(T2,k,'question','EN:QUESTION_FORM','agreed');assert u.keep('  '+T2.replace(' ','  '),k,'question','EN:QUESTION_FORM',None)==a
    e=u.load()['entries'][a];assert (e['met'],e['parents'],e['first'],e['last'])==(2,'agreed',1,2)    # met alone later: what its parents did stays
    u.grow([[a,'learned','9',['gemini','claude']]]);assert u.load()['entries'][a]['grown']=={'seq':3,'how':'learned','value':'9','teachers':['claude','gemini']}
    u.grow([[a,'own','9',[]]]);assert u.load()['entries'][a]['grown']['how']=='learned'                # noticed once
    u.keep(T2,k,'question','EN:QUESTION_FORM',None);e=u.load()['entries'][a]                         # it cannot read it again: open again
    assert 'grown' not in e and e['lost']=={'seq':4,'why':'cannot_read_again','was':'9'} and growth.report(tmp_path)['cannot_read_yet']==1
    u.grow([[a,'learned','5',['claude','gemini']]]);assert 'corrected_from' not in u.load()['entries'][a]['grown']
    # two parents read the wording it learned otherwise: the growth is given up, and what it had read is kept
    u.lose([a]);e=u.load()['entries'][a];r=growth.report(tmp_path)
    assert 'grown' not in e and e['why']=='contested' and e['lost']=={'seq':6,'why':'contested','was':'5','teachers':['claude','gemini']}
    assert (r['can_read_now'],r['cannot_read_yet'])==(0,1) and [q['kind'] for q in r['wants_to_learn']]==['contested']
    # taught again: it reads it again, otherwise than before, and says so
    u.grow([[a,'learned','9',['chatgpt','claude']]]);r=growth.report(tmp_path)
    assert u.load()['entries'][a]['grown']['corrected_from']=='5' and r['corrected']==1 and 'two of my parents later read the wording otherwise' in ' '.join(r['told'])
    said=growth.before(tmp_path,T2,{'answer':'9','value':'9','readings':[{'route':'learned','ok':True,'value':'9'}]})
    assert said=='Before, what I had learned for this wording read this problem as 5, and two of my parents later read the wording otherwise; now I read it as 9: I learned this wording again from my parents.'
    # a bounded record: the oldest it has since learned to read go first, then the oldest
    monkeypatch.setattr(growth,'MAX',3)
    b=u.keep(SAM,Store.key_of(SAM),'story','EN:NO_SCHEMA',None);c=u.keep(MIA,Store.key_of(MIA),'missing','SOLVE:UNDERDETERMINED',None)
    u.grow([[c,'own','1',[]]]);u.keep(BIKE,Store.key_of(BIKE),'story','EN:NO_SCHEMA',None)
    assert set(u.load()['entries'])=={b,c,u.entry_id(BIKE)}

def test_it_reads_again_every_problem_it_could_not_read(tmp_path):
    # g4-reflect reads again all it keeps, not only the oldest (an experiment found a child that noticed 2 of 23)
    u=growth.Unread(tmp_path)
    for i in range(120):t=T2.replace('28',str(100+i));u.keep(t,Store.key_of(t),'question','EN:QUESTION_FORM',None)
    u.keep(BIKE,Store.key_of(BIKE),'story','EN:NO_SCHEMA',None)
    now,still,n=growth.look(tmp_path);assert n==121 and [x['text'] for x in now]==[BIKE] and len(still)==120

def test_a_learned_reading_is_said_with_this_problems_numbers(tmp_path,clean):
    _write(tmp_path/'r.jsonl',[_line(p,T,R) for p in PARENTS]);clean.setenv('TUKUYO_LLM_REPLAY',str(tmp_path/'r.jsonl'));llm._replay_cache.clear()
    assert api.solve(T,data=tmp_path)['learned']==Store.key_of(T2)
    r=api.solve(T2,llm='off',data=tmp_path);v=voice.explain(T2,r,tmp_path)
    assert r['answer']=='9' and r['route']=='learned' and v['read'][0]=='"decreased by eight": eight = 8' and 'twelve' not in v['said']
    assert 'From factor × number - eight = result (4 × 9 - 8 = 28): number = 9' in v['read']

def test_it_notices_when_it_can_read_what_it_could_not(tmp_path,clean):
    cli=_cli();d=tmp_path/'d';cli(d,'init','--individual-id','GROWTH-TEST');assert (d/'state'/'integration_state.json').is_file()
    rec=_write(tmp_path/'r.jsonl',[_line(p,T,R) for p in PARENTS])
    first=cli(d,'g4-solve','--llm','off','--',T2)
    assert first['answer'] is None and first['voice']['before'] is None and first['life']==[]
    again=cli(d,'g4-solve','--llm','off','--',T2)
    assert again['voice']['before']=='I could not read it alone when I met it before, either.' and again['voice']['before'] in again['voice']['said']
    for t in (SAM,MIA):assert cli(d,'g4-solve','--llm','off','--',t)['answer'] is None
    g=cli(d,'g4-self')['growth']
    assert (g['could_not_read'],g['cannot_read_yet'],g['can_read_now'],g['grew'])==(3,3,0,{})
    assert {q['kind']:q['problems'] for q in g['weak_spots']}=={'question':1,'story':1,'missing':1}
    # what it wants to learn: the question it met twice first; never the story whose amount is not given
    assert [(q['kind'],q['example']) for q in g['wants_to_learn']]==[('question',T2),('story',SAM)]
    assert g['told'][0]=='I could not read 3 problems alone when I met them; I cannot read any of them alone yet.'
    ev=_events(d);un=(d/'g4'/'unread.json').read_bytes();look=cli(d,'g4-reflect')
    assert [x['text'] for x in look['intentions'] if x['do']=='learn_to_read']==[T2,SAM]
    assert look['open']['could_not_read']==3 and look['open']['can_read_now']==0
    assert _events(d)==ev and (d/'g4'/'unread.json').read_bytes()==un                       # looking changes nothing
    # its parents teach it T, the wording of T2 with other numbers: it notices that it can read T2 alone now
    r=cli(d,'think','--',T,replay=rec)
    assert r['answer']=='14' and [x for x in r['life'] if x['theme']=='g4:grew']==[{'kind':'discovery','theme':'g4:grew','relation':''}]
    g=cli(d,'g4-self')['growth']
    assert g['can_read_now']==1 and g['grew']=={'learned_from_parents':1} and {q['kind'] for q in g['weak_spots']}=={'story','missing'}
    assert g['told'][0]=='I could not read 3 problems alone when I met them; now I can read 1 of them alone (1 with what my parents taught me).'
    now=cli(d,'g4-solve','--llm','off','--',T2)
    assert now['answer']=='9' and now['voice']['before']=='I could not read this problem alone when I met it before; now I can: I learned this wording from ChatGPT, Claude and Gemini.'
    assert not [x for x in now['life'] if x['theme']=='g4:grew']                             # noticed once
    other=cli(d,'g4-solve','--llm','off','--',T2.replace('28','32'))
    assert other['answer']=='10' and other['voice']['before'].startswith('I could not read a problem worded like this alone before; now I can')
    me=cli(d,'g4-self');assert me['life_story']['grew']==1 and 'It noticed it had grown once' in ' '.join(me['life_story']['told'])
    assert [x['text'] for x in cli(d,'g4-reflect')['intentions'] if x['do']=='learn_to_read']==[SAM]
    # a child without that past learns the same wording, and has nothing to notice
    f=tmp_path/'fresh';cli(f,'init','--individual-id','GROWTH-FRESH');cli(f,'think','--',T,replay=rec)
    fv=cli(f,'g4-solve','--llm','off','--',T2);assert fv['answer']=='9' and fv['voice']['before'] is None and not [e for e in _events(f) if e['theme']=='g4:grew']
    au=cli(d,'g4-audit');assert au['ok'] and au['unread']=={'ok':True,'kept':3,'grown':1} and cli(d,'whole-audit')['ok']

def test_it_notices_its_own_reader_grew_and_tries_again_on_its_own(tmp_path,clean):
    cli=_cli();d=tmp_path/'d';cli(d,'init','--individual-id','GROWTH-OWN')
    # problems an earlier version of its reader could not read, kept as that version kept them
    from tukuyo_v977.whole_state import sync
    for t in (BIKE,RUN):growth.Unread(d).keep(t,Store.key_of(t),'story','EN:NO_SCHEMA',None)
    sync(d)
    ev=_events(d);look=cli(d,'g4-reflect')
    assert look['open']['can_read_now']==2 and [x['do'] for x in look['intentions']]==['try_again_alone','try_again_alone'] and _events(d)==ev
    # with no parent configured it asks nobody, but tries again alone what it can read now
    r=cli(d,'g4-reflect','--act')
    assert r['acted']==[] and r['note'].startswith('NO_PARENT_TO_ASK') and [x['answer'] for x in r['tried_alone']]==['150','115']
    assert [e['theme'] for e in _events(d)]==['g4:grew','g4:grew']
    g=cli(d,'g4-self')['growth'];assert g['grew']=={'own_reader':2} and g['cannot_read_yet']==0 and g['weak_spots']==[] and g['wants_to_learn']==[]
    v=cli(d,'g4-solve','--llm','off','--',BIKE)['voice']
    assert v['before']=='I could not read this problem alone when I met it before; now I can: my own reader reads it now.'
    assert cli(d,'g4-audit')['ok'] and cli(d,'whole-audit')['ok'] and len(_events(d))==2

def test_its_record_of_growth_is_its_own(tmp_path,clean):
    cli=_cli();d=tmp_path/'d';cli(d,'init','--individual-id','GROWTH-MINE');o_=tmp_path/'o';cli(o_,'init','--individual-id','GROWTH-OTHER')
    rec=_write(tmp_path/'r.jsonl',[_line(p,T,R) for p in PARENTS])
    for x in (d,o_):
        cli(x,'g4-solve','--llm','off','--',T2)
        if x==d:older=(d/'g4'/'unread.json').read_bytes()                  # its own, signed: the one problem it had met
        cli(x,'g4-solve','--llm','off','--',SAM)
    o=json.loads((d/'g4'/'unread.json').read_text(encoding='utf-8'));assert o['signed']['payload']['individual_id']==own.individual(d)
    # a thought killed while it notices its growth: the next start finishes it, once
    k=tmp_path/'killed';shutil.copytree(d,k)
    assert cli(k,'think','--',T,replay=rec,crash='g4:after_experience').get('rc')==-9
    assert cli(k,'whole-audit')['ok'] and cli(d,'think','--',T,replay=rec)['answer']=='14'
    assert [(e['kind'],e['theme']) for e in _events(k)]==[(e['kind'],e['theme']) for e in _events(d)] and sum(e['theme']=='g4:grew' for e in _events(k))==1
    assert cli(k,'g4-self')['growth']==cli(d,'g4-self')['growth'] and cli(k,'g4-audit')['ok']
    # it is kept in its soul and its own record: erasing the surface memory does not take it away
    before=cli(d,'g4-self');cli(d,'soul-forget-surface');after=cli(d,'g4-self')
    assert after['growth']==before['growth'] and after['life_story']['grew']==1
    # changed by hand (every problem marked as read, the seal recomputed), taken from another child, or an older version
    # of its own put back (signed by itself, but not the one its whole state recorded; before, the next start took it in
    # and it forgot what it had met since): refused
    for name,change,why in (('edited',lambda x:_mark_all_read(x),'UNREAD_NOT_ITS_OWN'),
                            ('foreign',lambda x:shutil.copy(o_/'g4'/'unread.json',x/'g4'/'unread.json'),'UNREAD_NOT_ITS_OWN'),
                            ('older',lambda x:(x/'g4'/'unread.json').write_bytes(older),'UNREAD_ROLLED_BACK')):
        x=tmp_path/name;shutil.copytree(d,x);change(x)
        au=cli(x,'g4-audit');assert not au['ok'] and au['unread']['reason']==why,name
        me=cli(x,'g4-self');assert me['growth'] is None and me['refused']['unread']==why,name
        # it still thinks; nothing is written to the store, and the whole state does not take it in
        b0=(x/'g4'/'unread.json').read_bytes()
        assert cli(x,'g4-solve','--llm','off','--',MIA)['answer'] is None and (x/'g4'/'unread.json').read_bytes()==b0
        assert cli(x,'whole-audit')['errors']==['COMPONENT_DRIFT:g4_unread'],name

def test_the_whole_state_does_not_take_in_a_store_that_is_not_its_own(tmp_path,clean):
    # before: a store changed by hand was reported until the next thought synced the whole state, which then took it in.
    # Its stores (here: the record of its life, changed to say it had already used alone what it learned) are refused
    # when read, and the whole state keeps what it had recorded; what it learned is a signed commit of its runtime, and
    # nothing goes on until that is put right
    cli=_cli();d=tmp_path/'d';cli(d,'init','--individual-id','GROWTH-WHOLE');rec=_write(tmp_path/'r.jsonl',[_line(p,T,R) for p in PARENTS])
    assert cli(d,'think','--',T,replay=rec)['answer']=='14'
    tid=next(iter(json.loads((d/'g4'/'learned.json').read_text(encoding='utf-8'))['templates']))
    p=d/'g4'/'life.json';kept=p.read_bytes();o=json.loads(kept);assert o['life']['first_alone']==[]
    o['life']['first_alone']=[tid];o['sha256']=own.body_sha(o['life']);p.write_text(json.dumps(o),encoding='utf-8')
    assert cli(d,'whole-audit')['errors']==['COMPONENT_DRIFT:g4_life']
    assert cli(d,'g4-solve','--llm','off','--',BIKE)['answer']=='150'                        # a thought, and the whole state is synced
    assert cli(d,'whole-audit')['errors']==['COMPONENT_DRIFT:g4_life'] and not cli(d,'g4-audit')['ok']
    p.write_bytes(kept)                                                                     # put right: the audits pass again
    assert cli(d,'whole-audit')['ok'] and cli(d,'g4-audit')['ok']
    q=d/'g4'/'learned.json';kept=q.read_bytes();o=json.loads(kept)
    for t in o['templates'].values():t['provenance']['parents']=['claude']
    o['sha256']=own.body_sha(o['templates']);q.write_text(json.dumps(o),encoding='utf-8');w=W.state_path(d).read_bytes()
    r=cli(d,'g4-solve','--llm','off','--',BIKE);assert not r['ok'] and r['error'].endswith('G4_LEARNING_CACHE_MISMATCH')
    assert W.state_path(d).read_bytes()==w
    q.write_bytes(kept);assert cli(d,'whole-audit')['ok'] and cli(d,'g4-audit')['ok']

def _mark_all_read(x):
    p=x/'g4'/'unread.json';o=json.loads(p.read_text(encoding='utf-8'))
    for e in o['entries'].values():e['grown']={'seq':1,'how':'own','value':'0'}
    o['sha256']=own.body_sha(o['entries']);p.write_text(json.dumps(o,ensure_ascii=False,sort_keys=True),encoding='utf-8')
