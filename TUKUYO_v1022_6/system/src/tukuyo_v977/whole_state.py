from __future__ import annotations
import hashlib,json,os,base64,time
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey
from tukuyo_common.atomic_fs import atomic_write_bytes,atomic_write_text

SCHEMA='tukuyo.v977.unified_individual_state/1'
ZERO='0'*64

def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha_obj(o):return sha_bytes(canon(o))
def _read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def _file_sha(p):
    p=Path(p);return sha_bytes(p.read_bytes()) if p.is_file() else None

def _key_paths(data):
    r=Path(data)/'v977';return r/'private'/'whole_state.key',r/'whole_state.pub'

def _ensure_key(data):
    skp,pkp=_key_paths(data);skp.parent.mkdir(parents=True,exist_ok=True)
    if skp.exists() and pkp.exists():return skp.read_text().strip(),pkp.read_text().strip()
    sk=Ed25519PrivateKey.generate(); raw=base64.b64encode(sk.private_bytes_raw()).decode();pub=base64.b64encode(sk.public_key().public_bytes_raw()).decode()
    atomic_write_text(skp,raw,mode=0o600);atomic_write_text(pkp,pub);return raw,pub

def _sign(data,payload):
    sk64,pub=_ensure_key(data);sk=Ed25519PrivateKey.from_private_bytes(base64.b64decode(sk64));return {'payload':payload,'public_key':pub,'signature':base64.b64encode(sk.sign(canon(payload))).decode()}

def _verify(env,pub):
    if env.get('public_key')!=pub:return False
    try:Ed25519PublicKey.from_public_bytes(base64.b64decode(pub)).verify(base64.b64decode(env['signature']),canon(env['payload']));return True
    except Exception:return False

def state_path(data):return Path(data)/'v977'/'UNIFIED_STATE.json'
def soul_path(data):return Path(data)/'v977'/'SOUL_CORE.json'
def event_path(data):return Path(data)/'v977'/'SOUL_EVENTS.jsonl'
def legacy_event_path(data):return Path(data)/'v977'/'SOUL_EVENTS.json'
def event_head_path(data):return Path(data)/'v977'/'SOUL_EVENT_HEAD.json'

def _live_identity(data):
    p=Path(data)/'state'/'integration_state.json'
    if not p.is_file():raise ValueError('LIVE_INDIVIDUAL_REQUIRED')
    q=_read(p)['payload'];return {'individual_id':q['individual_id'],'lineage_id':q['lineage_id'],'branch_id':q['branch_id']}

def _organism(data):return _read(Path(data)/'state'/'organism'/'organism_state.json')['payload']

# The temperament every individual is born with: the values of a new soul, and where law 2 lets them settle back to.
TEMPERAMENT={'survival':0.8,'integrity':0.8,'curiosity':0.5,'truthfulness':0.65,'relationship':0.4}

def _default_soul(identity):
    return {'schema':'tukuyo.v977.soul_core/1','individual_id':identity['individual_id'],'update_seq':0,
      'core_values':dict(TEMPERAMENT),
      'vows':[],'scars':[],'attachments':{},'aversions':{},'themes':{},'value_drift':{},
      'origin':'FUNCTIONAL_SOUL_MODEL_NOT_CONSCIOUSNESS_CLAIM'}

def load_soul(data):
    ident=_live_identity(data);p=soul_path(data)
    if not p.exists():
        x=_default_soul(ident);p.parent.mkdir(parents=True,exist_ok=True);atomic_write_bytes(p,canon(x)+b'\n');return x
    x=_read(p)
    if x.get('schema')!='tukuyo.v977.soul_core/1' or x.get('individual_id')!=ident['individual_id']:raise ValueError('SOUL_IDENTITY_BINDING')
    return x

