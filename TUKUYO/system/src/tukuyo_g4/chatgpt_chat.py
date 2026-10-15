"""Signed, bounded teacher conversations. Dialogue is not verified knowledge.

Reserve a request before network I/O. Interrupted requests consume their slot;
they are not replayed automatically. This is a request bound, not a dollar cap.
"""
from pathlib import Path
import copy,json,re,secrets,hashlib
from . import llm
from tukuyo_v977 import whole_state as whole
from tukuyo_v1019.transaction import transactional
from tukuyo_v1019.lifecycle import require_alive
from tukuyo_v1022 import store

NS='chatgpt_chat';COMPONENT='chatgpt_dialogue';SCHEMA='tukuyo.chatgpt.dialogue/1'
SYSTEM='You are a teacher speaking with TUKUYO. Help clarify its question, assumptions, and next test. Be concise. Your reply is not independently verified knowledge. Do not claim to change TUKUYO code or its identity.'

def needs_preflight(data):
    if (Path(data)/NS).exists():return True
    p=whole.state_path(data)
    return p.is_file() and COMPONENT in json.loads(p.read_text()).get('payload',{}).get('component_hashes',{})

def validate(state):
    if state.get('schema')!=SCHEMA or not isinstance(state.get('sessions'),dict):raise ValueError('CHATGPT_DIALOGUE_SCHEMA')
    pauses=state.get('paused_routes',{})
    if not isinstance(pauses,dict) or any(k not in ('api','plan') or not isinstance(v,dict) for k,v in pauses.items()):raise ValueError('CHATGPT_PAUSE_STATE')
    for name,s in state['sessions'].items():
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,40}',name):raise ValueError('CHATGPT_SESSION_NAME')
        if type(s['max_calls']) is not int or type(s['requests']) is not int or not 1<=s['max_calls']<=64 or not 0<=s['requests']<=s['max_calls']:raise ValueError('CHATGPT_REQUEST_BOUND')
        if len(s['turns'])>s['requests']:raise ValueError('CHATGPT_TURN_CHAIN')
        for t in s['turns']:
            if t['verified'] is not False:raise ValueError('CHATGPT_DIALOGUE_IS_UNVERIFIED')
        c=s.get('connection')
        if c is not None and (not isinstance(c,dict) or c.get('auth_mode') not in ('api','plan') or not isinstance(c.get('base_url'),str)):
            raise ValueError('CHATGPT_CONNECTION_BINDING')

def load(data):
    if not (Path(data)/NS/'commits').exists():
        if needs_preflight(data):raise ValueError('CHATGPT_DIALOGUE_HISTORY_MISSING')
        return {'schema':SCHEMA,'sessions':{}}
    return store.load(data,NS,COMPONENT,validate)

def audit(data):
    try:
        s=load(data);return {'ok':True,'sessions':len(s['sessions']),'requests':sum(x['requests'] for x in s['sessions'].values()),
                            'pending_requests':sum(bool(x.get('pending')) for x in s['sessions'].values()),
                            'pending':[{'session':name,'nonce':x['pending']['nonce'],'query_sha256':hashlib.sha256(x['pending']['query'].encode()).hexdigest()}
                                       for name,x in s['sessions'].items() if x.get('pending')],
                            'paused_routes':s.get('paused_routes',{}),'dialogue_is_verified_knowledge':False}
    except (ValueError,OSError) as e:return {'ok':False,'errors':[str(e)]}

