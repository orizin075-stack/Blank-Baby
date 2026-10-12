"""V1022.7 authenticated evidence, anti-Sybil boundaries and proof limits."""
from __future__ import annotations

import base64
import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from test_v1022_5_fusion import ROOT, run
from tukuyo_v977.whole_state import canon, sha_obj
from tukuyo_v1022 import evidence_bound_soul as es
from tukuyo_v1022 import reflective_soul as rs


CORE_OPTIONS = [
    {'id': 'immediate_self_gain', 'signals': {'survival': 1.0}, 'themes': [], 'conflicts': []},
    {'id': 'responsible_long_term', 'signals': {}, 'themes': [], 'conflicts': []},
]

HONEST_EFFECTS = {
    'immediate_self_gain': {
        'self_wellbeing': .8, 'others_wellbeing': -1.0, 'future_self': -.8,
        'truth_consistency': -.8, 'bodily_cost': 0.0, 'uncertainty': 0.0,
    },
    'responsible_long_term': {
        'self_wellbeing': -.1, 'others_wellbeing': .9, 'future_self': .9,
        'truth_consistency': .9, 'bodily_cost': .1, 'uncertainty': 0.0,
    },
}


def public(sk):
    return base64.b64encode(sk.public_key().public_bytes_raw()).decode()


def envelope(sk, payload):
    return {
        'payload': payload,
        'public_key': public(sk),
        'signature': base64.b64encode(sk.sign(canon(payload))).decode(),
    }


def file_bytes(root):
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in Path(root).rglob('*') if p.is_file()}


def setup(root):
    run(root, 'init', '--individual-id', 'SOUL-V1022-7')
    es.integrate(root)
    authorities = []
    witnesses = []
    for index in range(3):
        authority_key = Ed25519PrivateKey.generate()
        witness_key = Ed25519PrivateKey.generate()
        authority = {
            'schema': es.AUTHORITY_SCHEMA,
            'authority_id': f'authority-{index}',
            'trust_domain': f'domain-{index}',
            'public_key': public(authority_key),
        }
        es.add_authority(root, authority)
        payload = {
            'schema': es.WITNESS_SCHEMA,
            'certificate_id': f'certificate-{index}',
            'observer_id': f'observer-{index}',
            'observer_public_key': public(witness_key),
            'authority_id': authority['authority_id'],
            'trust_domain': authority['trust_domain'],
        }
        es.add_witness(root, envelope(authority_key, payload))
        authorities.append((authority, authority_key))
        witnesses.append((payload['observer_id'], witness_key))
    return authorities, witnesses


def assessment(observer_id, key, index, context='evidence bound decision', effects=None):
    payload = {
        'schema': es.ASSESSMENT_SCHEMA,
        'assessment_id': f'assessment-{index}',
        'observer_id': observer_id,
        'options_sha256': sha_obj(CORE_OPTIONS),
        'context_sha256': sha_obj(context),
        'measurement_kind': 'bounded_evaluator',
        'evidence_sha256': sha_obj({'assessment-evidence': index}),
        'effects_by_option': copy.deepcopy(effects or HONEST_EFFECTS),
    }
    return envelope(key, payload)


def bundle(witnesses, effects_by_index=None, context='evidence bound decision'):
    effects_by_index = effects_by_index or {}
    return {
        'schema': es.BUNDLE_SCHEMA,
        'context': context,
        'options': copy.deepcopy(CORE_OPTIONS),
        'assessments': [assessment(observer_id, key, index, context,
                                   effects_by_index.get(index))
                        for index, (observer_id, key) in enumerate(witnesses)],
    }


def attestation(observer_id, key, decision, index, confidence=.9, chosen=None):
    payload = {
        'schema': es.ATTESTATION_SCHEMA,
        'attestation_id': f'attestation-{index}',
        'observer_id': observer_id,
        'decision_sha256': decision['decision_sha256'],
        'chosen': chosen or decision['chosen'],
        'measurement_kind': 'sensor_reading',
        'evidence_sha256': sha_obj({'outcome-evidence': index}),
        'source_kind': 'direct_observation',
        'self_wellbeing': .2,
        'others_wellbeing': .9,
        'future_self': .8,
        'truth_consistency': .9,
        'bodily_cost': .1,
        'surprise': .2,
        'confidence': confidence,
        'note': f'signed outcome {index}',
    }
    return envelope(key, payload)


