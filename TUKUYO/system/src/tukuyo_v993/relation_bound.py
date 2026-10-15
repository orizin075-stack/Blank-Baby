from __future__ import annotations
import copy,json
from pathlib import Path
from tukuyo_v977.whole_state import canon,sha_obj,load_soul,_live_identity,event_path as soul_event_path,legacy_event_path as legacy_soul_event_path,event_head_path as soul_event_head_path
from tukuyo_v978.heart_loop import load as load_heart,_score_option
from tukuyo_common.journal import migrate_boxed_json,load_events,read_from_offset,last_event,prefix_last_event
SCHEMA='tukuyo.v993.relation_bound_state/2'
def _read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def _write(p,o):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')
def path(data):return Path(data)/'v993'/'RELATION_BOUND_STATE.json'
def _blank(peer):return {'peer_id':peer,'encounters':0,'positive_count':0,'negative_count':0,'betrayal_count':0,'harm_count':0,'trust':0.5,'attachment':0.0,'scar_load':0.0,'risk':0.0,'support_load':0.0,'last_source_event_sha256':None}
def _apply_event(m,e):
    v=float(e.get('valence',0));imp=float(e.get('importance',0));kind=str(e.get('kind',''));signed=v*imp;m['encounters']+=1
    if signed>=0:m['positive_count']+=1;m['support_load']+=signed;m['trust']=min(1.0,m['trust']+signed*(0.16 if kind!='vow' else 0.19))
    else:m['negative_count']+=1;m['trust']=max(0.0,m['trust']+signed*(0.34 if kind in ('betrayal','harm') else 0.22))
    if kind=='betrayal' and v<0:m['betrayal_count']+=1;m['scar_load']+=abs(signed)
    if kind=='harm' and v<0:m['harm_count']+=1;m['scar_load']+=abs(signed)
    m['attachment']=max(-1.0,min(1.0,m['attachment']+signed*0.10));m['risk']=max(0.0,min(1.0,m['scar_load']*0.14+max(0.0,0.5-m['trust'])*0.70))
    for k in ('trust','attachment','scar_load','risk','support_load'):m[k]=round(float(m[k]),6)
    m['last_source_event_sha256']=e.get('event_sha256')
def _ensure(data):
    sp=soul_event_path(data);migrate_boxed_json(legacy_soul_event_path(data),sp,soul_event_head_path(data),'tukuyo.v1011.soul_event_head/1',sha_obj);return sp
def _derive(data):
    sp=_ensure(data);events=load_events(sp);models={}
    for e in events:
        peer=str(e.get('relation') or '').strip()
        if peer:_apply_event(models.setdefault(peer,_blank(peer)),e)
    last=events[-1] if events else None
    return {'schema':SCHEMA,'version':'v1011','individual_id':_live_identity(data)['individual_id'],'source_event_count':len(events),'source_event_head_sha256':last.get('event_sha256') if last else None,'source_journal_size':sp.stat().st_size if sp.exists() else 0,'models':dict(sorted(models.items())),'claim_boundary':{'relation_specific_scar_choice_effect':True,'surface_memory_independent':True,'incremental_social_sync':True,'theory_of_mind_established':False,'literal_attachment_established':False}}
def sync(data):
    ident=_live_identity(data);sp=_ensure(data);p=path(data);live=None
    if p.is_file():
        try:
            x=_read(p);q=dict(x);h=q.pop('state_sha256',None)
            if x.get('schema')==SCHEMA and x.get('individual_id')==ident['individual_id'] and h==sha_obj(q):live=x
        except Exception:live=None
    if live is not None:
        try:
            off=int(live.get('source_journal_size',0));last=prefix_last_event(sp,off);head=last.get('event_sha256') if last else None
            if head!=live.get('source_event_head_sha256'):live=None
        except (ValueError,OSError,json.JSONDecodeError):live=None
    if live is None:x=_derive(data)
    else:
        models=copy.deepcopy(live.get('models',{}));suffix,newsize=read_from_offset(sp,int(live.get('source_journal_size',0)))
        for e in suffix:
            peer=str(e.get('relation') or '').strip()
            if peer:_apply_event(models.setdefault(peer,_blank(peer)),e)
        last=last_event(sp);x={'schema':SCHEMA,'version':'v1011','individual_id':ident['individual_id'],'source_event_count':int(live.get('source_event_count',0))+len(suffix),'source_event_head_sha256':last.get('event_sha256') if last else None,'source_journal_size':newsize,'models':dict(sorted(models.items())),'claim_boundary':{'relation_specific_scar_choice_effect':True,'surface_memory_independent':True,'incremental_social_sync':True,'theory_of_mind_established':False,'literal_attachment_established':False}}
    x['state_sha256']=sha_obj(x);_write(p,x);return {'ok':True,'version':'v1011','peer_count':len(x['models']),'state':x}
def load(data):
    if not path(data).is_file():sync(data)
    x=_read(path(data));q=dict(x);h=q.pop('state_sha256',None)
    if x.get('schema')!=SCHEMA or h!=sha_obj(q):raise ValueError('V993_STATE_HASH')
    return x
def model(data,peer):sync(data);return copy.deepcopy(load(data)['models'].get(str(peer),_blank(str(peer))))
def choose(data,peer,options,context=''):
    if not isinstance(options,list) or len(options)<2:raise ValueError('V993_OPTIONS_REQUIRED')
    soul=load_soul(data);heart=load_heart(data);m=model(data,peer);rows=[]
    for opt0 in options:
        opt=copy.deepcopy(opt0);base,parts=_score_option(data,soul,heart,opt);exposure=float(opt.get('relation_exposure',1.0 if opt.get('engages_relation') else 0.0));rel_adj=exposure*((m['trust']-0.5)*0.75+m['attachment']*0.30-m['risk']*0.72);rows.append({'id':opt['id'],'score':round(base+rel_adj,6),'base_score':base,'relation_adjustment':round(rel_adj,6),'relation_exposure':exposure,'parts':parts})
    ranked=sorted(rows,key=lambda z:(z['score'],z['id']),reverse=True);return {'ok':True,'version':'v1011','peer_id':peer,'context':context,'chosen':ranked[0]['id'],'scores':ranked,'relation_model':m,'claim_boundary':{'decision_uses_peer_identity_not_theme_only':True,'theory_of_mind_established':False}}
def audit(data):
    try:
        live=load(data);exp=_derive(data);q=dict(live);q.pop('state_sha256',None);errs=[]
        if q!=exp:errs.append('V993_REPLAY_MISMATCH')
        return {'ok':not errs,'version':'v1011','errors':errs,'peer_count':len(live.get('models',{})),'claim_boundary':live.get('claim_boundary',{})}
    except Exception as e:return {'ok':False,'version':'v1011','errors':[type(e).__name__+':'+str(e)]}
def status(data,peer=None):
    a=audit(data)
    if not a['ok']:return a
    x=load(data);return {'ok':True,'version':'v1011','peer':model(data,peer) if peer else None,'models':x['models'] if peer is None else None,'audit':a}
