"""Precommitted, measured, finite action verification; no physical actuator."""
import copy
from . import sensor_decision

DECISION_SCHEMA = 'tukuyo.v1022_7_3.sensor_decision_request/1'
INTENT_SCHEMA = 'tukuyo.v1022_7_3.action_intent_request/1'
RECEIPT_SCHEMA = 'tukuyo.v1022_7_3.measured_outcome_receipt/1'


def maps(state):
    return ({r['observation_sha256']: r for r in state['observations']},
            {r['sensor']['device_id']: r['sensor'] for r in state['sensors']})


def validate(state):
    from . import grounded_sensor as gs
    observations, sensors = maps(state)
    decisions = {}; seen = set(); children = set(); previous = gs.ZERO
    for i, row in enumerate(state['decisions'], 1):
        if set(row) != {'seq', 'observation_sha256', 'predecessor_sha256', 'assessment',
                        'previous_decision_sha256', 'decision_sha256'}:
            raise ValueError('SENSOR_ACTION_DECISION_FIELDS')
        observation = observations[row['observation_sha256']]
        predecessor = row['predecessor_sha256']
        remaining = 2
        if predecessor is not None:
            parent = decisions.get(predecessor)
            if parent is None or predecessor in children or parent['assessment']['decision'] != 'ACQUIRE':
                raise ValueError('SENSOR_ACTION_ACQUISITION_PARENT')
            old = observations[parent['observation_sha256']]
            if old['claim'] != observation['claim'] or observation['observed_at_tick'] <= old['observed_at_tick']:
                raise ValueError('SENSOR_ACTION_ACQUISITION_BINDING')
            remaining = parent['assessment']['remaining_acquisitions'] - 1
            children.add(predecessor)
        if (row['observation_sha256'] in seen or row['seq'] != i
                or row['assessment'] != sensor_decision.assess(observation, sensors, remaining)
                or row['previous_decision_sha256'] != previous
                or row['decision_sha256'] != gs._row_hash(row, 'decision_sha256')):
            raise ValueError('SENSOR_ACTION_DECISION_DERIVATION')
        decisions[row['decision_sha256']] = row; seen.add(row['observation_sha256']); previous = row['decision_sha256']
    if state['decision_head_sha256'] != previous:
        raise ValueError('SENSOR_ACTION_DECISION_HEAD')
    intents = {}; previous = gs.ZERO; used = set(); identifiers = set()
    for i, row in enumerate(state['intents'], 1):
        required = {'seq', 'intent_id', 'decision_sha256', 'observation_sha256', 'runtime_id',
                    'runtime_head_sha256', 'action_id', 'action_context_sha256', 'expected_result',
                    'maximum_credit', 'started_at_tick', 'deadline_tick', 'observations_at_commit',
                    'previous_intent_sha256', 'intent_sha256'}
        if set(row) != required:
            raise ValueError('SENSOR_ACTION_INTENT_FIELDS')
        decision = decisions.get(row['decision_sha256']); observation = observations.get(row['observation_sha256'])
        if (not decision or not observation or decision['observation_sha256'] != row['observation_sha256']
                or decision['assessment']['decision'] != 'ACT' or row['observation_sha256'] in used
                or row['intent_id'] in identifiers):
            raise ValueError('SENSOR_ACTION_INTENT_DECISION')
        gs._text(row['intent_id'], 'INTENT_ID', 96); gs._text(row['action_id'], 'ACTION_ID', 96)
        import re
        if not re.fullmatch(r'R\d{6}', row['runtime_id']): raise ValueError('SENSOR_ACTION_RUNTIME')
        gs._sha(row['action_context_sha256']); gs._sha(row['runtime_head_sha256'])
        if gs.truth._normal_claim(row['expected_result']) != row['expected_result']:
            raise ValueError('SENSOR_ACTION_EXPECTED_RESULT')
        start = gs._tick(row['started_at_tick'], 'INTENT_START'); end = gs._tick(row['deadline_tick'], 'INTENT_DEADLINE')
        if (not observation['observed_at_tick'] <= start < end <= observation['expires_at_tick']
                or type(row['maximum_credit']) is not int or not 1 <= row['maximum_credit'] <= 1000
                or type(row['observations_at_commit']) is not int
                or not observation['seq'] <= row['observations_at_commit'] <= len(observations)
                or row['seq'] != i or row['previous_intent_sha256'] != previous
                or row['intent_sha256'] != gs._row_hash(row, 'intent_sha256')):
            raise ValueError('SENSOR_ACTION_INTENT_DERIVATION')
        intents[row['intent_sha256']] = row; used.add(row['observation_sha256']); identifiers.add(row['intent_id']); previous = row['intent_sha256']
    if state['intent_head_sha256'] != previous: raise ValueError('SENSOR_ACTION_INTENT_HEAD')
    if len(decisions) > 512 or len(intents) > 128: raise ValueError('SENSOR_ACTION_HISTORY_BOUND')
    return decisions, intents


