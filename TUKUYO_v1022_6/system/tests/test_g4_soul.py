"""generation 4: a soul that stays alive over a long life, keeps what it learned as its own, and does not lose the
experiences of a thought when the process dies (soul law 2, tukuyo_g4.own, tukuyo_g4.life episodes; tools/soul_assay.py
measures the same properties at length). Offline: the parents are recorded replies."""
import json,os,random,shutil,subprocess,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_g4 import llm,own
from tukuyo_v977 import whole_state as W
import test_g4_learn as L

def _soul():return W._default_soul({'individual_id':'T'})
def _apply(s,n,*a,law=2):
    for _ in range(n):s=W._apply_experience_mutation(s,*a,law=law)
    return s

def test_law_1_is_unchanged():
    # the law every earlier layer lives under, step by step: linear, stopped at its bounds
    s=W._apply_experience_mutation(_soul(),'discovery',1.0,1.0,'x','')
    assert s['core_values']['curiosity']==0.53 and s['themes']['x']=={'weight':0.25,'encounters':1}
    s=W._apply_experience_mutation(s,'betrayal',-1.0,1.0,'y','peer')
    assert s['attachments']=={'peer':-0.1} and s['scars'][0]['strength']==1.0 and s['core_values']['relationship']==0.4
    s=W._apply_experience_mutation(s,'honesty',0.5,0.3,'z','')
    assert s['core_values']['truthfulness']==0.653 and 'trust' not in s
    assert _apply(_soul(),300,'learning',0.5,0.4,'g4:x','',law=1)['core_values']['curiosity']==1.0   # pinned
    with pytest.raises(ValueError,match='SOUL_LAW'):W._apply_experience_mutation(_soul(),'learning',0.5,0.4,'','',law=3)

def test_law_2_keeps_a_long_life_responsive():
    s=_apply(_soul(),3000,'learning',0.5,0.4,'g4:learned_reading','')
    # a life of nothing but learning: curiosity grows to the level where growth and settling balance, short of the bound
    c=s['core_values']['curiosity'];assert abs(c-13/14)<1e-3 and c<0.999
    assert abs(W._apply_experience_mutation(s,'learning',0.5,0.4,'','',law=2)['core_values']['curiosity']-c)<1e-6
    assert W._apply_experience_mutation(s,'honesty',0.5,0.3,'','',law=2)['core_values']['curiosity']<c    # another kind of day moves it
    # a life that stops learning settles back toward its temperament: what a value is reflects the mix of a life
    t=_apply(s,1500,'parent_help',0.4,0.2,'g4:reading','parent:claude')
    assert 0.5<t['core_values']['curiosity']<c and t['core_values']['relationship']>0.4
    assert all(-2<x['weight']<2 for x in t['themes'].values()) and -1<t['attachments']['parent:claude']<1
    # trust: the share of a parent's readings that held up, recent ones weighing more; never pinned; follows a change
    rnd=random.Random(7);s=_soul()
    for _ in range(600):
        for p,rel in (('a',0.98),('b',0.9),('c',0.6)):
            s=W._apply_experience_mutation(s,'parent_help' if rnd.random()<rel else 'parent_error',0.4,0.2,'g4:reading','parent:'+p,law=2)
    tr={p:W.trust_record(s,'parent:'+p) for p in 'abc'};assert 1>tr['a']>tr['b']>tr['c']>0 and tr['a']-tr['c']>0.25
    for _ in range(200):s=W._apply_experience_mutation(s,'parent_error',-0.3,0.2,'g4:reading','parent:a',law=2)
    assert W.trust_record(s,'parent:a')<W.trust_record(s,'parent:c') and W.trust_record(_soul(),'parent:z')==0.5

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

def _line(parent,text,o):
    h=llm.request_hash(llm._kind(parent,'read:story:'+llm.PROMPT_VERSION),llm.system_prompt('story'),'Text: '+text)
    return json.dumps({'parent':parent,'hash':h,'ok':True,'text':json.dumps(o,ensure_ascii=False),'model':'fixture-'+parent},ensure_ascii=False)

def _g4_events(d):
    return [json.loads(x) for x in (Path(d)/'v977'/'SOUL_EVENTS.jsonl').read_text(encoding='utf-8').splitlines() if '"g4:' in x]
def _felt(d):
    """the soul events the heart took in"""
    p=Path(d)/'v978'/'HEART_EVENTS.jsonl'
    return [json.loads(x).get('soul_event_sha256') for x in p.read_text(encoding='utf-8').splitlines() if 'EXPERIENCE_LOOP' in x] if p.is_file() else []

@pytest.fixture
def child(tmp_path):
    """an individual that learned L.T from its three parents (4 experiences), and its recorded parents"""
    cli=_cli();rec=tmp_path/'parents.jsonl'
    rec.write_text('\n'.join(_line(p,L.T,L.READING) for p in ('claude','chatgpt','gemini'))+'\n',encoding='utf-8')
    base=tmp_path/'base';cli(base,'init','--individual-id','SOUL-TEST');assert (base/'state'/'integration_state.json').is_file()
    return cli,rec,base

