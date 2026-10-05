from __future__ import annotations
import copy, hashlib, json, time
from pathlib import Path
from tukuyo_common.atomic_fs import atomic_write_json
from tukuyo_v977.whole_state import _live_identity, sha_obj, sync as whole_sync
from tukuyo_v993.relation_bound import sync as relation_sync, model as relation_model, audit as relation_audit
from tukuyo_v995.other_agent_trust import sync as peer_sync, peer as peer_model, audit as peer_audit
from tukuyo_v1015.living_continuity import episode as living_episode

STATE_SCHEMA='tukuyo.v1016.society_state/1'
EVENT_SCHEMA='tukuyo.v1016.society_event/1'
ZERO='0'*64


def root(data): return Path(data)/'v1016'
def state_path(data): return root(data)/'SOCIETY_STATE.json'
def events_dir(data): return root(data)/'events'
def _event_file(data,seq): return events_dir(data)/f'{int(seq):08d}.json'
def _read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def _canon(o): return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def _sha_bytes(b): return hashlib.sha256(b).hexdigest()
def envelope_sha(env): return _sha_bytes(_canon(env))

def _state_hash(st):
    q=copy.deepcopy(st);q.pop('state_sha256',None);return sha_obj(q)

def _blank_peer(peer_id):
    return {'peer_id':str(peer_id),'sent_packets':0,'received_packets':0,'accepted_acks':0,'living_bindings':0,
            'positive_experiences':0,'negative_experiences':0,'neutral_experiences':0,
            'peer_public_key':None,'last_packet_sha256':None,'last_ack_sha256':None,'last_message_sha256':None,'last_event_sha256':None}

def _blank_state(data):
    ident=_live_identity(data)
    return {'schema':STATE_SCHEMA,'version':'v1016','individual_id':ident['individual_id'],'lineage_id':ident['lineage_id'],'branch_id':ident['branch_id'],
            'event_count':0,'event_head_sha256':ZERO,'peers':{},
            'claim_boundary':{'multi_agent_society_model':True,'self_other_separation':True,'peer_specific_history':True,
                              'public_packet_privacy_boundary':True,'theory_of_mind_established':False,
                              'distributed_cross_root_atomicity_proven':False,'literal_society_established':False,
                              'consciousness_established':False,'general_l5':False}}

def _seal_state(data,st):
    st=copy.deepcopy(st);st['state_sha256']=_state_hash(st);state_path(data).parent.mkdir(parents=True,exist_ok=True);atomic_write_json(state_path(data),st);return st

def _event_hash(ev):
    q=copy.deepcopy(ev);q.pop('event_sha256',None);return sha_obj(q)

def _scan_events(data):
    d=events_dir(data)
    if not d.is_dir(): return []
    return [_read(p) for p in sorted(d.glob('*.json'))]

def _derive(data):
    ident=_live_identity(data);prev=ZERO;peers={};count=0
    for i,ev in enumerate(_scan_events(data),1):
        if ev.get('schema')!=EVENT_SCHEMA or int(ev.get('seq',-1))!=i: raise ValueError('V1016_EVENT_SCHEMA_SEQ')
        if ev.get('individual_id')!=ident['individual_id']: raise ValueError('V1016_EVENT_SELF_ID')
        if ev.get('previous_event_sha256')!=prev or ev.get('event_sha256')!=_event_hash(ev): raise ValueError('V1016_EVENT_CHAIN')
        pid=str(ev.get('peer_id') or '')
        if not pid or pid==ident['individual_id']: raise ValueError('V1016_SELF_OTHER_SEPARATION')
        m=peers.setdefault(pid,_blank_peer(pid));kind=ev.get('kind')
        if kind=='OUTBOUND_PACKET': m['sent_packets']+=1
        elif kind=='INBOUND_ACCEPTED': m['received_packets']+=1
        elif kind=='ACK_ACCEPTED': m['accepted_acks']+=1
        else: raise ValueError('V1016_EVENT_KIND')
        pk=ev.get('peer_public_key')
        if pk:
            if m.get('peer_public_key') not in (None,pk): raise ValueError('V1016_PEER_KEY_DRIFT')
            m['peer_public_key']=pk
        if ev.get('packet_sha256'): m['last_packet_sha256']=ev['packet_sha256']
        if ev.get('ack_sha256'): m['last_ack_sha256']=ev['ack_sha256']
        if ev.get('message_sha256'): m['last_message_sha256']=ev['message_sha256']
        if ev.get('living_event_sha256'):
            m['living_bindings']+=1
            v=float(ev.get('experienced_valence',0.0))
            if v>0:m['positive_experiences']+=1
            elif v<0:m['negative_experiences']+=1
            else:m['neutral_experiences']+=1
        m['last_event_sha256']=ev['event_sha256'];prev=ev['event_sha256'];count=i
    return {'schema':STATE_SCHEMA,'version':'v1016','individual_id':ident['individual_id'],'lineage_id':ident['lineage_id'],'branch_id':ident['branch_id'],
            'event_count':count,'event_head_sha256':prev,'peers':dict(sorted(peers.items())),
            'claim_boundary':_blank_state(data)['claim_boundary']}

