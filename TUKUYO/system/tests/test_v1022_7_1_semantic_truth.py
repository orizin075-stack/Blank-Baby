"""V1022.7.1 bounded semantic truth challenges and explicit proof limits."""
from __future__ import annotations

import base64
import copy
import json
import subprocess
import sys

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from test_v1022_5_fusion import ROOT, run
from test_v1022_7_evidence_bound_soul import envelope, file_bytes, public, setup
from tukuyo_v977.whole_state import canon, sha_obj
from tukuyo_v1022 import evidence_bound_soul as es
from tukuyo_v1022 import semantic_truth as st


CONTEXT = sha_obj({'route': 'walk', 'speed_kmh': 6, 'duration_minutes': 150})


def manifest(expected=15, unit='km'):
    return {
        'schema': st.MANIFEST_SCHEMA,
        'benchmark_id': 'mixed-duration-v1',
        'scope_id': 'bounded-word-problem',
        'entries': [{
            'subject': 'walker-1', 'predicate': 'distance-travelled',
            'context_sha256': CONTEXT, 'value_type': 'number',
            'unit': unit, 'expected_value': expected,
        }],
    }


def claim(value=12, unit='km', claim_id='claim-1'):
    return {
        'schema': st.CLAIM_SCHEMA, 'claim_id': claim_id,
        'scope_id': 'bounded-word-problem', 'subject': 'walker-1',
        'predicate': 'distance-travelled', 'context_sha256': CONTEXT,
        'value_type': 'number', 'unit': unit, 'comparator': 'equal',
        'tolerance': 0, 'asserted_value': value,
    }


def report(observer_id, key, index, typed_claim, nonce='nonce-001', value=12, unit='km'):
    payload = {
        'schema': st.REPORT_SCHEMA, 'report_id': f'report-{index}',
        'observer_id': observer_id, 'claim_sha256': sha_obj(typed_claim),
        'challenge_nonce': nonce, 'observed_value': value,
        'value_type': typed_claim['value_type'], 'unit': unit,
        'evidence_sha256': sha_obj({'report-evidence': index, 'nonce': nonce}),
        'method_sha256': sha_obj({'method': f'reporter-{index}'}),
    }
    return envelope(key, payload)


def report_bundle(witnesses, typed_claim=None, nonce='nonce-001', values=None, unit='km'):
    typed_claim = typed_claim or claim()
    values = values or [typed_claim['asserted_value']] * 3
    return {
        'schema': st.REPORT_BUNDLE_SCHEMA, 'challenge_nonce': nonce,
        'claim': copy.deepcopy(typed_claim),
        'reports': [report(observer_id, key, index, typed_claim, nonce, values[index], unit)
                    for index, (observer_id, key) in enumerate(witnesses)],
    }


def receipt(oracle_key, oracle, report_row, benchmark, value=None, receipt_id='receipt-1'):
    entry = benchmark['entries'][0]
    payload = {
        'schema': st.RECEIPT_SCHEMA, 'receipt_id': receipt_id,
        'oracle_id': oracle['oracle_id'], 'report_sha256': report_row['report_sha256'],
        'claim_sha256': report_row['claim_sha256'],
        'challenge_nonce': report_row['challenge_nonce'],
        'benchmark_manifest_sha256': sha_obj(benchmark),
        'entry_sha256': sha_obj(entry),
        'expected_value': entry['expected_value'] if value is None else value,
        'value_type': entry['value_type'], 'unit': entry['unit'],
    }
    return envelope(oracle_key, payload)


def prepare(root, expected=15):
    _, witnesses = setup(root)
    benchmark = manifest(expected)
    oracle_key = Ed25519PrivateKey.generate()
    oracle = {
        'schema': st.ORACLE_SCHEMA, 'oracle_id': 'oracle-bounded-1',
        'scope_id': benchmark['scope_id'], 'public_key': public(oracle_key),
        'adapter_sha256': sha_obj({'adapter': 'independent-lookup-v1'}),
        'method_sha256': sha_obj({'method': 'exact-context-key'}),
        'benchmark_manifest_sha256': sha_obj(benchmark),
    }
    st.add_oracle(root, oracle)
    return witnesses, benchmark, oracle, oracle_key


