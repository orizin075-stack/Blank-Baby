from __future__ import annotations
import json
from pathlib import Path
from tukuyo_v977.whole_state import (
    canon, sha_obj, _live_identity, _default_soul, _apply_experience_mutation,
    load_soul, event_path as soul_event_path, legacy_event_path as legacy_soul_event_path, event_head_path as soul_event_head_path,
)

SCHEMA='tukuyo.v989.temporal_soul_identity/1'
TRANSITION_SCHEMA='tukuyo.v989.soul_transition_chain/1'
ZERO='0'*64


def _read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def _write(p,o):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')


def root(data): return Path(data)/'v989'
def state_path(data): return root(data)/'TEMPORAL_IDENTITY.json'
def transitions_path(data): return root(data)/'SOUL_TRANSITIONS.json'


def _load_soul_events(data):
    from tukuyo_common.journal import migrate_boxed_json,load_events
    p=soul_event_path(data);hp=soul_event_head_path(data);migrate_boxed_json(legacy_soul_event_path(data),p,hp,'tukuyo.v1011.soul_event_head/1',sha_obj)
    return {'schema':'tukuyo.v977.soul_events/1','events':load_events(p)}


def _verify_event_chain(events,ident):
    errors=[];prev=ZERO
    for i,e in enumerate(events,1):
        if e.get('seq')!=i: errors.append(f'SOUL_EVENT_SEQ:{i}')
        if e.get('individual_id')!=ident['individual_id']: errors.append(f'SOUL_EVENT_IDENTITY:{i}')
        if e.get('prev_sha256')!=prev: errors.append(f'SOUL_EVENT_PREV:{i}')
        q=dict(e);got=q.pop('event_sha256',None)
        if got!=sha_obj(q): errors.append(f'SOUL_EVENT_HASH:{i}')
        prev=got or ZERO
    return errors


def _replay(data):
    ident=_live_identity(data);box=_load_soul_events(data);events=box['events']
    errors=_verify_event_chain(events,ident)
    soul=_default_soul(ident);origin_sha=sha_obj(soul);prev_transition=ZERO;transitions=[]
    for i,e in enumerate(events,1):
        before=sha_obj(soul)
        try:
            soul=_apply_experience_mutation(
                soul,e.get('kind',''),float(e.get('valence',0)),float(e.get('importance',0)),
                e.get('theme',''),e.get('relation',''))
        except Exception as exc:
            errors.append(f'REPLAY_EVENT:{i}:{type(exc).__name__}')
            break
        after=sha_obj(soul)
        if after!=e.get('soul_sha256'):
            errors.append(f'HISTORICAL_REPLAY_MISMATCH:{i}')
        t={
            'schema':'tukuyo.v989.soul_transition/1',
            'seq':i,
            'individual_id':ident['individual_id'],
            'lineage_id':ident['lineage_id'],
            'branch_id':ident['branch_id'],
            'from_soul_sha256':before,
            'to_soul_sha256':after,
            'source_event_seq':i,
            'source_event_sha256':e.get('event_sha256'),
            'kind':e.get('kind',''),
            'theme':e.get('theme',''),
            'relation':e.get('relation',''),
            'previous_transition_sha256':prev_transition,
        }
        t['transition_sha256']=sha_obj(t);prev_transition=t['transition_sha256'];transitions.append(t)
    current=load_soul(data);current_sha=sha_obj(current)
    expected=transitions[-1]['to_soul_sha256'] if transitions else origin_sha
    if current_sha!=expected: errors.append('ILLEGAL_STATE_JUMP')
    return ident,origin_sha,current_sha,events,transitions,errors


def _validated_existing_chain(data,ident,events,origin_sha):
    """Return an append-safe prior chain or None. Full replay remains audit authority."""
    sp,tp=state_path(data),transitions_path(data)
    if not sp.exists() or not tp.exists(): return None
    try:
        old=_read(sp); chain=_read(tp)
        oq=dict(old); oh=oq.pop('state_sha256',None)
        cq=dict(chain); ch=cq.pop('chain_sha256',None)
        if oh!=sha_obj(oq) or ch!=sha_obj(cq): return None
        oi=old.get('origin_identity',{})
        if oi.get('individual_id')!=ident['individual_id'] or oi.get('lineage_id')!=ident['lineage_id'] or oi.get('branch_id')!=ident['branch_id']: return None
        if old.get('origin_soul_sha256')!=origin_sha or chain.get('origin_soul_sha256')!=origin_sha:return None
        n=int(chain.get('transition_count',-1)); ts=chain.get('transitions',[])
        if n!=len(ts) or n>len(events):return None
        # Prefix is anchored by the old transition's source event hash. New events remain append-only.
        if n:
            if ts[-1].get('source_event_sha256')!=events[n-1].get('event_sha256'):return None
            if ts[-1].get('to_soul_sha256')!=events[n-1].get('soul_sha256'):return None
            if chain.get('head_transition_sha256')!=ts[-1].get('transition_sha256'):return None
        elif chain.get('head_transition_sha256')!=ZERO:return None
        return chain
    except Exception:
        return None


