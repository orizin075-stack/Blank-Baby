import copy,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_v1022 import hypothesis_research as h
from tukuyo_v1022.hypothesis_research_verify import check
TASK={'degree':2,'coefficient_values':[-1,0,1],'examples':[[0,0]],'target_x':2,'probe_costs':{'-1':1,'1':1,'2':10},'budget':3}

def test_generate_nine_hypotheses_and_plan_two_step_discrimination():
 r=h.run(TASK)
 assert r['survivor_count']==9 and r['answer'] is None and r['uncertain']
 assert r['worst_case_remaining_cost']==2 and r['next_observation']['x']=='-1' and check(r['proof'])
 assert r['proof']['generated_model_count']==27

def test_branch_updates_candidates_and_proves_target():
 r=h.run(TASK,[{'x':'-1','y':0}]);assert r['survivor_count']==3 and r['next_observation']['x']=='1' and r['answer'] is None
 r=h.run(TASK,[{'x':'-1','y':0},{'x':'1','y':2}])
 assert r['answer']=='6' and r['spent']==2 and r['status']=='TARGET_AGREEMENT_WITHIN_CLASS' and check(r['proof'])

def test_surprising_output_falsifies_class_instead_of_confident_answer():
 r=h.run(TASK,[{'x':'-1','y':999}])
 assert r['status']=='HYPOTHESIS_CLASS_FALSIFIED' and r['answer'] is None and r['survivor_count']==0 and r['spent']==1 and check(r['proof'])

def test_minimax_can_avoid_cheapest_first_question():
 task=copy.deepcopy(TASK);task['probe_costs']={'-1':1,'1':2,'2':2};task['budget']=2
 r=h.run(task);assert r['next_observation']['x']=='2' and r['worst_case_remaining_cost']==2 and check(r['proof'])

def test_goal_agreement_stops_without_identifying_all_hypotheses():
 task=copy.deepcopy(TASK);task['target_x']=0;task['budget']=0;task['probe_costs']={}
 r=h.run(task);assert r['answer']=='0' and r['survivor_count']==9 and r['spent']==0 and r['next_observation'] is None
 assert check(r['proof']) and r['claim_boundary']['world_membership_in_class_proven'] is False

def test_failure_burns_cost_and_switches_to_affordable_direct_probe():
 task=copy.deepcopy(TASK);task['budget']=11
 r=h.run(task,[{'x':'-1','error':'unavailable'}]);assert r['next_observation']['x']=='2' and r['spent']==1 and r['worst_case_remaining_cost']==10
 r=h.run(task,[{'x':'-1','error':'unavailable'},{'x':'2','y':6}]);assert r['answer']=='6' and r['spent']==11 and check(r['proof'])

def test_failure_can_leave_no_affordable_experiment():
 task=copy.deepcopy(TASK);task['budget']=10
 r=h.run(task,[{'x':'-1','error':'unavailable'}]);assert r['status']=='NO_AFFORDABLE_DISCRIMINATION' and r['answer'] is None and r['spent']==1 and r['worst_case_remaining_cost']==10 and check(r['proof'])

def test_uninformative_or_missing_probes_keep_answer_unknown():
 for probes in ({},{'0':1}):
  task=copy.deepcopy(TASK);task['probe_costs']=probes;r=h.run(task)
  assert r['status']=='NO_AFFORDABLE_DISCRIMINATION' and r['worst_case_remaining_cost'] is None and check(r['proof'])

def test_fractional_probe_and_answer_are_exact():
 task=copy.deepcopy(TASK);task['degree']=1;task['target_x']='1/3';task['probe_costs']={'1/2':1}
 r=h.run(task);assert r['next_observation']['x']=='1/2'
 r=h.run(task,[{'x':'1/2','y':'1/2'}]);assert r['answer']=='1/3' and check(r['proof'])

def test_all_nine_secret_worlds_recover_without_exposing_coefficients():
 for linear in (-1,0,1):
  for square in (-1,0,1):
   events=[]
   for i in range(3):
    r=h.run(TASK,events)
    if r['answer'] is not None:break
    x=int(r['next_observation']['x']);events.append({'x':str(x),'y':linear*x+square*x*x})
   assert r['answer']==str(2*linear+4*square) and r['spent']<=2 and check(r['proof'])

