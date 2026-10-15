"""Independent action verifier using rational interval arithmetic.

No producer or TUKUYO runtime imports. This checks declarations and recorded
measurements, not the correctness of physical sensors or their operators.
"""
from fractions import Fraction as F


def evidence_class(observation, sensors, remaining):
    claim = observation['claim']; samples = [e['payload'] for e in observation['reading_envelopes']]
    if claim['value_type'] == 'number':
        bounds = [(F(str(p['observed_value'])) - F(str(sensors[p['device_id']]['precision'])),
                   F(str(p['observed_value'])) + F(str(sensors[p['device_id']]['precision']))) for p in samples]
        lo, hi = max(x for x, _ in bounds), min(y for _, y in bounds)
        target = F(str(claim['asserted_value'])); error = F(str(claim['tolerance'])) if claim['comparator'] == 'within_tolerance' else F(0)
        compatible = lo <= hi
        valid = compatible and lo >= target-error and hi <= target+error
        refuted = compatible and (hi < target-error or lo > target+error)
        common = (lo, hi) if compatible else None
    else:
        values = [p['observed_value'] for p in samples]; compatible = len({(type(v).__name__, str(v)) for v in values}) == 1
        valid = compatible and values[0] == claim['asserted_value']; refuted = compatible and not valid
        common = (values[0],) if compatible else None
    decision = 'ACT' if valid else 'ABSTAIN' if refuted or not remaining else 'ACQUIRE'
    reason = ('ALL_DECLARED_ERROR_BOUNDS_SUPPORT_CLAIM' if valid else 'MEASUREMENTS_REFUTE_CLAIM' if refuted
              else 'CONFLICT_OR_UNRESOLVED_BOUND' if remaining else 'ACQUISITION_BUDGET_EXHAUSTED')
    return decision, reason, compatible, common, valid


def replay(state, observations, sensors, metabolism, errors, row_hash):
    decisions = {}; used = set(); children = set(); previous = '0'*64
    for i, row in enumerate(state.get('decisions', []), 1):
        obs = observations[row['observation_sha256']]; parent = row['predecessor_sha256']; remaining = 2
        if parent is not None:
            p = decisions[parent]; old = observations[p['observation_sha256']]
            if parent in children or p['assessment']['decision'] != 'ACQUIRE' or old['claim'] != obs['claim'] or old['observed_at_tick'] >= obs['observed_at_tick']:
                errors.append('DECISION_PARENT')
            remaining = p['assessment']['remaining_acquisitions'] - 1; children.add(parent)
        actual = row['assessment']; decision, reason, compatible, common, valid = evidence_class(obs, sensors, remaining)
        actual_common = actual['common_bound']
        if common is not None and obs['claim']['value_type'] == 'number': actual_common = tuple(F(x) for x in actual_common)
        elif actual_common is not None: actual_common = tuple(actual_common)
        if (remaining < 0 or obs['observation_sha256'] in used or row['seq'] != i
                or actual['decision'] != decision or actual['reason'] != reason or actual['remaining_acquisitions'] != remaining
                or actual['compatible_bounds'] is not compatible or actual_common != common
                or actual['claim_supported_for_entire_common_bound'] is not valid
                or actual['statistical_coverage_guaranteed'] is not False or actual['external_truth_verified'] is not False
                or row['previous_decision_sha256'] != previous or row['decision_sha256'] != row_hash(row, 'decision_sha256')):
            errors.append('DECISION_DERIVATION')
        previous = row['decision_sha256']; decisions[previous] = row; used.add(obs['observation_sha256'])
    if state.get('decision_head_sha256') != previous: errors.append('DECISION_HEAD')
    intents = {}; ids = set(); used = set(); previous = '0'*64
    for i, row in enumerate(state.get('intents', []), 1):
        decision = decisions[row['decision_sha256']]; obs = observations[row['observation_sha256']]
        if (decision['assessment']['decision'] != 'ACT' or decision['observation_sha256'] != obs['observation_sha256']
                or obs['observation_sha256'] in used or row['intent_id'] in ids
                or not obs['observed_at_tick'] <= row['started_at_tick'] < row['deadline_tick'] <= obs['expires_at_tick']
                or not obs['seq'] <= row['observations_at_commit'] <= len(observations)
                or type(row['maximum_credit']) is not int or not 1 <= row['maximum_credit'] <= 1000
                or row['seq'] != i or row['previous_intent_sha256'] != previous or row['intent_sha256'] != row_hash(row, 'intent_sha256')):
            errors.append('INTENT_DERIVATION')
        previous = row['intent_sha256']; intents[previous] = row; ids.add(row['intent_id']); used.add(obs['observation_sha256'])
    if state.get('intent_head_sha256') != previous: errors.append('INTENT_HEAD')
    used = set(); result_ids = set()
    for row in state['outcomes']:
        p = row['receipt_envelope']['payload']
        if p['schema'] != 'tukuyo.v1022_7_3.measured_outcome_receipt/1':
            if p['resource_credit']: errors.append('LEGACY_CREDIT_FORBIDDEN')
            continue
        intent = intents[p['intent_sha256']]; result = observations[p['result_observation_sha256']]
        derived_success = evidence_class(result, sensors, 0)[0] == 'ACT'
        if (p['intent_sha256'] in used or p['result_observation_sha256'] in result_ids
                or p['observation_sha256'] != intent['observation_sha256']
                or any(p[k] != intent[k] for k in ('runtime_id', 'action_id', 'action_context_sha256'))
                or result['seq'] <= intent['observations_at_commit'] or result['claim'] != intent['expected_result']
                or p['result_evidence_sha256'] != result['observation_sha256']
                or not intent['started_at_tick'] < result['observed_at_tick'] <= p['observed_at_tick'] <= intent['deadline_tick']
                or p['success'] is not derived_success or not 0 <= p['resource_credit'] <= intent['maximum_credit']):
            errors.append('MEASURED_OUTCOME_BINDING')
        used.add(p['intent_sha256']); result_ids.add(p['result_observation_sha256'])
    return len(decisions), len(intents)
