#!/usr/bin/env python3
"""Standalone v1015.4 verifier. It intentionally imports no TUKUYO package modules."""
import re
import argparse, base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
ZERO='0'*64
BUNDLE_SCHEMA='tukuyo.v1015_4.portable_reproduction_bundle/1'
SUCCESS_SCHEMA='tukuyo.v1015_1.authenticated_endurance_bundle/1'
FAILURE_SCHEMA='tukuyo.v1015_3.failure_evidence/1'
RT_EVENT='tukuyo.v1013.realtime_event/1'
CAMPAIGN_EVENT='tukuyo.v1014_4.campaign_event/1'
WITNESS='tukuyo.v1013.witness_receipt/1'
WITNESS_PAYLOAD='tukuyo.v1013.witness_payload/1'
REQUEST='tukuyo.v1013.witness_request/1'
RESUME_EVENT='tukuyo.v1015_3.endurance_resume_event/1'
EXEC_EVENT='tukuyo.v1015_2.endurance_execution_event/1'
PROFILE_SECONDS={'24h':86400,'72h':259200,'7d':604800}
FORMAL_MAX_TICK_SECONDS=900

def canon(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha_obj(x): return hashlib.sha256(canon(x)).hexdigest()
def sha_bytes(x): return hashlib.sha256(x).hexdigest()
def read_json(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def load_pub(path):
    s=Path(path).read_text(encoding='utf-8').strip(); b=base64.b64decode(s,validate=True)
    if len(b)!=32: raise ValueError('KEYLEN')
    return s,Ed25519PublicKey.from_public_bytes(b)
def verify_env(env,pub):
    try:
        if env.get('public_key')!=pub:return False
        Ed25519PublicKey.from_public_bytes(base64.b64decode(pub,validate=True)).verify(base64.b64decode(env['signature'],validate=True),canon(env['payload']))
        return True
    except Exception:return False

def chain_errors(events,schema,count=None,head=None,prefix='EVENT'):
    errs=[]; prev=ZERO
    for i,e in enumerate(events,1):
        if not isinstance(e,dict): errs.append(f'{prefix}_MALFORMED:{i}'); continue
        if e.get('schema')!=schema or int(e.get('seq',-1))!=i: errs.append(f'{prefix}_SCHEMA_SEQ:{i}')
        if e.get('previous_event_sha256')!=prev: errs.append(f'{prefix}_CHAIN:{i}')
        prev=sha_obj(e)
    if count is not None and int(count)!=len(events):errs.append(prefix+'_STATE_COUNT')
    if head is not None and head!=prev:errs.append(prefix+'_STATE_HEAD')
    return errs,prev

def release_errors(obj,publisher_trust_file):
    errs=[]
    try:
        mb=base64.b64decode(obj.get('release_manifest_bytes_b64',''),validate=True); rb=base64.b64decode(obj.get('release_receipt_bytes_b64',''),validate=True)
        m=json.loads(mb); r=json.loads(rb); p=r['payload']; pub,pk=load_pub(publisher_trust_file)
        if r.get('public_key')!=pub: errs.append('RELEASE_TRUST_ROOT_MISMATCH')
        mv=str(m.get('version') or ''); tag=mv.replace('.','_')
        if not re.fullmatch(r'v[0-9]+(?:\.[0-9]+)*',mv) or m.get('schema')!=f'tukuyo.{tag}.release.manifest/1':errs.append('RELEASE_MANIFEST_SCHEMA')
        if r.get('schema')!=f'tukuyo.{tag}.release.receipt/1' or p.get('schema')!=f'tukuyo.{tag}.release.receipt_payload/1' or p.get('version')!=mv:errs.append('RELEASE_RECEIPT_SCHEMA')
        if m.get('file_count')!=len(m.get('files') or {}):errs.append('RELEASE_FILE_COUNT')
        if p.get('manifest_sha256')!=sha_bytes(mb):errs.append('RELEASE_RECEIPT_BINDING')
        try: pk.verify(base64.b64decode(r['signature'],validate=True),canon(p))
        except Exception: errs.append('RELEASE_SIGNATURE')
        b=obj.get('release_binding') or {}
        checks={
          'manifest_sha256':sha_bytes(mb),'receipt_sha256':sha_bytes(rb),'manifest_version':m.get('version'),
          'manifest_file_count':m.get('file_count'),'release_public_key':r.get('public_key'),'receipt_manifest_sha256':p.get('manifest_sha256')}
        for k,v in checks.items():
            if b.get(k)!=v:errs.append('RELEASE_BINDING:'+k)
        return errs,m,r
    except Exception as e:
        return ['RELEASE_MALFORMED:'+type(e).__name__],None,None

def witness_material_errors(source,witness_trust_file):
    errs=[]
    try: trust,pk=load_pub(witness_trust_file)
    except Exception as e:return ['WITNESS_TRUST_INVALID:'+type(e).__name__],[],None
    if source.get('witness_public_key') and source.get('witness_public_key')!=trust:errs.append('WITNESS_EMBEDDED_TRUST_MISMATCH')
    reqs={}
    for i,rq in enumerate(source.get('witness_requests') or [],1):
        try:
            z=dict(rq); got=z.pop('request_sha256',None)
            if rq.get('schema')!=REQUEST or got!=sha_obj(z):raise ValueError('HASH')
            reqs[got]=rq
        except Exception as e:errs.append(f'WITNESS_REQUEST_INVALID:{i}:{e}')
    return errs,reqs,(trust,pk)

def audit_success(src,witness_trust_file):
    errs=[]
    z=dict(src); got=z.pop('bundle_sha256',None)
    if src.get('schema')!=SUCCESS_SCHEMA:errs.append('SUCCESS_EVIDENCE_SCHEMA')
    if got!=sha_obj(z):errs.append('SUCCESS_EVIDENCE_HASH')
    cs=src.get('campaign_state') or {}; ce=src.get('campaign_events') or []; rs=src.get('realtime_state') or {}; revs=src.get('realtime_events') or []; pub=src.get('realtime_public_key') or ''
    if not (cs and ce and rs and revs and pub):errs.append('SUCCESS_SOURCE_MISSING')
    prev=ZERO; heads=[]; times=[]
    for i,env in enumerate(revs,1):
        p=env.get('payload') or {}
        if not verify_env(env,pub):errs.append(f'REALTIME_EVENT_SIGNATURE:{i}')
        if p.get('schema')!=RT_EVENT or int(p.get('seq',-1))!=i:errs.append(f'REALTIME_EVENT_SCHEMA_SEQ:{i}')
        if p.get('run_id')!=rs.get('run_id') or p.get('identity')!=rs.get('identity'):errs.append(f'REALTIME_EVENT_BINDING:{i}')
        if p.get('previous_event_sha256')!=prev:errs.append(f'REALTIME_EVENT_CHAIN:{i}')
        prev=sha_obj(env);heads.append(prev);times.append(int(p.get('observed_utc_ns',0)))
    if int(rs.get('last_event_seq',-1))!=len(revs) or rs.get('last_event_sha256')!=prev:errs.append('REALTIME_STATE_HEAD')
    cprev=ZERO
    for i,e in enumerate(ce,1):
        if e.get('schema')!=CAMPAIGN_EVENT or int(e.get('seq',-1))!=i:errs.append(f'CAMPAIGN_EVENT_SCHEMA_SEQ:{i}')
        if e.get('previous_event_sha256')!=cprev:errs.append(f'CAMPAIGN_EVENT_CHAIN:{i}')
        cprev=sha_obj(e)
    if int(cs.get('event_count',-1))!=len(ce) or cs.get('event_head_sha256')!=cprev:errs.append('CAMPAIGN_STATE_HEAD')
    if cs.get('run_id')!=rs.get('run_id'):errs.append('CAMPAIGN_REALTIME_RUN_BINDING')
    tick=int(cs.get('tick_seconds',0) or 0)
    if tick<1 or tick>FORMAL_MAX_TICK_SECONDS:errs.append('FORMAL_TICK_CADENCE_OUT_OF_RANGE')
    max_tick=max(5,tick*2) if 1<=tick<=FORMAL_MAX_TICK_SECONDS else 0
    if max_tick and any((b-a)/1e9>max_tick for a,b in zip(times,times[1:])):errs.append('REALTIME_TICK_GAP')
    wx,reqs,wctx=witness_material_errors(src,witness_trust_file);errs+=wx; pts=[]
    if wctx:
        trust,pk=wctx
        for i,r in enumerate(src.get('witness_receipts') or [],1):
            try:
                if r.get('schema')!=WITNESS or r.get('public_key')!=trust:raise ValueError('SCHEMA_OR_TRUST')
                p=r['payload']; pk.verify(base64.b64decode(r['signature'],validate=True),canon(p))
                if p.get('schema')!=WITNESS_PAYLOAD:raise ValueError('PAYLOAD_SCHEMA')
                if p.get('run_id')!=rs.get('run_id') or p.get('identity')!=rs.get('identity'):raise ValueError('BINDING')
                seq=int(p.get('seq',0));
                if seq<1 or seq>len(heads) or heads[seq-1]!=p.get('head_sha256'):raise ValueError('HEAD')
                rq=reqs.get(p.get('request_sha256'))
                if not rq or rq.get('run_id')!=p.get('run_id') or rq.get('identity')!=p.get('identity') or int(rq.get('seq',0))!=seq or rq.get('head_sha256')!=p.get('head_sha256'):raise ValueError('REQUEST_BINDING')
                pts.append((int(p.get('witnessed_utc_ns',0)),seq,p.get('head_sha256')))
            except Exception as e:errs.append(f'WITNESS_INVALID:{i}:{e}')
    pts=sorted(set(pts)); target=int(cs.get('target_seconds',0) or 0); elapsed=None
    if len(pts)<2:errs.append('WITNESS_CHAIN_TOO_SHORT')
    else:
        elapsed=(pts[-1][0]-pts[0][0])/1e9
        if elapsed<0:errs.append('WITNESS_TIME_REGRESSION')
        if any(b[1]<=a[1] for a,b in zip(pts,pts[1:])):errs.append('WITNESS_NO_PROGRESS')
        max_w=max(15,tick*2) if 1<=tick<=FORMAL_MAX_TICK_SECONDS else 0
        if max_w and any((b[0]-a[0])/1e9>max_w for a,b in zip(pts,pts[1:])):errs.append('WITNESS_GAP')
    formal=bool(not errs and elapsed is not None and elapsed>=target)
    prof=cs.get('profile'); required=PROFILE_SECONDS.get(prof)
    if required is None:errs.append('PROFILE_UNKNOWN')
    claims={'formal_duration_complete':formal,'24h_completed':bool(formal and target>=86400 and elapsed is not None and elapsed>=86400),
            '72h_completed':bool(formal and target>=259200 and elapsed is not None and elapsed>=259200),'7day_completed':bool(formal and target>=604800 and elapsed is not None and elapsed>=604800)}
    return errs,{'run_id':rs.get('run_id'),'profile':prof,'target_seconds':target,'external_witness_elapsed_seconds':elapsed,'verified_witness_receipts':len(pts),'claim_boundary':claims}

def audit_failure(src,witness_trust_file):
    errs=[]
    z=dict(src); got=z.pop('bundle_sha256',None)
    if src.get('schema')!=FAILURE_SCHEMA:errs.append('FAILURE_EVIDENCE_SCHEMA')
    if got!=sha_obj(z):errs.append('FAILURE_EVIDENCE_HASH')
    if src.get('terminal_state')!='FAILED' or not src.get('failure_reasons'):errs.append('FAILURE_TERMINAL_STATE')
    cb=src.get('claim_boundary') or {}
    if any(cb.get(k) for k in ('protocol_success','24h_completed','72h_completed','7day_completed')):errs.append('FAILURE_SUCCESS_CLAIM')
    rs=src.get('resume_state') or {}; re=src.get('resume_events') or []; x,_=chain_errors(re,RESUME_EVENT,rs.get('event_count'),rs.get('event_head_sha256'),'FAIL_RESUME');errs+=x
    es=src.get('execution_state') or {}; ee=src.get('execution_events') or []; x,_=chain_errors(ee,EXEC_EVENT,es.get('event_count'),es.get('event_head_sha256'),'FAIL_EXEC');errs+=x
    revs=src.get('realtime_events') or []; pub=src.get('realtime_public_key') or ''; prev=ZERO; heads=[]
    for i,env in enumerate(revs,1):
        p=env.get('payload') or {}
        if not verify_env(env,pub):errs.append(f'FAIL_REALTIME_SIGNATURE:{i}')
        if int(p.get('seq',-1))!=i or p.get('previous_event_sha256')!=prev:errs.append(f'FAIL_REALTIME_CHAIN:{i}')
        prev=sha_obj(env);heads.append(prev)
    rs2=src.get('realtime_state') or {}
    if revs and (int(rs2.get('last_event_seq',-1))!=len(revs) or rs2.get('last_event_sha256')!=prev):errs.append('FAIL_REALTIME_STATE_HEAD')
    wx,reqs,wctx=witness_material_errors(src,witness_trust_file);errs+=wx
    if wctx:
        trust,pk=wctx
        for i,r in enumerate(src.get('witness_receipts') or [],1):
            try:
                if r.get('schema')!=WITNESS or r.get('public_key')!=trust:raise ValueError('SCHEMA_OR_TRUST')
                p=r['payload'];pk.verify(base64.b64decode(r['signature'],validate=True),canon(p))
                rq=reqs.get(p.get('request_sha256'))
                if not rq:raise ValueError('REQUEST_MISSING')
                seq=int(p.get('seq',0));
                if seq<1 or seq>len(heads) or heads[seq-1]!=p.get('head_sha256'):raise ValueError('HEAD')
            except Exception as e:errs.append(f'FAIL_WITNESS_INVALID:{i}:{e}')
    return errs,{'failure_reasons':src.get('failure_reasons') or [],'claim_boundary':{'protocol_success':False,'24h_completed':False,'72h_completed':False,'7day_completed':False}}

def verify(bundle,publisher_trust_file,witness_trust_file):
    errs=[]
    try: obj=read_json(bundle)
    except Exception as e:return {'ok':False,'version':'v1015.4','errors':['BUNDLE_MALFORMED:'+type(e).__name__]}
    if obj.get('schema')!=BUNDLE_SCHEMA or obj.get('version')!='v1015.4':errs.append('BUNDLE_SCHEMA')
    z=dict(obj); got=z.pop('bundle_sha256',None)
    if got!=sha_obj(z):errs.append('BUNDLE_HASH')
    rerr,_,_=release_errors(obj,publisher_trust_file);errs+=rerr
    try:wtext,_=load_pub(witness_trust_file)
    except Exception as e:wtext='';errs.append('WITNESS_TRUST_INVALID:'+type(e).__name__)
    if obj.get('witness_public_key')!=wtext:errs.append('BUNDLE_WITNESS_TRUST_MISMATCH')
    rs=obj.get('resume_state') or {}; re=obj.get('resume_events') or []; x,_=chain_errors(re,RESUME_EVENT,rs.get('event_count'),rs.get('event_head_sha256'),'RESUME');errs+=x
    es=obj.get('execution_state') or {}; ee=obj.get('execution_events') or []; x,_=chain_errors(ee,EXEC_EVENT,es.get('event_count'),es.get('event_head_sha256'),'EXECUTION');errs+=x
    if rs.get('run_id')!=es.get('run_id'):errs.append('RUN_ID_RESUME_EXECUTION')
    outcome=obj.get('outcome'); src=obj.get('source_evidence') or {}; detail={}
    if outcome=='SUCCESS':
        if rs.get('terminal_state')!='SUCCEEDED' or es.get('phase')!='PROTOCOL_COMPLETE':errs.append('SUCCESS_TERMINAL_STATE')
        x,detail=audit_success(src,witness_trust_file);errs+=x
        if detail.get('run_id')!=rs.get('run_id'):errs.append('SUCCESS_RUN_ID_BINDING')
    elif outcome=='FAILURE':
        if rs.get('terminal_state')!='FAILED' or es.get('phase')!='FAILED':errs.append('FAILURE_TERMINAL_BINDING')
        x,detail=audit_failure(src,witness_trust_file);errs+=x
    else:errs.append('OUTCOME_UNKNOWN')
    return {'ok':not errs,'version':'v1015.4','schema':'tukuyo.v1015_4.independent_reproduction_audit/1','errors':errs,'outcome':outcome if not errs else None,
            'detail':detail,'claim_boundary':{'24h_completed':bool(detail.get('claim_boundary',{}).get('24h_completed')) if outcome=='SUCCESS' and not errs else False,
            '72h_completed':bool(detail.get('claim_boundary',{}).get('72h_completed')) if outcome=='SUCCESS' and not errs else False,
            '7day_completed':bool(detail.get('claim_boundary',{}).get('7day_completed')) if outcome=='SUCCESS' and not errs else False,
            'portable_no_data_root_required':True,'independent_verifier_imports_tukuyo_modules':False,'human_third_party_reproduction_completed':False}}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('bundle');ap.add_argument('--publisher-trust-file',required=True);ap.add_argument('--witness-trust-file',required=True);a=ap.parse_args()
    r=verify(a.bundle,a.publisher_trust_file,a.witness_trust_file);print(json.dumps(r,ensure_ascii=False,sort_keys=True));raise SystemExit(0 if r['ok'] else 1)
if __name__=='__main__':main()
