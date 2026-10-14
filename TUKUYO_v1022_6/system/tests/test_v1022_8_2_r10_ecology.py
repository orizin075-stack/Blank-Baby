"""v1022.8.2 round 10: the ecology's new opt-in options. Founders born at different ticks (their seed energy waits in a
nursery), exploring a wild place that only a runtime able to read the clue can use (learning decides), births by living
parents with their own energy (the heritable trait line still passes only through death), and a bequest from an old
runtime to its successor. Every option keeps the energy account: what is in the ecology is what it began with, what
regenerated and what was found, less what was burned."""
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from test_v1022_7_8_canon import _cli, ROOT
from tukuyo_v1022 import metabolism as m


def _eco(tmp_path, name, *flags):
    C = _cli(); d = tmp_path / name
    assert C(d, 'init', '--individual-id', 'ECO-' + name.upper())['ok']
    r = C(d, 'metabolism-init', *map(str, flags))
    assert r['ok'], r
    return C, d, r


def _state(d):
    return m.store.load(d, m.NS, m.COMPONENT, m._validate)


def test_staggered_founders_wait_in_the_nursery_and_join_later(tmp_path):
    C, d, r = _eco(tmp_path, 'stagger', '--families', 3, '--max-age', 8, '--reservoir', 30000, '--regeneration', 2000, '--stagger')
    assert r['active_runtime_count'] == 1 and r['unborn'] == [3, 5] and r['nursery'] == 2 * 6500
    assert r['initial_total'] == 30000 + 3 * 6500
    s = C(d, 'metabolism-step', '--ticks', '5')
    assert s['ok'] and s['unborn'] == [] and s['nursery'] == 0 and s['active_runtime_count'] == 3, s
    assert len({x['family'] for x in s['alive']}) == 3                  # each founder its own family line
    assert C(d, 'metabolism-audit')['ok'] and C(d, 'whole-audit')['ok']
    st = _state(d)
    bad = copy.deepcopy(st); bad['nursery'] += 6500                    # energy that is not in the account
    with pytest.raises(ValueError, match='NURSERY_BINDING|RESOURCE_CONSERVATION'):
        m._validate(bad)
    bad = copy.deepcopy(st); bad['config'].pop('stagger')              # the option and its state go together
    with pytest.raises(ValueError, match='OPTION_BINDING'):
        m._validate(bad)


def test_the_clue_is_read_with_the_public_skills_and_one_word_no_one_was_taught():
    s = {'seed': '0' * 64}
    seen = {}
    for t in range(200):
        q, a = m._clue(s, 'R000000', t)
        assert q.startswith('隠し場所の手がかり：') and a.isdigit()
        seen[next(w for w, _ in m.CLUE_EVENTS if w in q)] = True
    assert set(seen) == {w for w, _ in m.CLUE_EVENTS}                   # every kind of clue comes up


BUILTIN = ('もらいました', '使いました', '食べました')                 # cognition's bounded built-in event words
TAUGHT = ('盗まれました', '補充しました', 'を落として失いました')       # only the public skills teach these


@pytest.mark.parametrize('learning', [True, False])
def test_what_a_runtime_learned_decides_how_well_the_wild_feeds_it(tmp_path, learning):
    # an empty commons that never regenerates: the wild is the only food
    flags = ['--families', 2, '--max-age', 16, '--reservoir', 0, '--regeneration', 0, '--explore',
             '--wild-regeneration', 1000, '--wild-cap', 20000] + ([] if learning else ['--no-learning'])
    C, d, r = _eco(tmp_path, 'explore' + ('' if learning else '_nolearn'), *flags)
    assert r['wild'] == 20000 and r['found'] == 0
    s = C(d, 'metabolism-step', '--ticks', '8')
    assert s['ok'], s
    assert s['explore_attempts'] >= 1 and s['wild'] + s['found'] == _state(d)['wild_grown']
    # every kind of clue, put to one of the runtimes as it is now: it reads the taught words only if it learned them
    from tukuyo_v1022 import cognition
    rid = s['alive'][0]['runtime']
    read = {w for w, sign in m.CLUE_EVENTS
            if cognition.solve(m.child(d, rid), f'隠し場所の手がかり：1袋に9個入りが7袋、ここにあります。3個{w}。ここに残っているのは何個？')['answer']
            == str(63 + 3 * sign)}
    assert read == (set(BUILTIN) | set(TAUGHT) if learning else set(BUILTIN))
    # and in the ecology itself, without learning no taught-word clue was ever answered
    ticks = [json.loads(p.read_text()) for p in sorted((m.root(d) / 'ticks').glob('*.json'))]
    right = [a['question'] for t in ticks for a in t['actions'] if a['action'] == 'explore' and a['correct']]
    if not learning:
        assert all(any(w in q for w in BUILTIN) for q in right)
    assert C(d, 'metabolism-audit')['ok']
    bad = copy.deepcopy(_state(d)); bad['found'] += 100                 # energy found that the wild never had
    with pytest.raises(ValueError, match='WILD_BOUND|RESOURCE_CONSERVATION'):
        m._validate(bad)


