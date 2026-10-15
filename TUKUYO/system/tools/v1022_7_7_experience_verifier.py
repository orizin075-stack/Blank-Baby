#!/usr/bin/env python3
"""Raw-byte verifier; imports no TUKUYO runtime or learning implementation.

Reuses only the earlier independent cryptographic checker. Reconstructs the
learning frontier, eligible episodes, errors, clipping and reflective choice.
It establishes neither external truth nor human-like experience.
"""
import argparse, copy, hashlib, json, statistics
from pathlib import Path
from v1022_7_evidence_verifier import verify as verify_evidence, read, sha_obj, row_hash, verify_envelope

FIELDS=('self_wellbeing','others_wellbeing','future_self','truth_consistency','bodily_cost')

def replay(state, reflective):
    errors=[]
    linked={r['decision_sha256']:r for r in reflective['decisions']}
    for index,dec in enumerate(state['decisions']):
        cert=dec.get('experience_learning')
        if cert is None:continue  # authentic historical v7 certificates
        n=cert['attestation_frontier_count']
        if type(n) is not int or not 0<=n<=len(state['attestations']):raise ValueError('FRONTIER_RANGE')
        prefix=state['attestations'][:n]
        head=prefix[-1]['attestation_sha256'] if prefix else '0'*64
        prior=state['decisions'][:index]; allowed={r['decision_sha256'] for r in prior}
        if any(r['envelope']['payload']['decision_sha256'] not in allowed for r in prefix):raise ValueError('FUTURE_EPISODE')
        meta={'schema':'tukuyo.v1022_7_7.soul_experience_learning/1','context_sha256':sha_obj(dec['context']),
              'attestation_frontier_count':n,'attestation_frontier_sha256':head,'decision_frontier_count':index,
              'profile_policy':'EXCLUDE_LEGACY_UNAUTHENTICATED_REAPPRAISALS','minimum_episodes':2,
              'minimum_configured_domains':3,'maximum_outcome_disagreement':.25,'maximum_effect_correction':.6,'learning_gain':.5}
        if any(cert.get(k)!=v for k,v in meta.items()):raise ValueError('LEARNING_POLICY')
        if cert.get('claim_boundary') != {'signatures_establish_truth':False,
                'statistical_source_independence_established':False,'unrelated_context_transfer':False,
                'private_experience_inherited':False,'consciousness_established':False,'literal_soul_established':False}:
            raise ValueError('LEARNING_CLAIM_BOUNDARY')
        applied=copy.deepcopy(dec['aggregated_effects']); expected_options={}
        for opt in dec['core_options']:
            samples=[];excluded=[]
            for old in prior:
                old_opt=next((o for o in old['core_options'] if o['id']==old['chosen']),None)
                if old['context']!=dec['context'] or old_opt!=opt:continue
                vote_by_domain={};seen_keys=set()
                for vote in prefix:
                    p=vote['envelope']['payload']
                    if p['decision_sha256']!=old['decision_sha256'] or p['confidence']<.7 or p['source_kind']=='self_report':continue
                    if vote['trust_domain'] in vote_by_domain or vote['observer_key_sha256'] in seen_keys:continue
                    vote_by_domain[vote['trust_domain']]=vote;seen_keys.add(vote['observer_key_sha256'])
                votes=list(vote_by_domain.values())
                reason='INSUFFICIENT_AUTHENTICATED_DOMAINS' if len(votes)<3 else None
                values={k:[v['envelope']['payload'][k] for v in votes] for k in FIELDS}
                if reason is None and any(round(max(v)-min(v),6)>.25 for v in values.values()):reason='OUTCOME_DISAGREEMENT'
                if reason:
                    excluded.append({'decision_sha256':old['decision_sha256'],'reason':reason});continue
                observed={k:round(sum(v)/len(v),6) for k,v in values.items()}
                pred=old['aggregated_effects'][opt['id']]
                samples.append({'decision_sha256':old['decision_sha256'],'attestation_sha256s':[v['attestation_sha256'] for v in votes],
                    'domain_count':len(votes),'observed_effects':observed,
                    'prediction_error':{k:round(observed[k]-pred[k],6) for k in FIELDS},
                    'mean_absolute_prediction_error':round(sum(abs(observed[k]-pred[k]) for k in FIELDS)/5,6)})
            corrections={k:0.0 for k in FIELDS}
            if len(samples)>=2:
                for k in FIELDS:
                    err=sum(s['prediction_error'][k] for s in samples)/len(samples)
                    corrections[k]=round(min(.6,max(-.6,.5*err)),6)
                    applied[opt['id']][k]=round(min(1,max(0 if k=='bodily_cost' else -1,applied[opt['id']][k]+corrections[k])),6)
            expected_options[opt['id']]={'option_sha256':sha_obj(opt),'eligible_episode_count':len(samples),
                'status':'APPLIED_BOUNDED_EXPERIENCE' if len(samples)>=2 else 'WAIT_FOR_REPLICATION',
                'cases':samples,'excluded_cases':excluded,'correction':corrections}
        if cert['options']!=expected_options or cert['applied_effects']!=applied:raise ValueError('EXPERIENCE_REPLAY')
        r=linked.get(dec['reflective_decision_sha256'])
        options=[{**o,'effects':applied[o['id']]} for o in dec['core_options']]
        if not r or r['options']!=options or r['context']!=dec['context'] or r.get('profile_policy')!=meta['profile_policy']:raise ValueError('REFLECTIVE_BINDING')
        if r['decision_sha256']!=row_hash(r,'decision_sha256'):raise ValueError('REFLECTIVE_ROW_HASH')
        if r['profile_used']['distinct_observers']!=0:raise ValueError('UNAUTHENTICATED_CALIBRATION')
        weights=r['profile_used']['perspective_weights'];scores={};conflicts=0
        for o in options:
            e=o['effects'];oid=o['id']
            total=sum(e[k]*weights[k] for k in FIELDS[:-1])-e['bodily_cost']*weights['bodily_cost']-.15*e['uncertainty']
            adjustment=round(max(-1.5,min(1.5,total)),6)
            if r['reflective_adjustments'][oid]!=adjustment:raise ValueError('REFLECTIVE_ADJUSTMENT')
            scores[oid]=round(r['heart_base_scores'][oid]+r['functional_adjustments'][oid]+adjustment,6)
            if e['self_wellbeing']*e['others_wellbeing']<0 or e['self_wellbeing']*e['future_self']<0 or e['others_wellbeing']*e['future_self']<0:conflicts+=1
        rank=sorted(scores,key=lambda x:(scores[x],x),reverse=True);margin=round(scores[rank[0]]-scores[rank[1]],6)
        threshold=round(min(.3,.1+.08*sum(o['effects']['uncertainty'] for o in options)/len(options)+(.05 if conflicts else 0)),6)
        chosen=None if margin<threshold else rank[0]
        if (r['full_scores']!=scores or r['score_margin']!=margin or r['review_threshold']!=threshold
                or r['chosen']!=chosen or dec['chosen']!=chosen):raise ValueError('ACTION_REPLAY')
    return errors

