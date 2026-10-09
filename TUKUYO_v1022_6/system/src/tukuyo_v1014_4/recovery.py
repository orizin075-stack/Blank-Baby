from __future__ import annotations
import base64,json,time,hashlib,os
from pathlib import Path
from tukuyo_common.atomic_fs import atomic_write_bytes,atomic_write_json,durable_unlink

SCHEMA='tukuyo.v1014_4.conversation_txn/2'
# Only mutable materializations/heads are copied. Append-only journals are represented
# by their pre-transaction byte length, so transaction cost does not grow with history.
STATE_FILES=(
 'v977/SOUL_CORE.json','v977/SOUL_EVENT_HEAD.json',
 'v978/HEART_STATE.json','v978/HEART_EVENT_HEAD.json',
 'v998/SEMANTIC_EVENT_HEAD.json','v996/CONVERSATION_EVENT_HEAD.json',
 'v994/SEMANTIC_EVENTS.json',
)
JOURNALS=(
 'v977/SOUL_EVENTS.jsonl','v978/HEART_EVENTS.jsonl',
 'v998/SEMANTIC_INFERENCE_EVENTS.jsonl','v996/CONVERSATION_GROUNDING_EVENTS.jsonl',
)
DERIVED_FILES=(
 'v989/TEMPORAL_IDENTITY.json','v989/SOUL_TRANSITIONS.json',
 'v993/RELATION_BOUND_STATE.json','v995/OTHER_AGENT_MODELS.json','v977/UNIFIED_STATE.json',
)

def marker_path(data):return Path(data)/'v1014_4'/'private'/'CONVERSATION_TXN.json'

def _state_snapshot(data):
    d=Path(data);out={}
    for rel in STATE_FILES:
        p=d/rel
        out[rel]=base64.b64encode(p.read_bytes()).decode() if p.is_file() else None
    return out

def _journal_snapshot(data):
    d=Path(data);out={}
    for rel in JOURNALS:
        p=d/rel;out[rel]={'existed':p.is_file(),'size':p.stat().st_size if p.is_file() else 0}
    return out

def begin_conversation(data,text=''):
    p=marker_path(data);p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():raise ValueError('CONVERSATION_TXN_ALREADY_PENDING')
    atomic_write_json(p,{'schema':SCHEMA,'phase':'PREPARED','created_utc_ns':time.time_ns(),
      'text_sha256':__import__('hashlib').sha256(str(text).encode()).hexdigest(),
      'states':_state_snapshot(data),'journals':_journal_snapshot(data)})
    return p

def commit_conversation(data):
    durable_unlink(marker_path(data))

def _truncate_or_remove(path,meta):
    p=Path(path);existed=bool(meta.get('existed'));size=int(meta.get('size',0))
    if not existed:
        if p.exists():durable_unlink(p)
        return
    if not p.is_file():raise ValueError('CONVERSATION_JOURNAL_MISSING:'+str(p))
    if p.stat().st_size<size:raise ValueError('CONVERSATION_JOURNAL_TRUNCATED:'+str(p))
    with p.open('r+b') as f:f.truncate(size);f.flush();__import__('os').fsync(f.fileno())

def recover_conversation(data):
    d=Path(data);p=marker_path(d)
    if not p.is_file():return {'ok':True,'recovered':False}
    x=json.loads(p.read_text(encoding='utf-8'))
    if x.get('schema') not in (SCHEMA,'tukuyo.v1014_4.conversation_txn/1'):raise ValueError('CONVERSATION_TXN_SCHEMA')
    # Backward compatibility for any v1 marker stranded by a crash during upgrade.
    if 'files' in x:
        snap=x.get('files',{})
        for rel,b64 in snap.items():
            q=d/rel;q.parent.mkdir(parents=True,exist_ok=True);atomic_write_bytes(q,base64.b64decode(b64))
    else:
        for rel,meta in x.get('journals',{}).items():_truncate_or_remove(d/rel,meta)
        for rel,b64 in x.get('states',{}).items():
            q=d/rel
            if b64 is None:
                if q.exists():durable_unlink(q)
            else:
                q.parent.mkdir(parents=True,exist_ok=True);atomic_write_bytes(q,base64.b64decode(b64))
    # Derived caches/materializations are regenerated from the rolled-back canonical journals.
    for rel in DERIVED_FILES:
        q=d/rel
        if q.exists():durable_unlink(q)
    from tukuyo_v989.temporal_identity import sync_transitions
    sync_transitions(d)
    try:
        from tukuyo_v993.relation_bound import sync as relation_sync
        from tukuyo_v995.other_agent_trust import sync as peer_sync
        relation_sync(d);peer_sync(d)
    except Exception:
        pass
    try:
        from tukuyo_v977.whole_state import sync as whole_sync
        whole_sync(d)
    except Exception:
        pass
    durable_unlink(p)
    return {'ok':True,'recovered':True,'action':'CONVERSATION_TXN_ROLLED_BACK'}