@transactional()
def reserve(data,name,query,max_calls,connection=None,context_turns=16,context_chars=48000):
    require_alive(data)
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,40}',name):raise ValueError('CHATGPT_SESSION_NAME')
    if type(max_calls) is not int or not 1<=max_calls<=64 or not isinstance(query,str) or not 1<=len(query)<=8000:raise ValueError('CHATGPT_INPUT_BOUND')
    if type(context_turns) is not int or not 1<=context_turns<=32 or type(context_chars) is not int or not 1024<=context_chars<=65536:
        raise ValueError('CHATGPT_CONTEXT_BOUND')
    if len(json.dumps([{'role':'user','content':query}],ensure_ascii=False))>context_chars:raise ValueError('CHATGPT_CONTEXT_QUERY_BOUND')
    state=load(data)
    if connection is not None and connection['auth_mode'] in state.get('paused_routes',{}):raise ValueError('CHATGPT_ROUTE_PAUSED:'+connection['auth_mode'])
    if name not in state['sessions'] and len(state['sessions'])>=32:raise ValueError('CHATGPT_SESSION_BOUND')
    s=state['sessions'].setdefault(name,{'max_calls':max_calls,'requests':0,'turns':[],'pending':None})
    if s['pending']:raise ValueError('CHATGPT_PENDING_REQUEST_NOT_RETRIED')
    if s['requests']>=s['max_calls']:raise ValueError('CHATGPT_SESSION_REQUEST_LIMIT')
    if connection is not None:
        if s.get('connection') is not None and s['connection']!=connection:raise ValueError('CHATGPT_SESSION_CONNECTION_CHANGED')
        if s.get('connection') is None:s['connection']=connection;s['legacy_history_unbound']=bool(s['turns'])
    nonce=secrets.token_hex(16);s['requests']+=1;s['pending']={'nonce':nonce,'query':query}
    history=[]
    successes=[t for t in s['turns'] if t['ok']]
    for t in successes[-context_turns:]:
        history.extend([{'role':'user','content':t['query']},{'role':'assistant','content':t['answer']}])
    history.append({'role':'user','content':query})
    while len(history)>1 and len(json.dumps(history,ensure_ascii=False))>context_chars:history=history[2:]
    context={'included_turns':(len(history)-1)//2,'omitted_successful_turns':len(successes)-(len(history)-1)//2,
             'character_budget':context_chars,'serialized_characters':len(json.dumps(history,ensure_ascii=False))}
    s['pending']['context']=context
    validate(state);store.save(data,NS,COMPONENT,state)
    return {'nonce':nonce,'history':history,'connection':connection,'context':context}

@transactional()
def finish(data,name,nonce,reply):
    require_alive(data);state=load(data);s=state['sessions'][name]
    if not s.get('pending') or s['pending']['nonce']!=nonce:raise ValueError('CHATGPT_REQUEST_BINDING')
    t={'query':s['pending']['query'],'ok':bool(reply.get('ok')),'answer':reply.get('text') if reply.get('ok') else None,
       'reason':reply.get('reason'),'model':reply.get('model'),'response_id':reply.get('request_id'),
       'usage':reply.get('usage'),'replayed':bool(reply.get('replayed')),'verified':False}
    t.update(context=s['pending'].get('context'),transport=reply.get('transport'),recovery=reply.get('recovery'),
             provider_code=reply.get('provider_code'),provider_param=reply.get('provider_param'),http_status=reply.get('http_status'))
    if (reply.get('recovery') or {}).get('action')=='pause_usage' and s.get('connection'):
        state.setdefault('paused_routes',{})[s['connection']['auth_mode']]={'reason':t['reason'],'provider_code':t['provider_code'],'session':name}
    s['turns'].append(t);s['pending']=None;validate(state);store.save(data,NS,COMPONENT,state)
    return t

def connection_profile():
    from . import chatgpt_auth as auth
    s=llm.settings('chatgpt');identity=None
    if s['auth_mode']=='plan':
        o=auth.load()
        if o:identity=whole.sha_obj({k:o[k] for k in ('issuer','subject','client_id')})
    return {'auth_mode':s['auth_mode'],'base_url':s['base_url'],'model':s['model'],'identity_binding':identity}

@transactional()
def resume_route(data,auth_mode):
    """Explicit local operator action after reviewing usage; no request or refund."""
    require_alive(data)
    if auth_mode not in ('api','plan'):raise ValueError('CHATGPT_AUTH_MODE')
    state=load(data);resumed=auth_mode in state.get('paused_routes',{})
    if resumed:
        del state['paused_routes'][auth_mode];validate(state);store.save(data,NS,COMPONENT,state)
    return {'ok':True,'auth_mode':auth_mode,'resumed':resumed,'external_calls':0,'request_slots_refunded':False}