def verify(data):
    result=verify_evidence(data)
    try:
        root=Path(data);state=read(root/'evidence_bound_soul/STATE.json')['state']
        pub=(root/'v977/whole_state.pub').read_text().strip();whole=read(root/'v977/UNIFIED_STATE.json')
        ns=root/'reflective_soul';raw=(ns/'STATE.json').read_bytes();cache=json.loads(raw)
        if hashlib.sha256(raw).hexdigest()!=whole['payload']['component_hashes']['whole_reflective_soul']:raise ValueError('REFLECTIVE_WHOLE_BINDING')
        previous='0'*64;latest=None
        for i,p in enumerate(sorted((ns/'commits').glob('*.json')),1):
            env=read(p);q=env['payload']
            if not verify_envelope(env,pub) or q['seq']!=i or q['previous']!=previous or q['namespace']!='reflective_soul':raise ValueError('REFLECTIVE_COMMIT')
            previous=sha_obj(env);latest=q['state']
        if cache['state']!=latest or cache['head']!=previous:raise ValueError('REFLECTIVE_CACHE')
        replay(state,cache['state'])
        result['experience_certificates_replayed']=sum('experience_learning' in d for d in state['decisions'])
        result['bounded_learning_replay_valid']=result['ok']
    except Exception as exc:
        result['ok']=False;result['errors'].append(type(exc).__name__+':'+str(exc));result['bounded_learning_replay_valid']=False
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);a=p.parse_args()
    r=verify(a.data);print(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2));raise SystemExit(0 if r['ok'] else 1)
