"""v1022.7.9 / 8.2: restoring a checkpoint taken after a restore, the canon with recovery checkpoints, the ecology's
bounds and environment, and energy given between runtimes (relations)."""
import hashlib
import json
import shutil

import pytest

from test_v1022_7_8_canon import _cli, Q
from tukuyo_v1007 import organism2


def _checkpoint(C, d, note):
    r = C(d, 'recovery-checkpoint', '--note', note)
    assert r.get('path'), r
    return r['path']


def test_a_checkpoint_taken_after_a_restore_restores_and_lives_on(tmp_path):
    # before: its restore receipt made every command after the second restore fail (RESTORE_FRONTIER_BYTE_DRIFT)
    C = _cli(); d = tmp_path / 'd'
    assert C(d, 'init', '--individual-id', 'RESTORE-TWICE')['ok'] and C(d, 'organism2-init')['ok']
    C(d, 'realtime-start', '--target-seconds', '3600'); C(d, 'realtime-tick')
    first = _checkpoint(C, d, 'first')
    C(d, 'g4-solve', '--llm', 'off', '--', Q)
    assert C(d, 'recovery-restore', first).get('restored')
    after = _checkpoint(C, d, 'after a restore')
    C(d, 'organism2-update', 'REST', '--amount', '0.1')
    assert C(d, 'recovery-restore', after).get('restored')
    assert C(d, 'whole-audit')['ok']
    assert C(d, 'g4-solve', '--llm', 'off', '--', Q)['answer'] == '7'
    assert C(d, 'recovery-checkpoint', '--note', 'and again').get('path')


def test_with_a_canon_a_restored_copy_waits_for_the_owner_then_lives_on(tmp_path):
    canon = tmp_path / 'canon'; C = _cli(canon); d = tmp_path / 'd'
    assert C(d, 'init', '--individual-id', 'RESTORE-CANON')['ok'] and C(d, 'organism2-init')['ok']
    C(d, 'realtime-start', '--target-seconds', '3600'); C(d, 'realtime-tick')
    cp = _checkpoint(C, d, 'first')
    assert C(d, 'organism2-update', 'REST', '--amount', '0.1')['ok']        # the individual lives on after the checkpoint
    assert C(d, 'recovery-restore', cp).get('restored')
    assert C(d, 'whole-audit')['errors'] == ['CANON_BEHIND']
    assert C(d, 'identity-canon-adopt', '--yes')['adopted']['kind'] == 'restore'
    assert C(d, 'whole-audit')['ok'] and C(d, 'soul-identity-audit')['ok']
    # the cursor is the canon's private note: a recovery checkpoint does not carry it, so a restore cannot drift it
    assert (d / 'canon' / 'private' / 'CURSOR.json').is_file() and not (d / 'canon' / 'CURSOR.json').exists()
    assert C(d, 'g4-solve', '--llm', 'off', '--', Q)['answer'] == '7'
    assert C(d, 'identity-canon-audit')['ok']


def _gift_receipt(i):
    return hashlib.sha256(f'gift-{i}'.encode()).hexdigest()


def test_an_organism_gives_energy_without_an_elapsed_tick(tmp_path):
    C = _cli(); d = tmp_path / 'd'
    assert C(d, 'init', '--individual-id', 'GIFT')['ok'] and C(d, 'organism2-init')['ok']
    before = organism2.load(d)
    r = organism2.resource_gift(d, 1500, _gift_receipt(1))
    assert r['event']['after_energy'] == r['event']['before_energy'] - 1500
    assert r['state'].get('metabolic_age', 0) == before.get('metabolic_age', 0)
    assert organism2.audit(d)['ok']
    with pytest.raises(ValueError, match='RESOURCE_GIFT_WOULD_EMPTY'):
        organism2.resource_gift(d, 5000, _gift_receipt(2))
    box = json.loads(organism2.events_path(d).read_text())
    box['events'][-1]['after_energy'] += 100                       # a gift that kept some of what it gave
    organism2.events_path(d).write_text(json.dumps(box))
    assert not organism2.audit(d)['ok']


def test_ecology_bounds_environment_and_sharing(tmp_path):
    C = _cli(); d = tmp_path / 'eco'
    assert C(d, 'init', '--individual-id', 'ECO-BOUNDS')['ok']
    r = C(d, 'metabolism-init', '--families', '2', '--reservoir', '30000', '--regeneration', '1500', '--max-ticks', '600',
          '--max-runtimes', '16', '--sharing')
    assert r['ok'] and r['bounds'] == {'max_ticks': 600, 'max_runtimes': 16} and r['sharing'] is True
    e = C(d, 'metabolism-environment', '--regeneration', '700')
    assert e['ok'] and e['environment_change'] == {'tick': 0, 'from': 1500, 'regeneration': 700} and e['regeneration'] == 700
    s = C(d, 'metabolism-step', '--ticks', '4')
    assert s['ok'] and s['tick'] == 4 and s['regenerated'] == 4 * 700
    # energy given from one runtime to another: the total of the ecology stays, each lives it with the other's name
    from tukuyo_v1022 import metabolism as m
    from tukuyo_v1019.transaction import transactional
    a, b = s['alive'][0]['runtime'], s['alive'][1]['runtime']

    @transactional()
    def give(data):
        st = m.preflight(data)
        m._give(data, st, a, b, 1000, {'tick': st['tick']}, 'test-gift')
        m._validate(st); m.store.save(data, m.NS, m.COMPONENT, st)
        return st
    st = give(d)
    assert st['relations']['gifts'] == 1 and st['relations']['energy_given'] == 1000
    au = C(d, 'metabolism-audit'); assert au['ok'], au
    soul_b = json.loads((m.child(d, b) / 'v977' / 'SOUL_CORE.json').read_text())
    assert soul_b['attachments'].get('runtime:' + a, 0) > 0
    assert C(d, 'whole-audit')['ok']


def test_an_ecology_made_before_keeps_its_bounds(tmp_path):
    from tukuyo_v1022 import metabolism as m
    old = {'config': {'regeneration': 0, 'max_age': 32, 'learning': True, 'actions': True}}
    assert m.bounds(old) == (512, 64)
    with pytest.raises(ValueError, match='BOUND_CONFIG'):
        m.bounds({'config': {'max_ticks': 99999}})
