from __future__ import annotations
import json
from pathlib import Path
from tukuyo_v977.whole_state import load_soul,sha_obj,canon,_live_identity
from tukuyo_v978.heart_loop import load as load_heart,state_path as heart_state_path

SCHEMA='tukuyo.v979.deep_soul_core/1'
def _read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def _write(p,o):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')
def path(data):return Path(data)/'v979'/'DEEP_SOUL_CORE.json'

def consolidate(data):
    ident=_live_identity(data);s=load_soul(data);h=load_heart(data)
    vows=sorted((x['theme'],round(float(x['strength']),6)) for x in s.get('vows',[]))
    scars=sorted((x.get('theme',''),x.get('kind',''),round(float(x.get('strength',0)),6)) for x in s.get('scars',[]))
    attachments=sorted((k,round(float(v),6)) for k,v in s.get('attachments',{}).items() if abs(float(v))>=0.03)
    themes=sorted((k,round(float(v.get('weight',0)),6)) for k,v in s.get('themes',{}).items() if abs(float(v.get('weight',0)))>=0.05)
    identity_themes=[]
    for t,strength in vows:
        identity_themes.append({'theme':t,'source':'VOW','weight':strength})
    for t,k,strength in scars:
        if t:identity_themes.append({'theme':t,'source':'SCAR:'+k,'weight':-strength})
    core={'schema':SCHEMA,'individual_id':ident['individual_id'],'core_values':s['core_values'],'identity_themes':identity_themes,
          'vow_signature':vows,'scar_signature':scars,'attachment_signature':attachments,'theme_signature':themes,
          'soul_sha256':sha_obj(s),'consolidated_from_heart_seq':h['seq'],
          'claim_boundary':{'functional_deep_self':True,'memory_independence_testable':True,'consciousness_established':False}}
    if s.get('trust'):
        # soul law 2: whom it trusts, and how far, is part of the deep self
        from tukuyo_v977.whole_state import trust_record
        core['trust_signature']=sorted((k,trust_record(s,k)) for k in s['trust'])
    core['core_sha256']=sha_obj(core);_write(path(data),core);return {'ok':True,'version':'v979','deep_core':core}

def forget_surface_memory(data):
    h=load_heart(data);before={'episodic_meanings':len(h.get('episodic_meanings',[])),'meaning_weights':len(h.get('meaning_weights',{})),'value_bias':dict(h.get('value_bias',{}))}
    h['episodic_meanings']=[];h['meaning_weights']={};h['value_bias']={};h['last_feedback']=None
    h['self_model']['last_update_reason']='SURFACE_MEMORY_LOSS_SIMULATION'
    _write(heart_state_path(data),h)
    return {'ok':True,'version':'v979','cleared':before,'preserved':['v977/SOUL_CORE.json','v979/DEEP_SOUL_CORE.json']}

def load(data):
    p=path(data)
    if not p.exists():raise ValueError('DEEP_SOUL_NOT_CONSOLIDATED')
    x=_read(p);ident=_live_identity(data)
    if x.get('schema')!=SCHEMA or x.get('individual_id')!=ident['individual_id']:raise ValueError('DEEP_SOUL_IDENTITY_BINDING')
    q=dict(x);got=q.pop('core_sha256',None)
    if got!=sha_obj(q):raise ValueError('DEEP_SOUL_HASH')
    return x

def audit(data):
    try:x=load(data);return {'ok':True,'version':'v979','individual_id':x['individual_id'],'core_sha256':x['core_sha256'],'identity_theme_count':len(x['identity_themes']),'consciousness_established':False}
    except Exception as e:return {'ok':False,'version':'v979','error':type(e).__name__+':'+str(e),'consciousness_established':False}
