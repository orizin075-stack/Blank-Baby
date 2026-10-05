"""claude-patch6: read what the question asks (situation model: holders, events and the question's role),
new problem families with replayable proofs (mathprob), another person's stock is out of scope, and law
invention for the V1023r research agent (a public grammar with a prior shared by the whole grammar, claims
checked against the whole grammar, fed curiosity while unexplained, tier-5 worlds, versioned replay of
expeditions recorded before invention existed)."""
import ast,hashlib,json,math,os,subprocess,sys
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
def _names(path):
    tree=ast.parse(path.read_text(encoding='utf-8'));names=set()
    for n in ast.walk(tree):
        if isinstance(n,ast.Import):names|={a.name.split('.')[-1] for a in n.names}
        if isinstance(n,ast.ImportFrom):names|={(n.module or '').split('.')[-1]}|{a.name for a in n.names}
        if isinstance(n,ast.Attribute):names.add(n.attr)
    return names
def _solve_all(d,cases):
    from tukuyo_v1022 import cognition,proofs
    for q,exp in cases.items():
        r=cognition.solve(str(d),q);ans=None if r.get('uncertain') else r.get('answer')
        assert ans==exp,(q,ans,r.get('reason'))
        if exp is not None:assert proofs.check(r['proof'],exp),q

def test_cp6_independence_and_secrecy_import_graph():
    # Parser B (the semantic gate) stays independent of the new producers
    assert not _names(ROOT/'src/tukuyo_v1022/semantic_gate.py')&{'situation','mathprob'}
    # neither the agent nor the invention grammar can see a world's secret
    secret={'DeviceWorld','_u','reveal','replay','true_agreement','_key','_lawkey','WORLD_KEY'}
    for f in ('agent.py','invent.py'):assert not _names(ROOT/'src/tukuyo_v1023r'/f)&secret,f

def test_cp6_question_target_holders_and_roles(tmp_path):
    d=tmp_path/'d';run(d,'init','--individual-id','CP6-A')
    _solve_all(d,{
        'りんごが12個あります。妹に5個あげました。あげたのは何個？':'5',
        'みかんが20個あります。8個食べました。はじめにあったのは何個？':'20',
        'たまごが30個あります。12個使って、8個買いました。買う前は何個ありましたか？':'18',
        '姉はおはじきを50個持っています。妹はおはじきを20個持っています。姉は妹に8個あげました。妹は今何個持っていますか？':'28',
        '姉はおはじきを50個持っています。妹はおはじきを20個持っています。姉は妹に8個あげました。姉は今何個持っていますか？':'42',
        'かきが18個とくりが30個あります。かきを6個食べました。くりは何個ありますか？':'30',
        'Lucy has 14 marbles. Tom has 9 marbles. Lucy gives Tom 4 marbles. How many marbles does Tom have now?':'13',
        'Ken had 30 stamps. He gave 8 stamps to Joe and 5 stamps to Amy. How many stamps does Ken have left?':'17',   # patch5: 27
        'Ken had 30 stamps. He gave 8 stamps to Joe and 5 stamps to Amy. How many stamps did he give to Amy?':'5',
        '1箱に8個入りが4箱あります。別の人が別の在庫から3個食べました。残りは何個？':'32',
        # unknown holdings, unclear time and ambiguous holders stay unanswered
        'りんごが12個あります。妹に5個あげました。妹は何個持っていますか？':None,
        'りんごが12個あります。5個食べました。りんごは何個ありましたか？':None,
        'Kate had 25 crayons. She gave 8 crayons to Max. How many crayons does Max have now?':None,
        'りんごが20個あります。何個か食べました。残りは何個？':None})

def test_cp6_new_families_answer_with_replayable_proofs_or_refuse(tmp_path):
    d=tmp_path/'d';run(d,'init','--individual-id','CP6-B')
    _solve_all(d,{
        '5回のテストの点数は64点、78点、90点、85点、73点でした。平均は何点ですか？':'78',
        '8と12と20の最小公倍数はいくつですか？':'120',
        '30と45の最大公約数はいくつですか？':'15',
        '底辺が10cm、高さが6cmの三角形の面積は何cm²ですか？':'30',
        '41人が1台の車に4人ずつ乗ります。全員が乗るには、車は何台いりますか？':'11',
        '子どもが6人います。1人に5枚ずつ色紙を配ると、4枚足りませんでした。色紙ははじめに何枚ありましたか？':'26',
        '90個の3分の2は何個ですか？':'60',
        '1000円札で、230円のパンと150円の牛乳を買いました。おつりはいくら？':'620',
        'What is the greatest common factor of 18 and 24?':'6',
        'A train travels 240 km in 3 hours. What is its speed?':'80',
        # not whole, not a single answer, or not affordable: refused
        '50人の3分の1は何人？':None,'800円の3分の1は何円？':None,'15と20の公倍数はいくつですか？':None,'1, 4, 9, 16 の次の数は？':None,
        '500円持っています。1本120円のジュースを5本買うと、残りはいくらですか？':None})
    from tukuyo_v1022 import mathprob,proofs
    r=mathprob.solve('8と12と20の最小公倍数はいくつですか？');p=r['proof']
    assert proofs.check(p,'120') and not proofs.check(p,'240')
    assert not proofs.check({**p,'expression':'lcm(8,12,20)*2'},'120') and not proofs.check({**p,'answer':'240'},'240')

