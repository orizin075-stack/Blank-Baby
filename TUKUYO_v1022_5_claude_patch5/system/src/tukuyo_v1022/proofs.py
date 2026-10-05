"""Proof checking does not call the natural language answer generator.

Formal proofs check the stated premises; translation correctness additionally
requires the bounded language coverage guards and external test cases.
"""
import ast,heapq,json,math
from fractions import Fraction

def calculate(expr):
    if len(expr)>200:raise ValueError('EXPRESSION_LIMIT')
    def rec(n,d=0):
        if d>20:raise ValueError('EXPRESSION_DEPTH')
        if isinstance(n,ast.Expression):return rec(n.body,d+1)
        if isinstance(n,ast.Constant) and type(n.value) in (int,float):
            if not math.isfinite(float(n.value)) or abs(n.value)>10**12:raise ValueError('NUMBER_LIMIT')
            return Fraction(str(n.value))
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.UAdd,ast.USub)):
            v=rec(n.operand,d+1);return -v if isinstance(n.op,ast.USub) else v
        if isinstance(n,ast.BinOp):
            a=rec(n.left,d+1);b=rec(n.right,d+1)
            if isinstance(n.op,ast.Add):v=a+b
            elif isinstance(n.op,ast.Sub):v=a-b
            elif isinstance(n.op,ast.Mult):v=a*b
            elif isinstance(n.op,ast.Div):v=a/b
            elif isinstance(n.op,ast.Pow) and b.denominator==1 and abs(b)<=8:v=a**int(b)
            else:raise ValueError('OPERATOR_UNSUPPORTED')
            if max(v.numerator.bit_length(),v.denominator.bit_length())>160:raise ValueError('RESULT_LIMIT')
            return v
        raise ValueError('AST_REJECTED')
    return rec(ast.parse(expr,mode='eval'))
def calculate_env(expr,env):
    if len(expr)>240:raise ValueError('EXPRESSION_LIMIT')
    if not isinstance(env,dict) or len(env)>64:raise ValueError('ENV_LIMIT')
    vals={str(k):Fraction(str(v)) for k,v in env.items()}
    def rec(n,d=0):
        if d>20:raise ValueError('EXPRESSION_DEPTH')
        if isinstance(n,ast.Expression):return rec(n.body,d+1)
        if isinstance(n,ast.Constant) and type(n.value) in (int,float):
            if not math.isfinite(float(n.value)) or abs(n.value)>10**12:raise ValueError('NUMBER_LIMIT')
            return Fraction(str(n.value))
        if isinstance(n,ast.Name):
            if n.id not in vals:raise ValueError('UNBOUND_NAME')
            return vals[n.id]
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.UAdd,ast.USub)):
            v=rec(n.operand,d+1);return -v if isinstance(n.op,ast.USub) else v
        if isinstance(n,ast.BinOp):
            a=rec(n.left,d+1);b=rec(n.right,d+1)
            if isinstance(n.op,ast.Add):v=a+b
            elif isinstance(n.op,ast.Sub):v=a-b
            elif isinstance(n.op,ast.Mult):v=a*b
            elif isinstance(n.op,ast.Div):v=a/b
            elif isinstance(n.op,ast.Pow) and b.denominator==1 and abs(b)<=6:v=a**int(b)
            else:raise ValueError('OPERATOR_UNSUPPORTED')
            if max(v.numerator.bit_length(),v.denominator.bit_length())>160:raise ValueError('RESULT_LIMIT')
            return v
        raise ValueError('AST_REJECTED')
    return rec(ast.parse(expr,mode='eval'))

def number(v):
    v=Fraction(v);return str(v.numerator) if v.denominator==1 else format(float(v),'.12g')