def sync_transitions(data):
    ident=_live_identity(data); box=_load_soul_events(data); events=box['events']
    event_errors=_verify_event_chain(events,ident)
    if event_errors: raise ValueError('TEMPORAL_IDENTITY_PRECHECK:'+','.join(event_errors[:8]))
    origin_sha=sha_obj(_default_soul(ident)); current=load_soul(data); current_sha=sha_obj(current)
    chain=_validated_existing_chain(data,ident,events,origin_sha)
    if chain is None:
        # Bootstrap/recovery path: expensive deterministic replay, used only when no trusted checkpoint exists.
        ident,origin_sha,current_sha,events,transitions,errors=_replay(data)
        if errors: raise ValueError('TEMPORAL_IDENTITY_PRECHECK:'+','.join(errors[:8]))
    else:
        transitions=list(chain.get('transitions',[])); prev_transition=chain.get('head_transition_sha256',ZERO)
        before=transitions[-1]['to_soul_sha256'] if transitions else origin_sha
        # Append only the unseen suffix. Each canonical soul event already commits the resulting soul SHA.
        for i in range(len(transitions),len(events)):
            e=events[i]; after=e.get('soul_sha256')
            t={'schema':'tukuyo.v989.soul_transition/1','seq':i+1,'individual_id':ident['individual_id'],
               'lineage_id':ident['lineage_id'],'branch_id':ident['branch_id'],'from_soul_sha256':before,
               'to_soul_sha256':after,'source_event_seq':i+1,'source_event_sha256':e.get('event_sha256'),
               'kind':e.get('kind',''),'theme':e.get('theme',''),'relation':e.get('relation',''),
               'previous_transition_sha256':prev_transition}
            t['transition_sha256']=sha_obj(t); transitions.append(t);prev_transition=t['transition_sha256'];before=after
        expected=transitions[-1]['to_soul_sha256'] if transitions else origin_sha
        if current_sha!=expected: raise ValueError('TEMPORAL_IDENTITY_PRECHECK:ILLEGAL_STATE_JUMP')
    old=_read(state_path(data)) if state_path(data).exists() else None
    if old:
        old_origin=old.get('origin_identity',{})
        if old_origin.get('individual_id')!=ident['individual_id'] or old_origin.get('lineage_id')!=ident['lineage_id'] or old_origin.get('branch_id')!=ident['branch_id']:
            raise ValueError('TEMPORAL_ORIGIN_IDENTITY_DRIFT')
        if old.get('origin_soul_sha256')!=origin_sha: raise ValueError('TEMPORAL_ORIGIN_SOUL_DRIFT')
    chain={'schema':TRANSITION_SCHEMA,'individual_id':ident['individual_id'],'lineage_id':ident['lineage_id'],'branch_id':ident['branch_id'],
           'origin_soul_sha256':origin_sha,'transition_count':len(transitions),'head_transition_sha256':transitions[-1]['transition_sha256'] if transitions else ZERO,
           'transitions':transitions}
    chain['chain_sha256']=sha_obj(chain);_write(transitions_path(data),chain)
    state={'schema':SCHEMA,'origin_identity':ident,'origin_soul_sha256':origin_sha,'current_soul_sha256':current_sha,
           'transition_count':len(transitions),'transition_head_sha256':chain['head_transition_sha256'],'source_soul_event_count':len(events),
           'checkpoint_mode':'INCREMENTAL_APPEND_WITH_FULL_REPLAY_AUDIT',
           'same_identity_rule':{'same_origin':True,'valid_transition_chain':True,'no_illegal_state_jump':True,'lineage_continuity':True},
           'claim_boundary':{'functional_temporal_self_identity':True,'identity_allows_lawful_soul_change':True,'causal_transition_chain_verified':True,
                             'incremental_sync_is_not_full_replay_audit':True,'literal_soul_established':False,'consciousness_established':False}}
    state['state_sha256']=sha_obj(state);_write(state_path(data),state)
    return {'ok':True,'version':'v1010','same_identity':True,'transition_count':len(transitions),'origin_soul_sha256':origin_sha,
            'current_soul_sha256':current_sha,'transition_head_sha256':chain['head_transition_sha256'],'checkpoint_mode':state['checkpoint_mode'],'claim_boundary':state['claim_boundary']}


