import copy,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_v1022 import active_research as research
from tukuyo_v1022.research_verify import check
Q='制約: A+B=10。Aは何？'
CAP={'budget':5,'measurements':{'A':4,'B':1}}

def test_question_generated_without_external_options_or_values():
 r=research.run(Q,CAP)
 assert r['next_observation']=={'variable':'B','cost':1,'question':'Bは何？'}
 assert r['status']=='AWAITING_OBSERVATION' and r['answer'] is None and check(r['proof'])
 assert r['proof']['plan']['selected']==['B']

def test_one_observation_establishes_goal_and_stops():
 r=research.run(Q,CAP,[{'variable':'B','value':3}])
 assert r['answer']=='7' and r['spent']==1 and r['remaining_budget']==4
 assert r['status']=='GOAL_ESTABLISHED' and r['next_observation'] is None and check(r['proof'])

def test_partial_observation_replans_goal_specific_combination():
 q='制約: A+B+C=20。Aは何？';c={'budget':8,'measurements':{'A':8,'B':2,'C':3}}
 r=research.run(q,c);assert r['proof']['plan']['selected']==['B','C'] and r['next_observation']['variable']=='B'
 r=research.run(q,c,[{'variable':'B','value':'4'}]);assert r['answer'] is None and r['spent']==2 and r['next_observation']['variable']=='C'
 r=research.run(q,c,[{'variable':'B','value':'4'},{'variable':'C','value':'7'}]);assert r['answer']=='9' and r['spent']==5 and check(r['proof'])

def test_unavailable_sensor_costs_energy_budget_and_chooses_alternative():
 events=[{'variable':'B','error':'unavailable'}]
 r=research.run(Q,CAP,events);assert r['spent']==1 and r['next_observation']['variable']=='A'
 r=research.run(Q,CAP,events+[{'variable':'A','value':'7'}]);assert r['answer']=='7' and r['spent']==5

def test_failure_can_exhaust_budget_without_confident_answer():
 c={'budget':4,'measurements':{'A':4,'B':1}};r=research.run(Q,c,[{'variable':'B','error':'unavailable'}])
 assert r['status']=='NO_AFFORDABLE_RESEARCH' and r['answer'] is None and r['spent']==1 and check(r['proof'])

def test_known_goal_needs_no_measurements_even_without_sensors():
 r=research.run('制約: A+B=10。A+Bは何？',{'budget':0,'measurements':{}})
 assert r['answer']=='10' and r['spent']==0 and check(r['proof'])

def test_irrelevant_and_known_variables_are_not_measured():
 q='制約: A+B=10。C=2。D+E=5。Aは何？'
 r=research.run(q,{'budget':5,'measurements':{'A':4,'B':2,'C':1,'D':1,'E':1}})
 assert r['next_observation']['variable']=='B' and r['proof']['plan']['selected']==['B']

def test_goal_can_be_forced_without_every_variable_known():
 r=research.run('制約: A+B+C=20。A+Bは何？',{'budget':1,'measurements':{'C':1}},[{'variable':'C','value':3}])
 assert r['answer']=='17' and check(r['proof'])

def test_fractional_measurement_remains_exact():
 r=research.run('制約: A+B=10/3。Aは何？',CAP,[{'variable':'B','value':'1/3'}])
 assert r['answer']=='3' and check(r['proof'])

def test_canonical_ties_do_not_depend_on_mapping_order():
 a=research.run(Q,{'budget':1,'measurements':{'B':1,'A':1}})
 b=research.run(Q,{'budget':1,'measurements':{'A':1,'B':1}})
 assert a['next_observation']==b['next_observation'] and a['next_observation']['variable']=='A'

@pytest.mark.parametrize('events',[[{'variable':'A','value':7}],[{'variable':'B','value':True}],[{'variable':'B','value':'1/0'}],[{'variable':'B','value':3,'error':'unavailable'}],[{'variable':'B','error':'timeout'}],[{'variable':'B','value':3},{'variable':'A','value':7}],[{'variable':'B','error':'unavailable'},{'variable':'B','value':3}],{'B':3}])
def test_unselected_malformed_future_and_repeated_events_rejected(events):
 r=research.run(Q,CAP,events);assert r['status']=='RESEARCH_REJECTED' and r['answer'] is None and r['proof'] is None

