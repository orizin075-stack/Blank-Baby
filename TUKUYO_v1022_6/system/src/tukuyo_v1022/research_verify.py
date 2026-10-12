"""Independent chronological research replay; never calls the producer.

Separate input parser, homogeneous null-space decisions and certificate checks.
Checks consistency with supplied events, not their truth about the real world.
"""
from fractions import Fraction as F
from .constraints_verify import read, _q, verify
from .observation_verify import _determined, check as check_plan

def _state(query, measurements, disabled, remaining):
    g=read(query)
    if g is None or g['unit']:raise ValueError('VERIFY_RESEARCH_INPUT')
    names=g['variables']
    rows=[[F(e['coefficients'].get(v,0)) for v in names] for e in g['equations']]
    augmented=[row+[F(e['rhs'])] for row,e in zip(rows,g['equations'])]
    if _determined(augmented,[F(0)]*len(names)+[F(1)]):return 'OBSERVATION_CONFLICT',None,None
    goal=[F(g['target']['coefficients'].get(v,0)) for v in names]
    if _determined(rows,goal):return 'GOAL_ESTABLISHED',None,None
    options=[{'id':v,'expression':v,'cost':c} for v,c in sorted(measurements.items()) if v not in disabled]
    best=None
    for mask in range(1<<len(options)):
        chosen=[o for i,o in enumerate(options) if mask>>i&1]
        cost=sum(o['cost'] for o in chosen)
        if cost>remaining:continue
        key=(cost,len(chosen),sorted(o['id'] for o in chosen))
        if best is not None and key>=best[0]:continue
        extra=[[F(int(v==o['id'])) for v in names] for o in chosen]
        if _determined(rows+extra,goal):best=(key,chosen)
    if best is None:return 'NO_AFFORDABLE_RESEARCH',None,None
    selected=min(best[1],key=lambda o:(o['cost'],o['id']))
    nxt={'variable':selected['id'],'cost':selected['cost'],'question':selected['expression']+'は何？'}
    task={'budget':remaining,'options':options}
    return 'AWAITING_OBSERVATION',nxt,task

def check(packet):
    try:
        fields={'kind','source_query','capabilities','events','history','current_query','spent','status','next_observation','plan','answer','answer_proof','conflict'}
        if not isinstance(packet,dict) or set(packet)!=fields or packet['kind']!='active_research':return False
        graph=read(packet['source_query'])
        if graph is None or graph['unit']:return False
        cap=packet['capabilities']
        if not isinstance(cap,dict) or set(cap)!={'budget','measurements'} or type(cap['budget']) is not int or not 0<=cap['budget']<=800:return False
        measurements=cap['measurements']
        if not isinstance(measurements,dict) or len(measurements)>8 or len(graph['equations'])+len(measurements)>32:return False
        for name,cost in measurements.items():
            if name not in graph['variables'] or type(cost) is not int or not 1<=cost<=100:return False
        events=packet['events'];history=packet['history']
        if not isinstance(events,list) or len(events)>8 or not isinstance(history,list) or len(history)!=len(events):return False
        clauses=[e['source'] for e in graph['equations']];goal=graph['target']['expression']+'は何？';spent=0;disabled=set()
        def current():return '制約: '+'。'.join(clauses+[goal])
        if _state(current(),measurements,disabled,cap['budget'])[0]=='OBSERVATION_CONFLICT':return False
        def plan_ok(proof,query,task):
            return isinstance(proof,dict) and proof.get('source_query')==query and proof.get('task')==task and check_plan(proof)
        for event,step in zip(events,history):
            status,nxt,task=_state(current(),measurements,disabled,cap['budget']-spent)
            if status!='AWAITING_OBSERVATION' or not isinstance(step,dict) or set(step)!={'plan','measurement','event'}:return False
            if step['measurement']!=nxt or step['event']!=event or not plan_ok(step['plan'],current(),task):return False
            if not isinstance(event,dict) or set(event) not in ({'variable','value'},{'variable','error'}) or event['variable']!=nxt['variable']:return False
            if 'value' in event:
                if type(event['value']) not in (str,int):return False
                clauses.append(event['variable']+'='+str(_q(event['value'])))
            elif event['error']!='unavailable':return False
            spent+=nxt['cost'];disabled.add(event['variable'])
        status,nxt,task=_state(current(),measurements,disabled,cap['budget']-spent)
        if type(packet['spent']) is not int or packet['spent']!=spent or spent>cap['budget'] or packet['current_query']!=current():return False
        if packet['status']!=status or packet['next_observation']!=nxt or type(packet['conflict']) is not bool or packet['conflict']!=(status=='OBSERVATION_CONFLICT'):return False
        if status=='AWAITING_OBSERVATION':
            if not plan_ok(packet['plan'],current(),task):return False
        elif packet['plan'] is not None:return False
        if status=='GOAL_ESTABLISHED':
            if not isinstance(packet['answer'],str) or not isinstance(packet['answer_proof'],dict):return False
            if not verify(current(),packet['answer'],packet['answer_proof'])['supported']:return False
        elif packet['answer'] is not None or packet['answer_proof'] is not None:return False
        return True
    except (ValueError,TypeError,KeyError,ZeroDivisionError,OverflowError):return False
