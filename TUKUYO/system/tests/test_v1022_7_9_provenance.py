"""v1022.7.9 where an experience came from: only an outcome of its own grounded sensors, checked again, is an
experience confirmed from outside; a told, simulated, self-signed, reused or forged one never becomes one."""
from __future__ import annotations

import base64
import json

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from test_v1022_5_fusion import run
from test_v1022_7_evidence_bound_soul import envelope, public
from test_v1022_7_2_grounded_sensor import observation, outcome_receipt, setup
from tukuyo_common.journal import load_events
from tukuyo_v977 import whole_state as whole
from tukuyo_v977.whole_state import sha_obj
from tukuyo_v1022 import grounded_sensor as gs
from tukuyo_v1022 import provenance as pv


def _outcome(root, verifier, key, success=True, receipt_id='outcome-1'):
    row = gs.load(root)['observations'][-1]
    bundle = {'schema': gs.OUTCOME_BUNDLE_SCHEMA, 'observation_sha256': row['observation_sha256'],
              'runtime_id': 'R000000', 'action_id': 'move-sample', 'action_context_sha256': sha_obj({'action': 'move'}),
              'receipt': outcome_receipt(verifier, key, row, success, 0, receipt_id=receipt_id)}
    gs.apply_outcome(root, bundle)
    return gs.load(root)['outcomes'][-1]['outcome_sha256']


def _observed(root, success=True):
    devices, verifier, key = setup(root)
    gs.observe(root, observation(devices))
    return _outcome(root, verifier, key, success)


def _origins(root):
    return [e.get('origin') for e in load_events(whole.event_path(root))]


def test_a_caller_says_told_simulated_or_self_report_but_never_observed_or_checked(tmp_path):
    d = tmp_path / 'd'; run(d, 'init', '--individual-id', 'PROVENANCE-CLI')
    run(d, 'soul-experience', 'discovery', '1', '.8', '--theme', 'x')
    run(d, 'soul-experience', 'betrayal', '-1', '.9', '--theme', 'y', '--relation', 'peer', '--origin', 'simulated')
    run(d, 'heart-experience', 'support', '.5', '.5', '--origin', 'self_report')
    before = load_events(whole.event_path(d))
    for origin in ('observed', 'checked', 'real'):
        r = run(d, 'soul-experience', 'discovery', '1', '.8', '--origin', origin, ok=False)
        assert not r['ok'] and 'EXPERIENCE_ORIGIN_NOT_YOURS_TO_SAY' in r['error']
        r = run(d, 'heart-experience', 'discovery', '1', '.8', '--origin', origin, ok=False)
        assert not r['ok'] and 'EXPERIENCE_ORIGIN_NOT_YOURS_TO_SAY' in r['error']
    assert load_events(whole.event_path(d)) == before
    assert _origins(d)[-3:] == ['told', 'simulated', 'self_report']
    st = run(d, 'experience-provenance-status')
    assert st['externally_confirmed'] == 0 and st['origins'] == {'told': 1, 'simulated': 1, 'self_report': 1}
    assert run(d, 'experience-provenance-audit')['ok'] and run(d, 'whole-audit')['ok']


def test_an_outcome_of_its_own_sensors_is_confirmed_once(tmp_path):
    d = tmp_path / 'd'; outcome = _observed(d)
    r = run(d, 'experience-observed', outcome)
    assert r['origin'] == 'observed' and r['externally_confirmed']
    ev = r['soul_event']
    assert (ev['kind'], ev['valence'], ev['theme'], ev['origin']) == ('observation', .6, 'observed:mass', 'observed')
    a = run(d, 'experience-provenance-audit')
    assert a['ok'] and a['externally_confirmed'] == 1 and a['origins']['observed'] == 1
    assert run(d, 'whole-audit')['ok']
    again = run(d, 'experience-observed', outcome, ok=False)
    assert 'EXPERIENCE_EVIDENCE_REUSED' in again['error']
    assert run(d, 'experience-provenance-audit')['externally_confirmed'] == 1


def test_a_refuted_outcome_is_observed_too_and_hurts(tmp_path):
    d = tmp_path / 'd'; outcome = _observed(d, success=False)
    r = run(d, 'experience-observed', outcome, '--importance', '.7')
    assert r['soul_event']['valence'] == -.6 and r['evidence']['success'] is False
    assert run(d, 'experience-provenance-audit')['externally_confirmed'] == 1


@pytest.mark.parametrize('fake', ['0' * 64, 'f' * 64, 'not-a-sha'])
def test_an_unknown_outcome_confirms_nothing(tmp_path, fake):
    d = tmp_path / 'd'; _observed(d)
    r = run(d, 'experience-observed', fake, ok=False)
    assert not r['ok'] and 'EXPERIENCE_EVIDENCE_UNKNOWN' in r['error']
    assert run(d, 'experience-provenance-audit')['externally_confirmed'] == 0


