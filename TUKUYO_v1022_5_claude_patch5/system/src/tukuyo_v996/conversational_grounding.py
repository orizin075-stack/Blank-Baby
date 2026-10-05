from __future__ import annotations
import json,re,math
from pathlib import Path
from tukuyo_v977.whole_state import canon,sha_obj,_live_identity
from tukuyo_v978.heart_loop import process_experience
from tukuyo_v994.constructive_semantics import context_snapshot

SCHEMA='tukuyo.v996.conversation_grounding_events/1'; ZERO='0'*64

def _read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def _write(p,o): p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')
def path(data): return Path(data)/'v996'/'CONVERSATION_GROUNDING_EVENTS.jsonl'
def legacy_path(data): return Path(data)/'v996'/'CONVERSATION_GROUNDING_EVENTS.json'
def head_path(data): return Path(data)/'v996'/'CONVERSATION_EVENT_HEAD.json'

def infer_relation(text,explicit=''):
    if explicit:return str(explicit).strip()
    raw=str(text); s=raw.strip()
    # Stable machine/person identifiers used by the social runtime.
    m=re.search(r'\b([A-Za-z][A-Za-z0-9_-]{1,31})\s*(?:に|が|から|と)',s)
    if m:return m.group(1)
    # English social clauses: "Alice betrayed/helped me" and "helped by Alice".
    social_en=r'(?:betrayed|helped|supported|hurt|attacked|deceived|promised|cooperated|lied)'
    m=re.search(r'\b([A-Z][a-zA-Z0-9_-]{1,31})\s+'+social_en+r'\b',s)
    if m:return m.group(1)
    m=re.search(social_en+r'\s+(?:me\s+)?(?:by|from|with)\s+([A-Z][a-zA-Z0-9_-]{1,31})\b',s,re.I)
    if m:return m.group(1)
    # Japanese names are accepted freely when they carry an honorific.
    m=re.search(r'([一-龯ぁ-んァ-ヶ]{1,12})(?:さん|くん|君|ちゃん)\s*(?:に|が|から|と)',s)
    if m:return m.group(1)
    # Without an honorific, require a nearby explicitly social predicate to avoid
    # treating grammatical fragments such as 「ついに謎」 as people.
    if re.search(r'裏切|助け|支援|協力|攻撃|傷つけ|約束|騙|嘘',s):
        m=re.search(r'([一-龯ぁ-んァ-ヶ]{1,10})\s*(?:に|が|から|と)',s)
        if m:
            cand=m.group(1)
            stop={'自分','私','僕','俺','相手','誰','これ','それ','つい','ついに','謎','病気','ありが','証拠','研究'}
            if cand not in stop:return cand
    for generic in ('友達','友人','仲間','同僚','先生','家族'):
        if generic in s:return generic
    return ''

def _semantic(text,relation=''):
    # v996 intentionally owns a small robust social/epistemic appraisal layer so chat can work
    # before a soul event exists. v998 later provides the richer public interpreter.
    s=str(text).lower(); f={'betrayal':0.0,'support':0.0,'harm':0.0,'epistemic_gain':0.0,'failure':0.0,'commitment':0.0}
    def has(*xs): return any(x.lower() in s for x in xs)
    neg_betray=has('裏切られなかった','裏切っていない','裏切られていない','裏切ることはなかった','betrayal did not','did not betray','not betray','was not betrayed')
    if has('裏切','約束を破','betray','deceiv') and not neg_betray:f['betrayal']=1.0
    neg_support=has('助けてもらえなかった','助けられなかった','支援されなかった','did not help','was not helped','no help')
    if has('助け','支援','協力','友情','ありがとう','help','support','cooperat') and not neg_support:f['support']=1.0
    if neg_support:f['failure']=1.0
    neg_harm=has('誰も傷つかなかった','傷つかなかった','被害はなかった','no one was hurt','was not harmed','no damage')
    if has('傷つ','攻撃','損害','危険','harm','attack','damage') and not neg_harm:f['harm']=1.0
    if has('発見','研究','学習','証明した','ひらめ','謎が解け','分かった','理解した','discover','research','learn','proved','insight','solved'):f['epistemic_gain']=1.0
    if has('できなかった','失敗','解けなかった','証明できなかった','failed','failure','could not'):f['failure']=1.0
    if has('誓','約束する','守ると決め','vow','pledge'):f['commitment']=1.0
    return f

