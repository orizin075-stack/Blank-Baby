#!/usr/bin/env python3
"""Independent verifier for V1022.7.2 grounded sensor evidence.

Imports no TUKUYO runtime module.  It replays Whole/component binding, signed
namespace chains, calibration certificates, device readings, quorum, action
receipt and the finite metabolism transfer.  External truth and social/device
independence are deliberately not claimed.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import statistics
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


ZERO = '0' * 64
NS = 'grounded_sensor'
COMPONENT = 'whole_grounded_sensor'


def canon(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha_obj(value):
    return hashlib.sha256(canon(value)).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def verify_envelope(envelope, public_key):
    try:
        if set(envelope) != {'payload', 'public_key', 'signature'} or envelope['public_key'] != public_key:
            return False
        Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key, validate=True)).verify(
            base64.b64decode(envelope['signature'], validate=True), canon(envelope['payload']))
        return True
    except Exception:
        return False


def fingerprint(public_key):
    raw = base64.b64decode(public_key, validate=True)
    Ed25519PublicKey.from_public_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def row_hash(row, field):
    value = dict(row); value.pop(field, None); return sha_obj(value)


def load_namespace(root, namespace, component, whole_public, whole_payload, errors):
    cache_path = root / namespace / 'STATE.json'; cache_bytes = cache_path.read_bytes(); cache = json.loads(cache_bytes)
    if hashlib.sha256(cache_bytes).hexdigest() != whole_payload.get('component_hashes', {}).get(component):
        errors.append(namespace.upper() + '_WHOLE_BINDING')
    previous = ZERO; state = None; commits = sorted((root / namespace / 'commits').glob('*.json'))
    for index, path in enumerate(commits, 1):
        envelope = read(path); payload = envelope.get('payload', {})
        if path.name != f'{index:012d}.json' or not verify_envelope(envelope, whole_public):
            errors.append(f'{namespace.upper()}_COMMIT_SIGNATURE:{index}')
        if (payload.get('schema') != 'tukuyo.v1022.commit/1' or payload.get('namespace') != namespace
                or payload.get('seq') != index or payload.get('previous') != previous):
            errors.append(f'{namespace.upper()}_COMMIT_CHAIN:{index}')
        previous = sha_obj(envelope); state = payload.get('state')
    if not commits or cache.get('head') != previous or cache.get('state') != state:
        errors.append(namespace.upper() + '_CACHE_HEAD')
    return state or {}, len(commits)


def scalar(value, kind):
    if kind == 'number':
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError('number')
        value = round(float(value), 9); return int(value) if value.is_integer() else value
    if kind == 'string' and isinstance(value, str) and value:
        return value
    if kind == 'boolean' and type(value) is bool:
        return value
    raise ValueError('scalar')


def claim_matches(claim, value):
    value = scalar(value, claim['value_type'])
    return value == claim['asserted_value'] if claim['comparator'] == 'equal' else abs(float(value) - float(claim['asserted_value'])) <= float(claim['tolerance'])


def consensus(values, kind):
    if kind == 'number':
        return scalar(statistics.median([float(value) for value in values]), 'number')
    counts = {}
    for value in values:
        key = json.dumps(value, ensure_ascii=False, sort_keys=True); counts[key] = counts.get(key, 0) + 1
    winner, count = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0]
    return json.loads(winner) if count > len(values) // 2 else None


def verify(root):
    root = Path(root); errors = []
    counts = {'authorities': 0, 'sensors': 0, 'verifiers': 0, 'observations': 0, 'outcomes': 0}
    try:
        whole_public = (root / 'v977' / 'whole_state.pub').read_text(encoding='utf-8').strip()
        whole_env = read(root / 'v977' / 'UNIFIED_STATE.json')
        if not verify_envelope(whole_env, whole_public): errors.append('WHOLE_SIGNATURE')
        whole_payload = whole_env.get('payload', {})
        state, commits = load_namespace(root, NS, COMPONENT, whole_public, whole_payload, errors)
        if state.get('schema') != 'tukuyo.v1022_7_3.grounded_sensor/1': errors.append('SCHEMA')
        authorities = {}; authority_keys = set(); authority_domains = set(); previous = ZERO
        for index, row in enumerate(state.get('authorities', []), 1):
            authority = row.get('authority', {}); key_hash = fingerprint(authority.get('public_key', ''))
            if (row.get('seq') != index or row.get('previous_authority_sha256') != previous
                    or row.get('authority_row_sha256') != row_hash(row, 'authority_row_sha256')
                    or authority.get('public_key_sha256') != key_hash or key_hash in authority_keys
                    or authority.get('calibration_domain') in authority_domains): errors.append(f'AUTHORITY:{index}')
            authority_keys.add(key_hash); authority_domains.add(authority.get('calibration_domain')); authorities[authority.get('authority_id')] = authority
            previous = row.get('authority_row_sha256')
        if state.get('authority_head_sha256') != previous: errors.append('AUTHORITY_HEAD')
        sensors = {}; device_keys = set(); previous = ZERO
        for index, row in enumerate(state.get('sensors', []), 1):
            sensor = row.get('sensor', {}); certificate = sensor.get('certificate', {}); payload = certificate.get('payload', {})
            authority = authorities.get(payload.get('authority_id'), {}); key_hash = fingerprint(payload.get('device_public_key', ''))
            if (not authority or not verify_envelope(certificate, authority.get('public_key'))
                    or payload.get('schema') != 'tukuyo.v1022_7_2.sensor_certificate/1'
                    or payload.get('calibration_domain') != authority.get('calibration_domain')
                    or sensor.get('certificate_sha256') != sha_obj(certificate)
                    or sensor.get('device_key_sha256') != key_hash or key_hash in device_keys
                    or row.get('seq') != index or row.get('previous_sensor_sha256') != previous
                    or row.get('sensor_row_sha256') != row_hash(row, 'sensor_row_sha256')): errors.append(f'SENSOR:{index}')
            device_keys.add(key_hash); sensors[payload.get('device_id')] = {**sensor, 'payload': payload}; previous = row.get('sensor_row_sha256')
            fields = ('certificate_id','device_id','authority_id','calibration_domain','sensor_domain','device_model',
                      'adapter_sha256','measurement_kind','unit','precision','calibrated_from_tick','calibrated_until_tick')
            if any(sensor.get(k) != payload.get(k) for k in fields) or sensor.get('device_public_key') != payload.get('device_public_key'):
                errors.append('CERTIFICATE_METADATA_BINDING')
        if state.get('sensor_head_sha256') != previous: errors.append('SENSOR_HEAD')
        verifiers = {}; verifier_keys = set(); previous = ZERO
        for index, row in enumerate(state.get('verifiers', []), 1):
            verifier = row.get('verifier', {}); key_hash = fingerprint(verifier.get('public_key', ''))
            if (verifier.get('public_key_sha256') != key_hash or key_hash in verifier_keys | authority_keys | device_keys
                    or row.get('seq') != index or row.get('previous_verifier_sha256') != previous
                    or row.get('verifier_row_sha256') != row_hash(row, 'verifier_row_sha256')): errors.append(f'VERIFIER:{index}')
            verifier_keys.add(key_hash); verifiers[verifier.get('verifier_id')] = verifier; previous = row.get('verifier_row_sha256')
        if state.get('verifier_head_sha256') != previous: errors.append('VERIFIER_HEAD')
        observations = {}; reading_ids = set(); raw_ids = set(); nonces = set(); previous = ZERO; last_tick = -1
        for index, row in enumerate(state.get('observations', []), 1):
            claim = row.get('claim', {}); tick = row.get('observed_at_tick'); expiry = row.get('expires_at_tick'); records = []
            if (row.get('claim_sha256') != sha_obj(claim) or row.get('observation_nonce') in nonces
                    or not isinstance(tick, int) or tick < last_tick or not tick < expiry <= tick + 60): errors.append(f'OBSERVATION_BINDING:{index}')
            nonces.add(row.get('observation_nonce')); last_tick = tick
            for envelope in row.get('reading_envelopes', []):
                payload = envelope.get('payload', {}); sensor = sensors.get(payload.get('device_id'), {})
                if (not sensor or not verify_envelope(envelope, sensor.get('device_public_key'))
                        or payload.get('schema') != 'tukuyo.v1022_7_2.sensor_reading/1'
                        or payload.get('observation_nonce') != row.get('observation_nonce')
                        or payload.get('claim_sha256') != sha_obj(claim)
                        or payload.get('context_sha256') != claim.get('context_sha256')
                        or payload.get('observed_at_tick') != tick or payload.get('unit') != claim.get('unit')
                        or payload.get('unit') != sensor.get('unit') or sensor.get('measurement_kind') != claim.get('predicate')
                        or payload.get('value_type') != claim.get('value_type')
                        or payload.get('calibration_certificate_sha256') != sensor.get('certificate_sha256')
                        or not sensor.get('calibrated_from_tick') <= tick <= sensor.get('calibrated_until_tick')): errors.append(f'READING_BINDING:{index}')
                if payload.get('reading_id') in reading_ids or payload.get('raw_evidence_sha256') in raw_ids: errors.append(f'READING_REPLAY:{index}')
                reading_ids.add(payload.get('reading_id')); raw_ids.add(payload.get('raw_evidence_sha256'))
                records.append((sensor, payload))
            fingerprints = sorted({sensor.get('device_key_sha256') for sensor, _ in records})
            sensor_domains = sorted({sensor.get('sensor_domain') for sensor, _ in records})
            calibration_domains = sorted({sensor.get('calibration_domain') for sensor, _ in records})
            adapters = sorted({sensor.get('adapter_sha256') for sensor, _ in records})
            value = consensus([payload.get('observed_value') for _, payload in records], claim.get('value_type'))
            match = value is not None and claim_matches(claim, value)
            if (len(fingerprints) < 3 or len(sensor_domains) < 3 or len(calibration_domains) < 3 or len(adapters) < 2
                    or row.get('device_fingerprints') != fingerprints or row.get('sensor_domains') != sensor_domains
                    or row.get('calibration_domains') != calibration_domains or row.get('adapter_hashes') != adapters
                    or row.get('consensus_value') != value or row.get('claim_match') is not match
                    or row.get('status') != 'CALIBRATED_SENSOR_CONSENSUS_ONLY'
                    or row.get('seq') != index or row.get('previous_observation_sha256') != previous
                    or row.get('observation_sha256') != row_hash(row, 'observation_sha256')): errors.append(f'OBSERVATION_DERIVATION:{index}')
            observations[row.get('observation_sha256')] = row; previous = row.get('observation_sha256')
        if state.get('observation_head_sha256') != previous: errors.append('OBSERVATION_HEAD')
        challenged = set(); receipt_ids = set(); reward_hashes = set(); previous = ZERO
        metabolism = None
        if any(row.get('resource_credit') for row in state.get('outcomes', [])):
            metabolism, _ = load_namespace(root, 'v1022_ecology', 'runtime_metabolism_v1022', whole_public, whole_payload, errors)
            reward_hashes = {row.get('receipt_sha256') for row in metabolism.get('grounded_rewards', [])}
            energy = sum(metabolism['runtimes'][rid]['energy'] for rid in metabolism['active'])
            if metabolism['initial_total'] + metabolism['regenerated'] != metabolism['reservoir'] + metabolism['burned'] + energy:
                errors.append('METABOLISM_RESOURCE_CONSERVATION')
        for index, row in enumerate(state.get('outcomes', []), 1):
            observation = observations.get(row.get('observation_sha256')); verifier = verifiers.get(row.get('verifier_id'), {})
            envelope = row.get('receipt_envelope', {}); payload = envelope.get('payload', {})
            if (not observation or row.get('observation_sha256') in challenged or not verifier
                    or not verify_envelope(envelope, verifier.get('public_key'))
                    or payload.get('schema') not in ('tukuyo.v1022_7_2.outcome_receipt/1', 'tukuyo.v1022_7_3.measured_outcome_receipt/1')
                    or payload.get('observation_sha256') != row.get('observation_sha256')
                    or payload.get('observation_nonce') != observation.get('observation_nonce')
                    or payload.get('runtime_id') != row.get('runtime_id') or payload.get('action_id') != row.get('action_id')
                    or payload.get('action_context_sha256') != row.get('action_context_sha256')
                    or not observation.get('observed_at_tick') <= payload.get('observed_at_tick', -1) <= observation.get('expires_at_tick')
                    or payload.get('success') is not row.get('success') or payload.get('resource_credit') != row.get('resource_credit')
                    or (not row.get('success') and row.get('resource_credit') != 0)): errors.append(f'OUTCOME_BINDING:{index}')
            challenged.add(row.get('observation_sha256'))
            if payload.get('receipt_id') in receipt_ids: errors.append(f'OUTCOME_REPLAY:{index}')
            receipt_ids.add(payload.get('receipt_id'))
            expected = 'GROUNDED_ACTION_CONFIRMED' if row.get('success') else 'GROUNDED_ACTION_REFUTED'
            if (row.get('status') != expected or row.get('seq') != index or row.get('previous_outcome_sha256') != previous
                    or row.get('outcome_sha256') != row_hash(row, 'outcome_sha256')): errors.append(f'OUTCOME_DERIVATION:{index}')
            if row.get('success') and row.get('resource_credit'):
                receipt_hash = sha_obj(envelope)
                if receipt_hash not in reward_hashes or not row.get('metabolism_result', {}).get('resource_conservation'):
                    errors.append(f'METABOLISM_RECEIPT_BINDING:{index}')
            elif row.get('metabolism_result') is not None:
                errors.append(f'UNEXPECTED_METABOLISM_RESULT:{index}')
            previous = row.get('outcome_sha256')
        if state.get('outcome_head_sha256') != previous: errors.append('OUTCOME_HEAD')
        from v1022_7_3_decision_replay import replay
        ndecisions, nintents = replay(state, observations, sensors, metabolism, errors, row_hash)
        counts.update(decisions=ndecisions, intents=nintents)
        if authority_keys & {sensor['device_key_sha256'] for sensor in sensors.values()}:
            errors.append('CROSS_ROLE_KEY_REUSE')
        if metabolism is not None:
            outcome_by_hash = {sha_obj(row['receipt_envelope']): row for row in state['outcomes'] if row['resource_credit']}
            for reward in metabolism.get('grounded_rewards', []):
                source = outcome_by_hash.get(reward['receipt_sha256'])
                if (not source or source['runtime_id'] != reward['runtime'] or source['resource_credit'] != reward['requested']
                        or reward['energy_before'] + reward['paid'] != reward['energy_after']
                        or reward['burn'] != 0 or reward['death_cause'] is not None
                        or source['metabolism_result']['paid'] != reward['paid']):
                    errors.append('REWARD_EXACT_BINDING')
                if source:
                    intent = next(r for r in state['intents'] if r['intent_sha256'] == source['receipt_envelope']['payload']['intent_sha256'])
                    if reward.get('runtime_head_before_sha256') != intent['runtime_head_sha256']:
                        errors.append('REWARD_PRECOMMITTED_RUNTIME_HEAD')
                child = root / 'v1022_ecology' / 'runtimes' / reward['runtime']
                child_env = read(child / 'v977' / 'UNIFIED_STATE.json')
                snapshot = metabolism['runtimes'][reward['runtime']]
                events_bytes = (child / 'v1007' / 'ORGANISM2_EVENTS.json').read_bytes()
                if (not verify_envelope(child_env, snapshot['whole_public_key'])
                        or hashlib.sha256((child / 'v977' / 'UNIFIED_STATE.json').read_bytes()).hexdigest() != snapshot['whole_sha256']
                        or child_env['payload']['component_hashes']['organism2_events_v1007'] != hashlib.sha256(events_bytes).hexdigest()):
                    errors.append('CHILD_RESOURCE_EVENT_ANCHOR')
                events = json.loads(events_bytes)['events']
                matches = [e for e in events if e.get('receipt_sha256') == reward['receipt_sha256']]
                if (len(matches) != 1 or matches[0]['event'] != 'RESOURCE_CREDIT'
                        or matches[0]['credit'] != reward['paid'] or matches[0]['before_energy'] != reward['energy_before']
                        or matches[0]['after_energy'] != reward['energy_after'] or matches[0]['age_before'] != matches[0]['age_after']
                        or matches[0]['event_sha256'] != row_hash(matches[0], 'event_sha256')):
                    errors.append('CHILD_RESOURCE_EVENT_BINDING')
        boundary = state.get('claim_boundary', {})
        if (boundary.get('sensor_consensus_establishes_external_truth') is not False
                or boundary.get('configured_domains_prove_real_world_independence') is not False
                or boundary.get('literal_soul_established') is not False
                or boundary.get('consciousness_established') is not False): errors.append('CLAIM_BOUNDARY')
        counts = {'authorities': len(authorities), 'sensors': len(sensors), 'verifiers': len(verifiers),
                  'observations': len(observations), 'outcomes': len(state.get('outcomes', [])), 'commits': commits}
    except Exception as exc:
        errors.append(type(exc).__name__ + ':' + str(exc))
    return {'ok': not errors, 'version': 'v1022.7.3', 'errors': errors, **counts,
            'whole_and_component_binding_verified': not errors,
            'calibration_and_device_signatures_verified': not errors,
            'typed_observation_quorum_replayed': not errors,
            'action_receipt_and_metabolic_transfer_replayed': not errors,
            'external_truth_verified': False, 'real_world_independence_verified': False,
            'literal_soul_established': False, 'consciousness_established': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--data', required=True); args = parser.parse_args()
    result = verify(args.data); print(json.dumps(result, ensure_ascii=False, sort_keys=True)); raise SystemExit(0 if result['ok'] else 1)
