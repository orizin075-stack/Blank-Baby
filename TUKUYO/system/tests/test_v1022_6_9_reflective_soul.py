"""v1022.6.9 append-only reflection, perspective conflict and integrity."""
import copy
import json
from pathlib import Path

import pytest

from test_v1022_5_fusion import run
from tukuyo_v1022 import reflective_soul as rs


OPTIONS = [
    {'id': 'immediate_self_gain', 'signals': {'survival': 1.0},
     'themes': [], 'conflicts': [],
     'effects': {'self_wellbeing': .8, 'others_wellbeing': -1,
                 'future_self': -.8, 'truth_consistency': -.8,
                 'bodily_cost': 0, 'uncertainty': 0}},
    {'id': 'responsible_long_term', 'signals': {}, 'themes': [], 'conflicts': [],
     'effects': {'self_wellbeing': -.1, 'others_wellbeing': .9,
                 'future_self': .9, 'truth_consistency': .9,
                 'bodily_cost': .1, 'uncertainty': 0}},
]


def outcome(evidence='outcome-001', confidence=.9, kind='direct_observation', observer='observer-A'):
    return {'evidence_id': evidence, 'observer_id': observer, 'source_kind': kind,
            'self_wellbeing': .2, 'others_wellbeing': .9, 'future_self': .8,
            'truth_consistency': .9, 'bodily_cost': .1, 'surprise': .4,
            'confidence': confidence, 'note': 'bounded observed result'}


def file_bytes(root):
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in root.rglob('*') if p.is_file()}


def init(root, ident='SOUL69'):
    run(root, 'init', '--individual-id', ident)


def test_integrates_five_perspectives_without_ontological_claim(tmp_path):
    d = tmp_path / 'd'; init(d)
    r = rs.integrate(d)
    assert set(r['profile']['perspective_weights']) == {
        'self_wellbeing', 'others_wellbeing', 'future_self',
        'truth_consistency', 'bodily_cost'}
    assert r['profile']['canonical_history_rewritten'] is False
    assert r['workspace']['finite_capacity'] is True
    assert r['claim_boundary']['literal_soul_established'] is False
    assert r['claim_boundary']['consciousness_established'] is False
    assert rs.audit(d)['ok'] and run(d, 'whole-audit')['ok']


def test_reflective_layer_changes_actual_heart_choice(tmp_path):
    d = tmp_path / 'd'; init(d)
    r = rs.deliberate(d, OPTIONS, 'self other future conflict')
    assert r['counterfactual_heart_only'] == 'immediate_self_gain'
    assert r['counterfactual_without_reflective_layer'] == 'immediate_self_gain'
    assert r['chosen'] == 'responsible_long_term'
    assert r['perspective_conflict_count'] == 2
    from tukuyo_v978.heart_loop import status
    assert status(d)['last_action']['chosen'] == 'responsible_long_term'
    assert rs.audit(d)['counterfactual_certificates_valid']


def test_conflict_and_uncertainty_raise_threshold_and_withhold(tmp_path):
    d = tmp_path / 'd'; init(d)
    options = copy.deepcopy(OPTIONS)
    for option in options:
        option['effects']['uncertainty'] = .1
    r = rs.deliberate(d, options, 'uncertain moral conflict')
    assert r['best_candidate'] == 'responsible_long_term'
    assert r['review_threshold'] > .15
    assert r['chosen'] is None and r['review_required']
    from tukuyo_v978.heart_loop import status
    assert status(d)['last_action'] is None


def test_reflection_is_append_only_and_recalibrates_gradually(tmp_path):
    d = tmp_path / 'd'; init(d)
    decision = rs.deliberate(d, OPTIONS)['decision_sha256']
    before = copy.deepcopy(rs.load(d)['decisions'][0])
    old_weight = rs.load(d)['profile']['perspective_weights']['others_wellbeing']
    r = rs.reflect(d, decision, outcome())
    state = rs.load(d)
    assert state['decisions'][0] == before
    assert state['reflections'][0]['canonical_decision_rewritten'] is False
    assert r['canonical_decision_rewritten'] is False
    assert state['profile']['perspective_weights']['others_wellbeing'] > old_weight
    assert state['profile']['canonical_history_rewritten'] is False
    assert rs.audit(d)['ok'] and run(d, 'whole-audit')['ok']


def test_low_confidence_reappraisal_remains_provisional(tmp_path):
    d = tmp_path / 'd'; init(d)
    decision = rs.deliberate(d, OPTIONS)['decision_sha256']
    r = rs.reflect(d, decision, outcome(confidence=.4, kind='self_report'))
    assert r['reappraisal_status'] == 'PROVISIONAL_UNAUTHENTICATED'
    assert r['claim_boundary']['outcome_annotations_independently_verified'] is False


def test_corroboration_requires_distinct_observers(tmp_path):
    d = tmp_path / 'd'; init(d)
    d1 = rs.deliberate(d, OPTIONS)['decision_sha256']
    assert rs.reflect(d, d1, outcome())['reappraisal_status'] == 'SINGLE_ID_CLAIM_UNAUTHENTICATED'
    d2 = rs.deliberate(d, OPTIONS)['decision_sha256']
    assert rs.reflect(d, d2, outcome('outcome-002', observer='observer-B'))['reappraisal_status'] == 'MULTI_ID_CLAIM_UNAUTHENTICATED'
    state = rs.load(d)
    assert state['profile']['distinct_observers'] == 2
    assert state['profile']['per_observer_reliability_cap'] == 2.0


