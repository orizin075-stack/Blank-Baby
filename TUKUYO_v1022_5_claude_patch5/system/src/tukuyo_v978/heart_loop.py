from __future__ import annotations
import hashlib,json,time
from pathlib import Path
from tukuyo_v977.whole_state import load_soul,experience as soul_experience,sha_obj,canon,_live_identity

ZERO='0'*64
SCHEMA='tukuyo.v978.heart_state/1'
EVENT_SCHEMA='tukuyo.v978.heart_events/1'

def _read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def _write(p,o):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')
def root(data): return Path(data)/'v978'
def state_path(data): return root(data)/'HEART_STATE.json'
def events_path(data): return root(data)/'HEART_EVENTS.jsonl'
def legacy_events_path(data): return root(data)/'HEART_EVENTS.json'
def event_head_path(data): return root(data)/'HEART_EVENT_HEAD.json'

def _default(data):
    ident=_live_identity(data);s=load_soul(data)
    return {'schema':SCHEMA,'individual_id':ident['individual_id'],'seq':0,
      'emotion':{'valence':0.0,'arousal':0.15,'trust':0.5,'threat':0.0},
      'meaning_weights':{},'episodic_meanings':[],
      'self_model':{'traits':{'curious':s['core_values']['curiosity'],'truth_oriented':s['core_values']['truthfulness'],'integrity_oriented':s['core_values']['integrity']},'last_update_reason':'INIT'},
      'value_bias':{},'active_goal':None,'last_action':None,'last_feedback':None,
      'soul_sha256':sha_obj(s),'claim_boundary':{'functional_heart_loop':True,'consciousness_established':False,'literal_emotion_established':False}}

def load(data):
    p=state_path(data);ident=_live_identity(data)
    if not p.exists():
        x=_default(data);_write(p,x);return x
    x=_read(p)
    if x.get('schema')!=SCHEMA or x.get('individual_id')!=ident['individual_id']: raise ValueError('HEART_IDENTITY_BINDING')
    return x

def _append(data,event):
    from tukuyo_common.journal import migrate_boxed_json,last_event,append_event
    p=events_path(data);hp=event_head_path(data);ident=_live_identity(data)['individual_id'];migrate_boxed_json(legacy_events_path(data),p,hp,'tukuyo.v1011.heart_event_head/1',sha_obj,'individual_id')
    last=last_event(p);prev=last.get('event_sha256',ZERO) if last else ZERO;seq=int(last.get('seq',0))+1 if last else 1
    e=dict(event);e['seq']=seq;e['prev_sha256']=prev;e['event_sha256']=sha_obj(e);append_event(p,hp,e,'tukuyo.v1011.heart_event_head/1',sha_obj,ident);return e

def _meaning(kind,valence,importance,theme,relation):
    if kind in ('betrayal','harm') and valence<0:return 'THREAT_TO_TRUST_OR_INTEGRITY'
    if kind in ('discovery','learning') and valence>=0:return 'KNOWLEDGE_GAIN'
    if kind=='vow':return 'SELF_COMMITMENT'
    if relation and valence>0:return 'RELATIONSHIP_SUPPORT'
    if relation and valence<0:return 'RELATIONSHIP_RISK'
    return 'SALIENT_EXPERIENCE' if importance>=0.5 else 'LOW_SALIENCE_EXPERIENCE'


def _decision_core_values(data,soul):
    """Merge bounded inherited v1017+ succession values into live decisions.

    Import lazily so older standalone roots keep working. The succession layer
    already combines inherited bias with this individual's own soul delta.
    """
    try:
        from tukuyo_v1018.succession import effective_values
        return effective_values(data)
    except Exception:
        return dict(soul['core_values'])

def _derive_goal(soul,h,data=None):
    e=h['emotion'];v=_decision_core_values(data,soul) if data is not None else soul['core_values'];candidates={
      'PRESERVE_INTEGRITY':v['integrity']+e['threat']*0.65,
      'SEEK_KNOWLEDGE':v['curiosity']+max(0,e['valence'])*0.2,
      'MAINTAIN_RELATIONSHIPS':v['relationship']+e['trust']*0.35,
      'SELF_MAINTENANCE':v['survival']+e['threat']*0.35,
      'PRESERVE_TRUTH':v['truthfulness']+abs(e['valence'])*0.05,
    }
    goal=max(candidates,key=lambda k:(candidates[k],k))
    return {'goal':goal,'score':round(candidates[goal],6),'candidate_scores':{k:round(x,6) for k,x in candidates.items()}}

