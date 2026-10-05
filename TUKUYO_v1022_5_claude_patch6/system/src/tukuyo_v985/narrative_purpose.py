from __future__ import annotations
import json
from pathlib import Path
from tukuyo_v977.whole_state import canon,sha_obj,_live_identity,load_soul
from tukuyo_v978.heart_loop import load as load_heart
from tukuyo_v983.homeostasis import state_path as homeostasis_path

SCHEMA='tukuyo.v985.narrative_purpose_state/1';EVENT_SCHEMA='tukuyo.v985.narrative_purpose_events/1';ZERO='0'*64
PURPOSES=('PRESERVE_INTEGRITY','SEEK_KNOWLEDGE','MAINTAIN_RELATIONSHIPS','SELF_MAINTENANCE','PRESERVE_TRUTH')

def _read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def _write(p,o):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')
def state_path(data):return Path(data)/'v985'/'NARRATIVE_PURPOSE_STATE.json'
def events_path(data):return Path(data)/'v985'/'NARRATIVE_PURPOSE_EVENTS.json'

def _homeostasis(data):
    p=homeostasis_path(data)
    if not p.exists():return None
    return _read(p)

def _evidence_summary(heart):
    by_meaning={};by_theme={};positive=negative=0.0
    for e in heart.get('episodic_meanings',[]):
        m=e.get('meaning') or 'UNKNOWN';theme=e.get('theme') or m;imp=max(0.0,min(1.0,float(e.get('importance',0))));v=max(-1.0,min(1.0,float(e.get('valence',0))))
        z=by_meaning.setdefault(m,{'count':0,'weighted_valence':0.0,'importance':0.0});z['count']+=1;z['weighted_valence']+=v*imp;z['importance']+=imp
        t=by_theme.setdefault(theme,{'count':0,'weighted_valence':0.0,'importance':0.0});t['count']+=1;t['weighted_valence']+=v*imp;t['importance']+=imp
        if v>=0:positive+=v*imp
        else:negative+=abs(v)*imp
    for box in (by_meaning,by_theme):
        for z in box.values():
            z['weighted_valence']=round(z['weighted_valence'],6);z['importance']=round(z['importance'],6)
    return {'episode_count':len(heart.get('episodic_meanings',[])),'meaning_groups':by_meaning,'theme_groups':by_theme,'positive_mass':round(positive,6),'negative_mass':round(negative,6)}

def _purpose_scores(soul,heart,home,evidence):
    v=soul['core_values'];em=heart['emotion'];mg=evidence['meaning_groups']
    know=max(0.0,float(mg.get('KNOWLEDGE_GAIN',{}).get('weighted_valence',0)))
    threat=max(0.0,-float(mg.get('THREAT_TO_TRUST_OR_INTEGRITY',{}).get('weighted_valence',0)))
    support=max(0.0,float(mg.get('RELATIONSHIP_SUPPORT',{}).get('weighted_valence',0)))
    risk=max(0.0,-float(mg.get('RELATIONSHIP_RISK',{}).get('weighted_valence',0)))
    self_commit=float(mg.get('SELF_COMMITMENT',{}).get('importance',0))
    maint=0.0
    if home:
        n=home.get('needs',{});maint=max([float(n.get(k,0)) for k in ('energy_deficit','reserve_deficit','integrity_deficit','maintenance_pressure','fatigue','perceived_threat')]+[0.0])
    vow_truth=max([float(x.get('strength',0)) for x in soul.get('vows',[]) if x.get('theme') in ('preserve_truth','truth','truthfulness')]+[0.0])
    scores={
      'PRESERVE_INTEGRITY':float(v.get('integrity',0))+min(.65,threat*.08)+float(em.get('threat',0))*.45,
      'SEEK_KNOWLEDGE':float(v.get('curiosity',0))+min(.65,know*.06)+max(0.0,float(em.get('valence',0)))*.10,
      'MAINTAIN_RELATIONSHIPS':float(v.get('relationship',0))+min(.45,support*.08)+float(em.get('trust',0))*.20-min(.20,risk*.03),
      'SELF_MAINTENANCE':float(v.get('survival',0))+maint*.80+float(em.get('threat',0))*.15,
      'PRESERVE_TRUTH':float(v.get('truthfulness',0))+vow_truth*.55+min(.20,self_commit*.03),
    }
    return {k:round(scores[k],6) for k in PURPOSES}

def _narrative(evidence,soul):
    ranked=sorted(evidence['theme_groups'].items(),key=lambda kv:(abs(float(kv[1]['weighted_valence'])),kv[1]['count'],kv[0]),reverse=True)[:8]
    persistent=[{'theme':k,'count':v['count'],'weight':v['weighted_valence']} for k,v in ranked if v['count']>=2 or abs(float(v['weighted_valence']))>=1.0]
    vows=[{'theme':x.get('theme'),'strength':x.get('strength')} for x in soul.get('vows',[])]
    scars=[{'theme':x.get('theme'),'kind':x.get('kind'),'strength':x.get('strength')} for x in soul.get('scars',[])][-16:]
    return {'persistent_themes':persistent,'vows':vows,'scars':scars,'interpretation':'EVIDENCE_BOUNDED_SELF_NARRATIVE_NOT_LITERAL_IDENTITY'}

