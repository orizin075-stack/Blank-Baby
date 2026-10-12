import ast, copy, json, random, sys
from fractions import Fraction
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_v1022 import constraints, proofs
from tukuyo_v1022.constraints_verify import verify, read

@pytest.mark.parametrize('query,answer',[
 ('制約: A+B=18。B=2*A。Aは何？','6'),
 ('制約: 利益=売上-費用。利益=1800。費用=3200。売上は何？','5000'),
 ('制約: x+y+z=12。x-y=2。y-z=1。xは何？','17/3'),
 ('制約: x+y=10。x+yは何？','10'),
 ('制約: A=B+1。B=A-1。A-Bは何？','1'),
 ('制約: 0*x=0。y=7。yは何？','7'),
 ('制約: x=0.1。y=0.2。x+yは何？','3/10'),
 ('constraints: a+b=5; a-b=1; goal: a','3'),
 ('AとBの合計は30個。AはBの2倍。Aは何個？','20'),
 ('AとBの平均は15円。AはBより10円高い。Aは何円？','20'),
 ('AとBとCの合計は30個。AはBの2倍。BはCの3倍。Cは何個？','3'),
])
def test_compositional_goal_is_certified(query,answer):
 r=constraints.solve(query)
 assert r['answer']==answer,r
 assert proofs.check(r['proof'],answer)
 assert verify(query,answer,r['proof'])['target_uniqueness_certified']

def test_free_variables_do_not_force_an_individual_answer():
 q='制約: A+B=10。Aは何？';r=constraints.solve(q)
 assert r['answer'] is None and r['reason']=='CONSTRAINT_UNDERDETERMINED'
 assert r['information_requests']
 examples=r['counterexamples'];assert len(examples)==2
 for e in examples:
  w=e['assignment'];assert Fraction(w['A'])+Fraction(w['B'])==10
 assert examples[0]['target_value']!=examples[1]['target_value']

def test_new_evidence_recovers_the_same_goal():
 r=constraints.solve('制約: A+B=10。Aは何？')
 z=constraints.refine(r,'A-B=4')
 assert z['answer']=='7' and z['refinement_evidence']['recovered']
 assert proofs.check(z['proof'],'7')

def test_all_constraints_are_checked_even_outside_goal_dependencies():
 r=constraints.solve('制約: A+B=10。C=1。C=2。A+Bは何？')
 assert r['answer'] is None and r['reason']=='CONSTRAINT_INCONSISTENT'
 g=r['graph'];ms=[Fraction(x) for x in r['contradiction_certificate']['multipliers']]
 for v in g['variables']:
  assert sum(m*Fraction(e['coefficients'].get(v,'0')) for m,e in zip(ms,g['equations']))==0
 assert sum(m*Fraction(e['rhs']) for m,e in zip(ms,g['equations']))!=0

@pytest.mark.parametrize('q',[
 '制約: x=2。途中の条件は不明。xは何？',
 '制約: x=2。xは何？ y=99',
 '制約: x*y=12。xは何？',
 '制約: x=1/0。xは何？',
 '制約: x=2**100000。xは何？',
 '制約: x=__import__("os").system("touch bad")。xは何？',
 '制約: x=(1).__class__。xは何？',
 '制約: x=1。x<0。xは何？',
 'AとBの合計は12個。AはBの3倍かもしれない。Aは何個？',
 'AとBの合計は12個。AはBより1円多い。Aは何個？',
 'AとBの合計は5個。AはBの2倍。Aは何個？',
 'AとBの合計は10個。AはBより20個多い。Aは何個？',
 'AとBの合計は12個。AはBの2倍。Aは何箱？',
])
def test_unsupported_ambiguous_or_impossible_premises_are_withheld(q):
 r=constraints.solve(q);assert r is not None and r['answer'] is None,r

