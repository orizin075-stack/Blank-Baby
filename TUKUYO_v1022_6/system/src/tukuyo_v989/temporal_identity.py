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
    from tukuyo_common.atomic_fs import atomic_write_bytes
    atomic_write_bytes(p,canon(o)+b'\n')


def root(data): return Path(data)/'v989'
def state_path(data): return root(data)/'TEMPORAL_IDENTITY.json'
# The transition chain is an append-only journal, one transition per line: a new experience appends a line, it does not
# rewrite the history. Each transition names the one before it (previous_transition_sha256), so the head commits to all.
def transitions_path(data): return root(data)/'SOUL_TRANSITIONS.jsonl'
# Before 2026-10-09 the chain was one JSON object; it is still read until the next sync writes the journal.
def legacy_transitions_path(data): return root(data)/'SOUL_TRANSITIONS.json'


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
                e.get('theme',''),e.get('relation',''),e.get('law',1))
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


def _stored(data):
    """the stored transitions: (list, 'journal'|'legacy'|None, the legacy chain object or None); ValueError if unreadable"""
    from tukuyo_common.journal import read_from_offset
    tp=transitions_path(data);lp=legacy_transitions_path(data)
    if tp.exists():return read_from_offset(tp,0)[0],'journal',None
    if lp.exists():c=_read(lp);return list(c.get('transitions',[])),'legacy',c
    return [],None,None


def load_chain(data):
    """the transition chain as one object, the way it was stored before the journal (v1009 and older readers use this);
    chain_sha256 is computed as it always was, so it matches a chain stored the old way with the same transitions"""
    ident=_live_identity(data);ts,_,_=_stored(data)
    chain={'schema':TRANSITION_SCHEMA,'individual_id':ident['individual_id'],'lineage_id':ident['lineage_id'],'branch_id':ident['branch_id'],
           'origin_soul_sha256':sha_obj(_default_soul(ident)),'transition_count':len(ts),'head_transition_sha256':ts[-1]['transition_sha256'] if ts else ZERO,
           'transitions':ts}
    chain['chain_sha256']=sha_obj(chain);return chain


def _from_checkpoint(data,ident,origin_sha):
    """(last state, last transition, unseen soul events, soul journal size) when the stored checkpoint extends from the
    journal bytes it was built from: only the tail of each journal is read, and only the unseen soul events are
    verified, so one experience does not cost the whole history. Any doubt -> None, and the full path runs instead.
    audit() still replays the whole history."""
    from tukuyo_common.journal import read_from_offset,prefix_last_event
    sp,tp=state_path(data),transitions_path(data)
    if not sp.exists() or not tp.exists():return None
    try:
        old=_read(sp);oq=dict(old);oh=oq.pop('state_sha256',None)
        if oh!=sha_obj(oq) or old.get('schema')!=SCHEMA or 'source_journal_size' not in old or 'transitions_journal_size' not in old:return None
        if old.get('origin_identity')!=ident or old.get('origin_soul_sha256')!=origin_sha:return None
        n=int(old['transition_count']);tsize=int(old['transitions_journal_size'])
        if old.get('source_soul_event_count')!=n or tp.stat().st_size!=tsize:return None
        last=prefix_last_event(tp,tsize) if tsize else None
        if n:
            if (not last or last.get('seq')!=n or last.get('transition_sha256')!=old.get('transition_head_sha256')
                    or last.get('to_soul_sha256')!=old.get('current_soul_sha256') or last.get('individual_id')!=ident['individual_id']):return None
        elif last is not None or old.get('transition_head_sha256')!=ZERO:return None
        jp=soul_event_path(data);off=int(old['source_journal_size']);edge=prefix_last_event(jp,off)
        if n and (not edge or edge.get('seq')!=n or edge.get('event_sha256')!=last.get('source_event_sha256')
                  or edge.get('soul_sha256')!=last.get('to_soul_sha256')):return None
        if not n and edge is not None:return None
        suffix,size=read_from_offset(jp,off);prev=last['source_event_sha256'] if n else ZERO
        for i,e in enumerate(suffix,n+1):
            q=dict(e);got=q.pop('event_sha256',None)
            if e.get('seq')!=i or e.get('individual_id')!=ident['individual_id'] or e.get('prev_sha256')!=prev or got!=sha_obj(q):return None
            prev=got
        return old,last,suffix,size
    except Exception:
        return None