def process_experience(data,kind,valence,importance,theme='',relation=''):
    from tukuyo_v1019.lifecycle import require_alive
    require_alive(data)
    valence=float(valence);importance=float(importance)
    if not -1<=valence<=1 or not 0<=importance<=1: raise ValueError('HEART_EXPERIENCE_RANGE')
    sr=soul_experience(data,kind,valence,importance,theme,relation);soul=sr['soul'];h=load(data);h['seq']+=1
    meaning=_meaning(kind,valence,importance,theme,relation)
    em=h['emotion'];alpha=0.15+0.35*importance
    em['valence']=round(max(-1,min(1,em['valence']*(1-alpha)+valence*alpha)),6)
    em['arousal']=round(max(0,min(1,em['arousal']*0.75+importance*0.35)),6)
    if kind in ('betrayal','harm'): em['trust']=round(max(0,em['trust']-importance*abs(valence)*0.25),6);em['threat']=round(min(1,em['threat']+importance*abs(valence)*0.35),6)
    elif relation and valence>0: em['trust']=round(min(1,em['trust']+importance*valence*0.18),6);em['threat']=round(max(0,em['threat']-importance*0.12),6)
    else: em['threat']=round(max(0,em['threat']-0.03),6)
    key=theme or meaning;h['meaning_weights'][key]=round(max(-3,min(3,h['meaning_weights'].get(key,0.0)+valence*importance)),6)
    mem={'seq':h['seq'],'kind':kind,'theme':theme,'relation':relation,'meaning':meaning,'valence':valence,'importance':importance}
    h['episodic_meanings']=(h['episodic_meanings']+[mem])[-128:]
    # Slow value bias from meaning rather than direct event labels.
    if meaning=='KNOWLEDGE_GAIN':h['value_bias']['curiosity']=round(min(0.35,h['value_bias'].get('curiosity',0)+max(0,valence)*importance*0.04),6)
    if meaning=='THREAT_TO_TRUST_OR_INTEGRITY':h['value_bias']['integrity']=round(min(0.35,h['value_bias'].get('integrity',0)+importance*abs(valence)*0.05),6)
    h['self_model']={'traits':{'curious':round(min(1,soul['core_values']['curiosity']+h['value_bias'].get('curiosity',0)),6),'truth_oriented':soul['core_values']['truthfulness'],'integrity_oriented':round(min(1,soul['core_values']['integrity']+h['value_bias'].get('integrity',0)),6),'social_trust':em['trust']},'last_update_reason':meaning}
    h['active_goal']=_derive_goal(soul,h,data);h['soul_sha256']=sha_obj(soul)
    _write(state_path(data),h)
    ev=_append(data,{'individual_id':h['individual_id'],'type':'EXPERIENCE_LOOP','kind':kind,'theme':theme,'relation':relation,'meaning':meaning,'emotion':dict(em),'active_goal':h['active_goal'],'heart_sha256':sha_obj(h),'soul_event_sha256':sr['event']['event_sha256']})
    # Every canonical soul event advances the source journal observed by the
    # relation/peer caches, including non-social grounded experiences. Keep the
    # incremental heads current even when relation is empty.
    try:
        from tukuyo_v993.relation_bound import sync as relation_sync
        from tukuyo_v995.other_agent_trust import sync as peer_sync
        relation_sync(data);peer_sync(data)
    except ImportError:
        pass
    return {'ok':True,'version':'v978','meaning':meaning,'emotion':em,'self_model':h['self_model'],'active_goal':h['active_goal'],'event':ev}

