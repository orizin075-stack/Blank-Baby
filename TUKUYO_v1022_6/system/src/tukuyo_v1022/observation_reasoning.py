"""Choose a bounded minimum-cost set of observations that forces the goal.

Observation values are absent during planning. Only declared expressions and
costs are available. No external tool is executed or hidden answer read.
"""
import copy,itertools
from fractions import Fraction as F
from . import constraints

def _forced(rows,target):
    basis=[]
    for original in rows:
        row=list(original)
        for col,b in basis:
            f=row[col];row=[constraints._bounded(a-f*x) for a,x in zip(row,b)]
        col=next((i for i,x in enumerate(row) if x),None)
        if col is not None:
            f=row[col];basis.append((col,[constraints._bounded(x/f) for x in row]))
    remainder=list(target)
    for col,b in basis:
        f=remainder[col];remainder=[constraints._bounded(a-f*x) for a,x in zip(remainder,b)]
    return not any(remainder)

def prepare(query,task):
    result=constraints.solve(query)
    if result is None:raise ValueError('OBSERVATION_LINEAR_PROBLEM_REQUIRED')
    graph=result.get('graph')
    if graph is None or result.get('reason') not in ('CONSTRAINT_TARGET_FORCED','CONSTRAINT_UNDERDETERMINED'):raise ValueError('OBSERVATION_BASE_NOT_CONSISTENT')
    if graph['unit']:raise ValueError('OBSERVATION_RATIONAL_SCOPE_ONLY')
    if not isinstance(task,dict) or set(task)!={'budget','options'} or type(task['budget']) is not int or not 0<=task['budget']<=800:raise ValueError('OBSERVATION_TASK')
    options=task['options']
    if not isinstance(options,list) or not 1<=len(options)<=8:raise ValueError('OBSERVATION_OPTION_LIMIT')
    names=graph['variables'];rows=[[F(e['coefficients'].get(k,0)) for k in names] for e in graph['equations']];target=[F(graph['target']['coefficients'].get(k,0)) for k in names]
    parsed=[];ids=set()
    for option in options:
        if not isinstance(option,dict) or set(option)!={'id','expression','cost'}:raise ValueError('OBSERVATION_OPTION_FIELDS')
        if not isinstance(option['id'],str) or not 1<=len(option['id'])<=64 or option['id'] in ids:raise ValueError('OBSERVATION_DUPLICATE_ID')
        if type(option['cost']) is not int or not 1<=option['cost']<=100:raise ValueError('OBSERVATION_COST')
        if not isinstance(option['expression'],str):raise ValueError('OBSERVATION_EXPRESSION')
        expr,symbols=constraints._affine(option['expression'])
        if not symbols<=set(names):raise ValueError('OBSERVATION_UNKNOWN_VARIABLE')
        ids.add(option['id']);parsed.append((option,[expr[1].get(k,F(0)) for k in names]))
    return result,rows,target,parsed

def plan(query,task):
    try:
        base,rows,target,parsed=prepare(query,task);best=None;examined=0
        for mask in range(1<<len(parsed)):
            examined+=1;selected=[i for i in range(len(parsed)) if mask>>i&1];cost=sum(parsed[i][0]['cost'] for i in selected)
            if cost>task['budget']:continue
            ids=sorted(parsed[i][0]['id'] for i in selected);key=(cost,len(ids),ids)
            if best is not None and key>=best[0]:continue
            if _forced(rows+[parsed[i][1] for i in selected],target):best=(key,ids)
        if best is None:return {'ok':True,'status':'NO_FEASIBLE_OBSERVATION_PLAN','answer':None,'uncertain':True,'search_complete':True,'candidates_examined':examined}
        proof={'kind':'observation_plan','source_query':str(query),'task':copy.deepcopy(task),'selected':best[1],'total_cost':best[0][0],'search_complete':True,'candidates_examined':examined}
        from .observation_verify import check
        if not check(proof):raise ValueError('OBSERVATION_SECONDARY_CHECK_REJECTED')
        selected=[copy.deepcopy(x) for x,v in parsed if x['id'] in best[1]]
        return {'ok':True,'status':'OBSERVE_THEN_REASON' if selected else 'ALREADY_KNOWN','answer':base.get('answer') if not selected else None,
                'uncertain':bool(selected),'selected_observations':selected,'total_cost':best[0][0],'proof':proof,'search_complete':True,
                'candidates_examined':examined,'verification_evidence':{'independent_input_and_plan_check':True,'bounded_minimum_cost':True},
                'claim_boundary':{'available_options_supplied_externally':True,'observation_values_seen_during_planning':False,'external_tool_execution':False}}
    except (ValueError,TypeError,KeyError,ZeroDivisionError,OverflowError) as e:
        return {'ok':True,'status':'OBSERVATION_PLAN_REJECTED','answer':None,'uncertain':True,'reason':str(e),'search_complete':False,'proof':None}

def update(proof,observations):
    """Apply exactly the chosen supplied observations, then reprove the goal."""
    from .observation_verify import check
    if not check(proof):raise ValueError('OBSERVATION_PLAN_PROOF_REJECTED')
    if not isinstance(observations,dict) or set(observations)!=set(proof['selected']):raise ValueError('OBSERVATION_BINDING')
    graph=constraints.parse(proof['source_query']);options={x['id']:x for x in proof['task']['options']};clauses=[e['source'] for e in graph['equations']]
    for ident in proof['selected']:
        value=observations[ident]
        if type(value) not in (str,int) or len(str(value))>100:raise ValueError('OBSERVATION_VALUE')
        value=constraints._bounded(F(value));clauses.append('('+options[ident]['expression']+')='+str(value))
    q='制約: '+'。'.join(clauses+[graph['target']['expression']+'は何？']);result=constraints.solve(q)
    if result.get('answer') is not None:
        from .constraints_verify import verify
        if not verify(q,result['answer'],result['proof'])['supported']:raise ValueError('OBSERVATION_UPDATE_VERIFY_REJECTED')
    return {**result,'ok':True,'uncertain':result.get('answer') is None,'observation_provenance':{'original_query':proof['source_query'],'selected':proof['selected'],'values':{k:str(F(v)) for k,v in observations.items()},'observations_externally_supplied_not_world_authenticated':True}}