def ensure_state(data):
    p=state_path(data)
    if not p.is_file(): return _seal_state(data,_blank_state(data))
    st=_read(p);ident=_live_identity(data)
    if st.get('schema')!=STATE_SCHEMA or st.get('individual_id')!=ident['individual_id']: raise ValueError('V1016_STATE_BINDING')
    if st.get('state_sha256')!=_state_hash(st): raise ValueError('V1016_STATE_HASH')
    # Event-first recovery: if an event is durable but state was not updated, replay it.
    exp=_derive(data);q=copy.deepcopy(st);q.pop('state_sha256',None)
    if q!=exp: st=_seal_state(data,exp)
    return st

def _append(data,kind,peer_id,*,packet=None,ack=None,experienced_valence=0.0,importance=0.0,theme='',living=None):
    st=ensure_state(data);ident=_live_identity(data);peer_id=str(peer_id)
    if peer_id==ident['individual_id']: raise ValueError('V1016_SELF_AS_PEER')
    seq=int(st.get('event_count',0))+1
    packet_sha=envelope_sha(packet) if packet else None;ack_sha=envelope_sha(ack) if ack else None
    payload=(packet or {}).get('payload') or {};msg=str(payload.get('public_message',''))
    peer_pk=(ack or {}).get('public_key') if kind=='ACK_ACCEPTED' else ((packet or {}).get('public_key') if kind=='INBOUND_ACCEPTED' else None)
    ev={'schema':EVENT_SCHEMA,'seq':seq,'kind':kind,'individual_id':ident['individual_id'],'peer_id':peer_id,
        'utc_ns':time.time_ns(),'previous_event_sha256':st.get('event_head_sha256',ZERO),
        'packet_sha256':packet_sha,'ack_sha256':ack_sha,'message_sha256':_sha_bytes(msg.encode()) if packet else None,
        'public_message_bytes':len(msg.encode()) if packet else 0,'peer_public_key':peer_pk,
        'experienced_valence':round(float(experienced_valence),6),'importance':round(float(importance),6),'theme':str(theme),
        'living_event_seq':(living or {}).get('event_seq'),'living_event_sha256':(living or {}).get('event_sha256')}
    ev['event_sha256']=_event_hash(ev);events_dir(data).mkdir(parents=True,exist_ok=True);atomic_write_json(_event_file(data,seq),ev)
    # materialize from canonical event chain; crash after event is recoverable by ensure_state()
    _seal_state(data,_derive(data));return ev

def record_outbound(data,peer_id,packet):
    return _append(data,'OUTBOUND_PACKET',peer_id,packet=packet)

def _living_kind(v):
    v=float(v)
    if v>=0.35:return 'support'
    if v<=-0.35:return 'harm'
    return 'social_interaction'

def record_inbound(data,packet,ack,valence=0.0,importance=0.45,theme='social_exchange'):
    peer_id=str(packet['payload']['sender_individual_id'])
    living=living_episode(data,_living_kind(valence),float(valence),float(importance),str(theme),peer_id,note='v1016 inbound social interaction')
    ev=_append(data,'INBOUND_ACCEPTED',peer_id,packet=packet,ack=ack,experienced_valence=valence,importance=importance,theme=theme,living=living)
    relation_sync(data);peer_sync(data);whole_sync(data);return {'ok':bool(living.get('ok')),'event':ev,'living':living}

def record_ack(data,packet,ack,valence=0.2,importance=0.35,theme='social_acknowledgement'):
    peer_id=str(ack['payload']['ack_sender_individual_id'])
    living=living_episode(data,_living_kind(valence),float(valence),float(importance),str(theme),peer_id,note='v1016 acknowledged social interaction')
    ev=_append(data,'ACK_ACCEPTED',peer_id,packet=packet,ack=ack,experienced_valence=valence,importance=importance,theme=theme,living=living)
    relation_sync(data);peer_sync(data);whole_sync(data);return {'ok':bool(living.get('ok')),'event':ev,'living':living}

