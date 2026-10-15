"""Finite active polynomial hypothesis research with minimax experiment cost.

The declared coefficient class is exhaustive only inside its explicit bounds.
No assumption is made that it contains the real world. A contrary observation
falsifies the whole class and withholds the answer. No world tool is executed.
"""
import copy,itertools
from fractions import Fraction as F
from functools import lru_cache

def number(value):
    if type(value) not in (str,int) or len(str(value))>80:raise ValueError('HYPOTHESIS_NUMBER')
    v=F(value)
    if max(v.numerator.bit_length(),v.denominator.bit_length())>128:raise ValueError('HYPOTHESIS_ARITHMETIC_LIMIT')
    return v

def evaluate(coeff,x):
    y=F(0)
    for c in reversed(coeff):y=number(str(y*x+c))
    return y

def prepare(task):
    fields={'degree','coefficient_values','examples','target_x','probe_costs','budget'}
    if not isinstance(task,dict) or set(task)!=fields:raise ValueError('HYPOTHESIS_TASK_FIELDS')
    if type(task['degree']) is not int or not 0<=task['degree']<=2:raise ValueError('HYPOTHESIS_DEGREE')
    values=task['coefficient_values']
    if not isinstance(values,list) or not 1<=len(values)<=5 or any(type(v) is not int or abs(v)>10 for v in values) or len(set(values))!=len(values):raise ValueError('HYPOTHESIS_COEFFICIENT_DOMAIN')
    examples=task['examples'];pairs=[]
    if not isinstance(examples,list) or not 1<=len(examples)<=16:raise ValueError('HYPOTHESIS_EXAMPLE_LIMIT')
    for row in examples:
        if not isinstance(row,list) or len(row)!=2:raise ValueError('HYPOTHESIS_EXAMPLE')
        x,y=map(number,row)
        if abs(x)>100 or any(x==a for a,b in pairs):raise ValueError('HYPOTHESIS_DUPLICATE_OR_LARGE_INPUT')
        pairs.append((x,y))
    target=number(task['target_x'])
    if abs(target)>100:raise ValueError('HYPOTHESIS_TARGET_LIMIT')
    probes=task['probe_costs']
    if not isinstance(probes,dict) or len(probes)>8:raise ValueError('HYPOTHESIS_PROBE_LIMIT')
    parsed={}
    for raw,cost in probes.items():
        if not isinstance(raw,str):raise ValueError('HYPOTHESIS_PROBE_ID')
        x=number(raw)
        if abs(x)>100 or x in parsed or type(cost) is not int or not 1<=cost<=100:raise ValueError('HYPOTHESIS_PROBE_OR_COST')
        parsed[x]=cost
    if type(task['budget']) is not int or not 0<=task['budget']<=800:raise ValueError('HYPOTHESIS_BUDGET')
    all_models=tuple(itertools.product(sorted(values),repeat=task['degree']+1))
    models=tuple(c for c in all_models if all(evaluate(c,x)==y for x,y in pairs))
    if len(models)>32:raise ValueError('HYPOTHESIS_SURVIVOR_LIMIT')
    return models,sorted(parsed.items()),target,len(all_models)

class SearchLimit(ValueError):pass

def decision(models,probes,target,used,remaining):
    predictions={evaluate(c,target) for c in models}
    if not models:return 'HYPOTHESIS_CLASS_FALSIFIED',None,None,None,0
    if len(predictions)==1:return 'TARGET_AGREEMENT_WITHIN_CLASS',next(iter(predictions)),None,0,0
    available=tuple(i for i,(x,cost) in enumerate(probes) if x not in used);count=0
    @lru_cache(None)
    def cost(cs,available):
        nonlocal count
        count+=1
        if count>50000:raise SearchLimit('HYPOTHESIS_SEARCH_LIMIT')
        if len({evaluate(c,target) for c in cs})==1:return (0,None)
        best=None
        for i in available:
            x,immediate=probes[i];groups={}
            for c in cs:groups.setdefault(evaluate(c,x),[]).append(c)
            if len(groups)<2:continue
            rest=tuple(j for j in available if j!=i);continuations=[cost(tuple(g),rest)[0] for g in groups.values()]
            if any(v is None for v in continuations):continue
            worst=immediate+max(continuations);key=(worst,immediate,x)
            if best is None or key<best[0]:best=(key,i)
        return (None,None) if best is None else (best[0][0],best[1])
    optimal,index=cost(models,available)
    if optimal is None or optimal>remaining:return 'NO_AFFORDABLE_DISCRIMINATION',None,None,optimal,count
    x,price=probes[index]
    return 'AWAITING_HYPOTHESIS_OBSERVATION',None,{'x':str(x),'cost':price,'question':'入力'+str(x)+'で出力は何？'},optimal,count

def run(task,events=None):
    try:
        models,probes,target,generated=prepare(task);events=[] if events is None else events
        if not isinstance(events,list) or len(events)>8:raise ValueError('HYPOTHESIS_EVENT_LIMIT')
        used=set();spent=0;history=[]
        for event in events:
            status,answer,nxt,worst,states=decision(models,probes,target,used,task['budget']-spent)
            if status!='AWAITING_HYPOTHESIS_OBSERVATION':raise ValueError('HYPOTHESIS_EVENT_AFTER_TERMINATION')
            if not isinstance(event,dict) or set(event) not in ({'x','y'},{'x','error'}) or not isinstance(event['x'],str) or event['x']!=nxt['x']:raise ValueError('HYPOTHESIS_UNSELECTED_EVENT')
            before=len(models)
            if 'y' in event:
                y=number(event['y']);x=number(event['x']);models=tuple(c for c in models if evaluate(c,x)==y)
            elif event['error']!='unavailable':raise ValueError('HYPOTHESIS_EVENT_ERROR')
            history.append({'question':nxt,'event':copy.deepcopy(event),'worst_case_cost_before':worst,'survivors_before':before,'survivors_after':len(models)})
            spent+=nxt['cost'];used.add(number(nxt['x']))
        status,answer,nxt,worst,states=decision(models,probes,target,used,task['budget']-spent)
        packet={'kind':'hypothesis_research','task':copy.deepcopy(task),'events':copy.deepcopy(events),'history':history,
                'status':status,'answer':str(answer) if answer is not None else None,'next_observation':nxt,'spent':spent,
                'worst_case_remaining_cost':worst,'survivors':[list(c) for c in models],'generated_model_count':generated}
        from .hypothesis_research_verify import check
        if not check(packet):raise ValueError('HYPOTHESIS_RESEARCH_VERIFY_REJECTED')
        return {'ok':True,'status':status,'answer':packet['answer'],'uncertain':answer is None,'next_observation':nxt,'spent':spent,
                'remaining_budget':task['budget']-spent,'survivor_count':len(models),'worst_case_remaining_cost':worst,
                'proof':packet,'verification_evidence':{'independent_candidate_history_and_minimax_check':True,'exact_search_complete':True},
                'claim_boundary':{'explicit_finite_polynomial_class':True,'world_membership_in_class_proven':False,'observation_values_external':True,
                                  'future_probe_unavailability_in_optimization':False,'external_tool_execution':False,'persistent_research_memory':False}}
    except (ValueError,TypeError,KeyError,ZeroDivisionError,OverflowError) as e:
        return {'ok':True,'status':'HYPOTHESIS_RESEARCH_REJECTED','answer':None,'uncertain':True,'reason':str(e),'proof':None}