def test_outcome_requires_acted_decision_and_unique_evidence(tmp_path):
    d = tmp_path / 'd'; init(d)
    uncertain = copy.deepcopy(OPTIONS)
    for option in uncertain: option['effects']['uncertainty'] = .1
    no_action = rs.deliberate(d, uncertain)['decision_sha256']
    with pytest.raises(ValueError, match='UNACTED_DECISION'):
        rs.reflect(d, no_action, outcome())
    acted = rs.deliberate(d, OPTIONS)['decision_sha256']
    rs.reflect(d, acted, outcome())
    before = file_bytes(d)
    with pytest.raises(ValueError, match='EVIDENCE_REPLAY'):
        rs.reflect(d, acted, outcome())
    assert file_bytes(d) == before


def test_option_and_outcome_ranges_fail_before_mutation(tmp_path):
    d = tmp_path / 'd'; init(d); before = file_bytes(d)
    bad = copy.deepcopy(OPTIONS); bad[0]['effects']['uncertainty'] = 2
    with pytest.raises(ValueError, match='UNCERTAINTY_RANGE'):
        rs.deliberate(d, bad)
    assert file_bytes(d) == before
    decision = rs.deliberate(d, OPTIONS)['decision_sha256']; before = file_bytes(d)
    bad_outcome = outcome(); bad_outcome['confidence'] = 3
    with pytest.raises(ValueError, match='CONFIDENCE_RANGE'):
        rs.reflect(d, decision, bad_outcome)
    assert file_bytes(d) == before


def test_cache_reconstruction_tamper_and_coherent_rollback(tmp_path):
    d = tmp_path / 'd'; init(d)
    rs.integrate(d); old = file_bytes(d / rs.NS)
    rs.deliberate(d, OPTIONS)
    cache = d / rs.NS / 'STATE.json'; latest = cache.read_bytes(); cache.unlink()
    assert rs.status(d)['ok'] and cache.read_bytes() == latest
    box = json.loads(cache.read_text()); box['state']['profile']['homeostatic_urgency'] = .9
    cache.write_text(json.dumps(box))
    assert not rs.audit(d)['ok'] and not run(d, 'whole-audit', ok=False)['ok']
    cache.write_bytes(latest)
    for p in sorted((d / rs.NS).rglob('*'), reverse=True):
        if p.is_file(): p.unlink()
    for name, raw in old.items():
        p = d / rs.NS / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(raw)
    with pytest.raises(ValueError, match='RECOVERY_HEAD'):
        rs.load(d)


def test_reflection_certificate_tamper_is_rejected(tmp_path):
    d = tmp_path / 'd'; init(d)
    decision = rs.deliberate(d, OPTIONS)['decision_sha256']
    rs.reflect(d, decision, outcome())
    commit = sorted((d / rs.NS / 'commits').glob('*.json'))[-1]
    env = json.loads(commit.read_text())
    env['payload']['state']['reflections'][0]['outcome']['others_wellbeing'] = -1
    commit.write_text(json.dumps(env))
    assert not rs.audit(d)['ok']


def test_dead_individual_cannot_decide_or_reappraise(tmp_path):
    d = tmp_path / 'd'; init(d)
    decision = rs.deliberate(d, OPTIONS)['decision_sha256']
    run(d, 'organism2-init'); run(d, 'organism2-update', 'INJURY', '--amount', '1')
    run(d, 'organism2-update', 'INJURY', '--amount', '1')
    with pytest.raises(ValueError, match='ENTITY_DEAD'): rs.deliberate(d, OPTIONS)
    with pytest.raises(ValueError, match='ENTITY_DEAD'): rs.reflect(d, decision, outcome())
    assert rs.audit(d)['ok']


def test_reflective_private_state_is_not_in_successor_payload(tmp_path):
    d = tmp_path / 'd'; init(d)
    decision = rs.deliberate(d, OPTIONS)['decision_sha256']
    rs.reflect(d, decision, outcome(evidence='PRIVATE_REFLECTIVE_MARKER_69'))
    from tukuyo_v1018.succession import _make_cert, founder_init, ensure_state
    from tukuyo_v1007.organism2 import init as oi, update as ou
    founder_init(d); oi(d); ou(d, 'INJURY', 1); ou(d, 'INJURY', 1)
    cert = _make_cert(d, ensure_state(d)[0], 'child', 'A' * 44)
    raw = json.dumps(cert, ensure_ascii=False)
    assert 'PRIVATE_REFLECTIVE_MARKER_69' not in raw
    assert 'reflective_soul' not in raw
    assert cert['payload']['claim_boundary']['private_memory_transferred'] is False


def test_cli_and_restore_remove_future_reflection(tmp_path):
    d = tmp_path / 'd'; init(d, 'SOUL69-RESTORE'); run(d, 'realtime-start')
    assert run(d, 'reflective-soul-integrate')['version'] == 'v1022.6.9'
    options_file = tmp_path / 'options.json'; options_file.write_text(json.dumps(OPTIONS))
    decision = run(d, 'reflective-soul-deliberate', options_file)['decision_sha256']
    cp = run(d, 'recovery-checkpoint', '--note', 'reflective baseline')['path']
    outcome_file = tmp_path / 'outcome.json'; outcome_file.write_text(json.dumps(outcome()))
    assert run(d, 'reflective-soul-outcome', decision, outcome_file)['canonical_decision_rewritten'] is False
    assert run(d, 'reflective-soul-status')['reflection_count'] == 1
    run(d, 'recovery-restore', cp, '--trust-file', d / 'v1014/recovery.pub')
    assert run(d, 'reflective-soul-status')['reflection_count'] == 0
    assert run(d, 'reflective-soul-audit')['ok'] and run(d, 'whole-audit')['ok']
