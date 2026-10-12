"""Independent finite candidate enumeration and backward experiment checking.

No imports from the hypothesis producer, existing induction or research code.
Structured task parsing avoids the old shared natural-language regex surface.
"""
from fractions import Fraction
import json

def q(raw):
    if type(raw) not in (str,int) or len(str(raw))>80:raise ValueError('VERIFY_HYPOTHESIS_NUMBER')
    value=Fraction(raw)
    if value.numerator.bit_length()>128 or value.denominator.bit_length()>128:raise ValueError('VERIFY_HYPOTHESIS_BITS')
    return value

def predict(c,x):
    return q(str(sum(Fraction(a)*x**i for i,a in enumerate(c))))

def read(task):
    if not isinstance(task,dict) or set(task)!={'degree','coefficient_values','examples','target_x','probe_costs','budget'}:raise ValueError('VERIFY_TASK')
    degree=task['degree'];values=task['coefficient_values']
    if type(degree) is not int or degree not in (0,1,2) or not isinstance(values,list) or not 1<=len(values)<=5:raise ValueError('VERIFY_CLASS')
    if any(type(v) is not int or not -10<=v<=10 for v in values) or len(set(values))!=len(values):raise ValueError('VERIFY_COEFFICIENTS')
    pairs=task['examples'];examples={}
    if not isinstance(pairs,list) or not 1<=len(pairs)<=16:raise ValueError('VERIFY_EXAMPLES')
    for pair in pairs:
        if not isinstance(pair,list) or len(pair)!=2:raise ValueError('VERIFY_PAIR')
        x,y=q(pair[0]),q(pair[1])
        if abs(x)>100 or x in examples:raise ValueError('VERIFY_EXAMPLE_X')
        examples[x]=y
    target=q(task['target_x'])
    if abs(target)>100 or type(task['budget']) is not int or not 0<=task['budget']<=800:raise ValueError('VERIFY_TARGET_BUDGET')
    probe_map=task['probe_costs'];probes={}
    if not isinstance(probe_map,dict) or len(probe_map)>8:raise ValueError('VERIFY_PROBES')
    for label,cost in probe_map.items():
        if not isinstance(label,str):raise ValueError('VERIFY_PROBE_LABEL')
        x=q(label)
        if abs(x)>100 or x in probes or type(cost) is not int or not 1<=cost<=100:raise ValueError('VERIFY_PROBE_COST')
        probes[x]=cost
    # Explicit nested loops, independently generated coefficient tuples.
    rows=[()]
    for index in range(degree+1):rows=[prefix+(v,) for prefix in rows for v in sorted(values)]
    models=tuple(c for c in rows if all(predict(c,x)==y for x,y in examples.items()))
    if len(models)>32:raise ValueError('VERIFY_SURVIVOR_LIMIT')
    return models,sorted(probes.items()),target,len(rows)

def decide(models,probes,target,used,budget):
    if not models:return 'HYPOTHESIS_CLASS_FALSIFIED',None,None,None
    answers={predict(c,target) for c in models}
    if len(answers)==1:return 'TARGET_AGREEMENT_WITHIN_CLASS',str(next(iter(answers))),None,0
    # Bottom-up cache by surviving model indices and available probe mask.
    memo={};visited=0
    def solve(indices,mask):
        nonlocal visited
        key=(indices,mask)
        if key in memo:return memo[key]
        visited+=1
        if visited>50000:raise ValueError('VERIFY_SEARCH_LIMIT')
        if len({predict(models[i],target) for i in indices})==1:
            memo[key]=(0,None);return memo[key]
        winner=None
        for p,(x,cost) in enumerate(probes):
            if not mask&(1<<p):continue
            outputs=sorted({predict(models[i],x) for i in indices})
            if len(outputs)==1:continue
            tail=[]
            for output in outputs:
                members=tuple(i for i in indices if predict(models[i],x)==output)
                value,_=solve(members,mask^(1<<p))
                if value is None:tail=None;break
                tail.append(value)
            if tail is None:continue
            candidate=(cost+max(tail),cost,x,p)
            if winner is None or candidate<winner:winner=candidate
        memo[key]=(None,None) if winner is None else (winner[0],winner[3]);return memo[key]
    mask=sum(1<<i for i,(x,cost) in enumerate(probes) if x not in used)
    value,probe=solve(tuple(range(len(models))),mask)
    if value is None or value>budget:return 'NO_AFFORDABLE_DISCRIMINATION',None,None,value
    x,cost=probes[probe]
    return 'AWAITING_HYPOTHESIS_OBSERVATION',None,{'x':str(x),'cost':cost,'question':'入力'+str(x)+'で出力は何？'},value

def same(a,b):
    return json.dumps(a,sort_keys=True,ensure_ascii=False,allow_nan=False)==json.dumps(b,sort_keys=True,ensure_ascii=False,allow_nan=False)

def check(packet):
    try:
        fields={'kind','task','events','history','status','answer','next_observation','spent','worst_case_remaining_cost','survivors','generated_model_count'}
        if not isinstance(packet,dict) or set(packet)!=fields or packet['kind']!='hypothesis_research':return False
        models,probes,target,generated=read(packet['task']);events=packet['events'];history=packet['history']
        if not isinstance(events,list) or len(events)>8 or not isinstance(history,list) or len(history)!=len(events):return False
        used=set();spent=0
        for event,entry in zip(events,history):
            status,answer,nxt,worst=decide(models,probes,target,used,packet['task']['budget']-spent)
            if status!='AWAITING_HYPOTHESIS_OBSERVATION':return False
            if not isinstance(event,dict) or set(event) not in ({'x','y'},{'x','error'}) or not isinstance(event['x'],str) or event['x']!=nxt['x']:return False
            before=len(models)
            if 'y' in event:
                x,y=q(event['x']),q(event['y']);models=tuple(c for c in models if predict(c,x)==y)
            elif event['error']!='unavailable':return False
            expected={'question':nxt,'event':event,'worst_case_cost_before':worst,'survivors_before':before,'survivors_after':len(models)}
            if not same(entry,expected):return False
            spent+=nxt['cost'];used.add(q(nxt['x']))
        status,answer,nxt,worst=decide(models,probes,target,used,packet['task']['budget']-spent)
        expected={'kind':'hypothesis_research','task':packet['task'],'events':events,'history':history,'status':status,'answer':answer,
                  'next_observation':nxt,'spent':spent,'worst_case_remaining_cost':worst,'survivors':[list(c) for c in models],'generated_model_count':generated}
        return same(packet,expected) and spent<=packet['task']['budget']
    except (ValueError,TypeError,KeyError,ZeroDivisionError,OverflowError):return False
