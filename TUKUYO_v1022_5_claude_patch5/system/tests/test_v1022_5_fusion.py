"""Exercise conflicts between both branches through public commands and proof APIs."""
import copy,json,os,subprocess,sys,tempfile
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from tukuyo_v1022 import cognition,logic2,kqa,proofs
from tukuyo_v1022_llm import providers,study

def run(data,*args,extra=None,ok=True):
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    for name in ('TUKUYO_LLM_PROVIDER','TUKUYO_LLM_COMMAND','TUKUYO_LLM_TEACHERS','TUKUYO_LLM_MIN_TEACHERS'):
        env.pop(name,None)
    env.update(extra or {})
    command=[sys.executable,'-B',str(ROOT/'run_tukuyo.py')]
    anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if anchor:command+=['--runtime-trust-file',anchor]
    result=subprocess.run(command+['--data',str(data),*map(str,args)],env=env,capture_output=True,text=True,timeout=240)
    body=json.loads(result.stdout)
    if ok:assert result.returncode==0 and body.get('ok'),(args,body,result.stderr)
    return body

def test_shared_event_refusal_precedes_every_answer_route():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','FUSION-NEGATION')
        for q in ['時速5kmで4時間歩きません。何km進む？',
                  '24枚のカードを6人で分けません。1人何枚？',
                  '1冊120円のノートを3冊買いません。全部でいくら？',
                  '800円の商品を25%値引きする予定です。価格は何円？',
                  'A train did not travel at 5 km per hour for 4 hours. How far did it travel?']:
            assert run(d,'think',q)['answer'] is None,q
            assert run(d,'verified-query',q)['uncertain'],q
        q='1箱に8個入りが4箱あります。3個食べていません。残りは何個？'
        assert run(d,'think',q)['answer']=='32'
        assert run(d,'whole-audit')['ok']

def test_old_and_new_reasoning_routes_coexist():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','FUSION-ROUTES')
        cases=[('A=3。B=A*4。C=B+2。Cは何？','14','meta_derivation'),
               ('x=1のときy=3、x=2のときy=5、x=4のときy=9。x=7のときyは何？','15','hypothesis'),
               ('800円の商品を25%値引きした価格は何円？','600','deliberation'),
               ('バスに12人乗っていて、5人降りて7人乗った。今何人？','14','arithmetic')]
        for q,a,kind in cases:
            r=run(d,'think',q)
            assert r['answer']==a and r['proof']['kind']==kind and proofs.check(r['proof'],a),(q,r)
        conflict='A=3。B=A*4。B=13。Bは何？'
        assert run(d,'think',conflict)['answer'] is None

def test_full_logic_overrules_inconsistent_legacy_premises():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','FUSION-CONTRADICTION')
        r=run(d,'think','雨なら試合は中止だ。雨だ。雨ではない。どうなる？')
        assert r['answer'] is None and r['reason']=='PREMISES_CONTRADICT'
        r=logic2.solve('AはBより重い。BはCより重い。AとCではどちらが重い？')
        assert proofs.check(r['proof'],r['answer'])
        forged=copy.deepcopy(r['proof']);forged['answer']='Cの方が重いです。'
        assert not proofs.check(forged,forged['answer'])
        forged=copy.deepcopy(r['proof']);forged['source_query']='CはAより重い。CとAではどちらが重い？'
        assert not proofs.check(forged,r['answer'])

def test_knowledge_proof_binds_entity_and_attribute():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','FUSION-KNOWLEDGE')
        run(d,'knowledge-add','緑ヶ丘病院の院長は村井ケイである。')
        r=run(d,'think','緑ヶ丘病院の院長は？')
        assert r['answer']=='村井ケイ' and proofs.check(r['proof'],r['answer'])
        for field,value in [('entity','青葉病院'),('attribute','副院長'),('source_query','青葉病院の院長は？')]:
            forged=copy.deepcopy(r['proof']);forged[field]=value
            assert not proofs.check(forged,r['answer'])

