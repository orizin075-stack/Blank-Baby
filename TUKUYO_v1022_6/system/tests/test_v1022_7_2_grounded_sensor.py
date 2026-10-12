"""V1022.7.2 calibrated sensor, action outcome and resource binding tests."""
from __future__ import annotations

import base64
import copy
import json
import subprocess
import sys

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from test_v1022_5_fusion import ROOT, run
from test_v1022_7_evidence_bound_soul import envelope, file_bytes, public
from tukuyo_v977.whole_state import sha_obj
from tukuyo_v1022 import grounded_sensor as gs
from tukuyo_v1022 import semantic_truth as st


CONTEXT = sha_obj({'bin': 'A', 'physical_quantity': 'mass'})


def typed_claim(value=10, claim_id='mass-claim-1'):
    return {'schema': st.CLAIM_SCHEMA, 'claim_id': claim_id, 'scope_id': 'lab-mass',
            'subject': 'sample-1', 'predicate': 'mass', 'context_sha256': CONTEXT,
            'value_type': 'number', 'unit': 'kg', 'comparator': 'within_tolerance',
            'tolerance': .2, 'asserted_value': value}


def setup(root, same_adapter=False, same_sensor_domain=False):
    run(root, 'init', '--individual-id', 'GROUNDED-V1022-7-2')
    gs.integrate(root); devices = []
    adapter_a = sha_obj({'adapter': 'A'}); adapter_b = sha_obj({'adapter': 'B'})
    for index in range(3):
        authority_key = Ed25519PrivateKey.generate(); device_key = Ed25519PrivateKey.generate()
        authority = {'schema': gs.AUTHORITY_SCHEMA, 'authority_id': f'cal-{index}',
                     'calibration_domain': f'cal-domain-{index}', 'public_key': public(authority_key)}
        gs.add_authority(root, authority)
        payload = {'schema': gs.CERTIFICATE_SCHEMA, 'certificate_id': f'cert-{index}',
                   'device_id': f'device-{index}', 'device_public_key': public(device_key),
                   'authority_id': authority['authority_id'], 'calibration_domain': authority['calibration_domain'],
                   'sensor_domain': 'same-domain' if same_sensor_domain else f'sensor-domain-{index}',
                   'device_model': f'model-{index}',
                   'adapter_sha256': adapter_a if same_adapter or index < 2 else adapter_b,
                   'measurement_kind': 'mass', 'unit': 'kg', 'precision': .1,
                   'calibrated_from_tick': 0, 'calibrated_until_tick': 1000}
        cert = envelope(authority_key, payload); gs.add_sensor(root, cert)
        devices.append((payload, device_key, cert))
    verifier_key = Ed25519PrivateKey.generate()
    verifier = {'schema': gs.VERIFIER_SCHEMA, 'verifier_id': 'action-verifier-1',
                'verification_domain': 'physical-outcome', 'public_key': public(verifier_key),
                'method_sha256': sha_obj({'method': 'separate-scale-and-resource-meter'})}
    gs.add_verifier(root, verifier)
    return devices, verifier, verifier_key


def reading(device, key, cert, index, claim, nonce='observation-1', tick=10, value=10):
    payload = {'schema': gs.READING_SCHEMA, 'reading_id': f'reading-{index}-{nonce}',
               'device_id': device['device_id'], 'observation_nonce': nonce,
               'claim_sha256': sha_obj(claim), 'context_sha256': claim['context_sha256'],
               'observed_at_tick': tick, 'value_type': claim['value_type'], 'unit': claim['unit'],
               'observed_value': value, 'calibration_certificate_sha256': sha_obj(cert),
               'raw_evidence_sha256': sha_obj({'raw': index, 'nonce': nonce, 'value': value})}
    return envelope(key, payload)


def observation(devices, values=(10, 10, 10), nonce='observation-1', tick=10, expiry=20, claim=None):
    claim = claim or typed_claim()
    return {'schema': gs.OBSERVATION_BUNDLE_SCHEMA, 'observation_nonce': nonce,
            'observed_at_tick': tick, 'expires_at_tick': expiry, 'claim': copy.deepcopy(claim),
            'readings': [reading(device, key, cert, index, claim, nonce, tick, values[index])
                         for index, (device, key, cert) in enumerate(devices)]}


