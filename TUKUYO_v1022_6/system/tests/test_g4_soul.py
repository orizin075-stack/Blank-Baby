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
    with pytest.raises(ValueError,match='SOUL_LAW'):W._apply_experience_mutation(_soul(),'learning',0.5,0.4,'','',law=4)

def test_law_3_is_law_2_and_what_it_knows_of_itself():
    # law 3 lives every experience as law 2 does ...
    a=W._apply_experience_mutation(_soul(),'parent_help',0.4,0.2,'g4:reading','parent:claude',law=2)
    b=W._apply_experience_mutation(_soul(),'parent_help',0.4,0.2,'g4:reading','parent:claude',law=3)
    assert a==b
    # ... and keeps, for each of its own ways of reading, how it held up when its parents checked it (recent ones weighing
    # more); that is not a bond with someone: neither attachments nor relationship move
    s=_soul()
    for k in ('self_error','self_error'):s=W._apply_experience_mutation(s,k,-0.3,0.3,'g4:self_knowledge','self:reader_en:compare',law=3)
    assert s['self_trust']['reader_en:compare']=={'held':0.0,'failed':1.99} and W.self_trust_record(s,'reader_en:compare')<0.5
    assert s['attachments']=={} and s['core_values']['relationship']==W.TEMPERAMENT['relationship'] and 'trust' not in s
    for _ in range(3):s=W._apply_experience_mutation(s,'self_confirmed',0.2,0.15,'g4:self_knowledge','self:reader_en:compare',law=3)
    r=s['self_trust']['reader_en:compare'];assert r['held']>r['failed'] and W.self_trust_record(s,'reader_en:compare')>0.5
    assert W.self_trust_record(s,'reader_en:holding')==0.5                     # never checked

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
    # in a live individual what it learned is a signed commit of its runtime (tukuyo_g4.runtime_store, taken from
    # v1022.7.7): learned.json is a cache of the last commit, and its whole state records the head
    cli,rec,base=child;x=tmp_path/'x';shutil.copytree(base,x)
    assert cli(x,'think','--',L.T,replay=rec)['answer']=='14' and cli(x,'whole-audit')['ok']
    head=json.loads(sorted((x/'g4'/'commits').glob('*.json'))[-1].read_text(encoding='utf-8'))
    assert head['payload']['namespace']=='g4' and W._verify(head,W._key_paths(x)[1].read_text().strip())
    o=json.loads((x/'g4'/'learned.json').read_text(encoding='utf-8'));assert o==head['payload']['state']['learned']
    # changed by hand, its seal recomputed: it does not go on with it (every command refuses until it is put right), and
    # its whole state is not rewritten
    y=tmp_path/'y';shutil.copytree(x,y)
    for t in o['templates'].values():t['provenance']['parents']=['claude']
    o['sha256']=own.body_sha(o['templates']);(y/'g4'/'learned.json').write_text(json.dumps(o),encoding='utf-8')
    w=W.state_path(y).read_bytes()
    for a in (('g4-solve','--llm','off','--',L.T.replace('30','45')),('g4-self',),('whole-audit',)):
        r=cli(y,*a);assert not r['ok'] and 'G4_LEARNING_CACHE_MISMATCH' in r['error'],(a,r)
    assert W.state_path(y).read_bytes()==w
    # taken from another child (another id, another key), with its commits or the cache alone: refused as well
    for name,files in (('z1',('learned.json','STATE.json','commits')),('z2',('learned.json',))):
        z=tmp_path/name;cli(z,'init','--individual-id','SOUL-OTHER');(z/'g4').mkdir()
        for f in files:(shutil.copytree if (x/'g4'/f).is_dir() else shutil.copy)(x/'g4'/f,z/'g4'/f)
        r=cli(z,'g4-self');assert not r['ok'] and r['error'].endswith(('V1022_COMMIT_SIGNATURE','G4_LEARNING_UNSIGNED_LEGACY')),(name,r)
    # its own, untouched: read, used, and every audit passes
    assert cli(x,'g4-solve','--llm','off','--',L.T.replace('30','45'))['answer']=='19' and cli(x,'whole-audit')['ok']