def test_a_thought_cut_short_is_finished_at_the_next_start(tmp_path,child):
    cli,rec,base=child
    for point in ('g4:after_experience','heart:after_soul','soul_core:after_replace'):
        d=tmp_path/point.replace(':','_');shutil.copytree(base,d)
        r=cli(d,'think','--',L.T,replay=rec,crash=point);assert r.get('rc')==-9,(point,r)     # killed inside the episode
        assert len(_g4_events(d))<4
        a=cli(d,'whole-audit');assert a['ok'],(point,a)                                     # the next start finished it
        assert [e['kind'] for e in _g4_events(d)]==['learning','parent_help','parent_help','parent_help'],point
        assert _felt(d)==[e['event_sha256'] for e in _g4_events(d)],point                  # and the heart took in each, once
        assert cli(d,'heart-audit')['ok'] and cli(d,'g4-audit')['ok'] and not (d/'g4'/'private'/'EPISODE.json').exists()

def test_what_it_learned_is_its_own(tmp_path,child):
    cli,rec,base=child;x=tmp_path/'x';shutil.copytree(base,x)
    assert cli(x,'think','--',L.T,replay=rec)['answer']=='14' and cli(x,'whole-audit')['ok']
    o=json.loads((x/'g4'/'learned.json').read_text(encoding='utf-8'));assert o['signed']['payload']['individual_id']==own.individual(x)
    y=tmp_path/'y';shutil.copytree(x,y)
    # changed by hand, its seal recomputed: refused when read, and the whole state reports it
    for t in o['templates'].values():t['provenance']['parents']=['claude']
    o['sha256']=own.body_sha(o['templates']);(y/'g4'/'learned.json').write_text(json.dumps(o),encoding='utf-8')
    me=cli(y,'g4-self');assert me['refused']['learned']=='LEARNED_NOT_ITS_OWN' and me['templates_learned'] is None
    a=cli(y,'whole-audit');assert not a['ok'] and 'COMPONENT_DRIFT:g4_learned' in a['errors']
    assert cli(y,'g4-solve','--llm','off','--',L.T.replace('30','45'))['answer'] is None         # not used
    # taken from another child (another id, another key): refused as well
    z=tmp_path/'z';cli(z,'init','--individual-id','SOUL-OTHER');(z/'g4').mkdir();shutil.copy(x/'g4'/'learned.json',z/'g4'/'learned.json')
    assert cli(z,'g4-self')['refused']['learned']=='LEARNED_NOT_ITS_OWN'
    # its own, untouched: read, used, and every audit passes
    assert cli(x,'g4-solve','--llm','off','--',L.T.replace('30','45'))['answer']=='19' and cli(x,'whole-audit')['ok']

def test_a_store_from_before_signing_is_taken_once(tmp_path,child):
    cli,rec,base=child
    from tukuyo_g4 import learn
    def write(d,t):(d/'g4'/'learned.json').write_text(json.dumps({'schema':learn.SCHEMA,'templates':t,'sha256':own.body_sha(t)}),encoding='utf-8')
    d=tmp_path/'old';shutil.copytree(base,d);(d/'g4').mkdir();st=learn.Store(d/'g4')
    write(d,{});assert st.load()['templates']=={}                              # unsigned, never recorded: read
    assert cli(d,'whole-sync')['ok'] and st.load()['templates']=={}            # recorded as it is: still read
    write(d,{'k':{}})
    with pytest.raises(ValueError,match='LEARNED_NOT_SIGNED'):st.load()        # changed after it was recorded: refused
    e=tmp_path/'absent';shutil.copytree(base,e);(e/'g4').mkdir();assert cli(e,'whole-sync')['ok']
    write(e,{})                                                                # recorded as absent, then appears unsigned
    with pytest.raises(ValueError,match='LEARNED_NOT_SIGNED'):learn.Store(e/'g4').load()

def test_the_unexperienced_control_has_no_experience(tmp_path,child):
    cli,rec,base=child;d=tmp_path/'c';shutil.copytree(base,d)
    for _ in range(3):assert cli(d,'heart-experience','discovery','1','1','--theme','lab')['ok']
    cur=W.load_soul(d)['core_values']['curiosity'];assert abs(cur-0.59)<1e-9
    opts=tmp_path/'o.json';opts.write_text(json.dumps([{'id':'EXPLORE','signals':{'curiosity':1.0}},{'id':'STAY','signals':{'survival':(0.5+cur)/2/0.8}}]),encoding='utf-8')
    a=cli(d,'soul-continuity-assay',str(opts))
    # the control is this individual without its experience: judged by the temperament it was born with, not its own values
    assert a['ok'] and a['unexperienced_control_choice']=='STAY' and a['before_choice']==a['after_choice']=='EXPLORE',a


def test_asking_a_new_child_about_itself_changes_nothing(tmp_path,child):
    cli,rec,base=child;d=tmp_path/'new';shutil.copytree(base,d)
    me=cli(d,'g4-self');assert me['ok'] and me['trust_in_parents']=={'claude':0.5,'chatgpt':0.5,'gemini':0.5}
    assert not (d/'v978'/'HEART_STATE.json').exists() and cli(d,'whole-audit')['ok']