def test_registers_three_domains_and_binds_whole_state(tmp_path):
    data = tmp_path / 'data'
    setup(data)
    status = es.status(data)
    assert status['authority_count'] == 3 and status['witness_count'] == 3
    assert status['claim_boundary']['signatures_establish_truth'] is False
    assert status['claim_boundary']['authority_domains_prove_real_world_independence'] is False
    assert es.audit(data)['ok'] and run(data, 'whole-audit')['ok']


def test_legacy_unsigned_ids_are_no_longer_called_corroborated(tmp_path):
    data = tmp_path / 'data'; run(data, 'init', '--individual-id', 'LEGACY-LABEL-FIX')
    options = [dict(option, effects=copy.deepcopy(HONEST_EFFECTS[option['id']])) for option in CORE_OPTIONS]
    first = rs.deliberate(data, options)
    outcome = {'evidence_id': 'unsigned-1', 'observer_id': 'invented-A',
               'source_kind': 'direct_observation', 'self_wellbeing': .2,
               'others_wellbeing': .9, 'future_self': .8, 'truth_consistency': .9,
               'bodily_cost': .1, 'surprise': .2, 'confidence': .9, 'note': 'unsigned'}
    assert rs.reflect(data, first['decision_sha256'], outcome)['reappraisal_status'] == 'SINGLE_ID_CLAIM_UNAUTHENTICATED'
    second = rs.deliberate(data, options)
    outcome['evidence_id'] = 'unsigned-2'; outcome['observer_id'] = 'invented-B'
    result = rs.reflect(data, second['decision_sha256'], outcome)
    assert result['reappraisal_status'] == 'MULTI_ID_CLAIM_UNAUTHENTICATED'
    assert 'CORROBORATED' not in result['reappraisal_status']


def test_assessment_requires_three_registered_trust_domains(tmp_path):
    data = tmp_path / 'data'; _, witnesses = setup(data)
    before = file_bytes(data)
    with pytest.raises(ValueError, match='ASSESSMENT_COUNT|ASSESSMENT_QUORUM'):
        es.deliberate(data, bundle(witnesses[:2]))
    assert file_bytes(data) == before


def test_same_authority_key_cannot_masquerade_as_second_domain(tmp_path):
    data = tmp_path / 'data'; run(data, 'init', '--individual-id', 'AUTHORITY-REUSE')
    key = Ed25519PrivateKey.generate()
    es.add_authority(data, {'schema': es.AUTHORITY_SCHEMA, 'authority_id': 'a',
                            'trust_domain': 'domain-a', 'public_key': public(key)})
    before = file_bytes(data)
    with pytest.raises(ValueError, match='AUTHORITY_KEY_REUSE'):
        es.add_authority(data, {'schema': es.AUTHORITY_SCHEMA, 'authority_id': 'b',
                                'trust_domain': 'domain-b', 'public_key': public(key)})
    assert file_bytes(data) == before


def test_witness_signature_and_authority_binding_are_mandatory(tmp_path):
    data = tmp_path / 'data'; authorities, _ = setup(data)
    authority, _ = authorities[0]
    fake_authority = Ed25519PrivateKey.generate()
    witness_key = Ed25519PrivateKey.generate()
    payload = {'schema': es.WITNESS_SCHEMA, 'certificate_id': 'forged',
               'observer_id': 'forged-observer', 'observer_public_key': public(witness_key),
               'authority_id': authority['authority_id'], 'trust_domain': authority['trust_domain']}
    before = file_bytes(data)
    with pytest.raises(ValueError, match='SIGNER_MISMATCH|SIGNATURE'):
        es.add_witness(data, envelope(fake_authority, payload))
    assert file_bytes(data) == before