def challenge_bundle(root, oracle, oracle_key, benchmark, report_sha, **kwargs):
    state = st.load(root)
    row = next(item for item in state['reports'] if item['report_sha256'] == report_sha)
    return {
        'schema': st.CHALLENGE_BUNDLE_SCHEMA, 'report_sha256': report_sha,
        'benchmark_manifest': copy.deepcopy(benchmark),
        'oracle_receipt': receipt(oracle_key, oracle, row, benchmark, **kwargs),
    }


def test_false_three_domain_consensus_is_not_called_truth(tmp_path):
    data = tmp_path / 'data'; witnesses, _, _, _ = prepare(data)
    result = st.submit_reports(data, report_bundle(witnesses, claim(12)))
    assert result['report_consensus'] == 'CLAIM_SUPPORTED'
    assert result['status'] == 'CONFIGURED_CONSENSUS_ONLY'
    assert result['truth_verified'] is False
    assert result['claim_boundary']['report_consensus_establishes_truth'] is False


def test_precommitted_benchmark_refutes_unanimous_false_report(tmp_path):
    data = tmp_path / 'data'; witnesses, benchmark, oracle, oracle_key = prepare(data)
    report_result = st.submit_reports(data, report_bundle(witnesses, claim(12)))
    result = st.challenge(data, challenge_bundle(data, oracle, oracle_key, benchmark,
                                                  report_result['report_sha256']))
    assert result['status'] == 'BOUNDED_BENCHMARK_REFUTED'
    assert result['expected_value'] == 15 and result['asserted_value'] == 12
    assert result['reports_conflict_with_benchmark'] is True
    assert result['bounded_manifest_consistency_verified'] is True
    assert result['external_truth_verified'] is False


def test_correct_claim_is_bounded_benchmark_verified(tmp_path):
    data = tmp_path / 'data'; witnesses, benchmark, oracle, oracle_key = prepare(data)
    report_result = st.submit_reports(data, report_bundle(witnesses, claim(15), values=[15, 15, 15]))
    result = st.challenge(data, challenge_bundle(data, oracle, oracle_key, benchmark,
                                                  report_result['report_sha256']))
    assert result['status'] == 'BOUNDED_BENCHMARK_VERIFIED'
    assert result['reports_conflict_with_benchmark'] is False
    assert st.audit(data)['ok'] and run(data, 'whole-audit')['ok']


def test_oracle_cannot_rewrite_precommitted_manifest(tmp_path):
    data = tmp_path / 'data'; witnesses, benchmark, oracle, oracle_key = prepare(data)
    result = st.submit_reports(data, report_bundle(witnesses, claim(12)))
    altered = manifest(12)
    state = st.load(data); row = state['reports'][0]
    bundle = {'schema': st.CHALLENGE_BUNDLE_SCHEMA, 'report_sha256': result['report_sha256'],
              'benchmark_manifest': altered,
              'oracle_receipt': receipt(oracle_key, oracle, row, altered)}
    before = file_bytes(data)
    with pytest.raises(ValueError, match='MANIFEST_NOT_PRECOMMITTED'):
        st.challenge(data, bundle)
    assert file_bytes(data) == before


def test_receipt_value_must_equal_manifest_replay(tmp_path):
    data = tmp_path / 'data'; witnesses, benchmark, oracle, oracle_key = prepare(data)
    result = st.submit_reports(data, report_bundle(witnesses, claim(12)))
    bundle = challenge_bundle(data, oracle, oracle_key, benchmark, result['report_sha256'], value=12)
    before = file_bytes(data)
    with pytest.raises(ValueError, match='RECEIPT_MANIFEST_MISMATCH'):
        st.challenge(data, bundle)
    assert file_bytes(data) == before


