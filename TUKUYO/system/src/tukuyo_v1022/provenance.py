"""v1022.7.9 where an experience came from (経験の出どころ), and which experiences are confirmed from outside.

Every experience the soul takes in from v1022.7.9 on says where it came from (the soul event's `origin`, inside its
hash chain). The path that writes it decides, never the one who asks:

  observed     実観測          an outcome of its own grounded sensors (v1022.7.2): readings signed by calibrated
                               devices of three configured domains and a separate verifier's receipt. Only through
                               `experience-observed`, which checks that evidence and derives the experience from it
  checked      自分で確かめた    what its own checker and its parents' agreement established (generation 4)
  teacher      教師から         what the dialogue teacher said, taken in without its own check
  told         申告            what someone told it happened (soul-experience, heart-experience, heart-feedback, a
                               conversation, a living episode): it may have happened; nothing outside confirmed it
  self_report  自己申告         what it says of itself
  simulated    模擬            what happened in a simulation (the research world, the ecology, the assays)

An experience from before v1022.7.9 has no origin (unrecorded).

Only `observed` is confirmed from outside, and only while its evidence holds: the audit derives it again from the
signed sensor record every time; the word alone confirms nothing. A told, simulated or self-reported experience stays
what it is. Nothing turns it into an observed one: an observation makes a new experience of its own (derived from
the evidence, not chosen), and one outcome makes one experience.

Not established here: that the sensors' world is the real world, that the configured authorities are independent of
one another or of the owner (the owner registers them), or that what was observed is true. Keys the individual holds
itself, or holds for the runtimes it hosts, are never accepted as an outside witness.
"""
from __future__ import annotations
import base64,hashlib,json
from pathlib import Path

from tukuyo_v977 import whole_state as whole
from tukuyo_v977.whole_state import ORIGINS,sha_obj

VERSION='v1022.7.9'
CLAIMABLE=('told','self_report','teacher','simulated')     # what a caller may say of an experience it gives
WORDS={'observed':'実観測','checked':'自分で確かめた','teacher':'教師から','told':'申告（確認なし）','self_report':'自己申告',
       'simulated':'模擬','unrecorded':'出どころの記録なし（v1022.7.9 より前）'}
KIND='observation';LAW=3;VALENCE=.6
MIN_IMPORTANCE,MAX_IMPORTANCE=.1,1.0
CLAIM_BOUNDARY={'external_truth_verified':False,'configured_authorities_independent_of_owner_verified':False,
                'sensor_world_is_real_world_verified':False,'literal_soul_established':False,'consciousness_established':False}


def _events(data):
    from tukuyo_common.journal import load_events
    return load_events(whole.event_path(data))