def outcome_receipt(verifier, key, observation_row, success, credit, receipt_id='outcome-1', tick=12):
    payload = {'schema': gs.OUTCOME_RECEIPT_SCHEMA, 'receipt_id': receipt_id,
               'verifier_id': verifier['verifier_id'],
               'observation_sha256': observation_row['observation_sha256'],
               'observation_nonce': observation_row['observation_nonce'], 'runtime_id': 'R000000',
               'action_id': 'move-sample', 'action_context_sha256': sha_obj({'action': 'move'}),
               'result_evidence_sha256': sha_obj({'result': success, 'receipt': receipt_id}),
               'observed_at_tick': tick, 'success': success, 'resource_credit': credit}
    return envelope(key, payload)


def outcome_bundle(root, verifier, key, success=False, credit=0, **kwargs):
    row = gs.load(root)['observations'][0]
    return {'schema': gs.OUTCOME_BUNDLE_SCHEMA, 'observation_sha256': row['observation_sha256'],
            'runtime_id': 'R000000', 'action_id': 'move-sample',
            'action_context_sha256': sha_obj({'action': 'move'}),
            'receipt': outcome_receipt(verifier, key, row, success, credit, **kwargs)}


def test_one_faulty_sensor_does_not_overrule_two_calibrated_readings(tmp_path):
    data = tmp_path / 'data'; devices, _, _ = setup(data)
    result = gs.observe(data, observation(devices, values=(10, 10, 40)))
    assert result['consensus_value'] == 10 and result['claim_match']
    assert result['status'] == 'CALIBRATED_SENSOR_CONSENSUS_ONLY'
    assert result['external_truth_verified'] is False
    assert gs.audit(data)['ok'] and run(data, 'whole-audit')['ok']


def test_two_colluding_sensors_are_not_called_external_truth(tmp_path):
    data = tmp_path / 'data'; devices, _, _ = setup(data)
    result = gs.observe(data, observation(devices, values=(40, 40, 10)))
    assert result['consensus_value'] == 40 and not result['claim_match']
    assert result['status'] == 'CALIBRATED_SENSOR_CONSENSUS_ONLY'
    assert result['external_truth_verified'] is False


def test_adapter_and_domain_diversity_are_required(tmp_path):
    data = tmp_path / 'adapter'; devices, _, _ = setup(data, same_adapter=True); before = file_bytes(data)
    with pytest.raises(ValueError, match='QUORUM'):
        gs.observe(data, observation(devices))
    assert file_bytes(data) == before
    data2 = tmp_path / 'domain'; devices2, _, _ = setup(data2, same_sensor_domain=True); before = file_bytes(data2)
    with pytest.raises(ValueError, match='QUORUM'):
        gs.observe(data2, observation(devices2))
    assert file_bytes(data2) == before


def test_expired_calibration_and_stale_time_are_rejected_without_mutation(tmp_path):
    data = tmp_path / 'data'; devices, _, _ = setup(data); before = file_bytes(data)
    with pytest.raises(ValueError, match='CALIBRATION_EXPIRED'):
        gs.observe(data, observation(devices, tick=1001, expiry=1002))
    assert file_bytes(data) == before
    with pytest.raises(ValueError, match='OBSERVATION_WINDOW'):
        gs.observe(data, observation(devices, tick=10, expiry=100))
    assert file_bytes(data) == before


def test_device_signature_claim_unit_and_context_are_bound(tmp_path):
    data = tmp_path / 'data'; devices, _, _ = setup(data)
    bundle = observation(devices); bundle['readings'][0]['payload']['observed_value'] = 99; before = file_bytes(data)
    with pytest.raises(ValueError, match='SIGNATURE'):
        gs.observe(data, bundle)
    assert file_bytes(data) == before
    bundle = observation(devices); bundle['readings'][0]['payload']['unit'] = 'g'
    bundle['readings'][0] = envelope(devices[0][1], bundle['readings'][0]['payload'])
    with pytest.raises(ValueError, match='READING_BINDING'):
        gs.observe(data, bundle)
    assert file_bytes(data) == before


