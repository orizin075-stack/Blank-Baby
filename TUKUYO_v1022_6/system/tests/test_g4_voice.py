"""generation 4: the child's own voice (voice.py). It says in its own words how it read a problem and what it
calculated, how sure it is and why, and why it holds back; everything it says comes from what it did and from its own
record. Recorded replies for the parents; the wording is our own."""
import json,os,re,subprocess,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_g4 import api,llm,reader,voice,numbers as N
from tukuyo_g4.life import voice_check

ENV=('TUKUYO_ANTHROPIC_API_KEY','TUKUYO_OPENAI_API_KEY','TUKUYO_GEMINI_API_KEY','TUKUYO_OPENAI_MODEL','TUKUYO_GEMINI_MODEL',
     'TUKUYO_LLM_PARENTS','TUKUYO_LLM_VOICE','TUKUYO_LLM_REPLAY','TUKUYO_LLM_RECORD')
PARENTS=('claude','chatgpt','gemini')

def _numbers(s):return set(re.findall(r'(?<![\w/.])\d+(?:/\d+)?(?:\.\d+)?(?![\w/])',s))

@pytest.fixture
def clean(monkeypatch):
    for k in ENV:monkeypatch.delenv(k,raising=False)
    llm._replay_cache.clear();yield monkeypatch;llm._replay_cache.clear()

def test_it_says_how_it_read_and_calculated(clean):
    t='Nick has 90 marbles. 35 are blue and the rest are green. How many green marbles does Nick have?'
    r=api.solve(t,llm='off');v=voice.explain(t,r)
    assert r['answer']=='55' and v['answer']=='55 marbles' and v['lang']=='en'
    # the words it read each number from, then what it worked out, with the numbers put in
    assert v['read'][0].startswith('"Nick has 90 marbles."') and '90 - 35 = 55' in v['read'][-1]
    assert all(q in t for line in v['read'] for q in re.findall(r'"([^"]+)"',line))
    # every number it says is a number of the problem or a value of its reading; it speaks as itself
    ok={x for n in N.find(t) for x in (n.raw,str(n.value))}|{str(x) for x in r['readings'][0]['values'].values()}
    assert _numbers(v['said'])<=ok and voice_check(v['said'])['speaks_as_tukuyo']
    # without its individual it does not know its record, and says so
    assert v['sure']=='fairly sure' and 'did not look at my own record' in v['why']
    assert voice.explain(t,api.solve(t,llm='off'))==v                    # the same thought in the same words

def test_it_says_what_it_set_aside_and_known_constants(clean):
    t='Lena spent 240 minutes on her painting. How many hours did she spend on her painting?'
    v=voice.explain(t,api.solve(t,llm='off'))
    assert v['answer']=='4 hours' and any(x.startswith('I know: 60 minutes in an hour') for x in v['read'])
    t='There were 44 laptops in the shop, and Mike divided them equally into 5 rows. How many are left?'
    v=voice.explain(t,api.solve(t,llm='off'))
    assert v['answer']=='4 laptops' and any('⌊44 ÷ 5⌋ = 8' in x for x in v['read'])

def test_it_says_why_it_holds_back(clean):
    t='Mia had some shells. She found 4 more shells on the beach. How many shells does she have now?'
    v=voice.explain(t,api.solve(t,llm='off'))
    assert v['answer'] is None and v['sure']=='not sure' and v['held_back'].startswith('I do not answer:') and 'I did not ask my parents' in v['held_back']
    r={'answer':None,'reason':'DISAGREE:21,9','readings':[{'route':'own','ok':True,'value':'21'},{'route':'llm_story','ok':True,'value':'9','parent':'claude'},
                                                          {'route':'llm_chatgpt_story','ok':True,'value':'9','parent':'chatgpt'}]}
    v=voice.explain('Rosa has 6 more crayons than Ivan. Ivan has 15 crayons. How many crayons does Rosa have?',r)
    assert '21 (my own reading) and 9 (Claude and ChatGPT)' in v['held_back'] and 'cannot tell which is right' in v['held_back']
    r={'answer':None,'reason':'SINGLE_LLM_READING','withheld':'7','readings':[{'route':'llm_gemini_story','ok':True,'value':'7','parent':'gemini'}]}
    assert 'Only Gemini could read it (7)' in voice.explain('A problem with 3 numbers, 4 and 5?',r)['held_back']

def test_it_says_whose_reading_it_tells(clean):
    t='Nick has 90 marbles. 35 are blue and the rest are green. How many green marbles does Nick have?'
    sp=api.solve(t,llm='off')['readings'][0]
    # it could not read the problem itself and two parents agreed: it tells their reading as theirs
    r={'answer':'55','value':'55','unit':'marble','route':'claude+gemini','readings':[{'route':'own','ok':False,'reason':'EN:NO_SCHEMA'},
       {**sp,'route':'llm_story','parent':'claude'},{**sp,'route':'llm_gemini_story','parent':'gemini'}]}
    v=voice.explain(t,r)
    assert v['whose']=='its parents' and v['said'].startswith('How my parents read it:') and v['sure']=='fairly sure'
    assert v['why'].startswith('I could not read it myself; Claude and Gemini read it the same way') and 'solved their reading again' in v['why']
    # its own reading with a parent in agreement is its own
    r={**r,'route':'own+llm','readings':[sp,{**sp,'route':'llm_story','parent':'claude'}]}
    v=voice.explain(t,r);assert v['whose']=='its own' and v['said'].startswith('How I read it:') and v['sure']=='sure'

