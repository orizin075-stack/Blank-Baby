"""Private, bounded prediction-error learning from signed, agreed outcomes.

Configured witness authorship is authenticated. External truth and statistical
independence are not established. Two acted episodes with three agreeing
domains each are required; lessons apply to the exact context and core option.
Canonical history, commitments, identity, energy and reward stay unchanged.
"""
from __future__ import annotations
import copy
from statistics import mean
from tukuyo_v977.whole_state import sha_obj

SCHEMA = 'tukuyo.v1022_7_7.soul_experience_learning/1'
FIELDS = ('self_wellbeing', 'others_wellbeing', 'future_self', 'truth_consistency', 'bodily_cost')
MIN_EPISODES, MIN_DOMAINS = 2, 3
MAX_DISAGREEMENT, MAX_CORRECTION, GAIN = .25, .6, .5

def _case(decision, attestations):
    # First eligible vote per domain AND key prevents repeated signed reports
    # from adding weight or shopping for a later favourable vote.
    votes, keys, domains = [], set(), set()
    for row in attestations:
        p = row['envelope']['payload']
        if (p['decision_sha256'] != decision['decision_sha256'] or p['confidence'] < .7
                or p['source_kind'] not in ('direct_observation', 'external_report')):
            continue
        if row['trust_domain'] in domains or row['observer_key_sha256'] in keys:
            continue
        votes.append(row); domains.add(row['trust_domain']); keys.add(row['observer_key_sha256'])
    if len(domains) < MIN_DOMAINS:
        return None, 'INSUFFICIENT_AUTHENTICATED_DOMAINS'
    values = {k: [v['envelope']['payload'][k] for v in votes] for k in FIELDS}
    if any(round(max(v) - min(v), 6) > MAX_DISAGREEMENT for v in values.values()):
        return None, 'OUTCOME_DISAGREEMENT'
    observed = {k: round(mean(v), 6) for k, v in values.items()}
    predicted = decision['aggregated_effects'][decision['chosen']]
    return {'decision_sha256': decision['decision_sha256'],
            'attestation_sha256s': [r['attestation_sha256'] for r in votes],
            'domain_count': len(domains), 'observed_effects': observed,
            'prediction_error': {k: round(observed[k] - predicted[k], 6) for k in FIELDS},
            'mean_absolute_prediction_error': round(mean(abs(observed[k]-predicted[k]) for k in FIELDS), 6)}, None

def prepare(state, options, context, effects, provenance_snapshot=None):
    """Pure replay; evidence_bound_soul must validate state before calling."""
    if provenance_snapshot is not None:
        return prepare_origin_bound(state,options,context,effects,provenance_snapshot)
    result, learning = copy.deepcopy(effects), {}
    for option in options:
        cases, excluded = [], []
        for decision in state['decisions']:
            if (decision['chosen'] != option['id'] or decision['context'] != context
                    or next((o for o in decision['core_options'] if o['id']==option['id']), None) != option):
                continue
            case, reason = _case(decision, state['attestations'])
            if case is None: excluded.append({'decision_sha256':decision['decision_sha256'], 'reason':reason})
            else: cases.append(case)
        correction = {k:0.0 for k in FIELDS}
        if len(cases) >= MIN_EPISODES:
            for key in FIELDS:
                delta = GAIN * mean(c['prediction_error'][key] for c in cases)
                correction[key] = round(max(-MAX_CORRECTION, min(MAX_CORRECTION, delta)), 6)
                low = 0.0 if key=='bodily_cost' else -1.0
                result[option['id']][key] = round(max(low, min(1.0, effects[option['id']][key]+correction[key])), 6)
        learning[option['id']] = {'option_sha256':sha_obj(option), 'eligible_episode_count':len(cases),
            'status':'APPLIED_BOUNDED_EXPERIENCE' if len(cases)>=MIN_EPISODES else 'WAIT_FOR_REPLICATION',
            'cases':cases, 'excluded_cases':excluded, 'correction':correction}
    return {'schema':SCHEMA, 'context_sha256':sha_obj(context),
        'attestation_frontier_count':len(state['attestations']), 'attestation_frontier_sha256':state['attestation_head_sha256'],
        'decision_frontier_count':len(state['decisions']), 'profile_policy':'EXCLUDE_LEGACY_UNAUTHENTICATED_REAPPRAISALS',
        'minimum_episodes':MIN_EPISODES, 'minimum_configured_domains':MIN_DOMAINS,
        'maximum_outcome_disagreement':MAX_DISAGREEMENT, 'maximum_effect_correction':MAX_CORRECTION, 'learning_gain':GAIN,
        'options':learning, 'applied_effects':result,
        'claim_boundary':{'signatures_establish_truth':False, 'statistical_source_independence_established':False,
                          'unrelated_context_transfer':False, 'private_experience_inherited':False,
                          'consciousness_established':False, 'literal_soul_established':False}}