def test_a_store_from_an_earlier_version(tmp_path,child):
    # signed with its own key by generation 4 before the runtime commits: read, used, and taken over by the next commit.
    # Unsigned (written before stores were signed) or signed by another child: not taken. Before, an unsigned store its
    # whole state had never recorded was read and then signed, so one put into an individual that had not used
    # generation 4 yet was taken in; v1022.6.5 already refused it, and this keeps that
    cli,rec,base=child
    from tukuyo_g4 import learn,runtime_store
    x=tmp_path/'x';shutil.copytree(base,x);assert cli(x,'think','--',L.T,replay=rec)['answer']=='14'
    tpl=runtime_store.load(x)['templates']
    def legacy(d,signer):
        """learned.json as generation 4 wrote it before the runtime commits; signer: whose own key signed it (None: unsigned)"""
        sha=own.body_sha(tpl);o={'schema':learn.SCHEMA,'templates':tpl,'sha256':sha}
        if signer is not None:o['signed']=own.sign(signer,'learned',sha)
        (d/'g4').mkdir(exist_ok=True);(d/'g4'/'learned.json').write_text(json.dumps(o),encoding='utf-8')
    old=tmp_path/'old';shutil.copytree(base,old);legacy(old,old)
    assert runtime_store.load(old)['templates']==tpl
    assert cli(old,'g4-solve','--llm','off','--',L.T.replace('30','45'))['answer']=='19' and cli(old,'whole-audit')['ok']
    runtime_store.save(old,runtime_store.load(old))                          # the next commit takes it over
    assert len(list((old/'g4'/'commits').glob('*.json')))==1 and runtime_store.load(old)['templates']==tpl
    assert 'signed' not in json.loads((old/'g4'/'learned.json').read_text(encoding='utf-8'))
    assert cli(old,'whole-audit')['ok'] and cli(old,'g4-solve','--llm','off','--',L.T.replace('30','45'))['answer']=='19'
    other=tmp_path/'other';cli(other,'init','--individual-id','SOUL-OTHER')
    for name,signer,why in (('unsigned',None,'G4_LEARNING_UNSIGNED_LEGACY'),('foreign',other,'LEARNED_NOT_ITS_OWN')):
        d=tmp_path/name;shutil.copytree(base,d);legacy(d,signer)
        with pytest.raises(ValueError,match=why):runtime_store.load(d)
        r=cli(d,'g4-solve','--llm','off','--',L.T.replace('30','45'));assert not r['ok'] and r['error'].endswith(why),(name,r)

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

def test_a_reading_that_fails_the_checker_is_a_mistake_even_when_the_child_withholds():
    from tukuyo_g4 import life
    r={'answer':None,'reason':'DISAGREE:12,8','readings':[{'route':'llm_claude_story','parent':'claude','ok':True,'value':'12'},
       {'route':'llm_gemini_story','parent':'gemini','ok':True,'value':'8'},{'route':'llm_chatgpt_story','parent':'chatgpt','ok':False,'reason':'CHECK:SPAN_NOT_IN_TEXT:x'}]}
    # who of claude and gemini was wrong nobody can tell yet; chatgpt's reading did not hold up at all
    assert life.experiences(r)==[('parent_error',-0.3,0.2,'g4:reading','parent:chatgpt'),('honesty',0.5,0.3,'g4:withheld','')]

def test_looking_back_tells_who_was_right(tmp_path):
    # the parents disagree on a wording (claude 12, gemini 8): the child withholds and keeps the disagreement. Later two
    # parents agree on the same wording with other numbers (17): it learns it, answers the old text with it (12) and
    # looks back - claude had been right, gemini wrong - in the same episode as the learning, even across a kill
    import test_g4_life as G
    cli=_cli();T5b=G.T5.replace('30','45');R5b=json.loads(json.dumps(G.R5).replace('30','45'))
    other5=json.loads(json.dumps(G.R5));other5['facts'][3]['eq']='three * number + six = result'
    rec=tmp_path/'p.jsonl'
    rec.write_text('\n'.join([_line('claude',G.T5,G.R5),_line('gemini',G.T5,other5),_line('claude',T5b,R5b),_line('chatgpt',T5b,R5b)])+'\n',encoding='utf-8')
    d=tmp_path/'c';cli(d,'init','--individual-id','SOUL-LOOKBACK')
    r=cli(d,'think','--',G.T5,replay=rec);assert r['answer'] is None and r['reason']=='DISAGREE:12,8'
    assert cli(d,'g4-self')['disagreements_to_look_back_on']==1
    k=tmp_path/'killed';shutil.copytree(d,k)
    r=cli(d,'think','--',T5b,replay=rec);assert r['answer']=='17' and r['gen4']['learned']
    assert [x for x in r['life'] if x['theme']=='g4:hindsight']==[{'kind':'parent_help','theme':'g4:hindsight','relation':'parent:claude'},
                                                                 {'kind':'parent_error','theme':'g4:hindsight','relation':'parent:gemini'}]
    me=cli(d,'g4-self');assert me['disagreements_to_look_back_on']==0
    assert me['life_story']['looked_back']=={'claude':{'right':1,'wrong':0},'gemini':{'right':0,'wrong':1}}
    assert me['trust_in_parents']['gemini']<0.5<me['trust_in_parents']['claude']
    assert cli(d,'whole-audit')['ok'] and cli(d,'g4-audit')['ok']
    # the same thought, killed after its first experience: the next start finishes it, looking back included, once
    assert cli(k,'think','--',T5b,replay=rec,crash='g4:after_experience').get('rc')==-9
    assert cli(k,'whole-audit')['ok']
    assert [(e['kind'],e['theme'],e['relation']) for e in _g4_events(k)]==[(e['kind'],e['theme'],e['relation']) for e in _g4_events(d)]
    assert cli(k,'g4-self')['disagreements_to_look_back_on']==0 and _felt(k)==[e['event_sha256'] for e in _g4_events(k)]
