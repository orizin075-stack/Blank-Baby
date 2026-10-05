"""claude-patch5: V1023r open-world research preview (hidden-rule worlds, information-driven
experiments, method change when the hypothesis language fails, replication before claims,
refutation, remembered laws, signed journal with replay against the world key) and the
Parser B extension of the semantic gate."""
import ast,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py'
sys.path.insert(0,str(ROOT/'src'))

def run(d,*a,ok=True):
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    for k in ('TUKUYO_LLM_PROVIDER','TUKUYO_LLM_COMMAND','TUKUYO_LLM_TEACHERS'):env.pop(k,None)
    cmd=[sys.executable,'-B',str(CLI)];anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if anchor:cmd+=['--runtime-trust-file',anchor]
    p=subprocess.run(cmd+['--data',str(d),*map(str,a)],cwd=ROOT,env=env,capture_output=True,text=True,timeout=240);r=json.loads(p.stdout)
    if ok:assert p.returncode==0 and r.get('ok'),(a,r,p.stderr[-400:])
    return r

def test_cp5_agent_cannot_see_the_world_secret():
    src=(ROOT/'src/tukuyo_v1023r/agent.py').read_text(encoding='utf-8');tree=ast.parse(src);names=set()
    for n in ast.walk(tree):
        if isinstance(n,ast.ImportFrom):names|={a.name for a in n.names}
        if isinstance(n,ast.Attribute):names.add(n.attr)
    assert not names&{'DeviceWorld','_u','reveal','replay','true_agreement','_table','_key','_lawkey','WORLD_KEY'},names&{'DeviceWorld','_u','reveal','_table','_key'}

def test_cp5_worlds_outside_family_is_far_from_every_known_law():
    from tukuyo_v1023r.worlds import DeviceWorld,library,hamming
    lib=library();assert len(lib)==492 and len({r[2] for r in lib})==len(lib)
    for s in range(5):
        w=DeviceWorld('t',s,4,0.0);t=w.reveal()['table'];assert min(hamming(t,r[2]) for r in lib)>=6

def test_cp5_research_finds_laws_and_changes_method_when_language_fails():
    from tukuyo_v1023r.worlds import DeviceWorld
    from tukuyo_v1023r.ecology import run_episode,REGIMES
    for tier in (1,2,3):
        r=run_episode(DeviceWorld('t5',11,tier,0.0),'research',econ=REGIMES['costly_failure'],seed=11)
        assert r['alive'] and r['ledger_conserved'] and not r['wrong_law_claimed']
    r=run_episode(DeviceWorld('t5',11,4,0.0),'research',econ=REGIMES['safe_failure'],seed=11)
    assert r['method']=='TABLE' and 'METHOD_CHANGE' in r['events'] and not r['law_claimed']

def test_cp5_wrong_remembered_law_is_refuted_by_a_noise_free_outcome():
    from tukuyo_v1023r.worlds import DeviceWorld,library
    from tukuyo_v1023r.agent import ResearchAgent
    w=DeviceWorld('t5r',3,1,0.0);truth=w.reveal()['table'];wrong=next(r for r in library() if r[2]!=truth and r[0]==1 and r[1]!='常に消灯')
    a=ResearchAgent(prior_claim={'law':wrong[1],'table':wrong[2],'claimed_min_agreement_99':0.5})
    assert a.status=='CONFIRMED'
    for _ in range(60):
        off=w.work_offer();x,_p=a.work_choice(off['locked']);a.observe(w.work(off,x))
        if a.status!='CONFIRMED':break
    assert a.status=='RESEARCHING' and any(e['event']=='REFUTED' for e in a.events)

def test_cp5_expedition_journal_replay_and_forgery(tmp_path):
    d=tmp_path/'d';run(d,'init')
    a=run(d,'research-run','--world','W1','--tier','1','--noise','0.0','--ticks','160')
    assert a['alive'] and a['claim'] and a['environment_verdict']['law_correct']
    b=run(d,'research-run','--world','W1','--tier','1','--noise','0.0','--ticks','40')
    assert b['started_with_inherited_law']==a['claim']['law'] and 'USING_REMEMBERED_LAW' in b['events']
    au=run(d,'research-audit');assert au['replayed_from_world_key']==2 and not au['errors']
    assert run(d,'whole-audit')['ok']
    # A rewritten journal that is re-chained and re-signed with the individual's own key
    # still fails: the world key recomputes what the world actually answered.
    from tukuyo_v1023r import life
    from tukuyo_v1022 import store
    from tukuyo_v977 import whole_state as whole
    s=life.state(d);eid=s['expeditions'][0]['expedition'];rows,_h=life._read_journal(d,eid)
    k=next(i for i,r in enumerate(rows) if r.get('obs',{}).get('kind')=='probe');rows[k]['obs']['y']^=1
    head=life._write_journal(d,eid,[{x:v for x,v in r.items() if x!='prev'} for r in rows])
    s['expeditions'][0]['journal_head']=head;store.save(d,life.NS,life.COMPONENT,s);whole.sync(d)
    bad=run(d,'research-audit',ok=False);assert not bad['ok'] and any('V1023R_REPLAY' in e for e in bad['errors'])

