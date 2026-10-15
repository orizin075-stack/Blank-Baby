"""Append-only reflective self model layered over v1022.6.8 Functional Soul.

The layer keeps canonical events and prior decisions immutable.  Later outcome
reports create signed reappraisal records instead of rewriting the past.  It
separates self, other, future-self, truth, and bodily consequences and raises
the abstention threshold when these perspectives conflict.

This is a bounded functional model.  It does not establish consciousness,
qualia, personhood, or a literal/metaphysical soul.  Option and outcome
annotations are caller supplied and are not independent semantic evidence.
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

from tukuyo_v977 import whole_state as whole
from tukuyo_v977.whole_state import _live_identity, load_soul, sha_obj
from tukuyo_v978 import heart_loop as heart
from tukuyo_v1019.lifecycle import require_alive
from tukuyo_v1019.transaction import transactional
from . import soul_integrity as base_soul
from . import store


NS = 'reflective_soul'
COMPONENT = 'whole_reflective_soul'
SCHEMA = 'tukuyo.v1022_6_9.reflective_soul/1'
WORKSPACE_SCHEMA = 'tukuyo.v1022_6_9.reflective_workspace/1'
ZERO = '0' * 64
EFFECTS = ('self_wellbeing', 'others_wellbeing', 'future_self',
           'truth_consistency', 'bodily_cost', 'uncertainty')
OUTCOMES = ('self_wellbeing', 'others_wellbeing', 'future_self',
            'truth_consistency', 'bodily_cost', 'surprise', 'confidence')


def _bounded_text(value, label, limit=160):
    if (not isinstance(value, str) or not value or len(value) > limit
            or re.search(r'[\x00-\x1f]', value)):
        raise ValueError('REFLECTIVE_SOUL_' + label)
    return value


def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def needs_preflight(data):
    if (Path(data) / NS).exists():
        return True
    p = whole.state_path(data)
    if not p.is_file():
        return False
    try:
        return COMPONENT in _read(p).get('payload', {}).get('component_hashes', {})
    except Exception:
        return True


def _hash_row(row, field):
    q = copy.deepcopy(row)
    q.pop(field, None)
    return sha_obj(q)


def _number(value, label, low=-1.0, high=1.0):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError('REFLECTIVE_SOUL_' + label)
    value = float(value)
    if not low <= value <= high:
        raise ValueError('REFLECTIVE_SOUL_' + label + '_RANGE')
    return round(value, 6)


def _core_option(option):
    if not isinstance(option, dict) or set(option) - {
            'id', 'signals', 'themes', 'conflicts', 'effects'}:
        raise ValueError('REFLECTIVE_SOUL_OPTION_FIELDS')
    core = base_soul._validate_option({
        'id': option.get('id'), 'signals': option.get('signals', {}),
        'themes': option.get('themes', []), 'conflicts': option.get('conflicts', []),
    })
    effects = option.get('effects', {})
    if not isinstance(effects, dict) or set(effects) - set(EFFECTS):
        raise ValueError('REFLECTIVE_SOUL_EFFECTS')
    normalized = {}
    for key, value in effects.items():
        if key in ('bodily_cost', 'uncertainty'):
            normalized[key] = _number(value, key.upper(), 0.0, 1.0)
        else:
            normalized[key] = _number(value, key.upper())
    return {**core, 'effects': normalized}


def _normal_outcome(outcome):
    if not isinstance(outcome, dict) or set(outcome) != {
            'evidence_id', 'observer_id', 'source_kind', 'self_wellbeing', 'others_wellbeing',
            'future_self', 'truth_consistency', 'bodily_cost', 'surprise',
            'confidence', 'note'}:
        raise ValueError('REFLECTIVE_SOUL_OUTCOME_FIELDS')
    kind = outcome['source_kind']
    if kind not in ('direct_observation', 'external_report', 'self_report'):
        raise ValueError('REFLECTIVE_SOUL_SOURCE_KIND')
    result = {
        'evidence_id': _bounded_text(outcome['evidence_id'], 'EVIDENCE_ID', 96),
        'observer_id': _bounded_text(outcome['observer_id'], 'OBSERVER_ID', 96),
        'source_kind': kind,
    }
    for key in OUTCOMES:
        if key in ('bodily_cost', 'surprise', 'confidence'):
            result[key] = _number(outcome[key], key.upper(), 0.0, 1.0)
        else:
            result[key] = _number(outcome[key], key.upper())
    note = outcome.get('note', '')
    if not isinstance(note, str) or len(note) > 512 or re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', note):
        raise ValueError('REFLECTIVE_SOUL_NOTE')
    result['note'] = note
    return result


def _sources(data):
    functional = base_soul.load(data)
    hp = Path(data) / 'v983' / 'HOMEOSTASIS_STATE.json'
    home = _read(hp) if hp.is_file() else None
    return functional, home, {
        'functional_soul_sha256': sha_obj(functional),
        'homeostasis_sha256': sha_obj(home) if home else ZERO,
        'soul_core_sha256': sha_obj(load_soul(data)),
    }


def _profile(functional, home, reflections):
    facets = functional['facets']
    weights = {
        'self_wellbeing': .18 + .22 * float(facets['autobiographical']['salience']),
        'others_wellbeing': .18 + .28 * float(facets['relational']['salience']),
        'future_self': .18 + .28 * float(facets['continuity']['salience']),
        'truth_consistency': .18 + .30 * float(facets['epistemic']['salience']),
        'bodily_cost': .18 + .30 * float(facets['embodied_regulation']['salience']),
    }
    needs = (home or {}).get('needs', {})
    urgency = max([float(v) for v in needs.values()] + [0.0])
    weights['bodily_cost'] += .25 * urgency
    aggregates = {k: {'weighted_sum': 0.0, 'weight': 0.0, 'evidence_count': 0}
                  for k in weights}
    reliability_map = {'direct_observation': 1.0, 'external_report': .65, 'self_report': .5}
    observer_budgets = {}
    for row in reflections:
        out = row['outcome']
        reliability = float(out['confidence']) * reliability_map[out['source_kind']]
        observer = out['observer_id']
        used = observer_budgets.get(observer, 0.0)
        reliability = min(reliability, max(0.0, 2.0 - used))
        observer_budgets[observer] = used + reliability
        for key in aggregates:
            value = -float(out[key]) if key == 'bodily_cost' else float(out[key])
            aggregates[key]['weighted_sum'] += value * reliability
            aggregates[key]['weight'] += reliability
            aggregates[key]['evidence_count'] += 1
    calibration = {}
    for key, item in aggregates.items():
        mean = item['weighted_sum'] / item['weight'] if item['weight'] else 0.0
        # Reflections calibrate a perspective gradually; they never erase its base.
        weights[key] = max(.1, min(.8, weights[key] * (1.0 + .2 * mean)))
        calibration[key] = {
            'signed_mean': round(mean, 6),
            'evidence_count': item['evidence_count'],
            'effective_weight': round(weights[key], 6),
        }
    return {
        'perspective_weights': {k: round(v, 6) for k, v in weights.items()},
        'outcome_calibration': calibration,
        'homeostatic_urgency': round(urgency, 6),
        'distinct_observers': len(observer_budgets),
        'per_observer_reliability_cap': 2.0,
        'canonical_history_rewritten': False,
    }


def _workspace(functional, profile):
    selected = list(functional['workspace']['selected_facets'])
    return {
        'schema': WORKSPACE_SCHEMA,
        'selected_facets': selected,
        'active_commitments': [c['theme'] for c in functional['commitments']
                               if c['status'] == 'ACTIVE'],
        'perspective_weights': copy.deepcopy(profile['perspective_weights']),
        'homeostatic_urgency': profile['homeostatic_urgency'],
        'finite_capacity': True,
        'workspace_is_not_consciousness_evidence': True,
    }


def validate(state):
    required = {'schema', 'individual_id', 'lineage_id', 'branch_id', 'integration_seq',
                'source', 'profile', 'workspace', 'decisions', 'decision_head_sha256',
                'reflections', 'reflection_head_sha256', 'claim_boundary'}
    if not isinstance(state, dict) or state.get('schema') != SCHEMA or set(state) != required:
        raise ValueError('REFLECTIVE_SOUL_SCHEMA')
    for key in ('individual_id', 'lineage_id', 'branch_id'):
        _bounded_text(state[key], key.upper(), 160)
    if type(state['integration_seq']) is not int or state['integration_seq'] < 1:
        raise ValueError('REFLECTIVE_SOUL_SEQ')
    if set(state['source']) != {'functional_soul_sha256', 'homeostasis_sha256', 'soul_core_sha256'}:
        raise ValueError('REFLECTIVE_SOUL_SOURCE')
    if any(not isinstance(v, str) or not re.fullmatch(r'[0-9a-f]{64}', v)
           for v in state['source'].values()):
        raise ValueError('REFLECTIVE_SOUL_SOURCE_HASH')
    profile = state['profile']
    if not isinstance(profile, dict) or profile.get('canonical_history_rewritten') is not False:
        raise ValueError('REFLECTIVE_SOUL_PROFILE')
    if set(profile.get('perspective_weights', {})) != {
            'self_wellbeing', 'others_wellbeing', 'future_self',
            'truth_consistency', 'bodily_cost'}:
        raise ValueError('REFLECTIVE_SOUL_PROFILE_WEIGHTS')
    if any(not .1 <= float(v) <= .8 for v in profile['perspective_weights'].values()):
        raise ValueError('REFLECTIVE_SOUL_PROFILE_RANGE')
    if type(profile.get('distinct_observers')) is not int or profile['distinct_observers'] < 0 or profile.get('per_observer_reliability_cap') != 2.0:
        raise ValueError('REFLECTIVE_SOUL_OBSERVER_CAP')
    workspace = state['workspace']
    if (not isinstance(workspace, dict) or workspace.get('schema') != WORKSPACE_SCHEMA
            or workspace.get('workspace_is_not_consciousness_evidence') is not True
            or workspace.get('finite_capacity') is not True):
        raise ValueError('REFLECTIVE_SOUL_WORKSPACE')
    previous = ZERO
    decisions = state['decisions']
    if not isinstance(decisions, list) or len(decisions) > 128:
        raise ValueError('REFLECTIVE_SOUL_DECISIONS')
    for seq, row in enumerate(decisions, 1):
        if (row.get('seq') != seq or row.get('previous_decision_sha256') != previous
                or row.get('decision_sha256') != _hash_row(row, 'decision_sha256')):
            raise ValueError('REFLECTIVE_SOUL_DECISION_CHAIN')
        opts = [_core_option(x) for x in row.get('options', [])]
        if opts != row.get('options') or sha_obj(opts) != row.get('options_sha256'):
            raise ValueError('REFLECTIVE_SOUL_OPTIONS')
        ids = [x['id'] for x in opts]
        if len(ids) < 2 or len(ids) != len(set(ids)):
            raise ValueError('REFLECTIVE_SOUL_OPTION_IDS')
        for name in ('heart_base_scores', 'functional_adjustments',
                     'reflective_adjustments', 'full_scores'):
            if set(row.get(name, {})) != set(ids):
                raise ValueError('REFLECTIVE_SOUL_SCORE_FIELDS')
        for oid in ids:
            total = round(float(row['heart_base_scores'][oid])
                          + float(row['functional_adjustments'][oid])
                          + float(row['reflective_adjustments'][oid]), 6)
            if total != float(row['full_scores'][oid]):
                raise ValueError('REFLECTIVE_SOUL_SCORE_REPLAY')
        ranked = sorted(ids, key=lambda x: (float(row['full_scores'][x]), x), reverse=True)
        margin = round(float(row['full_scores'][ranked[0]])
                       - float(row['full_scores'][ranked[1]]), 6)
        review = margin < float(row['review_threshold'])
        if (row.get('best_candidate') != ranked[0] or row.get('score_margin') != margin
                or row.get('review_required') != review
                or row.get('chosen') != (None if review else ranked[0])):
            raise ValueError('REFLECTIVE_SOUL_DECISION_RESULT')
        if 'profile_policy' in row:
            if (row['profile_policy'] != 'EXCLUDE_LEGACY_UNAUTHENTICATED_REAPPRAISALS'
                    or row.get('profile_used', {}).get('distinct_observers') != 0):
                raise ValueError('REFLECTIVE_SOUL_PROFILE_POLICY')
            weights = row['profile_used'].get('perspective_weights', {})
            if (set(weights) != {'self_wellbeing', 'others_wellbeing', 'future_self', 'truth_consistency', 'bodily_cost'}
                    or any(type(v) not in (int, float) or not .1 <= v <= .8 for v in weights.values())):
                raise ValueError('REFLECTIVE_SOUL_POLICY_WEIGHTS')
            for option in opts:
                adjustment, _ = _reflective_adjustment(row['profile_used'], option)
                if row['reflective_adjustments'][option['id']] != adjustment:
                    raise ValueError('REFLECTIVE_SOUL_POLICY_REPLAY')
            if _conflict_metrics(opts) != (row['perspective_conflict_count'], row['mean_declared_uncertainty'], row['review_threshold']):
                raise ValueError('REFLECTIVE_SOUL_POLICY_THRESHOLD')
            counter = max(ids, key=lambda x: (float(row['heart_base_scores'][x]), x))
            without = max(ids, key=lambda x: (float(row['heart_base_scores'][x]) + float(row['functional_adjustments'][x]), x))
            if row['counterfactual_heart_only'] != counter or row['counterfactual_without_reflective_layer'] != without:
                raise ValueError('REFLECTIVE_SOUL_POLICY_COUNTERFACTUAL')
        previous = row['decision_sha256']
    if state['decision_head_sha256'] != previous:
        raise ValueError('REFLECTIVE_SOUL_DECISION_HEAD')
    previous = ZERO
    ids = {r['decision_sha256'] for r in decisions}
    evidence_ids = set()
    reflections = state['reflections']
    if not isinstance(reflections, list) or len(reflections) > 256:
        raise ValueError('REFLECTIVE_SOUL_REFLECTIONS')
    for seq, row in enumerate(reflections, 1):
        if (row.get('seq') != seq or row.get('previous_reflection_sha256') != previous
                or row.get('reflection_sha256') != _hash_row(row, 'reflection_sha256')):
            raise ValueError('REFLECTIVE_SOUL_REFLECTION_CHAIN')
        if row.get('decision_sha256') not in ids:
            raise ValueError('REFLECTIVE_SOUL_REFLECTION_DECISION')
        outcome = _normal_outcome(row.get('outcome'))
        if outcome != row.get('outcome') or outcome['evidence_id'] in evidence_ids:
            raise ValueError('REFLECTIVE_SOUL_REFLECTION_EVIDENCE')
        evidence_ids.add(outcome['evidence_id'])
        if row.get('canonical_decision_rewritten') is not False:
            raise ValueError('REFLECTIVE_SOUL_HISTORY_REWRITE')
        previous = row['reflection_sha256']
    if state['reflection_head_sha256'] != previous:
        raise ValueError('REFLECTIVE_SOUL_REFLECTION_HEAD')
    boundary = state['claim_boundary']
    if (not isinstance(boundary, dict)
            or boundary.get('literal_soul_established') is not False
            or boundary.get('consciousness_established') is not False
            or boundary.get('outcome_annotations_independently_verified') is not False):
        raise ValueError('REFLECTIVE_SOUL_CLAIM_BOUNDARY')


def load(data):
    if not (Path(data) / NS / 'commits').exists():
        if needs_preflight(data):
            raise ValueError('REFLECTIVE_SOUL_HISTORY_MISSING')
        raise ValueError('REFLECTIVE_SOUL_NOT_INITIALIZED')
    return store.load(data, NS, COMPONENT, validate)


@transactional()
def integrate(data):
    require_alive(data)
    base_soul.integrate(data)
    functional, home, sources = _sources(data)
    ident = _live_identity(data)
    try:
        old = load(data)
    except ValueError as exc:
        if str(exc) != 'REFLECTIVE_SOUL_NOT_INITIALIZED':
            raise
        old = None
    decisions = copy.deepcopy(old.get('decisions', [])) if old else []
    reflections = copy.deepcopy(old.get('reflections', [])) if old else []
    profile = _profile(functional, home, reflections)
    state = {
        'schema': SCHEMA,
        'individual_id': ident['individual_id'],
        'lineage_id': ident['lineage_id'],
        'branch_id': ident['branch_id'],
        'integration_seq': int(old.get('integration_seq', 0)) + 1 if old else 1,
        'source': sources,
        'profile': profile,
        'workspace': _workspace(functional, profile),
        'decisions': decisions,
        'decision_head_sha256': old.get('decision_head_sha256', ZERO) if old else ZERO,
        'reflections': reflections,
        'reflection_head_sha256': old.get('reflection_head_sha256', ZERO) if old else ZERO,
        'claim_boundary': {
            'append_only_reappraisal': True,
            'canonical_history_preserved': True,
            'self_other_future_body_views_separated': True,
            'conflict_sensitive_abstention': True,
            'single_observer_reliability_capped': True,
            'corroboration_requires_distinct_observers': True,
            'observer_ids_authenticated': False,
            'observer_independence_established': False,
            'corroboration_established': False,
            'legacy_statuses_are_unauthenticated_claim_levels': True,
            'finite_workspace_model': True,
            'neuroscience_inspiration_not_brain_equivalence': True,
            'cross_cultural_views_are_non_equivalent_design_lenses': True,
            'option_annotations_independently_verified': False,
            'outcome_annotations_independently_verified': False,
            'literal_soul_established': False,
            'consciousness_established': False,
            'personhood_established': False,
        },
    }
    validate(state)
    store.save(data, NS, COMPONENT, state)
    return _public(state)


def _reflective_adjustment(profile, option):
    effects = option['effects']
    weights = profile['perspective_weights']
    parts = {}
    total = 0.0
    for key in ('self_wellbeing', 'others_wellbeing', 'future_self', 'truth_consistency'):
        delta = float(effects.get(key, 0.0)) * float(weights[key])
        if delta:
            parts[key] = round(delta, 6)
            total += delta
    body = -float(effects.get('bodily_cost', 0.0)) * float(weights['bodily_cost'])
    if body:
        parts['bodily_cost'] = round(body, 6)
        total += body
    uncertainty = -float(effects.get('uncertainty', 0.0)) * .15
    if uncertainty:
        parts['uncertainty_penalty'] = round(uncertainty, 6)
        total += uncertainty
    return round(max(-1.5, min(1.5, total)), 6), parts


def _conflict_metrics(options):
    conflicts = 0
    uncertainty = 0.0
    for option in options:
        effects = option['effects']
        self_v = float(effects.get('self_wellbeing', 0.0))
        other_v = float(effects.get('others_wellbeing', 0.0))
        future_v = float(effects.get('future_self', 0.0))
        if self_v * other_v < 0 or self_v * future_v < 0 or other_v * future_v < 0:
            conflicts += 1
        uncertainty += float(effects.get('uncertainty', 0.0))
    mean_uncertainty = uncertainty / len(options)
    threshold = min(.3, .1 + .08 * mean_uncertainty + (.05 if conflicts else 0.0))
    return conflicts, round(mean_uncertainty, 6), round(threshold, 6)


@transactional()
def deliberate(data, options, context='reflective_decision', *, authenticated_only=False):
    require_alive(data)
    if type(authenticated_only) is not bool:
        raise ValueError('REFLECTIVE_SOUL_AUTHENTICATION_POLICY')
    _bounded_text(context, 'CONTEXT', 256)
    normalized = [_core_option(x) for x in options]
    if not 2 <= len(normalized) <= 16 or len({x['id'] for x in normalized}) != len(normalized):
        raise ValueError('REFLECTIVE_SOUL_OPTIONS')
    integrate(data)
    state = load(data)
    functional = base_soul.load(data)
    soul = load_soul(data)
    # Legacy reports remain explicit scenario annotations. Evidence-bound
    # decisions exclude their global calibration and use signed local lessons.
    profile = (_profile(functional, _sources(data)[1], [])
               if authenticated_only else state['profile'])
    heart_state = heart.load(data)
    heart_base = {}
    functional_adjustments = {}
    reflective_adjustments = {}
    adjustment_parts = {}
    heart_options = []
    for option in normalized:
        core = {k: copy.deepcopy(option[k]) for k in ('id', 'signals', 'themes', 'conflicts')}
        heart_options.append(core)
        score, _ = heart._score_option(data, soul, heart_state, core)
        heart_base[option['id']] = score
        functional_adjustments[option['id']], functional_parts = base_soul._adjustment(functional, core)
        reflective_adjustments[option['id']], reflective_parts = _reflective_adjustment(profile, option)
        adjustment_parts[option['id']] = {
            'functional_soul': functional_parts,
            'reflective_soul': reflective_parts,
        }
    combined = {oid: round(float(functional_adjustments[oid])
                           + float(reflective_adjustments[oid]), 6)
                for oid in heart_base}
    proposed = {oid: round(float(heart_base[oid]) + float(combined[oid]), 6)
                for oid in heart_base}
    conflict_count, mean_uncertainty, threshold = _conflict_metrics(normalized)
    ranking = sorted(proposed, key=lambda x: (proposed[x], x), reverse=True)
    best = ranking[0]
    margin = round(proposed[best] - proposed[ranking[1]], 6)
    review = margin < threshold
    if review:
        chosen = None
        full = proposed
    else:
        result = heart.choose(data, heart_options, context, adjustments=combined,
                              adjustment_label='whole_reflective_soul')
        chosen = result['chosen']
        full = {row['id']: float(row['score']) for row in result['scores']}
    row = {
        'seq': len(state['decisions']) + 1,
        'context': context,
        'options': normalized,
        'options_sha256': sha_obj(normalized),
        'heart_base_scores': heart_base,
        'functional_adjustments': functional_adjustments,
        'reflective_adjustments': reflective_adjustments,
        'adjustment_parts': adjustment_parts,
        'full_scores': full,
        'best_candidate': best,
        'score_margin': margin,
        'review_threshold': threshold,
        'review_required': review,
        'chosen': chosen,
        'perspective_conflict_count': conflict_count,
        'mean_declared_uncertainty': mean_uncertainty,
        'counterfactual_heart_only': max(heart_base, key=lambda x: (heart_base[x], x)),
        'counterfactual_without_reflective_layer': max(
            heart_base, key=lambda x: (float(heart_base[x])
                                       + float(functional_adjustments[x]), x)),
        'source': copy.deepcopy(state['source']),
        'previous_decision_sha256': state['decision_head_sha256'],
        'conditional_on_caller_annotations': True,
    }
    if authenticated_only:
        row['profile_policy'] = 'EXCLUDE_LEGACY_UNAUTHENTICATED_REAPPRAISALS'
        row['profile_used'] = copy.deepcopy(profile)
    row['decision_sha256'] = _hash_row(row, 'decision_sha256')
    state['decisions'].append(row)
    state['decision_head_sha256'] = row['decision_sha256']
    validate(state)
    store.save(data, NS, COMPONENT, state)
    return {
        'ok': True, 'version': 'v1022.6.9', 'chosen': chosen,
        'best_candidate': best, 'review_required': review,
        'score_margin': margin, 'review_threshold': threshold,
        'perspective_conflict_count': conflict_count,
        'counterfactual_heart_only': row['counterfactual_heart_only'],
        'counterfactual_without_reflective_layer': row['counterfactual_without_reflective_layer'],
        'decision_sha256': row['decision_sha256'],
        'adjustment_parts': adjustment_parts,
        'claim_boundary': copy.deepcopy(state['claim_boundary']),
        'profile_policy': row.get('profile_policy', 'LEGACY_UNAUTHENTICATED_SCENARIO'),
        'profile_used': copy.deepcopy(profile),
    }


@transactional()
def reflect(data, decision_sha256, outcome):
    require_alive(data)
    if not isinstance(decision_sha256, str) or not re.fullmatch(r'[0-9a-f]{64}', decision_sha256):
        raise ValueError('REFLECTIVE_SOUL_DECISION_SHA')
    normalized = _normal_outcome(outcome)
    integrate(data)
    state = load(data)
    decision = next((row for row in state['decisions']
                     if row['decision_sha256'] == decision_sha256), None)
    if decision is None:
        raise ValueError('REFLECTIVE_SOUL_UNKNOWN_DECISION')
    if decision['chosen'] is None:
        raise ValueError('REFLECTIVE_SOUL_UNACTED_DECISION')
    if normalized['evidence_id'] in {r['outcome']['evidence_id'] for r in state['reflections']}:
        raise ValueError('REFLECTIVE_SOUL_EVIDENCE_REPLAY')
    observers = {r['outcome']['observer_id'] for r in state['reflections']
                 if r['chosen'] == decision['chosen']}
    observers.add(normalized['observer_id'])
    # V1022.7 correction: these IDs and annotations are caller supplied.  Even
    # two different strings do not prove authenticated or independent sources.
    # Keep the legacy learning path, but never label it corroborated evidence.
    reappraisal = ('PROVISIONAL_UNAUTHENTICATED' if normalized['confidence'] < .7 else
                   'MULTI_ID_CLAIM_UNAUTHENTICATED' if len(observers) >= 2
                   else 'SINGLE_ID_CLAIM_UNAUTHENTICATED')
    row = {
        'seq': len(state['reflections']) + 1,
        'decision_sha256': decision_sha256,
        'chosen': decision['chosen'],
        'outcome': normalized,
        'interpretation': {
            'self_other_tension': round(normalized['self_wellbeing']
                                        - normalized['others_wellbeing'], 6),
            'present_future_tension': round(normalized['self_wellbeing']
                                            - normalized['future_self'], 6),
            'prediction_error': normalized['surprise'],
            'reappraisal_status': reappraisal,
            'distinct_observers_for_chosen': len(observers),
        },
        'canonical_decision_rewritten': False,
        'previous_reflection_sha256': state['reflection_head_sha256'],
    }
    row['reflection_sha256'] = _hash_row(row, 'reflection_sha256')
    state['reflections'].append(row)
    state['reflection_head_sha256'] = row['reflection_sha256']
    functional, home, sources = _sources(data)
    state['source'] = sources
    state['profile'] = _profile(functional, home, state['reflections'])
    state['workspace'] = _workspace(functional, state['profile'])
    validate(state)
    store.save(data, NS, COMPONENT, state)
    return {
        'ok': True, 'version': 'v1022.6.9',
        'reflection_sha256': row['reflection_sha256'],
        'reappraisal_status': row['interpretation']['reappraisal_status'],
        'canonical_decision_rewritten': False,
        'profile': copy.deepcopy(state['profile']),
        'claim_boundary': copy.deepcopy(state['claim_boundary']),
    }


def _public(state):
    return {
        'ok': True, 'version': 'v1022.6.9',
        'individual_id': state['individual_id'],
        'integration_seq': state['integration_seq'],
        'decision_count': len(state['decisions']),
        'reflection_count': len(state['reflections']),
        'profile': copy.deepcopy(state['profile']),
        'profile_calibration_status': 'LEGACY_UNAUTHENTICATED_SCENARIO',
        'workspace': copy.deepcopy(state['workspace']),
        'decision_head_sha256': state['decision_head_sha256'],
        'reflection_head_sha256': state['reflection_head_sha256'],
        'claim_boundary': copy.deepcopy(state['claim_boundary']),
    }


def status(data):
    state = load(data)
    result = _public(state)
    result['audit'] = audit(data)
    return result


def audit(data):
    try:
        state = load(data)
        ident = _live_identity(data)
        errors = []
        if any(state.get(k) != ident[k] for k in ('individual_id', 'lineage_id', 'branch_id')):
            errors.append('REFLECTIVE_SOUL_IDENTITY')
        functional, home, sources = _sources(data)
        stale = state['source'] != sources
        expected_profile = _profile(functional, home, state['reflections'])
        if state['profile'] != expected_profile:
            errors.append('REFLECTIVE_SOUL_PROFILE_DERIVATION')
        return {
            'ok': not errors, 'version': 'v1022.6.9', 'errors': errors,
            'stale_sources': stale, 'decision_count': len(state['decisions']),
            'reflection_count': len(state['reflections']),
            'append_only_history_valid': True,
            'counterfactual_certificates_valid': True,
            'literal_soul_established': False,
            'consciousness_established': False,
        }
    except (ValueError, TypeError, KeyError, OSError) as exc:
        return {
            'ok': False, 'version': 'v1022.6.9',
            'errors': [type(exc).__name__ + ':' + str(exc)],
            'literal_soul_established': False,
            'consciousness_established': False,
        }
