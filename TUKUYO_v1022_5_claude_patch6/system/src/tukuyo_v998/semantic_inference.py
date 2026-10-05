from __future__ import annotations
import json,re,unicodedata
from pathlib import Path
from tukuyo_v977.whole_state import canon,sha_obj,_live_identity,event_path as soul_event_path,legacy_event_path as legacy_soul_event_path,event_head_path as soul_event_head_path
from tukuyo_v994.constructive_semantics import context_snapshot
SCHEMA='tukuyo.v998.semantic_events/1';ZERO='0'*64

def _read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def _write(p,o):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')
def path(data):return Path(data)/'v998'/'SEMANTIC_INFERENCE_EVENTS.jsonl'
def legacy_path(data):return Path(data)/'v998'/'SEMANTIC_INFERENCE_EVENTS.json'
def head_path(data):return Path(data)/'v998'/'SEMANTIC_EVENT_HEAD.json'
def _norm(s):return unicodedata.normalize('NFKC',str(s)).lower().strip()

DOMAINS={
 'epistemic':['発見','研究','学習','調査','観察','証拠','定理','証明','ひらめ','謎が解け','理解','分かった','discover','research','learn','evidence','theorem','proof','proved','insight','solved'],
 'betrayal':['裏切','約束を破','欺','騙','betray','broken promise','deceiv'],
 'support':['友情','友人','協力','助け','支援','信頼','仲間','friend','support','collaboration','cooperate','help','trust'],
 'harm':['危険','損傷','傷つ','害','脅威','攻撃','danger','damage','harm','threat','attack'],
 'commitment':['誓','誓約','約束する','決意','vow','oath','pledge','commitment'],
 'truth':['真実','事実','正確','検証','truth','fact','accurate','verify'],
}
NEG_SUFFIX=('ない','なかった','ません','ず','ではない','じゃない','できなかった','失敗した')
FAIL=('失敗','できなかった','解けなかった','証明できなかった','failed','failure','could not','unsolved')

def _cue_negated(raw,start,end):
    around=raw[max(0,start-5):min(len(raw),end+10)]
    return any(n in around for n in NEG_SUFFIX) or bool(re.search(r'\b(?:not|never|no)\b.{0,16}$',raw[max(0,start-20):start]))

def interpret_snapshot(text,ctx):
    raw=_norm(text);features={};matches={};negated=[]
    for dom,terms in DOMAINS.items():
        pos=[]
        for term in terms:
            t=_norm(term);i=raw.find(t)
            if i>=0:
                if _cue_negated(raw,i,i+len(t)):negated.append({'domain':dom,'cue':term})
                else:pos.append(term)
        matches[dom]=pos;features[dom]=round(min(1.0,len(pos)*0.65),6)
    failed=any(x in raw for x in FAIL);features['failure']=1.0 if failed else 0.0
    # Explicit successful epistemic constructions.
    epistemic_success=bool(features['epistemic'] and not failed)
    labels=[]
    if epistemic_success:labels.append({'label':'EPISTEMIC_GAIN','weight':1.0})
    if features['betrayal']:labels.append({'label':'TRUST_VIOLATION','weight':features['betrayal']})
    if features['support']:labels.append({'label':'SOCIAL_SUPPORT','weight':features['support']})
    if features['harm']:labels.append({'label':'INTEGRITY_THREAT','weight':features['harm']})
    if features['commitment']:labels.append({'label':'COMMITMENT','weight':features['commitment']})
    if features['truth']:labels.append({'label':'TRUTH_ORIENTATION','weight':features['truth']})
    if failed:labels.append({'label':'FAILED_OUTCOME','weight':1.0})
    if negated:labels.append({'label':'NEGATED_PROPOSITION','weight':1.0})
    if not labels:labels=[{'label':'UNRESOLVED_EXPERIENCE','weight':1.0}]
    labels=sorted(labels,key=lambda x:(x['weight'],x['label']),reverse=True)
    return {'text':str(text),'normalized':raw,'features':features,'matched_cues':matches,'negated_cues':negated,'meaning_profile':labels,'primary_meaning':labels[0]['label'],
            'composition_rules':['LOCAL_NEGATION_SCOPE','SUCCESS_FAILURE_COMPOSITION','MULTI_CUE_DOMAIN_COMPOSITION','RELATION_CONTEXT']}

def interpret(data,text,relation=''):
    ctx=context_snapshot(data,relation);return {'ok':True,'version':'v998','context_snapshot':ctx,'analysis':interpret_snapshot(text,ctx),
      'claim_boundary':{'bounded_compositional_semantic_inference':True,'negation_scope_improved':True,'general_language_understanding':False}}

def record(data,text,relation=''):
    from tukuyo_common.journal import migrate_boxed_json,last_event,append_event
    migrate_boxed_json(legacy_soul_event_path(data),soul_event_path(data),soul_event_head_path(data),'tukuyo.v1011.soul_event_head/1',sha_obj)
    source=last_event(soul_event_path(data))
    if not source:raise ValueError('V998_SOURCE_SOUL_EVENT_REQUIRED')
    ctx=context_snapshot(data,relation or source.get('relation',''));analysis=interpret_snapshot(text,ctx);p=path(data);hp=head_path(data);ident=_live_identity(data)['individual_id']
    migrate_boxed_json(legacy_path(data),p,hp,'tukuyo.v1011.semantic_event_head/1',sha_obj,'individual_id');last=last_event(p);prev=last.get('event_sha256',ZERO) if last else ZERO;seq=int(last.get('seq',0))+1 if last else 1
    e={'seq':seq,'individual_id':ident,'text':str(text),'relation':relation or source.get('relation',''),'source_soul_event_sha256':source['event_sha256'],'analysis':analysis,'prev_sha256':prev};e['event_sha256']=sha_obj(e);append_event(p,hp,e,'tukuyo.v1011.semantic_event_head/1',sha_obj,ident)
    return {'ok':True,'version':'v1011','analysis':analysis,'event':e}

def audit(data):
    from tukuyo_common.journal import migrate_boxed_json,load_events
    p=path(data);hp=head_path(data);ident=_live_identity(data)['individual_id'];migrate_boxed_json(legacy_path(data),p,hp,'tukuyo.v1011.semantic_event_head/1',sha_obj,'individual_id')
    if not p.is_file():return {'ok':True,'version':'v1011','errors':[],'events':0}
    try:
        prev=ZERO;errs=[];events=load_events(p)
        for i,e in enumerate(events,1):
            if e.get('seq')!=i or e.get('prev_sha256')!=prev or e.get('individual_id')!=ident:errs.append('V998_CHAIN');break
            q=dict(e);h=q.pop('event_sha256',None)
            if h!=sha_obj(q):errs.append('V998_HASH');break
            prev=h
        return {'ok':not errs,'version':'v1011','errors':errs,'events':len(events)}
    except Exception as exc:return {'ok':False,'version':'v1011','errors':[type(exc).__name__+':'+str(exc)]}
