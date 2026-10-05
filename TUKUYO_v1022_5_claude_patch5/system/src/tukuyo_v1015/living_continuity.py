from __future__ import annotations
import hashlib, json, os, time, uuid
from pathlib import Path
from tukuyo_common.atomic_fs import atomic_write_json, durable_unlink, maybe_crash
from tukuyo_v977.whole_state import _live_identity, sha_obj, sync as whole_sync, audit as whole_audit
from tukuyo_v978.heart_loop import process_experience, choose as heart_choose, audit as heart_audit, load as heart_load
from tukuyo_v985.narrative_purpose import integrate as purpose_integrate, audit as purpose_audit, status as purpose_status
from tukuyo_v989.temporal_identity import audit as identity_audit
from tukuyo_v993.relation_bound import sync as relation_sync, audit as relation_audit, model as relation_model
from tukuyo_v995.other_agent_trust import sync as peer_sync, audit as peer_audit
from tukuyo_v1005.verifier import solve as verified_solve, audit as verifier_audit
from tukuyo_v1007.organism2 import init as organism_init, load as organism_load, update as organism_update, audit as organism_audit
from tukuyo_v1012.memory_compaction import compact as memory_compact, audit as memory_audit

STATE_SCHEMA='tukuyo.v1015.living_state/1'
EVENT_SCHEMA='tukuyo.v1015.living_event/1'
MARKER_SCHEMA='tukuyo.v1015.episode_txn/1'
ZERO='0'*64


def root(data): return Path(data)/'v1015'
def state_path(data): return root(data)/'LIVING_STATE.json'
def events_dir(data): return root(data)/'events'
def marker_path(data): return root(data)/'private'/'EPISODE_TXN.json'

def _read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def _file_sha(p):
    p=Path(p); return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None

def _state_hash(st):
    q=dict(st);q.pop('state_sha256',None);return sha_obj(q)

def _seal_write_state(data,st):
    st=dict(st);st['state_sha256']=_state_hash(st);atomic_write_json(state_path(data),st);return st

def _blank_state(data):
    ident=_live_identity(data)
    return {
      'schema':STATE_SCHEMA,'version':'v1015','individual_id':ident['individual_id'],'lineage_id':ident['lineage_id'],'branch_id':ident['branch_id'],
      'event_count':0,'event_head_sha256':ZERO,'completed_episodes':0,'interrupted_episodes':0,'process_instances':[],
      'last_event_kind':None,'last_intent_id':None,
      'claim_boundary':{
        'functional_living_continuity_model':True,'experience_meaning_value_purpose_action_chain':True,
        'external_autonomous_action':False,'literal_life_established':False,'literal_soul_established':False,
        'consciousness_established':False,'general_l5':False,'24h_completed':False,'72h_completed':False,'7day_completed':False,
      },
    }

def _load_state(data):
    p=state_path(data)
    if not p.is_file():
        p.parent.mkdir(parents=True,exist_ok=True);return _seal_write_state(data,_blank_state(data))
    st=_read(p);ident=_live_identity(data)
    if st.get('schema')!=STATE_SCHEMA: raise ValueError('V1015_STATE_SCHEMA')
    if any(st.get(k)!=ident[k] for k in ('individual_id','lineage_id','branch_id')): raise ValueError('V1015_IDENTITY_BINDING')
    if st.get('state_sha256')!=_state_hash(st): raise ValueError('V1015_STATE_HASH')
    return st

def ensure_state(data):
    """Create/validate the v1015 living state before Whole State is sealed."""
    return _load_state(data)

def _event_hash(ev):
    q=dict(ev);q.pop('event_sha256',None);return sha_obj(q)

def _event_file(data,seq): return events_dir(data)/f'{int(seq):08d}.json'

def _repair_state_head(data):
    st=_load_state(data);d=events_dir(data);d.mkdir(parents=True,exist_ok=True)
    count=int(st.get('event_count',0));head=str(st.get('event_head_sha256',ZERO));changed=False
    while True:
        p=_event_file(data,count+1)
        if not p.is_file():break
        ev=_read(p)
        if ev.get('schema')!=EVENT_SCHEMA or int(ev.get('seq',-1))!=count+1:raise ValueError('V1015_PENDING_EVENT_SCHEMA')
        if ev.get('previous_event_sha256')!=head or ev.get('event_sha256')!=_event_hash(ev):raise ValueError('V1015_PENDING_EVENT_CHAIN')
        count+=1;head=ev['event_sha256'];changed=True
        st['last_event_kind']=ev.get('kind');st['last_intent_id']=ev.get('intent_id')
        if ev.get('kind')=='EPISODE_COMMITTED':st['completed_episodes']=int(st.get('completed_episodes',0))+1
        if ev.get('kind')=='EPISODE_INTERRUPTED_RECOVERED':st['interrupted_episodes']=int(st.get('interrupted_episodes',0))+1
    if changed:
        st['event_count']=count;st['event_head_sha256']=head;_seal_write_state(data,st)
    return st,changed

