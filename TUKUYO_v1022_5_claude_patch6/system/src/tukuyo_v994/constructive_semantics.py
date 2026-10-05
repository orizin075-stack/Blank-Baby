from __future__ import annotations
import json,re,unicodedata
from pathlib import Path
from tukuyo_v977.whole_state import canon,sha_obj,load_soul,_live_identity,event_path as soul_event_path,legacy_event_path as legacy_soul_event_path,event_head_path as soul_event_head_path
from tukuyo_v993.relation_bound import model as relation_model

SCHEMA='tukuyo.v994.semantic_events/1';ZERO='0'*64
CUES={
 'epistemic':['発見','学習','勉強','研究','調査','観察','知識','証拠','learning','learn','study','research','discovery','discover','investigate','observe','evidence'],
 'betrayal':['裏切','約束を破','欺','騙','betray','broken promise','deceiv'],
 'support':['友情','友人','協力','助け','支援','信頼','仲間','friend','support','collaboration','cooperate','help','trust'],
 'integrity_threat':['危険','損傷','傷つ','害','脅威','攻撃','danger','damage','harm','threat','attack'],
 'commitment':['誓','誓約','約束','決意','vow','oath','pledge','commitment'],
 'truth':['真実','事実','正確','検証','truth','fact','accurate','verify'],
 'resource':['資源','食料','蓄え','エネルギー','resource','food','reserve','energy'],
}
NEG=['ない','なかった','できなかった','失敗','not ','no ','failed','failure','without']

def _read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def _write(p,o):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')
def path(data):return Path(data)/'v994'/'SEMANTIC_EVENTS.json'
def _norm(s):return unicodedata.normalize('NFKC',str(s)).lower().strip()

def context_snapshot(data,relation=''):
    s=load_soul(data);vocab=sorted(set(list(s.get('themes',{}))+[x.get('theme','') for x in s.get('vows',[]) if x.get('theme')]))
    rel=relation_model(data,relation) if relation else None
    return {'soul_vocabulary':vocab[-128:],'relation':str(relation),'relation_context':rel}

def interpret_snapshot(text,ctx):
    raw=_norm(text);scores={k:0.0 for k in CUES};matches={k:[] for k in CUES};neg=any(x in raw for x in NEG)
    for k,terms in CUES.items():
        for term in terms:
            t=_norm(term)
            if t and t in raw:
                matches[k].append(term);scores[k]+=1.0
    # Negation/failure does not erase the domain; it changes the compositional interpretation.
    if neg:
        scores['failure_or_negation']=1.0
        scores['epistemic']=scores['epistemic']*0.45
        scores['support']=scores['support']*0.35
    self_hits=[]
    for term in ctx.get('soul_vocabulary',[]):
        if term and _norm(term) in raw:self_hits.append(term)
    scores['self_relevance']=min(1.0,len(self_hits)*0.35)
    rel=ctx.get('relation_context') or {}
    scores['relational_risk_context']=round(float(rel.get('risk',0.0)),6)
    scores['relational_affiliation_context']=round(max(0.0,float(rel.get('attachment',0.0))),6)
    labels=[]
    mapping={'epistemic':'EPISTEMIC_CONTENT','betrayal':'TRUST_VIOLATION','support':'SOCIAL_SUPPORT','integrity_threat':'INTEGRITY_THREAT',
             'commitment':'COMMITMENT','truth':'TRUTH_ORIENTATION','resource':'RESOURCE_STATE','self_relevance':'SELF_THEME_RESONANCE'}
    for k,label in mapping.items():
        if float(scores.get(k,0))>0:labels.append({'label':label,'weight':round(float(scores[k]),6)})
    if neg:labels.append({'label':'NEGATED_OR_FAILED_OUTCOME','weight':1.0})
    if not labels:labels=[{'label':'UNRESOLVED_EXPERIENCE','weight':1.0}]
    labels=sorted(labels,key=lambda x:(x['weight'],x['label']),reverse=True)
    return {'text':str(text),'normalized':raw,'features':{k:round(float(v),6) for k,v in scores.items()},'matched_cues':matches,
            'matched_soul_vocabulary':self_hits,'meaning_profile':labels,'primary_meaning':labels[0]['label'],
            'composition_rules':['MULTI_CUE_ACCUMULATION','NEGATION_MODULATION','SOUL_VOCABULARY_MATCH','RELATION_CONTEXT_BINDING']}