def replay_prefix(state, index, certificate):
    n = certificate.get('attestation_frontier_count')
    if type(n) is not int or not 0<=n<=len(state['attestations']):
        raise ValueError('EVIDENCE_SOUL_LEARNING_FRONTIER')
    prior = copy.copy(state); prior['decisions']=state['decisions'][:index]; prior['attestations']=state['attestations'][:n]
    prior['attestation_head_sha256']=prior['attestations'][-1]['attestation_sha256'] if n else '0'*64
    allowed={d['decision_sha256'] for d in prior['decisions']}
    if any(r['envelope']['payload']['decision_sha256'] not in allowed for r in prior['attestations']):
        raise ValueError('EVIDENCE_SOUL_LEARNING_FUTURE_EPISODE')
    row=state['decisions'][index]
    from .experience_provenance import LEARNING
    expected=prepare(prior,row['core_options'],row['context'],row['aggregated_effects'],
                     certificate.get('provenance_snapshot') if certificate.get('schema')==LEARNING else None)
    if expected != certificate: raise ValueError('EVIDENCE_SOUL_LEARNING_REPLAY')
    return expected

def prepare_origin_bound(state,options,context,effects,snapshot):
    from . import experience_provenance as pv
    pv.validate_snapshot(snapshot);p=snapshot['policy'];ident=snapshot['identity']
    if any(ident[k]!=state[k] for k in ('individual_id','lineage_id','branch_id')) or pv.registry(state)!=p['registry']:
        raise ValueError('PROVENANCE_LEARNING_IDENTITY_OR_REGISTRY')
    if p['initial_decision_count']>len(state['decisions']) or p['initial_attestation_count']>len(state['attestations']):
        raise ValueError('PROVENANCE_LEARNING_INITIAL_FRONTIER')
    att={r['attestation_sha256']:r for r in state['attestations']};decs={d['decision_sha256']:d for d in state['decisions']}
    bindings={};sources={r['certificate']['payload']['source_id']:r['certificate']['payload'] for r in snapshot['sources']}
    domains={a['authority_id']:a['trust_domain'] for a in p['registry']['authorities']}
    for b in snapshot['bindings']:
        a=att.get(b['attestation_sha256']);d=decs.get(b['report']['payload']['decision_sha256'])
        if a is None or a['envelope']!=b['attestation'] or a['seq']<=p['initial_attestation_count'] or d is None or d['seq']<=p['initial_decision_count']:
            raise ValueError('PROVENANCE_LEARNING_FUTURE_OR_LEGACY_BINDING')
        bindings[b['attestation_sha256']]=b
    wanted=pv.SCOPES[p['scope']];applied=copy.deepcopy(effects);learned={}
    for option in options:
        cases=[];excluded=[]
        for d in state['decisions']:
            if d['chosen']!=option['id'] or d['context']!=context or next((o for o in d['core_options'] if o['id']==option['id']),None)!=option:continue
            votes=[];keys=set();ods=set();producers=set();pds=set();origins=[];wrong_scope=False
            for a in state['attestations']:
                q=a['envelope']['payload'];b=bindings.get(a['attestation_sha256'])
                if q['decision_sha256']!=d['decision_sha256'] or q['confidence']<.7 or q['source_kind']=='self_report' or b is None:continue
                report=b['report']['payload'];src=sources[report['source_id']]
                if src['source_class']!=wanted:wrong_scope=True;continue
                producer=pv.fingerprint(src['producer_public_key']);domain=domains[src['authority_id']]
                if a['observer_key_sha256'] in keys or a['trust_domain'] in ods or producer in producers or domain in pds:continue
                votes.append(a);origins.append(b);keys.add(a['observer_key_sha256']);ods.add(a['trust_domain']);producers.add(producer);pds.add(domain)
            reason=None
            if len(votes)<MIN_DOMAINS:reason='EXPERIENCE_SCOPE_MISMATCH' if wrong_scope and not votes else 'INSUFFICIENT_ORIGIN_AND_OBSERVER_DOMAINS'
            values={k:[r['envelope']['payload'][k] for r in votes] for k in FIELDS}
            if reason is None and any(round(max(v)-min(v),6)>MAX_DISAGREEMENT for v in values.values()):reason='OUTCOME_DISAGREEMENT'
            if reason is not None:excluded.append({'decision_sha256':d['decision_sha256'],'reason':reason});continue
            observed={k:round(mean(v),6) for k,v in values.items()};predicted=d['aggregated_effects'][d['chosen']]
            cases.append({'decision_sha256':d['decision_sha256'],'attestation_sha256s':[r['attestation_sha256'] for r in votes],
                'domain_count':len(votes),'observed_effects':observed,'prediction_error':{k:round(observed[k]-predicted[k],6) for k in FIELDS},
                'mean_absolute_prediction_error':round(mean(abs(observed[k]-predicted[k]) for k in FIELDS),6),
                'origin':{'source_class':wanted,'producer_key_sha256s':sorted(producers),'source_domains':sorted(pds),
                          'report_sha256s':[pv.sha(b['report']) for b in origins],'physical_truth_verified':False}})
        correction={k:0.0 for k in FIELDS}
        if len(cases)>=MIN_EPISODES:
            for k in FIELDS:
                delta=GAIN*mean(c['prediction_error'][k] for c in cases);correction[k]=round(max(-MAX_CORRECTION,min(MAX_CORRECTION,delta)),6)
                applied[option['id']][k]=round(max(0.0 if k=='bodily_cost' else -1.0,min(1.0,effects[option['id']][k]+correction[k])),6)
        learned[option['id']]={'option_sha256':sha_obj(option),'eligible_episode_count':len(cases),'status':'APPLIED_ORIGIN_BOUND_EXPERIENCE' if len(cases)>=MIN_EPISODES else 'WAIT_FOR_ORIGIN_BOUND_REPLICATION','cases':cases,'excluded_cases':excluded,'correction':correction}
    return {'schema':pv.LEARNING,'context_sha256':sha_obj(context),'attestation_frontier_count':len(state['attestations']),
        'attestation_frontier_sha256':state['attestation_head_sha256'],'decision_frontier_count':len(state['decisions']),
        'profile_policy':'EXCLUDE_LEGACY_UNAUTHENTICATED_REAPPRAISALS','minimum_episodes':MIN_EPISODES,
        'minimum_configured_domains':MIN_DOMAINS,'maximum_outcome_disagreement':MAX_DISAGREEMENT,
        'maximum_effect_correction':MAX_CORRECTION,'learning_gain':GAIN,'provenance_snapshot':copy.deepcopy(snapshot),
        'experience_scope':p['scope'],'options':learned,'applied_effects':applied,
        'claim_boundary':{'origin_classes_authority_declared_and_signature_bound':True,'reports_from_one_origin_do_not_count_as_independent_origins':True,
                          'unclassified_history_automatically_promoted':False,'signatures_establish_truth':False,
                          'statistical_source_independence_established':False,'unrelated_context_transfer':False,
                          'private_experience_inherited':False,'consciousness_established':False,'literal_soul_established':False}}