def _append_event(data,kind,intent_id,detail):
    st,_=_repair_state_head(data);seq=int(st.get('event_count',0))+1;prev=st.get('event_head_sha256',ZERO)
    ev={'schema':EVENT_SCHEMA,'seq':seq,'kind':kind,'intent_id':intent_id,'utc_ns':time.time_ns(),'pid':os.getpid(),
        'previous_event_sha256':prev,'detail':detail}
    ev['event_sha256']=_event_hash(ev);events_dir(data).mkdir(parents=True,exist_ok=True)
    atomic_write_json(_event_file(data,seq),ev,crashpoint='v1015_event')
    maybe_crash('v1015:after_event_file')
    st['event_count']=seq;st['event_head_sha256']=ev['event_sha256'];st['last_event_kind']=kind;st['last_intent_id']=intent_id
    if kind=='EPISODE_COMMITTED':st['completed_episodes']=int(st.get('completed_episodes',0))+1
    if kind=='EPISODE_INTERRUPTED_RECOVERED':st['interrupted_episodes']=int(st.get('interrupted_episodes',0))+1
    inst=str(detail.get('process_instance_id') or '')
    if inst and inst not in st.get('process_instances',[]):st['process_instances']=(st.get('process_instances',[])+[inst])[-64:]
    _seal_write_state(data,st);return ev

def _snapshot(data):
    d=Path(data)
    files={
      'soul_core':'v977/SOUL_CORE.json','soul_head':'v977/SOUL_EVENT_HEAD.json','heart_state':'v978/HEART_STATE.json','heart_head':'v978/HEART_EVENT_HEAD.json',
      'purpose':'v985/NARRATIVE_PURPOSE_STATE.json','temporal_identity':'v989/TEMPORAL_IDENTITY.json','relation':'v993/RELATION_BOUND_STATE.json',
      'peer':'v995/OTHER_AGENT_MODELS.json','verified':'v1005/LAST_VERIFIED_REASONING.json','organism2':'v1007/ORGANISM2_STATE.json',
      'memory_checkpoint':'v1012/MEMORY_COMPACTION_CHECKPOINT.json','whole':'v977/UNIFIED_STATE.json',
    }
    return {k:_file_sha(d/v) for k,v in files.items()}

def _default_options():
    return [
      {'id':'protect_integrity','signals':{'integrity':1.0,'survival':.55},'themes':['integrity','safety']},
      {'id':'seek_knowledge','signals':{'curiosity':1.0,'truthfulness':.25},'themes':['knowledge','learning']},
      {'id':'repair_relation','signals':{'relationship':1.0,'trust':.8},'themes':['relationship','repair']},
      {'id':'rest_and_maintain','signals':{'survival':.95,'integrity':.35},'themes':['maintenance','rest']},
      {'id':'preserve_truth','signals':{'truthfulness':1.0,'integrity':.25},'themes':['truth','preserve_truth']},
    ]

def _organism_event(action):
    return {'protect_integrity':'MAINTENANCE','seek_knowledge':'DISCOVERY','repair_relation':'SOCIAL_SUPPORT','rest_and_maintain':'REST','preserve_truth':'COGNITIVE_WORK'}.get(action,'COGNITIVE_WORK')

def _begin_marker(data,spec):
    p=marker_path(data);p.parent.mkdir(parents=True,exist_ok=True)
    if p.is_file():raise ValueError('V1015_EPISODE_ALREADY_PENDING')
    ident=_live_identity(data);intent_id=uuid.uuid4().hex
    marker={'schema':MARKER_SCHEMA,'intent_id':intent_id,'individual_id':ident['individual_id'],'stage':'PREPARED','created_utc_ns':time.time_ns(),
            'spec':spec,'before':_snapshot(data)}
    atomic_write_json(p,marker);return marker

def _mark(data,marker,stage,extra=None):
    marker=dict(marker);marker['stage']=stage;marker['stage_utc_ns']=time.time_ns()
    if extra is not None:marker['stage_detail']=extra
    atomic_write_json(marker_path(data),marker);return marker