def interpret(data,text,relation=''):
    ctx=context_snapshot(data,relation);return {'ok':True,'version':'v994','context_snapshot':ctx,'analysis':interpret_snapshot(text,ctx),
        'claim_boundary':{'multilingual_bounded_semantic_composition':True,'free_language_understanding':False,'general_semantics':False}}

def record(data,text,relation=''):
    from tukuyo_common.journal import migrate_boxed_json,last_event
    sp=soul_event_path(data);migrate_boxed_json(legacy_soul_event_path(data),sp,soul_event_head_path(data),'tukuyo.v1011.soul_event_head/1',sha_obj);source=last_event(sp)
    if not source:raise ValueError('V994_SOURCE_SOUL_EVENT_REQUIRED')
    ctx=context_snapshot(data,relation or source.get('relation',''));analysis=interpret_snapshot(text,ctx)
    p=path(data);box=_read(p) if p.is_file() else {'schema':SCHEMA,'individual_id':_live_identity(data)['individual_id'],'events':[]}
    prev=box['events'][-1]['event_sha256'] if box['events'] else ZERO
    e={'seq':len(box['events'])+1,'individual_id':box['individual_id'],'text':str(text),'relation':relation or source.get('relation',''),
       'source_soul_event_sha256':source['event_sha256'],'source_valence':source.get('valence'),'source_importance':source.get('importance'),
       'context_snapshot':ctx,'analysis':analysis,'prev_sha256':prev};e['event_sha256']=sha_obj(e);box['events'].append(e);_write(p,box)
    return {'ok':True,'version':'v994','event':e,'analysis':analysis}

def audit(data):
    p=path(data)
    if not p.is_file():return {'ok':True,'version':'v994','errors':[],'event_count':0}
    try:
        from tukuyo_common.journal import migrate_boxed_json,load_events
        box=_read(p);errs=[];prev=ZERO;spth=soul_event_path(data);migrate_boxed_json(legacy_soul_event_path(data),spth,soul_event_head_path(data),'tukuyo.v1011.soul_event_head/1',sha_obj);valid={e['event_sha256'] for e in load_events(spth)}
        if box.get('schema')!=SCHEMA or box.get('individual_id')!=_live_identity(data)['individual_id']:errs.append('V994_IDENTITY')
        for i,e in enumerate(box.get('events',[]),1):
            if e.get('seq')!=i or e.get('prev_sha256')!=prev:errs.append('V994_CHAIN');break
            q=dict(e);got=q.pop('event_sha256',None)
            if got!=sha_obj(q):errs.append('V994_HASH');break
            if e.get('source_soul_event_sha256') not in valid:errs.append('V994_SOURCE_BINDING');break
            if e.get('analysis')!=interpret_snapshot(e.get('text',''),e.get('context_snapshot',{})):errs.append('V994_REPLAY');break
            prev=got
        return {'ok':not errs,'version':'v994','errors':errs,'event_count':len(box.get('events',[])),
                'claim_boundary':{'bounded_compositional_semantics':True,'general_language_understanding':False}}
    except Exception as e:return {'ok':False,'version':'v994','errors':[type(e).__name__+':'+str(e)]}

def status(data):
    a=audit(data);box=_read(path(data)) if path(data).is_file() else {'events':[]}
    return {'ok':a['ok'],'version':'v994','event_count':len(box['events']),'last':box['events'][-1] if box['events'] else None,'audit':a}
