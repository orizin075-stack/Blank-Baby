"""claude-patch4: semantic commit gate (coverage accounting + roles + separately written parser B),
mixed durations and price-operation chains, ability/voice forms in logic, and LLM 'verified' that needs
relevant claims and fully backed content. Cases from the external v1022.5 review are included."""
import ast,json,os,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py';MOCK=ROOT/'tools'/'mock_llm_provider.py'
sys.path.insert(0,str(ROOT/'src'))

def run(d,*a,ok=True,mode=None):
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    for k in ('TUKUYO_LLM_PROVIDER','TUKUYO_LLM_COMMAND','TUKUYO_LLM_TEACHERS'):env.pop(k,None)
    if mode:env.update({'TUKUYO_LLM_COMMAND':f'{sys.executable} -B {MOCK}','MOCK_LLM_MODE':mode,'MOCK_LLM_STATE':str(Path(d).parent/'mock_state')})
    cmd=[sys.executable,'-B',str(CLI)];anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if anchor:cmd+=['--runtime-trust-file',anchor]
    p=subprocess.run(cmd+['--data',str(d),*map(str,a)],cwd=ROOT,env=env,capture_output=True,text=True,timeout=240);r=json.loads(p.stdout)
    if ok:assert p.returncode==0 and r.get('ok'),(a,r,p.stderr[-400:])
    return r
def think(d,q):return run(d,'think','--',q)

def test_cp4_gate_imports_no_producer_module():
    tree=ast.parse((ROOT/'src/tukuyo_v1022/semantic_gate.py').read_text(encoding='utf-8'))
    banned={'wordprob','wordprob2','deliberation','deliberation_verify','meta_reasoning','meta_reasoning_verify','hypothesis','hypothesis_verify','qtime','nl_arith','cognition','logic2','kqa','proofs','explain'}
    names=set()
    for n in ast.walk(tree):
        if isinstance(n,ast.Import):names|={a.name.split('.')[-1] for a in n.names}
        if isinstance(n,ast.ImportFrom):names|={(n.module or '').split('.')[-1]}|{a.name for a in n.names}
    assert not names&banned,names&banned

def test_cp4_gate_unit_blocks_partial_and_disagreeing_proofs():
    from tukuyo_v1022 import semantic_gate as g
    q='時速5kmで3時間20分歩くと、何km進みますか？'
    assert g.audit(q,'15',{'kind':'deliberation','givens':{'speed':'5','hours':'3'},'steps':[{'label':'d','expression':'5*3','value':'15'}],'answer':'15'})['reason']=='INDEPENDENT_PARSER_DISAGREES'
    q2='りんごが17個あります。りんごの箱が2つあります。4個食べました。残りは何個？'
    r=g.audit(q2,'13',{'kind':'inventory','initial':17,'per':1,'events':[{'quantity':4,'direction':-1,'factor':1}]})
    assert r['reason']=='UNCOVERED_NUMERIC_OR_OPERATION' and '2' in r['unexplained']
    ok=g.audit('りんごが17個あります。4個食べました。残りは何個？','13',{'kind':'inventory','initial':17,'per':1,'events':[{'quantity':4,'direction':-1,'factor':1}]})
    assert ok['ok'] and ok['coverage']=='ALL_NUMERIC_TOKENS_EXPLAINED'
    forged={'kind':'arithmetic','expression':'17-4','source_query':'りんごが17個あります。りんごの箱が2つあります。4個食べました。'}
    assert not g.audit(q2,'13',forged)['ok']                      # question text copied into the proof never counts

def test_cp4_review_cases_end_to_end():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','CP4-A')
        r=think(d,'時速6kmで2時間30分歩きました。何km進みましたか？')
        assert r['answer']=='15' and r['verification_evidence']['semantic_gate']['independent_parser']=='AGREE',r
        r=think(d,'2000円の商品を20%引きし、さらに25%引きし、その後10%値上げしました。最終価格は？')
        assert r['answer']=='1320' and r['verification_evidence']['semantic_gate']['independent_parser']=='AGREE',r
        for q in ['2000円の商品Aを20%引きし、商品Bを25%引きし、その後10%値上げしました。最終価格は？',
                  '1箱に12個入りが6箱あります。箱は全部で何個？','ペンとノートが合わせて18本あります。ペンは何本？',
                  '9時に、みかんが20個ありました。6個食べました。残りは何個？','1500円の品物を3割引きにする予定です。値段はいくら？']:
            r=think(d,q);assert r['answer'] is None,(q,r)
        assert think(d,'水が3Lあります。400mL使い、さらに1.5L使いました。残りは何mL？')['answer']=='1100'
        assert think(d,'お茶が2L300mLあります。800mL飲みました。残りは何mL？')['answer']=='1500'
        assert think(d,'3000円のかばんを2割引きにし、そこから200円引きました。いくらになりましたか？')['answer']=='2200'
        r=run(d,'verified-query','時速6kmで2時間30分歩きました。何km進みましたか？');assert r['answer']=='15' and not r['uncertain']
        assert run(d,'whole-audit')['ok']

def test_cp4_ability_and_voice_are_not_events():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','CP4-B')
        for q in ['花子が泳げば花子は疲れる。花子は泳げる。花子は疲れた？','窓を開ければ寒くなる。窓が開いた。寒くなる？',
                  'If Ann swims, Ann gets tired. Ann can swim. Does Ann get tired?']:
            assert think(d,q)['answer'] is None,q
        assert think(d,'If Ann swims, Ann gets tired. Ann swims. Does Ann get tired?')['answer'].startswith('Yes')
        assert think(d,'No snakes can walk. Sid is a snake. Can Sid walk?')['answer'].startswith('No')

def test_cp4_llm_verified_needs_relevant_claims_and_backed_content():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','CP4-C');run(d,'knowledge-add','星野村の人口は1240人である。')
        for m in ('fabricate','fabricate2'):
            r=run(d,'llm-ask','--no-local-first','光の速さは？',mode=m);assert r['status']!='verified' and r['uncertain'],(m,r)
        r=run(d,'llm-ask','--no-local-first','12かける9足す3は？',mode='honest');assert r['status']=='verified'
        r=run(d,'llm-ask','--no-local-first','星野村の人口は？',mode='honest');assert r['status']=='verified'
        assert run(d,'llm-audit')['ok']