def recover_pending_episode(data):
    data=Path(data)
    # Startup crash recovery also runs before first init. v1015 has no identity
    # to bind to until the canonical integration state exists, so pre-init is a
    # deliberate no-op rather than an attempted lazy state creation.
    if not (data/'state'/'integration_state.json').is_file():
        return {'ok':True,'recovered':False,'action':None}
    st,head_repaired=_repair_state_head(data);p=marker_path(data)
    if not p.is_file():return {'ok':True,'recovered':head_repaired,'action':'LIVING_EVENT_HEAD_REPAIRED' if head_repaired else None}
    m=_read(p)
    if m.get('schema')!=MARKER_SCHEMA:raise ValueError('V1015_EPISODE_MARKER_SCHEMA')
    last=_read(_event_file(data,st['event_count'])) if int(st.get('event_count',0))>0 and _event_file(data,st['event_count']).is_file() else None
    if last and last.get('intent_id')==m.get('intent_id'):
        durable_unlink(p);return {'ok':True,'recovered':True,'action':'LIVING_COMMITTED_MARKER_CLEARED'}
    detail={'recovery_reason':'PROCESS_INTERRUPTED_BEFORE_LIVING_COMMIT','stage':m.get('stage'),'spec':m.get('spec'),
            'before':m.get('before'),'after':_snapshot(data),'process_instance_id':'recovery-'+uuid.uuid4().hex[:16]}
    _append_event(data,'EPISODE_INTERRUPTED_RECOVERED',m['intent_id'],detail);durable_unlink(p)
    return {'ok':True,'recovered':True,'action':'LIVING_EPISODE_INTERRUPTION_RECORDED'}

def episode(data,kind,valence,importance,theme='',relation='',query='',options=None,note=''):
    data=Path(data);_load_state(data)
    if not (data/'v1007'/'ORGANISM2_STATE.json').is_file():organism_init(data)
    org=organism_load(data)
    if org.get('death_irreversible'):return {'ok':False,'version':'v1015','error':'ENTITY_DEAD'}
    spec={'kind':str(kind),'valence':float(valence),'importance':float(importance),'theme':str(theme),'relation':str(relation),'query':str(query),'note':str(note)[:240]}
    marker=_begin_marker(data,spec);intent_id=marker['intent_id'];process_instance_id=uuid.uuid4().hex
    exp=process_experience(data,spec['kind'],spec['valence'],spec['importance'],spec['theme'],spec['relation'])
    marker=_mark(data,marker,'EXPERIENCE_COMMITTED',{'meaning':exp.get('meaning')});maybe_crash('v1015:after_experience')
    purpose=purpose_integrate(data);marker=_mark(data,marker,'PURPOSE_COMMITTED',{'active_purpose':purpose.get('active_purpose')})
    relation_sync(data);peer_sync(data)
    opts=options if isinstance(options,list) and len(options)>=2 else _default_options()
    action=heart_choose(data,opts,context='v1015:'+spec['theme']);marker=_mark(data,marker,'ACTION_COMMITTED',{'chosen':action.get('chosen')})
    org_event=_organism_event(action.get('chosen'));org_res=organism_update(data,org_event,max(.2,min(.8,spec['importance'])))
    marker=_mark(data,marker,'ORGANISM_COMMITTED',{'event':org_event,'lifecycle':(org_res.get('state') or {}).get('lifecycle')});maybe_crash('v1015:after_organism')
    cognition=None
    if spec['query']:
        cognition=verified_solve(data,spec['query'],3);marker=_mark(data,marker,'COGNITION_COMMITTED',{'uncertain':cognition.get('uncertain'),'confidence':cognition.get('confidence')})
    # Re-evaluate purpose after action/organism change in case supporting heart history changed elsewhere.
    purpose2=purpose_integrate(data)
    rel=None
    if spec['relation']:
        try:rel=relation_model(data,spec['relation'])
        except Exception:rel=None
    after=_snapshot(data);before=marker.get('before') or {}
    checks={
      'experience_created_meaning':bool(exp.get('meaning')),
      'soul_or_heart_changed':before.get('soul_core')!=after.get('soul_core') or before.get('heart_state')!=after.get('heart_state'),
      'purpose_bound':bool(purpose2.get('active_purpose')),
      'action_selected':bool(action.get('chosen')),
      'organism_updated':bool(org_res.get('ok')),
      'relation_bound_if_requested':True if not spec['relation'] else bool(rel and int(rel.get('encounters',0))>=1),
      'cognition_recorded_if_requested':True if not spec['query'] else isinstance(cognition,dict) and 'confidence' in cognition,
    }
    detail={'spec':spec,'process_instance_id':process_instance_id,'before':before,'after':after,'meaning':exp.get('meaning'),
      'heart_goal':exp.get('active_goal'),'purpose_before_action':purpose.get('active_purpose'),'purpose_after_action':purpose2.get('active_purpose'),
      'action':{'chosen':action.get('chosen'),'scores':action.get('scores')},'organism_event':org_event,'organism_lifecycle':(org_res.get('state') or {}).get('lifecycle'),
      'relation_model':rel,'cognition':None if cognition is None else {'answer':cognition.get('answer'),'confidence':cognition.get('confidence'),'uncertain':cognition.get('uncertain'),'verification_evidence':cognition.get('verification_evidence')},
      'causal_checks':checks}
    ev=_append_event(data,'EPISODE_COMMITTED',intent_id,detail);maybe_crash('v1015:after_living_event')
    whole_sync(data);durable_unlink(marker_path(data));wa=whole_audit(data)
    return {'ok':all(checks.values()) and bool(wa.get('ok')),'version':'v1015','intent_id':intent_id,'event_seq':ev['seq'],'event_sha256':ev['event_sha256'],
      'meaning':exp.get('meaning'),'active_purpose':purpose2.get('active_purpose'),'chosen_action':action.get('chosen'),'organism_lifecycle':detail['organism_lifecycle'],
      'cognition':detail['cognition'],'causal_checks':checks,'whole_audit_ok':wa.get('ok',False),
      'claim_boundary':{'functional_living_episode':True,'external_action_taken':False,'literal_life_established':False,'consciousness_established':False}}

