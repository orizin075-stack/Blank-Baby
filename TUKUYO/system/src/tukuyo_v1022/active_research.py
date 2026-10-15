"""Finite active research over stated rational constraints and sensor abilities.

Questions are generated from declared variables, not supplied as answer-bearing
options. Every event is replayed after selecting its question from the preceding
state. Events and abilities are external inputs; no world tool is executed.
"""
import copy
from fractions import Fraction as F
from . import constraints, observation_reasoning

def _capabilities(graph, capability):
    if not isinstance(capability,dict) or set(capability)!={'budget','measurements'}:
        raise ValueError('RESEARCH_CAPABILITY_FIELDS')
    if type(capability['budget']) is not int or not 0<=capability['budget']<=800:
        raise ValueError('RESEARCH_BUDGET')
    measures=capability['measurements']
    if not isinstance(measures,dict) or len(measures)>8:
        raise ValueError('RESEARCH_MEASUREMENT_LIMIT')
    if graph['unit'] or len(graph['equations'])+len(measures)>32:
        raise ValueError('RESEARCH_RATIONAL_SCOPE_OR_STATEMENT_LIMIT')
    for name,cost in measures.items():
        if name not in graph['variables'] or type(cost) is not int or not 1<=cost<=100:
            raise ValueError('RESEARCH_UNKNOWN_SENSOR_OR_COST')
    return measures

def _query(graph, observations):
    clauses=[e['source'] for e in graph['equations']]
    clauses += [name+'='+value for name,value in observations]
    return '制約: '+'。'.join(clauses+[graph['target']['expression']+'は何？'])

def _decision(query, measures, disabled, spent, budget):
    result=constraints.solve(query)
    if result is None or result.get('graph') is None:
        raise ValueError('RESEARCH_LINEAR_PROBLEM_REQUIRED')
    if result['reason']=='CONSTRAINT_INCONSISTENT':
        return 'OBSERVATION_CONFLICT',result,None,None
    if result.get('answer') is not None:
        return 'GOAL_ESTABLISHED',result,None,None
    if result['reason']!='CONSTRAINT_UNDERDETERMINED':
        raise ValueError('RESEARCH_BASE_NOT_SUPPORTED')
    options=[{'id':name,'expression':name,'cost':cost} for name,cost in sorted(measures.items()) if name not in disabled]
    if not options:
        return 'NO_AFFORDABLE_RESEARCH',result,None,None
    planned=observation_reasoning.plan(query,{'budget':budget-spent,'options':options})
    if planned['status']=='NO_FEASIBLE_OBSERVATION_PLAN':
        return 'NO_AFFORDABLE_RESEARCH',result,None,None
    if planned['status']!='OBSERVE_THEN_REASON':
        raise ValueError('RESEARCH_PLAN_REJECTED')
    chosen=min(planned['selected_observations'],key=lambda x:(x['cost'],x['id']))
    next_observation={'variable':chosen['id'],'cost':chosen['cost'],'question':chosen['expression']+'は何？'}
    return 'AWAITING_OBSERVATION',result,planned['proof'],next_observation

def run(query, capability, events=None):
    """Stateless replay: choose, receive one event, replan, stop on proof/conflict."""
    try:
        initial=constraints.solve(query)
        if initial is None or initial.get('graph') is None or initial['reason'] not in ('CONSTRAINT_TARGET_FORCED','CONSTRAINT_UNDERDETERMINED'):
            raise ValueError('RESEARCH_CONSISTENT_LINEAR_BASE_REQUIRED')
        graph=initial['graph'];measures=_capabilities(graph,capability)
        events=[] if events is None else events
        if not isinstance(events,list) or len(events)>8:
            raise ValueError('RESEARCH_EVENT_LIMIT')
        spent=0;disabled=set();observed=[];history=[]
        for event in events:
            current=_query(graph,observed)
            status,base,proof,nxt=_decision(current,measures,disabled,spent,capability['budget'])
            if status!='AWAITING_OBSERVATION':raise ValueError('RESEARCH_EVENT_AFTER_TERMINATION')
            if not isinstance(event,dict) or set(event) not in ({'variable','value'},{'variable','error'}) or event['variable']!=nxt['variable']:
                raise ValueError('RESEARCH_EVENT_NOT_SELECTED')
            # Values are inspected only after this step's question was chosen.
            if 'value' in event:
                if type(event['value']) not in (str,int) or len(str(event['value']))>100:
                    raise ValueError('RESEARCH_OBSERVATION_VALUE')
                value=str(constraints._bounded(F(event['value'])))
                observed.append((event['variable'],value))
            elif event['error']!='unavailable':
                raise ValueError('RESEARCH_OBSERVATION_ERROR')
            spent+=nxt['cost'];disabled.add(event['variable'])
            history.append({'plan':proof,'measurement':nxt,'event':copy.deepcopy(event)})
        current=_query(graph,observed)
        status,base,proof,nxt=_decision(current,measures,disabled,spent,capability['budget'])
        packet={'kind':'active_research','source_query':str(query),'capabilities':copy.deepcopy(capability),
                'events':copy.deepcopy(events),'history':history,'current_query':current,'spent':spent,
                'status':status,'next_observation':nxt,'plan':proof,'answer':base.get('answer'),
                'answer_proof':base.get('proof'),'conflict':status=='OBSERVATION_CONFLICT'}
        from .research_verify import check
        if not check(packet):raise ValueError('RESEARCH_INDEPENDENT_REPLAY_REJECTED')
        return {'ok':True,'status':status,'answer':packet['answer'],'uncertain':packet['answer'] is None,
                'next_observation':nxt,'spent':spent,'remaining_budget':capability['budget']-spent,
                'proof':packet,'verification_evidence':{'independent_input_history_and_budget_check':True},
                'claim_boundary':{'questions_generated_from_declared_variables':True,'sensor_abilities_and_costs_external':True,
                                  'event_values_not_used_to_select_earlier_questions':True,'events_world_authenticated':False,
                                  'external_tool_execution':False,'persistent_research_memory':False}}
    except (ValueError,TypeError,KeyError,ZeroDivisionError,OverflowError) as e:
        return {'ok':True,'status':'RESEARCH_REJECTED','answer':None,'uncertain':True,'reason':str(e),'proof':None}
