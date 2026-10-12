"""Signed bounded clarification of stated linear premises.

Conditions are supplied by the user, never guessed or fetched from a teacher.
Every answer is conditional on those premises and replayed by a separate parser.
"""
from pathlib import Path
import json,re
from . import constraints,store
from .constraints_verify import verify,verify_nonunique
from tukuyo_v977 import whole_state as whole
from tukuyo_v1019.transaction import transactional
from tukuyo_v1019.lifecycle import require_alive

NS='clarification';COMPONENT='clarification_dialogue';SCHEMA='tukuyo.clarification/1'

def needs_preflight(data):
    if (Path(data)/NS).exists():return True
    p=whole.state_path(data)
    return p.is_file() and COMPONENT in json.loads(p.read_text()).get('payload',{}).get('component_hashes',{})

def _name(name):
    if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,40}',name):raise ValueError('CLARIFICATION_SESSION_NAME')

def _checked(query):
    r=constraints.solve(query)
    if not r or 'graph' not in r:raise ValueError('CLARIFICATION_OUTSIDE_SCOPE')
    if r['reason'] not in ('CONSTRAINT_TARGET_FORCED','CONSTRAINT_UNDERDETERMINED'):
        raise ValueError('CLARIFICATION_REJECTED:'+r['reason'])
    if r['answer'] is not None:
        c=verify(query,r['answer'],r['proof'])
        if not c['supported']:raise ValueError('CLARIFICATION_VERIFY_REJECTED')
    else:
        p={'kind':'linear_nonunique','source_query':query,'graph':r['graph'],'witnesses':r['counterexamples']}
        c=verify_nonunique(query,p)
        if not c['supported']:raise ValueError('CLARIFICATION_AMBIGUITY_UNPROVEN:'+c.get('reason','REJECTED'))
        r['ambiguity_proof']=p;r['ambiguity_check']=c
    return r

def _query(query,condition):
    if not isinstance(condition,str) or not 1<=len(condition)<=512 or re.search(r'[。;；\n\r]',condition):
        raise ValueError('CLARIFICATION_ONE_CONDITION_REQUIRED')
    graph=constraints.parse(query)
    clauses=[e['source'] for e in graph['equations']]
    goal=graph['target']['expression']+'は何'+graph['unit']+'？'
    return ('' if graph['unit'] else '制約: ')+'。'.join(clauses+[condition.strip(),goal])

def _replay(s):
    if not isinstance(s,dict) or set(s)!={'initial_query','conditions','current_query','result'} or not isinstance(s['conditions'],list) or len(s['conditions'])>8:
        raise ValueError('CLARIFICATION_SESSION_SHAPE')
    q=s['initial_query'];r=_checked(q)
    for c in s['conditions']:q=_query(q,c);r=_checked(q)
    if q!=s['current_query'] or r!=s['result']:raise ValueError('CLARIFICATION_REPLAY_DRIFT')
    return r

def validate(state):
    if not isinstance(state,dict) or set(state)!={'schema','sessions'} or state.get('schema')!=SCHEMA or not isinstance(state['sessions'],dict) or len(state['sessions'])>16:
        raise ValueError('CLARIFICATION_SCHEMA')
    for name,s in state['sessions'].items():_name(name);_replay(s)

def load(data):
    if not (Path(data)/NS/'commits').exists():
        if needs_preflight(data):raise ValueError('CLARIFICATION_HISTORY_MISSING')
        return {'schema':SCHEMA,'sessions':{}}
    return store.load(data,NS,COMPONENT,validate)

def _public(name,s):
    r=s['result']
    return {'ok':True,'session':name,'answer':r['answer'],'unit':r['graph']['unit'],
            'uncertain':r['answer'] is None,'reason':r['reason'],'information_requests':r.get('information_requests',[]),
            'conditions_added':len(s['conditions']),'query':s['current_query'],'proof':r['proof'],
            'verified':r['answer'] is not None,'conditional_on_supplied_premises':True,
            'ambiguity_verified':bool(r.get('ambiguity_check',{}).get('supported')),'ambiguity_proof':r.get('ambiguity_proof'),
            'external_calls':0,'conditions_invented':False}

@transactional()
def start(data,query,name='main'):
    require_alive(data);_name(name)
    if not isinstance(query,str) or not 1<=len(query)<=5000:raise ValueError('CLARIFICATION_INPUT_BOUND')
    state=load(data)
    if name in state['sessions']:raise ValueError('CLARIFICATION_SESSION_EXISTS')
    if len(state['sessions'])>=16:raise ValueError('CLARIFICATION_SESSION_BOUND')
    s={'initial_query':query,'conditions':[],'current_query':query,'result':_checked(query)}
    state['sessions'][name]=s;validate(state);store.save(data,NS,COMPONENT,state)
    return _public(name,s)

@transactional()
def add(data,condition,name='main'):
    require_alive(data);_name(name);state=load(data)
    if name not in state['sessions']:raise ValueError('CLARIFICATION_SESSION_MISSING')
    s=state['sessions'][name]
    if len(s['conditions'])>=8:raise ValueError('CLARIFICATION_ROUND_BOUND')
    q=_query(s['current_query'],condition);r=_checked(q)
    s['conditions'].append(condition);s['current_query']=q;s['result']=r
    validate(state);store.save(data,NS,COMPONENT,state)
    return _public(name,s)

def status(data,name='main'):
    _name(name);state=load(data)
    if name not in state['sessions']:raise ValueError('CLARIFICATION_SESSION_MISSING')
    return _public(name,state['sessions'][name])

def audit(data):
    try:
        state=load(data)
        return {'ok':True,'sessions':len(state['sessions']),'answered':sum(s['result']['answer'] is not None for s in state['sessions'].values()),
                'conditional_on_supplied_premises':True,'external_calls':0}
    except (ValueError,TypeError,KeyError,OSError) as e:return {'ok':False,'errors':[str(e)]}
