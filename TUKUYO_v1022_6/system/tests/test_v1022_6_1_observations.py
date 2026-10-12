import copy,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_v1022 import observation_reasoning as obs,proofs
from tukuyo_v1022.observation_verify import check
Q='制約: A+B=10。Aは何？'
TASK={'budget':10,'options':[{'id':'total','expression':'A+B','cost':1},{'id':'A','expression':'A','cost':8},{'id':'difference','expression':'A-B','cost':2}]}

def test_cheapest_informative_observation_beats_cheap_redundancy():
 r=obs.plan(Q,TASK);assert r['status']=='OBSERVE_THEN_REASON' and r['proof']['selected']==['difference'] and r['total_cost']==2
 assert r['answer'] is None and r['uncertain'] and check(r['proof'])
 assert r['claim_boundary']['observation_values_seen_during_planning'] is False

def test_observation_update_reproves_original_goal():
 p=obs.plan(Q,TASK)['proof'];r=obs.update(p,{'difference':'4'})
 assert r['answer']=='7' and proofs.check(r['proof'],'7')

def test_unselected_measurements_are_not_applied():
 q='制約: A+B=10。C=1。Aは何？';t={'budget':2,'options':[{'id':'probe','expression':'A+C','cost':2}]}
 p=obs.plan(q,t)['proof'];r=obs.update(p,{'probe':'8'});assert r['answer']=='7'
 q='制約: A=1。Aは何？';p=obs.plan(q,{'budget':2,'options':[{'id':'probe','expression':'A','cost':2}]})['proof']
 with pytest.raises(ValueError):obs.update(p,{'probe':'2'})

def test_two_observations_can_be_necessary_and_goal_specific():
 q='制約: A+B+C=20。Aは何？';t={'budget':8,'options':[{'id':'B','expression':'B','cost':2},{'id':'C','expression':'C','cost':3},{'id':'direct','expression':'A','cost':8}]}
 r=obs.plan(q,t);assert r['proof']['selected']==['B','C'] and r['total_cost']==5
 z=obs.update(r['proof'],{'B':'4','C':'7'});assert z['answer']=='9'

def test_budget_exhaustion_keeps_answer_unknown():
 t=copy.deepcopy(TASK);t['budget']=1;r=obs.plan(Q,t)
 assert r['status']=='NO_FEASIBLE_OBSERVATION_PLAN' and r['answer'] is None and r['search_complete']

def test_known_goal_needs_no_observation():
 r=obs.plan('制約: A+B=10。A+Bは何？',TASK)
 assert r['status']=='ALREADY_KNOWN' and r['total_cost']==0 and r['answer']=='10' and r['proof']['selected']==[]

@pytest.mark.parametrize('change',['cost','selected','task','query','complete','count'])
def test_plan_tampering_is_rejected(change):
 p=copy.deepcopy(obs.plan(Q,TASK)['proof'])
 if change=='cost':p['total_cost']=1
 elif change=='selected':p['selected']=['A'];p['total_cost']=8
 elif change=='task':p['task']['options'][2]['expression']='A+B'
 elif change=='query':p['source_query']='制約: A+B=10。Cは何？'
 elif change=='complete':p['search_complete']=False
 else:p['candidates_examined']=1
 assert not check(p)

@pytest.mark.parametrize('bad',[{'id':'x','expression':'A','cost':0},{'id':'x','expression':'A*B','cost':1},{'id':'x','expression':'C','cost':1},{'id':'x','expression':'A','cost':True},{'id':'x','expression':'A','cost':1,'value':'7'}])
def test_values_and_invalid_options_cannot_enter_planning(bad):
 r=obs.plan(Q,{'budget':10,'options':[bad]});assert r['status']=='OBSERVATION_PLAN_REJECTED' and r['answer'] is None

def test_verifier_does_not_call_producer(monkeypatch):
 p=obs.plan(Q,TASK)['proof']
 def fail(*a,**k):raise AssertionError('producer called')
 monkeypatch.setattr(obs,'prepare',fail);monkeypatch.setattr(obs,'_forced',fail);monkeypatch.setattr(obs,'plan',fail)
 assert check(p)

def test_fresh_numeric_values_transfer_after_the_same_plan():
 for total,difference in [(17,3),(37,-5),(102,18),(23,1),(100,0)]:
  q=f'制約: A+B={total}。Aは何？';p=obs.plan(q,TASK)['proof'];r=obs.update(p,{'difference':str(difference)})
  assert r['answer']==str((total+difference)//2) and proofs.check(r['proof'],r['answer'])

def test_inconsistent_base_and_excess_options_are_rejected():
 r=obs.plan('制約: A=1。A=2。Aは何？',TASK);assert r['status']=='OBSERVATION_PLAN_REJECTED'
 t={'budget':10,'options':[{'id':str(i),'expression':'A','cost':1} for i in range(9)]};assert obs.plan(Q,t)['status']=='OBSERVATION_PLAN_REJECTED'