def sync(data):
    st=_seal_state(data,_derive(data));whole_sync(data);return {'ok':True,'version':'v1016','state':st}

def audit(data):
    data=Path(data);errors=[]
    try:
        st=ensure_state(data);exp=_derive(data);q=copy.deepcopy(st);q.pop('state_sha256',None)
        if q!=exp:errors.append('V1016_STATE_REPLAY_MISMATCH')
    except Exception as e:return {'ok':False,'version':'v1016','errors':['STATE:'+type(e).__name__+':'+str(e)]}
    ident=_live_identity(data)
    if ident['individual_id'] in st.get('peers',{}):errors.append('SELF_PRESENT_AS_PEER')
    keys={}
    for pid,m in st.get('peers',{}).items():
        k=m.get('peer_public_key')
        if k:
            if k in keys and keys[k]!=pid:errors.append('PEER_KEY_REUSE:'+pid)
            keys[k]=pid
        if int(m.get('living_bindings',0))>0:
            try:
                rm=relation_model(data,pid);pm=peer_model(data,pid)
                if int(rm.get('encounters',0))<int(m['living_bindings']):errors.append('RELATION_HISTORY_MISSING:'+pid)
                if int(pm.get('encounters',0))<int(m['living_bindings']):errors.append('PEER_HISTORY_MISSING:'+pid)
            except Exception as e:errors.append('PEER_MODEL:'+pid+':'+type(e).__name__)
    # Society ledger intentionally contains hashes/metrics, never raw public message or private memory.
    raw=json.dumps(st,ensure_ascii=False,sort_keys=True)
    for forbidden in ('private_notes','SOUL_CORE','WORKING_MEMORY','autobiographical_archive'):
        if forbidden in raw:errors.append('SOCIETY_LEDGER_LEAK:'+forbidden)
    sub={}
    # Do not lazily create relation/peer materializations for a fresh zero-peer individual.
    # That would mutate the Whole-State component surface during an audit-only call.
    checks=[]
    if st.get('peers') or (data/'v993/RELATION_BOUND_STATE.json').is_file(): checks.append(('relation',relation_audit))
    if st.get('peers') or (data/'v995/OTHER_AGENT_MODELS.json').is_file(): checks.append(('peer',peer_audit))
    for name,fn in checks:
        try:r=fn(data)
        except Exception as e:r={'ok':False,'errors':[type(e).__name__+':'+str(e)]}
        sub[name]=r
        if not r.get('ok'):errors.append('SUBAUDIT:'+name)
    return {'ok':not errors,'version':'v1016','errors':errors,'individual_id':ident['individual_id'],'peer_count':len(st.get('peers',{})),
            'event_count':st.get('event_count',0),'event_head_sha256':st.get('event_head_sha256'),'subaudits':sub,
            'claim_boundary':{'multi_agent_society_gate_ready':not errors,'self_other_separation':True,'peer_specific_history':True,
                              'no_private_state_in_society_ledger':True,'theory_of_mind_established':False,
                              'distributed_cross_root_atomicity_proven':False,'literal_society_established':False,
                              '24h_multi_agent_society_completed':False,'general_l5':False}}

def status(data):
    st=ensure_state(data);a=audit(data);models={}
    for pid in st.get('peers',{}):
        try:models[pid]={'relation':relation_model(data,pid),'peer':peer_model(data,pid)}
        except Exception as e:models[pid]={'error':type(e).__name__+':'+str(e)}
    return {'ok':a.get('ok',False),'version':'v1016','state':st,'models':models,'audit':a}