def _transition(ident,i,before,after,e,prev_transition):
    t={'schema':'tukuyo.v989.soul_transition/1','seq':i,'individual_id':ident['individual_id'],
       'lineage_id':ident['lineage_id'],'branch_id':ident['branch_id'],'from_soul_sha256':before,
       'to_soul_sha256':after,'source_event_seq':i,'source_event_sha256':e.get('event_sha256'),
       'kind':e.get('kind',''),'theme':e.get('theme',''),'relation':e.get('relation',''),
       'previous_transition_sha256':prev_transition}
    t['transition_sha256']=sha_obj(t);return t


def sync_transitions(data):
    import os
    from tukuyo_common.journal import read_from_offset,_line
    from tukuyo_common.atomic_fs import atomic_write_bytes,durable_unlink
    ident=_live_identity(data);origin_sha=sha_obj(_default_soul(ident));current_sha=sha_obj(load_soul(data))
    fast=_from_checkpoint(data,ident,origin_sha);tp=transitions_path(data)
    if fast is not None:
        old,last,todo,size=fast;n=int(old['transition_count']);new=[]
        prev_transition=last['transition_sha256'] if last else ZERO;before=last['to_soul_sha256'] if last else origin_sha
        # Append only the unseen suffix. Each canonical soul event already commits the resulting soul SHA.
        for i,e in enumerate(todo,n+1):
            t=_transition(ident,i,before,e.get('soul_sha256'),e,prev_transition);new.append(t);prev_transition=t['transition_sha256'];before=t['to_soul_sha256']
        if current_sha!=before: raise ValueError('TEMPORAL_IDENTITY_PRECHECK:ILLEGAL_STATE_JUMP')
        if new:
            with tp.open('ab') as f:
                f.write(b''.join(_line(t).encode('utf-8') for t in new));f.flush();os.fsync(f.fileno())
        count=n+len(new);head=prev_transition
    else:
        # Bootstrap, recovery and the move from the old one-object chain: a deterministic replay of the whole history.
        _load_soul_events(data);events,size=read_from_offset(soul_event_path(data),0)
        event_errors=_verify_event_chain(events,ident)
        if event_errors: raise ValueError('TEMPORAL_IDENTITY_PRECHECK:'+','.join(event_errors[:8]))
        ident,origin_sha,current_sha,events,transitions,errors=_replay(data)
        if errors: raise ValueError('TEMPORAL_IDENTITY_PRECHECK:'+','.join(errors[:8]))
        old=_read(state_path(data)) if state_path(data).exists() else None
        if old:
            old_origin=old.get('origin_identity',{})
            if old_origin.get('individual_id')!=ident['individual_id'] or old_origin.get('lineage_id')!=ident['lineage_id'] or old_origin.get('branch_id')!=ident['branch_id']:
                raise ValueError('TEMPORAL_ORIGIN_IDENTITY_DRIFT')
            if old.get('origin_soul_sha256')!=origin_sha: raise ValueError('TEMPORAL_ORIGIN_SOUL_DRIFT')
        atomic_write_bytes(tp,b''.join(_line(t).encode('utf-8') for t in transitions))
        if legacy_transitions_path(data).exists():durable_unlink(legacy_transitions_path(data))
        count=len(transitions);head=transitions[-1]['transition_sha256'] if transitions else ZERO
    state={'schema':SCHEMA,'origin_identity':ident,'origin_soul_sha256':origin_sha,'current_soul_sha256':current_sha,
           'transition_count':count,'transition_head_sha256':head,'source_soul_event_count':count,
           # where the next sync may start reading the soul journal, and how long the transition journal it extends is
           'source_journal_size':size,'transitions_journal_size':tp.stat().st_size,
           'checkpoint_mode':'INCREMENTAL_APPEND_WITH_FULL_REPLAY_AUDIT',
           'same_identity_rule':{'same_origin':True,'valid_transition_chain':True,'no_illegal_state_jump':True,'lineage_continuity':True},
           'claim_boundary':{'functional_temporal_self_identity':True,'identity_allows_lawful_soul_change':True,'causal_transition_chain_verified':True,
                             'incremental_sync_is_not_full_replay_audit':True,'literal_soul_established':False,'consciousness_established':False}}
    state['state_sha256']=sha_obj(state);_write(state_path(data),state)
    return {'ok':True,'version':'v1010','same_identity':True,'transition_count':count,'origin_soul_sha256':origin_sha,
            'current_soul_sha256':current_sha,'transition_head_sha256':head,'checkpoint_mode':state['checkpoint_mode'],'claim_boundary':state['claim_boundary']}


