"""generation 4 lives through its soul and heart: what it learns from its parents becomes experience (v978 -> v977 ->
v993), its trust in each parent follows how their readings fared, the most trusted parent is its voice, answers its
parents agree on are remembered, and every audit of the soul, the heart and the learned stores still passes.
Offline: the parents are recorded replies."""
import copy,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_g4 import llm,life
import test_g4_learn as L

# the same wording as L.T with other number words: the template learned from L.T reads it, so the child reads it itself
T2='When four times a number is decreased by eight, the result is 28. What is the number?'
R2={'readable':True,'quantities':[{'name':n,'unit':'1','integer':False,'signed':False,'about':n} for n in ('eight','factor','result','number')],
    'facts':[{'eq':'eight = 8','span':'decreased by eight','known':''},{'eq':'factor = 4','span':'four times','known':''},
             {'eq':'result = 28','span':'the result is 28','known':''},
             {'eq':'factor * number - eight = result','span':'When four times a number is decreased by eight, the result is 28','known':''}],
    'ask':'number','answer_unit':'','unused':[]}
# other wordings that neither TUKUYO's own readers nor that template read: only the parents can
T4='A number is multiplied by four and then eight is taken away. The result is 28. What is the number?'
R4={'readable':True,'quantities':[{'name':n,'unit':'1','integer':False,'signed':False,'about':n} for n in ('four','eight','result','number')],
    'facts':[{'eq':'four = 4','span':'multiplied by four','known':''},{'eq':'eight = 8','span':'eight is taken away','known':''},
             {'eq':'result = 28','span':'The result is 28','known':''},
             {'eq':'four * number - eight = result','span':'A number is multiplied by four and then eight is taken away','known':''}],
    'ask':'number','answer_unit':'','unused':[]}
T5='Take a number, triple it, and subtract six: you get 30. What is the number?'
R5={'readable':True,'quantities':[{'name':n,'unit':'1','integer':False,'signed':False,'about':n} for n in ('three','six','result','number')],
    'facts':[{'eq':'three = 3','span':'triple it','known':''},{'eq':'six = 6','span':'subtract six','known':''},
             {'eq':'result = 30','span':'you get 30','known':''},
             {'eq':'three * number - six = result','span':'Take a number, triple it, and subtract six: you get 30','known':''}],
    'ask':'number','answer_unit':'','unused':[]}

def _line(parent,kind,system,user,text):
    return json.dumps({'parent':parent,'hash':llm.request_hash(llm._kind(parent,kind),system,user),'ok':True,'text':text,'model':'fixture-'+parent},ensure_ascii=False)
def _read(parent,text,o):return _line(parent,'read:story:'+llm.PROMPT_VERSION,llm.system_prompt('story'),'Text: '+text,json.dumps(o,ensure_ascii=False))