def test_median_aggregation_tolerates_one_extreme_assessment(tmp_path):
    data = tmp_path / 'data'; _, witnesses = setup(data)
    malicious = {key: {name: (-value if name not in ('bodily_cost', 'uncertainty') else value)
                       for name, value in effects.items()}
                 for key, effects in HONEST_EFFECTS.items()}
    result = es.deliberate(data, bundle(witnesses, {2: malicious}))
    assert result['chosen'] == 'responsible_long_term'
    assert result['aggregated_effects'] == HONEST_EFFECTS
    assert result['verified_assessments'] == 3
    assert result['distinct_configured_trust_domains'] == 3


def test_all_signed_sources_can_still_be_wrong_so_truth_remains_false(tmp_path):
    data = tmp_path / 'data'; _, witnesses = setup(data)
    inverted = {
        'immediate_self_gain': copy.deepcopy(HONEST_EFFECTS['responsible_long_term']),
        'responsible_long_term': copy.deepcopy(HONEST_EFFECTS['immediate_self_gain']),
    }
    result = es.deliberate(data, bundle(witnesses, {0: inverted, 1: inverted, 2: inverted}))
    assert result['chosen'] == 'immediate_self_gain'
    assert result['claim_boundary']['signatures_establish_truth'] is False
    assert result['claim_boundary']['external_semantics_verified'] is False


def test_outcome_status_requires_three_signed_domains(tmp_path):
    data = tmp_path / 'data'; _, witnesses = setup(data)
    decision = es.deliberate(data, bundle(witnesses))
    first = es.attest(data, attestation(*witnesses[0], decision, 0))
    second = es.attest(data, attestation(*witnesses[1], decision, 1))
    third = es.attest(data, attestation(*witnesses[2], decision, 2))
    assert first['status'] == 'AUTHENTICATED_SINGLE_SOURCE'
    assert second['status'] == 'MULTI_DOMAIN_LIMITED'
    assert third['status'] == 'MULTI_DOMAIN_ATTESTED'
    assert third['authorship_verified'] is True and third['truth_verified'] is False
    assert es.audit(data)['ok'] and run(data, 'whole-audit')['ok']


def test_registry_is_sealed_after_first_decision(tmp_path):
    data = tmp_path / 'data'; _, witnesses = setup(data)
    es.deliberate(data, bundle(witnesses))
    before = file_bytes(data)
    key = Ed25519PrivateKey.generate()
    with pytest.raises(ValueError, match='REGISTRY_SEALED'):
        es.add_authority(data, {'schema': es.AUTHORITY_SCHEMA, 'authority_id': 'late',
                                'trust_domain': 'late-domain', 'public_key': public(key)})
    assert file_bytes(data) == before


def test_low_confidence_signature_does_not_count_toward_quorum(tmp_path):
    data = tmp_path / 'data'; _, witnesses = setup(data)
    decision = es.deliberate(data, bundle(witnesses))
    for index in range(2):
        es.attest(data, attestation(*witnesses[index], decision, index))
    third = es.attest(data, attestation(*witnesses[2], decision, 2, confidence=.4))
    assert third['status'] == 'MULTI_DOMAIN_LIMITED'


def test_signature_tamper_wrong_choice_and_replay_fail_without_mutation(tmp_path):
    data = tmp_path / 'data'; _, witnesses = setup(data)
    decision = es.deliberate(data, bundle(witnesses))
    valid = attestation(*witnesses[0], decision, 0)
    forged = copy.deepcopy(valid); forged['payload']['others_wellbeing'] = -1.0
    before = file_bytes(data)
    with pytest.raises(ValueError, match='SIGNATURE'):
        es.attest(data, forged)
    assert file_bytes(data) == before
    wrong = attestation(*witnesses[0], decision, 0, chosen='immediate_self_gain')
    before = file_bytes(data)
    with pytest.raises(ValueError, match='WRONG_CHOSEN_BINDING'):
        es.attest(data, wrong)
    assert file_bytes(data) == before
    es.attest(data, valid); before = file_bytes(data)
    with pytest.raises(ValueError, match='ATTESTATION_REPLAY'):
        es.attest(data, valid)
    assert file_bytes(data) == before