def test_forged_oracle_signature_fails_without_mutation(tmp_path):
    data = tmp_path / 'data'; witnesses, benchmark, oracle, oracle_key = prepare(data)
    result = st.submit_reports(data, report_bundle(witnesses, claim(12)))
    bundle = challenge_bundle(data, oracle, oracle_key, benchmark, result['report_sha256'])
    bundle['oracle_receipt']['payload']['expected_value'] = 12
    before = file_bytes(data)
    with pytest.raises(ValueError, match='SIGNATURE'):
        st.challenge(data, bundle)
    assert file_bytes(data) == before


def test_unit_mismatch_is_rejected_before_consensus(tmp_path):
    data = tmp_path / 'data'; witnesses, _, _, _ = prepare(data)
    typed_claim = claim(12, unit='km')
    before = file_bytes(data)
    with pytest.raises(ValueError, match='REPORT_UNIT_OR_TYPE'):
        st.submit_reports(data, report_bundle(witnesses, typed_claim, unit='m'))
    assert file_bytes(data) == before


def test_ambiguous_untyped_natural_language_is_not_accepted(tmp_path):
    data = tmp_path / 'data'; witnesses, _, _, _ = prepare(data)
    malformed = {'schema': st.CLAIM_SCHEMA, 'claim_id': 'ambiguous',
                 'text': 'たぶん二時間半くらい歩いた'}
    before = file_bytes(data)
    with pytest.raises(ValueError, match='CLAIM_FIELDS'):
        st.submit_reports(data, {'schema': st.REPORT_BUNDLE_SCHEMA,
                                 'challenge_nonce': 'ambiguous-nonce',
                                 'claim': malformed, 'reports': []})
    assert file_bytes(data) == before


def test_nonce_report_and_challenge_replay_are_rejected(tmp_path):
    data = tmp_path / 'data'; witnesses, benchmark, oracle, oracle_key = prepare(data)
    rb = report_bundle(witnesses, claim(12))
    result = st.submit_reports(data, rb)
    before = file_bytes(data)
    with pytest.raises(ValueError, match='CLAIM_REPLAY|NONCE_REPLAY'):
        st.submit_reports(data, rb)
    assert file_bytes(data) == before
    cb = challenge_bundle(data, oracle, oracle_key, benchmark, result['report_sha256'])
    st.challenge(data, cb); before = file_bytes(data)
    with pytest.raises(ValueError, match='CHALLENGE_REPLAY'):
        st.challenge(data, cb)
    assert file_bytes(data) == before


def test_oracle_registry_sealed_after_first_report(tmp_path):
    data = tmp_path / 'data'; witnesses, _, _, _ = prepare(data)
    st.submit_reports(data, report_bundle(witnesses, claim(12)))
    key = Ed25519PrivateKey.generate(); before = file_bytes(data)
    with pytest.raises(ValueError, match='ORACLE_REGISTRY_SEALED'):
        st.add_oracle(data, {'schema': st.ORACLE_SCHEMA, 'oracle_id': 'late',
                             'scope_id': 'late', 'public_key': public(key),
                             'adapter_sha256': sha_obj({'late': 1}),
                             'method_sha256': sha_obj({'late': 2}),
                             'benchmark_manifest_sha256': sha_obj({'late': 3})})
    assert file_bytes(data) == before


def test_oracle_key_cannot_reuse_witness_role(tmp_path):
    data = tmp_path / 'data'; _, witnesses = setup(data)
    witness_key = witnesses[0][1]
    benchmark = manifest(); before = file_bytes(data)
    with pytest.raises(ValueError, match='CROSS_ROLE_KEY_REUSE'):
        st.add_oracle(data, {'schema': st.ORACLE_SCHEMA, 'oracle_id': 'role-reuse',
                             'scope_id': benchmark['scope_id'], 'public_key': public(witness_key),
                             'adapter_sha256': sha_obj({'adapter': 1}),
                             'method_sha256': sha_obj({'method': 1}),
                             'benchmark_manifest_sha256': sha_obj(benchmark)})
    assert file_bytes(data) == before


