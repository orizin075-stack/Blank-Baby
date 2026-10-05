from __future__ import annotations
import copy,json
from pathlib import Path
from tukuyo_v977.whole_state import canon,sha_obj,_live_identity,event_path as soul_event_path,legacy_event_path as legacy_soul_event_path,event_head_path as soul_event_head_path
from tukuyo_v993.relation_bound import _derive as derive_relations,_blank as blank_relation,choose as relation_choose,sync as relation_sync,load as relation_load
from tukuyo_common.journal import migrate_boxed_json,load_events,read_from_offset,last_event,prefix_last_event
SCHEMA='tukuyo.v995.other_agent_models/2'
def _read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def _write(p,o):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')
def path(data):return Path(data)/'v995'/'OTHER_AGENT_MODELS.json'
def _new(peer):return {'peer_id':peer,'encounters':0,'trust':0.5,'unresolved_harm':0.0,'raw_unresolved_harm':0.0,'positive_evidence':0.0,'negative_evidence':0.0,'recent_valences':[],'history':[]}
def _apply(m,e):
    v=float(e.get('valence',0));imp=float(e.get('importance',0));kind=str(e.get('kind',''));signed=v*imp;before=m['trust'];m['encounters']+=1;m['raw_unresolved_harm']=float(m.get('raw_unresolved_harm',m.get('unresolved_harm',0.0)))*0.94
    if signed<0:m['negative_evidence']+=abs(signed);m['raw_unresolved_harm']+=abs(signed)*(0.30 if kind in ('betrayal','harm') else 0.18);m['trust']=max(0.0,m['trust']+signed*(0.34 if kind in ('betrayal','harm') else 0.22))
    else:m['positive_evidence']+=signed;m['raw_unresolved_harm']=max(0.0,m['raw_unresolved_harm']-signed*0.09);m['trust']=min(1.0,m['trust']+signed*0.15)
    m['recent_valences']=(m['recent_valences']+[round(v,6)])[-4:]
    for k in ('trust','raw_unresolved_harm','positive_evidence','negative_evidence'):m[k]=round(float(m[k]),6)
    m['history']=(m['history']+[{'seq':e.get('seq'),'kind':kind,'theme':e.get('theme',''),'valence':v,'importance':imp,'trust_before':round(before,6),'trust_after':round(m['trust'],6),'source_event_sha256':e.get('event_sha256')}])[-128:]
def _finish(peers,relation_state):
    out={}
    for peer,m0 in peers.items():
        m=copy.deepcopy(m0);rel=relation_state.get('models',{}).get(peer,blank_relation(peer));floor=min(0.8,float(rel.get('scar_load',0))*0.08);m['unresolved_harm']=max(float(m.get('raw_unresolved_harm',0.0)),floor);m['trend']=round(sum(m['recent_valences'])/len(m['recent_valences']),6) if m['recent_valences'] else 0.0;m['confidence']=round(min(1.0,m['encounters']/6.0),6)
        for k in ('trust','unresolved_harm','raw_unresolved_harm','positive_evidence','negative_evidence'):m[k]=round(float(m[k]),6)
        m['relation_model_sha256']=sha_obj(rel);out[peer]=m
    return out
def _ensure(data):
    sp=soul_event_path(data);migrate_boxed_json(legacy_soul_event_path(data),sp,soul_event_head_path(data),'tukuyo.v1011.soul_event_head/1',sha_obj);return sp
def _derive(data):
    rs=derive_relations(data);sp=_ensure(data);events=load_events(sp);peers={}
    for e in events:
        peer=str(e.get('relation') or '').strip()
        if peer:_apply(peers.setdefault(peer,_new(peer)),e)
    last=events[-1] if events else None
    return {'schema':SCHEMA,'version':'v1011','individual_id':_live_identity(data)['individual_id'],'source_event_count':len(events),'source_event_head_sha256':last.get('event_sha256') if last else None,'source_journal_size':sp.stat().st_size if sp.exists() else 0,'peers':dict(sorted(_finish(peers,rs).items())),'claim_boundary':{'peer_specific_trust_history':True,'trust_repair_is_gradual':True,'incremental_peer_sync':True,'theory_of_mind_established':False,'social_consciousness_established':False}}