def test_the_child_learns_from_its_parents_with_its_soul(tmp_path):
    env={k:v for k,v in os.environ.items() if not k.startswith(('TUKUYO_ANTHROPIC','TUKUYO_OPENAI','TUKUYO_GEMINI','TUKUYO_LLM'))}
    env['PYTHONDONTWRITEBYTECODE']='1'
    cmd=[sys.executable,'-B',str(ROOT/'run_tukuyo.py')];anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if anchor:cmd+=['--runtime-trust-file',anchor]
    D=str(tmp_path/'child');rec=tmp_path/'parents.jsonl'
    def cli(*a,replay=True):
        e=dict(env,**({'TUKUYO_LLM_REPLAY':str(rec)} if replay else {}))
        p=subprocess.run(cmd+['--data',D,*a],cwd=ROOT,env=e,capture_output=True,text=True,timeout=300);return json.loads(p.stdout)
    bad4=copy.deepcopy(R4);bad4['facts'][1]['eq']='eight = 9'                    # a number that is not in the text
    other5=copy.deepcopy(R5);other5['facts'][3]['eq']='three * number + six = result'   # a valid reading with another answer
    rec.write_text('\n'.join([_read(p,L.T,L.READING) for p in ('claude','chatgpt','gemini')]+[_read('claude',T2,R2)]+
                             [_read('claude',T4,R4),_read('chatgpt',T4,bad4),_read('gemini',T4,R4)]+
                             [_read('claude',T5,R5),_read('gemini',T5,other5)])+'\n',encoding='utf-8')
    assert cli('init')['ok']
    s0=cli('g4-self');assert s0['trust_in_parents']=={'claude':0.5,'chatgpt':0.5,'gemini':0.5} and s0['templates_learned']==0
    cur0=s0['soul']['core_values']['curiosity'];tru0=s0['soul']['core_values']['truthfulness']
    # three parents agree: answered, learned, and each parent is trusted a little more
    r=cli('think','--',L.T);assert r['answer']=='14' and {x['kind'] for x in r['life']}=={'learning','parent_help'}
    s1=cli('g4-self');assert all(v>0.5 for v in s1['trust_in_parents'].values()) and s1['soul']['core_values']['curiosity']>cur0
    assert s1['templates_learned']==1 and s1['templates_by_parent']=={'chatgpt':1,'claude':1,'gemini':1}
    # the same wording with other number words: read by the child itself, and the parent it trusts most confirms it
    r=cli('think','--',T2);assert r['answer']=='9' and r['gen4']['route']=='learned+llm'
    # ChatGPT's reading fails the checker; Claude and Gemini agree: ChatGPT is trusted less than the others
    r=cli('think','--',T4);assert r['answer']=='9' and r['gen4']['route']=='claude+gemini'
    assert {'kind':'parent_error','theme':'g4:reading','relation':'parent:chatgpt'} in r['life']
    s2=cli('g4-self');t=s2['trust_in_parents'];assert t['chatgpt']<t['gemini']<t['claude']   # Claude also confirmed T2
    # two parents give two different valid answers: the child withholds instead of guessing, and grows more truthful
    r=cli('think','--',T5);assert r['answer'] is None and r['reason'].startswith('DISAGREE') and r['life'][0]['kind']=='honesty'
    assert cli('g4-self')['soul']['core_values']['truthfulness']>tru0
    # with the template it learned, it solves alone; the first time is a discovery, the second is routine
    r=cli('g4-solve','--llm','off','--',L.T.replace('30','45'),replay=False);assert (r['answer'],r['route'])==('19','learned')
    assert [x['kind'] for x in r['life']]==['discovery']
    assert cli('g4-solve','--llm','off','--',L.T.replace('30','60'),replay=False)['life']==[]
    # its voice is the parent it trusts most; what its parents agree on is remembered and given again without them
    q='What is the capital of France?';persona=life.persona(D);sysp=llm.ANSWER_SYSTEM+'\n\n'+persona
    with open(rec,'a',encoding='utf-8') as f:
        for p,a in (('claude','Paris.'),('chatgpt','Paris'),('gemini','Paris')):f.write(_line(p,'answer:2',sysp,q,a)+'\n')
    r=cli('g4-ask','--voices','all','--',q)
    assert (r['source'],r['agree'],r['remembered'])==('claude',True,True) and {x['kind'] for x in r['life']}=={'learning','parent_help'}
    r=cli('g4-ask','--llm','off','--',q,replay=False)
    assert (r['answer'],r['route'],r['source'],r['verified'])==('Paris.','remembered','parents_agreed',False) and r['parents']==['chatgpt','claude','gemini']
    s=cli('g4-self');assert s['remembered_answers']==1 and s['solved_alone_first_times']==1 and s['claim_boundary']['consciousness_established'] is False
    assert len(cli('g4-remembered')['entries'])==1
    # without the soul: nothing is passed on
    assert 'life' not in cli('think','--no-soul','--',L.T)
    # every audit of the soul, the heart and the stores still passes
    for c in ('whole-audit','heart-audit','learning-audit','g4-audit'):assert cli(c,replay=False)['ok'],c
    assert cli('soul-consolidate',replay=False)['ok'] and cli('soul-deep-audit',replay=False)['ok']
    # what it lived through is in its soul journal: forgetting the surface memory does not take it, nor its trust
    me=cli('g4-self',replay=False);story=me['life_story']
    assert story['experiences']['parent_error']==1 and story['from_parents']['chatgpt']=={'held':2,'failed':1}
    assert cli('soul-forget-surface',replay=False)['ok'];after=cli('g4-self',replay=False)
    assert after['life_story']==story and after['recent_g4_experiences']==[] and after['trust_in_parents']==me['trust_in_parents']
    assert cli('whole-audit',replay=False)['ok']