def authorize(state, payload):
    from . import grounded_sensor as gs
    _, intents = validate(state); observations, sensors = maps(state)
    intent = intents.get(payload.get('intent_sha256'))
    result = observations.get(payload.get('result_observation_sha256'))
    if not intent or not result: raise ValueError('SENSOR_ACTION_INTENT_OR_RESULT_MISSING')
    if (payload['observation_sha256'] != intent['observation_sha256']
            or any(payload[k] != intent[k] for k in ('runtime_id', 'action_id', 'action_context_sha256'))
            or result['seq'] <= intent['observations_at_commit']
            or result['claim'] != intent['expected_result']
            or not intent['started_at_tick'] < result['observed_at_tick'] <= payload['observed_at_tick'] <= intent['deadline_tick']
            or payload['result_evidence_sha256'] != result['observation_sha256']):
        raise ValueError('SENSOR_ACTION_RESULT_BINDING')
    success = sensor_decision.assess(result, sensors, 0)['decision'] == 'ACT'
    if payload['success'] is not success or not 0 <= payload['resource_credit'] <= intent['maximum_credit']:
        raise ValueError('SENSOR_ACTION_RESULT_DISAGREES')
    if any(r['receipt_envelope']['payload'].get('intent_sha256') == intent['intent_sha256']
           or r['receipt_envelope']['payload'].get('result_observation_sha256') == result['observation_sha256']
           for r in state['outcomes'] if r['receipt_envelope']['payload'] != payload):
        raise ValueError('SENSOR_ACTION_INTENT_OR_RESULT_REPLAY')
    return intent


def decide(data, request):
    from . import grounded_sensor as gs
    from tukuyo_v1019.transaction import transactional
    @transactional()
    def perform(data):
        gs.require_alive(data); state = gs.load(data)
        if set(request) != {'schema', 'observation_sha256', 'predecessor_sha256'} or request['schema'] != DECISION_SCHEMA:
            raise ValueError('SENSOR_ACTION_DECISION_REQUEST')
        observations, sensors = maps(state)
        observation = observations[request['observation_sha256']]
        if request['predecessor_sha256'] is None and any(
                observations[r['observation_sha256']]['claim'] == observation['claim']
                for r in state['decisions']):
            # A new root must not replenish the two-acquisition allowance for
            # the exact same typed claim. Continue its recorded chain instead.
            # Historical v7.3 rows remain replayable; new admission is stricter.
            raise ValueError('SENSOR_ACTION_CLAIM_BUDGET_RESET')
        parent = next((r for r in state['decisions'] if r['decision_sha256'] == request['predecessor_sha256']), None)
        remaining = parent['assessment']['remaining_acquisitions'] - 1 if parent else 2
        row = {'seq': len(state['decisions']) + 1, 'observation_sha256': request['observation_sha256'],
               'predecessor_sha256': request['predecessor_sha256'],
               'assessment': sensor_decision.assess(observation, sensors, remaining),
               'previous_decision_sha256': state['decision_head_sha256']}
        row['decision_sha256'] = gs._row_hash(row, 'decision_sha256')
        state['decisions'].append(row); state['decision_head_sha256'] = row['decision_sha256']
        gs.validate(state); gs.store.save(data, gs.NS, gs.COMPONENT, state)
        return {'ok': True, 'version': 'v1022.7.3', **row}
    return perform(data)


def precommit(data, request):
    from . import grounded_sensor as gs, metabolism
    from tukuyo_v1019.transaction import transactional
    @transactional()
    def perform(data):
        gs.require_alive(data); state = gs.load(data)
        fields = {'schema', 'intent_id', 'decision_sha256', 'runtime_id', 'action_id',
                  'action_context_sha256', 'expected_result', 'maximum_credit', 'started_at_tick', 'deadline_tick'}
        if set(request) != fields or request['schema'] != INTENT_SCHEMA:
            raise ValueError('SENSOR_ACTION_INTENT_REQUEST')
        decisions, _ = validate(state); decision = decisions.get(request['decision_sha256'])
        if not decision or decision['assessment']['decision'] != 'ACT': raise ValueError('SENSOR_ACTION_NOT_READY')
        metabolic = metabolism.preflight(data)
        if request['runtime_id'] not in metabolic['active']: raise ValueError('SENSOR_ACTION_RUNTIME_INACTIVE')
        row = copy.deepcopy(request); row.pop('schema'); row.update(seq=len(state['intents'])+1,
            observation_sha256=decision['observation_sha256'],
            runtime_head_sha256=metabolic['runtimes'][request['runtime_id']]['whole_sha256'],
            observations_at_commit=len(state['observations']), previous_intent_sha256=state['intent_head_sha256'])
        row['intent_sha256'] = gs._row_hash(row, 'intent_sha256')
        state['intents'].append(row); state['intent_head_sha256'] = row['intent_sha256']
        gs.validate(state); gs.store.save(data, gs.NS, gs.COMPONENT, state)
        return {'ok': True, 'version': 'v1022.7.3', **row, 'physical_action_executed': False}
    return perform(data)
