"""v1022.8.1 goals formed from its own record, acting on its choices, and revised by what comes of them."""
from __future__ import annotations

import json
import shutil

from test_v1022_5_fusion import run
from tukuyo_v1022 import goals as g

WORK = [{'id': 'with_peer', 'relation': 'peer-x', 'themes': ['shared-work'], 'signals': {'relationship': .5, 'survival': .2}},
        {'id': 'alone', 'themes': ['solo-work'], 'signals': {'survival': .3, 'integrity': .2}}]


def ev(seq, kind, valence, importance=.8, theme='', relation=''):
    return {'seq': seq, 'kind': kind, 'valence': valence, 'importance': importance, 'theme': theme, 'relation': relation}


def test_rules_form_guard_rebuild_and_rely_from_the_record():
    harm = [ev(i, 'betrayal', -.9, relation='p') for i in (1, 2)]
    assert set(g.form(harm)) == {'guard_against:p'}
    assert g.form(harm[:1]) == {}                                      # one harm is not yet a pattern
    helped = harm + [ev(i, 'support', .9, relation='p') for i in (3, 4)]
    guarded = g.form(harm)
    assert set(g.form(helped, guarded)) == {'rebuild_trust:p'}         # it had guarded: the trust is being rebuilt
    assert set(g.form(helped)) == set()                                # with no past guard, a mixed record forms nothing
    more = helped + [ev(i, 'support', .9, relation='p') for i in (5, 6, 7)]
    assert set(g.form(more, {'rebuild_trust:p': {}})) == {'rely_on:p'}
    assert set(g.form([ev(1, 'support', .8, relation='q'), ev(2, 'support', .8, relation='q')])) == {'rely_on:q'}


def test_rules_pursue_and_give_up_a_theme_and_keep_a_vow():
    found = [ev(1, 'discovery', .8, theme='stars'), ev(2, 'discovery', .9, theme='stars')]
    assert set(g.form(found)) == {'pursue:stars'}
    failed = found + [ev(3, 'action_feedback', -.6, theme='stars'), ev(4, 'action_feedback', -.7, theme='stars')]
    assert set(g.form(failed, g.form(found))) == {'give_up:stars'}
    assert 'keep_vow:truth' in g.form([ev(1, 'vow', 1.0, .9, theme='truth')])


def test_goal_terms_touch_only_the_options_they_name():
    goals = {'guard_against:peer-x': {'kind': 'guard_against', 'target': 'peer-x', 'strength': .8},
             'pursue:solo-work': {'kind': 'pursue', 'target': 'solo-work', 'strength': .5}}
    adj, why = g.adjustments(goals, WORK)
    assert adj['with_peer'] < 0 < adj['alone'] and why['with_peer'] == ['guard_against:peer-x']
    big = {f'guard_against:peer-x{i}': {'kind': 'guard_against', 'target': 'peer-x', 'strength': 1.0} for i in range(9)}
    assert g.adjustments(big, WORK)[0]['with_peer'] == -1.5           # bounded like any heart adjustment


def test_two_copies_form_different_goals_act_differently_and_revise(tmp_path):
    start = tmp_path / 'start'; run(start, 'init', '--individual-id', 'GOALS-TEST')
    a, b = tmp_path / 'a', tmp_path / 'b'; shutil.copytree(start, a); shutil.copytree(start, b)
    for _ in range(3):
        run(a, 'soul-experience', 'betrayal', '-0.9', '.8', '--relation', 'peer-x', '--theme', 'shared-work')
        run(b, 'soul-experience', 'support', '.8', '.7', '--relation', 'peer-x', '--theme', 'shared-work')
    fa, fb = run(a, 'goal-form'), run(b, 'goal-form')
    assert [x['goal'] for x in fa['goals']] == ['guard_against:peer-x'] and [x['goal'] for x in fb['goals']] == ['rely_on:peer-x']
    assert fa['changes'][0]['reasons'] == [1, 2] and fa['goals'][0]['reasons'] == [1, 2, 3]   # formed at the second; held since
    opts = tmp_path / 'work.json'; opts.write_text(json.dumps(WORK))
    ca, cb = run(a, 'goal-choose', opts), run(b, 'goal-choose', opts)
    assert (ca['chosen'], cb['chosen']) == ('alone', 'with_peer') and cb['goals_that_touched_it'] == ['rely_on:peer-x']
    o = run(b, 'goal-outcome', '-0.9')
    assert o['took_in']['kind'] == 'betrayal' and o['took_in']['relation'] == 'peer-x'
    assert {'change': 'dropped', 'goal': 'rely_on:peer-x'}.items() <= o['changes'][0].items()
    assert run(b, 'goal-choose', opts)['chosen'] == 'alone'
    for x in (a, b):
        assert run(x, 'goal-audit')['ok'] and run(x, 'whole-audit')['ok']


def test_an_outcome_needs_a_choice_and_never_says_observed(tmp_path):
    d = tmp_path / 'd'; run(d, 'init', '--individual-id', 'GOALS-OUTCOME')
    assert 'GOAL_OUTCOME_WITHOUT_CHOICE' in run(d, 'goal-outcome', '0.5', ok=False)['error']
    opts = tmp_path / 'work.json'; opts.write_text(json.dumps(WORK)); run(d, 'goal-choose', opts)
    assert 'EXPERIENCE_ORIGIN_NOT_YOURS_TO_SAY' in run(d, 'goal-outcome', '0.5', '--origin', 'observed', ok=False)['error']


def test_a_ledger_changed_by_hand_fails_its_audit(tmp_path):
    d = tmp_path / 'd'; run(d, 'init', '--individual-id', 'GOALS-AUDIT')
    for _ in range(2):
        run(d, 'soul-experience', 'betrayal', '-0.9', '.8', '--relation', 'peer-x')
    run(d, 'goal-form')
    s = g._load(d); s['goals'] = {'rely_on:peer-x': {'kind': 'rely_on', 'target': 'peer-x', 'strength': 1.0, 'reasons': [1]}}
    from tukuyo_v1022 import store
    from tukuyo_v977 import whole_state as whole
    store.save(d, g.NS, g.COMPONENT, s); whole.sync(d)                 # even signed with its own key
    assert run(d, 'goal-audit', ok=False)['errors'] == ['GOALS_NOT_FROM_ITS_RECORD']
    assert not run(d, 'whole-audit', ok=False)['ok']