# The soul laws. Each soul event records the law it was lived under (no field: law 1), so every history replays exactly.
#   law 1  (v977) every step is linear and stops at its bound: a long life pins curiosity, truthfulness, attachments and
#          themes at their bounds, and survival, integrity and relationship never move
#   law 2  (generation 4) a step toward a bound shrinks as the value nears it, and with each experience every value
#          settles a little back toward its temperament and every theme fades a little: what a value becomes reflects
#          the mix of a whole life, not only its length, and it keeps answering to what happens next. Relationship
#          follows the experiences with others; the soul keeps, for each one it learns from, how often what they gave
#          held up and how often it failed, recent ones weighing more (TRUST_MEMORY)
LAWS=(1,2)
SETTLE=0.002        # law 2: how far each experience lets values settle back toward the temperament and themes fade
VALUE_RATE=0.06     # law 2: curiosity and truthfulness (the same step as law 1 at the temperament)
RELATION_RATE=0.02  # law 2: relationship, moved by every experience with another
TRUST_MEMORY=0.99   # law 2: each new experience with someone keeps 99% of the weight of the earlier ones (about the last 100)

def _toward(x,d,lo=0.0,hi=1.0):
    # law 2: diminishing returns - a step toward a bound shrinks as the value nears it, so no value is ever pinned
    return x+d*((hi-x) if d>=0 else (x-lo))/(hi-lo)

def _law2(s,kind,v,imp,theme,relation):
    cv=s['core_values']
    for k,x0 in TEMPERAMENT.items():
        if k in cv:cv[k]=x0+(cv[k]-x0)*(1-SETTLE)
    for t in s['themes'].values():t['weight']=round(t['weight']*(1-SETTLE),6)
    if theme:
        t=s['themes'].setdefault(theme,{'weight':0.0,'encounters':0});t['encounters']+=1;t['weight']=round(_toward(t['weight'],v*imp*0.5,-2,2),6)
    if kind in ('discovery','learning'):cv['curiosity']=_toward(cv['curiosity'],max(0,v)*imp*VALUE_RATE)
    if kind=='honesty' and v>0:cv['truthfulness']=_toward(cv['truthfulness'],v*imp*VALUE_RATE)
    if relation:
        cv['relationship']=_toward(cv['relationship'],v*imp*RELATION_RATE)
        a=s['attachments'].get(relation,0.0);s['attachments'][relation]=round(_toward(a,v*imp*0.2,-1,1),6)
        if kind in ('parent_help','parent_error'):
            r=s.setdefault('trust',{}).setdefault(relation,{'held':0.0,'failed':0.0})
            r['held']=round(r['held']*TRUST_MEMORY+(kind=='parent_help'),6);r['failed']=round(r['failed']*TRUST_MEMORY+(kind=='parent_error'),6)
    for k in cv:cv[k]=round(cv[k],6)
    _marks(s,kind,v,imp,theme,relation)
    return s

def _marks(s,kind,v,imp,theme,relation):
    # scars and vows stay for good, under either law
    if kind in ('betrayal','harm') and imp>=0.6:
        sid=hashlib.sha256(f"{kind}:{theme}:{relation}:{s['update_seq']}".encode()).hexdigest()[:16]
        s['scars'].append({'scar_id':sid,'kind':kind,'theme':theme,'relation':relation,'strength':round(imp*abs(v),6)})
    if kind=='vow' and imp>=0.5 and theme:
        if theme not in [x['theme'] for x in s['vows']]:s['vows'].append({'theme':theme,'strength':round(imp,6)})

def trust_record(s,relation):
    # law 2: the share of what came from this one that held up, recent experiences weighing more; 0.5 for someone never met
    r=(s.get('trust') or {}).get(relation)
    return round((1+r['held'])/(2+r['held']+r['failed']),6) if r else 0.5

def _apply_experience_mutation(s,kind,valence,importance,theme='',relation='',law=1):
    # Deterministic soul transition law retained for replay/audit by v989+.
    import copy
    if law not in LAWS:raise ValueError('SOUL_LAW')
    s=copy.deepcopy(s);imp=float(importance);v=float(valence);s['update_seq']+=1
    if law==2:return _law2(s,kind,v,imp,theme,relation)
    if theme:
        t=s['themes'].setdefault(theme,{'weight':0.0,'encounters':0});t['encounters']+=1;t['weight']=round(max(-2,min(2,t['weight']+v*imp*0.25)),6)
    if kind in ('discovery','learning'):
        s['core_values']['curiosity']=round(min(1.0,s['core_values']['curiosity']+max(0,v)*imp*0.03),6)
    if kind=='honesty' and v>0:
        # generation 4: an answer withheld because the readings did not agree, instead of a guess
        s['core_values']['truthfulness']=round(min(1.0,s['core_values']['truthfulness']+v*imp*0.02),6)
    _marks(s,kind,v,imp,theme,relation)
    if relation:
        a=s['attachments'].setdefault(relation,0.0);s['attachments'][relation]=round(max(-1,min(1,a+v*imp*0.1)),6)
    return s

