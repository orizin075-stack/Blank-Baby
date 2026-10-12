#!/usr/bin/env python3
"""Independent V1022.7 evidence-bound Soul verifier.

Deliberately imports no TUKUYO runtime module.  It replays the signed commit
chain, authority certificates, witness signatures, quorum, median aggregation,
attestation status and Whole State component binding from raw JSON bytes.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import statistics
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


ZERO = '0' * 64
NS = 'evidence_bound_soul'
COMPONENT = 'whole_evidence_bound_soul'
EFFECTS = ('self_wellbeing', 'others_wellbeing', 'future_self',
           'truth_consistency', 'bodily_cost', 'uncertainty')


def canon(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode()


def sha_obj(value):
    return hashlib.sha256(canon(value)).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def verify_envelope(envelope, public_key):
    if set(envelope) != {'payload', 'public_key', 'signature'} or envelope['public_key'] != public_key:
        return False
    try:
        Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key, validate=True)).verify(
            base64.b64decode(envelope['signature'], validate=True), canon(envelope['payload']))
        return True
    except Exception:
        return False


def row_hash(row, field):
    value = dict(row); value.pop(field, None)
    return sha_obj(value)


def status_for(decision_sha, rows):
    strong = [row for row in rows
              if row['envelope']['payload']['decision_sha256'] == decision_sha
              and float(row['envelope']['payload']['confidence']) >= .7]
    domains = {row['trust_domain'] for row in strong}
    witnesses = {row['observer_key_sha256'] for row in strong}
    if len(domains) >= 3 and len(witnesses) >= 3:
        return 'MULTI_DOMAIN_ATTESTED'
    if len(domains) >= 2 and len(witnesses) >= 2:
        return 'MULTI_DOMAIN_LIMITED'
    return 'AUTHENTICATED_SINGLE_SOURCE' if strong else 'AUTHENTICATED_LOW_CONFIDENCE'


def verify(root):
    root = Path(root)
    errors = []
    try:
        whole_public = (root / 'v977' / 'whole_state.pub').read_text(encoding='utf-8').strip()
        whole_env = read(root / 'v977' / 'UNIFIED_STATE.json')
        if not verify_envelope(whole_env, whole_public):
            errors.append('WHOLE_SIGNATURE')
        cache_path = root / NS / 'STATE.json'
        cache_bytes = cache_path.read_bytes()
        cache = json.loads(cache_bytes)
        component_hash = whole_env.get('payload', {}).get('component_hashes', {}).get(COMPONENT)
        if hashlib.sha256(cache_bytes).hexdigest() != component_hash:
            errors.append('WHOLE_COMPONENT_BINDING')

        commits = sorted((root / NS / 'commits').glob('*.json'))
        previous = ZERO
        latest = None
        for index, path in enumerate(commits, 1):
            envelope = read(path)
            payload = envelope.get('payload', {})
            if path.name != f'{index:012d}.json' or not verify_envelope(envelope, whole_public):
                errors.append(f'COMMIT_SIGNATURE:{index}')
            if (payload.get('schema') != 'tukuyo.v1022.commit/1'
                    or payload.get('namespace') != NS or payload.get('seq') != index
                    or payload.get('previous') != previous):
                errors.append(f'COMMIT_CHAIN:{index}')
            previous = sha_obj(envelope)
            latest = payload.get('state')
        if latest is None or cache.get('head') != previous or cache.get('state') != latest:
            errors.append('CACHE_HEAD')
        state = latest or {}
        if state.get('schema') != 'tukuyo.v1022_7.evidence_bound_soul/1':
            errors.append('STATE_SCHEMA')

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
                fingerprint = ''
                errors.append(f'AUTHORITY_KEY:{index}')
            if (row.get('seq') != index or row.get('previous_authority_sha256') != previous
                    or row.get('authority_row_sha256') != row_hash(row, 'authority_row_sha256')):
                errors.append(f'AUTHORITY_CHAIN:{index}')
            if authority.get('public_key_sha256') != fingerprint or fingerprint in authority_keys:
                errors.append(f'AUTHORITY_FINGERPRINT:{index}')
            authority_keys.add(fingerprint)
            authority_map[authority.get('authority_id')] = authority
            previous = row.get('authority_row_sha256')
        if state.get('authority_head_sha256') != previous:
            errors.append('AUTHORITY_HEAD')

        witness_map = {}
        witness_keys = set()
        previous = ZERO
        for index, row in enumerate(state.get('witnesses', []), 1):
            witness = row.get('witness', {})
            certificate = witness.get('certificate', {})
            payload = certificate.get('payload', {})
            authority = authority_map.get(payload.get('authority_id'), {})
            if not authority or not verify_envelope(certificate, authority.get('public_key')):
                errors.append(f'WITNESS_CERTIFICATE:{index}')
            try:
                raw = base64.b64decode(payload['observer_public_key'], validate=True)
                Ed25519PublicKey.from_public_bytes(raw)
                fingerprint = hashlib.sha256(raw).hexdigest()
            except Exception:
                fingerprint = ''
                errors.append(f'WITNESS_KEY:{index}')
            if (payload.get('trust_domain') != authority.get('trust_domain')
                    or witness.get('observer_key_sha256') != fingerprint
                    or fingerprint in witness_keys):
                errors.append(f'WITNESS_BINDING:{index}')
            if (row.get('seq') != index or row.get('previous_witness_sha256') != previous
                    or row.get('witness_row_sha256') != row_hash(row, 'witness_row_sha256')):
                errors.append(f'WITNESS_CHAIN:{index}')
            witness_keys.add(fingerprint)
            witness_map[payload.get('observer_id')] = {
                'public_key': payload.get('observer_public_key'),
                'fingerprint': fingerprint,
                'authority_id': payload.get('authority_id'),
                'trust_domain': payload.get('trust_domain'),
            }
            previous = row.get('witness_row_sha256')
        if state.get('witness_head_sha256') != previous:
            errors.append('WITNESS_HEAD')

        decision_map = {}
        assessment_ids = set()
        assessment_evidence = set()
        previous = ZERO
        for index, row in enumerate(state.get('decisions', []), 1):
            options = row.get('core_options', [])
            option_ids = [option.get('id') for option in options]
            if row.get('core_options_sha256') != sha_obj(options):
                errors.append(f'OPTION_HASH:{index}')
            records = []
            for envelope in row.get('assessment_envelopes', []):
                payload = envelope.get('payload', {})
                witness = witness_map.get(payload.get('observer_id'), {})
                if not witness or not verify_envelope(envelope, witness.get('public_key')):
                    errors.append(f'ASSESSMENT_SIGNATURE:{index}')
                    continue
                if (payload.get('schema') != 'tukuyo.v1022_7.option_assessment/1'
                        or payload.get('options_sha256') != sha_obj(options)
                        or payload.get('context_sha256') != sha_obj(row.get('context'))
                        or set(payload.get('effects_by_option', {})) != set(option_ids)):
                    errors.append(f'ASSESSMENT_BINDING:{index}')
                assessment_id = payload.get('assessment_id')
                evidence_sha = payload.get('evidence_sha256')
                if assessment_id in assessment_ids or evidence_sha in assessment_evidence:
                    errors.append(f'ASSESSMENT_REPLAY:{index}')
                assessment_ids.add(assessment_id); assessment_evidence.add(evidence_sha)
                for option_id in option_ids:
                    if set(payload['effects_by_option'].get(option_id, {})) != set(EFFECTS):
                        errors.append(f'ASSESSMENT_COVERAGE:{index}')
                records.append((payload, witness))
            domains = sorted({witness['trust_domain'] for _, witness in records})
            fingerprints = sorted({witness['fingerprint'] for _, witness in records})
            if len(domains) < 3 or len(fingerprints) < 3:
                errors.append(f'ASSESSMENT_QUORUM:{index}')
            aggregate = {option_id: {
                effect: round(float(statistics.median([
                    payload['effects_by_option'][option_id][effect] for payload, _ in records])), 6)
                for effect in EFFECTS} for option_id in option_ids} if records else {}
            if (row.get('trust_domains') != domains
                    or row.get('witness_fingerprints') != fingerprints
                    or row.get('aggregated_effects') != aggregate):
                errors.append(f'ASSESSMENT_AGGREGATE:{index}')
            if (row.get('seq') != index or row.get('previous_decision_sha256') != previous
                    or row.get('decision_sha256') != row_hash(row, 'decision_sha256')):
                errors.append(f'DECISION_CHAIN:{index}')
            decision_map[row.get('decision_sha256')] = row
            previous = row.get('decision_sha256')
        if state.get('decision_head_sha256') != previous:
            errors.append('DECISION_HEAD')

        previous = ZERO
        attestations = []
        attestation_ids = set()
        outcome_evidence = set()
        for index, row in enumerate(state.get('attestations', []), 1):
            envelope = row.get('envelope', {})
            payload = envelope.get('payload', {})
            witness = witness_map.get(payload.get('observer_id'), {})
            decision = decision_map.get(payload.get('decision_sha256'))
            if not witness or not verify_envelope(envelope, witness.get('public_key')):
                errors.append(f'ATTESTATION_SIGNATURE:{index}')
            if (not decision or payload.get('chosen') != decision.get('chosen')
                    or payload.get('schema') != 'tukuyo.v1022_7.outcome_attestation/1'):
                errors.append(f'ATTESTATION_BINDING:{index}')
            if (payload.get('attestation_id') in attestation_ids
                    or payload.get('evidence_sha256') in outcome_evidence):
                errors.append(f'ATTESTATION_REPLAY:{index}')
            attestation_ids.add(payload.get('attestation_id'))
            outcome_evidence.add(payload.get('evidence_sha256'))
            if (row.get('observer_key_sha256') != witness.get('fingerprint')
                    or row.get('trust_domain') != witness.get('trust_domain')
                    or row.get('authority_id') != witness.get('authority_id')
                    or row.get('envelope_sha256') != sha_obj(envelope)):
                errors.append(f'ATTESTATION_SOURCE:{index}')
            attestations.append(row)
            if row.get('derived_status') != status_for(payload.get('decision_sha256'), attestations):
                errors.append(f'ATTESTATION_STATUS:{index}')
            if (row.get('seq') != index or row.get('previous_attestation_sha256') != previous
                    or row.get('attestation_sha256') != row_hash(row, 'attestation_sha256')):
                errors.append(f'ATTESTATION_CHAIN:{index}')
            previous = row.get('attestation_sha256')
        if state.get('attestation_head_sha256') != previous:
            errors.append('ATTESTATION_HEAD')

        boundary = state.get('claim_boundary', {})
        if (boundary.get('signatures_establish_truth') is not False
                or boundary.get('authority_domains_prove_real_world_independence') is not False
                or boundary.get('literal_soul_established') is not False
                or boundary.get('consciousness_established') is not False):
            errors.append('CLAIM_BOUNDARY')
        return {
            'ok': not errors,
            'schema': 'tukuyo.v1022_7.independent_evidence_verification/1',
            'errors': errors,
            'commits': len(commits),
            'authorities': len(authority_map),
            'witnesses': len(witness_map),
            'decisions': len(decision_map),
            'attestations': len(attestations),
            'cryptographic_authorship_verified': not errors,
            'median_aggregation_replayed': not errors,
            'external_truth_verified': False,
            'real_world_domain_independence_verified': False,
            'literal_soul_established': False,
            'consciousness_established': False,
        }
    except Exception as exc:
        return {
            'ok': False,
            'schema': 'tukuyo.v1022_7.independent_evidence_verification/1',
            'errors': [type(exc).__name__ + ':' + str(exc)],
            'external_truth_verified': False,
            'real_world_domain_independence_verified': False,
            'literal_soul_established': False,
            'consciousness_established': False,
        }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.data)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    raise SystemExit(0 if result['ok'] else 1)
