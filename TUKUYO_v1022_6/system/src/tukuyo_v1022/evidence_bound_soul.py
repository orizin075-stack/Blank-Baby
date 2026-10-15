"""Authenticated, evidence-bound reflection layered over V1022.6.9.

This module separates four claims that V1022.6.9 could not safely combine:
configured trust, cryptographic authorship, multi-domain agreement, and truth.
It verifies the first three under explicit assumptions.  It never claims that a
signed statement is true, that configured domains are socially independent, or
that the runtime is conscious / a person / a literal soul.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import re
import statistics
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from tukuyo_v977 import whole_state as whole
from tukuyo_v977.whole_state import _live_identity, sha_obj
from tukuyo_v1019.lifecycle import require_alive
from tukuyo_v1019.transaction import transactional
from . import reflective_soul as reflective
from . import store


NS = 'evidence_bound_soul'
COMPONENT = 'whole_evidence_bound_soul'
SCHEMA = 'tukuyo.v1022_7.evidence_bound_soul/1'
AUTHORITY_SCHEMA = 'tukuyo.v1022_7.authority/1'
WITNESS_SCHEMA = 'tukuyo.v1022_7.witness_certificate/1'
ASSESSMENT_SCHEMA = 'tukuyo.v1022_7.option_assessment/1'
BUNDLE_SCHEMA = 'tukuyo.v1022_7.option_assessment_bundle/1'
ATTESTATION_SCHEMA = 'tukuyo.v1022_7.outcome_attestation/1'
ZERO = '0' * 64
MIN_TRUST_DOMAINS = 3
MIN_WITNESSES = 3
MEASUREMENT_KINDS = ('sensor_reading', 'bounded_evaluator', 'human_attestation')


def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _text(value, label, limit=160):
    if (not isinstance(value, str) or not value or len(value) > limit
            or re.search(r'[\x00-\x1f]', value)):
        raise ValueError('EVIDENCE_SOUL_' + label)
    return value


def _sha256(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value) or value == ZERO:
        raise ValueError('EVIDENCE_SOUL_SHA256')
    return value


def _public_key(value, label='PUBLIC_KEY'):
    try:
        raw = base64.b64decode(value, validate=True)
        if len(raw) != 32:
            raise ValueError
        Ed25519PublicKey.from_public_bytes(raw)
    except Exception as exc:
        raise ValueError('EVIDENCE_SOUL_' + label) from exc
    return value, hashlib.sha256(raw).hexdigest()


def _verify_envelope(envelope, expected_public_key, schema):
    if not isinstance(envelope, dict) or set(envelope) != {'payload', 'public_key', 'signature'}:
        raise ValueError('EVIDENCE_SOUL_ENVELOPE_FIELDS')
    if envelope.get('public_key') != expected_public_key:
        raise ValueError('EVIDENCE_SOUL_SIGNER_MISMATCH')
    payload = envelope.get('payload')
    if not isinstance(payload, dict) or payload.get('schema') != schema:
        raise ValueError('EVIDENCE_SOUL_ENVELOPE_SCHEMA')
    try:
        public_raw = base64.b64decode(expected_public_key, validate=True)
        signature = base64.b64decode(envelope.get('signature', ''), validate=True)
        Ed25519PublicKey.from_public_bytes(public_raw).verify(signature, whole.canon(payload))
    except Exception as exc:
        raise ValueError('EVIDENCE_SOUL_SIGNATURE') from exc
    return payload


def _hash_row(row, field):
    value = copy.deepcopy(row)
    value.pop(field, None)
    return sha_obj(value)


def _normal_authority(authority):
    if not isinstance(authority, dict) or set(authority) != {
            'schema', 'authority_id', 'trust_domain', 'public_key'}:
        raise ValueError('EVIDENCE_SOUL_AUTHORITY_FIELDS')
    if authority.get('schema') != AUTHORITY_SCHEMA:
        raise ValueError('EVIDENCE_SOUL_AUTHORITY_SCHEMA')
    public_key, fingerprint = _public_key(authority.get('public_key'))
    return {
        'schema': AUTHORITY_SCHEMA,
        'authority_id': _text(authority.get('authority_id'), 'AUTHORITY_ID', 96),
        'trust_domain': _text(authority.get('trust_domain'), 'TRUST_DOMAIN', 96),
        'public_key': public_key,
        'public_key_sha256': fingerprint,
        'configured_not_real_world_independence_proof': True,
    }


def _authority_input(record):
    return {k: record[k] for k in ('schema', 'authority_id', 'trust_domain', 'public_key')}


def _authorities(state):
    return {row['authority']['authority_id']: row['authority'] for row in state['authorities']}


def _normal_witness(certificate, authority_map):
    authority_id = None
    if isinstance(certificate, dict):
        authority_id = (certificate.get('payload') or {}).get('authority_id')
    authority = authority_map.get(authority_id)
    if authority is None:
        raise ValueError('EVIDENCE_SOUL_UNKNOWN_AUTHORITY')
    payload = _verify_envelope(certificate, authority['public_key'], WITNESS_SCHEMA)
    required = {'schema', 'certificate_id', 'observer_id', 'observer_public_key',
                'authority_id', 'trust_domain'}
    if set(payload) != required:
        raise ValueError('EVIDENCE_SOUL_WITNESS_FIELDS')
    if payload['authority_id'] != authority['authority_id'] or payload['trust_domain'] != authority['trust_domain']:
        raise ValueError('EVIDENCE_SOUL_WITNESS_AUTHORITY_BINDING')
    observer_public_key, observer_fingerprint = _public_key(
        payload['observer_public_key'], 'OBSERVER_PUBLIC_KEY')
    return {
        'certificate': copy.deepcopy(certificate),
        'certificate_sha256': sha_obj(certificate),
        'certificate_id': _text(payload['certificate_id'], 'CERTIFICATE_ID', 96),
        'observer_id': _text(payload['observer_id'], 'OBSERVER_ID', 96),
        'observer_public_key': observer_public_key,
        'observer_key_sha256': observer_fingerprint,
        'authority_id': authority['authority_id'],
        'trust_domain': authority['trust_domain'],
    }


def _witnesses(state):
    return {row['witness']['observer_id']: row['witness'] for row in state['witnesses']}


def _normal_core_options(options):
    if not isinstance(options, list) or not 2 <= len(options) <= 16:
        raise ValueError('EVIDENCE_SOUL_OPTIONS')
    normalized = []
    for option in options:
        if not isinstance(option, dict) or set(option) != {'id', 'signals', 'themes', 'conflicts'}:
            raise ValueError('EVIDENCE_SOUL_OPTION_FIELDS')
        checked = reflective._core_option({**option, 'effects': {}})
        checked.pop('effects')
        normalized.append(checked)
    ids = [row['id'] for row in normalized]
    if len(ids) != len(set(ids)):
        raise ValueError('EVIDENCE_SOUL_OPTION_IDS')
    return normalized


def _normal_effects(effects):
    if not isinstance(effects, dict) or set(effects) != set(reflective.EFFECTS):
        raise ValueError('EVIDENCE_SOUL_EFFECT_COVERAGE')
    result = {}
    for key in reflective.EFFECTS:
        result[key] = reflective._number(
            effects[key], key.upper(), 0.0 if key in ('bodily_cost', 'uncertainty') else -1.0, 1.0)
    return result


def _normal_assessment(envelope, witness_map, options, context):
    observer_id = None
    if isinstance(envelope, dict):
        observer_id = (envelope.get('payload') or {}).get('observer_id')
    witness = witness_map.get(observer_id)
    if witness is None:
        raise ValueError('EVIDENCE_SOUL_UNKNOWN_WITNESS')
    payload = _verify_envelope(envelope, witness['observer_public_key'], ASSESSMENT_SCHEMA)
    required = {'schema', 'assessment_id', 'observer_id', 'options_sha256',
                'context_sha256', 'measurement_kind', 'evidence_sha256', 'effects_by_option'}
    if set(payload) != required:
        raise ValueError('EVIDENCE_SOUL_ASSESSMENT_FIELDS')
    if payload['observer_id'] != witness['observer_id']:
        raise ValueError('EVIDENCE_SOUL_ASSESSMENT_OBSERVER')
    if payload['options_sha256'] != sha_obj(options) or payload['context_sha256'] != sha_obj(context):
        raise ValueError('EVIDENCE_SOUL_ASSESSMENT_BINDING')
    if payload['measurement_kind'] not in MEASUREMENT_KINDS:
        raise ValueError('EVIDENCE_SOUL_MEASUREMENT_KIND')
    _sha256(payload['evidence_sha256'])
    effects = payload['effects_by_option']
    ids = [row['id'] for row in options]
    if not isinstance(effects, dict) or set(effects) != set(ids):
        raise ValueError('EVIDENCE_SOUL_ASSESSMENT_OPTION_COVERAGE')
    normalized_effects = {oid: _normal_effects(effects[oid]) for oid in ids}
    normalized_payload = copy.deepcopy(payload)
    normalized_payload['assessment_id'] = _text(payload['assessment_id'], 'ASSESSMENT_ID', 96)
    normalized_payload['effects_by_option'] = normalized_effects
    if normalized_payload != payload:
        raise ValueError('EVIDENCE_SOUL_ASSESSMENT_CANONICAL')
    return {
        'envelope': copy.deepcopy(envelope),
        'assessment_id': normalized_payload['assessment_id'],
        'observer_id': witness['observer_id'],
        'observer_key_sha256': witness['observer_key_sha256'],
        'authority_id': witness['authority_id'],
        'trust_domain': witness['trust_domain'],
        'effects_by_option': normalized_effects,
    }


def _aggregate_assessments(records, option_ids):
    result = {}
    for option_id in option_ids:
        result[option_id] = {}
        for effect in reflective.EFFECTS:
            values = [float(row['effects_by_option'][option_id][effect]) for row in records]
            result[option_id][effect] = round(float(statistics.median(values)), 6)
    return result


def _normal_attestation(envelope, witness_map):
    observer_id = None
    if isinstance(envelope, dict):
        observer_id = (envelope.get('payload') or {}).get('observer_id')
    witness = witness_map.get(observer_id)
    if witness is None:
        raise ValueError('EVIDENCE_SOUL_UNKNOWN_WITNESS')
    payload = _verify_envelope(envelope, witness['observer_public_key'], ATTESTATION_SCHEMA)
    required = {'schema', 'attestation_id', 'observer_id', 'decision_sha256', 'chosen',
                'measurement_kind', 'evidence_sha256', 'source_kind', 'self_wellbeing',
                'others_wellbeing', 'future_self', 'truth_consistency', 'bodily_cost',
                'surprise', 'confidence', 'note'}
    if set(payload) != required:
        raise ValueError('EVIDENCE_SOUL_ATTESTATION_FIELDS')
    normalized = {
        'schema': ATTESTATION_SCHEMA,
        'attestation_id': _text(payload['attestation_id'], 'ATTESTATION_ID', 80),
        'observer_id': witness['observer_id'],
        'decision_sha256': _sha256(payload['decision_sha256']),
        'chosen': _text(payload['chosen'], 'CHOSEN', 96),
        'measurement_kind': payload['measurement_kind'],
        'evidence_sha256': _sha256(payload['evidence_sha256']),
        'source_kind': payload['source_kind'],
    }
    if normalized['measurement_kind'] not in MEASUREMENT_KINDS:
        raise ValueError('EVIDENCE_SOUL_MEASUREMENT_KIND')
    if normalized['source_kind'] not in ('direct_observation', 'external_report', 'self_report'):
        raise ValueError('EVIDENCE_SOUL_SOURCE_KIND')
    for key in reflective.OUTCOMES:
        normalized[key] = reflective._number(
            payload[key], key.upper(), 0.0 if key in ('bodily_cost', 'surprise', 'confidence') else -1.0, 1.0)
    note = payload['note']
    if not isinstance(note, str) or len(note) > 512 or re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', note):
        raise ValueError('EVIDENCE_SOUL_NOTE')
    normalized['note'] = note
    if normalized != payload:
        raise ValueError('EVIDENCE_SOUL_ATTESTATION_CANONICAL')
    return normalized, witness


def _status_for(decision_sha256, rows):
    strong = []
    for row in rows:
        payload = row['envelope']['payload']
        if payload['decision_sha256'] == decision_sha256 and float(payload['confidence']) >= .7:
            strong.append(row)
    domains = {row['trust_domain'] for row in strong}
    witnesses = {row['observer_key_sha256'] for row in strong}
    if len(domains) >= MIN_TRUST_DOMAINS and len(witnesses) >= MIN_WITNESSES:
        return 'MULTI_DOMAIN_ATTESTED'
    if len(domains) >= 2 and len(witnesses) >= 2:
        return 'MULTI_DOMAIN_LIMITED'
    if strong:
        return 'AUTHENTICATED_SINGLE_SOURCE'
    return 'AUTHENTICATED_LOW_CONFIDENCE'


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
                'authorities', 'authority_head_sha256', 'witnesses', 'witness_head_sha256',
                'decisions', 'decision_head_sha256', 'attestations',
                'attestation_head_sha256', 'claim_boundary'}
    if not isinstance(state, dict) or state.get('schema') != SCHEMA or set(state) != required:
        raise ValueError('EVIDENCE_SOUL_SCHEMA')
    for key in ('individual_id', 'lineage_id', 'branch_id'):
        _text(state[key], key.upper(), 160)
    if type(state['integration_seq']) is not int or state['integration_seq'] < 1:
        raise ValueError('EVIDENCE_SOUL_SEQ')

    previous = ZERO
    authority_ids = set()
    authority_keys = set()
    for seq, row in enumerate(state['authorities'], 1):
        if set(row) != {'seq', 'authority', 'previous_authority_sha256', 'authority_row_sha256'}:
            raise ValueError('EVIDENCE_SOUL_AUTHORITY_ROW')
        authority = _normal_authority(_authority_input(row['authority']))
        if authority != row['authority'] or row['seq'] != seq or row['previous_authority_sha256'] != previous:
            raise ValueError('EVIDENCE_SOUL_AUTHORITY_CHAIN')
        if authority['authority_id'] in authority_ids or authority['public_key_sha256'] in authority_keys:
            raise ValueError('EVIDENCE_SOUL_AUTHORITY_DUPLICATE')
        authority_ids.add(authority['authority_id'])
        authority_keys.add(authority['public_key_sha256'])
        if row['authority_row_sha256'] != _hash_row(row, 'authority_row_sha256'):
            raise ValueError('EVIDENCE_SOUL_AUTHORITY_HASH')
        previous = row['authority_row_sha256']
    if state['authority_head_sha256'] != previous:
        raise ValueError('EVIDENCE_SOUL_AUTHORITY_HEAD')
    authority_map = _authorities(state)

    previous = ZERO
    observer_ids = set()
    observer_keys = set()
    cert_ids = set()
    for seq, row in enumerate(state['witnesses'], 1):
        if set(row) != {'seq', 'witness', 'previous_witness_sha256', 'witness_row_sha256'}:
            raise ValueError('EVIDENCE_SOUL_WITNESS_ROW')
        witness = _normal_witness(row['witness']['certificate'], authority_map)
        if witness != row['witness'] or row['seq'] != seq or row['previous_witness_sha256'] != previous:
            raise ValueError('EVIDENCE_SOUL_WITNESS_CHAIN')
        if (witness['observer_id'] in observer_ids or witness['observer_key_sha256'] in observer_keys
                or witness['certificate_id'] in cert_ids):
            raise ValueError('EVIDENCE_SOUL_WITNESS_DUPLICATE')
        observer_ids.add(witness['observer_id'])
        observer_keys.add(witness['observer_key_sha256'])
        cert_ids.add(witness['certificate_id'])
        if row['witness_row_sha256'] != _hash_row(row, 'witness_row_sha256'):
            raise ValueError('EVIDENCE_SOUL_WITNESS_HASH')
        previous = row['witness_row_sha256']
    if state['witness_head_sha256'] != previous:
        raise ValueError('EVIDENCE_SOUL_WITNESS_HEAD')
    witness_map = _witnesses(state)

    previous = ZERO
    decision_ids = set()
    assessment_ids = set()
    assessment_evidence = set()
    for seq, row in enumerate(state['decisions'], 1):
        required_row = {'seq', 'context', 'core_options', 'core_options_sha256',
                        'assessment_envelopes', 'assessment_ids', 'witness_fingerprints',
                        'trust_domains', 'aggregated_effects', 'reflective_decision_sha256',
                        'chosen', 'best_candidate', 'review_required',
                        'previous_decision_sha256', 'decision_sha256'}
        if (set(row) not in (required_row, required_row | {'experience_learning'})
                or row['seq'] != seq or row['previous_decision_sha256'] != previous):
            raise ValueError('EVIDENCE_SOUL_DECISION_ROW')
        context = _text(row['context'], 'CONTEXT', 256)
        options = _normal_core_options(row['core_options'])
        if options != row['core_options'] or row['core_options_sha256'] != sha_obj(options):
            raise ValueError('EVIDENCE_SOUL_DECISION_OPTIONS')
        assessments = [_normal_assessment(env, witness_map, options, context)
                       for env in row['assessment_envelopes']]
        ids = [item['assessment_id'] for item in assessments]
        if len(ids) != len(set(ids)) or any(item in assessment_ids for item in ids):
            raise ValueError('EVIDENCE_SOUL_ASSESSMENT_REPLAY')
        assessment_ids.update(ids)
        evidence_hashes = [item['envelope']['payload']['evidence_sha256'] for item in assessments]
        if (len(evidence_hashes) != len(set(evidence_hashes))
                or any(item in assessment_evidence for item in evidence_hashes)):
            raise ValueError('EVIDENCE_SOUL_ASSESSMENT_EVIDENCE_REPLAY')
        assessment_evidence.update(evidence_hashes)
        fingerprints = sorted({item['observer_key_sha256'] for item in assessments})
        domains = sorted({item['trust_domain'] for item in assessments})
        if len(fingerprints) < MIN_WITNESSES or len(domains) < MIN_TRUST_DOMAINS:
            raise ValueError('EVIDENCE_SOUL_ASSESSMENT_QUORUM')
        if (row['assessment_ids'] != ids or row['witness_fingerprints'] != fingerprints
                or row['trust_domains'] != domains):
            raise ValueError('EVIDENCE_SOUL_ASSESSMENT_SUMMARY')
        aggregate = _aggregate_assessments(assessments, [option['id'] for option in options])
        if row['aggregated_effects'] != aggregate:
            raise ValueError('EVIDENCE_SOUL_AGGREGATE')
        _sha256(row['reflective_decision_sha256'])
        if row['chosen'] is not None:
            _text(row['chosen'], 'CHOSEN', 96)
        _text(row['best_candidate'], 'BEST_CANDIDATE', 96)
        if type(row['review_required']) is not bool:
            raise ValueError('EVIDENCE_SOUL_REVIEW_REQUIRED')
        if row['decision_sha256'] != _hash_row(row, 'decision_sha256'):
            raise ValueError('EVIDENCE_SOUL_DECISION_HASH')
        if row['decision_sha256'] in decision_ids:
            raise ValueError('EVIDENCE_SOUL_DECISION_DUPLICATE')
        decision_ids.add(row['decision_sha256'])
        previous = row['decision_sha256']
    if state['decision_head_sha256'] != previous:
        raise ValueError('EVIDENCE_SOUL_DECISION_HEAD')

    previous = ZERO
    attestation_ids = set()
    evidence_ids = set()
    rows_so_far = []
    decision_map = {row['decision_sha256']: row for row in state['decisions']}
    for seq, row in enumerate(state['attestations'], 1):
        required_row = {'seq', 'envelope', 'envelope_sha256', 'observer_key_sha256',
                        'authority_id', 'trust_domain', 'derived_status',
                        'legacy_reflection_sha256', 'previous_attestation_sha256',
                        'attestation_sha256'}
        if set(row) != required_row or row['seq'] != seq or row['previous_attestation_sha256'] != previous:
            raise ValueError('EVIDENCE_SOUL_ATTESTATION_ROW')
        payload, witness = _normal_attestation(row['envelope'], witness_map)
        decision = decision_map.get(payload['decision_sha256'])
        if decision is None or decision['chosen'] is None or payload['chosen'] != decision['chosen']:
            raise ValueError('EVIDENCE_SOUL_ATTESTATION_DECISION')
        if payload['attestation_id'] in attestation_ids or payload['evidence_sha256'] in evidence_ids:
            raise ValueError('EVIDENCE_SOUL_ATTESTATION_REPLAY')
        attestation_ids.add(payload['attestation_id'])
        evidence_ids.add(payload['evidence_sha256'])
        if (row['envelope_sha256'] != sha_obj(row['envelope'])
                or row['observer_key_sha256'] != witness['observer_key_sha256']
                or row['authority_id'] != witness['authority_id']
                or row['trust_domain'] != witness['trust_domain']):
            raise ValueError('EVIDENCE_SOUL_ATTESTATION_BINDING')
        _sha256(row['legacy_reflection_sha256'])
        rows_so_far.append(row)
        if row['derived_status'] != _status_for(payload['decision_sha256'], rows_so_far):
            raise ValueError('EVIDENCE_SOUL_ATTESTATION_STATUS')
        if row['attestation_sha256'] != _hash_row(row, 'attestation_sha256'):
            raise ValueError('EVIDENCE_SOUL_ATTESTATION_HASH')
        previous = row['attestation_sha256']
    if state['attestation_head_sha256'] != previous:
        raise ValueError('EVIDENCE_SOUL_ATTESTATION_HEAD')

    from .soul_experience_learning import replay_prefix
    for index, row in enumerate(state['decisions']):
        if 'experience_learning' in row:
            replay_prefix(state, index, row['experience_learning'])

    boundary = state['claim_boundary']
    if (not isinstance(boundary, dict)
            or boundary.get('signatures_establish_truth') is not False
            or boundary.get('authority_domains_prove_real_world_independence') is not False
            or boundary.get('literal_soul_established') is not False
            or boundary.get('consciousness_established') is not False):
        raise ValueError('EVIDENCE_SOUL_CLAIM_BOUNDARY')


def load(data):
    if not (Path(data) / NS / 'commits').exists():
        if needs_preflight(data):
            raise ValueError('EVIDENCE_SOUL_HISTORY_MISSING')
        raise ValueError('EVIDENCE_SOUL_NOT_INITIALIZED')
    return store.load(data, NS, COMPONENT, validate)


@transactional()
def integrate(data):
    require_alive(data)
    from . import experience_provenance as provenance
    if provenance.needs_preflight(data):provenance.preflight(data)
    reflective.integrate(data)
    ident = _live_identity(data)
    try:
        old = load(data)
    except ValueError as exc:
        if str(exc) != 'EVIDENCE_SOUL_NOT_INITIALIZED':
            raise
        old = None
    state = {
        'schema': SCHEMA,
        'individual_id': ident['individual_id'],
        'lineage_id': ident['lineage_id'],
        'branch_id': ident['branch_id'],
        'integration_seq': int(old.get('integration_seq', 0)) + 1 if old else 1,
        'authorities': copy.deepcopy(old.get('authorities', [])) if old else [],
        'authority_head_sha256': old.get('authority_head_sha256', ZERO) if old else ZERO,
        'witnesses': copy.deepcopy(old.get('witnesses', [])) if old else [],
        'witness_head_sha256': old.get('witness_head_sha256', ZERO) if old else ZERO,
        'decisions': copy.deepcopy(old.get('decisions', [])) if old else [],
        'decision_head_sha256': old.get('decision_head_sha256', ZERO) if old else ZERO,
        'attestations': copy.deepcopy(old.get('attestations', [])) if old else [],
        'attestation_head_sha256': old.get('attestation_head_sha256', ZERO) if old else ZERO,
        'claim_boundary': {
            'authority_keys_are_explicitly_configured': True,
            'witness_certificates_are_signature_verified': True,
            'option_assessments_are_signature_verified': True,
            'outcome_attestations_are_signature_verified': True,
            'minimum_distinct_trust_domains': MIN_TRUST_DOMAINS,
            'registry_sealed_after_first_decision': True,
            'median_aggregation_tolerates_one_extreme_of_three': True,
            'signatures_establish_authorship_not_truth': True,
            'signatures_establish_truth': False,
            'authority_domains_prove_real_world_independence': False,
            'external_semantics_verified': False,
            'experience_learning_requires_repeated_signed_outcomes': True,
            'experience_learning_is_exact_context_and_option_bound': True,
            'legacy_unsigned_calibration_used_by_new_decisions': False,
            'authenticated_outcome_agreement_establishes_truth': False,
            'literal_soul_established': False,
            'consciousness_established': False,
            'personhood_established': False,
        },
    }
    validate(state)
    store.save(data, NS, COMPONENT, state)
    return _public(state)


@transactional()
def add_authority(data, authority):
    require_alive(data)
    from . import experience_provenance as provenance
    if provenance.needs_preflight(data):raise ValueError('PROVENANCE_TRUST_REGISTRY_SEALED')
    integrate(data)
    state = load(data)
    if state['decisions']:
        raise ValueError('EVIDENCE_SOUL_REGISTRY_SEALED')
    normalized = _normal_authority(authority)
    existing = [row['authority'] for row in state['authorities']]
    if any(row['authority_id'] == normalized['authority_id'] for row in existing):
        raise ValueError('EVIDENCE_SOUL_AUTHORITY_ID_REPLAY')
    if any(row['public_key_sha256'] == normalized['public_key_sha256'] for row in existing):
        raise ValueError('EVIDENCE_SOUL_AUTHORITY_KEY_REUSE')
    row = {
        'seq': len(existing) + 1,
        'authority': normalized,
        'previous_authority_sha256': state['authority_head_sha256'],
    }
    row['authority_row_sha256'] = _hash_row(row, 'authority_row_sha256')
    state['authorities'].append(row)
    state['authority_head_sha256'] = row['authority_row_sha256']
    validate(state)
    store.save(data, NS, COMPONENT, state)
    return {'ok': True, 'version': 'v1022.7', 'authority': copy.deepcopy(normalized),
            'authority_count': len(state['authorities']), 'claim_boundary': copy.deepcopy(state['claim_boundary'])}


@transactional()
def add_witness(data, certificate):
    require_alive(data)
    from . import experience_provenance as provenance
    if provenance.needs_preflight(data):raise ValueError('PROVENANCE_TRUST_REGISTRY_SEALED')
    integrate(data)
    state = load(data)
    if state['decisions']:
        raise ValueError('EVIDENCE_SOUL_REGISTRY_SEALED')
    normalized = _normal_witness(certificate, _authorities(state))
    existing = [row['witness'] for row in state['witnesses']]
    if any(row['observer_id'] == normalized['observer_id'] for row in existing):
        raise ValueError('EVIDENCE_SOUL_OBSERVER_ID_REPLAY')
    if any(row['observer_key_sha256'] == normalized['observer_key_sha256'] for row in existing):
        raise ValueError('EVIDENCE_SOUL_OBSERVER_KEY_REUSE')
    row = {
        'seq': len(existing) + 1,
        'witness': normalized,
        'previous_witness_sha256': state['witness_head_sha256'],
    }
    row['witness_row_sha256'] = _hash_row(row, 'witness_row_sha256')
    state['witnesses'].append(row)
    state['witness_head_sha256'] = row['witness_row_sha256']
    validate(state)
    store.save(data, NS, COMPONENT, state)
    return {'ok': True, 'version': 'v1022.7', 'witness': copy.deepcopy(normalized),
            'witness_count': len(state['witnesses']), 'claim_boundary': copy.deepcopy(state['claim_boundary'])}


@transactional()
def deliberate(data, bundle):
    require_alive(data)
    integrate(data)
    state = load(data)
    if not isinstance(bundle, dict) or set(bundle) != {'schema', 'context', 'options', 'assessments'}:
        raise ValueError('EVIDENCE_SOUL_BUNDLE_FIELDS')
    if bundle.get('schema') != BUNDLE_SCHEMA:
        raise ValueError('EVIDENCE_SOUL_BUNDLE_SCHEMA')
    context = _text(bundle['context'], 'CONTEXT', 256)
    options = _normal_core_options(bundle['options'])
    assessment_envelopes = bundle['assessments']
    if not isinstance(assessment_envelopes, list) or not MIN_WITNESSES <= len(assessment_envelopes) <= 16:
        raise ValueError('EVIDENCE_SOUL_ASSESSMENT_COUNT')
    records = [_normal_assessment(env, _witnesses(state), options, context)
               for env in assessment_envelopes]
    assessment_ids = [row['assessment_id'] for row in records]
    if len(assessment_ids) != len(set(assessment_ids)):
        raise ValueError('EVIDENCE_SOUL_ASSESSMENT_REPLAY')
    old_ids = {item for row in state['decisions'] for item in row['assessment_ids']}
    if any(item in old_ids for item in assessment_ids):
        raise ValueError('EVIDENCE_SOUL_ASSESSMENT_REPLAY')
    evidence_hashes = [row['envelope']['payload']['evidence_sha256'] for row in records]
    old_evidence = {env['payload']['evidence_sha256']
                    for row in state['decisions'] for env in row['assessment_envelopes']}
    if (len(evidence_hashes) != len(set(evidence_hashes))
            or any(item in old_evidence for item in evidence_hashes)):
        raise ValueError('EVIDENCE_SOUL_ASSESSMENT_EVIDENCE_REPLAY')
    fingerprints = sorted({row['observer_key_sha256'] for row in records})
    domains = sorted({row['trust_domain'] for row in records})
    if len(fingerprints) < MIN_WITNESSES or len(domains) < MIN_TRUST_DOMAINS:
        raise ValueError('EVIDENCE_SOUL_ASSESSMENT_QUORUM')
    effects = _aggregate_assessments(records, [option['id'] for option in options])
    from .soul_experience_learning import prepare
    from . import experience_provenance as provenance
    origin=provenance.snapshot(provenance.preflight(data)) if provenance.needs_preflight(data) else None
    experience = prepare(state, options, context, effects,origin)
    reflective_options = [{**copy.deepcopy(option), 'effects': experience['applied_effects'][option['id']]}
                          for option in options]
    result = reflective.deliberate(data, reflective_options, context, authenticated_only=True)
    row = {
        'seq': len(state['decisions']) + 1,
        'context': context,
        'core_options': options,
        'core_options_sha256': sha_obj(options),
        'assessment_envelopes': copy.deepcopy(assessment_envelopes),
        'assessment_ids': assessment_ids,
        'witness_fingerprints': fingerprints,
        'trust_domains': domains,
        'aggregated_effects': effects,
        'experience_learning': experience,
        'reflective_decision_sha256': result['decision_sha256'],
        'chosen': result['chosen'],
        'best_candidate': result['best_candidate'],
        'review_required': result['review_required'],
        'previous_decision_sha256': state['decision_head_sha256'],
    }
    row['decision_sha256'] = _hash_row(row, 'decision_sha256')
    state['decisions'].append(row)
    state['decision_head_sha256'] = row['decision_sha256']
    validate(state)
    store.save(data, NS, COMPONENT, state)
    if origin is not None:provenance.record_decision(data,row)
    return {
        'ok': True, 'version': 'v1022.7', 'chosen': row['chosen'],
        'best_candidate': row['best_candidate'], 'review_required': row['review_required'],
        'decision_sha256': row['decision_sha256'],
        'reflective_decision_sha256': row['reflective_decision_sha256'],
        'verified_assessments': len(records), 'distinct_witness_keys': len(fingerprints),
        'distinct_configured_trust_domains': len(domains),
        'aggregated_effects': copy.deepcopy(effects),
        'experience_learning': copy.deepcopy(experience),
        'profile_used': copy.deepcopy(result['profile_used']),
        'profile_policy': result['profile_policy'],
        'claim_boundary': copy.deepcopy(state['claim_boundary']),
    }


@transactional()
def attest(data, envelope):
    require_alive(data)
    integrate(data)
    state = load(data)
    payload, witness = _normal_attestation(envelope, _witnesses(state))
    decision = next((row for row in state['decisions']
                     if row['decision_sha256'] == payload['decision_sha256']), None)
    if decision is None or decision['chosen'] is None:
        raise ValueError('EVIDENCE_SOUL_UNKNOWN_OR_UNACTED_DECISION')
    if payload['chosen'] != decision['chosen']:
        raise ValueError('EVIDENCE_SOUL_WRONG_CHOSEN_BINDING')
    existing_payloads = [row['envelope']['payload'] for row in state['attestations']]
    if payload['attestation_id'] in {row['attestation_id'] for row in existing_payloads}:
        raise ValueError('EVIDENCE_SOUL_ATTESTATION_REPLAY')
    if payload['evidence_sha256'] in {row['evidence_sha256'] for row in existing_payloads}:
        raise ValueError('EVIDENCE_SOUL_EVIDENCE_REPLAY')
    legacy = reflective.reflect(data, decision['reflective_decision_sha256'], {
        'evidence_id': 'attested:' + payload['attestation_id'],
        'observer_id': witness['observer_key_sha256'],
        'source_kind': payload['source_kind'],
        'self_wellbeing': payload['self_wellbeing'],
        'others_wellbeing': payload['others_wellbeing'],
        'future_self': payload['future_self'],
        'truth_consistency': payload['truth_consistency'],
        'bodily_cost': payload['bodily_cost'],
        'surprise': payload['surprise'],
        'confidence': payload['confidence'],
        'note': payload['note'],
    })
    row = {
        'seq': len(state['attestations']) + 1,
        'envelope': copy.deepcopy(envelope),
        'envelope_sha256': sha_obj(envelope),
        'observer_key_sha256': witness['observer_key_sha256'],
        'authority_id': witness['authority_id'],
        'trust_domain': witness['trust_domain'],
        'derived_status': '',
        'legacy_reflection_sha256': legacy['reflection_sha256'],
        'previous_attestation_sha256': state['attestation_head_sha256'],
    }
    provisional_rows = [*state['attestations'], row]
    row['derived_status'] = _status_for(payload['decision_sha256'], provisional_rows)
    row['attestation_sha256'] = _hash_row(row, 'attestation_sha256')
    state['attestations'].append(row)
    state['attestation_head_sha256'] = row['attestation_sha256']
    validate(state)
    store.save(data, NS, COMPONENT, state)
    return {
        'ok': True, 'version': 'v1022.7',
        'attestation_sha256': row['attestation_sha256'],
        'status': row['derived_status'],
        'authorship_verified': True,
        'truth_verified': False,
        'configured_domain_independence_only': True,
        'claim_boundary': copy.deepcopy(state['claim_boundary']),
    }


def observation_status_for(decision_sha256, rows):
    """v1022.7.9: the same count as _status_for, of the witnesses who saw or were told by someone who saw - an
    attestation of what the individual says of itself (self_report) is authored, never observed. The stored status
    keeps its old meaning (authorship of the attestations); this one says whether anything outside was observed."""
    outside = [row for row in rows if row['envelope']['payload']['source_kind'] in ('direct_observation', 'external_report')]
    status = _status_for(decision_sha256, outside)
    if status == 'AUTHENTICATED_LOW_CONFIDENCE' and any(
            row['envelope']['payload']['decision_sha256'] == decision_sha256 for row in rows if row not in outside):
        return 'SELF_REPORTED_ONLY'
    return status.replace('ATTESTED', 'OBSERVED')


def _public(state):
    statuses = {}
    observed = {}
    for decision in state['decisions']:
        statuses[decision['decision_sha256']] = _status_for(
            decision['decision_sha256'], state['attestations'])
        observed[decision['decision_sha256']] = observation_status_for(
            decision['decision_sha256'], state['attestations'])
    return {
        'ok': True, 'version': 'v1022.7',
        'individual_id': state['individual_id'],
        'integration_seq': state['integration_seq'],
        'authority_count': len(state['authorities']),
        'witness_count': len(state['witnesses']),
        'decision_count': len(state['decisions']),
        'attestation_count': len(state['attestations']),
        'decision_statuses': statuses,
        'decision_observation_statuses': observed,
        'experience_learning_decisions': sum('experience_learning' in d for d in state['decisions']),
        'last_experience_learning': copy.deepcopy(state['decisions'][-1].get('experience_learning')) if state['decisions'] else None,
        'authority_head_sha256': state['authority_head_sha256'],
        'witness_head_sha256': state['witness_head_sha256'],
        'decision_head_sha256': state['decision_head_sha256'],
        'attestation_head_sha256': state['attestation_head_sha256'],
        'claim_boundary': copy.deepcopy(state['claim_boundary']),
    }


def status(data):
    state = load(data)
    result = _public(state)
    from . import experience_provenance as provenance
    result['experience_provenance']=provenance.status(data) if provenance.needs_preflight(data) else {
        'mode':'LEGACY_UNCLASSIFIED','physical_truth_verified':False,'strict_origin_learning_enabled':False}
    result['audit'] = audit(data)
    return result


def audit(data):
    try:
        state = load(data)
        ident = _live_identity(data)
        errors = []
        if any(state.get(key) != ident[key] for key in ('individual_id', 'lineage_id', 'branch_id')):
            errors.append('EVIDENCE_SOUL_IDENTITY')
        reflective_state = reflective.load(data)
        reflective_decisions = {row['decision_sha256']: row for row in reflective_state['decisions']}
        reflective_reflections = {row['reflection_sha256']: row for row in reflective_state['reflections']}
        for row in state['decisions']:
            linked = reflective_decisions.get(row['reflective_decision_sha256'])
            if linked is None or linked['chosen'] != row['chosen']:
                errors.append('EVIDENCE_SOUL_REFLECTIVE_DECISION_BINDING')
            elif 'experience_learning' in row:
                expected_options = [{**copy.deepcopy(o), 'effects': row['experience_learning']['applied_effects'][o['id']]}
                                    for o in row['core_options']]
                if (linked['options'] != expected_options or linked['context'] != row['context']
                        or linked.get('profile_policy') != row['experience_learning']['profile_policy']):
                    errors.append('EVIDENCE_SOUL_EXPERIENCE_DECISION_BINDING')
        for row in state['attestations']:
            linked = reflective_reflections.get(row['legacy_reflection_sha256'])
            if linked is None:
                errors.append('EVIDENCE_SOUL_REFLECTION_BINDING')
        return {
            'ok': not errors,
            'version': 'v1022.7',
            'errors': errors,
            'authority_count': len(state['authorities']),
            'witness_count': len(state['witnesses']),
            'decision_count': len(state['decisions']),
            'attestation_count': len(state['attestations']),
            'signature_chains_valid': not errors,
            'median_aggregation_replay_valid': not errors,
            'external_truth_verified': False,
            'real_world_domain_independence_verified': False,
            'literal_soul_established': False,
            'consciousness_established': False,
        }
    except (ValueError, TypeError, KeyError, OSError) as exc:
        return {
            'ok': False,
            'version': 'v1022.7',
            'errors': [type(exc).__name__ + ':' + str(exc)],
            'external_truth_verified': False,
            'real_world_domain_independence_verified': False,
            'literal_soul_established': False,
            'consciousness_established': False,
        }
