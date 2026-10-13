"""V1022.7.2 bounded grounded sensor challenges.

Signed, calibrated sensor agreement is not external truth.  This module binds
typed claims to device identities, calibration authorities, adapter hashes,
fresh observation nonces and bounded logical time.  A separately keyed action
verifier may then attest an outcome.  Only a successful outcome can transfer a
finite credit from the existing metabolism reservoir to an actual runtime.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import math
import re
import statistics
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from tukuyo_v977 import whole_state as whole
from tukuyo_v977.whole_state import _live_identity, sha_obj
from tukuyo_v1019.lifecycle import require_alive
from tukuyo_v1019.transaction import transactional
from . import semantic_truth as truth
from . import store


NS = 'grounded_sensor'
COMPONENT = 'whole_grounded_sensor'
SCHEMA = 'tukuyo.v1022_7_3.grounded_sensor/1'
AUTHORITY_SCHEMA = 'tukuyo.v1022_7_2.calibration_authority/1'
CERTIFICATE_SCHEMA = 'tukuyo.v1022_7_2.sensor_certificate/1'
VERIFIER_SCHEMA = 'tukuyo.v1022_7_2.action_verifier/1'
READING_SCHEMA = 'tukuyo.v1022_7_2.sensor_reading/1'
OBSERVATION_BUNDLE_SCHEMA = 'tukuyo.v1022_7_2.observation_bundle/1'
OUTCOME_RECEIPT_SCHEMA = 'tukuyo.v1022_7_2.outcome_receipt/1'
OUTCOME_BUNDLE_SCHEMA = 'tukuyo.v1022_7_2.outcome_bundle/1'
ZERO = '0' * 64
MIN_SENSORS = 3
MIN_SENSOR_DOMAINS = 3
MIN_ADAPTERS = 2
MAX_TICK_SPAN = 60


def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _text(value, label, limit=160):
    if (not isinstance(value, str) or not value or len(value) > limit
            or re.search(r'[\x00-\x1f]', value)):
        raise ValueError('GROUNDED_SENSOR_' + label)
    return value


def _sha(value, label='SHA256'):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value) or value == ZERO:
        raise ValueError('GROUNDED_SENSOR_' + label)
    return value


def _key(value, label='PUBLIC_KEY'):
    try:
        raw = base64.b64decode(value, validate=True)
        if len(raw) != 32:
            raise ValueError
        Ed25519PublicKey.from_public_bytes(raw)
    except Exception as exc:
        raise ValueError('GROUNDED_SENSOR_' + label) from exc
    return value, hashlib.sha256(raw).hexdigest()


def _verify(envelope, public_key, schema):
    if not isinstance(envelope, dict) or set(envelope) != {'payload', 'public_key', 'signature'}:
        raise ValueError('GROUNDED_SENSOR_ENVELOPE_FIELDS')
    if envelope.get('public_key') != public_key:
        raise ValueError('GROUNDED_SENSOR_SIGNER_MISMATCH')
    payload = envelope.get('payload')
    if not isinstance(payload, dict) or payload.get('schema') != schema:
        raise ValueError('GROUNDED_SENSOR_ENVELOPE_SCHEMA')
    try:
        Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key, validate=True)).verify(
            base64.b64decode(envelope.get('signature', ''), validate=True), whole.canon(payload))
    except Exception as exc:
        raise ValueError('GROUNDED_SENSOR_SIGNATURE') from exc
    return payload


def _row_hash(row, field):
    value = copy.deepcopy(row); value.pop(field, None)
    return sha_obj(value)


def _tick(value, label):
    if type(value) is not int or not 0 <= value <= 10 ** 12:
        raise ValueError('GROUNDED_SENSOR_' + label)
    return value


def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError('GROUNDED_SENSOR_' + label)
    value = round(float(value), 9)
    return int(value) if value.is_integer() else value


def _normal_authority(value):
    required = {'schema', 'authority_id', 'calibration_domain', 'public_key'}
    if not isinstance(value, dict) or set(value) != required or value.get('schema') != AUTHORITY_SCHEMA:
        raise ValueError('GROUNDED_SENSOR_AUTHORITY_FIELDS')
    public_key, fingerprint = _key(value['public_key'], 'AUTHORITY_KEY')
    return {'schema': AUTHORITY_SCHEMA,
            'authority_id': _text(value['authority_id'], 'AUTHORITY_ID', 96),
            'calibration_domain': _text(value['calibration_domain'], 'CALIBRATION_DOMAIN', 96),
            'public_key': public_key, 'public_key_sha256': fingerprint,
            'configured_domain_not_real_world_independence_proof': True}


def _authority_input(value):
    return {key: value[key] for key in ('schema', 'authority_id', 'calibration_domain', 'public_key')}


def _normal_sensor(certificate, authorities):
    authority_id = (certificate.get('payload') or {}).get('authority_id') if isinstance(certificate, dict) else None
    authority = authorities.get(authority_id)
    if authority is None:
        raise ValueError('GROUNDED_SENSOR_UNKNOWN_AUTHORITY')
    payload = _verify(certificate, authority['public_key'], CERTIFICATE_SCHEMA)
    required = {'schema', 'certificate_id', 'device_id', 'device_public_key', 'authority_id',
                'calibration_domain', 'sensor_domain', 'device_model', 'adapter_sha256',
                'measurement_kind', 'unit', 'precision', 'calibrated_from_tick',
                'calibrated_until_tick'}
    if set(payload) != required:
        raise ValueError('GROUNDED_SENSOR_CERTIFICATE_FIELDS')
    if (payload['authority_id'] != authority['authority_id']
            or payload['calibration_domain'] != authority['calibration_domain']):
        raise ValueError('GROUNDED_SENSOR_CERTIFICATE_AUTHORITY')
    public_key, fingerprint = _key(payload['device_public_key'], 'DEVICE_KEY')
    start = _tick(payload['calibrated_from_tick'], 'CALIBRATION_START')
    end = _tick(payload['calibrated_until_tick'], 'CALIBRATION_END')
    if end <= start or end - start > 10 ** 9:
        raise ValueError('GROUNDED_SENSOR_CALIBRATION_WINDOW')
    precision = _number(payload['precision'], 'PRECISION')
    if precision <= 0 or payload['precision'] != precision or payload['unit'] not in truth.UNITS:
        raise ValueError('GROUNDED_SENSOR_PRECISION')
    return {'certificate': copy.deepcopy(certificate), 'certificate_sha256': sha_obj(certificate),
            'certificate_id': _text(payload['certificate_id'], 'CERTIFICATE_ID', 96),
            'device_id': _text(payload['device_id'], 'DEVICE_ID', 96),
            'device_public_key': public_key, 'device_key_sha256': fingerprint,
            'authority_id': authority['authority_id'],
            'calibration_domain': authority['calibration_domain'],
            'sensor_domain': _text(payload['sensor_domain'], 'SENSOR_DOMAIN', 96),
            'device_model': _text(payload['device_model'], 'DEVICE_MODEL', 96),
            'adapter_sha256': _sha(payload['adapter_sha256'], 'ADAPTER_SHA256'),
            'measurement_kind': _text(payload['measurement_kind'], 'MEASUREMENT_KIND', 96),
            'unit': payload['unit'], 'precision': precision,
            'calibrated_from_tick': start, 'calibrated_until_tick': end}


def _normal_verifier(value):
    required = {'schema', 'verifier_id', 'verification_domain', 'public_key', 'method_sha256'}
    if not isinstance(value, dict) or set(value) != required or value.get('schema') != VERIFIER_SCHEMA:
        raise ValueError('GROUNDED_SENSOR_VERIFIER_FIELDS')
    public_key, fingerprint = _key(value['public_key'], 'VERIFIER_KEY')
    return {'schema': VERIFIER_SCHEMA,
            'verifier_id': _text(value['verifier_id'], 'VERIFIER_ID', 96),
            'verification_domain': _text(value['verification_domain'], 'VERIFICATION_DOMAIN', 96),
            'public_key': public_key, 'public_key_sha256': fingerprint,
            'method_sha256': _sha(value['method_sha256'], 'METHOD_SHA256'),
            'configured_verifier_not_external_truth_proof': True}


def _verifier_input(value):
    return {key: value[key] for key in ('schema', 'verifier_id', 'verification_domain',
                                        'public_key', 'method_sha256')}


def _normal_reading(envelope, sensor_map, claim, nonce, observed_tick):
    device_id = (envelope.get('payload') or {}).get('device_id') if isinstance(envelope, dict) else None
    sensor = sensor_map.get(device_id)
    if sensor is None:
        raise ValueError('GROUNDED_SENSOR_UNKNOWN_DEVICE')
    payload = _verify(envelope, sensor['device_public_key'], READING_SCHEMA)
    required = {'schema', 'reading_id', 'device_id', 'observation_nonce', 'claim_sha256',
                'context_sha256', 'observed_at_tick', 'value_type', 'unit', 'observed_value',
                'calibration_certificate_sha256', 'raw_evidence_sha256'}
    if set(payload) != required:
        raise ValueError('GROUNDED_SENSOR_READING_FIELDS')
    if (payload['device_id'] != sensor['device_id'] or payload['observation_nonce'] != nonce
            or payload['claim_sha256'] != sha_obj(claim)
            or payload['context_sha256'] != claim['context_sha256']
            or payload['observed_at_tick'] != observed_tick
            or payload['value_type'] != claim['value_type'] or payload['unit'] != claim['unit']
            or payload['unit'] != sensor['unit']
            or sensor['measurement_kind'] != claim['predicate']
            or payload['calibration_certificate_sha256'] != sensor['certificate_sha256']):
        raise ValueError('GROUNDED_SENSOR_READING_BINDING')
    if not sensor['calibrated_from_tick'] <= observed_tick <= sensor['calibrated_until_tick']:
        raise ValueError('GROUNDED_SENSOR_CALIBRATION_EXPIRED')
    value = truth._scalar(payload['observed_value'], claim['value_type'], 'SENSOR_VALUE')
    if value != payload['observed_value']:
        raise ValueError('GROUNDED_SENSOR_NONCANONICAL_VALUE')
    _sha(payload['raw_evidence_sha256'], 'RAW_EVIDENCE_SHA256')
    return {'envelope': copy.deepcopy(envelope),
            'reading_id': _text(payload['reading_id'], 'READING_ID', 96),
            'device_id': device_id, 'device_key_sha256': sensor['device_key_sha256'],
            'sensor_domain': sensor['sensor_domain'],
            'calibration_domain': sensor['calibration_domain'],
            'adapter_sha256': sensor['adapter_sha256'], 'observed_value': value}


def needs_preflight(data):
    if (Path(data) / NS).exists():
        return True
    path = whole.state_path(data)
    if not path.is_file():
        return False
    try:
        return COMPONENT in _read(path).get('payload', {}).get('component_hashes', {})
    except Exception:
        return True


def validate(state):
    required = {'schema', 'individual_id', 'lineage_id', 'branch_id', 'integration_seq',
                'authorities', 'authority_head_sha256', 'sensors', 'sensor_head_sha256',
                'verifiers', 'verifier_head_sha256', 'observations', 'observation_head_sha256',
                'outcomes', 'outcome_head_sha256', 'claim_boundary'}
    required.update({'decisions', 'decision_head_sha256', 'intents', 'intent_head_sha256'})
    if not isinstance(state, dict) or set(state) != required or state.get('schema') != SCHEMA:
        raise ValueError('GROUNDED_SENSOR_SCHEMA')
    for key in ('individual_id', 'lineage_id', 'branch_id'):
        _text(state[key], key.upper(), 160)
    if type(state['integration_seq']) is not int or state['integration_seq'] < 1:
        raise ValueError('GROUNDED_SENSOR_SEQ')
    previous = ZERO; authority_ids = set(); authority_keys = set(); domains = set()
    authorities = {}
    for index, row in enumerate(state['authorities'], 1):
        if set(row) != {'seq', 'authority', 'previous_authority_sha256', 'authority_row_sha256'}:
            raise ValueError('GROUNDED_SENSOR_AUTHORITY_ROW')
        authority = _normal_authority(_authority_input(row['authority']))
        if (authority != row['authority'] or row['seq'] != index
                or row['previous_authority_sha256'] != previous
                or row['authority_row_sha256'] != _row_hash(row, 'authority_row_sha256')):
            raise ValueError('GROUNDED_SENSOR_AUTHORITY_CHAIN')
        if authority['authority_id'] in authority_ids or authority['public_key_sha256'] in authority_keys or authority['calibration_domain'] in domains:
            raise ValueError('GROUNDED_SENSOR_AUTHORITY_REPLAY')
        authority_ids.add(authority['authority_id']); authority_keys.add(authority['public_key_sha256']); domains.add(authority['calibration_domain'])
        authorities[authority['authority_id']] = authority; previous = row['authority_row_sha256']
    if state['authority_head_sha256'] != previous:
        raise ValueError('GROUNDED_SENSOR_AUTHORITY_HEAD')
    previous = ZERO; device_ids = set(); device_keys = set(); certificate_ids = set(); sensors = {}
    for index, row in enumerate(state['sensors'], 1):
        if set(row) != {'seq', 'sensor', 'previous_sensor_sha256', 'sensor_row_sha256'}:
            raise ValueError('GROUNDED_SENSOR_SENSOR_ROW')
        sensor = _normal_sensor(row['sensor']['certificate'], authorities)
        if (sensor != row['sensor'] or row['seq'] != index or row['previous_sensor_sha256'] != previous
                or row['sensor_row_sha256'] != _row_hash(row, 'sensor_row_sha256')):
            raise ValueError('GROUNDED_SENSOR_SENSOR_CHAIN')
        if sensor['device_id'] in device_ids or sensor['device_key_sha256'] in device_keys or sensor['certificate_id'] in certificate_ids:
            raise ValueError('GROUNDED_SENSOR_SENSOR_REPLAY')
        device_ids.add(sensor['device_id']); device_keys.add(sensor['device_key_sha256']); certificate_ids.add(sensor['certificate_id'])
        sensors[sensor['device_id']] = sensor; previous = row['sensor_row_sha256']
    if state['sensor_head_sha256'] != previous:
        raise ValueError('GROUNDED_SENSOR_SENSOR_HEAD')
    previous = ZERO; verifier_ids = set(); verifier_keys = set(); verifiers = {}
    for index, row in enumerate(state['verifiers'], 1):
        if set(row) != {'seq', 'verifier', 'previous_verifier_sha256', 'verifier_row_sha256'}:
            raise ValueError('GROUNDED_SENSOR_VERIFIER_ROW')
        verifier = _normal_verifier(_verifier_input(row['verifier']))
        if (verifier != row['verifier'] or row['seq'] != index or row['previous_verifier_sha256'] != previous
                or row['verifier_row_sha256'] != _row_hash(row, 'verifier_row_sha256')):
            raise ValueError('GROUNDED_SENSOR_VERIFIER_CHAIN')
        if (verifier['verifier_id'] in verifier_ids or verifier['public_key_sha256'] in verifier_keys
                or verifier['public_key_sha256'] in authority_keys or verifier['public_key_sha256'] in device_keys):
            raise ValueError('GROUNDED_SENSOR_VERIFIER_ROLE_REUSE')
        verifier_ids.add(verifier['verifier_id']); verifier_keys.add(verifier['public_key_sha256']); verifiers[verifier['verifier_id']] = verifier
        previous = row['verifier_row_sha256']
    if state['verifier_head_sha256'] != previous:
        raise ValueError('GROUNDED_SENSOR_VERIFIER_HEAD')
    if authority_keys & device_keys or authority_keys & verifier_keys or device_keys & verifier_keys:
        raise ValueError('GROUNDED_SENSOR_CROSS_ROLE_KEY_REUSE')
    previous = ZERO; nonces = set(); reading_ids = set(); raw_hashes = set(); observation_map = {}
    last_tick = -1
    for index, row in enumerate(state['observations'], 1):
        required_row = {'seq', 'claim', 'claim_sha256', 'observation_nonce', 'observed_at_tick',
                        'expires_at_tick', 'reading_envelopes', 'reading_ids', 'device_fingerprints',
                        'sensor_domains', 'calibration_domains', 'adapter_hashes', 'consensus_value',
                        'claim_match', 'status', 'previous_observation_sha256', 'observation_sha256'}
        if set(row) != required_row or row['seq'] != index or row['previous_observation_sha256'] != previous:
            raise ValueError('GROUNDED_SENSOR_OBSERVATION_ROW')
        claim = truth._normal_claim(row['claim'])
        if claim != row['claim'] or row['claim_sha256'] != sha_obj(claim):
            raise ValueError('GROUNDED_SENSOR_CLAIM_BINDING')
        tick = _tick(row['observed_at_tick'], 'OBSERVED_TICK'); expiry = _tick(row['expires_at_tick'], 'EXPIRY_TICK')
        if tick < last_tick or not tick < expiry <= tick + MAX_TICK_SPAN or row['observation_nonce'] in nonces:
            raise ValueError('GROUNDED_SENSOR_OBSERVATION_TIME_OR_REPLAY')
        last_tick = tick; nonces.add(row['observation_nonce']); _text(row['observation_nonce'], 'NONCE', 128)
        records = [_normal_reading(env, sensors, claim, row['observation_nonce'], tick) for env in row['reading_envelopes']]
        ids = [record['reading_id'] for record in records]
        hashes = [record['envelope']['payload']['raw_evidence_sha256'] for record in records]
        if (len(records) < MIN_SENSORS or len(ids) != len(set(ids)) or any(item in reading_ids for item in ids)
                or len(hashes) != len(set(hashes)) or any(item in raw_hashes for item in hashes)):
            raise ValueError('GROUNDED_SENSOR_READING_REPLAY')
        reading_ids.update(ids); raw_hashes.update(hashes)
        fingerprints = sorted({record['device_key_sha256'] for record in records})
        sensor_domains = sorted({record['sensor_domain'] for record in records})
        calibration_domains = sorted({record['calibration_domain'] for record in records})
        adapters = sorted({record['adapter_sha256'] for record in records})
        if (len(fingerprints) < MIN_SENSORS or len(sensor_domains) < MIN_SENSOR_DOMAINS
                or len(calibration_domains) < MIN_SENSOR_DOMAINS or len(adapters) < MIN_ADAPTERS):
            raise ValueError('GROUNDED_SENSOR_QUORUM')
        values = [record['observed_value'] for record in records]
        consensus = truth._consensus_value(values, claim['value_type'])
        match = consensus is not None and truth._matches(claim, consensus)
        if (row['reading_ids'] != ids or row['device_fingerprints'] != fingerprints
                or row['sensor_domains'] != sensor_domains or row['calibration_domains'] != calibration_domains
                or row['adapter_hashes'] != adapters or row['consensus_value'] != consensus
                or row['claim_match'] is not match or row['status'] != 'CALIBRATED_SENSOR_CONSENSUS_ONLY'
                or row['observation_sha256'] != _row_hash(row, 'observation_sha256')):
            raise ValueError('GROUNDED_SENSOR_OBSERVATION_DERIVATION')
        observation_map[row['observation_sha256']] = row; previous = row['observation_sha256']
    if state['observation_head_sha256'] != previous:
        raise ValueError('GROUNDED_SENSOR_OBSERVATION_HEAD')
    from . import sensor_action
    sensor_action.validate(state)
    previous = ZERO; challenged = set(); receipts = set()
    for index, row in enumerate(state['outcomes'], 1):
        required_row = {'seq', 'observation_sha256', 'verifier_id', 'verifier_key_sha256',
                        'runtime_id', 'action_id', 'action_context_sha256', 'success',
                        'resource_credit', 'receipt_envelope', 'receipt_id', 'status',
                        'metabolism_result', 'previous_outcome_sha256', 'outcome_sha256'}
        if set(row) != required_row or row['seq'] != index or row['previous_outcome_sha256'] != previous:
            raise ValueError('GROUNDED_SENSOR_OUTCOME_ROW')
        observation = observation_map.get(row['observation_sha256']); verifier = verifiers.get(row['verifier_id'])
        if observation is None or verifier is None or row['observation_sha256'] in challenged:
            raise ValueError('GROUNDED_SENSOR_OUTCOME_BINDING')
        challenged.add(row['observation_sha256'])
        schema = row['receipt_envelope'].get('payload', {}).get('schema')
        if schema not in (OUTCOME_RECEIPT_SCHEMA, sensor_action.RECEIPT_SCHEMA):
            raise ValueError('GROUNDED_SENSOR_OUTCOME_SCHEMA')
        payload = _verify(row['receipt_envelope'], verifier['public_key'], schema)
        expected = {'schema', 'receipt_id', 'verifier_id', 'observation_sha256', 'observation_nonce',
                    'runtime_id', 'action_id', 'action_context_sha256', 'result_evidence_sha256',
                    'observed_at_tick', 'success', 'resource_credit'}
        if schema == sensor_action.RECEIPT_SCHEMA:
            expected.update({'intent_sha256', 'result_observation_sha256'})
        if set(payload) != expected:
            raise ValueError('GROUNDED_SENSOR_OUTCOME_RECEIPT_FIELDS')
        if (payload['verifier_id'] != verifier['verifier_id'] or payload['observation_sha256'] != row['observation_sha256']
                or payload['observation_nonce'] != observation['observation_nonce']
                or payload['runtime_id'] != row['runtime_id'] or payload['action_id'] != row['action_id']
                or payload['action_context_sha256'] != row['action_context_sha256']
                or not observation['observed_at_tick'] <= payload['observed_at_tick'] <= observation['expires_at_tick']
                or payload['success'] is not row['success'] or payload['resource_credit'] != row['resource_credit']):
            raise ValueError('GROUNDED_SENSOR_OUTCOME_RECEIPT_BINDING')
        _sha(payload['result_evidence_sha256'], 'RESULT_EVIDENCE_SHA256')
        _tick(payload['observed_at_tick'], 'OUTCOME_TICK')
        if type(payload['success']) is not bool or type(payload['resource_credit']) is not int or not 0 <= payload['resource_credit'] <= 1000:
            raise ValueError('GROUNDED_SENSOR_OUTCOME_VALUE')
        if not payload['success'] and payload['resource_credit'] != 0:
            raise ValueError('GROUNDED_SENSOR_FAILED_ACTION_CREDIT')
        if schema == sensor_action.RECEIPT_SCHEMA:
            sensor_action.authorize(state, payload)
        elif payload['resource_credit']:
            raise ValueError('SENSOR_ACTION_PRECOMMIT_REQUIRED')
        if row['receipt_id'] != payload['receipt_id'] or row['receipt_id'] in receipts:
            raise ValueError('GROUNDED_SENSOR_RECEIPT_REPLAY')
        receipts.add(row['receipt_id'])
        expected_status = 'GROUNDED_ACTION_CONFIRMED' if row['success'] else 'GROUNDED_ACTION_REFUTED'
        if (row['verifier_key_sha256'] != verifier['public_key_sha256'] or row['status'] != expected_status
                or row['outcome_sha256'] != _row_hash(row, 'outcome_sha256')):
            raise ValueError('GROUNDED_SENSOR_OUTCOME_DERIVATION')
        previous = row['outcome_sha256']
    if state['outcome_head_sha256'] != previous:
        raise ValueError('GROUNDED_SENSOR_OUTCOME_HEAD')
    boundary = state['claim_boundary']
    if (boundary.get('sensor_consensus_establishes_external_truth') is not False
            or boundary.get('configured_domains_prove_real_world_independence') is not False
            or boundary.get('literal_soul_established') is not False
            or boundary.get('consciousness_established') is not False):
        raise ValueError('GROUNDED_SENSOR_CLAIM_BOUNDARY')


def load(data):
    if not (Path(data) / NS / 'commits').exists():
        if needs_preflight(data):
            raise ValueError('GROUNDED_SENSOR_HISTORY_MISSING')
        raise ValueError('GROUNDED_SENSOR_NOT_INITIALIZED')
    return store.load(data, NS, COMPONENT, validate)


def _public(state):
    return {'ok': True, 'version': 'v1022.7.3', 'individual_id': state['individual_id'],
            'authority_count': len(state['authorities']), 'sensor_count': len(state['sensors']),
            'verifier_count': len(state['verifiers']), 'observation_count': len(state['observations']),
            'outcome_count': len(state['outcomes']),
            'decision_count': len(state['decisions']), 'intent_count': len(state['intents']),
            'decision_history': copy.deepcopy(state['decisions']),
            'observation_statuses': {row['observation_sha256']: row['status'] for row in state['observations']},
            'outcome_statuses': {row['observation_sha256']: row['status'] for row in state['outcomes']},
            'outcome_hashes': {row['observation_sha256']: row['outcome_sha256'] for row in state['outcomes']},
            'claim_boundary': copy.deepcopy(state['claim_boundary'])}


@transactional()
def integrate(data):
    require_alive(data); ident = _live_identity(data)
    try:
        old = load(data)
    except ValueError as exc:
        if str(exc) != 'GROUNDED_SENSOR_NOT_INITIALIZED':
            raise
        old = None
    state = {'schema': SCHEMA, 'individual_id': ident['individual_id'], 'lineage_id': ident['lineage_id'],
             'branch_id': ident['branch_id'], 'integration_seq': int(old.get('integration_seq', 0)) + 1 if old else 1,
             'authorities': copy.deepcopy(old.get('authorities', [])) if old else [],
             'authority_head_sha256': old.get('authority_head_sha256', ZERO) if old else ZERO,
             'sensors': copy.deepcopy(old.get('sensors', [])) if old else [],
             'sensor_head_sha256': old.get('sensor_head_sha256', ZERO) if old else ZERO,
             'verifiers': copy.deepcopy(old.get('verifiers', [])) if old else [],
             'verifier_head_sha256': old.get('verifier_head_sha256', ZERO) if old else ZERO,
             'observations': copy.deepcopy(old.get('observations', [])) if old else [],
             'observation_head_sha256': old.get('observation_head_sha256', ZERO) if old else ZERO,
             'outcomes': copy.deepcopy(old.get('outcomes', [])) if old else [],
             'outcome_head_sha256': old.get('outcome_head_sha256', ZERO) if old else ZERO,
             'decisions': copy.deepcopy(old.get('decisions', [])) if old else [],
             'decision_head_sha256': old.get('decision_head_sha256', ZERO) if old else ZERO,
             'intents': copy.deepcopy(old.get('intents', [])) if old else [],
             'intent_head_sha256': old.get('intent_head_sha256', ZERO) if old else ZERO,
             'claim_boundary': {'typed_claims_required': True, 'signed_device_identity_required': True,
                 'signed_calibration_required': True, 'bounded_time_and_nonce_required': True,
                 'minimum_distinct_sensor_keys': MIN_SENSORS, 'minimum_configured_sensor_domains': MIN_SENSOR_DOMAINS,
                 'minimum_declared_adapter_hashes': MIN_ADAPTERS, 'action_verifier_role_separated': True,
                 'adapter_binary_implementation_independently_attested': False,
                 'successful_outcome_can_transfer_finite_metabolic_resource': True,
                 'sensor_consensus_establishes_external_truth': False,
                 'configured_domains_prove_real_world_independence': False,
                 'literal_soul_established': False, 'consciousness_established': False,
                 'personhood_established': False}}
    validate(state); store.save(data, NS, COMPONENT, state); return _public(state)


@transactional()
def add_authority(data, authority):
    require_alive(data); integrate(data); state = load(data)
    if state['observations']:
        raise ValueError('GROUNDED_SENSOR_REGISTRY_SEALED')
    normalized = _normal_authority(authority)
    forbidden = {r['sensor']['device_key_sha256'] for r in state['sensors']}
    forbidden.update(r['verifier']['public_key_sha256'] for r in state['verifiers'])
    if normalized['public_key_sha256'] in forbidden:
        raise ValueError('GROUNDED_SENSOR_CROSS_ROLE_KEY_REUSE')
    if any(normalized['authority_id'] == row['authority']['authority_id'] or normalized['public_key_sha256'] == row['authority']['public_key_sha256'] or normalized['calibration_domain'] == row['authority']['calibration_domain'] for row in state['authorities']):
        raise ValueError('GROUNDED_SENSOR_AUTHORITY_REPLAY')
    row = {'seq': len(state['authorities']) + 1, 'authority': normalized,
           'previous_authority_sha256': state['authority_head_sha256']}
    row['authority_row_sha256'] = _row_hash(row, 'authority_row_sha256')
    state['authorities'].append(row); state['authority_head_sha256'] = row['authority_row_sha256']
    validate(state); store.save(data, NS, COMPONENT, state); return {'ok': True, 'authority': normalized}


@transactional()
def add_sensor(data, certificate):
    require_alive(data); integrate(data); state = load(data)
    if state['observations']:
        raise ValueError('GROUNDED_SENSOR_REGISTRY_SEALED')
    authorities = {row['authority']['authority_id']: row['authority'] for row in state['authorities']}
    sensor = _normal_sensor(certificate, authorities)
    if any(sensor['device_id'] == row['sensor']['device_id'] or sensor['device_key_sha256'] == row['sensor']['device_key_sha256'] or sensor['certificate_id'] == row['sensor']['certificate_id'] for row in state['sensors']):
        raise ValueError('GROUNDED_SENSOR_SENSOR_REPLAY')
    forbidden = {row['authority']['public_key_sha256'] for row in state['authorities']}
    forbidden.update(row['verifier']['public_key_sha256'] for row in state['verifiers'])
    if sensor['device_key_sha256'] in forbidden:
        raise ValueError('GROUNDED_SENSOR_CROSS_ROLE_KEY_REUSE')
    row = {'seq': len(state['sensors']) + 1, 'sensor': sensor,
           'previous_sensor_sha256': state['sensor_head_sha256']}
    row['sensor_row_sha256'] = _row_hash(row, 'sensor_row_sha256')
    state['sensors'].append(row); state['sensor_head_sha256'] = row['sensor_row_sha256']
    validate(state); store.save(data, NS, COMPONENT, state); return {'ok': True, 'sensor': sensor}


@transactional()
def add_verifier(data, verifier):
    require_alive(data); integrate(data); state = load(data)
    if state['observations']:
        raise ValueError('GROUNDED_SENSOR_REGISTRY_SEALED')
    normalized = _normal_verifier(verifier)
    forbidden = {row['authority']['public_key_sha256'] for row in state['authorities']}
    forbidden.update(row['sensor']['device_key_sha256'] for row in state['sensors'])
    forbidden.update(row['verifier']['public_key_sha256'] for row in state['verifiers'])
    if normalized['public_key_sha256'] in forbidden:
        raise ValueError('GROUNDED_SENSOR_CROSS_ROLE_KEY_REUSE')
    if any(normalized['verifier_id'] == row['verifier']['verifier_id'] for row in state['verifiers']):
        raise ValueError('GROUNDED_SENSOR_VERIFIER_REPLAY')
    row = {'seq': len(state['verifiers']) + 1, 'verifier': normalized,
           'previous_verifier_sha256': state['verifier_head_sha256']}
    row['verifier_row_sha256'] = _row_hash(row, 'verifier_row_sha256')
    state['verifiers'].append(row); state['verifier_head_sha256'] = row['verifier_row_sha256']
    validate(state); store.save(data, NS, COMPONENT, state); return {'ok': True, 'verifier': normalized}


@transactional()
def observe(data, bundle):
    require_alive(data); integrate(data); state = load(data)
    if not isinstance(bundle, dict) or set(bundle) != {'schema', 'observation_nonce', 'observed_at_tick', 'expires_at_tick', 'claim', 'readings'} or bundle.get('schema') != OBSERVATION_BUNDLE_SCHEMA:
        raise ValueError('GROUNDED_SENSOR_OBSERVATION_BUNDLE_FIELDS')
    claim = truth._normal_claim(bundle['claim']); nonce = _text(bundle['observation_nonce'], 'NONCE', 128)
    tick = _tick(bundle['observed_at_tick'], 'OBSERVED_TICK'); expiry = _tick(bundle['expires_at_tick'], 'EXPIRY_TICK')
    if not tick < expiry <= tick + MAX_TICK_SPAN:
        raise ValueError('GROUNDED_SENSOR_OBSERVATION_WINDOW')
    if nonce in {row['observation_nonce'] for row in state['observations']} or (state['observations'] and tick < state['observations'][-1]['observed_at_tick']):
        raise ValueError('GROUNDED_SENSOR_OBSERVATION_REPLAY')
    sensor_map = {row['sensor']['device_id']: row['sensor'] for row in state['sensors']}
    envelopes = bundle['readings']
    if not isinstance(envelopes, list) or not MIN_SENSORS <= len(envelopes) <= 16:
        raise ValueError('GROUNDED_SENSOR_READING_COUNT')
    records = [_normal_reading(env, sensor_map, claim, nonce, tick) for env in envelopes]
    ids = [record['reading_id'] for record in records]; old_ids = {item for row in state['observations'] for item in row['reading_ids']}
    raw = [record['envelope']['payload']['raw_evidence_sha256'] for record in records]
    old_raw = {env['payload']['raw_evidence_sha256'] for row in state['observations'] for env in row['reading_envelopes']}
    if len(ids) != len(set(ids)) or any(item in old_ids for item in ids) or len(raw) != len(set(raw)) or any(item in old_raw for item in raw):
        raise ValueError('GROUNDED_SENSOR_READING_REPLAY')
    fingerprints = sorted({record['device_key_sha256'] for record in records})
    sensor_domains = sorted({record['sensor_domain'] for record in records})
    calibration_domains = sorted({record['calibration_domain'] for record in records})
    adapters = sorted({record['adapter_sha256'] for record in records})
    if len(fingerprints) < MIN_SENSORS or len(sensor_domains) < MIN_SENSOR_DOMAINS or len(calibration_domains) < MIN_SENSOR_DOMAINS or len(adapters) < MIN_ADAPTERS:
        raise ValueError('GROUNDED_SENSOR_QUORUM')
    consensus = truth._consensus_value([record['observed_value'] for record in records], claim['value_type'])
    match = consensus is not None and truth._matches(claim, consensus)
    row = {'seq': len(state['observations']) + 1, 'claim': claim, 'claim_sha256': sha_obj(claim),
           'observation_nonce': nonce, 'observed_at_tick': tick, 'expires_at_tick': expiry,
           'reading_envelopes': copy.deepcopy(envelopes), 'reading_ids': ids,
           'device_fingerprints': fingerprints, 'sensor_domains': sensor_domains,
           'calibration_domains': calibration_domains, 'adapter_hashes': adapters,
           'consensus_value': consensus, 'claim_match': match,
           'status': 'CALIBRATED_SENSOR_CONSENSUS_ONLY',
           'previous_observation_sha256': state['observation_head_sha256']}
    row['observation_sha256'] = _row_hash(row, 'observation_sha256')
    state['observations'].append(row); state['observation_head_sha256'] = row['observation_sha256']
    validate(state); store.save(data, NS, COMPONENT, state)
    return {'ok': True, 'version': 'v1022.7.3', 'observation_sha256': row['observation_sha256'],
            'status': row['status'], 'claim_match': match, 'consensus_value': consensus,
            'external_truth_verified': False, 'distinct_sensor_keys': len(fingerprints),
            'distinct_sensor_domains': len(sensor_domains), 'distinct_adapter_hashes': len(adapters)}


@transactional()
def apply_outcome(data, bundle):
    require_alive(data); integrate(data); state = load(data)
    if not isinstance(bundle, dict) or set(bundle) != {'schema', 'observation_sha256', 'runtime_id', 'action_id', 'action_context_sha256', 'receipt'} or bundle.get('schema') != OUTCOME_BUNDLE_SCHEMA:
        raise ValueError('GROUNDED_SENSOR_OUTCOME_BUNDLE_FIELDS')
    observation_sha = _sha(bundle['observation_sha256'], 'OBSERVATION_SHA256')
    observation = next((row for row in state['observations'] if row['observation_sha256'] == observation_sha), None)
    if observation is None or observation_sha in {row['observation_sha256'] for row in state['outcomes']}:
        raise ValueError('GROUNDED_SENSOR_OUTCOME_REPLAY_OR_UNKNOWN')
    payload0 = (bundle.get('receipt') or {}).get('payload', {})
    verifier = next((row['verifier'] for row in state['verifiers'] if row['verifier']['verifier_id'] == payload0.get('verifier_id')), None)
    if verifier is None:
        raise ValueError('GROUNDED_SENSOR_UNKNOWN_VERIFIER')
    from . import sensor_action
    schema = payload0.get('schema')
    if schema not in (OUTCOME_RECEIPT_SCHEMA, sensor_action.RECEIPT_SCHEMA):
        raise ValueError('GROUNDED_SENSOR_OUTCOME_SCHEMA')
    payload = _verify(bundle['receipt'], verifier['public_key'], schema)
    required = {'schema', 'receipt_id', 'verifier_id', 'observation_sha256', 'observation_nonce',
                'runtime_id', 'action_id', 'action_context_sha256', 'result_evidence_sha256',
                'observed_at_tick', 'success', 'resource_credit'}
    if schema == sensor_action.RECEIPT_SCHEMA:
        required.update({'intent_sha256', 'result_observation_sha256'})
    if set(payload) != required:
        raise ValueError('GROUNDED_SENSOR_OUTCOME_RECEIPT_FIELDS')
    runtime_id = _text(bundle['runtime_id'], 'RUNTIME_ID', 96); action_id = _text(bundle['action_id'], 'ACTION_ID', 96)
    action_context = _sha(bundle['action_context_sha256'], 'ACTION_CONTEXT_SHA256')
    if (payload['observation_sha256'] != observation_sha or payload['observation_nonce'] != observation['observation_nonce']
            or payload['runtime_id'] != runtime_id or payload['action_id'] != action_id
            or payload['action_context_sha256'] != action_context
            or not observation['observed_at_tick'] <= payload['observed_at_tick'] <= observation['expires_at_tick']
            or payload['observed_at_tick'] < state['observations'][-1]['observed_at_tick']):
        raise ValueError('GROUNDED_SENSOR_OUTCOME_RECEIPT_BINDING')
    _sha(payload['result_evidence_sha256'], 'RESULT_EVIDENCE_SHA256')
    _tick(payload['observed_at_tick'], 'OUTCOME_TICK')
    success = payload['success']; credit = payload['resource_credit']
    if type(success) is not bool or type(credit) is not int or not 0 <= credit <= 1000 or (not success and credit != 0):
        raise ValueError('GROUNDED_SENSOR_OUTCOME_VALUE')
    if schema == sensor_action.RECEIPT_SCHEMA:
        intent = sensor_action.authorize(state, payload)
        from . import metabolism
        current = metabolism.preflight(data)
        if current['runtimes'].get(runtime_id, {}).get('whole_sha256') != intent['runtime_head_sha256']:
            raise ValueError('SENSOR_ACTION_RUNTIME_CHANGED_SINCE_INTENT')
    elif credit:
        raise ValueError('SENSOR_ACTION_PRECOMMIT_REQUIRED')
    receipt_id = _text(payload['receipt_id'], 'RECEIPT_ID', 96)
    if receipt_id in {row['receipt_id'] for row in state['outcomes']}:
        raise ValueError('GROUNDED_SENSOR_RECEIPT_REPLAY')
    metabolism_result = None
    row = {'seq': len(state['outcomes']) + 1, 'observation_sha256': observation_sha,
           'verifier_id': verifier['verifier_id'], 'verifier_key_sha256': verifier['public_key_sha256'],
           'runtime_id': runtime_id, 'action_id': action_id, 'action_context_sha256': action_context,
           'success': success, 'resource_credit': credit, 'receipt_envelope': copy.deepcopy(bundle['receipt']),
           'receipt_id': receipt_id, 'status': 'GROUNDED_ACTION_CONFIRMED' if success else 'GROUNDED_ACTION_REFUTED',
           'metabolism_result': metabolism_result, 'previous_outcome_sha256': state['outcome_head_sha256']}
    row['outcome_sha256'] = _row_hash(row, 'outcome_sha256')
    state['outcomes'].append(row); state['outcome_head_sha256'] = row['outcome_sha256']
    validate(state); store.save(data, NS, COMPONENT, state)
    if success and credit:
        from . import metabolism
        from tukuyo_common.atomic_fs import maybe_crash
        maybe_crash('sensor:after_outcome_stage')
        metabolism_result = metabolism.grounded_reward(data, runtime_id, credit, sha_obj(bundle['receipt']))
        maybe_crash('sensor:after_reward')
        row['metabolism_result'] = metabolism_result
        row['outcome_sha256'] = _row_hash(row, 'outcome_sha256')
        state['outcome_head_sha256'] = row['outcome_sha256']
        validate(state); store.save(data, NS, COMPONENT, state)
    return {'ok': True, 'version': 'v1022.7.3', 'status': row['status'], 'success': success,
            'resource_credit_requested': credit, 'metabolism_result': metabolism_result,
            'outcome_sha256': row['outcome_sha256'],    # v1022.7.9: what experience-observed cites
            'external_truth_verified': False}


def status(data):
    state = load(data); result = _public(state); result['audit'] = audit(data); return result


def audit(data):
    try:
        state = load(data); ident = _live_identity(data); errors = []
        if any(state.get(key) != ident[key] for key in ('individual_id', 'lineage_id', 'branch_id')):
            errors.append('GROUNDED_SENSOR_IDENTITY')
        paid = [r for r in state['outcomes'] if r['success'] and r['resource_credit']]
        if paid:
            from . import metabolism
            metabolic = metabolism.preflight(data)
            for row in paid:
                digest = sha_obj(row['receipt_envelope'])
                reward = next((r for r in metabolic.get('grounded_rewards', []) if r['receipt_sha256'] == digest), None)
                result = row['metabolism_result']
                if (not reward or not isinstance(result, dict) or reward['runtime'] != row['runtime_id']
                        or reward['requested'] != row['resource_credit'] or result.get('paid') != reward['paid']
                        or result.get('energy_before') != reward['energy_before'] or result.get('energy_after') != reward['energy_after']):
                    errors.append('GROUNDED_SENSOR_METABOLISM_BINDING')
        return {'ok': not errors, 'version': 'v1022.7.3', 'errors': errors,
                'authority_count': len(state['authorities']), 'sensor_count': len(state['sensors']),
                'verifier_count': len(state['verifiers']), 'observation_count': len(state['observations']),
                'outcome_count': len(state['outcomes']), 'device_signatures_verified': not errors,
                'calibration_chains_verified': not errors, 'bounded_time_and_replay_verified': not errors,
                'external_truth_verified': False, 'real_world_independence_verified': False,
                'literal_soul_established': False, 'consciousness_established': False}
    except (ValueError, TypeError, KeyError, OSError) as exc:
        return {'ok': False, 'version': 'v1022.7.3', 'errors': [type(exc).__name__ + ':' + str(exc)],
                'external_truth_verified': False, 'real_world_independence_verified': False,
                'literal_soul_established': False, 'consciousness_established': False}