def audit(data):
    errs=[]
    try:
        ident,origin_sha,current_sha,events,replayed,replay_errors=_replay(data);errs.extend(replay_errors)
        sp=state_path(data);tp=transitions_path(data)
        if not sp.exists(): errs.append('TEMPORAL_IDENTITY_STATE_MISSING')
        if not tp.exists() and not legacy_transitions_path(data).exists(): errs.append('TEMPORAL_TRANSITIONS_MISSING')
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
        try:stored,kind,legacy=_stored(data)
        except ValueError:stored,kind,legacy=None,'journal',None;errs.append('TEMPORAL_CHAIN_HASH')
        if kind=='legacy':
            z=dict(legacy);got=z.pop('chain_sha256',None)
            if legacy.get('schema')!=TRANSITION_SCHEMA or got!=sha_obj(z): errs.append('TEMPORAL_CHAIN_HASH')
            if legacy.get('origin_soul_sha256')!=origin_sha: errs.append('TEMPORAL_CHAIN_ORIGIN')
            if legacy.get('transition_count')!=len(replayed): errs.append('TEMPORAL_CHAIN_COUNT')
        if stored is not None and kind is not None:
            if any(t.get('individual_id')!=ident['individual_id'] or t.get('lineage_id')!=ident['lineage_id'] or t.get('branch_id')!=ident['branch_id'] for t in stored):
                errs.append('TEMPORAL_CHAIN_IDENTITY')
            if stored!=replayed: errs.append('TEMPORAL_CHAIN_REPLAY')
            if len(stored)!=len(replayed): errs.append('TEMPORAL_CHAIN_COUNT')
            exp_head=replayed[-1]['transition_sha256'] if replayed else ZERO
            if (stored[-1]['transition_sha256'] if stored else ZERO)!=exp_head: errs.append('TEMPORAL_CHAIN_HEAD')
        if kind=='journal' and sp.exists() and 'transitions_journal_size' in s and s['transitions_journal_size']!=tp.stat().st_size:
            errs.append('TEMPORAL_CHAIN_SIZE')
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
    if not state_path(data).exists() or not (transitions_path(data).exists() or legacy_transitions_path(data).exists()):
        return sync_transitions(data)
    a=audit(data)
    if not a['ok']: return a
    s=_read(state_path(data))
    return {'ok':True,'version':'v989','same_identity':True,'transition_count':s['transition_count'],'origin_identity':s['origin_identity'],'origin_soul_sha256':s['origin_soul_sha256'],'current_soul_sha256':s['current_soul_sha256'],'transition_head_sha256':s['transition_head_sha256'],'checks':a['checks'],'claim_boundary':s['claim_boundary']}
