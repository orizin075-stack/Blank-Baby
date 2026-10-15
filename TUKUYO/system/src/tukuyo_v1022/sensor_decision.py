"""Bounded decisions from declared instrument error bounds.

Intervals are calibration declarations, not confidence intervals. No probability
or conformal coverage guarantee is inferred. A disagreement triggers a request
for another observation; exhaustion triggers abstention.
"""
from decimal import Decimal


def assess(observation, sensors, remaining):
    if type(remaining) is not int or not 0 <= remaining <= 2:
        raise ValueError('SENSOR_DECISION_BUDGET')
    claim = observation['claim']
    payloads = [env['payload'] for env in observation['reading_envelopes']]
    intervals = None
    if claim['value_type'] == 'number':
        intervals = []
        for reading in payloads:
            value = Decimal(str(reading['observed_value']))
            error = Decimal(str(sensors[reading['device_id']]['precision']))
            intervals.append((value - error, value + error))
        lower = max(pair[0] for pair in intervals)
        upper = min(pair[1] for pair in intervals)
        asserted = Decimal(str(claim['asserted_value']))
        tolerance = Decimal(str(claim['tolerance'])) if claim['comparator'] == 'within_tolerance' else Decimal(0)
        compatible = lower <= upper
        supported = compatible and asserted - tolerance <= lower <= upper <= asserted + tolerance
        contradicted = compatible and (upper < asserted - tolerance or lower > asserted + tolerance)
        bound = [str(lower), str(upper)] if compatible else None
    else:
        values = [reading['observed_value'] for reading in payloads]
        compatible = all(value == values[0] for value in values)
        supported = compatible and values[0] == claim['asserted_value']
        contradicted = compatible and not supported
        bound = [values[0]] if compatible else None
    if supported:
        decision, reason = 'ACT', 'ALL_DECLARED_ERROR_BOUNDS_SUPPORT_CLAIM'
    elif contradicted:
        decision, reason = 'ABSTAIN', 'MEASUREMENTS_REFUTE_CLAIM'
    else:
        decision = 'ACQUIRE' if remaining else 'ABSTAIN'
        reason = 'CONFLICT_OR_UNRESOLVED_BOUND' if remaining else 'ACQUISITION_BUDGET_EXHAUSTED'
    return {'decision': decision, 'reason': reason, 'remaining_acquisitions': remaining,
            'compatible_bounds': compatible, 'common_bound': bound,
            'claim_supported_for_entire_common_bound': supported,
            'next_observation_request': {'same_typed_claim': True, 'fresh_nonce': True,
                'later_logical_tick': True, 'recheck_calibration_and_device': True} if decision == 'ACQUIRE' else None,
            'statistical_coverage_guaranteed': False, 'external_truth_verified': False}
