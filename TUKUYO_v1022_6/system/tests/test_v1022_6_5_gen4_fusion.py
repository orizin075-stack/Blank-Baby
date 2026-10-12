"""G4 fusion boundaries: exact surfaces, source binding, unit agreement and signed live learning."""
import copy,hashlib,json
from fractions import Fraction
from test_v1022_5_fusion import run
from tukuyo_g4 import api,fpl,learn,llm,runtime_store
from tukuyo_g4.proof import verify
from tukuyo_v977 import whole_state
import test_g4_learn as example


def test_g4_decimal_surfaces_retain_exact_large_and_small_values():
    for value in ['1234567890123456789.125','-0.0000000000000125','55/3','9007199254740993/8']:
        v=Fraction(value)
        assert Fraction(fpl.fmt(v))==v


def test_nonlinear_jacobian_rank_does_not_certify_a_unique_root():
    from tukuyo_g4.check import check
    s={'schema':fpl.SCHEMA,'text':'A number satisfies x*x-3*x+2=0. What is the number?',
       'quantities':[{'name':'x','unit':'1'},{'name':'three','unit':'1'},{'name':'two','unit':'1'}],
       'facts':[{'eq':'three = 3','span':'x*x-3*x+2=0'},{'eq':'two = 2','span':'x*x-3*x+2=0'},
                {'eq':'x*x-three*x+two = 0','span':'x*x-3*x+2=0'}],'ask':'x','unused':[]}
    for x in (1,2):
        r=check(s,{'x':x,'three':3,'two':2})
        assert not r['ok'] and any(e.startswith('NOT_UNIQUE') for e in r['failures'])


def test_g4_proof_binds_original_question_and_exact_answer():
    q='Nora had 30 shells. She gave 8 shells to her cousin. How many shells does she have left?'
    r=api.think(None,q,{'answer':None,'uncertain':True,'recognized':False},llm='off')
    assert r['answer']=='22' and verify(q,'22',r['proof'])
    assert not verify(q.replace('30','31'),'22',r['proof'])
    p=copy.deepcopy(r['proof']);p['values'][p['spec']['ask']]='23'
    assert not verify(q,'23',p)


def test_equal_teacher_numbers_with_different_units_do_not_agree(monkeypatch):
    q='There are 5 apples. How many apples?'
    def spec(unit):
        return {'schema':fpl.SCHEMA,'text':q,'quantities':[{'name':'amount','unit':unit,'integer':True}],
                'facts':[{'eq':'amount = 5','span':'5 apples'}],'ask':'amount','unused':[]}
    monkeypatch.setattr(api,'_own',lambda text:None)
    monkeypatch.setattr(llm,'parents',lambda:['claude','gemini'])
    monkeypatch.setattr(llm,'read',lambda text,view,parent:{'ok':True,'spec':spec('apple' if parent=='claude' else 'orange')})
    r=api.solve(q,llm='on',learn=False)
    assert r['answer'] is None and r['reason']=='UNIT_DISAGREEMENT'


def test_conflicting_template_is_suspended(tmp_path):
    s={'schema':fpl.SCHEMA,'text':example.T,'quantities':example.READING['quantities'],
       'facts':[{k:v for k,v in f.items() if k!='known' or v} for f in example.READING['facts']],'ask':'number','unused':[]}
    st=learn.Store(tmp_path/'g4');st.add(s,{'route':'test'})
    assert st.find(example.T)
    other=copy.deepcopy(s);other['facts'][3]['eq']='factor * number + twelve = result'
    assert st.add(other,{'route':'conflicting-test'}) is None
    assert st.find(example.T) is None


def test_live_template_cannot_be_forged_with_a_recomputed_checksum(tmp_path):
    d=tmp_path/'individual';run(d,'init')
    st=learn.Store(d/'g4')
    s={'schema':fpl.SCHEMA,'text':example.T,'quantities':example.READING['quantities'],
       'facts':[{k:v for k,v in f.items() if k!='known' or v} for f in example.READING['facts']],'ask':'number','unused':[]}
    st.add(s,{'route':'test-human-spec'})
    assert run(d,'whole-audit')['ok'] and runtime_store.audit(d)['ok']
    p=d/'g4/learned.json';o=json.loads(p.read_text());tid=next(iter(o['templates']))
    o['templates'][tid]['reading']['facts'][3]['eq']='factor * number + twelve = result'
    o['sha256']=hashlib.sha256(json.dumps(o['templates'],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    p.write_text(json.dumps(o))
    before=whole_state.state_path(d).read_bytes()
    import pytest
    with pytest.raises(ValueError,match='G4_LEARNING_CACHE_MISMATCH'):st.load()
    assert not whole_state.audit(d)['ok']
    assert whole_state.state_path(d).read_bytes()==before


def test_live_partial_learning_rollback_is_not_resealed(tmp_path):
    d=tmp_path/'individual';run(d,'init');st=learn.Store(d/'g4')
    s={'schema':fpl.SCHEMA,'text':example.T,'quantities':example.READING['quantities'],
       'facts':[{k:v for k,v in f.items() if k!='known' or v} for f in example.READING['facts']],'ask':'number','unused':[]}
    st.add(s,{'route':'test-human-spec'})
    old={p.relative_to(d/'g4'):p.read_bytes() for p in (d/'g4').rglob('*') if p.is_file()}
    st.add(s,{'route':'second-observation'})
    for p in (d/'g4').rglob('*'):
        if p.is_file():p.unlink()
    for rel,b in old.items():
        p=d/'g4'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    before=whole_state.state_path(d).read_bytes()
    import pytest
    with pytest.raises(ValueError,match='V1022_RECOVERY_HEAD:g4'):st.load()
    assert whole_state.state_path(d).read_bytes()==before


def test_g4_and_both_research_interfaces_share_live_runtime(tmp_path):
    d=tmp_path/'individual';run(d,'init')
    r=run(d,'think','--llm','off','--','Kim saw 4 cats in the morning. Later she saw one more cat. How many cats did she see in all?')
    assert r['answer']=='5' and r['proof']['kind']=='g4_reading'
    r=run(d,'verified-query','--','Kim saw 4 cats in the morning. Later she saw one more cat. How many cats did she see in all?')
    assert r['answer']=='5' and not r['uncertain']
    assert run(d,'think','制約: A+B=18。B=2*A。Aは何？')['answer']=='6'
    assert run(d,'whole-audit')['ok']