def test_cp6_more_families_directions_and_number_words(tmp_path):
    d=tmp_path/'d';run(d,'init','--individual-id','CP6-C')
    _solve_all(d,{
        '電車に42人乗っていました。駅で15人降りて、9人乗りました。電車には今何人乗っていますか？':'36',
        '電車に42人乗っていました。駅で15人降りて、9人乗りました。駅で降りたのは何人ですか？':'15',
        '体育館に子どもが45人集まっていました。12人帰りました。体育館には今何人いますか？':'33',
        'A class has 28 students. 4 more students join, then 6 students leave. How many students are in the class now?':'26',
        '赤いテープは60cm、青いテープは15cmです。赤いテープの長さは青いテープの長さの何倍ですか？':'4',
        '5本で400円のえんぴつがあります。1本の値段はいくらですか？':'80',
        '1列に8人ずつ並ぶと、5列できました。全部で何人いますか？':'40',
        '3時間で150km走る車の時速は何kmですか？':'50',
        '30人のクラスで、そのうち5分の2が犬を飼っています。犬を飼っているのは何人ですか？':'12',
        '1個90円のパンを4個買って、1000円札を出しました。おつりはいくらですか？':'640',
        '73本の花を1つの花びんに8本ずつ入れます。全部入れるには、花びんはいくつ必要ですか？':'10',
        'You have 50 dollars. You buy 4 shirts for 9 dollars each. How much money is left?':'14',
        'There are 32 children. They form groups of 4. How many groups are there?':'8',
        'I think of a number. If I divide it by 4, I get 9. What is the number?':'36',
        # who is compared with whom decides the direction (patch5 answered 90 here)
        'Ann has 30 beads. Ann has 3 times as many beads as Kim. How many beads does Kim have?':'10',
        'Kim has 10 beads. Ann has 3 times as many beads as Kim. How many beads does Ann have?':'30',
        'Lisa read 12 pages on Monday and twice as many on Tuesday. How many pages did she read on Tuesday?':'24',
        'Paul has 16 stickers. Paul has 9 fewer stickers than Mary. How many stickers does Mary have?':'25',
        # traps: not exact, not affordable, not divisible, wrong unit, an amount spelled out in words (patch5 answered 3)
        'ひもAは48cm、ひもBは16cmです。ひもBはひもAの何倍の長さですか？':None,
        '3個で200円のみかんがあります。1個の値段はいくらですか？':None,
        'You have 30 dollars. You buy 4 shirts for 9 dollars each. How much money is left?':None,
        'There are 34 children. They form groups of 4. How many groups are there?':None,
        '3時間で150km走る車の分速は何mですか？':None,
        'Ten students were in the library. 3 more students came. How many students are in the library now?':None})

PATCH5_FINGERPRINT='7840bbdd62fe73a2bca55c6adf52e6cd886ff7fc8ecb058ba83f4df4c81aa3f3'   # patch5 agent, devkey seed 1000, 72 episodes
def test_cp6_invention_off_reproduces_patch5_bit_for_bit():
    from tukuyo_v1023r.worlds import DeviceWorld
    from tukuyo_v1023r.ecology import run_episode,REGIMES
    rows=[]
    for reg,econ in REGIMES.items():
        for tier in (1,2,3,4):
            for noise in (0.0,0.05,0.1):
                for pol in ('research','random_research','doing'):
                    r=run_episode(DeviceWorld('devkey',1000,tier,noise),pol,econ=econ,seed=1000,invent=False)
                    rows.append({k:r.get(k) for k in ('policy','alive','final_energy','actions','law_claimed','law_correct','status','method','events')})
    assert hashlib.sha256(json.dumps(rows,sort_keys=True,ensure_ascii=False).encode()).hexdigest()==PATCH5_FINGERPRINT

def test_cp6_grammar_is_new_public_and_priced():
    from tukuyo_v1023r.invent import grammar,log_priors,MASS,FAMILIES,groups
    from tukuyo_v1023r.worlds import library,hamming
    g=grammar();base={r[2] for r in library()}
    assert len(g)==14906 and len({r[1] for r in g})==len(g) and not {r[1] for r in g}&base
    assert {r[3] for r in g}==set(FAMILIES) and abs(sum(math.exp(v) for v in log_priors())-MASS)<1e-9
    assert sum(len(v) for v in groups().values())==len(g)
    from tukuyo_v1023r.worlds import DeviceWorld
    for s in range(6):
        t=DeviceWorld('cp6',s,5,0.0).reveal()['table'];assert t in {r[1] for r in g} and min(hamming(t,q) for q in base)>=4