def test_an_outcome_of_another_individual_confirms_nothing(tmp_path):
    a = tmp_path / 'a'; b = tmp_path / 'b'
    outcome_b = _observed(b); _observed(a)
    r = run(a, 'experience-observed', outcome_b, ok=False)
    assert 'EXPERIENCE_EVIDENCE_UNKNOWN' in r['error']


def test_its_own_key_is_never_an_outside_witness(tmp_path):
    d = tmp_path / 'd'; devices, _verifier, _key = setup(d)
    own_sk = Ed25519PrivateKey.from_private_bytes(base64.b64decode(whole._key_paths(d)[0].read_text().strip()))
    own_verifier = {'schema': gs.VERIFIER_SCHEMA, 'verifier_id': 'its-own-key', 'verification_domain': 'self',
                    'public_key': public(own_sk), 'method_sha256': sha_obj({'method': 'it says so'})}
    gs.add_verifier(d, own_verifier)
    gs.observe(d, observation(devices))
    outcome = _outcome(d, own_verifier, own_sk)          # the sensor record takes the receipt: it is well signed
    r = run(d, 'experience-observed', outcome, ok=False)
    assert 'EXPERIENCE_EVIDENCE_SELF_SIGNED' in r['error']
    assert run(d, 'experience-provenance-audit')['externally_confirmed'] == 0


def test_a_written_in_observed_experience_is_caught(tmp_path):
    d = tmp_path / 'd'; outcome = _observed(d)
    good, why = pv._evidence(d, gs.load(d), outcome)
    assert why is None
    # a forged evidence, and a real evidence under made-up content (a betrayal instead of the observation)
    whole.experience(d, 'observation', .6, .5, 'observed:mass', '', 3, origin='observed', evidence={**good, 'outcome_sha256': 'e' * 64})
    whole.experience(d, 'betrayal', -1.0, 1.0, 'observed:mass', 'peer', 3, origin='observed', evidence=good)
    a = pv.audit(d)
    assert not a['ok'] and a['externally_confirmed'] == 0
    assert any(x.startswith('EXPERIENCE_OBSERVED_UNPROVEN') for x in a['errors'])
    assert any(x.startswith('EXPERIENCE_NOT_FROM_ITS_EVIDENCE') for x in a['errors'])
    whole.sync(d)
    assert not run(d, 'whole-audit', ok=False)['ok']


def test_an_origin_label_edited_in_the_journal_breaks_the_chain(tmp_path):
    d = tmp_path / 'd'; run(d, 'init', '--individual-id', 'PROVENANCE-EDIT')
    run(d, 'soul-experience', 'discovery', '1', '.8', '--origin', 'simulated')
    p = whole.event_path(d); lines = p.read_text().splitlines()
    e = json.loads(lines[-1]); e['origin'] = 'observed'; lines[-1] = json.dumps(e, sort_keys=True, separators=(',', ':'))
    p.write_text('\n'.join(lines) + '\n')
    a = pv.audit(d)
    assert not a['ok'] and a['externally_confirmed'] == 0     # an observed label without its evidence
    assert not run(d, 'whole-audit', ok=False)['ok']


def test_the_paths_say_where_it_came_from(tmp_path):
    d = tmp_path / 'd'; run(d, 'init', '--individual-id', 'PROVENANCE-PATHS')
    run(d, 'g4-solve', '--llm', 'off', '--', 'Tom has 3 apples. He buys 4 more apples. How many apples does he have now?')
    from tukuyo_v978.heart_loop import process_experience
    process_experience(d, 'learning', .2, .2, 'teacher-dialogue', 'teacher-x', origin='teacher')
    o = _origins(d)
    assert 'teacher' in o and set(o) <= {None, 'checked', 'teacher', 'told', 'simulated', 'self_report', 'observed'}
    assert pv.audit(d)['ok']


def test_three_signed_self_reports_are_authored_never_observed(tmp_path):
    from test_v1022_7_evidence_bound_soul import setup as soul_setup
    from test_v1022_7_7_experiential_soul import decide, outcome
    from tukuyo_v1022 import evidence_bound_soul as es
    d = tmp_path / 'd'; _, w = soul_setup(d)
    mine = decide(d, w, 0); seen = decide(d, w, 1)
    for i, witness in enumerate(w):
        es.attest(d, outcome(witness, mine, 0, i, source_kind='self_report'))
        es.attest(d, outcome(witness, seen, 1, i))
    st = es.status(d)
    assert st['decision_statuses'][mine['decision_sha256']] == 'MULTI_DOMAIN_ATTESTED'      # who signed: unchanged
    assert st['decision_observation_statuses'][mine['decision_sha256']] == 'SELF_REPORTED_ONLY'
    assert st['decision_observation_statuses'][seen['decision_sha256']] == 'MULTI_DOMAIN_OBSERVED'