def experience(data,kind,valence,importance,theme='',relation='',law=1):
    from tukuyo_v1019.lifecycle import require_alive
    require_alive(data)
    if not (-1<=float(valence)<=1) or not (0<=float(importance)<=1):raise ValueError('EXPERIENCE_RANGE')
    if law not in LAWS:raise ValueError('SOUL_LAW')
    s=load_soul(data);imp=float(importance);v=float(valence)
    before_sha=sha_obj(s)
    new_s=_apply_experience_mutation(s,kind,v,imp,theme,relation,law)
    from tukuyo_common.journal import migrate_boxed_json,last_event,append_event
    ep=event_path(data);hp=event_head_path(data);migrate_boxed_json(legacy_event_path(data),ep,hp,'tukuyo.v1011.soul_event_head/1',sha_obj)
    last=last_event(ep);prev=last.get('event_sha256',ZERO) if last else ZERO;seq=int(last.get('seq',0))+1 if last else 1
    e={'seq':seq,'individual_id':new_s['individual_id'],'kind':kind,'valence':v,'importance':imp,'theme':theme,'relation':relation,'prev_sha256':prev,'soul_sha256':sha_obj(new_s)}
    if law!=1:e['law']=law
    e['event_sha256']=sha_obj(e)
    # v1014.4: canonical event first, then materialized soul. If process death occurs
    # between them, startup can deterministically rematerialize from the journal.
    append_event(ep,hp,e,'tukuyo.v1011.soul_event_head/1',sha_obj,new_s['individual_id'])
    from tukuyo_common.atomic_fs import maybe_crash
    maybe_crash('soul:after_event')
    atomic_write_bytes(soul_path(data),canon(new_s)+b'\n',crashpoint='soul_core')
    s=new_s
    # v989 is an audit layer over the pre-existing soul event chain. It is invoked
    # only after the canonical v977 event is durably written, so a crash cannot
    # create a transition without its source event.
    try:
        from tukuyo_v989.temporal_identity import sync_transitions
        sync_transitions(data)
    except ImportError:
        pass
    return {'ok':True,'event':e,'soul':s,'before_soul_sha256':before_sha}

