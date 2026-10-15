"""generation 4: what the child knows of itself, and its inner life. A reading of its own that two parents read another
way is marked (self_checks), one a parent reads the same way is confirmed; the soul keeps the record (law 3), the child
holds back alone where it was read otherwise more often than confirmed, says so in g4-self, and between problems looks
at what it is unsure of (g4-reflect) and, when it may and can, asks its parents again on its own. Recorded replies; the
wording is our own."""
import json,os,subprocess,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_g4 import api,llm,reader

ENV=('TUKUYO_ANTHROPIC_API_KEY','TUKUYO_OPENAI_API_KEY','TUKUYO_GEMINI_API_KEY','TUKUYO_OPENAI_MODEL','TUKUYO_GEMINI_MODEL',
     'TUKUYO_LLM_PARENTS','TUKUYO_LLM_VOICE','TUKUYO_LLM_REPLAY','TUKUYO_LLM_RECORD')
PARENTS=('claude','chatgpt','gemini')
GIVE=['Nora had 30 shells. She gave 8 shells to her cousin. How many shells does she have left?',
      'Owen had 12 stamps. He gave 5 stamps to his sister. How many stamps does he have left?']
MORE=['Rosa has 6 more crayons than Ivan. Ivan has 15 crayons. How many crayons does Rosa have?',
      'Lena has 12 more stamps than Omar. Omar has 20 stamps. How many stamps does Lena have?']
MORE_ALONE='Kai has 7 more shells than Ivy. Ivy has 11 shells. How many shells does Kai have?'
GIVE_ALONE='Kim had 40 beads. She gave 15 beads to Ann. How many beads does she have left?'

@pytest.fixture
def clean(monkeypatch):
    for k in ENV:monkeypatch.delenv(k,raising=False)
    llm._replay_cache.clear();yield monkeypatch;llm._replay_cache.clear()

def _reading(text,flip=False):
    """the child's own reading as a parent would send it; flip: 'x = y + d' read as 'x + d = y' (valid, another answer)"""
    spec=reader.read(text)['spec'];facts=[{'eq':f['eq'],'span':f.get('span',''),'known':f.get('known','')} for f in spec['facts']]
    if flip:
        x,rest=facts[-1]['eq'].split(' = ');y,d=rest.split(' + ');facts[-1]['eq']=f'{x} + {d} = {y}'
    return {'readable':True,'quantities':spec['quantities'],'facts':facts,'ask':spec['ask'],'answer_unit':spec.get('answer_unit',''),'unused':spec.get('unused') or []}

def _line(parent,text,o):
    return {'parent':parent,'hash':llm.request_hash(llm._kind(parent,'read:story:'+llm.PROMPT_VERSION),llm.system_prompt('story'),'Text: '+text),
            'ok':True,'text':json.dumps(o),'model':'fixture-'+parent}

def _write(path,lines):path.write_text('\n'.join(json.dumps(x) for x in lines)+'\n',encoding='utf-8');return path

def test_its_own_reading_is_checked_by_its_parents(tmp_path,clean):
    _write(tmp_path/'r.jsonl',[_line(p,MORE[0],_reading(MORE[0],flip=True)) for p in PARENTS]+[_line(p,GIVE[0],_reading(GIVE[0])) for p in PARENTS])
    clean.setenv('TUKUYO_LLM_REPLAY',str(tmp_path/'r.jsonl'));llm._replay_cache.clear()
    # the parent asked reads it another way: the others are asked too, and two of them agreeing marks its own way of reading
    r=api.solve(MORE[0],data=tmp_path)
    assert r['answer'] is None and r['reason']=='DISAGREE:21,9' and {x.get('parent') for x in r['readings'] if x.get('parent')}==set(PARENTS)
    assert r['self_checks']==[{'skill':'reader_en:compare','held':False,'was':'21','read_as':'9','by':['chatgpt','claude','gemini']}]
    # the parent asked reads it the same way: confirmed, and nobody else is asked
    r=api.solve(GIVE[0],data=tmp_path)
    assert r['answer']=='22' and r['route']=='own+llm' and r['self_checks']==[{'skill':'reader_en:holding','held':True}]
    assert {x.get('parent') for x in r['readings'] if x.get('parent')}=={'claude'}
    # without the individual's data nothing is marked
    assert 'self_checks' not in api.solve(GIVE[0])