@pytest.mark.parametrize('field',['witness','multipliers','answer','graph','source_query','answer_argument'])
def test_independent_certificate_tampering_is_rejected(field):
 q='制約: A+B=18。B=2*A。Aは何？';p=copy.deepcopy(constraints.solve(q)['proof']);a='6'
 if field=='witness':p['certificate']['witness']['A']='7'
 elif field=='multipliers':p['certificate']['multipliers'][0]='0'
 elif field=='answer':p['certificate']['answer']='7'
 elif field=='graph':p['graph']['equations'][0]['rhs']='21'
 elif field=='source_query':p['source_query']=q.replace('18','21')
 else:a='7'
 assert not proofs.check(p,a)
 assert not verify(q,a,p)['supported']

def test_verifier_does_not_import_or_call_producer(monkeypatch):
 q='制約: x+y=10。x-y=4。xは何？';p=constraints.solve(q)['proof']
 def forbidden(*args,**kwargs):raise AssertionError('producer called')
 monkeypatch.setattr(constraints,'parse',forbidden);monkeypatch.setattr(constraints,'solve',forbidden);monkeypatch.setattr(constraints,'_eliminate',forbidden)
 assert verify(q,'7',p)['supported']
 source=(ROOT/'src/tukuyo_v1022/constraints_verify.py').read_text();tree=ast.parse(source)
 imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]+[a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
 assert set(imports)<= {'re','unicodedata','fractions'}

def test_certificate_cannot_use_inconsistent_premises_ex_falso():
 q='制約: x=1。x=2。xは何？'
 graph=read(q);p={'kind':'linear_constraints','source_query':q,'graph':graph,'certificate':{'witness':{'x':'1'},'multipliers':['1','0'],'answer':'1'}}
 assert not verify(q,'1',p)['supported']

def test_random_invertible_systems_and_goal_projections():
 rng=random.Random(6022105)
 for _ in range(120):
  x=rng.randint(-50,50);y=rng.randint(-50,50);a=rng.randint(2,9);b=rng.randint(1,8)
  q=f'制約: {a}*x+{b}*y={a*x+b*y}。x-y={x-y}。2*x+yは何？'
  r=constraints.solve(q);answer=str(2*x+y)
  assert r['answer']==answer,(q,r)
  assert verify(q,answer,r['proof'])['supported']
  assert not verify(q,str(2*x+y+1),r['proof'])['supported']

def test_limits_are_explicit_and_do_not_invoke_search_without_a_bound():
 q='制約: '+'。'.join(f'x{i}=1' for i in range(17))+'。x0は何？'
 r=constraints.solve(q);assert r['answer'] is None and r['reason']=='CONSTRAINT_VARIABLE_LIMIT'
 q='制約: '+'。'.join('x=1' for _ in range(33))+'。xは何？'
 r=constraints.solve(q);assert r['answer'] is None and r['reason']=='CONSTRAINT_STATEMENT_LIMIT'

def test_existing_numeric_average_is_not_claimed_as_a_relation_frame(monkeypatch):
 from tukuyo_v1022 import cognition
 q='10, 20, 30, 40 の平均は何？'
 assert constraints.solve(q) is None and read(q) is None
 monkeypatch.setattr(cognition,'state',lambda data:{'facts':[],'event_rules':{},'aliases':{}})
 r=cognition.solve('unused',q)
 assert r['answer']=='25' and not r['uncertain'],r

def test_public_surfaces_reject_a_faulting_generator(monkeypatch):
 from tukuyo_v1022 import cognition
 from tukuyo_v1005.verifier import _independent_crosscheck
 q='制約: A+B=18。B=2*A。Aは何？';p=constraints.solve(q)['proof']
 bad={'ok':True,'recognized':True,'answer':'7','uncertain':False,'confidence':.95,'proof':p}
 monkeypatch.setattr(cognition,'_solve_core',lambda *args,**kwargs:bad)
 r=cognition.solve('unused',q)
 assert r['uncertain'] and r['answer'] is None
 r=_independent_crosscheck(q,bad)
 assert r['uncertain'] and r['answer'] is None
