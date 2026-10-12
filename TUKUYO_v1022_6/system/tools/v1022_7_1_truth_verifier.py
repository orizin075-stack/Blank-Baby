#!/usr/bin/env python3
"""Independent raw verifier for V1022.7.1 bounded truth challenges.

This file imports no TUKUYO runtime module.  It verifies signatures, commit
chains, typed claims, exact unit binding, report quorum, precommitted benchmark
lookup and oracle receipt replay directly from JSON.  Its result is explicitly
bounded to the supplied benchmark; external reality is not established.
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
TRUTH_NS = 'semantic_truth'
TRUTH_COMPONENT = 'whole_semantic_truth'
EVIDENCE_NS = 'evidence_bound_soul'
EVIDENCE_COMPONENT = 'whole_evidence_bound_soul'


def canon(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode()


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


def row_hash(row, field):
    value = dict(row); value.pop(field, None)
    return sha_obj(value)


def load_signed_namespace(root, namespace, component, whole_public, whole_payload, errors):
    cache_path = root / namespace / 'STATE.json'
    cache_bytes = cache_path.read_bytes()
    cache = json.loads(cache_bytes)
    if hashlib.sha256(cache_bytes).hexdigest() != whole_payload.get('component_hashes', {}).get(component):
        errors.append(namespace.upper() + '_WHOLE_BINDING')
    previous = ZERO
    latest = None
    commits = sorted((root / namespace / 'commits').glob('*.json'))
    for index, path in enumerate(commits, 1):
        envelope = read(path); payload = envelope.get('payload', {})
        if path.name != f'{index:012d}.json' or not verify_envelope(envelope, whole_public):
            errors.append(f'{namespace.upper()}_COMMIT_SIGNATURE:{index}')
        if (payload.get('schema') != 'tukuyo.v1022.commit/1'
                or payload.get('namespace') != namespace or payload.get('seq') != index
                or payload.get('previous') != previous):
            errors.append(f'{namespace.upper()}_COMMIT_CHAIN:{index}')
        previous = sha_obj(envelope); latest = payload.get('state')
    if latest is None or cache.get('head') != previous or cache.get('state') != latest:
        errors.append(namespace.upper() + '_CACHE_HEAD')
    return latest or {}, len(commits)


def scalar(value, value_type):
    if value_type == 'number':
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError('number')
        value = round(float(value), 9)
        return int(value) if value.is_integer() else value
    if value_type == 'string':
        if not isinstance(value, str) or not value:
            raise ValueError('string')
        return value
    if value_type == 'boolean' and type(value) is bool:
        return value
    raise ValueError('value_type')


def matches(claim, value):
    value = scalar(value, claim['value_type'])
    if claim['comparator'] == 'equal':
        return value == claim['asserted_value']
    return abs(float(value) - float(claim['asserted_value'])) <= float(claim['tolerance'])


def consensus(values, value_type):
    if value_type == 'number':
        return scalar(statistics.median([float(value) for value in values]), 'number')
    counts = {}
    for value in values:
        key = json.dumps(value, ensure_ascii=False, sort_keys=True)
        counts[key] = counts.get(key, 0) + 1
    winner, count = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0]
    return json.loads(winner) if count > len(values) // 2 else None


def evidence_witnesses(state, errors):
    authority_map = {}
    authority_keys = set()
    previous = ZERO
    for index, row in enumerate(state.get('authorities', []), 1):
        authority = row.get('authority', {})
        try:
            raw = base64.b64decode(authority['public_key'], validate=True)
            Ed25519PublicKey.from_public_bytes(raw)
            fingerprint = hashlib.sha256(raw).hexdigest()
        except Exception:
            fingerprint = ''; errors.append(f'EVIDENCE_AUTHORITY_KEY:{index}')
        if (row.get('seq') != index or row.get('previous_authority_sha256') != previous
                or row.get('authority_row_sha256') != row_hash(row, 'authority_row_sha256')
                or authority.get('public_key_sha256') != fingerprint or fingerprint in authority_keys):
            errors.append(f'EVIDENCE_AUTHORITY_CHAIN:{index}')
        authority_keys.add(fingerprint); authority_map[authority.get('authority_id')] = authority
        previous = row.get('authority_row_sha256')
    if state.get('authority_head_sha256') != previous:
        errors.append('EVIDENCE_AUTHORITY_HEAD')
    witness_map = {}
    witness_keys = set()
    previous = ZERO
    for index, row in enumerate(state.get('witnesses', []), 1):
        witness = row.get('witness', {}); certificate = witness.get('certificate', {})
        payload = certificate.get('payload', {}); authority = authority_map.get(payload.get('authority_id'), {})
        if not authority or not verify_envelope(certificate, authority.get('public_key')):
            errors.append(f'EVIDENCE_WITNESS_CERTIFICATE:{index}')
        try:
            raw = base64.b64decode(payload['observer_public_key'], validate=True)
            Ed25519PublicKey.from_public_bytes(raw)
            fingerprint = hashlib.sha256(raw).hexdigest()
        except Exception:
            fingerprint = ''; errors.append(f'EVIDENCE_WITNESS_KEY:{index}')
        if (payload.get('trust_domain') != authority.get('trust_domain')
                or witness.get('observer_key_sha256') != fingerprint or fingerprint in witness_keys
                or row.get('seq') != index or row.get('previous_witness_sha256') != previous
                or row.get('witness_row_sha256') != row_hash(row, 'witness_row_sha256')):
            errors.append(f'EVIDENCE_WITNESS_BINDING:{index}')
        witness_keys.add(fingerprint)
        witness_map[payload.get('observer_id')] = {
            'public_key': payload.get('observer_public_key'), 'fingerprint': fingerprint,
            'authority_id': payload.get('authority_id'), 'trust_domain': payload.get('trust_domain')}
        previous = row.get('witness_row_sha256')
    if state.get('witness_head_sha256') != previous:
        errors.append('EVIDENCE_WITNESS_HEAD')
    return witness_map, authority_keys | witness_keys


def verify(root):
    root = Path(root); errors = []
    try:
        whole_public = (root / 'v977' / 'whole_state.pub').read_text(encoding='utf-8').strip()
        whole_env = read(root / 'v977' / 'UNIFIED_STATE.json')
        if not verify_envelope(whole_env, whole_public):
            errors.append('WHOLE_SIGNATURE')
        whole_payload = whole_env.get('payload', {})
        evidence_state, evidence_commits = load_signed_namespace(
            root, EVIDENCE_NS, EVIDENCE_COMPONENT, whole_public, whole_payload, errors)
        truth_state, truth_commits = load_signed_namespace(
            root, TRUTH_NS, TRUTH_COMPONENT, whole_public, whole_payload, errors)
        if evidence_state.get('schema') != 'tukuyo.v1022_7.evidence_bound_soul/1':
            errors.append('EVIDENCE_SCHEMA')
        if truth_state.get('schema') != 'tukuyo.v1022_7_1.semantic_truth/1':
            errors.append('TRUTH_SCHEMA')
        witness_map, forbidden_keys = evidence_witnesses(evidence_state, errors)

        oracle_map = {}; scopes = set(); oracle_keys = set(); manifest_hashes = set()
        previous = ZERO
        for index, row in enumerate(truth_state.get('oracles', []), 1):
            oracle = row.get('oracle', {})
            try:
                raw = base64.b64decode(oracle['public_key'], validate=True)
                Ed25519PublicKey.from_public_bytes(raw)
                fingerprint = hashlib.sha256(raw).hexdigest()
            except Exception:
                fingerprint = ''; errors.append(f'ORACLE_KEY:{index}')
            if (oracle.get('public_key_sha256') != fingerprint or fingerprint in oracle_keys
                    or fingerprint in forbidden_keys or oracle.get('scope_id') in scopes
                    or oracle.get('benchmark_manifest_sha256') in manifest_hashes
                    or row.get('seq') != index or row.get('previous_oracle_sha256') != previous
                    or row.get('oracle_row_sha256') != row_hash(row, 'oracle_row_sha256')):
                errors.append(f'ORACLE_BINDING:{index}')
            oracle_keys.add(fingerprint); scopes.add(oracle.get('scope_id'))
            manifest_hashes.add(oracle.get('benchmark_manifest_sha256'))
            oracle_map[oracle.get('oracle_id')] = oracle
            previous = row.get('oracle_row_sha256')
        if truth_state.get('oracle_head_sha256') != previous:
            errors.append('ORACLE_HEAD')

        report_map = {}; report_ids = set(); evidence_ids = set(); claim_ids = set(); nonces = set()
        previous = ZERO
        for index, row in enumerate(truth_state.get('reports', []), 1):
            claim = row.get('claim', {})
            required_claim = {'schema', 'claim_id', 'scope_id', 'subject', 'predicate',
                              'context_sha256', 'value_type', 'unit', 'comparator',
                              'tolerance', 'asserted_value'}
            if set(claim) != required_claim or claim.get('schema') != 'tukuyo.v1022_7_1.typed_claim/1':
                errors.append(f'CLAIM_FIELDS:{index}')
            if (row.get('claim_sha256') != sha_obj(claim) or claim.get('claim_id') in claim_ids
                    or row.get('challenge_nonce') in nonces):
                errors.append(f'CLAIM_BINDING:{index}')
            claim_ids.add(claim.get('claim_id')); nonces.add(row.get('challenge_nonce'))
            records = []
            for envelope in row.get('report_envelopes', []):
                payload = envelope.get('payload', {}); witness = witness_map.get(payload.get('observer_id'), {})
                if not witness or not verify_envelope(envelope, witness.get('public_key')):
                    errors.append(f'REPORT_SIGNATURE:{index}')
                if (payload.get('schema') != 'tukuyo.v1022_7_1.signed_report/1'
                        or payload.get('claim_sha256') != sha_obj(claim)
                        or payload.get('challenge_nonce') != row.get('challenge_nonce')
                        or payload.get('value_type') != claim.get('value_type')
                        or payload.get('unit') != claim.get('unit')):
                    errors.append(f'REPORT_BINDING:{index}')
                report_id = payload.get('report_id'); evidence_id = payload.get('evidence_sha256')
                if report_id in report_ids or evidence_id in evidence_ids:
                    errors.append(f'REPORT_REPLAY:{index}')
                report_ids.add(report_id); evidence_ids.add(evidence_id)
                try:
                    value = scalar(payload.get('observed_value'), claim.get('value_type'))
                except Exception:
                    value = None; errors.append(f'REPORT_VALUE:{index}')
                records.append((payload, witness, value))
            fingerprints = sorted({witness.get('fingerprint') for _, witness, _ in records})
            domains = sorted({witness.get('trust_domain') for _, witness, _ in records})
            if len(fingerprints) < 3 or len(domains) < 3:
                errors.append(f'REPORT_QUORUM:{index}')
            try:
                value = consensus([value for _, _, value in records], claim.get('value_type'))
                status = ('DISAGREEMENT' if value is None else
                          ('CLAIM_SUPPORTED' if matches(claim, value) else 'CLAIM_REFUTED'))
            except Exception:
                value = None; status = 'ERROR'; errors.append(f'REPORT_DERIVATION:{index}')
            if (row.get('report_ids') != [payload.get('report_id') for payload, _, _ in records]
                    or row.get('witness_fingerprints') != fingerprints
                    or row.get('trust_domains') != domains
                    or row.get('consensus_value') != value or row.get('report_consensus') != status):
                errors.append(f'REPORT_SUMMARY:{index}')
            if (row.get('seq') != index or row.get('previous_report_sha256') != previous
                    or row.get('report_sha256') != row_hash(row, 'report_sha256')):
                errors.append(f'REPORT_CHAIN:{index}')
            report_map[row.get('report_sha256')] = row; previous = row.get('report_sha256')
        if truth_state.get('report_head_sha256') != previous:
            errors.append('REPORT_HEAD')

        challenged = set(); receipts = set(); previous = ZERO
        for index, row in enumerate(truth_state.get('challenges', []), 1):
            report = report_map.get(row.get('report_sha256')); oracle = oracle_map.get(row.get('oracle_id'))
            if not report or row.get('report_sha256') in challenged:
                errors.append(f'CHALLENGE_REPORT:{index}')
            challenged.add(row.get('report_sha256'))
            manifest = row.get('benchmark_manifest', {})
            if (not oracle or manifest.get('schema') != 'tukuyo.v1022_7_1.benchmark_manifest/1'
                    or manifest.get('scope_id') != oracle.get('scope_id')
                    or sha_obj(manifest) != oracle.get('benchmark_manifest_sha256')
                    or row.get('benchmark_manifest_sha256') != sha_obj(manifest)):
                errors.append(f'MANIFEST_BINDING:{index}')
            claim = report.get('claim', {}) if report else {}
            entries = [entry for entry in manifest.get('entries', [])
                       if entry.get('subject') == claim.get('subject')
                       and entry.get('predicate') == claim.get('predicate')
                       and entry.get('context_sha256') == claim.get('context_sha256')]
            if len(entries) != 1:
                errors.append(f'MANIFEST_COVERAGE:{index}'); entry = {}
            else:
                entry = entries[0]
            envelope = row.get('receipt_envelope', {}); payload = envelope.get('payload', {})
            if not oracle or not verify_envelope(envelope, oracle.get('public_key')):
                errors.append(f'RECEIPT_SIGNATURE:{index}')
            if (payload.get('schema') != 'tukuyo.v1022_7_1.oracle_receipt/1'
                    or payload.get('report_sha256') != row.get('report_sha256')
                    or payload.get('claim_sha256') != row.get('claim_sha256')
                    or payload.get('challenge_nonce') != (report or {}).get('challenge_nonce')
                    or payload.get('benchmark_manifest_sha256') != sha_obj(manifest)
                    or payload.get('entry_sha256') != sha_obj(entry)
                    or payload.get('expected_value') != entry.get('expected_value')
                    or payload.get('unit') != claim.get('unit')):
                errors.append(f'RECEIPT_BINDING:{index}')
            if payload.get('receipt_id') in receipts or row.get('receipt_id') != payload.get('receipt_id'):
                errors.append(f'RECEIPT_REPLAY:{index}')
            receipts.add(payload.get('receipt_id'))
            try:
                benchmark_match = matches(claim, entry.get('expected_value'))
                conflict = (((report or {}).get('report_consensus') == 'CLAIM_SUPPORTED') != benchmark_match
                            if (report or {}).get('report_consensus') != 'DISAGREEMENT' else True)
                status = 'BOUNDED_BENCHMARK_VERIFIED' if benchmark_match else 'BOUNDED_BENCHMARK_REFUTED'
            except Exception:
                benchmark_match = None; conflict = None; status = 'ERROR'
                errors.append(f'CHALLENGE_DERIVATION:{index}')
            if (row.get('entry_sha256') != sha_obj(entry)
                    or row.get('expected_value') != entry.get('expected_value')
                    or row.get('report_consensus') != (report or {}).get('report_consensus')
                    or row.get('benchmark_match') is not benchmark_match
                    or row.get('reports_conflict_with_benchmark') is not conflict
                    or row.get('status') != status):
                errors.append(f'CHALLENGE_SUMMARY:{index}')
            if (row.get('seq') != index or row.get('previous_challenge_sha256') != previous
                    or row.get('challenge_sha256') != row_hash(row, 'challenge_sha256')):
                errors.append(f'CHALLENGE_CHAIN:{index}')
            previous = row.get('challenge_sha256')
        if truth_state.get('challenge_head_sha256') != previous:
            errors.append('CHALLENGE_HEAD')
        boundary = truth_state.get('claim_boundary', {})
        if (boundary.get('report_consensus_establishes_truth') is not False
                or boundary.get('bounded_benchmark_proves_external_reality') is not False
                or boundary.get('literal_soul_established') is not False
                or boundary.get('consciousness_established') is not False):
            errors.append('CLAIM_BOUNDARY')
        return {
            'ok': not errors,
            'schema': 'tukuyo.v1022_7_1.independent_truth_verification/1',
            'errors': errors, 'evidence_commits': evidence_commits,
            'truth_commits': truth_commits, 'witnesses': len(witness_map),
            'oracles': len(oracle_map), 'reports': len(report_map),
            'challenges': len(truth_state.get('challenges', [])),
            'typed_claim_and_unit_binding_replayed': not errors,
            'precommitted_manifest_replayed': not errors,
            'oracle_receipt_signature_replayed': not errors,
            'external_truth_verified': False,
            'real_world_domain_independence_verified': False,
            'literal_soul_established': False,
            'consciousness_established': False,
        }
    except Exception as exc:
        errors.append(type(exc).__name__ + ':' + str(exc))
        return {'ok': False, 'schema': 'tukuyo.v1022_7_1.independent_truth_verification/1',
                'errors': errors, 'external_truth_verified': False,
                'real_world_domain_independence_verified': False,
                'literal_soul_established': False, 'consciousness_established': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True, type=Path)
    args = parser.parse_args()
    result = verify(args.data)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if result['ok'] else 1)


if __name__ == '__main__':
    main()