def test_cache_rebuild_tamper_and_old_history_rollback_rejected(tmp_path):
    data = tmp_path / 'data'; witnesses, _, _, _ = prepare(data)
    old = file_bytes(data / st.NS)
    st.submit_reports(data, report_bundle(witnesses, claim(12)))
    cache = data / st.NS / 'STATE.json'; latest = cache.read_bytes(); cache.unlink()
    assert st.status(data)['ok'] and cache.read_bytes() == latest
    box = json.loads(cache.read_text()); box['state']['claim_boundary']['report_consensus_establishes_truth'] = True
    cache.write_text(json.dumps(box)); assert not st.audit(data)['ok']
    assert not run(data, 'whole-audit', ok=False)['ok']
    cache.write_bytes(latest)
    for path in sorted((data / st.NS).rglob('*'), reverse=True):
        if path.is_file(): path.unlink()
    for name, raw in old.items():
        path = data / st.NS / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    with pytest.raises(ValueError, match='RECOVERY_HEAD'):
        st.load(data)


def test_private_truth_state_is_not_in_successor_payload(tmp_path):
    data = tmp_path / 'data'; witnesses, _, _, _ = prepare(data)
    st.submit_reports(data, report_bundle(witnesses, claim(12)))
    from tukuyo_v1018.succession import _make_cert, founder_init, ensure_state
    from tukuyo_v1007.organism2 import init as organism_init, update as organism_update
    founder_init(data); organism_init(data); organism_update(data, 'INJURY', 1); organism_update(data, 'INJURY', 1)
    certificate = _make_cert(data, ensure_state(data)[0], 'child', 'A' * 44)
    raw = json.dumps(certificate, ensure_ascii=False)
    assert 'semantic_truth' not in raw and 'report-0' not in raw
    assert certificate['payload']['claim_boundary']['private_memory_transferred'] is False


def test_cli_restore_removes_future_truth_challenge(tmp_path):
    data = tmp_path / 'data'; witnesses, benchmark, oracle, oracle_key = prepare(data)
    report_result = st.submit_reports(data, report_bundle(witnesses, claim(12)))
    run(data, 'realtime-start')
    checkpoint = run(data, 'recovery-checkpoint', '--note', 'truth baseline')['path']
    cb = challenge_bundle(data, oracle, oracle_key, benchmark, report_result['report_sha256'])
    bundle_file = tmp_path / 'challenge.json'; bundle_file.write_text(json.dumps(cb))
    assert run(data, 'semantic-truth-challenge', bundle_file)['status'] == 'BOUNDED_BENCHMARK_REFUTED'
    assert run(data, 'semantic-truth-status')['challenge_count'] == 1
    run(data, 'recovery-restore', checkpoint, '--trust-file', data / 'v1014/recovery.pub')
    assert run(data, 'semantic-truth-status')['challenge_count'] == 0
    assert run(data, 'semantic-truth-audit')['ok'] and run(data, 'whole-audit')['ok']


def test_independent_verifier_replays_truth_derivation_and_rejects_tamper(tmp_path):
    data = tmp_path / 'data'; witnesses, benchmark, oracle, oracle_key = prepare(data)
    report_result = st.submit_reports(data, report_bundle(witnesses, claim(12)))
    st.challenge(data, challenge_bundle(data, oracle, oracle_key, benchmark,
                                        report_result['report_sha256']))
    verifier = ROOT / 'tools' / 'v1022_7_1_truth_verifier.py'
    first = subprocess.run([sys.executable, '-B', str(verifier), '--data', str(data)],
                           capture_output=True, text=True, timeout=120)
    assert first.returncode == 0, first.stdout + first.stderr
    assert json.loads(first.stdout)['ok']
    commit = sorted((data / st.NS / 'commits').glob('*.json'))[-1]
    value = json.loads(commit.read_text())
    value['payload']['state']['challenges'][0]['expected_value'] = 12
    commit.write_text(json.dumps(value))
    second = subprocess.run([sys.executable, '-B', str(verifier), '--data', str(data)],
                            capture_output=True, text=True, timeout=120)
    assert second.returncode != 0 and not json.loads(second.stdout)['ok']