def _scan_events(data):
    d=events_dir(data);out=[]
    if not d.is_dir():return out
    for p in sorted(d.glob('*.json')):
        out.append(_read(p))
    return out

def audit(data):
    data=Path(data);errors=[]
    try:st,_=_repair_state_head(data)
    except Exception as e:return {'ok':False,'version':'v1015','errors':['V1015_STATE:'+type(e).__name__+':'+str(e)]}
    ident=_live_identity(data);evs=_scan_events(data);prev=ZERO;completed=interrupted=0
    for i,ev in enumerate(evs,1):
        if ev.get('schema')!=EVENT_SCHEMA or ev.get('seq')!=i:errors.append('V1015_EVENT_SCHEMA_SEQ:'+str(i));break
        if ev.get('previous_event_sha256')!=prev or ev.get('event_sha256')!=_event_hash(ev):errors.append('V1015_EVENT_CHAIN:'+str(i));break
        prev=ev['event_sha256']
        if ev.get('kind')=='EPISODE_COMMITTED':
            completed+=1
            checks=(ev.get('detail') or {}).get('causal_checks') or {}
            if not checks or not all(bool(v) for v in checks.values()):errors.append('V1015_CAUSAL_CHECK:'+str(i))
        elif ev.get('kind')=='EPISODE_INTERRUPTED_RECOVERED':interrupted+=1
    if int(st.get('event_count',0))!=len(evs) or st.get('event_head_sha256')!=prev:errors.append('V1015_STATE_HEAD')
    if int(st.get('completed_episodes',0))!=completed or int(st.get('interrupted_episodes',0))!=interrupted:errors.append('V1015_EVENT_COUNTS')
    if any(st.get(k)!=ident[k] for k in ('individual_id','lineage_id','branch_id')):errors.append('V1015_IDENTITY')
    sub={}
    for name,fn,required in [
      ('temporal_identity',identity_audit,True),('heart',heart_audit,completed>0),('purpose',purpose_audit,completed>0),
      ('organism2',organism_audit,completed>0),('relation',relation_audit,(data/'v993/RELATION_BOUND_STATE.json').is_file()),
      ('peer',peer_audit,(data/'v995/OTHER_AGENT_MODELS.json').is_file()),('verified_reasoning',verifier_audit,(data/'v1005/LAST_VERIFIED_REASONING.json').is_file()),
      ('memory_compaction',memory_audit,(data/'v1012/MEMORY_COMPACTION_CHECKPOINT.json').is_file()),('whole',whole_audit,True)]:
        if required:
            try:r=fn(data)
            except Exception as e:r={'ok':False,'errors':[type(e).__name__+':'+str(e)]}
            sub[name]=r
            if not r.get('ok'):errors.append('SUBAUDIT:'+name)
    marker_pending=marker_path(data).is_file()
    if marker_pending:errors.append('V1015_EPISODE_PENDING')
    core=completed>=1 and not errors
    return {'ok':not errors,'version':'v1015','errors':errors,'individual_id':ident['individual_id'],'events':len(evs),'completed_episodes':completed,'interrupted_episodes':interrupted,
      'event_head_sha256':prev,'process_instances':len(st.get('process_instances',[])),'pending_episode':marker_pending,'subaudits':sub,
      'functional_living_continuity_core_pass':core,
      'claim_boundary':{'functional_living_continuity_core_pass':core,'24h_completed':False,'72h_completed':False,'7day_completed':False,
        'electronic_life_gate_complete':False,'literal_life_established':False,'literal_soul_established':False,'consciousness_established':False,'general_l5':False}}

