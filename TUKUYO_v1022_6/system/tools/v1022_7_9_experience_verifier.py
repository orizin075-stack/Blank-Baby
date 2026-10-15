#!/usr/bin/env python3
"""Independent provenance and learning replay; no TUKUYO runtime imports."""
import argparse,base64,copy,hashlib,json,re
from pathlib import Path
from v1022_7_evidence_verifier import verify as verify_evidence,read,sha_obj,verify_envelope,row_hash
from v1022_7_7_experience_verifier import replay as replay_legacy

NS='experience_provenance';COMP='whole_experience_provenance';ZERO='0'*64
V2='tukuyo.v1022_7_9.origin_bound_learning/1'
F=('self_wellbeing','others_wellbeing','future_self','truth_consistency','bodily_cost')
def fp(pub):return hashlib.sha256(base64.b64decode(pub,validate=True)).hexdigest()
def insist(condition,message):
    if not condition:raise ValueError(message)
def chain(rows,fields):
    previous=ZERO
    for i,row in enumerate(rows,1):
        insist(set(row)=={'seq','previous','sha256',*fields} and type(row['seq']) is int and row['seq']==i and row['previous']==previous and row['sha256']==row_hash(row,'sha256'),'PROVENANCE_CHAIN')
        previous=row['sha256']
    return previous
def snapshot(state,n=None,m=None):
    bindings=state['bindings'] if n is None else state['bindings'][:n];sources=state['sources'] if m is None else state['sources'][:m]
    return {'schema':'tukuyo.v1022_7_9.provenance_snapshot/1','identity':state['identity'],'policy':state['policy'],'policy_sha256':state['policy_sha256'],'sources':sources,'source_head':sources[-1]['sha256'] if sources else ZERO,'bindings':bindings,'binding_head':bindings[-1]['sha256'] if bindings else ZERO}