@pytest.mark.parametrize('cap',[{'budget':True,'measurements':{'B':1}},{'budget':2,'measurements':{'Z':1}},{'budget':2,'measurements':{'B':True}},{'budget':2,'measurements':{'B':0}},{'budget':2,'measurements':{'B':1},'value':3},{'budget':2,'measurements':{'B':{'cost':1,'value':3}}}])
def test_capabilities_do_not_embed_hidden_answers_or_unsupported_variables(cap):
 assert research.run(Q,cap)['status']=='RESEARCH_REJECTED'

@pytest.mark.parametrize('field',['spent','next','history_value','history_cost','source','query','answer','answer_proof','capability','events','plan','status','conflict'])
def test_independent_replay_rejects_packet_tampering(field):
 p=copy.deepcopy(research.run(Q,CAP,[{'variable':'B','value':3}])['proof'])
 if field=='spent':p['spent']=0
 elif field=='next':p['next_observation']={'variable':'A','cost':4,'question':'Aは何？'}
 elif field=='history_value':p['history'][0]['event']['value']=4
 elif field=='history_cost':p['history'][0]['measurement']['cost']=0
 elif field=='source':p['source_query']='制約: A+B=11。Aは何？'
 elif field=='query':p['current_query']='制約: A+B=10。B=4。Aは何？'
 elif field=='answer':p['answer']='6'
 elif field=='answer_proof':p['answer_proof']['certificate']['answer']='6'
 elif field=='capability':p['capabilities']['budget']=0
 elif field=='events':p['events']=[]
 elif field=='plan':p['history'][0]['plan']['selected']=['A']
 elif field=='status':p['status']='AWAITING_OBSERVATION'
 else:p['conflict']=True
 assert not check(p)

def test_independent_checker_works_with_producer_disabled(monkeypatch):
 p=research.run(Q,CAP,[{'variable':'B','error':'unavailable'},{'variable':'A','value':7}])['proof']
 def forbidden(*args,**kwargs):raise AssertionError('producer used')
 monkeypatch.setattr(research,'run',forbidden);monkeypatch.setattr(research,'_decision',forbidden)
 monkeypatch.setattr(research.observation_reasoning,'plan',forbidden);monkeypatch.setattr(research.constraints,'solve',forbidden)
 assert check(p)

def test_zero_budget_or_no_informative_sensor_is_proven_infeasible():
 for c in ({'budget':0,'measurements':{'B':1}},{'budget':5,'measurements':{}}):
  r=research.run(Q,c);assert r['status']=='NO_AFFORDABLE_RESEARCH' and check(r['proof'])

def test_future_values_cannot_change_the_first_question():
 for value in (-100,0,3,100,'1/7'):
  r=research.run(Q,CAP,[{'variable':'B','value':value}]);assert r['proof']['history'][0]['measurement']['variable']=='B' and check(r['proof'])

def test_nonrational_inconsistent_and_nonlinear_sources_refuse():
 for q in ('制約: A=1。A=2。Aは何？','制約: A*B=10。Aは何？','AとBの合計は10個。Aは何個？'):
  assert research.run(q,CAP)['status']=='RESEARCH_REJECTED'

def test_exhaustion_after_unavailability_replays_without_producer():
 r=research.run(Q,{'budget':1,'measurements':{'B':1}},[{'variable':'B','error':'unavailable'}])
 assert r['status']=='NO_AFFORDABLE_RESEARCH' and r['spent']==1 and check(r['proof'])

def test_sensor_and_replay_statement_bounds_are_enforced():
 names=[chr(65+i) for i in range(9)]
 q='制約: '+'+'.join(names)+'=20。Aは何？'
 assert research.run(q,{'budget':20,'measurements':{name:1 for name in names}})['status']=='RESEARCH_REJECTED'
 q='制約: '+'。'.join(['A+B=10']*32)+ '。Aは何？'
 assert research.run(q,CAP)['status']=='RESEARCH_REJECTED'
