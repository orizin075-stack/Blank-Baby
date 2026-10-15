"""Bounded semantic-truth challenges for V1022.7.1.

Authenticated agreement is not truth.  This layer records a typed claim and a
three-domain signed report consensus first, then permits a separate configured
oracle to challenge it against a benchmark manifest whose hash was committed
before the first report.  A successful result proves consistency with that
finite manifest.  It does not prove that the manifest describes external
reality, that the configured actors are socially independent, or that a
literal soul / consciousness exists.
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
from . import evidence_bound_soul as evidence
from . import store


NS = 'semantic_truth'
COMPONENT = 'whole_semantic_truth'
SCHEMA = 'tukuyo.v1022_7_1.semantic_truth/1'
ORACLE_SCHEMA = 'tukuyo.v1022_7_1.truth_oracle/1'
CLAIM_SCHEMA = 'tukuyo.v1022_7_1.typed_claim/1'
REPORT_SCHEMA = 'tukuyo.v1022_7_1.signed_report/1'
REPORT_BUNDLE_SCHEMA = 'tukuyo.v1022_7_1.report_bundle/1'
MANIFEST_SCHEMA = 'tukuyo.v1022_7_1.benchmark_manifest/1'
RECEIPT_SCHEMA = 'tukuyo.v1022_7_1.oracle_receipt/1'
CHALLENGE_BUNDLE_SCHEMA = 'tukuyo.v1022_7_1.challenge_bundle/1'
ZERO = '0' * 64
MIN_REPORTS = 3
MIN_DOMAINS = 3
VALUE_TYPES = ('number', 'string', 'boolean')
COMPARATORS = ('equal', 'within_tolerance')
UNITS = ('none', 'count', 'm', 'km', 's', 'min', 'h', 'g', 'kg', 'ml', 'l', 'j')


def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _text(value, label, limit=160):
    if (not isinstance(value, str) or not value or len(value) > limit
            or re.search(r'[\x00-\x1f]', value)):
        raise ValueError('SEMANTIC_TRUTH_' + label)
    return value


def _sha256(value, label='SHA256'):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value) or value == ZERO:
        raise ValueError('SEMANTIC_TRUTH_' + label)
    return value


def _public_key(value, label='PUBLIC_KEY'):
    try:
        raw = base64.b64decode(value, validate=True)
        if len(raw) != 32:
            raise ValueError
        Ed25519PublicKey.from_public_bytes(raw)
    except Exception as exc:
        raise ValueError('SEMANTIC_TRUTH_' + label) from exc
    return value, hashlib.sha256(raw).hexdigest()


def _verify_envelope(envelope, expected_public_key, schema):
    if not isinstance(envelope, dict) or set(envelope) != {'payload', 'public_key', 'signature'}:
        raise ValueError('SEMANTIC_TRUTH_ENVELOPE_FIELDS')
    if envelope.get('public_key') != expected_public_key:
        raise ValueError('SEMANTIC_TRUTH_SIGNER_MISMATCH')
    payload = envelope.get('payload')
    if not isinstance(payload, dict) or payload.get('schema') != schema:
        raise ValueError('SEMANTIC_TRUTH_ENVELOPE_SCHEMA')
    try:
        key = base64.b64decode(expected_public_key, validate=True)
        signature = base64.b64decode(envelope.get('signature', ''), validate=True)
        Ed25519PublicKey.from_public_bytes(key).verify(signature, whole.canon(payload))
    except Exception as exc:
        raise ValueError('SEMANTIC_TRUTH_SIGNATURE') from exc
    return payload


def _hash_row(row, field):
    value = copy.deepcopy(row)
    value.pop(field, None)
    return sha_obj(value)


def _scalar(value, value_type, label='VALUE'):
    if value_type == 'number':
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError('SEMANTIC_TRUTH_' + label)
        value = round(float(value), 9)
        return int(value) if value.is_integer() else value
    if value_type == 'string':
        return _text(value, label, 256)
    if value_type == 'boolean':
        if type(value) is not bool:
            raise ValueError('SEMANTIC_TRUTH_' + label)
        return value
    raise ValueError('SEMANTIC_TRUTH_VALUE_TYPE')


def _normal_claim(claim):
    required = {'schema', 'claim_id', 'scope_id', 'subject', 'predicate',
                'context_sha256', 'value_type', 'unit', 'comparator',
                'tolerance', 'asserted_value'}
    if not isinstance(claim, dict) or set(claim) != required or claim.get('schema') != CLAIM_SCHEMA:
        raise ValueError('SEMANTIC_TRUTH_CLAIM_FIELDS')
    value_type = claim['value_type']
    if value_type not in VALUE_TYPES:
        raise ValueError('SEMANTIC_TRUTH_VALUE_TYPE')
    unit = claim['unit']
    if unit not in UNITS or (value_type != 'number' and unit != 'none'):
        raise ValueError('SEMANTIC_TRUTH_UNIT')
    comparator = claim['comparator']
    if comparator not in COMPARATORS:
        raise ValueError('SEMANTIC_TRUTH_COMPARATOR')
    tolerance = _scalar(claim['tolerance'], 'number', 'TOLERANCE')
    if tolerance < 0 or (comparator == 'equal' and tolerance != 0):
        raise ValueError('SEMANTIC_TRUTH_TOLERANCE')
    if comparator == 'within_tolerance' and value_type != 'number':
        raise ValueError('SEMANTIC_TRUTH_TOLERANCE_TYPE')
    normalized = {
        'schema': CLAIM_SCHEMA,
        'claim_id': _text(claim['claim_id'], 'CLAIM_ID', 96),
        'scope_id': _text(claim['scope_id'], 'SCOPE_ID', 96),
        'subject': _text(claim['subject'], 'SUBJECT', 160),
        'predicate': _text(claim['predicate'], 'PREDICATE', 160),
        'context_sha256': _sha256(claim['context_sha256'], 'CONTEXT_SHA256'),
        'value_type': value_type,
        'unit': unit,
        'comparator': comparator,
        'tolerance': tolerance,
        'asserted_value': _scalar(claim['asserted_value'], value_type, 'ASSERTED_VALUE'),
    }
    if normalized != claim:
        raise ValueError('SEMANTIC_TRUTH_CLAIM_CANONICAL')
    return normalized


def _matches(claim, value):
    value = _scalar(value, claim['value_type'], 'COMPARED_VALUE')
    if claim['comparator'] == 'equal':
        return value == claim['asserted_value']
    return abs(float(value) - float(claim['asserted_value'])) <= float(claim['tolerance'])


def _consensus_value(values, value_type):
    if value_type == 'number':
        return _scalar(statistics.median([float(value) for value in values]), 'number')
    counts = {}
    for value in values:
        key = json.dumps(value, ensure_ascii=False, sort_keys=True)
        counts[key] = counts.get(key, 0) + 1
    winner, count = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0]
    if count <= len(values) // 2:
        return None
    return json.loads(winner)


def _normal_oracle(oracle):
    required = {'schema', 'oracle_id', 'scope_id', 'public_key', 'adapter_sha256',
                'method_sha256', 'benchmark_manifest_sha256'}
    if not isinstance(oracle, dict) or set(oracle) != required or oracle.get('schema') != ORACLE_SCHEMA:
        raise ValueError('SEMANTIC_TRUTH_ORACLE_FIELDS')
    public_key, fingerprint = _public_key(oracle['public_key'], 'ORACLE_PUBLIC_KEY')
    return {
        'schema': ORACLE_SCHEMA,
        'oracle_id': _text(oracle['oracle_id'], 'ORACLE_ID', 96),
        'scope_id': _text(oracle['scope_id'], 'SCOPE_ID', 96),
        'public_key': public_key,
        'public_key_sha256': fingerprint,
        'adapter_sha256': _sha256(oracle['adapter_sha256'], 'ADAPTER_SHA256'),
        'method_sha256': _sha256(oracle['method_sha256'], 'METHOD_SHA256'),
        'benchmark_manifest_sha256': _sha256(
            oracle['benchmark_manifest_sha256'], 'MANIFEST_SHA256'),
        'configured_oracle_not_external_truth_proof': True,
    }


def _oracle_input(row):
    return {key: row[key] for key in ('schema', 'oracle_id', 'scope_id', 'public_key',
                                      'adapter_sha256', 'method_sha256',
                                      'benchmark_manifest_sha256')}


def _oracles(state):
    return {row['oracle']['oracle_id']: row['oracle'] for row in state['oracles']}


def _evidence_witnesses():
    return None


def _normal_report(envelope, witness_map, claim, nonce):
    observer_id = (envelope.get('payload') or {}).get('observer_id') if isinstance(envelope, dict) else None
    witness = witness_map.get(observer_id)
    if witness is None:
        raise ValueError('SEMANTIC_TRUTH_UNKNOWN_WITNESS')
    payload = _verify_envelope(envelope, witness['observer_public_key'], REPORT_SCHEMA)
    required = {'schema', 'report_id', 'observer_id', 'claim_sha256',
                'challenge_nonce', 'observed_value', 'value_type', 'unit',
                'evidence_sha256', 'method_sha256'}
    if set(payload) != required:
        raise ValueError('SEMANTIC_TRUTH_REPORT_FIELDS')
    if (payload['observer_id'] != observer_id or payload['claim_sha256'] != sha_obj(claim)
            or payload['challenge_nonce'] != nonce):
        raise ValueError('SEMANTIC_TRUTH_REPORT_BINDING')
    if payload['value_type'] != claim['value_type'] or payload['unit'] != claim['unit']:
        raise ValueError('SEMANTIC_TRUTH_REPORT_UNIT_OR_TYPE')
    normalized = copy.deepcopy(payload)
    normalized['report_id'] = _text(payload['report_id'], 'REPORT_ID', 96)
    normalized['challenge_nonce'] = _text(payload['challenge_nonce'], 'NONCE', 128)
    normalized['observed_value'] = _scalar(payload['observed_value'], claim['value_type'], 'OBSERVED_VALUE')
    _sha256(payload['evidence_sha256'], 'EVIDENCE_SHA256')
    _sha256(payload['method_sha256'], 'METHOD_SHA256')
    if normalized != payload:
        raise ValueError('SEMANTIC_TRUTH_REPORT_CANONICAL')
    return {
        'envelope': copy.deepcopy(envelope),
        'report_id': normalized['report_id'],
        'observed_value': normalized['observed_value'],
        'observer_key_sha256': witness['observer_key_sha256'],
        'authority_id': witness['authority_id'],
        'trust_domain': witness['trust_domain'],
    }


def _normal_manifest(manifest):
    required = {'schema', 'benchmark_id', 'scope_id', 'entries'}
    if not isinstance(manifest, dict) or set(manifest) != required or manifest.get('schema') != MANIFEST_SCHEMA:
        raise ValueError('SEMANTIC_TRUTH_MANIFEST_FIELDS')
    entries = manifest['entries']
    if not isinstance(entries, list) or not 1 <= len(entries) <= 10000:
        raise ValueError('SEMANTIC_TRUTH_MANIFEST_ENTRIES')
    normalized_entries = []
    seen = set()
    for entry in entries:
        required_entry = {'subject', 'predicate', 'context_sha256', 'value_type', 'unit', 'expected_value'}
        if not isinstance(entry, dict) or set(entry) != required_entry:
            raise ValueError('SEMANTIC_TRUTH_MANIFEST_ENTRY_FIELDS')
        value_type = entry['value_type']
        if value_type not in VALUE_TYPES or entry['unit'] not in UNITS:
            raise ValueError('SEMANTIC_TRUTH_MANIFEST_ENTRY_TYPE')
        if value_type != 'number' and entry['unit'] != 'none':
            raise ValueError('SEMANTIC_TRUTH_MANIFEST_ENTRY_UNIT')
        normalized = {
            'subject': _text(entry['subject'], 'SUBJECT', 160),
            'predicate': _text(entry['predicate'], 'PREDICATE', 160),
            'context_sha256': _sha256(entry['context_sha256'], 'CONTEXT_SHA256'),
            'value_type': value_type,
            'unit': entry['unit'],
            'expected_value': _scalar(entry['expected_value'], value_type, 'EXPECTED_VALUE'),
        }
        key = (normalized['subject'], normalized['predicate'], normalized['context_sha256'])
        if key in seen:
            raise ValueError('SEMANTIC_TRUTH_MANIFEST_ENTRY_DUPLICATE')
        seen.add(key)
        normalized_entries.append(normalized)
    normalized_manifest = {
        'schema': MANIFEST_SCHEMA,
        'benchmark_id': _text(manifest['benchmark_id'], 'BENCHMARK_ID', 96),
        'scope_id': _text(manifest['scope_id'], 'SCOPE_ID', 96),
        'entries': normalized_entries,
    }
    if normalized_manifest != manifest:
        raise ValueError('SEMANTIC_TRUTH_MANIFEST_CANONICAL')
    return normalized_manifest


def _manifest_entry(manifest, claim):
    matches = [entry for entry in manifest['entries']
               if entry['subject'] == claim['subject']
               and entry['predicate'] == claim['predicate']
               and entry['context_sha256'] == claim['context_sha256']]
    if len(matches) != 1:
        raise ValueError('SEMANTIC_TRUTH_MANIFEST_COVERAGE')
    entry = matches[0]
    if entry['value_type'] != claim['value_type'] or entry['unit'] != claim['unit']:
        raise ValueError('SEMANTIC_TRUTH_MANIFEST_UNIT_OR_TYPE')
    return entry


def _normal_receipt(envelope, oracle, report_row, manifest, entry):
    payload = _verify_envelope(envelope, oracle['public_key'], RECEIPT_SCHEMA)
    required = {'schema', 'receipt_id', 'oracle_id', 'report_sha256', 'claim_sha256',
                'challenge_nonce', 'benchmark_manifest_sha256', 'entry_sha256',
                'expected_value', 'value_type', 'unit'}
    if set(payload) != required:
        raise ValueError('SEMANTIC_TRUTH_RECEIPT_FIELDS')
    claim = report_row['claim']
    if (payload['oracle_id'] != oracle['oracle_id']
            or payload['report_sha256'] != report_row['report_sha256']
            or payload['claim_sha256'] != report_row['claim_sha256']
            or payload['challenge_nonce'] != report_row['challenge_nonce']
            or payload['benchmark_manifest_sha256'] != sha_obj(manifest)
            or payload['entry_sha256'] != sha_obj(entry)
            or payload['value_type'] != claim['value_type']
            or payload['unit'] != claim['unit']):
        raise ValueError('SEMANTIC_TRUTH_RECEIPT_BINDING')
    normalized = copy.deepcopy(payload)
    normalized['receipt_id'] = _text(payload['receipt_id'], 'RECEIPT_ID', 96)
    normalized['expected_value'] = _scalar(payload['expected_value'], claim['value_type'], 'EXPECTED_VALUE')
    if normalized['expected_value'] != entry['expected_value']:
        raise ValueError('SEMANTIC_TRUTH_RECEIPT_MANIFEST_MISMATCH')
    if normalized != payload:
        raise ValueError('SEMANTIC_TRUTH_RECEIPT_CANONICAL')
    return normalized


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
                'oracles', 'oracle_head_sha256', 'reports', 'report_head_sha256',
                'challenges', 'challenge_head_sha256', 'claim_boundary'}
    if not isinstance(state, dict) or set(state) != required or state.get('schema') != SCHEMA:
        raise ValueError('SEMANTIC_TRUTH_SCHEMA')
    for key in ('individual_id', 'lineage_id', 'branch_id'):
        _text(state[key], key.upper(), 160)
    if type(state['integration_seq']) is not int or state['integration_seq'] < 1:
        raise ValueError('SEMANTIC_TRUTH_SEQ')

    previous = ZERO
    oracle_ids, scopes, keys, manifests = set(), set(), set(), set()
    for seq, row in enumerate(state['oracles'], 1):
        if set(row) != {'seq', 'oracle', 'previous_oracle_sha256', 'oracle_row_sha256'}:
            raise ValueError('SEMANTIC_TRUTH_ORACLE_ROW')
        oracle = _normal_oracle(_oracle_input(row['oracle']))
        if oracle != row['oracle'] or row['seq'] != seq or row['previous_oracle_sha256'] != previous:
            raise ValueError('SEMANTIC_TRUTH_ORACLE_CHAIN')
        if (oracle['oracle_id'] in oracle_ids or oracle['scope_id'] in scopes
                or oracle['public_key_sha256'] in keys
                or oracle['benchmark_manifest_sha256'] in manifests):
            raise ValueError('SEMANTIC_TRUTH_ORACLE_DUPLICATE')
        oracle_ids.add(oracle['oracle_id']); scopes.add(oracle['scope_id'])
        keys.add(oracle['public_key_sha256']); manifests.add(oracle['benchmark_manifest_sha256'])
        if row['oracle_row_sha256'] != _hash_row(row, 'oracle_row_sha256'):
            raise ValueError('SEMANTIC_TRUTH_ORACLE_HASH')
        previous = row['oracle_row_sha256']
    if state['oracle_head_sha256'] != previous:
        raise ValueError('SEMANTIC_TRUTH_ORACLE_HEAD')

    previous = ZERO
    report_ids, claim_ids, nonces, evidence_hashes = set(), set(), set(), set()
    for seq, row in enumerate(state['reports'], 1):
        required_row = {'seq', 'claim', 'claim_sha256', 'challenge_nonce',
                        'report_envelopes', 'report_ids', 'witness_fingerprints',
                        'trust_domains', 'consensus_value', 'report_consensus',
                        'previous_report_sha256', 'report_sha256'}
        if set(row) != required_row or row['seq'] != seq or row['previous_report_sha256'] != previous:
            raise ValueError('SEMANTIC_TRUTH_REPORT_ROW')
        claim = _normal_claim(row['claim'])
        if claim != row['claim'] or row['claim_sha256'] != sha_obj(claim):
            raise ValueError('SEMANTIC_TRUTH_CLAIM_BINDING')
        if claim['claim_id'] in claim_ids or row['challenge_nonce'] in nonces:
            raise ValueError('SEMANTIC_TRUTH_REPORT_REPLAY')
        claim_ids.add(claim['claim_id']); nonces.add(row['challenge_nonce'])
        _text(row['challenge_nonce'], 'NONCE', 128)
        # Signature-level report validation is performed in audit because it
        # depends on the live evidence-bound witness registry.
        envelopes = row['report_envelopes']
        if not isinstance(envelopes, list) or len(envelopes) < MIN_REPORTS:
            raise ValueError('SEMANTIC_TRUTH_REPORT_COUNT')
        ids = [env.get('payload', {}).get('report_id') for env in envelopes]
        evidences = [env.get('payload', {}).get('evidence_sha256') for env in envelopes]
        if len(ids) != len(set(ids)) or any(item in report_ids for item in ids):
            raise ValueError('SEMANTIC_TRUTH_REPORT_ID_REPLAY')
        if len(evidences) != len(set(evidences)) or any(item in evidence_hashes for item in evidences):
            raise ValueError('SEMANTIC_TRUTH_REPORT_EVIDENCE_REPLAY')
        report_ids.update(ids); evidence_hashes.update(evidences)
        if len(row['witness_fingerprints']) < MIN_REPORTS or len(row['trust_domains']) < MIN_DOMAINS:
            raise ValueError('SEMANTIC_TRUTH_REPORT_QUORUM')
        if row['report_consensus'] not in ('CLAIM_SUPPORTED', 'CLAIM_REFUTED', 'DISAGREEMENT'):
            raise ValueError('SEMANTIC_TRUTH_REPORT_STATUS')
        if row['report_consensus'] == 'DISAGREEMENT' and row['consensus_value'] is not None:
            raise ValueError('SEMANTIC_TRUTH_CONSENSUS_VALUE')
        if row['report_consensus'] != 'DISAGREEMENT':
            _scalar(row['consensus_value'], claim['value_type'], 'CONSENSUS_VALUE')
        if row['report_sha256'] != _hash_row(row, 'report_sha256'):
            raise ValueError('SEMANTIC_TRUTH_REPORT_HASH')
        previous = row['report_sha256']
    if state['report_head_sha256'] != previous:
        raise ValueError('SEMANTIC_TRUTH_REPORT_HEAD')

    previous = ZERO
    challenged, receipt_ids = set(), set()
    report_map = {row['report_sha256']: row for row in state['reports']}
    for seq, row in enumerate(state['challenges'], 1):
        required_row = {'seq', 'report_sha256', 'claim_sha256', 'oracle_id',
                        'scope_id', 'oracle_key_sha256', 'benchmark_manifest',
                        'benchmark_manifest_sha256', 'entry_sha256', 'expected_value',
                        'receipt_envelope', 'receipt_id', 'report_consensus',
                        'benchmark_match', 'reports_conflict_with_benchmark',
                        'status', 'previous_challenge_sha256', 'challenge_sha256'}
        if set(row) != required_row or row['seq'] != seq or row['previous_challenge_sha256'] != previous:
            raise ValueError('SEMANTIC_TRUTH_CHALLENGE_ROW')
        report = report_map.get(row['report_sha256'])
        if report is None or row['report_sha256'] in challenged:
            raise ValueError('SEMANTIC_TRUTH_CHALLENGE_REPLAY')
        challenged.add(row['report_sha256'])
        if row['claim_sha256'] != report['claim_sha256'] or row['report_consensus'] != report['report_consensus']:
            raise ValueError('SEMANTIC_TRUTH_CHALLENGE_REPORT_BINDING')
        oracle = _oracles(state).get(row['oracle_id'])
        if oracle is None or row['scope_id'] != oracle['scope_id'] or row['oracle_key_sha256'] != oracle['public_key_sha256']:
            raise ValueError('SEMANTIC_TRUTH_CHALLENGE_ORACLE')
        manifest = _normal_manifest(row['benchmark_manifest'])
        if (manifest['scope_id'] != oracle['scope_id']
                or row['benchmark_manifest_sha256'] != sha_obj(manifest)
                or row['benchmark_manifest_sha256'] != oracle['benchmark_manifest_sha256']):
            raise ValueError('SEMANTIC_TRUTH_CHALLENGE_MANIFEST')
        entry = _manifest_entry(manifest, report['claim'])
        if row['entry_sha256'] != sha_obj(entry) or row['expected_value'] != entry['expected_value']:
            raise ValueError('SEMANTIC_TRUTH_CHALLENGE_ENTRY')
        receipt = _normal_receipt(row['receipt_envelope'], oracle, report, manifest, entry)
        if row['receipt_id'] != receipt['receipt_id'] or row['receipt_id'] in receipt_ids:
            raise ValueError('SEMANTIC_TRUTH_RECEIPT_REPLAY')
        receipt_ids.add(row['receipt_id'])
        match = _matches(report['claim'], entry['expected_value'])
        conflict = ((report['report_consensus'] == 'CLAIM_SUPPORTED') != match
                    if report['report_consensus'] != 'DISAGREEMENT' else True)
        status = 'BOUNDED_BENCHMARK_VERIFIED' if match else 'BOUNDED_BENCHMARK_REFUTED'
        if (row['benchmark_match'] is not match
                or row['reports_conflict_with_benchmark'] is not conflict
                or row['status'] != status):
            raise ValueError('SEMANTIC_TRUTH_DERIVATION')
        if row['challenge_sha256'] != _hash_row(row, 'challenge_sha256'):
            raise ValueError('SEMANTIC_TRUTH_CHALLENGE_HASH')
        previous = row['challenge_sha256']
    if state['challenge_head_sha256'] != previous:
        raise ValueError('SEMANTIC_TRUTH_CHALLENGE_HEAD')

    boundary = state['claim_boundary']
    if (not isinstance(boundary, dict)
            or boundary.get('report_consensus_establishes_truth') is not False
            or boundary.get('bounded_benchmark_proves_external_reality') is not False
            or boundary.get('literal_soul_established') is not False
            or boundary.get('consciousness_established') is not False):
        raise ValueError('SEMANTIC_TRUTH_CLAIM_BOUNDARY')


def load(data):
    if not (Path(data) / NS / 'commits').exists():
        if needs_preflight(data):
            raise ValueError('SEMANTIC_TRUTH_HISTORY_MISSING')
        raise ValueError('SEMANTIC_TRUTH_NOT_INITIALIZED')
    return store.load(data, NS, COMPONENT, validate)


@transactional()
def integrate(data):
    require_alive(data)
    evidence.integrate(data)
    ident = _live_identity(data)
    try:
        old = load(data)
    except ValueError as exc:
        if str(exc) != 'SEMANTIC_TRUTH_NOT_INITIALIZED':
            raise
        old = None
    state = {
        'schema': SCHEMA,
        'individual_id': ident['individual_id'],
        'lineage_id': ident['lineage_id'],
        'branch_id': ident['branch_id'],
        'integration_seq': int(old.get('integration_seq', 0)) + 1 if old else 1,
        'oracles': copy.deepcopy(old.get('oracles', [])) if old else [],
        'oracle_head_sha256': old.get('oracle_head_sha256', ZERO) if old else ZERO,
        'reports': copy.deepcopy(old.get('reports', [])) if old else [],
        'report_head_sha256': old.get('report_head_sha256', ZERO) if old else ZERO,
        'challenges': copy.deepcopy(old.get('challenges', [])) if old else [],
        'challenge_head_sha256': old.get('challenge_head_sha256', ZERO) if old else ZERO,
        'claim_boundary': {
            'typed_claims_required': True,
            'exact_unit_and_value_type_binding': True,
            'minimum_distinct_report_keys': MIN_REPORTS,
            'minimum_configured_report_domains': MIN_DOMAINS,
            'report_consensus_establishes_truth': False,
            'oracle_manifest_precommitted_before_first_report': True,
            'oracle_role_key_separated_from_report_roles': True,
            'oracle_receipt_replayed_against_manifest': True,
            'bounded_benchmark_match_can_be_verified': True,
            'bounded_benchmark_proves_external_reality': False,
            'configured_domains_prove_social_independence': False,
            'literal_soul_established': False,
            'consciousness_established': False,
            'personhood_established': False,
        },
    }
    validate(state)
    store.save(data, NS, COMPONENT, state)
    return _public(state)


@transactional()
def add_oracle(data, oracle):
    require_alive(data)
    integrate(data)
    state = load(data)
    if state['reports']:
        raise ValueError('SEMANTIC_TRUTH_ORACLE_REGISTRY_SEALED')
    normalized = _normal_oracle(oracle)
    existing = [row['oracle'] for row in state['oracles']]
    if any(row['oracle_id'] == normalized['oracle_id'] for row in existing):
        raise ValueError('SEMANTIC_TRUTH_ORACLE_ID_REPLAY')
    if any(row['scope_id'] == normalized['scope_id'] for row in existing):
        raise ValueError('SEMANTIC_TRUTH_SCOPE_REPLAY')
    if any(row['public_key_sha256'] == normalized['public_key_sha256'] for row in existing):
        raise ValueError('SEMANTIC_TRUTH_ORACLE_KEY_REUSE')
    evidence_state = evidence.load(data)
    forbidden_keys = {row['authority']['public_key_sha256'] for row in evidence_state['authorities']}
    forbidden_keys.update(row['witness']['observer_key_sha256'] for row in evidence_state['witnesses'])
    if normalized['public_key_sha256'] in forbidden_keys:
        raise ValueError('SEMANTIC_TRUTH_CROSS_ROLE_KEY_REUSE')
    row = {'seq': len(existing) + 1, 'oracle': normalized,
           'previous_oracle_sha256': state['oracle_head_sha256']}
    row['oracle_row_sha256'] = _hash_row(row, 'oracle_row_sha256')
    state['oracles'].append(row); state['oracle_head_sha256'] = row['oracle_row_sha256']
    validate(state); store.save(data, NS, COMPONENT, state)
    return {'ok': True, 'version': 'v1022.7.1', 'oracle': copy.deepcopy(normalized),
            'oracle_count': len(state['oracles']), 'claim_boundary': copy.deepcopy(state['claim_boundary'])}


@transactional()
def submit_reports(data, bundle):
    require_alive(data)
    integrate(data)
    state = load(data)
    if not isinstance(bundle, dict) or set(bundle) != {'schema', 'challenge_nonce', 'claim', 'reports'}:
        raise ValueError('SEMANTIC_TRUTH_REPORT_BUNDLE_FIELDS')
    if bundle.get('schema') != REPORT_BUNDLE_SCHEMA:
        raise ValueError('SEMANTIC_TRUTH_REPORT_BUNDLE_SCHEMA')
    claim = _normal_claim(bundle['claim'])
    nonce = _text(bundle['challenge_nonce'], 'NONCE', 128)
    if claim['scope_id'] not in {row['oracle']['scope_id'] for row in state['oracles']}:
        raise ValueError('SEMANTIC_TRUTH_UNKNOWN_SCOPE')
    if claim['claim_id'] in {row['claim']['claim_id'] for row in state['reports']}:
        raise ValueError('SEMANTIC_TRUTH_CLAIM_REPLAY')
    if nonce in {row['challenge_nonce'] for row in state['reports']}:
        raise ValueError('SEMANTIC_TRUTH_NONCE_REPLAY')
    envelopes = bundle['reports']
    if not isinstance(envelopes, list) or not MIN_REPORTS <= len(envelopes) <= 16:
        raise ValueError('SEMANTIC_TRUTH_REPORT_COUNT')
    evidence_state = evidence.load(data)
    witness_map = evidence._witnesses(evidence_state)
    records = [_normal_report(envelope, witness_map, claim, nonce) for envelope in envelopes]
    ids = [record['report_id'] for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError('SEMANTIC_TRUTH_REPORT_ID_REPLAY')
    old_ids = {item for row in state['reports'] for item in row['report_ids']}
    if any(item in old_ids for item in ids):
        raise ValueError('SEMANTIC_TRUTH_REPORT_ID_REPLAY')
    evidence_hashes = [record['envelope']['payload']['evidence_sha256'] for record in records]
    old_evidence = {env['payload']['evidence_sha256'] for row in state['reports']
                    for env in row['report_envelopes']}
    if len(evidence_hashes) != len(set(evidence_hashes)) or any(value in old_evidence for value in evidence_hashes):
        raise ValueError('SEMANTIC_TRUTH_REPORT_EVIDENCE_REPLAY')
    fingerprints = sorted({record['observer_key_sha256'] for record in records})
    domains = sorted({record['trust_domain'] for record in records})
    if len(fingerprints) < MIN_REPORTS or len(domains) < MIN_DOMAINS:
        raise ValueError('SEMANTIC_TRUTH_REPORT_QUORUM')
    values = [record['observed_value'] for record in records]
    consensus_value = _consensus_value(values, claim['value_type'])
    if consensus_value is None:
        report_consensus = 'DISAGREEMENT'
    else:
        report_consensus = 'CLAIM_SUPPORTED' if _matches(claim, consensus_value) else 'CLAIM_REFUTED'
    row = {
        'seq': len(state['reports']) + 1,
        'claim': claim,
        'claim_sha256': sha_obj(claim),
        'challenge_nonce': nonce,
        'report_envelopes': copy.deepcopy(envelopes),
        'report_ids': ids,
        'witness_fingerprints': fingerprints,
        'trust_domains': domains,
        'consensus_value': consensus_value,
        'report_consensus': report_consensus,
        'previous_report_sha256': state['report_head_sha256'],
    }
    row['report_sha256'] = _hash_row(row, 'report_sha256')
    state['reports'].append(row); state['report_head_sha256'] = row['report_sha256']
    _audit_links(data, state)
    validate(state); store.save(data, NS, COMPONENT, state)
    return {'ok': True, 'version': 'v1022.7.1', 'report_sha256': row['report_sha256'],
            'report_consensus': report_consensus, 'consensus_value': consensus_value,
            'status': 'CONFIGURED_CONSENSUS_ONLY', 'truth_verified': False,
            'bounded_benchmark_checked': False, 'distinct_witness_keys': len(fingerprints),
            'distinct_configured_domains': len(domains),
            'claim_boundary': copy.deepcopy(state['claim_boundary'])}


@transactional()
def challenge(data, bundle):
    require_alive(data)
    integrate(data)
    state = load(data)
    if not isinstance(bundle, dict) or set(bundle) != {'schema', 'report_sha256',
                                                       'benchmark_manifest', 'oracle_receipt'}:
        raise ValueError('SEMANTIC_TRUTH_CHALLENGE_BUNDLE_FIELDS')
    if bundle.get('schema') != CHALLENGE_BUNDLE_SCHEMA:
        raise ValueError('SEMANTIC_TRUTH_CHALLENGE_BUNDLE_SCHEMA')
    report_sha = _sha256(bundle['report_sha256'], 'REPORT_SHA256')
    report = next((row for row in state['reports'] if row['report_sha256'] == report_sha), None)
    if report is None:
        raise ValueError('SEMANTIC_TRUTH_UNKNOWN_REPORT')
    if report_sha in {row['report_sha256'] for row in state['challenges']}:
        raise ValueError('SEMANTIC_TRUTH_CHALLENGE_REPLAY')
    manifest = _normal_manifest(bundle['benchmark_manifest'])
    oracle = next((row['oracle'] for row in state['oracles']
                   if row['oracle']['scope_id'] == report['claim']['scope_id']), None)
    if oracle is None or manifest['scope_id'] != oracle['scope_id']:
        raise ValueError('SEMANTIC_TRUTH_UNKNOWN_ORACLE_SCOPE')
    manifest_sha = sha_obj(manifest)
    if manifest_sha != oracle['benchmark_manifest_sha256']:
        raise ValueError('SEMANTIC_TRUTH_MANIFEST_NOT_PRECOMMITTED')
    entry = _manifest_entry(manifest, report['claim'])
    receipt = _normal_receipt(bundle['oracle_receipt'], oracle, report, manifest, entry)
    if receipt['receipt_id'] in {row['receipt_id'] for row in state['challenges']}:
        raise ValueError('SEMANTIC_TRUTH_RECEIPT_REPLAY')
    benchmark_match = _matches(report['claim'], entry['expected_value'])
    conflict = ((report['report_consensus'] == 'CLAIM_SUPPORTED') != benchmark_match
                if report['report_consensus'] != 'DISAGREEMENT' else True)
    status = 'BOUNDED_BENCHMARK_VERIFIED' if benchmark_match else 'BOUNDED_BENCHMARK_REFUTED'
    row = {
        'seq': len(state['challenges']) + 1,
        'report_sha256': report_sha,
        'claim_sha256': report['claim_sha256'],
        'oracle_id': oracle['oracle_id'],
        'scope_id': oracle['scope_id'],
        'oracle_key_sha256': oracle['public_key_sha256'],
        'benchmark_manifest': manifest,
        'benchmark_manifest_sha256': manifest_sha,
        'entry_sha256': sha_obj(entry),
        'expected_value': entry['expected_value'],
        'receipt_envelope': copy.deepcopy(bundle['oracle_receipt']),
        'receipt_id': receipt['receipt_id'],
        'report_consensus': report['report_consensus'],
        'benchmark_match': benchmark_match,
        'reports_conflict_with_benchmark': conflict,
        'status': status,
        'previous_challenge_sha256': state['challenge_head_sha256'],
    }
    row['challenge_sha256'] = _hash_row(row, 'challenge_sha256')
    state['challenges'].append(row); state['challenge_head_sha256'] = row['challenge_sha256']
    _audit_links(data, state)
    validate(state); store.save(data, NS, COMPONENT, state)
    return {'ok': True, 'version': 'v1022.7.1', 'challenge_sha256': row['challenge_sha256'],
            'status': status, 'report_consensus': report['report_consensus'],
            'expected_value': entry['expected_value'], 'asserted_value': report['claim']['asserted_value'],
            'reports_conflict_with_benchmark': conflict,
            'bounded_manifest_consistency_verified': True,
            'external_truth_verified': False, 'truth_verified': False,
            'claim_boundary': copy.deepcopy(state['claim_boundary'])}


def _audit_links(data, state):
    evidence_state = evidence.load(data)
    witness_map = evidence._witnesses(evidence_state)
    old_ids, old_evidence = set(), set()
    for row in state['reports']:
        records = [_normal_report(env, witness_map, row['claim'], row['challenge_nonce'])
                   for env in row['report_envelopes']]
        ids = [record['report_id'] for record in records]
        evidences = [record['envelope']['payload']['evidence_sha256'] for record in records]
        if (ids != row['report_ids'] or len(ids) != len(set(ids)) or any(value in old_ids for value in ids)
                or len(evidences) != len(set(evidences)) or any(value in old_evidence for value in evidences)):
            raise ValueError('SEMANTIC_TRUTH_REPORT_REPLAY')
        old_ids.update(ids); old_evidence.update(evidences)
        fingerprints = sorted({record['observer_key_sha256'] for record in records})
        domains = sorted({record['trust_domain'] for record in records})
        if fingerprints != row['witness_fingerprints'] or domains != row['trust_domains']:
            raise ValueError('SEMANTIC_TRUTH_REPORT_SUMMARY')
        value = _consensus_value([record['observed_value'] for record in records], row['claim']['value_type'])
        status = ('DISAGREEMENT' if value is None else
                  ('CLAIM_SUPPORTED' if _matches(row['claim'], value) else 'CLAIM_REFUTED'))
        if value != row['consensus_value'] or status != row['report_consensus']:
            raise ValueError('SEMANTIC_TRUTH_REPORT_DERIVATION')


def _public(state):
    return {
        'ok': True, 'version': 'v1022.7.1', 'individual_id': state['individual_id'],
        'integration_seq': state['integration_seq'], 'oracle_count': len(state['oracles']),
        'report_count': len(state['reports']), 'challenge_count': len(state['challenges']),
        'report_statuses': {row['report_sha256']: 'CONFIGURED_CONSENSUS_ONLY'
                            for row in state['reports']},
        'challenge_statuses': {row['report_sha256']: row['status'] for row in state['challenges']},
        'oracle_head_sha256': state['oracle_head_sha256'],
        'report_head_sha256': state['report_head_sha256'],
        'challenge_head_sha256': state['challenge_head_sha256'],
        'claim_boundary': copy.deepcopy(state['claim_boundary']),
    }


def status(data):
    state = load(data)
    result = _public(state); result['audit'] = audit(data)
    return result


def audit(data):
    try:
        state = load(data)
        ident = _live_identity(data)
        errors = []
        if any(state.get(key) != ident[key] for key in ('individual_id', 'lineage_id', 'branch_id')):
            errors.append('SEMANTIC_TRUTH_IDENTITY')
        try:
            _audit_links(data, state)
        except (ValueError, TypeError, KeyError) as exc:
            errors.append(type(exc).__name__ + ':' + str(exc))
        return {
            'ok': not errors, 'version': 'v1022.7.1', 'errors': errors,
            'oracle_count': len(state['oracles']), 'report_count': len(state['reports']),
            'challenge_count': len(state['challenges']),
            'typed_claims_verified': not errors,
            'report_signatures_and_quorum_verified': not errors,
            'precommitted_manifest_replay_verified': not errors,
            'external_truth_verified': False,
            'real_world_domain_independence_verified': False,
            'literal_soul_established': False,
            'consciousness_established': False,
        }
    except (ValueError, TypeError, KeyError, OSError) as exc:
        return {
            'ok': False, 'version': 'v1022.7.1',
            'errors': [type(exc).__name__ + ':' + str(exc)],
            'external_truth_verified': False,
            'real_world_domain_independence_verified': False,
            'literal_soul_established': False,
            'consciousness_established': False,
        }