def verify_snapshot(s,registry,identity):
    insist(set(s)=={'schema','identity','policy','policy_sha256','sources','source_head','bindings','binding_head'} and s['schema']=='tukuyo.v1022_7_9.provenance_snapshot/1','SNAPSHOT_FIELDS')
    p=s['policy'];ident=s['identity'];scopes={'simulation':'simulation','teacher':'teacher','external_channel':'external_observation'}
    insist(set(p)=={'schema','scope','environment_id','registry','initial_decision_count','initial_attestation_count'} and p['schema']=='tukuyo.v1022_7_9.experience_policy/1' and p['scope'] in scopes and sha_obj(p)==s['policy_sha256'],'POLICY')
    insist(p['registry']==registry and ident==identity,'REGISTRY_OR_IDENTITY')
    insist(all(type(p[k]) is int and p[k]>=0 for k in ('initial_decision_count','initial_attestation_count')),'INITIAL_FRONTIER')
    authorities={a['authority_id']:a for a in registry['authorities']};witnesses={w['observer_id']:w for w in registry['witnesses']}
    banned={fp(a['public_key']) for a in authorities.values()}|{fp(w['observer_public_key']) for w in witnesses.values()}
    insist(chain(s['sources'],{'certificate'})==s['source_head'],'SOURCE_HEAD');sources={};pubs=set()
    for row in s['sources']:
        env=row['certificate'];q=env['payload'];a=authorities.get(q.get('authority_id'))
        insist(a and verify_envelope(env,a['public_key']),'SOURCE_SIGNATURE')
        insist(set(q)=={'schema','source_id','authority_id','source_class','environment_id','measurement_kind','producer_public_key'} and q['schema']=='tukuyo.v1022_7_9.source_certificate/1','SOURCE_FIELDS')
        insist(q['source_class'] in ('simulation','teacher','external_observation','self_report') and q['environment_id']==p['environment_id'],'SOURCE_CLASS')
        pub=q['producer_public_key'];key=fp(pub);insist(len(base64.b64decode(pub,validate=True))==32 and key not in banned and (key!=fp(ident['whole_public_key']) or q['source_class']=='self_report'),'SOURCE_ROLE')
        allowed=('sensor_reading','human_attestation') if q['source_class']=='external_observation' else ('bounded_evaluator',) if q['source_class'] in ('teacher','simulation') else ('human_attestation','bounded_evaluator')
        insist(q['measurement_kind'] in allowed and q['source_id'] not in sources and key not in pubs,'SOURCE_DUPLICATE_OR_MEASUREMENT')
        sources[q['source_id']]=q;pubs.add(key)
    insist(chain(s['bindings'],{'attestation_sha256','attestation','report'})==s['binding_head'],'BINDING_HEAD')
    seen=set();ids={};raws={}
    for row in s['bindings']:
        h=row['attestation_sha256'];insist(re.fullmatch('[0-9a-f]{64}',h) and h!=ZERO and h not in seen,'ATTESTATION_REPLAY');seen.add(h)
        env=row['report'];q=env['payload'];src=sources.get(q.get('source_id'));insist(src and verify_envelope(env,src['producer_public_key']),'PRODUCER_SIGNATURE')
        insist(set(q)=={'schema','report_id','source_id','source_class','environment_id','measurement_kind','individual_id','policy_sha256','decision_sha256','chosen','raw_evidence','outcomes'} and q['schema']=='tukuyo.v1022_7_9.source_report/1','REPORT_FIELDS')
        insist(all(q[k]==src[k] for k in ('source_id','source_class','environment_id','measurement_kind')) and q['individual_id']==ident['individual_id'] and q['policy_sha256']==s['policy_sha256'],'REPORT_ORIGIN_BINDING')
        insist(len(json.dumps(q['raw_evidence'],ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode())<=4096,'RAW_SIZE')
        insist(set(q['outcomes'])==set(F) and all(type(v) in (int,float) and (0 if k=='bodily_cost' else -1)<=v<=1 for k,v in q['outcomes'].items()),'OUTCOME_VECTOR')
        obs=row['attestation'];a=obs['payload'];w=witnesses.get(a.get('observer_id'));insist(w and verify_envelope(obs,w['observer_public_key']),'OBSERVER_SIGNATURE')
        evidence=sha_obj({'source_report_sha256':sha_obj(env),'observer_id':a['observer_id'],'decision_sha256':q['decision_sha256']})
        insist(a['decision_sha256']==q['decision_sha256'] and a['chosen']==q['chosen'] and a['measurement_kind']==q['measurement_kind'] and a['evidence_sha256']==evidence and all(a[k]==q['outcomes'][k] for k in F),'OBSERVER_BINDING')
        insist(src['source_class']!='self_report' or a['source_kind']=='self_report','SELF_REPORT_MASQUERADE')
        key=(src['source_id'],q['report_id']);digest=sha_obj(env);insist(key not in ids or ids[key]==digest,'REPORT_ID_REPLAY');ids[key]=digest
        key=(src['source_id'],sha_obj(q['raw_evidence']));insist(key not in raws or raws[key]==q['decision_sha256'],'RAW_REPLAY');raws[key]=q['decision_sha256']
    return sources,scopes[p['scope']]
def reflective_choice(dec,ref,applied):
    options=[{**o,'effects':applied[o['id']]} for o in dec['core_options']]
    insist(ref['options']==options and ref['context']==dec['context'] and ref['profile_policy']=='EXCLUDE_LEGACY_UNAUTHENTICATED_REAPPRAISALS' and ref['profile_used']['distinct_observers']==0,'REFLECTIVE_INPUT')
    weights=ref['profile_used']['perspective_weights'];scores={};conflicts=0
    for o in options:
        e=o['effects'];oid=o['id'];total=sum(e[k]*weights[k] for k in F[:-1])-e['bodily_cost']*weights['bodily_cost']-.15*e['uncertainty'];adj=round(max(-1.5,min(1.5,total)),6)
        insist(ref['reflective_adjustments'][oid]==adj,'REFLECTIVE_ADJUSTMENT');scores[oid]=round(ref['heart_base_scores'][oid]+ref['functional_adjustments'][oid]+adj,6)
        if e['self_wellbeing']*e['others_wellbeing']<0 or e['self_wellbeing']*e['future_self']<0 or e['others_wellbeing']*e['future_self']<0:conflicts+=1
    rank=sorted(scores,key=lambda x:(scores[x],x),reverse=True);margin=round(scores[rank[0]]-scores[rank[1]],6)
    threshold=round(min(.3,.1+.08*sum(o['effects']['uncertainty'] for o in options)/len(options)+(.05 if conflicts else 0)),6);chosen=None if margin<threshold else rank[0]
    insist(ref['full_scores']==scores and ref['score_margin']==margin and ref['review_threshold']==threshold and ref['chosen']==chosen and dec['chosen']==chosen,'ACTION_REPLAY')
def replay_strict(state,index,registry,identity,ref):
    dec=state['decisions'][index];c=dec['experience_learning'];sources,wanted=verify_snapshot(c['provenance_snapshot'],registry,identity);p=c['provenance_snapshot']['policy'];n=c['attestation_frontier_count']
    insist(type(n) is int and 0<=n<=len(state['attestations']),'FRONTIER');votes=state['attestations'][:n];prior=state['decisions'][:index];ams={r['attestation_sha256']:r for r in votes};dms={d['decision_sha256']:d for d in prior};links={}
    for b in c['provenance_snapshot']['bindings']:
        a=ams.get(b['attestation_sha256']);d=dms.get(b['report']['payload']['decision_sha256']);insist(a and d and a['envelope']==b['attestation'] and a['seq']>p['initial_attestation_count'] and d['seq']>p['initial_decision_count'],'FUTURE_OR_LEGACY_BINDING');links[b['attestation_sha256']]=b
    expected_meta={'schema':V2,'context_sha256':sha_obj(dec['context']),'attestation_frontier_count':n,'attestation_frontier_sha256':votes[-1]['attestation_sha256'] if votes else ZERO,'decision_frontier_count':index,'profile_policy':'EXCLUDE_LEGACY_UNAUTHENTICATED_REAPPRAISALS','minimum_episodes':2,'minimum_configured_domains':3,'maximum_outcome_disagreement':.25,'maximum_effect_correction':.6,'learning_gain':.5,'experience_scope':p['scope']}
    insist(all(c.get(k)==v for k,v in expected_meta.items()),'LEARNING_POLICY')
    boundary={'origin_classes_authority_declared_and_signature_bound':True,'reports_from_one_origin_do_not_count_as_independent_origins':True,'unclassified_history_automatically_promoted':False,'signatures_establish_truth':False,'statistical_source_independence_established':False,'unrelated_context_transfer':False,'private_experience_inherited':False,'consciousness_established':False,'literal_soul_established':False};insist(c['claim_boundary']==boundary,'CLAIM_BOUNDARY')
    ds={a['authority_id']:a['trust_domain'] for a in registry['authorities']};applied=copy.deepcopy(dec['aggregated_effects']);expected={}
    for opt in dec['core_options']:
        cases=[];excluded=[]
        for old in prior:
            if old['chosen']!=opt['id'] or old['context']!=dec['context'] or next((o for o in old['core_options'] if o['id']==opt['id']),None)!=opt:continue
            selected=[];origins=[];obkeys=set();obdomains=set();keys=set();domains=set();mismatch=False
            for a in votes:
                q=a['envelope']['payload'];b=links.get(a['attestation_sha256'])
                if q['decision_sha256']!=old['decision_sha256'] or q['confidence']<.7 or q['source_kind']=='self_report' or b is None:continue
                s=sources[b['report']['payload']['source_id']]
                if s['source_class']!=wanted:mismatch=True;continue
                key=fp(s['producer_public_key']);domain=ds[s['authority_id']]
                if a['observer_key_sha256'] in obkeys or a['trust_domain'] in obdomains or key in keys or domain in domains:continue
                selected.append(a);origins.append(b);obkeys.add(a['observer_key_sha256']);obdomains.add(a['trust_domain']);keys.add(key);domains.add(domain)
            reason=('EXPERIENCE_SCOPE_MISMATCH' if mismatch and not selected else 'INSUFFICIENT_ORIGIN_AND_OBSERVER_DOMAINS') if len(selected)<3 else None
            values={k:[a['envelope']['payload'][k] for a in selected] for k in F}
            if reason is None and any(round(max(v)-min(v),6)>.25 for v in values.values()):reason='OUTCOME_DISAGREEMENT'
            if reason:excluded.append({'decision_sha256':old['decision_sha256'],'reason':reason});continue
            obs={k:round(sum(v)/len(v),6) for k,v in values.items()};pred=old['aggregated_effects'][old['chosen']]
            cases.append({'decision_sha256':old['decision_sha256'],'attestation_sha256s':[a['attestation_sha256'] for a in selected],'domain_count':len(selected),'observed_effects':obs,'prediction_error':{k:round(obs[k]-pred[k],6) for k in F},'mean_absolute_prediction_error':round(sum(abs(obs[k]-pred[k]) for k in F)/5,6),'origin':{'source_class':wanted,'producer_key_sha256s':sorted(keys),'source_domains':sorted(domains),'report_sha256s':[sha_obj(b['report']) for b in origins],'physical_truth_verified':False}})
        corr={k:0.0 for k in F}
        if len(cases)>=2:
            for k in F:
                corr[k]=round(max(-.6,min(.6,.5*sum(v['prediction_error'][k] for v in cases)/len(cases))),6);applied[opt['id']][k]=round(max(0 if k=='bodily_cost' else -1,min(1,applied[opt['id']][k]+corr[k])),6)
        expected[opt['id']]={'option_sha256':sha_obj(opt),'eligible_episode_count':len(cases),'status':'APPLIED_ORIGIN_BOUND_EXPERIENCE' if len(cases)>=2 else 'WAIT_FOR_ORIGIN_BOUND_REPLICATION','cases':cases,'excluded_cases':excluded,'correction':corr}
    insist(c['options']==expected and c['applied_effects']==applied,'EXPERIENCE_REPLAY');reflective_choice(dec,ref,applied)
def verify(data):
    result=verify_evidence(data)
    try:
        insist(result['ok'],'LEGACY_EVIDENCE_CHECK');root=Path(data);whole=read(root/'v977/UNIFIED_STATE.json');pub=(root/'v977/whole_state.pub').read_text().strip();state=read(root/'evidence_bound_soul/STATE.json')['state']
        registry={'authorities':[r['authority'] for r in state['authorities']],'witnesses':[r['witness'] for r in state['witnesses']],'authority_head':state['authority_head_sha256'],'witness_head':state['witness_head_sha256']};identity={**whole['payload']['identity'],'whole_public_key':pub}
        cache=read(root/NS/'STATE.json');previous=ZERO;latest=None
        for i,path in enumerate(sorted((root/NS/'commits').glob('*.json')),1):
            env=read(path);q=env['payload'];insist(verify_envelope(env,pub) and q['schema']=='tukuyo.v1022.commit/1' and q['namespace']==NS and q['seq']==i and q['previous']==previous,'PROVENANCE_COMMIT');st=q['state'];insist(st['schema']=='tukuyo.v1022_7_9.experience_provenance/1','PROVENANCE_STATE');verify_snapshot(snapshot(st),registry,identity);chain(st['decisions'],{'decision_sha256','binding_count','source_count','snapshot_sha256'});previous=sha_obj(env);latest=st
        insist(latest is not None and cache['state']==latest and cache['head']==previous,'PROVENANCE_CACHE');insist(hashlib.sha256((root/NS/'STATE.json').read_bytes()).hexdigest()==whole['payload']['component_hashes'][COMP],'PROVENANCE_WHOLE')
        am={r['attestation_sha256']:r for r in state['attestations']};dm={d['decision_sha256']:d for d in state['decisions']}
        for b in latest['bindings']:
            a=am.get(b['attestation_sha256']);d=dm.get(b['report']['payload']['decision_sha256']);insist(a and d and a['envelope']==b['attestation'] and a['seq']>latest['policy']['initial_attestation_count'] and d['seq']>latest['policy']['initial_decision_count'],'ACTUAL_BINDING')
        refs={x['decision_sha256']:x for x in latest['decisions']};rc=read(root/'reflective_soul/STATE.json');previous=ZERO;rs=None
        for i,path in enumerate(sorted((root/'reflective_soul/commits').glob('*.json')),1):
            env=read(path);q=env['payload'];insist(verify_envelope(env,pub) and q['seq']==i and q['previous']==previous and q['namespace']=='reflective_soul','REFLECTIVE_COMMIT');previous=sha_obj(env);rs=q['state']
        insist(rc['state']==rs and rc['head']==previous and hashlib.sha256((root/'reflective_soul/STATE.json').read_bytes()).hexdigest()==whole['payload']['component_hashes']['whole_reflective_soul'],'REFLECTIVE_CACHE');reflective={d['decision_sha256']:d for d in rs['decisions']}
        start=next((i for i,d in enumerate(state['decisions']) if d.get('experience_learning',{}).get('schema')==V2),len(state['decisions']));legacy=copy.deepcopy(state);legacy['decisions']=state['decisions'][:start];replay_legacy(legacy,rs)
        for i,d in enumerate(state['decisions'][start:],start):
            c=d['experience_learning'];insist(c['schema']==V2 and d['decision_sha256'] in refs,'STRICT_MODE_HISTORY');ref=refs[d['decision_sha256']];snap=snapshot(latest,ref['binding_count'],ref['source_count']);insist(c['provenance_snapshot']==snap and ref['snapshot_sha256']==sha_obj(snap),'HISTORICAL_SNAPSHOT');replay_strict(state,i,registry,identity,reflective[d['reflective_decision_sha256']])
        result.update({'ok':True,'strict_decisions_replayed':len(state['decisions'])-start,'producer_reports_bound':len(latest['bindings']),'source_count':len(latest['sources']),'physical_truth_verified':False,'source_domain_real_world_independence_proven':False})
    except Exception as e:result['ok']=False;result.setdefault('errors',[]).append(type(e).__name__+':'+str(e))
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);a=p.parse_args();r=verify(a.data);print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(0 if r['ok'] else 1)