def validate_task(t):
    if not isinstance(t,dict) or set(t)!={'initial','goal','actions'}:raise ValueError('PLAN_FIELDS')
    ini=t['initial'];goal=t['goal'];acts=t['actions']
    if not isinstance(ini,dict) or not 1<=len(ini)<=12 or not isinstance(goal,dict) or not set(goal)<=set(ini):raise ValueError('PLAN_STATE')
    if any(not isinstance(k,str) or type(v) not in (str,int,bool) or type(v) is int and not 0<=v<=100 for k,v in ini.items()):raise ValueError('PLAN_TYPES')
    if any(type(v) is not type(ini[k]) for k,v in goal.items()):raise ValueError('GOAL_TYPES')
    if not isinstance(acts,list) or not 1<=len(acts)<=24:raise ValueError('PLAN_ACTIONS')
    ids=[]
    for a in acts:
        if not isinstance(a,dict) or set(a)-{'id','pre','set','delta','cost'} or not {'id','cost'}<=set(a):raise ValueError('ACTION_FIELDS')
        if not isinstance(a['id'],str) or not a['id'] or len(a['id'])>100 or type(a['cost']) is not int or not 1<=a['cost']<=100:raise ValueError('ACTION_COST')
        ids.append(a['id'])
        for f in ('pre','set','delta'):
            if not isinstance(a.get(f,{}),dict) or not set(a.get(f,{}))<=set(ini):raise ValueError('ACTION_KEYS')
        for k,v in a.get('pre',{}).items():
            if type(v) is not type(ini[k]):raise ValueError('ACTION_PRE_TYPE')
        for k,v in a.get('set',{}).items():
            if type(v) is not type(ini[k]):raise ValueError('ACTION_SET_TYPE')
        for k,v in a.get('delta',{}).items():
            if type(ini[k]) is not int or type(v) is not int or abs(v)>100:raise ValueError('ACTION_DELTA')
    if len(ids)!=len(set(ids)):raise ValueError('ACTION_DUPLICATE')
def transition(s,a):
    if any(s[k]!=v for k,v in a.get('pre',{}).items()):return None
    q=dict(s);q.update(a.get('set',{}))
    for k,v in a.get('delta',{}).items():
        q[k]+=v
        if not 0<=q[k]<=100:return None
    return q
def plan(t,max_nodes=4096):
    validate_task(t);key=lambda s:json.dumps(s,sort_keys=True,ensure_ascii=False)
    # v1022.1: bounded Dijkstra with a Pareto frontier over (cost, depth).
    # With a hard 24-action horizon, a cheaper but deeper arrival at the same
    # state does NOT dominate a costlier shallow arrival: the latter may still
    # have enough remaining steps to reach the goal.  Keep only labels that are
    # non-dominated in both dimensions.
    ini=t['initial'];ik=key(ini);queue=[(0,0,(),ik,ini)];frontier={ik:[(0,0)]};expanded=0
    def dominated(labels,c,d,strict=False):
        return any(lc<=c and ld<=d and (not strict or lc<c or ld<d) for lc,ld in labels)
    while queue and expanded<max_nodes:
        cost,depth,route,k,s=heapq.heappop(queue)
        labels=frontier.get(k,[])
        if (cost,depth) not in labels:continue
        expanded+=1
        if all(s[x]==v for x,v in t['goal'].items()):return {'route':list(route),'cost':cost,'final':s,'expanded':expanded,'optimal':True}
        if depth>=24:continue
        for a in t['actions']:
            q=transition(s,a)
            if q is None:continue
            nk=key(q);nc=cost+a['cost'];nd=depth+1;labels=frontier.setdefault(nk,[])
            if dominated(labels,nc,nd):continue
            labels[:]=[(lc,ld) for lc,ld in labels if not (nc<=lc and nd<=ld and (nc<lc or nd<ld))]
            labels.append((nc,nd));heapq.heappush(queue,(nc,nd,route+(a['id'],),nk,q))
    return {'route':None,'cost':None,'expanded':expanded,'optimal':False,'reason':'SEARCH_LIMIT' if queue else 'UNREACHABLE'}