@pytest.mark.parametrize('field',['answer','spent','survivors','generated','next','history_event','history_cost','history_type','history_count','worst','target','events','status'])
def test_independent_checker_rejects_packet_tampering(field):
 p=copy.deepcopy(h.run(TASK,[{'x':'-1','y':0},{'x':'1','y':2}])['proof'])
 if field=='answer':p['answer']='5'
 elif field=='spent':p['spent']=1
 elif field=='survivors':p['survivors']=[[0,0,0]]
 elif field=='generated':p['generated_model_count']=1
 elif field=='next':p['next_observation']={'x':'2','cost':10,'question':'入力2で出力は何？'}
 elif field=='history_event':p['history'][0]['event']['y']=1
 elif field=='history_cost':p['history'][0]['question']['cost']=0
 elif field=='history_type':p['history'][0]['question']['cost']=True
 elif field=='history_count':p['history'][0]['survivors_after']=1
 elif field=='worst':p['worst_case_remaining_cost']=2
 elif field=='target':p['task']['target_x']=3
 elif field=='events':p['events']=[]
 else:p['status']='HYPOTHESIS_CLASS_FALSIFIED'
 assert not check(p)

@pytest.mark.parametrize('bad',[{'x':'1','y':2},{'x':'-1','y':True},{'x':'-1','y':'1/0'},{'x':'-1','error':'timeout'},{'x':'-1','y':0,'error':'unavailable'},{'x':-1,'y':0}])
def test_unselected_hidden_or_bad_observation_refused(bad):
 r=h.run(TASK,[bad]);assert r['status']=='HYPOTHESIS_RESEARCH_REJECTED' and r['proof'] is None

@pytest.mark.parametrize('key,value',[('degree',3),('degree',True),('budget',True),('coefficient_values',[0,0]),('coefficient_values',[False,1]),('probe_costs',{'1':1,'1.0':2}),('probe_costs',{'-1':0}),('examples',[[0,0],[0,1]]),('target_x',101)])
def test_invalid_class_bounds_and_sensor_aliases_refused(key,value):
 task=copy.deepcopy(TASK);task[key]=value;assert h.run(task)['status']=='HYPOTHESIS_RESEARCH_REJECTED'

def test_outside_class_initial_examples_are_falsified_not_answered():
 task=copy.deepcopy(TASK);task['examples']=[[0,99]];r=h.run(task)
 assert r['status']=='HYPOTHESIS_CLASS_FALSIFIED' and r['answer'] is None and check(r['proof'])

def test_events_after_goal_or_falsification_cannot_be_replayed():
 for events in ([{'x':'-1','y':999},{'x':'1','y':2}],[{'x':'-1','y':0},{'x':'1','y':2},{'x':'2','y':6}]):
  assert h.run(TASK,events)['status']=='HYPOTHESIS_RESEARCH_REJECTED'

def test_independent_check_never_calls_producer(monkeypatch):
 p=h.run(TASK,[{'x':'-1','y':0},{'x':'1','y':2}])['proof']
 def forbidden(*args,**kwargs):raise AssertionError('producer called')
 for name in ('prepare','decision','run','evaluate'):monkeypatch.setattr(h,name,forbidden)
 assert check(p)

def test_future_observation_does_not_choose_the_earlier_probe():
 for value in (-2,-1,0,1,2,999):
  r=h.run(TASK,[{'x':'-1','y':value}]);assert r['proof']['history'][0]['question']['x']=='-1' and check(r['proof'])

def test_excess_sensors_and_unknown_task_fields_are_refused():
 task=copy.deepcopy(TASK);task['probe_costs']={str(i):1 for i in range(9)}
 assert h.run(task)['status']=='HYPOTHESIS_RESEARCH_REJECTED'
 task=copy.deepcopy(TASK);task['events']=[]
 assert h.run(task)['status']=='HYPOTHESIS_RESEARCH_REJECTED'