def repair_soul_materialization(data):
    from tukuyo_v977.whole_state import _live_identity,_default_soul,_apply_experience_mutation,event_path,legacy_event_path,event_head_path,sha_obj,soul_path,canon
    from tukuyo_common.journal import migrate_boxed_json,load_events
    d=Path(data)
    if not (d/'state'/'integration_state.json').is_file():return {'ok':True,'repaired':False}
    ident=_live_identity(d);ep=event_path(d);migrate_boxed_json(legacy_event_path(d),ep,event_head_path(d),'tukuyo.v1011.soul_event_head/1',sha_obj)
    from tukuyo_common.journal import last_event
    sp=soul_path(d);last=last_event(ep);expected=(last or {}).get('soul_sha256') or sha_obj(_default_soul(ident))
    current_sha=None
    if sp.is_file():
        try:current_sha=sha_obj(json.loads(sp.read_text(encoding='utf-8')))
        except Exception:pass
    # Normal startup is O(1): only replay the entire soul journal when the materialized core actually lags/diverges.
    if current_sha==expected:return _catch_up_derived(d,last)
    evs=load_events(ep);s=_default_soul(ident)
    for i,e in enumerate(evs,1):
        s=_apply_experience_mutation(s,e.get('kind',''),float(e.get('valence',0)),float(e.get('importance',0)),e.get('theme',''),e.get('relation',''),e.get('law',1))
        if sha_obj(s)!=e.get('soul_sha256'):raise ValueError('SOUL_REPLAY_MISMATCH:'+str(i))
    expected=sha_obj(s)
    atomic_write_bytes(sp,canon(s)+b'\n')
    try:
        from tukuyo_v989.temporal_identity import sync_transitions
        sync_transitions(d)
    except Exception:
        # A stale temporal checkpoint may itself reject the repaired materialization;
        # full audit will rebuild/flag if the canonical event chain is invalid.
        pass
    _sync_relations(d)
    return {'ok':True,'repaired':True,'action':'SOUL_MATERIALIZED_FROM_EVENT_CHAIN'}

def _sync_relations(d):
    # the relation and peer models are derived from the soul journal: bring them up to it as well
    try:
        from tukuyo_v993.relation_bound import sync as relation_sync
        from tukuyo_v995.other_agent_trust import sync as peer_sync
        relation_sync(d);peer_sync(d)
    except Exception:
        pass

def _catch_up_derived(d,last):
    """The soul is what its journal says, but the process stopped before the layers derived from the journal followed
    (v989 temporal identity, v993/v995 relation models) - the soul file had been written, the rest had not. Bring them up
    to the journal; the caller then syncs the whole state. Nothing is derived from anything but the canonical journal."""
    if not last:return {'ok':True,'repaired':False}
    tp=d/'v989'/'TEMPORAL_IDENTITY.json'
    try:behind=tp.is_file() and int(json.loads(tp.read_text(encoding='utf-8')).get('source_soul_event_count',0))<int(last.get('seq',0))
    except Exception:behind=False
    if not behind:return {'ok':True,'repaired':False}
    try:
        from tukuyo_v989.temporal_identity import sync_transitions
        sync_transitions(d)
    except Exception:
        return {'ok':True,'repaired':False}
    _sync_relations(d)
    return {'ok':True,'repaired':True,'action':'SOUL_DERIVED_STATE_CAUGHT_UP'}