def _score_option(data,soul,h,opt):
    sig=opt.get('signals',{});score=0.0;parts={}
    merged=dict(_decision_core_values(data,soul))
    for k,v in h.get('value_bias',{}).items(): merged[k]=max(0,min(1,merged.get(k,0)+float(v)))
    for k,w in merged.items():
        c=float(sig.get(k,0));parts[k]=round(w*c,6);score+=w*c
    score+=float(sig.get('trust',0))*h['emotion']['trust']*0.35
    score-=float(sig.get('threat',0))*(0.3+h['emotion']['threat']*0.7)
    # persistent themes/scars influence unknown choices, but bounded.
    for scar in soul.get('scars',[]):
        if scar.get('theme') and scar['theme'] in opt.get('themes',[]): score-=min(0.5,float(scar.get('strength',0))*0.25)
    for vow in soul.get('vows',[]):
        if vow.get('theme') and vow['theme'] in opt.get('themes',[]): score+=min(0.5,float(vow.get('strength',0))*0.25)
    return round(score,6),parts

def choose(data,options,context=''):
    from tukuyo_v1019.lifecycle import require_alive
    require_alive(data)
    if not isinstance(options,list) or len(options)<2: raise ValueError('HEART_OPTIONS_REQUIRED')
    ids=[o.get('id') for o in options]
    if any(not isinstance(x,str) or not x for x in ids) or len(set(ids))!=len(ids):raise ValueError('HEART_OPTION_IDS')
    soul=load_soul(data);h=load(data);scored=[]
    for o in options:
        score,parts=_score_option(data,soul,h,o);scored.append({'id':o['id'],'score':score,'parts':parts})
    ranked=sorted(scored,key=lambda x:(x['score'],x['id']),reverse=True);chosen=ranked[0]
    h['seq']+=1;h['last_action']={'context':context,'chosen':chosen['id'],'scores':ranked};_write(state_path(data),h)
    ev=_append(data,{'individual_id':h['individual_id'],'type':'ACTION_SELECTION','context':context,'chosen':chosen['id'],'scores':ranked,'heart_sha256':sha_obj(h)})
    return {'ok':True,'version':'v978','chosen':chosen['id'],'scores':ranked,'active_goal':h.get('active_goal'),'event':ev}

def feedback(data,action_id,outcome_valence,importance,theme=''):
    from tukuyo_v1019.lifecycle import require_alive
    require_alive(data)
    h=load(data)
    if not h.get('last_action') or h['last_action'].get('chosen')!=action_id: raise ValueError('HEART_FEEDBACK_ACTION_BINDING')
    res=process_experience(data,'action_feedback',float(outcome_valence),float(importance),theme or action_id,'')
    h=load(data);h['last_feedback']={'action_id':action_id,'outcome_valence':float(outcome_valence),'importance':float(importance),'theme':theme};_write(state_path(data),h)
    return {'ok':True,'feedback':h['last_feedback'],'loop_result':res}

def audit(data):
    h=load(data);s=load_soul(data);errs=[]
    if h.get('soul_sha256')!=sha_obj(s):errs.append('HEART_SOUL_DRIFT')
    from tukuyo_common.journal import migrate_boxed_json,load_events
    p=events_path(data);hp=event_head_path(data);migrate_boxed_json(legacy_events_path(data),p,hp,'tukuyo.v1011.heart_event_head/1',sha_obj,'individual_id')
    if p.exists():
        prev=ZERO
        for i,e in enumerate(load_events(p),1):
            if e.get('seq')!=i or e.get('prev_sha256')!=prev:errs.append('HEART_EVENT_CHAIN');break
            q=dict(e);got=q.pop('event_sha256',None)
            if got!=sha_obj(q):errs.append('HEART_EVENT_HASH');break
            prev=got
    return {'ok':not errs,'version':'v978','errors':errs,'individual_id':h['individual_id'],'seq':h['seq'],'active_goal':h.get('active_goal'),'claim_boundary':h['claim_boundary']}

def status(data):
    h=load(data);a=audit(data)
    return {'ok':a['ok'],'version':'v978','individual_id':h['individual_id'],'emotion':h['emotion'],'active_goal':h.get('active_goal'),'self_model':h['self_model'],'meaning_count':len(h['episodic_meanings']),'last_action':h.get('last_action'),'audit':a,'general_l5':False,'general_l6':False,'consciousness_established':False}
