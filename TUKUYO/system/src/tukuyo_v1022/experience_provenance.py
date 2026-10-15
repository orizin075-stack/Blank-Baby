"""Signed origin classes for bounded Soul learning; no physical truth proof.

Opt-in per individual. Reports, their original producers and forwarding
observers have separate identities. Historical unclassified outcomes stay out
of this policy. The configured authorities themselves remain trusted parties.
"""
from __future__ import annotations
import base64,copy,json,re
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from tukuyo_v977 import whole_state as whole
from tukuyo_v1019.lifecycle import require_alive
from tukuyo_v1019.transaction import transactional
from . import store

NS='experience_provenance';COMPONENT='whole_experience_provenance'
SCHEMA='tukuyo.v1022_7_9.experience_provenance/1'
POLICY='tukuyo.v1022_7_9.experience_policy/1'
SOURCE='tukuyo.v1022_7_9.source_certificate/1'
REPORT='tukuyo.v1022_7_9.source_report/1'
SNAPSHOT='tukuyo.v1022_7_9.provenance_snapshot/1'
LEARNING='tukuyo.v1022_7_9.origin_bound_learning/1'
CLASSES=('simulation','teacher','external_observation','self_report')
SCOPES={'simulation':'simulation','teacher':'teacher','external_channel':'external_observation'}
FIELDS=('self_wellbeing','others_wellbeing','future_self','truth_consistency','bodily_cost')
ZERO='0'*64

def text(v):
    if not isinstance(v,str) or not v or len(v)>160 or re.search(r'[\x00-\x1f]',v):raise ValueError('PROVENANCE_TEXT')
    return v
def sha(v):return whole.sha_obj(v)
def digest(v):
    if not isinstance(v,str) or not re.fullmatch('[0-9a-f]{64}',v) or v==ZERO:raise ValueError('PROVENANCE_HASH')
    return v
def fingerprint(pub):
    try:
        b=base64.b64decode(pub,validate=True)
        if len(b)!=32:raise ValueError()
        Ed25519PublicKey.from_public_bytes(b)
        import hashlib
        return hashlib.sha256(b).hexdigest()
    except Exception as e:raise ValueError('PROVENANCE_PUBLIC_KEY') from e
def verify(env,pub,schema):
    if not isinstance(env,dict) or set(env)!={'payload','public_key','signature'} or env['public_key']!=pub or not isinstance(env['payload'],dict) or env['payload'].get('schema')!=schema:raise ValueError('PROVENANCE_ENVELOPE')
    try:Ed25519PublicKey.from_public_bytes(base64.b64decode(pub,validate=True)).verify(base64.b64decode(env['signature'],validate=True),whole.canon(env['payload']))
    except Exception as e:raise ValueError('PROVENANCE_SIGNATURE') from e
    return env['payload']
def rowhash(row):return sha({k:v for k,v in row.items() if k!='sha256'})
def rowappend(rows,**fields):
    row={'seq':len(rows)+1,'previous':rows[-1]['sha256'] if rows else ZERO,**fields};row['sha256']=rowhash(row);rows.append(row);return row
def chain(rows,fields):
    if not isinstance(rows,list):raise ValueError('PROVENANCE_ROWS')
    previous=ZERO
    for i,r in enumerate(rows,1):
        if set(r)!={'seq','previous','sha256',*fields} or type(r['seq']) is not int or r['seq']!=i or r['previous']!=previous or r['sha256']!=rowhash(r):raise ValueError('PROVENANCE_CHAIN')
        previous=r['sha256']
    return previous
def registry(e):
    return {'authorities':[copy.deepcopy(r['authority']) for r in e['authorities']],
            'witnesses':[copy.deepcopy(r['witness']) for r in e['witnesses']],
            'authority_head':e['authority_head_sha256'],'witness_head':e['witness_head_sha256']}
def _source(env,policy,identity):
    p=env.get('payload',{}) if isinstance(env,dict) else {};a=next((x for x in policy['registry']['authorities'] if x['authority_id']==p.get('authority_id')),None)
    if not a:raise ValueError('PROVENANCE_AUTHORITY')
    p=verify(env,a['public_key'],SOURCE)
    if set(p)!={'schema','source_id','authority_id','source_class','environment_id','measurement_kind','producer_public_key'}:raise ValueError('PROVENANCE_SOURCE_FIELDS')
    text(p['source_id']);fingerprint(p['producer_public_key'])
    if p['source_class'] not in CLASSES or p['environment_id']!=policy['environment_id']:raise ValueError('PROVENANCE_SOURCE_CLASS_OR_ENVIRONMENT')
    kinds=('sensor_reading','human_attestation') if p['source_class']=='external_observation' else ('bounded_evaluator',) if p['source_class'] in ('simulation','teacher') else ('human_attestation','bounded_evaluator')
    if p['measurement_kind'] not in kinds:raise ValueError('PROVENANCE_MEASUREMENT_KIND')
    banned={fingerprint(x['public_key']) for x in policy['registry']['authorities']}|{fingerprint(x['observer_public_key']) for x in policy['registry']['witnesses']}
    producer=fingerprint(p['producer_public_key'])
    if producer in banned or (producer==fingerprint(identity['whole_public_key']) and p['source_class']!='self_report'):raise ValueError('PROVENANCE_PRODUCER_ROLE_COLLISION')
    return p,a
