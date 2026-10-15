"""Finite, need-driven goals. No environment key, truth table or file access.

Goal *instances* come from the current energy, uncertainties and prediction
errors. The vocabulary and scoring signals remain designed by the developer.
The individual's Heart chooses among the feasible instances, not a tick script.
"""
from __future__ import annotations
import copy
from .agent import ResearchAgent

GOALS = ('secure_energy', 'learn_rule', 'verify_rule', 'repair_prediction', 'rest')
POLICY = 'tukuyo.v1022_8_1.need_driven_goals/1'

def memory():
    return {'active': None, 'switches': 0, 'failures': [], 'revisions': 0,
            'last_reset_seq': 0, 'completed': {g: 0 for g in GOALS}}

def economics(econ, reservoir, energy):
    # A lamp turning on is not income when the finite reservoir is empty.
    return {**econ, 'reward': min(econ['reward'], reservoir,
                                  max(0, econ['cap'] - energy))}

def propose(agent, mem, energy, remaining, reservoir, locked, econ):
    e = economics(econ, reservoir, energy)
    x, p = agent.work_choice(locked)
    ev = p * e['reward'] - e['work'] - e['fail_penalty'] * (1-p)
    need = max(0., (7500-energy)/7500)
    entropy = agent.entropy_bits()
    recent = [r for r in mem['failures'] if r['seq'] > mem['last_reset_seq']]
    pressure = min(1., len(recent)/3)
    rows = [{'id': 'rest', 'signals': {'survival': .25, 'integrity': .1},
             'reason': 'avoid_unprofitable_extra_cost', 'criterion': {'extra_cost': 0}}]
    if energy > econ['base']+e['work']+e['fail_penalty'] and ev > 0:
        rows.append({'id': 'secure_energy',
                     'signals': {'survival': .55 + 4*need,
                                 'curiosity': .05, 'truthfulness': .05},
                     'reason': 'energy_below_reserve' if need else 'profitable_work',
                     'criterion': {'energy_at_least': 7500}})
    can_probe = energy > econ['base']+e['probe'] and remaining > 1 and reservoir > 0
    if can_probe and entropy > .1:
        rows.append({'id': 'learn_rule',
                     'signals': {'curiosity': min(2., entropy/4)+.4,
                                 'survival': .25*need, 'truthfulness': .2},
                     'reason': 'unresolved_predictive_model',
                     'criterion': {'entropy_reduction': .02}})
    if can_probe and (agent.rep is not None or agent.want_replication()):
        rows.append({'id': 'verify_rule',
                     'signals': {'truthfulness': 1.7, 'curiosity': .6,
                                 'survival': -.1*need},
                     'reason': 'candidate_requires_replication',
                     'criterion': {'status': 'CONFIRMED'}})
    if can_probe and recent:
        rows.append({'id': 'repair_prediction',
                     'signals': {'truthfulness': 2.2*pressure, 'curiosity': .8,
                                 'survival': .25},
                     'reason': 'observed_prediction_error',
                     'criterion': {'retest_input': recent[-1]['x']}})
    # Include an alternative even when no experiment or work is feasible.
    if len(rows) == 1:
        rows.append({'id': 'secure_energy', 'signals': {'survival': -.5},
                     'reason': 'no_affordable_profitable_action',
                     'criterion': {'energy_at_least': 7500}})
    return rows

def enact(agent, mem, goal, energy, remaining, reservoir, locked, econ, seq):
    """The selected goal causally controls an action and, if needed, model repair."""
    if goal not in GOALS: raise ValueError('DEVELOPMENT_UNKNOWN_GOAL')
    a = ResearchAgent.from_compact(copy.deepcopy(agent.to_compact()))
    reset = False
    failures = [r for r in mem['failures'] if r['seq'] > mem['last_reset_seq']]
    if goal == 'repair_prediction' and len(failures) >= 3:
        # Retire the predictive model, never erase the individual's signed
        # autobiographical record. Old observations stay in the life journal.
        a = ResearchAgent(invent=agent.invent)
        reset = True
    if goal == 'rest': return a, 'rest', None, reset
    e = economics(econ, reservoir, energy)
    if goal == 'secure_energy':
        x, p = a.work_choice(locked)
        ev = p*e['reward']-e['work']-e['fail_penalty']*(1-p)
        if energy > econ['base']+e['work']+e['fail_penalty'] and ev > 0:
            return a, 'work', x, reset
        return a, 'rest', None, reset
    if energy <= econ['base']+e['probe'] or remaining <= 1 or reservoir <= 0:
        return a, 'rest', None, reset
    if goal == 'verify_rule':
        if a.rep is None and a.want_replication():
            a.start_replication(); a._advance_confirmation()
        if a.rep is not None:
            if a.rep['queue']: return a, 'probe', a.rep['queue'][0], reset
            return a, 'trial', None, reset
    if goal == 'repair_prediction' and failures:
        return a, 'probe', failures[-1]['x'], reset
    return a, 'probe', a.next_experiment(), reset

def advance(mem, row):
    m = copy.deepcopy(mem)
    if m['active'] != row['goal']:
        m['switches'] += int(m['active'] is not None)
        m['active'] = row['goal']
    if row['reset_model']:
        m['revisions'] += 1; m['last_reset_seq'] = row['seq']
    if row['surprise']:
        m['failures'] = (m['failures'] + [{'seq': row['seq'],
                         'x': row['observation']['x']}])[-12:]
    # Resolve a disproved prediction when its targeted retest agrees with the
    # revised predictive model; old evidence is retained in signed episodes.
    if row['goal'] == 'repair_prediction' and not row['surprise'] and not row['reset_model']:
        m['failures'] = [r for r in m['failures'] if r['x'] != row['input']]
    if row['progress']: m['completed'][row['goal']] += 1
    return m

def result_metrics(before, after, goal, observation, credit, prediction):
    entropy_drop = before.entropy_bits()-after.entropy_bits()
    surprise = bool(observation is not None and prediction is not None and
                    abs(float(observation['y'])-prediction) >= .8)
    progress = (credit > 0 if goal == 'secure_energy' else
                after.status == 'CONFIRMED' if goal == 'verify_rule' else
                observation is not None and not surprise if goal == 'repair_prediction' else
                entropy_drop >= .02 if goal == 'learn_rule' else False)
    return {'entropy_drop': round(entropy_drop, 8), 'surprise': surprise,
            'progress': bool(progress)}
