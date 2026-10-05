from __future__ import annotations
import json
from pathlib import Path
from tukuyo_v977.whole_state import canon, sha_obj, _live_identity, sync as whole_sync, audit as whole_audit
from tukuyo_v978.heart_loop import process_experience, audit as heart_audit
from tukuyo_v979.deep_core import consolidate, forget_surface_memory, load as load_deep, audit as deep_audit
from tukuyo_v981.fork_divergence import run_assay as fork_assay, audit as fork_audit
from tukuyo_v985.narrative_purpose import integrate as purpose_integrate, audit as purpose_audit
from tukuyo_v989.temporal_identity import status as identity_status, audit as identity_audit, transitions_path
from tukuyo_v995.other_agent_trust import sync as peer_sync, audit as peer_audit
from tukuyo_v1007.organism2 import init as organism_init, update as organism_update, load as organism_load, audit as organism_audit
from tukuyo_v1008.whole_living_cognition import cycle as living_cycle, audit as living_audit

SCHEMA='tukuyo.v1009.long_lived_identity_assay/1'


def _read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def _write(p,o):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')


def root(data): return Path(data)/'v1009'
def receipt_path(data): return root(data)/'LONG_LIVED_IDENTITY_ASSAY.json'


def _transition_snapshot(data):
    s=identity_status(data)
    chain=_read(transitions_path(data))
    return {
        'origin_soul_sha256':s['origin_soul_sha256'],
        'current_soul_sha256':s['current_soul_sha256'],
        'transition_count':s['transition_count'],
        'transition_head_sha256':s['transition_head_sha256'],
        'transition_chain_sha256':chain['chain_sha256'],
    }


def _organism_event_head(data):
    p=Path(data)/'v1007'/'ORGANISM2_EVENTS.json'
    if not p.exists(): return '0'*64
    box=_read(p);ev=box.get('events',[])
    return ev[-1]['event_sha256'] if ev else '0'*64


def run_assay(data,cycles=1):
    if type(cycles) is not int or not 0 <= cycles <= 8:
        raise ValueError('V1009_CYCLES_RANGE')
    ident=_live_identity(data)
    start=_transition_snapshot(data)

    # Build a mixed autobiographical history: commitment, learning, rupture, and support.
    process_experience(data,'vow',1.0,.90,'preserve_truth','')
    process_experience(data,'discovery',1.0,.80,'unknown_domain','mentor-A')
    process_experience(data,'betrayal',-1.0,.85,'trust_boundary','peer-stressor')
    process_experience(data,'support',.75,.65,'repair_attempt','peer-support')
    consolidate(data)
    purpose_integrate(data)
    peer_sync(data)

    # Create a historical fork, then continue the parent. The origin must remain frozen
    # while lawful later soul transitions are still accepted as the same identity.
    f=fork_assay(data)
    process_experience(data,'discovery',.9,.70,'post_fork_learning','mentor-A')

    # Functional injury and recovery without death.
    organism_init(data)
    injured=organism_update(data,'INJURY',.70)
    repaired=organism_update(data,'MAINTENANCE',.80)
    organism_update(data,'REST',.45)

    cycle_results=[]
    for i in range(cycles):
        cycle_results.append(living_cycle(data, f'{12+i}*(5+4)'))

    # Remove surface episodic meaning after deep consolidation; continuity must remain.
    forgotten=forget_surface_memory(data)
    process_experience(data,'learning',.8,.55,'after_memory_loss','')
    peer_sync(data)
    whole_sync(data)

    end=_transition_snapshot(data);org=organism_load(data);deep=load_deep(data)
    checks={
        'same_live_identity': _live_identity(data)==ident,
        'origin_stable': start['origin_soul_sha256']==end['origin_soul_sha256'],
        'lawful_change_occurred': end['transition_count']>start['transition_count'] and end['current_soul_sha256']!=start['current_soul_sha256'],
        'temporal_identity_valid': bool(identity_audit(data).get('ok')),
        'heart_valid': bool(heart_audit(data).get('ok')),
        'deep_soul_valid': bool(deep_audit(data).get('ok')),
        'fork_valid_after_parent_growth': bool(f.get('ok')) and bool(fork_audit(data).get('ok')),
        'purpose_valid': bool(purpose_audit(data).get('ok')),
        'peer_history_valid': bool(peer_audit(data).get('ok')),
        'injury_was_nontrivial': injured.get('state',{}).get('lifecycle') in ('INJURED','CRITICAL'),
        'recovery_preserved_life': repaired.get('state',{}).get('lifecycle')!='DEAD' and org.get('lifecycle')!='DEAD',
        'surface_memory_removed': bool(forgotten.get('ok')),
        'living_cycles_succeeded': len(cycle_results)==cycles and all(x.get('ok') for x in cycle_results),
        'living_audit_valid': True if cycles==0 else bool(living_audit(data).get('ok')),
    }
    # whole audit is evaluated after the v1009 receipt is written and the unified state is resynced.
    receipt={
        'schema':SCHEMA,
        'version':'v1009',
        'individual_id':ident['individual_id'],'lineage_id':ident['lineage_id'],'branch_id':ident['branch_id'],
        'start_transition':start,'end_transition':end,
        'deep_core_sha256':deep['core_sha256'],
        'organism_event_head_sha256':_organism_event_head(data),
        'end_lifecycle':org['lifecycle'],
        'cycles':cycles,
        'checks':checks,
        'claim_boundary':{
            'mixed_event_long_lived_identity_stress_tested':True,
            'lawful_identity_change_across_memory_loss_and_fork':True,
            'fresh_process_restart_requires_separate_audit_invocation':True,
            'externally_anchored_wallclock_duration':False,
            'literal_life_established':False,
            'literal_soul_established':False,
            'consciousness_established':False,
        },
    }
    receipt['receipt_sha256']=sha_obj(receipt)
    _write(receipt_path(data),receipt)
    whole_sync(data)
    wa=whole_audit(data)
    return {
        'ok':all(receipt['checks'].values()) and bool(wa.get('ok')),'version':'v1009','individual_id':ident['individual_id'],
        'transition_delta':end['transition_count']-start['transition_count'],'end_lifecycle':org['lifecycle'],
        'checks':{**receipt['checks'],'whole_audit_valid':bool(wa.get('ok'))},'receipt_sha256':receipt['receipt_sha256'],'claim_boundary':receipt['claim_boundary'],
    }