def observer_evidence(report,observer_id):
    return sha({'source_report_sha256':sha(report),'observer_id':observer_id,'decision_sha256':report['payload']['decision_sha256']})
def _binding(attestation,report,source,policy,identity):
    p=verify(report,source['producer_public_key'],REPORT)
    required={'schema','report_id','source_id','source_class','environment_id','measurement_kind','individual_id','policy_sha256','decision_sha256','chosen','raw_evidence','outcomes'}
    if set(p)!=required:raise ValueError('PROVENANCE_REPORT_FIELDS')
    text(p['report_id']);digest(p['decision_sha256']);text(p['chosen'])
    if any(p[k]!=source[k] for k in ('source_id','source_class','environment_id','measurement_kind')):raise ValueError('PROVENANCE_ORIGIN_MISMATCH')
    if p['individual_id']!=identity['individual_id'] or p['policy_sha256']!=sha(policy):raise ValueError('PROVENANCE_INDIVIDUAL_OR_POLICY')
    if len(whole.canon(p['raw_evidence']))>4096:raise ValueError('PROVENANCE_RAW_SIZE')
    outcomes=p['outcomes']
    if not isinstance(outcomes,dict) or set(outcomes)!=set(FIELDS):raise ValueError('PROVENANCE_OUTCOME_FIELDS')
    for k,v in outcomes.items():
        if type(v) not in (int,float) or not (0 if k=='bodily_cost' else -1)<=v<=1:raise ValueError('PROVENANCE_OUTCOME_NUMBER')
    q=attestation['payload'];w=next((x for x in policy['registry']['witnesses'] if x['observer_id']==q.get('observer_id')),None)
    if not w:raise ValueError('PROVENANCE_OBSERVER')
    verify(attestation,w['observer_public_key'],'tukuyo.v1022_7.outcome_attestation/1')
    if q['decision_sha256']!=p['decision_sha256'] or q['chosen']!=p['chosen'] or q['measurement_kind']!=p['measurement_kind'] or q['evidence_sha256']!=observer_evidence(report,q['observer_id']) or any(q[k]!=outcomes[k] for k in FIELDS):raise ValueError('PROVENANCE_OBSERVER_REPORT_BINDING')
    if p['source_class']=='self_report' and q['source_kind']!='self_report':raise ValueError('PROVENANCE_SELF_REPORT_MASQUERADE')
    return p
def validate_snapshot(s):
    if not isinstance(s,dict) or set(s)!={'schema','identity','policy','policy_sha256','sources','source_head','bindings','binding_head'} or s['schema']!=SNAPSHOT:raise ValueError('PROVENANCE_SNAPSHOT')
    p=s['policy'];ident=s['identity']
    if set(p)!={'schema','scope','environment_id','registry','initial_decision_count','initial_attestation_count'} or p['schema']!=POLICY or p['scope'] not in SCOPES or s['policy_sha256']!=sha(p):raise ValueError('PROVENANCE_POLICY')
    text(p['environment_id']);fingerprint(ident['whole_public_key']);text(ident['individual_id'])
    if any(type(p[k]) is not int or p[k]<0 for k in ('initial_decision_count','initial_attestation_count')):raise ValueError('PROVENANCE_INITIAL_FRONTIER')
    if chain(s['sources'],{'certificate'})!=s['source_head']:raise ValueError('PROVENANCE_SOURCE_HEAD')
    ids={};pubs=set()
    for row in s['sources']:
        src,_=_source(row['certificate'],p,ident)
        producer=fingerprint(src['producer_public_key'])
        if src['source_id'] in ids or producer in pubs:raise ValueError('PROVENANCE_DUPLICATE_PRODUCER')
        ids[src['source_id']]=src;pubs.add(producer)
    if chain(s['bindings'],{'attestation_sha256','attestation','report'})!=s['binding_head']:raise ValueError('PROVENANCE_BINDING_HEAD')
    seen=set();reports={};raws={}
    for row in s['bindings']:
        digest(row['attestation_sha256'])
        if row['attestation_sha256'] in seen:raise ValueError('PROVENANCE_ATTESTATION_REPLAY')
        seen.add(row['attestation_sha256']);src=ids.get(row['report']['payload'].get('source_id'))
        if not src:raise ValueError('PROVENANCE_SOURCE_UNKNOWN')
        packet=_binding(row['attestation'],row['report'],src,p,ident)
        key=(src['source_id'],packet['report_id']);h=sha(row['report'])
        if key in reports and reports[key]!=h:raise ValueError('PROVENANCE_REPORT_ID_REPLAY')
        reports[key]=h;key=(src['source_id'],sha(packet['raw_evidence']))
        if key in raws and raws[key]!=packet['decision_sha256']:raise ValueError('PROVENANCE_RAW_EVIDENCE_REPLAY')
        raws[key]=packet['decision_sha256']