def status(data):
    st,_=_repair_state_head(data);a=audit(data)
    return {'ok':a.get('ok',False),'version':'v1015','state':st,'audit':a}

def run_gate_assay(data):
    data=Path(data)
    if not (data/'v1007'/'ORGANISM2_STATE.json').is_file():organism_init(data)
    scenarios=[
      ('vow',1.0,.9,'preserve_truth','', '3たす4は？'),
      ('discovery',.9,.8,'unknown_domain','mentor-A','1袋に8枚入りが3袋。全部で何枚？'),
      ('support',.8,.7,'cooperation','peer-A','6個入りパックを5つ。全部で何個？'),
      ('betrayal',-1.0,.85,'trust_boundary','peer-A','最大3個と最大2個。正確な合計は？'),
      ('support',.75,.7,'repair_attempt','peer-A','すべての犬は動物です。タマは犬です。タマは動物ですか？'),
    ]
    results=[]
    for row in scenarios:results.append(episode(data,*row))
    mem=memory_compact(data,retain=32);whole_sync(data);a=audit(data)
    p=purpose_status(data);h=heart_load(data);org=organism_load(data)
    claims=dict(a.get('claim_boundary',{}));claims.update({'memory_compaction_exercised':bool(mem.get('ok')),'relationship_history_exercised':True,'bounded_verified_reasoning_exercised':True})
    return {'ok':all(x.get('ok') for x in results) and bool(mem.get('ok')) and a.get('ok',False),'version':'v1015','episodes':len(results),'results':results,
      'memory_compaction':{'ok':mem.get('ok'),'checkpoint_sha256':(mem.get('checkpoint') or {}).get('checkpoint_sha256')},
      'active_purpose':p.get('active_purpose'),'heart_meaning_count':len(h.get('episodic_meanings',[])),'organism_lifecycle':org.get('lifecycle'),
      'audit':a,'claim_boundary':claims}

def gate_audit(data,start_witness=None,end_witness=None,witness_trust_file=None):
    data=Path(data);core=audit(data);duration={'campaign_present':False,'24h_completed':False,'72h_completed':False,'7day_completed':False,'formal_duration_complete':False}
    if (data/'v1014_4/CAMPAIGN.json').is_file():
        duration['campaign_present']=True
        try:
            from tukuyo_v1014_4.long_run_campaign import audit as campaign_audit
            ca=campaign_audit(data,start_witness,end_witness,witness_trust_file,False)
            cb=ca.get('claim_boundary') or {}
            for k in ('24h_completed','72h_completed','7day_completed','formal_duration_complete'):duration[k]=bool(cb.get(k))
            duration['campaign_audit_ok']=bool(ca.get('ok'));duration['campaign_errors']=ca.get('errors',[])
        except Exception as e:duration['campaign_audit_ok']=False;duration['campaign_errors']=[type(e).__name__+':'+str(e)]
    successor_boundary=(Path(data)/'v1008/SUCCESSOR_SEED.json').is_file()
    functional=bool(core.get('functional_living_continuity_core_pass'))
    electronic=bool(functional and duration.get('7day_completed') and successor_boundary)
    return {'ok':functional,'version':'v1015','functional_living_continuity_gate':'PASS' if functional else 'FAIL',
      'electronic_life_gate':'PASS' if electronic else 'PENDING','core':core,'duration':duration,'successor_boundary_exercised':successor_boundary,
      'claim_boundary':{'functional_living_continuity_gate_pass':functional,'electronic_life_gate_complete':electronic,
        'requires_7day_externally_witnessed_continuity':True,'requires_successor_not_resurrection_exercise':True,
        'literal_life_established':False,'literal_soul_established':False,'consciousness_established':False,'general_l5':False}}