def sync(data):
    relation_sync(data);rs=relation_load(data);sp=_ensure(data);ident=_live_identity(data)['individual_id'];p=path(data);live=None
    if p.is_file():
        try:
            x=_read(p);q=dict(x);h=q.pop('state_sha256',None)
            if x.get('schema')==SCHEMA and x.get('individual_id')==ident and h==sha_obj(q):live=x
        except Exception:live=None
    if live is not None:
        try:
            off=int(live.get('source_journal_size',0));last=prefix_last_event(sp,off);head=last.get('event_sha256') if last else None
            if head!=live.get('source_event_head_sha256'):live=None
        except (ValueError,OSError,json.JSONDecodeError):live=None
    if live is None:x=_derive(data)
    else:
        peers={}
        for peer,m0 in live.get('peers',{}).items():
            m=copy.deepcopy(m0)
            for k in ('trend','confidence','relation_model_sha256','unresolved_harm'):m.pop(k,None)
            peers[peer]=m
        suffix,newsize=read_from_offset(sp,int(live.get('source_journal_size',0)))
        for e in suffix:
            peer=str(e.get('relation') or '').strip()
            if peer:_apply(peers.setdefault(peer,_new(peer)),e)
        last=last_event(sp);x={'schema':SCHEMA,'version':'v1011','individual_id':ident,'source_event_count':int(live.get('source_event_count',0))+len(suffix),'source_event_head_sha256':last.get('event_sha256') if last else None,'source_journal_size':newsize,'peers':dict(sorted(_finish(peers,rs).items())),'claim_boundary':{'peer_specific_trust_history':True,'trust_repair_is_gradual':True,'incremental_peer_sync':True,'theory_of_mind_established':False,'social_consciousness_established':False}}
    x['state_sha256']=sha_obj(x);_write(p,x);return {'ok':True,'version':'v1011','peer_count':len(x['peers']),'state':x}
def load(data):
    if not path(data).is_file():sync(data)
    x=_read(path(data));q=dict(x);h=q.pop('state_sha256',None)
    if x.get('schema')!=SCHEMA or h!=sha_obj(q):raise ValueError('V995_STATE_HASH')
    return x
def peer(data,peer_id):sync(data);x=load(data);rel=relation_load(data).get('models',{}).get(str(peer_id),blank_relation(str(peer_id)));return copy.deepcopy(x['peers'].get(str(peer_id),{**_new(str(peer_id)),'trend':0.0,'confidence':0.0,'relation_model_sha256':sha_obj(rel)}))
def choose(data,peer_id,options,context=''):
    base=relation_choose(data,peer_id,options,context);pm=peer(data,peer_id);rows=[];orig={r['id']:r for r in base['scores']}
    for opt in options:
        r=copy.deepcopy(orig[opt['id']]);ex=float(opt.get('relation_exposure',1.0 if opt.get('engages_relation') else 0.0));adj=ex*((pm['trust']-0.5)*0.38-pm['unresolved_harm']*0.34+max(-0.2,min(0.2,pm.get('trend',0.0)*0.12)));r['peer_history_adjustment']=round(adj,6);r['score']=round(r['score']+adj,6);rows.append(r)
    ranked=sorted(rows,key=lambda z:(z['score'],z['id']),reverse=True);return {'ok':True,'version':'v1011','peer_id':peer_id,'context':context,'chosen':ranked[0]['id'],'scores':ranked,'peer_model':pm,'claim_boundary':{'decision_is_peer_specific':True,'tag_change_does_not_reset_peer_history':True,'theory_of_mind_established':False}}
def audit(data):
    try:
        live=load(data);exp=_derive(data);q=dict(live);q.pop('state_sha256',None);errs=[]
        if q!=exp:errs.append('V995_REPLAY_MISMATCH')
        return {'ok':not errs,'version':'v1011','errors':errs,'peer_count':len(live.get('peers',{})),'claim_boundary':live.get('claim_boundary',{})}
    except Exception as e:return {'ok':False,'version':'v1011','errors':[type(e).__name__+':'+str(e)]}
def status(data,peer_id=None):
    a=audit(data)
    if not a['ok']:return a
    x=load(data);return {'ok':True,'version':'v1011','peer':peer(data,peer_id) if peer_id else None,'peers':x['peers'] if peer_id is None else None,'audit':a}