def _append_event(data,event):
    p=events_path(data);box=_read(p) if p.exists() else {'schema':EVENT_SCHEMA,'individual_id':_live_identity(data)['individual_id'],'events':[]}
    prev=box['events'][-1]['event_sha256'] if box['events'] else ZERO
    e=dict(event);e['seq']=len(box['events'])+1;e['prev_sha256']=prev;e['event_sha256']=sha_obj(e);box['events'].append(e);_write(p,box);return e

def integrate(data):
    ident=_live_identity(data);soul=load_soul(data);heart=load_heart(data);home=_homeostasis(data);ev=_evidence_summary(heart);scores=_purpose_scores(soul,heart,home,ev)
    chosen=max(scores,key=lambda k:(scores[k],k));old=_read(state_path(data)) if state_path(data).exists() else None
    supporting=ev['episode_count'];theme_count=len(ev['theme_groups']);confidence=round(min(1.0,0.15+supporting*.035+min(0.25,theme_count*.025)),6)
    revision_count=int(old.get('revision_count',0)) if old else 0
    if old and old.get('active_purpose')!=chosen:revision_count+=1
    state={
      'schema':SCHEMA,'individual_id':ident['individual_id'],'lineage_id':ident['lineage_id'],'branch_id':ident['branch_id'],
      'source_soul_sha256':sha_obj(soul),'source_heart_sha256':sha_obj(heart),'source_homeostasis_sha256':sha_obj(home) if home else None,
      'evidence':ev,'narrative':_narrative(ev,soul),'purpose_scores':scores,'active_purpose':chosen,'confidence':confidence,
      'revision_count':revision_count,'previous_purpose':old.get('active_purpose') if old else None,
      'claim_boundary':{
        'experience_to_meaning_to_purpose_loop':True,
        'evidence_bounded_narrative_self_model':True,
        'high_level_purpose_only':True,
        'autonomous_external_action':False,
        'open_ended_goal_invention':False,
        'consciousness_established':False,
        'literal_soul_established':False,
      },
    }
    state['state_sha256']=sha_obj(state);_write(state_path(data),state)
    event=_append_event(data,{'active_purpose':chosen,'previous_purpose':state['previous_purpose'],'revision_count':revision_count,'confidence':confidence,'source_heart_sha256':state['source_heart_sha256'],'source_soul_sha256':state['source_soul_sha256'],'state_sha256':state['state_sha256']})
    return {'ok':True,'version':'v985','active_purpose':chosen,'purpose_scores':scores,'confidence':confidence,'revision_count':revision_count,'narrative':state['narrative'],'event':event,'claim_boundary':state['claim_boundary']}

def audit(data):
    p=state_path(data)
    if not p.exists():return {'ok':False,'version':'v985','errors':['V985_STATE_MISSING']}
    errs=[];x=_read(p);q=dict(x);got=q.pop('state_sha256',None)
    if x.get('schema')!=SCHEMA or got!=sha_obj(q):errs.append('V985_STATE_HASH')
    ident=_live_identity(data)
    if any(x.get(k)!=ident[k] for k in ('individual_id','lineage_id','branch_id')):errs.append('V985_IDENTITY')
    ep=events_path(data);prev=ZERO
    if ep.exists():
        box=_read(ep)
        if box.get('schema')!=EVENT_SCHEMA or box.get('individual_id')!=ident['individual_id']:errs.append('V985_EVENT_HEADER')
        for i,e in enumerate(box.get('events',[]),1):
            if e.get('seq')!=i or e.get('prev_sha256')!=prev:errs.append('V985_EVENT_CHAIN');break
            z=dict(e);h=z.pop('event_sha256',None)
            if h!=sha_obj(z):errs.append('V985_EVENT_HASH');break
            prev=h
    soul=load_soul(data);heart=load_heart(data);home=_homeostasis(data)
    stale=(x.get('source_soul_sha256')!=sha_obj(soul) or x.get('source_heart_sha256')!=sha_obj(heart) or x.get('source_homeostasis_sha256')!=(sha_obj(home) if home else None))
    return {'ok':not errs,'version':'v985','errors':errs,'active_purpose':x.get('active_purpose'),'revision_count':x.get('revision_count'),'stale_sources':stale,'claim_boundary':x.get('claim_boundary',{})}

def status(data):
    a=audit(data)
    if not a.get('ok'):return a
    x=_read(state_path(data));return {'ok':True,'version':'v985','active_purpose':x['active_purpose'],'confidence':x['confidence'],'revision_count':x['revision_count'],'purpose_scores':x['purpose_scores'],'narrative':x['narrative'],'stale_sources':a['stale_sources'],'claim_boundary':x['claim_boundary']}