def test_a_living_parent_bears_a_child_with_its_own_energy(tmp_path):
    C, d, r = _eco(tmp_path, 'births', '--families', 2, '--max-age', 16, '--reservoir', 80000, '--regeneration', 4000,
                   '--reproduction')
    assert r['claim_boundary']['living_parent_births_without_trait_inheritance'] is True
    assert r['claim_boundary']['living_parent_reproduction'] is False   # the trait line still passes only through death
    s = C(d, 'metabolism-step', '--ticks', '10')
    assert s['ok'] and s['births'], s
    b = s['births'][0]
    assert b['funded_by'] == {'parent': 6500} and b['trait_inheritance'] is False and b['public_learning_commitment']
    alive = {x['runtime']: x for x in s['alive']}
    assert b['child'] in alive and alive[b['child']]['family'] not in {x['family'] for x in r['alive']}
    st = _state(d)
    assert st['runtimes'][b['child']]['generation'] == 0                # a new individual, not the parent's successor
    # the parent gave the child's seed energy: two gifts in its organism events, none from the commons
    ev = json.loads((m.child(d, b['parent']) / 'v1007' / 'ORGANISM2_EVENTS.json').read_text())['events']
    assert sum(e['gift'] for e in ev if e['event'] == 'RESOURCE_GIFT' and e['receipt_sha256'] in b['gift_receipts']) == 6500
    # each holds the other in its soul
    soul = lambda rid: json.loads((m.child(d, rid) / 'v977' / 'SOUL_CORE.json').read_text())
    assert soul(b['child'])['attachments'].get('runtime:' + b['parent'], 0) > 0
    assert soul(b['parent'])['attachments'].get('runtime:' + b['child'], 0) > 0
    au = C(d, 'metabolism-audit'); assert au['ok'], au
    assert C(d, 'whole-audit')['ok']


@pytest.mark.parametrize('bequest', [True, False])
def test_an_old_runtime_leaves_what_it_has_to_its_successor(tmp_path, bequest):
    # the commons is small and does not regenerate: at the founders' deaths it cannot pay for successors
    flags = ['--families', 2, '--max-age', 6, '--reservoir', 9000, '--regeneration', 0] + (['--bequest'] if bequest else [])
    C, d, r = _eco(tmp_path, 'bequest' if bequest else 'no_bequest', *flags)
    s = C(d, 'metabolism-step', '--ticks', '7')
    assert s['ok'], s
    assert len(s['deaths']) >= 2 and all(x['cause'] == 'AGE' for x in s['deaths'][:2])
    if bequest:
        assert s['actual_successions'] >= 1 and s['active_runtime_count'] >= 1, s
        assert all(x['funded_by']['parent_bequest'] > 0 for x in s['successions'])
    else:
        assert s['actual_successions'] == 0 and s['active_runtime_count'] == 0
    assert C(d, 'metabolism-audit')['ok']


def test_an_ecology_made_without_the_options_is_as_before(tmp_path):
    C, d, r = _eco(tmp_path, 'plain', '--families', 2, '--reservoir', 20000, '--regeneration', 1000)
    assert r['claim_boundary'] == m.CLAIMS
    assert not {'stagger', 'unborn', 'nursery', 'births', 'reproduction', 'explore', 'wild', 'found', 'bequest'} & set(r)
    st = _state(d)
    assert not {'unborn', 'nursery', 'births', 'wild', 'found', 'wild_grown'} & set(st)
    bad = C(d, 'metabolism-step', '--ticks', '1'); assert bad['ok']
    r2 = _cli()(tmp_path / 'combo', 'init', '--individual-id', 'ECO-COMBO')
    assert r2['ok']
    r3 = _cli()(tmp_path / 'combo', 'metabolism-init', '--research-world', '--stagger')
    assert not r3['ok'] and 'V1022_OPTION_COMBINATION' in r3['error']


def test_the_long_run_tool_goes_on_after_a_restart(tmp_path):
    anchor = os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if not anchor:
        pytest.skip('needs the runtime trust anchor (the CLI checks the signed distribution)')
    out = tmp_path / 'run.json'
    base = [sys.executable, '-B', str(ROOT / 'tools' / 'ecology_long_run.py'), '--work', str(tmp_path / 'w'), '--runtime-trust-file', anchor,
            '--families', '2', '--max-age', '8', '--reservoir', '20000', '--regeneration', '2000', '--step', '2',
            '--change', '3:1000', '--out', str(out)]
    env = {k: v for k, v in os.environ.items() if not k.startswith('TUKUYO_CRASH')}
    p = subprocess.run(base + ['--ticks', '4'], cwd=ROOT, env=env, capture_output=True, text=True, timeout=600)
    first = json.loads(out.read_text())
    assert first['result']['ticks'] == 4 and first['environment'][0]['regeneration'] == 1000, p.stdout[-500:]
    p = subprocess.run(base + ['--ticks', '6', '--resume'], cwd=ROOT, env=env, capture_output=True, text=True, timeout=600)
    rep = json.loads(out.read_text())
    assert rep['resumed'] and rep['result']['ticks'] == 6 and rep['result']['stopped'] == 'REACHED_TICKS', p.stdout[-500:]
    assert [e['regeneration'] for e in rep['environment']] == [1000]    # the change it made is not made again
    assert rep['config']['changes'] == [[3, 1000]] and rep['audit']['ok']