def test_its_voice_never_stops_it_from_answering(clean):
    for r in ({'answer':'1','readings':'not a list'},{'answer':'1','readings':[{'ok':True,'value':'1','spec':{'facts':[]},'steps':[{'fact':9,'solve':'x','value':'1'}]}]},
              {'answer':None,'reason':None,'readings':None},{'answer':'2'}):
        v=voice.explain('How many?',r);assert isinstance(v,dict) and ('said' in v)

def test_japanese_problems_are_explained_in_japanese(clean):
    r={'answer':'5','value':'5','route':'v1022','readings':[{'route':'v1022','ok':True,'value':'5','proof_kind':'combine'}]}
    v=voice.explain('りんごが3個あります。2個もらいました。全部で何個ですか？',r)
    assert v['lang']=='ja' and v['answer']=='5' and v['sure']=='fairly sure' and '前の世代の考え方' in v['said'] and 'combine' in v['said']

def _line(parent,text,o):
    return {'parent':parent,'hash':llm.request_hash(llm._kind(parent,'read:story:'+llm.PROMPT_VERSION),llm.system_prompt('story'),'Text: '+text),
            'ok':True,'text':json.dumps(o),'model':'fixture-'+parent}
def _reading(text,flip=False):
    spec=reader.read(text)['spec'];facts=[{'eq':f['eq'],'span':f.get('span',''),'known':f.get('known','')} for f in spec['facts']]
    if flip:
        x,rest=facts[-1]['eq'].split(' = ');y,d=rest.split(' + ');facts[-1]['eq']=f'{x} + {d} = {y}'
    return {'readable':True,'quantities':spec['quantities'],'facts':facts,'ask':spec['ask'],'answer_unit':spec.get('answer_unit',''),'unused':spec.get('unused') or []}

GIVE=['Nora had 30 shells. She gave 8 shells to her cousin. How many shells does she have left?',
      'Owen had 12 stamps. He gave 5 stamps to his sister. How many stamps does he have left?']
MORE=['Rosa has 6 more crayons than Ivan. Ivan has 15 crayons. How many crayons does Rosa have?',
      'Lena has 12 more stamps than Omar. Omar has 20 stamps. How many stamps does Lena have?']
def test_how_sure_it_is_follows_its_own_life(tmp_path,clean):
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    for k in ENV:env.pop(k,None)
    cmd=[sys.executable,'-B',str(ROOT/'run_tukuyo.py')];anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if anchor:cmd+=['--runtime-trust-file',anchor]
    def run(d,*a,replay=None):
        e=dict(env)
        if replay:e['TUKUYO_LLM_REPLAY']=str(replay)
        p=subprocess.run(cmd+['--data',str(d),*a],cwd=ROOT,env=e,capture_output=True,text=True,timeout=240);return json.loads(p.stdout)
    d,fresh=tmp_path/'d',tmp_path/'fresh'
    assert run(d,'init')['ok'] and run(fresh,'init')['ok']
    rec=tmp_path/'r.jsonl'
    rec.write_text('\n'.join(json.dumps(x) for x in [_line(p,t,_reading(t)) for t in GIVE for p in PARENTS]+[_line(p,t,_reading(t,flip=True)) for t in MORE for p in PARENTS])+'\n',encoding='utf-8')
    for t in GIVE:
        v=run(d,'g4-solve','--',t,replay=rec)['voice'];assert v['sure']=='sure' and 'Claude read it the same way' in v['why']
    for t in MORE:assert run(d,'g4-solve','--',t,replay=rec)['answer'] is None
    alone='Kim had 40 beads. She gave 15 beads to Ann. How many beads does she have left?'
    lived,first=run(d,'g4-solve','--llm','off','--',alone)['voice'],run(fresh,'g4-solve','--llm','off','--',alone)['voice']
    # the same reading; a child whose parents confirmed it is sure, a child without that life is fairly sure
    assert lived['read']==first['read'] and lived['answer']==first['answer']=='25 beads'
    assert lived['sure']=='sure' and 'confirmed this way of reading 2 times and never read it otherwise' in lived['why']
    assert first['sure']=='fairly sure' and 'have not checked this way of reading yet' in first['why']
    held=run(d,'g4-solve','--llm','off','--','Kai has 7 more shells than Ivy. Ivy has 11 shells. How many shells does Kai have?')
    assert held['answer'] is None and held['voice']['held_back'].startswith('My reading says 18, but my parents')
    assert 'read it otherwise 2 times and confirmed it 0 times' in held['voice']['held_back']
    # think says it in the same voice
    th=run(d,'think','--llm','off','--',alone);assert th['answer']=='25' and th['gen4']['voice']==lived