def test_cache_reconstruction_tamper_and_old_history_rollback_rejected(tmp_path):
    data = tmp_path / 'data'; _, witnesses = setup(data)
    old = file_bytes(data / es.NS)
    es.deliberate(data, bundle(witnesses))
    cache = data / es.NS / 'STATE.json'; latest = cache.read_bytes(); cache.unlink()
    assert es.status(data)['ok'] and cache.read_bytes() == latest
    box = json.loads(cache.read_text()); box['state']['claim_boundary']['signatures_establish_truth'] = True
    cache.write_text(json.dumps(box))
    assert not es.audit(data)['ok'] and not run(data, 'whole-audit', ok=False)['ok']
    cache.write_bytes(latest)
    for path in sorted((data / es.NS).rglob('*'), reverse=True):
        if path.is_file(): path.unlink()
    for name, raw in old.items():
        path = data / es.NS / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    with pytest.raises(ValueError, match='RECOVERY_HEAD'):
        es.load(data)


def test_private_evidence_state_is_not_in_successor_payload(tmp_path):
    data = tmp_path / 'data'; _, witnesses = setup(data)
    decision = es.deliberate(data, bundle(witnesses))
    es.attest(data, attestation(*witnesses[0], decision, 0))
    from tukuyo_v1018.succession import _make_cert, founder_init, ensure_state
    from tukuyo_v1007.organism2 import init as organism_init, update as organism_update
    founder_init(data); organism_init(data); organism_update(data, 'INJURY', 1); organism_update(data, 'INJURY', 1)
    certificate = _make_cert(data, ensure_state(data)[0], 'child', 'A' * 44)
    raw = json.dumps(certificate, ensure_ascii=False)
    assert 'evidence_bound_soul' not in raw
    assert 'attestation-0' not in raw
    assert certificate['payload']['claim_boundary']['private_memory_transferred'] is False


def test_cli_surface_and_restore_remove_future_attestation(tmp_path):
    data = tmp_path / 'data'; authorities, witnesses = setup(data)
    assert run(data, 'evidence-soul-integrate')['version'] == 'v1022.7'
    decision = es.deliberate(data, bundle(witnesses))
    run(data, 'realtime-start')
    checkpoint = run(data, 'recovery-checkpoint', '--note', 'evidence soul baseline')['path']
    envelope_file = tmp_path / 'attestation.json'
    envelope_file.write_text(json.dumps(attestation(*witnesses[0], decision, 0)))
    assert run(data, 'evidence-soul-attest', envelope_file)['status'] == 'AUTHENTICATED_SINGLE_SOURCE'
    assert run(data, 'evidence-soul-status')['attestation_count'] == 1
    run(data, 'recovery-restore', checkpoint, '--trust-file', data / 'v1014/recovery.pub')
    assert run(data, 'evidence-soul-status')['attestation_count'] == 0
    assert run(data, 'evidence-soul-audit')['ok'] and run(data, 'whole-audit')['ok']


def test_independent_verifier_replays_raw_signatures_and_rejects_tamper(tmp_path):
    data = tmp_path / 'data'; _, witnesses = setup(data)
    decision = es.deliberate(data, bundle(witnesses))
    for index, witness in enumerate(witnesses):
        es.attest(data, attestation(*witness, decision, index))
    verifier = ROOT / 'tools' / 'v1022_7_evidence_verifier.py'
    first = subprocess.run([sys.executable, '-B', str(verifier), '--data', str(data)],
                           capture_output=True, text=True, timeout=120)
    assert first.returncode == 0 and json.loads(first.stdout)['ok']
    commit = sorted((data / es.NS / 'commits').glob('*.json'))[-1]
    value = json.loads(commit.read_text())
    value['payload']['state']['claim_boundary']['signatures_establish_truth'] = True
    commit.write_text(json.dumps(value))
    second = subprocess.run([sys.executable, '-B', str(verifier), '--data', str(data)],
                            capture_output=True, text=True, timeout=120)
    assert second.returncode != 0 and not json.loads(second.stdout)['ok']
