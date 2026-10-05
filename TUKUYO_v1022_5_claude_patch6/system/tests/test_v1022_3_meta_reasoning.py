import json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_v1022 import meta_reasoning,proofs
from tukuyo_v1022.meta_reasoning_verify import verify


def test_compound_problem_is_decomposed_and_verified():
    q='単価=120。個数=35。仕入単価=70。固定費=500。売上=単価*個数。変動費=仕入単価*個数。利益=売上-変動費-固定費。利益は何？'
    r=meta_reasoning.solve(q)
    assert r['answer']=='1250' and r['reason']=='META_DERIVED',r
    assert len(r['proof']['steps'])>=7 and proofs.check(r['proof'],'1250')
    v=verify(q,'1250');assert v['decidable'] and v['supported'],v
    assert not verify(q,'1251')['supported']


def test_two_independent_strategies_must_agree_before_commit():
    q='単価=120。個数=35。仕入単価=70。固定費=500。売上=単価*個数。変動費=仕入単価*個数。利益=売上-変動費-固定費。利益=(単価-仕入単価)*個数-固定費。利益は何？'
    r=meta_reasoning.solve(q)
    assert r['answer']=='1250' and r['reason']=='META_STRATEGY_AGREEMENT',r
    assert r['reasoning_evidence']['strategy_count']>=2 and r['reasoning_evidence']['strategy_agreement']


def test_failed_strategy_is_diagnosed_and_alternative_used():
    q='単価=120。個数=35。仕入単価=70。固定費=500。利益=売上-未知費。利益=(単価-仕入単価)*個数-固定費。利益は何？'
    r=meta_reasoning.solve(q)
    assert r['answer']=='1250',r
    assert r['failed_strategies'] and r['reasoning_evidence']['strategy_switch_available'],r
    blob=json.dumps(r['failed_strategies'],ensure_ascii=False)
    assert 'MISSING_DEPENDENCY' in blob and ('売上' in blob or '未知費' in blob)


def test_conflicting_successful_strategies_fail_closed():
    q='単価=120。個数=35。仕入単価=70。固定費=500。利益=(単価-仕入単価)*個数-固定費。利益=999。利益は何？'
    r=meta_reasoning.solve(q)
    assert r['answer'] is None and r['reason']=='META_STRATEGY_CONFLICT',r
    assert set(r['conflicting_values'])=={'999','1250'}
    v=verify(q,'1250');assert v['recognized'] and not v['decidable'] and not v['supported']


def test_cycle_is_not_fatal_when_independent_strategy_exists():
    q='A=B+1。B=A+1。A=5。Aは何？'
    r=meta_reasoning.solve(q)
    assert r['answer']=='5',r
    assert r['failed_strategies'] and 'CYCLE' in json.dumps(r['failed_strategies']),r


def test_missing_dependency_can_be_repaired_by_new_evidence():
    q='売上=5000。利益=売上-費用。利益は何？'
    r=meta_reasoning.solve(q)
    assert r['answer'] is None and r['reason']=='META_NO_SUCCESSFUL_STRATEGY',r
    z=meta_reasoning.refine(r,'費用=3200')
    assert z['answer']=='1800' and z['refinement_evidence']['recovered'],z
    assert proofs.check(z['proof'],'1800')


def test_meta_proof_tamper_is_rejected():
    q='A=3。B=A*4。C=B+2。Cは何？'
    r=meta_reasoning.solve(q);assert r['answer']=='14',r
    p=json.loads(json.dumps(r['proof']));p['steps'][-1]['value']='15'
    assert not proofs.check(p,'14')


def test_meta_rejects_code_execution_and_unbounded_operators():
    for q in [
        'A=__import__("os").system("echo pwn")。Aは何？',
        'A=(1).__class__。Aは何？',
        'A=[1,2,3]。Aは何？',
        'A=2**100。Aは何？',
    ]:
        r=meta_reasoning.solve(q)
        assert r is not None and r['answer'] is None,r


def test_meta_exact_fraction_chain():
    q='A=1/3。B=A*9。C=B/2。Cは何？'
    r=meta_reasoning.solve(q)
    assert r['answer']=='1.5' and proofs.check(r['proof'],'1.5'),r


def test_meta_random_affine_dependency_graphs():
    import random
    rnd=random.Random(10223)
    for _ in range(100):
        a=rnd.randint(-20,20);b=rnd.randint(-10,10);c=rnd.randint(1,9);d=rnd.randint(-12,12)
        q=f'A={a}。B=A*{c}+{b}。C=B+{d}。Cは何？'
        r=meta_reasoning.solve(q);expected=str(a*c+b+d)
        assert r['answer']==expected,(q,r,expected)
        assert proofs.check(r['proof'],expected)
        assert verify(q,expected)['supported']


def test_meta_random_equivalent_strategy_agreement():
    import random
    rnd=random.Random(32201)
    for _ in range(50):
        x=rnd.randint(1,40);p=rnd.randint(2,20);qv=rnd.randint(1,p);f=rnd.randint(0,100)
        text=f'個数={x}。単価={p}。原価={qv}。固定費={f}。利益=単価*個数-原価*個数-固定費。利益=(単価-原価)*個数-固定費。利益は何？'
        r=meta_reasoning.solve(text);expected=str((p-qv)*x-f)
        assert r['answer']==expected and r['reason']=='META_STRATEGY_AGREEMENT',(text,r)


def test_successful_derivation_can_be_abstracted_and_transferred():
    source='単価=120。個数=35。仕入単価=70。固定費=500。売上=単価*個数。変動費=仕入単価*個数。利益=売上-変動費-固定費。利益は何？'
    r=meta_reasoning.solve(source);schema=meta_reasoning.abstract_schema(r)
    assert set(schema['inputs'])=={'単価','個数','仕入単価','固定費'}
    q='単価=150。個数=20。仕入単価=90。固定費=300。利益は何？'
    z=meta_reasoning.solve_with_schema(q,schema)
    assert z['answer']=='900' and z['transfer_evidence']['schema_applied'],z
    assert proofs.check(z['proof'],'900')


def test_schema_transfer_requests_missing_inputs_instead_of_guessing():
    source='A=3。B=4。C=A*B。Cは何？';schema=meta_reasoning.abstract_schema(meta_reasoning.solve(source))
    z=meta_reasoning.solve_with_schema('A=8。Cは何？',schema)
    assert z['answer'] is None and z['reason']=='META_SCHEMA_INPUT_MISSING' and z['information_requests']==['B'],z


def test_no_strategy_names_missing_information_needed_for_retry():
    r=meta_reasoning.solve('売上=5000。利益=売上-費用-税。利益は何？')
    assert r['answer'] is None and set(r['information_requests'])=={'費用','税'},r