def audit(data):
    p=receipt_path(data)
    if not p.exists(): return {'ok':False,'version':'v1009','errors':['V1009_ASSAY_MISSING']}
    errs=[]
    try:
        r=_read(p);q=dict(r);got=q.pop('receipt_sha256',None)
        if r.get('schema')!=SCHEMA or got!=sha_obj(q): errs.append('V1009_RECEIPT_HASH')
        ident=_live_identity(data)
        if any(r.get(k)!=ident[k] for k in ('individual_id','lineage_id','branch_id')): errs.append('V1009_IDENTITY')
        ia=identity_audit(data)
        if not ia.get('ok'): errs.append('V1009_TEMPORAL_IDENTITY')
        end=r.get('end_transition',{})
        if ia.get('origin_soul_sha256')!=end.get('origin_soul_sha256'): errs.append('V1009_ORIGIN_DRIFT')
        if int(ia.get('transition_count',-1)) < int(end.get('transition_count',0)): errs.append('V1009_HISTORY_TRUNCATED')
        # The historical transition head must still exist in the current append-only chain.
        chain=_read(transitions_path(data));heads={t.get('transition_sha256') for t in chain.get('transitions',[])}
        recorded=end.get('transition_head_sha256')
        if recorded!='0'*64 and recorded not in heads: errs.append('V1009_HISTORY_HEAD_MISSING')
        if not all(bool(v) for v in r.get('checks',{}).values()): errs.append('V1009_ASSAY_CHECK')
        if not organism_audit(data).get('ok'): errs.append('V1009_ORGANISM_AUDIT')
        if not fork_audit(data).get('ok'): errs.append('V1009_FORK_AUDIT')
    except Exception as exc:
        errs.append(type(exc).__name__+':'+str(exc))
    return {
        'ok':not errs,'version':'v1009','errors':errs,
        'historical_assay_preserved':not any(x in errs for x in ('V1009_HISTORY_TRUNCATED','V1009_HISTORY_HEAD_MISSING','V1009_ORIGIN_DRIFT')),
        'claim_boundary':{
            'fresh_process_reopen_audit_supported':True,
            'future_lawful_soul_growth_allowed':True,
            'externally_anchored_wallclock_duration':False,
            'literal_life_established':False,'literal_soul_established':False,'consciousness_established':False,
        },
    }