def _component_hashes(data):
    d=Path(data);pairs={
      'integration_state':'state/integration_state.json','organism_state':'state/organism/organism_state.json','semantic_state':'state/semantic/semantic_state.json',
      'research_ledger':'research_v967/INTEGRATED_LEDGER.json','primitive_registry':'research_registry_v958/ACTIVE_PRIMITIVES.json','family_registry':'research_v967/FAMILY_REGISTRY.json',
      'inheritance_registry':'inherited_research_v962/PUBLIC_CAPABILITIES.json','soul_core':'v977/SOUL_CORE.json','soul_events':'v977/SOUL_EVENT_HEAD.json',
      'heart_state':'v978/HEART_STATE.json','heart_events':'v978/HEART_EVENT_HEAD.json','deep_soul_core':'v979/DEEP_SOUL_CORE.json',
      'fork_origin':'v981/FORK_ORIGIN.json','fork_registry':'v981/BRANCH_REGISTRY.json','homeostasis_state':'v983/HOMEOSTASIS_STATE.json','homeostasis_events':'v983/HOMEOSTASIS_EVENTS.json',
      'full_runtime_fork_assay':'v984/FULL_RUNTIME_FORK_ASSAY.json','narrative_purpose_state':'v985/NARRATIVE_PURPOSE_STATE.json','narrative_purpose_events':'v985/NARRATIVE_PURPOSE_EVENTS.json',
      'long_horizon_plan':'v986/LONG_HORIZON_PLAN.json','plan_events':'v986/PLAN_EVENTS.json','plan_execution_state':'v987/PLAN_EXECUTION_STATE.json','execution_events':'v987/EXECUTION_EVENTS.json',
      'strategy_state':'v988/STRATEGY_STATE.json','strategy_events':'v988/STRATEGY_EVENTS.json',
      'temporal_identity_state':'v989/TEMPORAL_IDENTITY.json','temporal_identity_transitions':'v989/TEMPORAL_IDENTITY.json',
      'closed_environment_state':'v990/ENVIRONMENT_STATE.json','closed_environment_events':'v990/ENVIRONMENT_EVENTS.json',
      'grounded_organism_state':'v991/GROUNDED_ORGANISM_STATE.json','grounded_organism_events':'v991/GROUNDED_EVENTS.json',
      'holdout_assay':'v992/HOLDOUT_ASSAY.json',
      'relation_bound_state':'v993/RELATION_BOUND_STATE.json','semantic_events_v994':'v994/SEMANTIC_EVENTS.json',
      'other_agent_models_v995':'v995/OTHER_AGENT_MODELS.json','conversation_events_v996':'v996/CONVERSATION_EVENT_HEAD.json','semantic_inference_events_v998':'v998/SEMANTIC_EVENT_HEAD.json',
      'verified_reasoning_v1005':'v1005/LAST_VERIFIED_REASONING.json','research_assay_v1006':'v1006/RESEARCH_ASSAY.json',
      'organism2_state_v1007':'v1007/ORGANISM2_STATE.json','organism2_events_v1007':'v1007/ORGANISM2_EVENTS.json',
      'whole_living_cycle_v1008':'v1008/LAST_CYCLE.json','long_lived_identity_assay_v1009':'v1009/LONG_LIVED_IDENTITY_ASSAY.json','memory_compaction_v1012':'v1012/MEMORY_COMPACTION_CHECKPOINT.json','working_memory_v1012':'v1012/WORKING_MEMORY.json','realtime_continuity_v1013':'v1013/REALTIME_EVENT_HEAD.json',
      'living_state_v1015':'v1015/LIVING_STATE.json','society_state_v1016':'v1016/SOCIETY_STATE.json','succession_state_v1017':'v1017/SUCCESSION_STATE.json','succession_state_v1018':'v1018/SUCCESSION_STATE.json','evolution_state_v1019':'v1019/EVOLUTION_STATE.json'}
    if (d/'v1020').exists():pairs['population_ecology_v1020']='v1020/ECOLOGY_STATE.json'
    if (d/'v1021').exists():pairs['runtime_ecology_bridge_v1021']='v1021/BRIDGE_STATE.json'
    if (d/'v1022'/'commits').exists():pairs['local_cognition_v1022']='v1022/STATE.json'
    if (d/'v1022_ecology'/'commits').exists():pairs['runtime_metabolism_v1022']='v1022_ecology/STATE.json'
    if (d/'v1023r'/'commits').exists():pairs['open_world_research_v1023r']='v1023r/STATE.json'
    # generation 4: what the child learned from its parents and the record of its life (tukuyo_g4.own)
    if (d/'g4').exists():pairs.update({'g4_learned':'g4/learned.json','g4_remembered':'g4/remembered.json','g4_life':'g4/life.json'})
    return {k:_file_sha(d/v) for k,v in pairs.items()}

def sync(data):
    ident=_live_identity(data);soul=load_soul(data);org=_organism(data)
    p=state_path(data);prev=ZERO;seq=1
    if p.exists():
        old=_read(p);prev=sha_obj(old);seq=int(old['payload']['seq'])+1
    payload={'schema':SCHEMA,'seq':seq,'identity':ident,'lifecycle':org['lifecycle'],'affect':org['affect'],'goals':org['goals'],
      'self_model_sha256':sha_obj(org['self_model']),'autobiography_sha256':sha_obj({'records':org['memory']['autobiographical'],'archive':org['memory']['autobiographical_archive']}),
      'soul_core_sha256':sha_obj(soul),'component_hashes':_component_hashes(data),'previous_unified_state_sha256':prev,
      'claim_boundary':{'functional_soul_model':True,'consciousness_established':False,'literal_soul_established':False,'general_l5':False,'general_l6':False}}
    env=_sign(data,payload);p.parent.mkdir(parents=True,exist_ok=True);atomic_write_bytes(p,canon(env)+b'\n');return env