def own_key_fingerprints(data):
    """sha256 of every Ed25519 public key the individual holds (its own, and those of runtimes it hosts): never an
    outside witness. Read from the keys themselves (*.key -> its public key, *.pub)."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    out=set();data=Path(data)
    skip={'recovery_blobs','recovery_checkpoints','.lineage_transaction','__pycache__'}
    for p in data.rglob('*'):
        if not p.is_file() or p.is_symlink() or p.suffix not in ('.key','.pub') or any(x in skip for x in p.relative_to(data).parts):continue
        try:
            raw=base64.b64decode(p.read_text(encoding='utf-8').strip(),validate=True)
            if len(raw)!=32:continue
            if p.suffix=='.key':raw=Ed25519PrivateKey.from_private_bytes(raw).public_key().public_bytes_raw()
            out.add(hashlib.sha256(raw).hexdigest())
        except Exception:  # noqa: BLE001 - a file that is not a key is not one of its keys
            continue
    return out


def _sensor_state(data):
    from . import grounded_sensor as gs
    try:return gs.load(data)
    except ValueError as e:
        if str(e)=='GROUNDED_SENSOR_NOT_INITIALIZED':return None
        raise


def _evidence(data,state,outcome_sha256,own=None):
    """the evidence of one grounded outcome, checked again: (evidence, None) or (None, refusal)"""
    if state is None:return None,'EXPERIENCE_NO_SENSORS'
    row=next((r for r in state['outcomes'] if r.get('outcome_sha256')==outcome_sha256),None)
    if row is None:return None,'EXPERIENCE_EVIDENCE_UNKNOWN'
    obs=next((o for o in state['observations'] if o['observation_sha256']==row['observation_sha256']),None)
    if obs is None:return None,'EXPERIENCE_EVIDENCE_UNKNOWN'
    if row.get('status') not in ('GROUNDED_ACTION_CONFIRMED','GROUNDED_ACTION_REFUTED') or row['status']!=('GROUNDED_ACTION_CONFIRMED' if row['success'] else 'GROUNDED_ACTION_REFUTED'):
        return None,'EXPERIENCE_EVIDENCE_STATUS'
    ident=whole._live_identity(data)
    if any(state.get(k)!=ident[k] for k in ('individual_id','lineage_id','branch_id')):return None,'EXPERIENCE_EVIDENCE_NOT_ITS_OWN'
    sensors={r['sensor']['device_key_sha256']:r['sensor'] for r in state['sensors']}
    authorities={r['authority']['authority_id']:r['authority'] for r in state['authorities']}
    devices=sorted(obs['device_fingerprints'])
    if any(d not in sensors for d in devices):return None,'EXPERIENCE_EVIDENCE_UNKNOWN_DEVICE'
    certifiers=sorted({authorities[sensors[d]['authority_id']]['public_key_sha256'] for d in devices})
    verifier=row['verifier_key_sha256']
    # one key, one role: the devices, the authorities that certified them and the verifier are all different keys
    if verifier in devices or verifier in certifiers or set(devices)&set(certifiers):return None,'EXPERIENCE_EVIDENCE_ROLE_REUSE'
    own=own_key_fingerprints(data) if own is None else own
    if own&({verifier}|set(devices)|set(certifiers)):return None,'EXPERIENCE_EVIDENCE_SELF_SIGNED'
    return {'outcome_sha256':row['outcome_sha256'],'observation_sha256':obs['observation_sha256'],
            'receipt_sha256':sha_obj(row['receipt_envelope']),'verifier_key_sha256':verifier,'device_key_sha256s':devices,
            'certifier_key_sha256s':certifiers,'claim_sha256':obs['claim_sha256'],'claim_match':bool(obs['claim_match']),
            'success':bool(row['success']),'observed_at_tick':row['receipt_envelope']['payload']['observed_at_tick']},None


def _content(evidence,claim):
    """the experience an outcome makes: derived from the evidence, never chosen by the caller"""
    return {'kind':KIND,'valence':VALENCE if evidence['success'] else -VALENCE,
            'theme':'observed:'+str(claim['predicate'])[:64],'relation':'','law':LAW}


def _used(events):
    return {(e.get('evidence') or {}).get('outcome_sha256') for e in events if e.get('origin')=='observed'}


def observe_experience(data,outcome_sha256,importance=.5):
    """take one grounded outcome in as an experience (origin 'observed'), after checking its evidence again"""
    from tukuyo_v1019.lifecycle import require_alive
    require_alive(data)
    if not isinstance(outcome_sha256,str) or len(outcome_sha256)!=64:raise ValueError('EXPERIENCE_EVIDENCE_UNKNOWN')
    if type(importance) not in (int,float) or not MIN_IMPORTANCE<=float(importance)<=MAX_IMPORTANCE:raise ValueError('EXPERIENCE_IMPORTANCE')
    state=_sensor_state(data);evidence,why=_evidence(data,state,outcome_sha256)
    if why:raise ValueError(why)
    if outcome_sha256 in _used(_events(data)):raise ValueError('EXPERIENCE_EVIDENCE_REUSED')
    obs=next(o for o in state['observations'] if o['observation_sha256']==evidence['observation_sha256'])
    c=_content(evidence,obs['claim'])
    from tukuyo_v978.heart_loop import process_experience
    res=process_experience(data,c['kind'],c['valence'],float(importance),c['theme'],c['relation'],law=c['law'],origin='observed',evidence=evidence)
    from tukuyo_v993.relation_bound import sync as relation_sync
    from tukuyo_v995.other_agent_trust import sync as peer_sync
    relation_sync(data);peer_sync(data);whole.sync(data)
    from tukuyo_common.journal import last_event
    e=last_event(whole.event_path(data)) or {}
    return {'ok':True,'version':VERSION,'origin':'observed','externally_confirmed':True,'meaning':res.get('meaning'),
            'soul_event':{k:e.get(k) for k in ('seq','kind','valence','importance','theme','origin','event_sha256')},
            'evidence':evidence,'claim_boundary':CLAIM_BOUNDARY}


def audit(data,events=None):
    """every experience's origin, and every observed one's evidence derived again from the signed sensor record"""
    events=_events(data) if events is None else events;errors=[];counts={k:0 for k in (*ORIGINS,'unrecorded')}
    confirmed=[];state=None;own=None;seen=set()
    for e in events:
        o=e.get('origin');seq=e.get('seq')
        if o is None:
            counts['unrecorded']+=1
            if 'evidence' in e:errors.append(f'EXPERIENCE_EVIDENCE_WITHOUT_ORIGIN:{seq}')
            continue
        if o not in ORIGINS:errors.append(f'EXPERIENCE_ORIGIN_UNKNOWN:{seq}');continue
        counts[o]+=1
        if o!='observed':
            if 'evidence' in e:errors.append(f'EXPERIENCE_EVIDENCE_ON_{o.upper()}:{seq}')
            continue
        ev=e.get('evidence') or {}
        if state is None:
            try:state=_sensor_state(data)
            except ValueError as x:errors.append(f'EXPERIENCE_SENSOR_RECORD:{x}');break
            own=own_key_fingerprints(data)
        derived,why=_evidence(data,state,ev.get('outcome_sha256'),own)
        if why:errors.append(f'EXPERIENCE_OBSERVED_UNPROVEN:{seq}:{why}');continue
        if derived!=ev:errors.append(f'EXPERIENCE_OBSERVED_EVIDENCE_MISMATCH:{seq}');continue
        if ev['outcome_sha256'] in seen:errors.append(f'EXPERIENCE_EVIDENCE_REUSED:{seq}');continue
        seen.add(ev['outcome_sha256'])
        obs=next(x for x in state['observations'] if x['observation_sha256']==ev['observation_sha256'])
        c=_content(derived,obs['claim'])
        if (e.get('kind'),float(e.get('valence',0)),e.get('theme'),e.get('relation'),e.get('law',1))!=(c['kind'],c['valence'],c['theme'],c['relation'],c['law']) \
                or not MIN_IMPORTANCE<=float(e.get('importance',0))<=MAX_IMPORTANCE:
            errors.append(f'EXPERIENCE_NOT_FROM_ITS_EVIDENCE:{seq}');continue
        confirmed.append({'seq':seq,'theme':e.get('theme'),'success':ev['success'],'outcome_sha256':ev['outcome_sha256']})
    return {'ok':not errors,'version':VERSION,'errors':errors,'experiences':len(events),'origins':counts,
            'externally_confirmed':len(confirmed),'confirmed':confirmed[-20:],'words':WORDS,'claim_boundary':CLAIM_BOUNDARY}


def needs_audit(events):
    """the whole audit runs this one only where there is something for it (an origin or evidence on some event)"""
    return any('origin' in e or 'evidence' in e for e in events)


def summary(data):
    """for its self-report: how many of its experiences came from where, and how many were confirmed from outside"""
    a=audit(data)
    return {'origins':{k:v for k,v in a['origins'].items() if v},'externally_confirmed':a['externally_confirmed'],'ok':a['ok']}