def test_cp5_research_survives_restore(tmp_path):
    d=tmp_path/'d';run(d,'init');run(d,'realtime-start');run(d,'research-run','--world','W2','--tier','2','--noise','0.05','--ticks','60')
    path=run(d,'recovery-checkpoint')['path']
    run(d,'research-run','--world','W2','--ticks','40')
    assert run(d,'research-status')['expeditions']==2
    run(d,'recovery-restore',path,'--trust-file',d/'v1014/recovery.pub')
    st=run(d,'research-status');assert st['expeditions']==1
    assert run(d,'research-audit')['ok'] and run(d,'whole-audit')['ok']

def test_cp5_research_niche_in_real_metabolism(tmp_path):
    d=tmp_path/'d';run(d,'init')
    run(d,'metabolism-init','--families','2','--reservoir','80000','--max-age','6','--research-world')
    r=run(d,'metabolism-step','--ticks','8')
    acts=[a for a in r['last_tick']['actions']]
    assert r['research_niche'] and all('niche' in a for a in acts)
    assert len(r['deaths'])>=2 and {x['cause'] for x in r['deaths']}<={'AGE','ENERGY'}     # founders really die (max-age 6)
    for s in r['successions']:assert 'inherited_law' in s
    assert run(d,'metabolism-audit')['ok'] and run(d,'whole-audit')['ok']
    from tukuyo_v1023r.agent import ResearchAgent
    from tukuyo_v1023r.worlds import DeviceWorld
    w=DeviceWorld('c',1,2,0.05);a=ResearchAgent()
    for i in range(20):a.observe(w.probe(i))
    b=ResearchAgent.from_compact(json.loads(json.dumps(a.to_compact())))
    assert b.ll==a.ll or max(abs(x-y) for x,y in zip(a.ll,b.ll))<1e-9
    assert b.posterior()[1]==a.posterior()[1] or abs(b.posterior()[1]-a.posterior()[1])<1e-12

def test_cp5_parser_b_reads_word_problem_families_and_blocks_disagreement():
    from tukuyo_v1022 import semantic_gate as g
    cases={'りんごが12個あります。5個食べました。残りは何個？':'7','バスに15人乗っています。6人降りました。4人乗ってきました。今何人乗っていますか？':'13',
           '120円のノートを3冊と80円のペンを2本買いました。1000円出すとおつりは何円？':'480','子どもが6人います。1人に4枚ずつ色紙を配ると、色紙は何枚いりますか？':'24',
           '35人の子どもが5人ずつのグループを作ると、グループはいくつできますか？':'7','あめが23個あります。1人に5個ずつ配ると、あまりは何個？':'3',
           '兄はビー玉を35個持っています。弟は兄より8個少なく持っています。弟は何個持っていますか？':'27','ある数を3倍して5を足すと20になります。ある数はいくつ？':'5',
           'Tom has 12 apples. He eats 3 apples and gets 5 more. How many apples does he have now?':'14'}
    for q,v in cases.items():assert g.parser_b(q)==('value',v),(q,g.parser_b(q))
    # ambiguous verbs, unknown verbs and container questions stay UNDECIDED
    for q in ('りんごが10個あります。3個売りました。残りは何個？','池に魚が20匹いました。7匹つりました。残りは何匹？','1箱に10個入りが4箱あります。箱は全部で何個？'):
        assert g.parser_b(q) is None,q
    forged={'kind':'arithmetic','expression':'35-8-0'}
    r=g.audit('兄はビー玉を35個持っています。弟は兄より8個少なく持っています。弟は何個持っていますか？','43',{'kind':'arithmetic','expression':'35+8'})
    assert not r['ok'] and r['reason']=='INDEPENDENT_PARSER_DISAGREES'
    ok=g.audit('りんごが12個あります。5個食べました。残りは何個？','7',{'kind':'inventory','initial':12,'per':1,'events':[{'quantity':5,'direction':-1,'factor':1}]})
    assert ok['ok'] and ok['independent_parser']=='AGREE'