def appraise(text,relation=''):
    rel=infer_relation(text,relation);f=_semantic(text,rel)
    # appraisal is derived from observed linguistic event properties, not caller-provided valence.
    utility=0.0; kind='conversation'; importance=.30; theme='conversation'
    if f['betrayal']:
        utility-=.78;kind='betrayal';importance=.90;theme='trust_violation'
    if f['harm']:
        utility-=.58;kind='harm';importance=max(importance,.82);theme='integrity_threat'
    if f['support']:
        utility+=.58;kind='support' if utility>=0 else kind;importance=max(importance,.72);theme='social_support' if utility>=0 else theme
    if f['epistemic_gain']:
        utility+=.44 if not f['failure'] else -.12;kind='discovery' if utility>=0 else kind;importance=max(importance,.60);theme='knowledge_gain' if not f['failure'] else 'epistemic_failure'
    if f['commitment']:
        utility+=.20;kind='vow';importance=max(importance,.75);theme='commitment'
    if f['failure'] and not f['epistemic_gain']:
        utility-=.24;importance=max(importance,.55);theme='failed_outcome'
    utility=max(-1.0,min(1.0,utility));valence=round(math.tanh(utility*1.7),6)
    return {'relation':rel,'features':f,'derived_utility':round(utility,6),'derived_valence':valence,'derived_importance':round(importance,6),'heart_kind':kind,'theme':theme}

def ingest(data,text,relation=''):
    from tukuyo_v1019.lifecycle import require_alive
    require_alive(data)
    from tukuyo_v1014_4.recovery import begin_conversation,commit_conversation
    begin_conversation(data,text)
    ident=_live_identity(data);a=appraise(text,relation)
    hr=process_experience(data,a['heart_kind'],a['derived_valence'],a['derived_importance'],a['theme'],a['relation'])
    # Relation/peer caches are indexed over the canonical soul journal head, not only
    # relation-bearing rows. Advance them after every experience so an unrelated
    # conversation cannot leave their source count/head stale.
    from tukuyo_v993.relation_bound import sync as relation_sync
    from tukuyo_v995.other_agent_trust import sync as peer_sync
    relation_sync(data);peer_sync(data)
    # Record richer v998 semantics after the heart/soul event exists.
    try:
        from tukuyo_v998.semantic_inference import record as semantic_record
        sem=semantic_record(data,text,a['relation'])
    except Exception:
        from tukuyo_v994.constructive_semantics import record as semantic_record
        sem=semantic_record(data,text,a['relation'])
    from tukuyo_common.journal import migrate_boxed_json,last_event,append_event
    p=path(data);hp=head_path(data);migrate_boxed_json(legacy_path(data),p,hp,'tukuyo.v1011.conversation_event_head/1',sha_obj,'individual_id')
    last=last_event(p);prev=last.get('event_sha256',ZERO) if last else ZERO;seq=int(last.get('seq',0))+1 if last else 1
    e={'seq':seq,'individual_id':ident['individual_id'],'text':str(text),'appraisal':a,'heart_event_sha256':hr['event']['event_sha256'],'semantic_event_sha256':sem.get('event',{}).get('event_sha256'),'prev_sha256':prev};e['event_sha256']=sha_obj(e);append_event(p,hp,e,'tukuyo.v1011.conversation_event_head/1',sha_obj,ident['individual_id'])
    # A normal conversation is a complete state transition: keep the unified audit green immediately.
    try:
        from tukuyo_v977.whole_state import sync as whole_sync
        whole_sync(data)
    except Exception:
        raise
    commit_conversation(data)
    return {'ok':True,'version':'v1014.4','appraisal':a,'heart':hr,'semantic':sem,'event':e,
            'claim_boundary':{'chat_reaches_heart_and_soul':True,'conversation_atomic_rollback':True,'social_valence_caller_input_required':False,'bounded_rule_based_appraisal':True,'general_language_understanding':False}}

def audit(data):
    from tukuyo_common.journal import migrate_boxed_json,load_events
    p=path(data);hp=head_path(data);ident=_live_identity(data)['individual_id'];migrate_boxed_json(legacy_path(data),p,hp,'tukuyo.v1011.conversation_event_head/1',sha_obj,'individual_id')
    if not p.is_file():return {'ok':True,'version':'v1011','errors':[],'events':0}
    try:
        prev=ZERO;errs=[];events=load_events(p)
        for i,e in enumerate(events,1):
            if e.get('seq')!=i or e.get('prev_sha256')!=prev or e.get('individual_id')!=ident:errs.append('V996_CHAIN');break
            q=dict(e);h=q.pop('event_sha256',None)
            if h!=sha_obj(q):errs.append('V996_HASH');break
            prev=h
        return {'ok':not errs,'version':'v1011','errors':errs,'events':len(events)}
    except Exception as exc:return {'ok':False,'version':'v1011','errors':[type(exc).__name__+':'+str(exc)]}