def test_duplicate_teacher_configuration_cannot_satisfy_quorum(monkeypatch):
    teacher={'provider':'command','command':f'{sys.executable} -B {ROOT}/tools/mock_llm_provider.py --mode=honest'}
    monkeypatch.setenv('TUKUYO_LLM_TEACHERS',json.dumps([teacher,teacher]))
    assert len(providers.teachers())==1
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','FUSION-QUORUM')
        q=Path(td)/'questions.json';q.write_text(json.dumps({'questions':['unknown']}))
        result=run(d,'llm-teach',q,extra={'TUKUYO_LLM_TEACHERS':json.dumps([teacher,teacher]),'TUKUYO_LLM_MIN_TEACHERS':'2'},ok=False)
        assert not result['ok'] and 'NEED_2_TEACHERS_HAVE_1' in result['error']

def test_llm_audit_covers_self_study_chain_and_head():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','FUSION-STUDY')
        question='1箱に10個入りが3箱あります。4個出荷しました。残りは何個？'
        assert run(d,'llm-ask',question)['status']=='abstained'
        r=run(d,'self-study',extra={'TUKUYO_LLM_COMMAND':f'{sys.executable} -B {ROOT}/tools/mock_llm_provider.py','MOCK_LLM_MODE':'honest'})
        assert r['now_solved_locally']==1 and run(d,'llm-audit')['studies']==1
        for name in ('STUDY.jsonl','STUDY_HEAD.json'):
            p=d/'v1022_llm'/name;original=p.read_bytes();value=json.loads(original)
            value['count' if name.endswith('.json') else 'now_solved_locally']=999
            p.write_text(json.dumps(value)+'\n')
            assert not study.audit(d)['ok']
            assert not run(d,'llm-audit',ok=False)['ok']
            p.write_bytes(original)
        assert run(d,'llm-audit')['ok'] and run(d,'whole-audit')['ok']

def test_complete_logic_resource_bounds_fail_closed():
    r=logic2.solve('A'*2001)
    assert r['verdict']=='refused' and r['reason']=='LOGIC_QUERY_LIMIT'
    r=logic2.solve('。'.join(['雨だ']*65)+'。雨？')
    assert r['verdict']=='refused' and r['reason']=='LOGIC_SENTENCE_LIMIT'
    chain='。'.join(f'人物{i}は人物{i+1}より重い' for i in range(33))+'。人物0と人物33ではどちらが重い？'
    r=logic2.solve(chain)
    assert r['verdict']=='refused' and r['reason']=='ORDER_NODE_LIMIT'

def test_complete_number_coverage_precedes_partial_price_parse():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','FUSION-PRICE-COVERAGE')
        question='1本100円のペンを2本、1冊300円のノートを3冊買う。代金はいくら？'
        r=run(d,'think',question)
        assert r['answer']=='1100' and r['fusion_resolution']['discarded_partial_legacy_answer']=='200'
        assert proofs.check(r['proof'],'1100')
        forged=copy.deepcopy(r['proof']);forged['source_query']='1本100円のペンを2本買う。代金はいくら？'
        assert not proofs.check(forged,'1100')
        verified=run(d,'verified-query',question)
        assert verified['uncertain'] or verified['answer']=='1100'
        assert run(d,'think','時速5kmで4時間歩く。何時間歩く？')['answer'] is None

def test_self_study_limit_rejects_negative_and_unbounded_work():
    for limit in (0,-1,129,True):
        with pytest.raises(ValueError,match='SELF_STUDY_LIMIT'):study.candidates(Path('/tmp/nonexistent-study-fixture'),limit)

def test_negative_occurrence_and_all_discount_stages_are_checked():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','FUSION-SECONDARY-GUARDS')
        for neg in ('雨が降らない','雨が降りません','雨が降っていない'):
            q=f'もし雨が降るなら道路が濡れる。雨が降る。{neg}。道路は濡れますか？'
            assert run(d,'think',q)['answer'] is None
            assert run(d,'verified-query',q)['uncertain']
        for q,a in [('1000円の品を20%割引し、さらに25%割引しました。価格はいくら？','600'),
                    ('2400円の商品を25%割引して、次に10%値上げしました。値段は何円？','1980')]:
            r=run(d,'think',q)
            assert r['answer']==a and proofs.check(r['proof'],a)
            v=run(d,'verified-query',q)
            assert v['uncertain'] or v['answer']==a
        q='1000円の品を20%割引し、別の品を25%割引しました。価格はいくら？'
        assert run(d,'think',q)['answer'] is None