def test_cp6_tier5_law_is_invented_confirmed_and_remembered():
    from tukuyo_v1023r.worlds import DeviceWorld
    from tukuyo_v1023r.ecology import run_episode,REGIMES
    E=REGIMES['safe_failure']
    r=run_episode(DeviceWorld('devkey',1003,5,0.0),'research',econ=E,seed=1003)
    assert r['law_correct'] and r['claim']['invented'] and r['claim_bound_held'] and 'LAW_LANGUAGE_RECOVERED' in r['events']
    off=run_episode(DeviceWorld('devkey',1003,5,0.0),'research',econ=E,seed=1003,invent=False)
    assert not off['law_claimed'] and off['method']=='TABLE'
    again=run_episode(DeviceWorld('devkey',1003,5,0.0,stream='visit2'),'research',econ=E,seed=1010,prior_claim=r['claim'])
    assert again['law_correct'] and 'USING_REMEMBERED_LAW' in again['events'] and again['actions']['probe']==0
    # tier 4 (random tables) stays unexplained, and nothing is claimed
    t4=run_episode(DeviceWorld('t5',11,4,0.0),'research',econ=E,seed=11)
    assert t4['method']=='TABLE' and not t4['law_claimed']

def test_cp6_a_better_law_outside_the_shortlist_blocks_the_claim():
    from tukuyo_v1023r.worlds import INPUTS,bit
    from tukuyo_v1023r.agent import ResearchAgent
    from tukuyo_v1023r.invent import grammar
    g={n:(n,t,c) for n,t,c,_ in grammar()}
    A=g['¬S1,¬S2,¬S3,¬S4,¬S5のうち4つ以上'];B=g['ちょうど1つがオン'];x0=(A[1]^B[1]).bit_length()-1
    assert bin(A[1]^B[1]).count('1')==1
    a=ResearchAgent();a._extend([A]);a._inv_at=[0,0]          # only A is on the shortlist
    for rep in range(3):
        for x in range(INPUTS):
            if x!=x0:a.absorb({'kind':'probe','n':rep*32+x,'x':x,'y':bit(A[1],x)})
    k=a.T.index(A[1]);w,_=a.posterior()
    assert w[k]>0.99 and a._p_full(k)<0.05 and not a.want_replication()
    a._revise()
    assert B[1] in a.T and a.events[-1]['event']=='INVENTED' and a.next_experiment()==x0

def test_cp6_invented_hypotheses_survive_compact_state():
    from tukuyo_v1023r.worlds import DeviceWorld
    from tukuyo_v1023r.agent import ResearchAgent
    a=ResearchAgent();w=DeviceWorld('devkey',1003,5,0.0)
    for i in range(64):a.observe(w.probe(i%32))
    assert a.ext
    b=ResearchAgent.from_compact(json.loads(json.dumps(a.to_compact())))
    assert b.T==a.T and b.NM==a.NM and b._inv_at==a._inv_at and abs(b.posterior()[1]-a.posterior()[1])<1e-12

def test_cp6_expedition_without_invention_record_replays_as_run(tmp_path):
    from tukuyo_v1023r import life
    import tukuyo_v1023r.agent as A
    from tukuyo_v1022 import store
    from tukuyo_v977 import whole_state as whole
    d=tmp_path/'d';run(d,'init')
    # a fixed world key: in this world the expedition changes method, so a replay WITH invention would not match
    (d/'v1023r_world').mkdir(parents=True,exist_ok=True);(d/'v1023r_world'/'WORLD_KEY').write_text('cp6-world-key-1')
    old=A.INVENT_DEFAULT;A.INVENT_DEFAULT=False
    try:life.run(d,'W4',120,'safe_failure',4,0.0)
    finally:A.INVENT_DEFAULT=old
    # make it look exactly like a patch5 record: no law_invention field, patch5 claim boundary
    s=life.state(d);ex=s['expeditions'][0];assert 'METHOD_CHANGE' in ex['events']
    ex.pop('law_invention');s['claim_boundary']=life.CLAIMS_PATCH5;store.save(d,life.NS,life.COMPONENT,s);whole.sync(d)
    au=run(d,'research-audit');assert au['ok'] and au['replayed_from_world_key']==1
    b=run(d,'research-run','--world','W5','--tier','5','--noise','0.0','--regime','safe_failure','--ticks','200')
    assert b['claim_boundary']['invents_laws_inside_a_fixed_grammar'] is True and b['environment_verdict']['law_correct'] is not False
    assert life.state(d)['claim_boundary']==life.CLAIMS and life.state(d)['expeditions'][1]['law_invention'] is True
    au=run(d,'research-audit');assert au['ok'] and au['replayed_from_world_key']==2
    assert run(d,'whole-audit')['ok']