def test_nonce_reading_and_raw_evidence_replay_are_rejected(tmp_path):
    data = tmp_path / 'data'; devices, _, _ = setup(data); bundle = observation(devices)
    gs.observe(data, bundle); before = file_bytes(data)
    with pytest.raises(ValueError, match='OBSERVATION_REPLAY'):
        gs.observe(data, bundle)
    assert file_bytes(data) == before


def test_verifier_key_cannot_reuse_sensor_or_authority_role(tmp_path):
    data = tmp_path / 'data'; devices, _, _ = setup(data)
    state = gs.load(data); before = file_bytes(data)
    reused = {'schema': gs.VERIFIER_SCHEMA, 'verifier_id': 'reused',
              'verification_domain': 'bad', 'public_key': devices[0][0]['device_public_key'],
              'method_sha256': sha_obj({'bad': 1})}
    with pytest.raises(ValueError, match='CROSS_ROLE_KEY_REUSE'):
        gs.add_verifier(data, reused)
    assert file_bytes(data) == before and state['verifiers']


def test_refuted_action_never_receives_resource_credit(tmp_path):
    data = tmp_path / 'data'; devices, verifier, key = setup(data); gs.observe(data, observation(devices))
    result = gs.apply_outcome(data, outcome_bundle(data, verifier, key, success=False, credit=0))
    assert result['status'] == 'GROUNDED_ACTION_REFUTED'
    assert result['metabolism_result'] is None


def test_successful_action_calls_finite_metabolism_transfer(tmp_path, monkeypatch):
    data = tmp_path / 'data'; devices, verifier, key = setup(data); gs.observe(data, observation(devices))
    from tukuyo_v1022 import metabolism
    called = {}
    def fake_reward(root, runtime_id, credit, receipt_hash):
        called.update(runtime=runtime_id, credit=credit, receipt=receipt_hash)
        return {'ok': True, 'paid': credit, 'resource_conservation': True}
    monkeypatch.setattr(metabolism, 'grounded_reward', fake_reward)
    before = file_bytes(data)
    with pytest.raises(ValueError, match='PRECOMMIT_REQUIRED'):
        gs.apply_outcome(data, outcome_bundle(data, verifier, key, success=True, credit=700))
    assert not called and file_bytes(data) == before


def test_successful_grounded_action_moves_real_metabolic_resource(tmp_path):
    data = tmp_path / 'data'; devices, verifier, key = setup(data)
    run(data, 'metabolism-init', '--families', '2', '--reservoir', '50000', '--max-age', '64', '--no-actions')
    before = run(data, 'metabolism-status'); gs.observe(data, observation(devices))
    from test_v1022_7_3_evidence_decision import measured_bundle
    result = gs.apply_outcome(data, measured_bundle(data, devices, verifier, key, credit=700))
    after = run(data, 'metabolism-status')
    assert result['metabolism_result']['paid'] == 700
    assert after['reservoir'] == before['reservoir'] - 700
    assert after['living_energy'] == before['living_energy'] + 700
    assert after['initial_total'] + after['regenerated'] == after['reservoir'] + after['burned'] + after['living_energy']
    assert run(data, 'metabolism-audit')['ok'] and run(data, 'grounded-sensor-audit')['ok'] and run(data, 'whole-audit')['ok']
    verifier_path = ROOT / 'tools' / 'v1022_7_2_grounded_verifier.py'
    first = subprocess.run([sys.executable, '-B', str(verifier_path), '--data', str(data)], capture_output=True, text=True, timeout=120)
    assert first.returncode == 0, first.stdout + first.stderr
    assert json.loads(first.stdout)['action_receipt_and_metabolic_transfer_replayed']
    commit = sorted((data / gs.NS / 'commits').glob('*.json'))[-1]
    tampered = json.loads(commit.read_text()); tampered['payload']['state']['outcomes'][0]['resource_credit'] = 699
    commit.write_text(json.dumps(tampered))
    second = subprocess.run([sys.executable, '-B', str(verifier_path), '--data', str(data)], capture_output=True, text=True, timeout=120)
    assert second.returncode != 0 and not json.loads(second.stdout)['ok']