@transactional()
def resolve_pending(data,session,nonce):
    """Locally settle an interrupted reservation as UNKNOWN; never contact a teacher."""
    require_alive(data);state=load(data)
    s=state['sessions'].get(session)
    if not s or not s.get('pending') or s['pending']['nonce']!=nonce:raise ValueError('CHATGPT_REQUEST_BINDING')
    reply={'ok':False,'reason':'INTERRUPTED_OUTCOME_UNKNOWN','recovery':{'action':'continue_with_new_request','remote_outcome':'unknown','automatic_retry':False}}
    # Reuse the same checked reservation binding and append-only finish path.
    t=finish(data,session,nonce,reply)
    return {'ok':True,'session':session,'settled_turn':t,'requests':s['requests'],'external_calls':0,'request_slot_refunded':False,'verified':False}

def turn(data,query,session='main',max_calls=16,system=SYSTEM,schema=None,kind='dialogue:1',history=True,context_turns=16,context_chars=48000):
    from . import chatgpt_auth as auth
    auth.require_external_to(data)
    if 'chatgpt' not in llm.parents():return {'ok':False,'reason':'CHATGPT_CONNECTION_REQUIRED','verified':False}
    profile=connection_profile()
    ticket=reserve(data,session,query,max_calls,profile,context_turns,context_chars)
    from tukuyo_common.atomic_fs import maybe_crash
    maybe_crash('chatgpt:after_reserve')
    try:
        user=ticket['history'] if history else query
        reply=llm.call(kind,system,user,schema=schema,max_tokens=2048,parent='chatgpt',auth_mode=profile['auth_mode'])
    except Exception as e:
        # Never persist SDK exception text or auth token-bearing request objects.
        reply={'ok':False,'reason':'TRANSPORT_'+type(e).__name__}
    maybe_crash('chatgpt:after_response')
    t=finish(data,session,ticket['nonce'],reply)
    return {**t,'session':session,'reply':reply,'dialogue_is_verified_knowledge':False}

def diagnose(probe=False,auth_mode=None,both=False):
    from . import chatgpt_auth as auth
    if both:
        routes={m:diagnose(probe,auth_mode=m) for m in ('plan','api')}
        return {'ok':all(x['ok'] for x in routes.values()),'routes':routes,'automatic_billing_fallback':False,'live_connection_verified':all(x['live_connection_verified'] for x in routes.values())}
    s=llm.settings('chatgpt',auth_mode=auth_mode)
    r={'ok':True,'configured':s['key'] and bool(s['model']),'model':s['model'],'auth_mode':s['auth_mode'],
       'replay_mode':bool(s['replay']),'live_connection_verified':False,'credential_present':s['key'],
       'stream':s['stream'],'timeout_seconds':s['timeout'],'automatic_retry':False}
    if s['auth_mode']=='plan':r['plan']=auth.status()
    if not probe:return r
    if s['replay']:return {**r,'ok':False,'reason':'LIVE_PROBE_DISABLED_FOR_REPLAY'}
    if not r['configured']:return {**r,'ok':False,'reason':'CHATGPT_CONNECTION_REQUIRED'}
    p=llm.call('connection-probe:1','Return exactly TUKUYO_CONNECTED.','Connection test.',max_tokens=128,parent='chatgpt',auth_mode=s['auth_mode'])
    good=p.get('ok') and (p.get('text') or '').strip()=='TUKUYO_CONNECTED'
    return {**r,'ok':bool(good),'live_connection_verified':bool(good),'reason':p.get('reason') or (None if good else 'PROBE_REPLY_MISMATCH'),
            'response_id':p.get('request_id'),'usage':p.get('usage'),'recovery':p.get('recovery')}