def audit(data):
    errs=[]
    try:
        ident,origin_sha,current_sha,events,replayed,replay_errors=_replay(data);errs.extend(replay_errors)
        sp=state_path(data);tp=transitions_path(data)
        if not sp.exists(): errs.append('TEMPORAL_IDENTITY_STATE_MISSING')
        if not tp.exists(): errs.append('TEMPORAL_TRANSITIONS_MISSING')
        if sp.exists():
            s=_read(sp);q=dict(s);got=q.pop('state_sha256',None)
            if s.get('schema')!=SCHEMA or got!=sha_obj(q): errs.append('TEMPORAL_IDENTITY_STATE_HASH')
            oi=s.get('origin_identity',{})
            if oi!=ident: errs.append('TEMPORAL_LIVE_IDENTITY_DRIFT')
            if s.get('origin_soul_sha256')!=origin_sha: errs.append('TEMPORAL_ORIGIN_SOUL_DRIFT')
            if s.get('current_soul_sha256')!=current_sha: errs.append('TEMPORAL_CURRENT_SOUL_DRIFT')
            if s.get('transition_count')!=len(replayed): errs.append('TEMPORAL_TRANSITION_COUNT')
            exp_head=replayed[-1]['transition_sha256'] if replayed else ZERO
            if s.get('transition_head_sha256')!=exp_head: errs.append('TEMPORAL_TRANSITION_HEAD')
        if tp.exists():
            c=_read(tp);z=dict(c);got=z.pop('chain_sha256',None)
            if c.get('schema')!=TRANSITION_SCHEMA or got!=sha_obj(z): errs.append('TEMPORAL_CHAIN_HASH')
            if c.get('individual_id')!=ident['individual_id'] or c.get('lineage_id')!=ident['lineage_id'] or c.get('branch_id')!=ident['branch_id']:
                errs.append('TEMPORAL_CHAIN_IDENTITY')
            if c.get('origin_soul_sha256')!=origin_sha: errs.append('TEMPORAL_CHAIN_ORIGIN')
            if c.get('transitions')!=replayed: errs.append('TEMPORAL_CHAIN_REPLAY')
            if c.get('transition_count')!=len(replayed): errs.append('TEMPORAL_CHAIN_COUNT')
            exp_head=replayed[-1]['transition_sha256'] if replayed else ZERO
            if c.get('head_transition_sha256')!=exp_head: errs.append('TEMPORAL_CHAIN_HEAD')
    except Exception as exc:
        errs.append(type(exc).__name__+':'+str(exc))
        ident={'individual_id':None,'lineage_id':None,'branch_id':None};origin_sha=None;current_sha=None;replayed=[]
    checks={
        'same_origin':not any('ORIGIN' in x for x in errs),
        'valid_transition_chain':not any(('CHAIN' in x or 'REPLAY' in x or 'EVENT_' in x or 'TRANSITION_' in x) for x in errs),
        'no_illegal_state_jump':'ILLEGAL_STATE_JUMP' not in errs,
        'lineage_continuity':not any(('IDENTITY' in x or 'LINEAGE' in x) for x in errs),
    }
    return {
        'ok':not errs,'version':'v989','same_identity':not errs,'checks':checks,'errors':errs,
        'individual_id':ident.get('individual_id'),'lineage_id':ident.get('lineage_id'),'branch_id':ident.get('branch_id'),
        'origin_soul_sha256':origin_sha,'current_soul_sha256':current_sha,'transition_count':len(replayed),
        'claim_boundary':{'functional_temporal_self_identity':True,'literal_soul_established':False,'consciousness_established':False},
    }


def status(data):
    if not state_path(data).exists() or not transitions_path(data).exists():
        return sync_transitions(data)
    a=audit(data)
    if not a['ok']: return a
    s=_read(state_path(data))
    return {'ok':True,'version':'v989','same_identity':True,'transition_count':s['transition_count'],'origin_identity':s['origin_identity'],'origin_soul_sha256':s['origin_soul_sha256'],'current_soul_sha256':s['current_soul_sha256'],'transition_head_sha256':s['transition_head_sha256'],'checks':a['checks'],'claim_boundary':s['claim_boundary']}