def snapshot(state,n=None,m=None):
    bs=state['bindings'] if n is None else state['bindings'][:n];ss=state['sources'] if m is None else state['sources'][:m]
    return {'schema':SNAPSHOT,'identity':copy.deepcopy(state['identity']),'policy':copy.deepcopy(state['policy']),'policy_sha256':state['policy_sha256'],'sources':copy.deepcopy(ss),'source_head':ss[-1]['sha256'] if ss else ZERO,'bindings':copy.deepcopy(bs),'binding_head':bs[-1]['sha256'] if bs else ZERO}
def validate(state):
    if not isinstance(state,dict) or set(state)!={'schema','identity','policy','policy_sha256','sources','source_head','bindings','binding_head','decisions'} or state['schema']!=SCHEMA:raise ValueError('PROVENANCE_STATE')
    validate_snapshot(snapshot(state));chain(state['decisions'],{'decision_sha256','binding_count','source_count','snapshot_sha256'})
    for row in state['decisions']:
        if any(type(row[k]) is not int or not 0<=row[k]<=len(state['bindings'] if k=='binding_count' else state['sources']) for k in ('binding_count','source_count')):raise ValueError('PROVENANCE_DECISION_FRONTIER')
        if row['snapshot_sha256']!=sha(snapshot(state,row['binding_count'],row['source_count'])):raise ValueError('PROVENANCE_DECISION_SNAPSHOT')
def needs_preflight(data):
    if (Path(data)/NS).exists():return True
    p=whole.state_path(data)
    if not p.is_file():return False
    try:return COMPONENT in store.read(p)['payload'].get('component_hashes',{})
    except Exception:return True
def load(data):return store.load(data,NS,COMPONENT,validate)
def preflight(data):
    state=load(data)
    from . import evidence_bound_soul as es
    e=es.load(data)
    if registry(e)!=state['policy']['registry']:raise ValueError('PROVENANCE_TRUST_REGISTRY_DRIFT')
    return state
@transactional()
def integrate(data,scope,environment_id):
    require_alive(data)
    if scope not in SCOPES:raise ValueError('PROVENANCE_SCOPE')
    text(environment_id)
    if needs_preflight(data):
        state=preflight(data)
        if state['policy']['scope']!=scope or state['policy']['environment_id']!=environment_id:raise ValueError('PROVENANCE_POLICY_IMMUTABLE')
        return status(data)
    from . import evidence_bound_soul as es
    es.integrate(data);e=es.load(data)
    if len(e['authorities'])<3 or len(e['witnesses'])<3:raise ValueError('PROVENANCE_TRUST_SETUP_REQUIRED')
    ident={**whole._live_identity(data),'whole_public_key':whole._key_paths(data)[1].read_text().strip()}
    p={'schema':POLICY,'scope':scope,'environment_id':environment_id,'registry':registry(e),'initial_decision_count':len(e['decisions']),'initial_attestation_count':len(e['attestations'])}
    state={'schema':SCHEMA,'identity':ident,'policy':p,'policy_sha256':sha(p),'sources':[],'source_head':ZERO,'bindings':[],'binding_head':ZERO,'decisions':[]}
    validate(state);store.save(data,NS,COMPONENT,state);return status(data)
@transactional()
def add_source(data,certificate):
    require_alive(data);state=preflight(data)
    if state['decisions']:raise ValueError('PROVENANCE_SOURCES_SEALED')
    _source(certificate,state['policy'],state['identity'])
    if len(state['sources'])>=16:raise ValueError('PROVENANCE_SOURCE_LIMIT')
    rowappend(state['sources'],certificate=copy.deepcopy(certificate));state['source_head']=state['sources'][-1]['sha256'];validate(state);store.save(data,NS,COMPONENT,state);return status(data)