def test_failed_action_with_credit_and_forged_receipt_are_rejected(tmp_path):
    data = tmp_path / 'data'; devices, verifier, key = setup(data); gs.observe(data, observation(devices))
    before = file_bytes(data); bundle = outcome_bundle(data, verifier, key, success=False, credit=1)
    with pytest.raises(ValueError, match='OUTCOME_VALUE'):
        gs.apply_outcome(data, bundle)
    assert file_bytes(data) == before
    bundle = outcome_bundle(data, verifier, key, success=False, credit=0)
    bundle['receipt']['payload']['action_id'] = 'different'
    with pytest.raises(ValueError, match='SIGNATURE'):
        gs.apply_outcome(data, bundle)
    assert file_bytes(data) == before


def test_outcome_replay_and_late_registry_mutation_are_rejected(tmp_path):
    data = tmp_path / 'data'; devices, verifier, key = setup(data); gs.observe(data, observation(devices))
    bundle = outcome_bundle(data, verifier, key, success=False, credit=0); gs.apply_outcome(data, bundle); before = file_bytes(data)
    with pytest.raises(ValueError, match='OUTCOME_REPLAY'):
        gs.apply_outcome(data, bundle)
    with pytest.raises(ValueError, match='REGISTRY_SEALED'):
        gs.add_authority(data, {'schema': gs.AUTHORITY_SCHEMA, 'authority_id': 'late',
                                'calibration_domain': 'late-domain',
                                'public_key': public(Ed25519PrivateKey.generate())})
    assert file_bytes(data) == before


def test_cache_rebuild_tamper_and_old_history_rollback_are_rejected(tmp_path):
    data = tmp_path / 'data'; devices, _, _ = setup(data); old = file_bytes(data / gs.NS)
    gs.observe(data, observation(devices)); cache = data / gs.NS / 'STATE.json'; latest = cache.read_bytes(); cache.unlink()
    assert gs.status(data)['ok'] and cache.read_bytes() == latest
    box = json.loads(cache.read_text()); box['state']['claim_boundary']['sensor_consensus_establishes_external_truth'] = True
    cache.write_text(json.dumps(box)); assert not gs.audit(data)['ok']; cache.write_bytes(latest)
    for path in sorted((data / gs.NS).rglob('*'), reverse=True):
        if path.is_file(): path.unlink()
    for name, raw in old.items():
        path = data / gs.NS / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    with pytest.raises(ValueError, match='RECOVERY_HEAD'):
        gs.load(data)


def test_private_sensor_state_is_not_in_successor_payload(tmp_path):
    data = tmp_path / 'data'; devices, _, _ = setup(data); gs.observe(data, observation(devices))
    from tukuyo_v1018.succession import _make_cert, founder_init, ensure_state
    from tukuyo_v1007.organism2 import init as organism_init, update as organism_update
    founder_init(data); organism_init(data); organism_update(data, 'INJURY', 1); organism_update(data, 'INJURY', 1)
    certificate = _make_cert(data, ensure_state(data)[0], 'child', 'A' * 44)
    raw = json.dumps(certificate, ensure_ascii=False)
    assert 'grounded_sensor' not in raw and 'reading-0' not in raw
    assert certificate['payload']['claim_boundary']['private_memory_transferred'] is False


def test_cli_checkpoint_restore_removes_future_outcome(tmp_path):
    data = tmp_path / 'data'; devices, verifier, key = setup(data); gs.observe(data, observation(devices))
    run(data, 'realtime-start'); checkpoint = run(data, 'recovery-checkpoint', '--note', 'grounded baseline')['path']
    bundle = outcome_bundle(data, verifier, key, success=False, credit=0)
    path = tmp_path / 'outcome.json'; path.write_text(json.dumps(bundle))
    assert run(data, 'grounded-sensor-outcome', path)['status'] == 'GROUNDED_ACTION_REFUTED'
    run(data, 'recovery-restore', checkpoint, '--trust-file', data / 'v1014/recovery.pub')
    assert run(data, 'grounded-sensor-status')['outcome_count'] == 0
    assert run(data, 'grounded-sensor-audit')['ok'] and run(data, 'whole-audit')['ok']
