from __future__ import annotations
import json
from pathlib import Path
from tukuyo_common.atomic_fs import durable_unlink, cleanup_orphan_temps

MUTATION_SCHEMA='tukuyo.v1014_2.pending_mutation/1'

def mutation_marker(data):return Path(data)/'v1014'/'private'/'PENDING_MUTATION.json'

def recover_startup(data):
    data=Path(data);actions=[];errors=[]
    if not data.exists():return {'ok':True,'version':'v1014.2','actions':[],'errors':[]}
    # Do not repair derived caches or replay conversations in a partially
    # restored tree. A failed prepared restore blocks every later repair.
    try:
        from tukuyo_v1014.recovery import recover_incomplete_restore
        r=recover_incomplete_restore(data)
        if r.get('recovered'):actions.append('RESTORE_COMMIT_COMPLETED')
    except Exception as e:
        return {'ok':False,'version':'v1014.2','actions':actions,'errors':['RECOVERY_TXN:'+type(e).__name__+':'+str(e)]}
    soul_changed=False
    # v1014.4: an interrupted conversation is rolled back before any derived audits run.
    try:
        from tukuyo_v1014_4.recovery import recover_conversation,repair_soul_materialization
        c=recover_conversation(data)
        if c.get('recovered'):actions.append('CONVERSATION_TXN_ROLLED_BACK')
        sr=repair_soul_materialization(data)
        soul_changed=bool(sr.get('repaired'))
        if soul_changed:actions.append(sr.get('action') or 'SOUL_MATERIALIZED_FROM_EVENT_CHAIN')
    except Exception as e:errors.append('V1014_4_RECOVERY:'+type(e).__name__+':'+str(e))
    # The heart takes in an experience the soul took in just before the process died (v978 written-ahead note).
    if (data/'state'/'integration_state.json').is_file():
        try:
            from tukuyo_v978.heart_loop import recover_pending as heart_recover
            hr=heart_recover(data)
            if hr and hr.get('recovered'):actions.append(hr['action']);soul_changed=True
            elif hr and str(hr.get('reason','')).startswith('HEART_COULD_NOT'):actions.append(hr['reason'])
        except Exception as e:errors.append('V978_HEART_RECOVERY:'+type(e).__name__+':'+str(e))
    # A restore can leave the whole live tree inconsistent, so finish it first.
    try:
        from tukuyo_v1014.recovery import recover_incomplete_restore,recover_checkpoint_commit
        r=recover_incomplete_restore(data)
        if r.get('recovered'):actions.append('RESTORE_COMMIT_COMPLETED')
        elif r.get('rolled_back'):actions.append('RESTORE_TXN_ROLLED_BACK')
        c=recover_checkpoint_commit(data)
        if c.get('recovered'):actions.append('CHECKPOINT_POINTER_REPAIRED')
        elif c.get('rolled_back'):actions.append('CHECKPOINT_TXN_ROLLED_BACK')
    except Exception as e:errors.append('RECOVERY_TXN:'+type(e).__name__+':'+str(e))
    # Realtime has a WAL-like pending event. Completing it can change a component hash.
    realtime_changed=False
    try:
        from tukuyo_v1013.realtime_continuity import repair as realtime_repair
        r=realtime_repair(data)
        realtime_changed=bool(r.get('repaired'))
        if realtime_changed:actions.append('REALTIME_PENDING_COMPLETED')
    except Exception as e:errors.append('REALTIME_REPAIR:'+type(e).__name__+':'+str(e))
    # v1015 living episode marker: never leave a partially applied life episode silent.
    living_changed=False
    try:
        from tukuyo_v1015.living_continuity import recover_pending_episode
        lr=recover_pending_episode(data)
        living_changed=bool(lr.get('recovered'))
        if living_changed and lr.get('action'):actions.append(str(lr.get('action')))
    except Exception as e:errors.append('V1015_LIVING_RECOVERY:'+type(e).__name__+':'+str(e))
    # generation 4 (after every other repair): finish a thought's episode the process did not, or sync stores it signed before it stopped
    g4_changed=False
    if (data/'g4').is_dir() and (data/'state'/'integration_state.json').is_file():
        try:
            from tukuyo_g4.life import recover as g4_recover
            from tukuyo_g4.own import unsynced as g4_unsynced
            r=g4_recover(data)
            if r and r.get('recovered'):actions.append('G4_EPISODE_COMPLETED');g4_changed=True
            elif r:actions.append('G4_EPISODE_SET_ASIDE:'+str(r.get('abandoned')))
            if g4_unsynced(data):actions.append('G4_STORES_RESYNCED');g4_changed=True
        except Exception as e:errors.append('G4_RECOVERY:'+type(e).__name__+':'+str(e))
    # A verified answer may have committed while unified state did not.
    m=mutation_marker(data)
    mutation_pending=False
    if m.is_file():
        try:
            obj=json.loads(m.read_text(encoding='utf-8'))
            if obj.get('schema')!=MUTATION_SCHEMA:raise ValueError('PENDING_MUTATION_SCHEMA')
            mutation_pending=True
        except Exception as e:errors.append('PENDING_MUTATION:'+type(e).__name__+':'+str(e))
    if (realtime_changed or mutation_pending or soul_changed or living_changed or g4_changed) and (data/'state'/'integration_state.json').is_file():
        try:
            from tukuyo_v977.whole_state import sync as whole_sync
            whole_sync(data);actions.append('WHOLE_STATE_RESYNC')
            if mutation_pending:durable_unlink(m);actions.append('PENDING_MUTATION_CLEARED')
        except Exception as e:errors.append('WHOLE_RESYNC:'+type(e).__name__+':'+str(e))
    removed=cleanup_orphan_temps(data)
    if removed:actions.append('ORPHAN_ATOMIC_TEMPS_CLEANED:'+str(len(removed)))
    return {'ok':not errors,'version':'v1014.2','actions':actions,'errors':errors}