def test_the_child_knows_itself_and_looks_at_what_it_is_unsure_of(tmp_path,clean):
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    for k in ENV:env.pop(k,None)
    cmd=[sys.executable,'-B',str(ROOT/'run_tukuyo.py')];anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if anchor:cmd+=['--runtime-trust-file',anchor]
    d=str(tmp_path/'d')
    def run(*a,replay=None):
        e=dict(env)
        if replay:e['TUKUYO_LLM_REPLAY']=str(replay)
        p=subprocess.run(cmd+['--data',d,*a],cwd=ROOT,env=e,capture_output=True,text=True,timeout=240);return json.loads(p.stdout)
    assert run('init')['ok']
    before=_write(tmp_path/'before.jsonl',[_line(p,t,_reading(t)) for t in GIVE for p in PARENTS]+[_line(p,t,_reading(t,flip=True)) for t in MORE for p in PARENTS])
    for t in GIVE:assert run('g4-solve','--',t,replay=before)['route']=='own+llm'
    for t in MORE:assert run('g4-solve','--',t,replay=before)['answer'] is None
    me=run('g4-self')['self_knowledge']
    assert me['reader_en:holding']['confirmed']==2 and not me['reader_en:holding']['doubted']
    assert me['reader_en:compare']['contradicted']==2 and me['reader_en:compare']['doubted']
    # alone, it holds back where its parents read it otherwise, and still answers what they confirmed
    r=run('g4-solve','--llm','off','--',MORE_ALONE);assert r['answer'] is None and r['reason']=='SELF_DOUBT:reader_en:compare'
    assert run('g4-solve','--llm','off','--',GIVE_ALONE)['answer']=='25'
    # between problems: what it is unsure of, and what it would ask; looking changes nothing, and with no parent nobody is asked
    look=run('g4-reflect');assert [x['text'] for x in look['intentions']]==MORE and all(x['skill']=='reader_en:compare' for x in look['intentions'])
    assert run('g4-reflect')==look
    none=run('g4-reflect','--act');assert none['acted']==[] and none['note'].startswith('NO_PARENT_TO_ASK')
    # its parents, asked again on its own, read the comparisons as the child does: its way of reading holds up again
    later=_write(tmp_path/'later.jsonl',[_line(p,t,_reading(t)) for t in MORE for p in PARENTS])
    acted=run('g4-reflect','--act',replay=later);assert [x['answer'] for x in acted['acted']]==['21','32']
    assert run('g4-reflect')['intentions']==[]
    me=run('g4-self');assert me['self_knowledge']['reader_en:compare']['confirmed']==2 and not me['self_knowledge']['reader_en:compare']['doubted']
    assert any('questions of its own' in x for x in me['life_story']['told'])
    assert run('g4-solve','--llm','off','--',MORE_ALONE)['answer']=='18'
    for c in ('whole-audit','soul-identity-audit','g4-audit'):assert run(c)['ok'],c

def test_think_lives_what_g4_solve_lives(tmp_path,clean):
    # before: think, the main way in, passed neither its own readings that a parent checked nor a reading taught again
    # on to its life, so a child that only thought with think never came to know itself (found by a trial experiment)
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    for k in ENV:env.pop(k,None)
    cmd=[sys.executable,'-B',str(ROOT/'run_tukuyo.py')];anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if anchor:cmd+=['--runtime-trust-file',anchor]
    rec=_write(tmp_path/'r.jsonl',[_line(p,GIVE[0],_reading(GIVE[0])) for p in PARENTS]+[_line(p,MORE[0],_reading(MORE[0],flip=True)) for p in PARENTS])
    def run(d,*a):
        p=subprocess.run(cmd+['--data',str(d),*a],cwd=ROOT,env={**env,'TUKUYO_LLM_REPLAY':str(rec)},capture_output=True,text=True,timeout=240)
        return json.loads(p.stdout)
    lives={}
    for way in ('think','g4-solve'):
        d=tmp_path/way;assert run(d,'init')['ok']
        lives[way]=[[(x['kind'],x['relation']) for x in run(d,way,'--',t)['life']] for t in (GIVE[0],MORE[0])]
        lives[way+':self']=run(d,'g4-self')['self_knowledge']
    assert lives['think'][0]==lives['g4-solve'][0]==[('learning',''),('parent_help','parent:claude'),('self_confirmed','self:reader_en:holding')]
    assert lives['g4-solve'][1]==[('honesty',''),('self_error','self:reader_en:compare')]
    # think also reads with its older core (here its formula reading, 21): its parents read that otherwise too
    assert lives['think'][1]==[('honesty',''),('self_error','self:v1022'),('self_error','self:reader_en:compare')]
    for k in ('reader_en:holding','reader_en:compare'):assert lives['think:self'][k]==lives['g4-solve:self'][k]
    assert lives['think:self']['reader_en:compare']['doubted'] and lives['think:self']['v1022']['doubted']