@transactional()
def attest(data,attestation,report):
    require_alive(data);state=preflight(data)
    from . import evidence_bound_soul as es
    e=es.load(data);p=attestation.get('payload',{}) if isinstance(attestation,dict) else {};src=next((r['certificate']['payload'] for r in state['sources'] if r['certificate']['payload']['source_id']==report.get('payload',{}).get('source_id')),None)
    if src is None:raise ValueError('PROVENANCE_SOURCE_UNKNOWN')
    _binding(attestation,report,src,state['policy'],state['identity'])
    target=next((d for d in e['decisions'] if d['decision_sha256']==p['decision_sha256']),None)
    if target is None or target['seq']<=state['policy']['initial_decision_count'] or target.get('experience_learning',{}).get('schema')!=LEARNING:raise ValueError('PROVENANCE_HISTORICAL_OR_UNACTED_DECISION')
    # Check replay before mutating either namespace, then append in one lineage transaction.
    probe=copy.deepcopy(state);fake='1'*64
    rowappend(probe['bindings'],attestation_sha256=fake,attestation=copy.deepcopy(attestation),report=copy.deepcopy(report));probe['binding_head']=probe['bindings'][-1]['sha256'];validate(probe)
    result=es.attest(data,attestation)
    rowappend(state['bindings'],attestation_sha256=result['attestation_sha256'],attestation=copy.deepcopy(attestation),report=copy.deepcopy(report));state['binding_head']=state['bindings'][-1]['sha256'];validate(state);store.save(data,NS,COMPONENT,state)
    return {'ok':True,'attestation_sha256':result['attestation_sha256'],'source_class':src['source_class'],'origin_authorship_verified':True,'physical_truth_verified':False,'eligible_class_for_scope':src['source_class']==SCOPES[state['policy']['scope']]}
def record_decision(data,decision):
    state=load(data);cert=decision['experience_learning'];snap=cert['provenance_snapshot']
    if snap!=snapshot(state):raise ValueError('PROVENANCE_DECISION_CHANGED_FRONTIER')
    rowappend(state['decisions'],decision_sha256=decision['decision_sha256'],binding_count=len(state['bindings']),source_count=len(state['sources']),snapshot_sha256=sha(snap));validate(state);store.save(data,NS,COMPONENT,state)
def status(data):
    s=preflight(data);return {'ok':True,'strict_origin_learning_enabled':True,'scope':s['policy']['scope'],'environment_id':s['policy']['environment_id'],'sources':len(s['sources']),'bindings':len(s['bindings']),'strict_decisions':len(s['decisions']),'source_classes':{c:sum(r['report']['payload']['source_class']==c for r in s['bindings']) for c in CLASSES},'physical_truth_verified':False,'legacy_unclassified_automatically_promoted':False}
def audit(data):
    try:
        s=preflight(data)
        from . import evidence_bound_soul as es
        e=es.load(data);am={r['attestation_sha256']:r for r in e['attestations']};dm={r['decision_sha256']:r for r in e['decisions']}
        if any(s['identity'][k]!=whole._live_identity(data)[k] for k in ('individual_id','lineage_id','branch_id')):raise ValueError('PROVENANCE_IDENTITY')
        for b in s['bindings']:
            a=am.get(b['attestation_sha256']);d=dm.get(b['report']['payload']['decision_sha256'])
            if a is None or a['envelope']!=b['attestation'] or a['seq']<=s['policy']['initial_attestation_count'] or d is None or d['seq']<=s['policy']['initial_decision_count']:raise ValueError('PROVENANCE_LEGACY_OR_ATTESTATION_BINDING')
        records={r['decision_sha256']:r for r in s['decisions']}
        for d in e['decisions']:
            c=d.get('experience_learning',{})
            if c.get('schema')!=LEARNING:continue
            row=records.get(d['decision_sha256'])
            if row is None or c['provenance_snapshot']!=snapshot(s,row['binding_count'],row['source_count']):raise ValueError('PROVENANCE_HISTORY_BINDING')
        if any(k not in dm for k in records):raise ValueError('PROVENANCE_UNKNOWN_DECISION')
        return {'ok':True,'sources':len(s['sources']),'bindings':len(s['bindings']),'strict_decisions':len(records),'physical_truth_verified':False}
    except (ValueError,KeyError,TypeError,OSError) as e:return {'ok':False,'errors':[type(e).__name__+':'+str(e)],'physical_truth_verified':False}