def quick_audit(data):
    ident=_live_identity(data);p=state_path(data)
    if not p.exists():return {'ok':False,'errors':['UNIFIED_STATE_MISSING'],'version':'v1014.4'}
    env=_read(p);pub=_key_paths(data)[1].read_text().strip();errs=[]
    if not _verify(env,pub):errs.append('UNIFIED_SIGNATURE')
    q=env.get('payload',{})
    if q.get('schema')!=SCHEMA:errs.append('UNIFIED_SCHEMA')
    if q.get('identity')!=ident:errs.append('UNIFIED_IDENTITY')
    current=_component_hashes(data)
    for k,v in q.get('component_hashes',{}).items():
        if v!=current.get(k):errs.append('COMPONENT_DRIFT:'+k)
    try:
        soul=load_soul(data)
        if sha_obj(soul)!=q.get('soul_core_sha256'):errs.append('SOUL_BINDING')
    except Exception as e:errs.append('SOUL:'+type(e).__name__)
    return {'ok':not errs,'errors':errs,'individual_id':ident,'seq':q.get('seq'),'version':'v1014.4','quick':True}

def audit(data):
    ident=_live_identity(data);p=state_path(data)
    if not p.exists():return {'ok':False,'errors':['UNIFIED_STATE_MISSING']}
    env=_read(p);pub=_key_paths(data)[1].read_text().strip();errs=[]
    if not _verify(env,pub):errs.append('UNIFIED_SIGNATURE')
    q=env.get('payload',{})
    if q.get('schema')!=SCHEMA:errs.append('UNIFIED_SCHEMA')
    if q.get('identity')!=ident:errs.append('UNIFIED_IDENTITY')
    current=_component_hashes(data)
    for folder,module in [('v1022','cognition'),('v1022_ecology','metabolism')]:
        if (Path(data)/folder/'commits').exists():
            try:
                from importlib import import_module
                if not import_module('tukuyo_v1022.'+module).audit(data).get('ok'):errs.append('V1022_'+module.upper()+'_AUDIT')
            except Exception as e:errs.append('V1022_'+module.upper()+'_AUDIT:'+type(e).__name__)
    if (Path(data)/'v1023r'/'commits').exists():
        try:
            from tukuyo_v1023r.life import audit as research_audit
            if not research_audit(data).get('ok'):errs.append('V1023R_RESEARCH_AUDIT')
        except Exception as e:errs.append('V1023R_RESEARCH_AUDIT:'+type(e).__name__)
    # Only compare components that existed at last sync. This forces explicit sync after state changes.
    for k,v in q.get('component_hashes',{}).items():
        if v!=current.get(k):errs.append('COMPONENT_DRIFT:'+k)
    try:
        soul=load_soul(data)
        if sha_obj(soul)!=q.get('soul_core_sha256'):errs.append('SOUL_BINDING')
    except Exception as e:errs.append('SOUL:'+type(e).__name__)
    # Reintegrated legacy layers: these were still present/reachable, but several
    # had fallen outside the unified audit surface in later compact releases.
    if (Path(data)/'v978'/'HEART_STATE.json').exists():
        try:
            from tukuyo_v978.heart_loop import audit as heart_audit
            if not heart_audit(data).get('ok'):errs.append('HEART_AUDIT')
        except Exception as e:errs.append('HEART_AUDIT:'+type(e).__name__)
    if (Path(data)/'v979'/'DEEP_SOUL_CORE.json').exists():
        try:
            from tukuyo_v979.deep_core import audit as deep_soul_audit
            if not deep_soul_audit(data).get('ok'):errs.append('DEEP_SOUL_AUDIT')
        except Exception as e:errs.append('DEEP_SOUL_AUDIT:'+type(e).__name__)
    if (Path(data)/'v982'/'HEAD.json').exists():
        try:
            from tukuyo_v982.continuity_ledger import quick_audit as continuity_ledger_audit
            if not continuity_ledger_audit(data).get('ok'):errs.append('CONTINUITY_LEDGER_AUDIT')
        except Exception as e:errs.append('CONTINUITY_LEDGER_AUDIT:'+type(e).__name__)
    if (Path(data)/'v983'/'HOMEOSTASIS_STATE.json').exists():
        try:
            from tukuyo_v983.homeostasis import audit as homeostasis_audit
            if not homeostasis_audit(data).get('ok'):errs.append('HOMEOSTASIS_AUDIT')
        except Exception as e:errs.append('HOMEOSTASIS_AUDIT:'+type(e).__name__)
    if (Path(data)/'v981'/'BRANCH_REGISTRY.json').exists():
        try:
            from tukuyo_v981.fork_divergence import audit as fork_audit
            if not fork_audit(data).get('ok'):errs.append('FORK_AUDIT')
        except Exception as e:errs.append('FORK_AUDIT:'+type(e).__name__)
    if (Path(data)/'v984'/'FULL_RUNTIME_FORK_ASSAY.json').exists():
        try:
            from tukuyo_v984.full_fork import audit as full_fork_audit
            if not full_fork_audit(data).get('ok'):errs.append('FULL_RUNTIME_FORK_AUDIT')
        except Exception as e:errs.append('FULL_RUNTIME_FORK_AUDIT:'+type(e).__name__)
    if (Path(data)/'v985'/'NARRATIVE_PURPOSE_STATE.json').exists():
        try:
            from tukuyo_v985.narrative_purpose import audit as purpose_audit
            if not purpose_audit(data).get('ok'):errs.append('NARRATIVE_PURPOSE_AUDIT')
        except Exception as e:errs.append('NARRATIVE_PURPOSE_AUDIT:'+type(e).__name__)
    if (Path(data)/'v986'/'LONG_HORIZON_PLAN.json').exists():
        try:
            from tukuyo_v986.long_horizon_plan import audit as plan_audit
            if not plan_audit(data).get('ok'):errs.append('LONG_HORIZON_PLAN_AUDIT')
        except Exception as e:errs.append('LONG_HORIZON_PLAN_AUDIT:'+type(e).__name__)
    if (Path(data)/'v987'/'PLAN_EXECUTION_STATE.json').exists():
        try:
            from tukuyo_v987.plan_executor import audit as execution_audit
            if not execution_audit(data).get('ok'):errs.append('PLAN_EXECUTION_AUDIT')
        except Exception as e:errs.append('PLAN_EXECUTION_AUDIT:'+type(e).__name__)
    if (Path(data)/'v988'/'STRATEGY_STATE.json').exists():
        try:
            from tukuyo_v988.strategy_learning import audit as strategy_audit
            if not strategy_audit(data).get('ok'):errs.append('STRATEGY_AUDIT')
        except Exception as e:errs.append('STRATEGY_AUDIT:'+type(e).__name__)
    if (Path(data)/'v989'/'TEMPORAL_IDENTITY.json').exists():
        try:
            from tukuyo_v989.temporal_identity import audit as temporal_identity_audit
            if not temporal_identity_audit(data).get('ok'):errs.append('TEMPORAL_IDENTITY_AUDIT')
        except Exception as e:errs.append('TEMPORAL_IDENTITY_AUDIT:'+type(e).__name__)
    if (Path(data)/'v990'/'ENVIRONMENT_STATE.json').exists():
        try:
            from tukuyo_v990.closed_environment import audit as environment_audit
            if not environment_audit(data).get('ok'):errs.append('CLOSED_ENVIRONMENT_AUDIT')
        except Exception as e:errs.append('CLOSED_ENVIRONMENT_AUDIT:'+type(e).__name__)
    if (Path(data)/'v991'/'GROUNDED_ORGANISM_STATE.json').exists():
        try:
            from tukuyo_v991.grounded_organism import audit as grounded_audit
            if not grounded_audit(data).get('ok'):errs.append('GROUNDED_ORGANISM_AUDIT')
        except Exception as e:errs.append('GROUNDED_ORGANISM_AUDIT:'+type(e).__name__)
    if (Path(data)/'v992'/'HOLDOUT_ASSAY.json').exists():
        try:
            from tukuyo_v992.holdout import audit as holdout_audit
            if not holdout_audit(data).get('ok'):errs.append('HOLDOUT_ASSAY_AUDIT')
        except Exception as e:errs.append('HOLDOUT_ASSAY_AUDIT:'+type(e).__name__)
    if (Path(data)/'v993'/'RELATION_BOUND_STATE.json').exists():
        try:
            from tukuyo_v993.relation_bound import audit as relation_bound_audit
            if not relation_bound_audit(data).get('ok'):errs.append('RELATION_BOUND_AUDIT')
        except Exception as e:errs.append('RELATION_BOUND_AUDIT:'+type(e).__name__)
    if (Path(data)/'v994'/'SEMANTIC_EVENTS.json').exists():
        try:
            from tukuyo_v994.constructive_semantics import audit as semantics_audit
            if not semantics_audit(data).get('ok'):errs.append('CONSTRUCTIVE_SEMANTICS_AUDIT')
        except Exception as e:errs.append('CONSTRUCTIVE_SEMANTICS_AUDIT:'+type(e).__name__)
    if (Path(data)/'v996'/'CONVERSATION_GROUNDING_EVENTS.jsonl').exists() or (Path(data)/'v996'/'CONVERSATION_EVENT_HEAD.json').exists():
        try:
            from tukuyo_v996.conversational_grounding import audit as conversation_audit
            if not conversation_audit(data).get('ok'):errs.append('CONVERSATION_GROUNDING_AUDIT')
        except Exception as e:errs.append('CONVERSATION_GROUNDING_AUDIT:'+type(e).__name__)
    if (Path(data)/'v998'/'SEMANTIC_INFERENCE_EVENTS.jsonl').exists() or (Path(data)/'v998'/'SEMANTIC_EVENT_HEAD.json').exists():
        try:
            from tukuyo_v998.semantic_inference import audit as semantic_inference_audit
            if not semantic_inference_audit(data).get('ok'):errs.append('SEMANTIC_INFERENCE_AUDIT')
        except Exception as e:errs.append('SEMANTIC_INFERENCE_AUDIT:'+type(e).__name__)
    if (Path(data)/'v999'/'ADAPTIVE_POLICY_ASSAY.json').exists():
        try:
            from tukuyo_v999.adaptive_policy import audit as adaptive_policy_audit
            if not adaptive_policy_audit(data).get('ok'):errs.append('ADAPTIVE_POLICY_AUDIT')
        except Exception as e:errs.append('ADAPTIVE_POLICY_AUDIT:'+type(e).__name__)
    if (Path(data)/'v995'/'OTHER_AGENT_MODELS.json').exists():
        try:
            from tukuyo_v995.other_agent_trust import audit as peer_audit
            if not peer_audit(data).get('ok'):errs.append('OTHER_AGENT_TRUST_AUDIT')
        except Exception as e:errs.append('OTHER_AGENT_TRUST_AUDIT:'+type(e).__name__)
    if (Path(data)/'v1005'/'LAST_VERIFIED_REASONING.json').exists():
        try:
            from tukuyo_v1005.verifier import audit as v1005_audit
            if not v1005_audit(data).get('ok'):errs.append('VERIFIED_REASONING_AUDIT')
        except Exception as e:errs.append('VERIFIED_REASONING_AUDIT:'+type(e).__name__)
    if (Path(data)/'v1006'/'RESEARCH_ASSAY.json').exists():
        try:
            from tukuyo_v1006.research_agent import audit as v1006_audit
            if not v1006_audit(data).get('ok'):errs.append('AUTONOMOUS_RESEARCH_AUDIT')
        except Exception as e:errs.append('AUTONOMOUS_RESEARCH_AUDIT:'+type(e).__name__)
    if (Path(data)/'v1007'/'ORGANISM2_STATE.json').exists():
        try:
            from tukuyo_v1007.organism2 import audit as v1007_audit
            if not v1007_audit(data).get('ok'):errs.append('ORGANISM2_AUDIT')
        except Exception as e:errs.append('ORGANISM2_AUDIT:'+type(e).__name__)
    if (Path(data)/'v1008'/'LAST_CYCLE.json').exists():
        try:
            from tukuyo_v1008.whole_living_cognition import audit as v1008_audit
            if not v1008_audit(data).get('ok'):errs.append('WHOLE_LIVING_COGNITION_AUDIT')
        except Exception as e:errs.append('WHOLE_LIVING_COGNITION_AUDIT:'+type(e).__name__)
    if (Path(data)/'v1009'/'LONG_LIVED_IDENTITY_ASSAY.json').exists():
        try:
            from tukuyo_v1009.long_lived_identity import audit as v1009_audit
            if not v1009_audit(data).get('ok'):errs.append('LONG_LIVED_IDENTITY_AUDIT')
        except Exception as e:errs.append('LONG_LIVED_IDENTITY_AUDIT:'+type(e).__name__)
    if (Path(data)/'v1012'/'MEMORY_COMPACTION_CHECKPOINT.json').exists():
        try:
            from tukuyo_v1012.memory_compaction import audit as v1012_audit
            if not v1012_audit(data).get('ok'):errs.append('MEMORY_COMPACTION_AUDIT')
        except Exception as e:errs.append('MEMORY_COMPACTION_AUDIT:'+type(e).__name__)
    if (Path(data)/'v1016'/'SOCIETY_STATE.json').exists():
        try:
            from tukuyo_v1016.society import audit as v1016_audit
            if not v1016_audit(data).get('ok'):errs.append('MULTI_AGENT_SOCIETY_AUDIT')
        except RecursionError: pass
        except Exception as e:errs.append('MULTI_AGENT_SOCIETY_AUDIT:'+type(e).__name__)
    if (Path(data)/'v1018'/'SUCCESSION_STATE.json').exists():
        try:
            from tukuyo_v1018.succession import audit as v1018_audit
            if not v1018_audit(data).get('ok'):errs.append('V1018_SUCCESSION_AUDIT')
        except RecursionError: pass
        except Exception as e:errs.append('V1018_SUCCESSION_AUDIT:'+type(e).__name__)
    if (Path(data)/'v1020').exists():
        try:
            from tukuyo_v1020.ecology import audit as population_audit
            if not population_audit(data).get('ok'):errs.append('V1020_POPULATION_AUDIT')
        except Exception as e:errs.append('V1020_POPULATION_AUDIT:'+type(e).__name__)
    if (Path(data)/'v1019'/'EVOLUTION_STATE.json').exists():
        try:
            from tukuyo_v1019.evolution import audit as v1019_audit
            if not v1019_audit(data).get('ok'):errs.append('V1019_EVOLUTION_AUDIT')
        except RecursionError: pass
        except Exception as e:errs.append('V1019_EVOLUTION_AUDIT:'+type(e).__name__)
    elif (Path(data)/'v1017'/'SUCCESSION_STATE.json').exists():
        try:
            from tukuyo_v1017.succession import audit as v1017_audit
            if not v1017_audit(data).get('ok'):errs.append('V1017_SUCCESSION_AUDIT')
        except RecursionError: pass
        except Exception as e:errs.append('V1017_SUCCESSION_AUDIT:'+type(e).__name__)
    if (Path(data)/'v1021').exists():
        try:
            from tukuyo_v1021.runtime_bridge import audit as bridge_audit
            if not bridge_audit(data).get('ok'):errs.append('V1021_RUNTIME_BRIDGE_AUDIT')
        except Exception as e:errs.append('V1021_RUNTIME_BRIDGE_AUDIT:'+type(e).__name__)
    if (Path(data)/'v1013'/'REALTIME_EVENT_HEAD.json').exists():
        try:
            from tukuyo_v1013.realtime_continuity import quick_audit as v1013_audit
            # Whole-State checks the current signed realtime head. Full historical chain verification remains
            # in explicit realtime/campaign audits so heartbeat cost does not grow with history length.
            r=v1013_audit(data,subaudits=False)
            if not r.get('ok'):errs.append('REALTIME_CONTINUITY_AUDIT')
        except RecursionError: pass
        except Exception as e:errs.append('REALTIME_CONTINUITY_AUDIT:'+type(e).__name__)
    return {'ok':not errs,'errors':errs,'version':'v977','individual_id':ident['individual_id'],'seq':q.get('seq'),'claim_boundary':q.get('claim_boundary')}

def status(data,base=None):
    s=load_soul(data);org=_organism(data);a=audit(data) if state_path(data).exists() else {'ok':False,'errors':['UNIFIED_STATE_MISSING']}
    return {'ok':a.get('ok',False),'version':'v977','individual_id':s['individual_id'],'lifecycle':org['lifecycle']['status'],'affect':org['affect'],
      'core_values':s['core_values'],'vows':len(s['vows']),'scars':len(s['scars']),'attachments':len(s['attachments']),'soul_update_seq':s['update_seq'],
      'unified_audit':a,'base_status':base,'general_l5':False,'general_l6':False,'consciousness_established':False}