def alternative_plans(t,limit=4):
    """Return the optimal plan plus bounded single-action-failure alternatives.

    This is not a full contingent planner.  It asks a useful counterfactual:
    if one action on the best route becomes unavailable, is there a verified
    fallback?  Every returned route is independently replayable by check_plan.
    """
    if type(limit) is not int or not 1<=limit<=8:raise ValueError('PLAN_ALTERNATIVE_LIMIT')
    base=plan(t);rows=[];seen=set()
    def add(p,blocked=None):
        if p.get('route') is None or not check_plan({**t,'actions':[a for a in t['actions'] if a['id']!=blocked]} if blocked else t,p):return
        k=tuple(p['route'])
        if k not in seen:
            seen.add(k);rows.append({'route':p['route'],'cost':p['cost'],'final':p['final'],'blocked_action':blocked})
    add(base)
    if base.get('route'):
        for aid in base['route']:
            tt={**t,'actions':[a for a in t['actions'] if a['id']!=aid]}
            if not tt['actions']:continue
            try:q=plan(tt)
            except ValueError:continue
            add(q,aid)
    rows.sort(key=lambda r:(r['cost'],len(r['route']),r['route']))
    return rows[:limit]

def replan(t,observed_state,unavailable_actions=None,max_nodes=4096):
    """Re-plan from an observed state after bounded execution failure/change."""
    validate_task(t)
    if not isinstance(observed_state,dict) or set(observed_state)!=set(t['initial']):raise ValueError('REPLAN_OBSERVED_STATE')
    for k,v in observed_state.items():
        if type(v) is not type(t['initial'][k]):raise ValueError('REPLAN_OBSERVED_TYPE')
    blocked=set(unavailable_actions or [])
    if any(not isinstance(x,str) for x in blocked):raise ValueError('REPLAN_BLOCKED_ACTION')
    known={a['id'] for a in t['actions']}
    if not blocked<=known:raise ValueError('REPLAN_UNKNOWN_ACTION')
    nt={'initial':dict(observed_state),'goal':dict(t['goal']),'actions':[a for a in t['actions'] if a['id'] not in blocked]}
    if not nt['actions']:
        return {'route':None,'cost':None,'expanded':0,'optimal':False,'reason':'NO_AVAILABLE_ACTIONS','replanned':True,'blocked_actions':sorted(blocked)}
    q=plan(nt,max_nodes=max_nodes);q={**q,'replanned':True,'blocked_actions':sorted(blocked),'observed_state':dict(observed_state)}
    return q

def check_plan(t,p):
    validate_task(t);s=dict(t['initial']);cost=0;actions={a['id']:a for a in t['actions']}
    for aid in p.get('route') or []:
        if aid not in actions:return False
        s=transition(s,actions[aid]);cost+=actions[aid]['cost']
        if s is None:return False
    return p.get('route') is not None and cost==p.get('cost') and s==p.get('final') and all(s[k]==v for k,v in t['goal'].items())

def assess_plan_robustness(t):
    """Bounded self-critique of the chosen route under one-action failures."""
    base=plan(t)
    route=base.get('route')
    if route is None:
        return {'ok':False,'base':base,'contingencies':[],'single_action_survival':0.0}
    rows=[];viable=0;extras=[]
    for aid in route:
        rp=replan(t,t.get('initial',{}),[aid])
        good=rp.get('route') is not None and check_plan({**t,'actions':[a for a in t.get('actions',[]) if str(a.get('id'))!=str(aid)]},rp)
        if good:
            viable+=1;extras.append(float(rp['cost'])-float(base['cost']))
        rows.append({'failed_action':aid,'viable':bool(good),'replan':rp})
    denom=max(1,len(route))
    return {'ok':True,'base':base,'contingencies':rows,'single_action_survival':round(viable/denom,6),
            'worst_extra_cost':max(extras) if extras else None,'all_single_action_failures_survivable':viable==len(route)}