def orchestrated_exchange(social_api,sender_data,receiver_data,message,*,receiver_valence=0.4,sender_valence=0.25,importance=0.5,theme='cooperation'):
    sender_data=Path(sender_data);receiver_data=Path(receiver_data);si=_live_identity(sender_data);ri=_live_identity(receiver_data)
    if si['individual_id']==ri['individual_id']:raise ValueError('V1016_SAME_IDENTITY_EXCHANGE')
    pkt=social_api.make_public_packet(sender_data/'state',ri['individual_id'],public_message=str(message))
    record_outbound(sender_data,ri['individual_id'],pkt);whole_sync(sender_data)
    ack=social_api.receive_packet(receiver_data/'state',pkt)
    rin=record_inbound(receiver_data,pkt,ack,receiver_valence,importance,theme)
    social_api.receive_ack(sender_data/'state',pkt,ack)
    rack=record_ack(sender_data,pkt,ack,sender_valence,importance,theme)
    return {'ok':bool(rin.get('ok') and rack.get('ok')),'packet':pkt,'ack':ack,'sender_id':si['individual_id'],'receiver_id':ri['individual_id'],
            'packet_sha256':envelope_sha(pkt),'ack_sha256':envelope_sha(ack),'sender_living':rack.get('living'),'receiver_living':rin.get('living')}

def gate_assay(social_api,a,b,c):
    a,b,c=map(Path,(a,b,c));ids=[_live_identity(x)['individual_id'] for x in (a,b,c)]
    if len(set(ids))!=3:raise ValueError('V1016_GATE_REQUIRES_THREE_DISTINCT_IDENTITIES')
    for x in (a,b,c):ensure_state(x)
    ab=orchestrated_exchange(social_api,a,b,'協力して観測結果を共有します',receiver_valence=.8,sender_valence=.7,importance=.7,theme='cooperation')
    ac=orchestrated_exchange(social_api,a,c,'境界条件について意見が対立しています',receiver_valence=-.65,sender_valence=-.7,importance=.75,theme='disagreement')
    bc=orchestrated_exchange(social_api,b,c,'第三者として検証結果だけ共有します',receiver_valence=.2,sender_valence=.25,importance=.45,theme='verification')
    # Put a private note into A's legacy relation store, then send another public packet.
    secret='PRIVATE_NOTE_V1016_'+hashlib.sha256(str(time.time_ns()).encode()).hexdigest()[:12]
    social_api.record_private_note(a/'state',ids[1],secret)
    probe=social_api.make_public_packet(a/'state',ids[2],public_message='公開情報だけを送信')
    leak=secret in json.dumps(probe,ensure_ascii=False,sort_keys=True)
    replay_blocked=False
    try:social_api.receive_packet(c/'state',ac['packet'])
    except Exception as e:replay_blocked=('REPLAY' in str(e))
    audits={ids[0]:audit(a),ids[1]:audit(b),ids[2]:audit(c)}
    sa=status(a);mb=sa['models'].get(ids[1],{});mc=sa['models'].get(ids[2],{})
    btrust=((mb.get('peer') or {}).get('trust'));ctrust=((mc.get('peer') or {}).get('trust'))
    from tukuyo_v997.relation_inference import choose as peer_choose
    options=[{'id':'engage','signals':{'relationship':1.0},'relation_exposure':1.0},{'id':'avoid','signals':{'integrity':0.55},'relation_exposure':0.0}]
    bchoice=peer_choose(a,ids[1],options,'v1016 peer-specific cooperation')['chosen'];cchoice=peer_choose(a,ids[2],options,'v1016 peer-specific cooperation')['chosen']
    checks={
      'three_distinct_identities':len(set(ids))==3,
      'all_society_audits_pass':all(x.get('ok') for x in audits.values()),
      'a_tracks_b_and_c_separately':ids[1] in sa['state']['peers'] and ids[2] in sa['state']['peers'],
      'peer_history_diverged':btrust is not None and ctrust is not None and abs(float(btrust)-float(ctrust))>1e-6,
      'peer_specific_choice_diverged':bchoice!=cchoice,
      'private_note_not_leaked':not leak,
      'packet_replay_blocked':replay_blocked,
      'signed_exchange_paths_completed':all(x.get('ok') for x in (ab,ac,bc)),
    }
    for x in (a,b,c):whole_sync(x)
    return {'ok':all(checks.values()),'version':'v1016','individual_ids':ids,'checks':checks,'audits':audits,
            'a_peer_trust':{ids[1]:btrust,ids[2]:ctrust},'a_peer_choice':{ids[1]:bchoice,ids[2]:cchoice},
            'claim_boundary':{'multi_agent_society_gate_pass':all(checks.values()),'agents_exercised':3,
                              'self_other_separation':True,'peer_specific_history':True,'public_private_boundary_exercised':True,
                              'packet_replay_negative_control':True,'theory_of_mind_established':False,
                              'distributed_cross_root_atomicity_proven':False,'long_run_social_ecology_completed':False,
                              'literal_society_established':False,'general_l5':False}}