def check(p,answer):
    try:
        if p['kind']=='arithmetic':
            if p.get('schema'):
                from .wordprob import solve as parse_word_problem
                source=p.get('source_query')
                if not isinstance(source,str):return False
                replay=parse_word_problem(source)
                if not replay or replay.get('refused') or any(replay.get(k)!=p.get(k) for k in ('expression','schema','unit')):return False
            return number(calculate(p['expression']))==str(answer)
        if p['kind']=='inventory':
            n=p['initial'];per=p.get('per',1)
            if type(n) is not int or n<0 or type(per) is not int or per<1:return False
            for e in p['events']:
                if type(e['quantity']) is not int or e['quantity']<0 or e['direction'] not in (-1,0,1) or e['factor'] not in (1,per):return False
                n+=e['quantity']*e['direction']*e['factor']
                if n<0:return False
            return str(n)==str(answer)
        if p['kind']=='logic':
            known=set(p['premises']);rules=[tuple(x) for x in p['rules']]
            for a,b in p['steps']:
                if a not in known or (a,b) not in rules:return False
                known.add(b)
            return p['conclusion'] in known and p['answer']==str(answer)
        if p['kind']=='plan':return check_plan(p['task'],p['plan']) and json.dumps(p['plan']['route'],ensure_ascii=False)==str(answer)
        if p['kind']=='plan_cost':return check_plan(p['task'],p['plan']) and str(p['plan']['cost'])==str(answer)
        if p['kind']=='memory':return bool(p['facts']) and len({f['value'] for f in p['facts']})==1 and str(answer)==str(p['facts'][0]['value'])
        if p['kind']=='hypothesis':
            examples=p.get('examples');model=p.get('model') or {};coeff=model.get('coefficients');tx=p.get('target_x')
            if not isinstance(examples,list) or not 2<=len(examples)<=16 or not isinstance(coeff,list) or len(coeff)!=3:return False
            c=[calculate(str(x)) for x in coeff];target=calculate(str(tx))
            def ev(x):return c[0]+c[1]*x+c[2]*x*x
            for row in examples:
                if not isinstance(row,list) or len(row)!=2:return False
                x=calculate(str(row[0]));y=calculate(str(row[1]))
                if ev(x)!=y:return False
            return number(ev(target))==str(answer)==str(p.get('answer')) and p.get('candidate_count')==1
        if p['kind']=='meta_derivation':
            steps=p.get('steps');target=p.get('target')
            if not isinstance(steps,list) or not 1<=len(steps)<=64 or not isinstance(target,str) or not target:return False
            env={};seen=set()
            for st in steps:
                if not isinstance(st,dict) or set(st)!={'variable','definition','expression','dependencies','value'}:return False
                var=st['variable'];deps=st['dependencies']
                if not isinstance(var,str) or not var or var in seen or not isinstance(deps,list):return False
                if any(not isinstance(x,str) or x not in env for x in deps):return False
                val=number(calculate_env(st['expression'],env))
                if val!=str(st['value']):return False
                env[var]=Fraction(str(st['value']));seen.add(var)
            return target in env and number(env[target])==str(answer)==str(p.get('answer'))
        if p['kind']=='deliberation':
            steps=p.get('steps')
            if not isinstance(steps,list) or not steps or len(steps)>64:return False
            for st in steps:
                if not isinstance(st,dict) or set(st)!={'label','expression','value'}:return False
                if not isinstance(st['label'],str) or not st['label'] or len(st['label'])>80:return False
                if number(calculate(st['expression']))!=str(st['value']):return False
            return str(steps[-1]['value'])==str(answer)==str(p.get('answer'))
        if p['kind'] in ('logic_models','order'):
            from .logic2 import check as check_logic
            return check_logic(p,str(answer))
        if p['kind']=='qtime':
            from .qtime import check as _check_qtime
            return _check_qtime(p,str(answer))
        if p['kind']=='knowledge':
            from .kqa import check as check_knowledge
            return check_knowledge(p,answer)
    except (ValueError,TypeError,KeyError,IndexError,ZeroDivisionError,OverflowError):return False
    return False
