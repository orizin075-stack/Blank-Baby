from __future__ import annotations
import base64, hashlib, json, math
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from tukuyo_v977.whole_state import canon, sha_obj

SCHEMA='tukuyo.v1015_1.authenticated_endurance_bundle/1'
EVENT_SCHEMA='tukuyo.v1013.realtime_event/1'
CAMPAIGN_EVENT_SCHEMA='tukuyo.v1014_4.campaign_event/1'
WITNESS_SCHEMA='tukuyo.v1013.witness_receipt/1'
WITNESS_PAYLOAD_SCHEMA='tukuyo.v1013.witness_payload/1'
ZERO='0'*64
PROFILE_SECONDS={'24h':86400,'72h':259200,'7d':604800}
FORMAL_MAX_TICK_SECONDS=900

def _read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def _file_sha(p):
    p=Path(p); return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None

def _verify_env(env,pub):
    try:
        if env.get('public_key')!=pub:return False
        Ed25519PublicKey.from_public_bytes(base64.b64decode(pub,validate=True)).verify(base64.b64decode(env['signature'],validate=True),canon(env['payload']))
        return True
    except Exception:return False

def _load_request(path):
    p=Path(path)
    if not p.is_file():return None
    try:
        x=_read(p);z=dict(x);got=z.pop('request_sha256',None)
        if x.get('schema')!='tukuyo.v1013.witness_request/1' or got!=sha_obj(z):return None
        return x
    except Exception:return None

def _safe_read_path(data,path):
    try:
        p=Path(path)
        if not p.is_absolute():p=Path(data)/p
        return _read(p) if p.is_file() else None
    except Exception:return None

def export_bundle(data,out,start_witness,end_witness,witness_trust_file):
    """Export self-contained evidence material. Claims are recomputed on audit; copied audit flags are non-authoritative."""
    data=Path(data);out=Path(out)
    from tukuyo_v1014_4.long_run_campaign import audit as campaign_audit, state_path as campaign_state_path, _scan_events as campaign_events, root as campaign_root
    from tukuyo_v1013.realtime_continuity import state_path as rt_state_path, _events as rt_events, _key_paths
    ca=campaign_audit(data,start_witness,end_witness,witness_trust_file,True)
    cs=_read(campaign_state_path(data));ce=campaign_events(data);rs=_read(rt_state_path(data));re=rt_events(data);pub=_key_paths(data)[1].read_text().strip()
    requests=[]
    cr=campaign_root(data)
    for p in sorted((cr/'witness_requests').glob('*.json')) if (cr/'witness_requests').is_dir() else []:
        x=_load_request(p)
        if x:requests.append(x)
    # Also collect request paths referenced by campaign events (supports custom --out paths).
    seen={x.get('request_sha256') for x in requests}
    for ev in ce:
        d=ev.get('detail') or {};p=d.get('path')
        if p:
            x=_load_request(p)
            if x and x.get('request_sha256') not in seen:requests.append(x);seen.add(x.get('request_sha256'))
    receipts=[]
    for p in [Path(start_witness)]+(sorted((cr/'witness_receipts').glob('*.json')) if (cr/'witness_receipts').is_dir() else [])+[Path(end_witness)]:
        try:x=_read(p)
        except Exception:continue
        if x not in receipts:receipts.append(x)
    obj={'schema':SCHEMA,'version':'v1015.1','campaign_state':cs,'campaign_events':ce,'realtime_state':rs,'realtime_events':re,
         'realtime_public_key':pub,'witness_requests':requests,'witness_receipts':receipts,
         'source_bindings':{'whole_state_sha256':_file_sha(data/'state'/'integration_state.json'),
                            'realtime_events_sha256':_file_sha(data/'v1013'/'REALTIME_EVENTS.jsonl'),
                            'realtime_state_sha256':_file_sha(data/'v1013'/'REALTIME_RUN.json')},
         'non_authoritative_source_audit':ca,
         'claim_boundary':{'copied_audit_flags_are_not_trusted':True,'formal_claim_requires_external_witness_signature_reverification':True}}
    obj['bundle_sha256']=sha_obj(obj);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(canon(obj)+b'\n')
    return audit_bundle(out,witness_trust_file)

def audit_bundle(evidence,witness_trust_file,profile=None):
    errs=[]
    try:obj=_read(evidence)
    except Exception as e:return {'ok':False,'version':'v1015.1','errors':['EVIDENCE_MALFORMED:'+type(e).__name__]}
    if obj.get('schema')!=SCHEMA:errs.append('EVIDENCE_SCHEMA')
    z=dict(obj);got=z.pop('bundle_sha256',None)
    if got!=sha_obj(z):errs.append('EVIDENCE_BUNDLE_HASH')
    cs=obj.get('campaign_state') or {};ce=obj.get('campaign_events') or [];rs=obj.get('realtime_state') or {};revs=obj.get('realtime_events') or []
    pub=obj.get('realtime_public_key') or ''
    if not (cs and ce and rs and revs and pub):errs.append('SOURCE_MATERIAL_MISSING')
    # Realtime signed chain.
    prev=ZERO;heads=[];times=[]
    for i,env in enumerate(revs,1):
        p=env.get('payload') or {}
        if not _verify_env(env,pub):errs.append(f'REALTIME_EVENT_SIGNATURE:{i}')
        if p.get('schema')!=EVENT_SCHEMA or int(p.get('seq',-1))!=i or p.get('run_id')!=rs.get('run_id'):errs.append(f'REALTIME_EVENT_SCHEMA_SEQ:{i}')
        if p.get('identity')!=rs.get('identity'):errs.append(f'REALTIME_EVENT_IDENTITY:{i}')
        if p.get('previous_event_sha256')!=prev:errs.append(f'REALTIME_EVENT_CHAIN:{i}')
        prev=sha_obj(env);heads.append(prev);times.append(int(p.get('observed_utc_ns',0)))
    if int(rs.get('last_event_seq',-1))!=len(revs) or rs.get('last_event_sha256')!=prev:errs.append('REALTIME_STATE_HEAD')
    # Campaign hash chain. Never trust copied audit.ok / completion flags.
    cprev=ZERO
    for i,ev in enumerate(ce,1):
        if ev.get('schema')!=CAMPAIGN_EVENT_SCHEMA or int(ev.get('seq',-1))!=i:errs.append(f'CAMPAIGN_EVENT_SCHEMA_SEQ:{i}')
        if ev.get('previous_event_sha256')!=cprev:errs.append(f'CAMPAIGN_EVENT_CHAIN:{i}')
        cprev=sha_obj(ev)
    if int(cs.get('event_count',-1))!=len(ce) or cs.get('event_head_sha256')!=cprev:errs.append('CAMPAIGN_STATE_HEAD')
    if cs.get('run_id')!=rs.get('run_id'):errs.append('CAMPAIGN_REALTIME_RUN_BINDING')
    # Formal cadence is derived and capped; a caller cannot make 24h formal by choosing a 12h tick.
    tick=int(cs.get('tick_seconds',0) or 0)
    if tick<1 or tick>FORMAL_MAX_TICK_SECONDS:errs.append('FORMAL_TICK_CADENCE_OUT_OF_RANGE')
    max_tick_gap=max(5,tick*2) if 1<=tick<=FORMAL_MAX_TICK_SECONDS else 0
    if max_tick_gap and any((b-a)/1e9>max_tick_gap for a,b in zip(times,times[1:])):errs.append('REALTIME_TICK_GAP')
    # Verify witness requests and externally signed receipts from raw material.
    reqs={}
    for rq in obj.get('witness_requests') or []:
        try:
            zz=dict(rq);rh=zz.pop('request_sha256',None)
            if rq.get('schema')!='tukuyo.v1013.witness_request/1' or rh!=sha_obj(zz):errs.append('WITNESS_REQUEST_HASH');continue
            reqs[rh]=rq
        except Exception:errs.append('WITNESS_REQUEST_MALFORMED')
    try:trust=Path(witness_trust_file).read_text(encoding='utf-8').strip();kb=base64.b64decode(trust,validate=True);Ed25519PublicKey.from_public_bytes(kb)
    except Exception:trust='';errs.append('WITNESS_TRUST_INVALID')
    pts=[]
    for j,r in enumerate(obj.get('witness_receipts') or [],1):
        try:
            if r.get('schema')!=WITNESS_SCHEMA or r.get('public_key')!=trust:raise ValueError('SCHEMA_OR_TRUST')
            p=r['payload'];Ed25519PublicKey.from_public_bytes(base64.b64decode(trust,validate=True)).verify(base64.b64decode(r['signature'],validate=True),canon(p))
            if p.get('schema')!=WITNESS_PAYLOAD_SCHEMA:raise ValueError('PAYLOAD_SCHEMA')
            if p.get('run_id')!=rs.get('run_id') or p.get('identity')!=rs.get('identity'):raise ValueError('BINDING')
            seq=int(p.get('seq',0))
            if seq<1 or seq>len(heads) or heads[seq-1]!=p.get('head_sha256'):raise ValueError('HEAD')
            rq=reqs.get(p.get('request_sha256'))
            if not rq:raise ValueError('REQUEST_MISSING')
            if rq.get('run_id')!=p.get('run_id') or rq.get('identity')!=p.get('identity') or int(rq.get('seq',0))!=seq or rq.get('head_sha256')!=p.get('head_sha256'):raise ValueError('REQUEST_BINDING')
            pts.append((int(p.get('witnessed_utc_ns',0)),seq,p.get('head_sha256')))
        except Exception as e:errs.append(f'WITNESS_INVALID:{j}:{str(e)}')
    pts=sorted(set(pts))
    target=int(cs.get('target_seconds',0) or 0)
    external_elapsed=None
    if len(pts)<2:errs.append('WITNESS_CHAIN_TOO_SHORT')
    else:
        external_elapsed=(pts[-1][0]-pts[0][0])/1e9
        if external_elapsed<0:errs.append('WITNESS_TIME_REGRESSION')
        if any(b[1]<=a[1] for a,b in zip(pts,pts[1:])):errs.append('WITNESS_NO_PROGRESS')
        max_witness_gap=max(15,tick*2) if 1<=tick<=FORMAL_MAX_TICK_SECONDS else 0
        if max_witness_gap and any((b[0]-a[0])/1e9>max_witness_gap for a,b in zip(pts,pts[1:])):errs.append('WITNESS_GAP')
    formal=bool(not errs and external_elapsed is not None and external_elapsed>=target)
    prof=profile or cs.get('profile')
    if prof not in PROFILE_SECONDS:errs.append('PROFILE_UNKNOWN')
    required=PROFILE_SECONDS.get(prof,10**18)
    profile_complete=bool(formal and target>=required and external_elapsed is not None and external_elapsed>=required)
    claims={'formal_duration_complete':formal,'24h_completed':bool(profile_complete and prof=='24h' or formal and target>=86400 and external_elapsed>=86400),
            '72h_completed':bool(formal and target>=259200 and external_elapsed>=259200),'7day_completed':bool(formal and target>=604800 and external_elapsed>=604800)}
    return {'ok':not errs,'version':'v1015.1','schema':'tukuyo.v1015_1.authenticity_audit/1','errors':errs,'profile':prof,'target_seconds':target,
            'realtime_events':len(revs),'campaign_events':len(ce),'verified_witness_receipts':len(pts),'external_witness_elapsed_seconds':external_elapsed,
            'claim_boundary':{**claims,'self_reported_completion_flags_ignored':True,'witness_signatures_reverified':True,'source_event_chains_recomputed':True}}

def route_evaluate(evidence_files,witness_trust_file):
    results=[audit_bundle(p,witness_trust_file) for p in evidence_files]
    pass24=any(r.get('ok') and (r.get('claim_boundary') or {}).get('24h_completed') for r in results)
    pass72=any(r.get('ok') and (r.get('claim_boundary') or {}).get('72h_completed') for r in results)
    pass7=any(r.get('ok') and (r.get('claim_boundary') or {}).get('7day_completed') for r in results)
    return {'ok':all(r.get('ok') for r in results) and bool(results),'version':'v1015.1','results':results,'profile_pass':{'24h':pass24,'72h':pass72,'7d':pass7},
            'v1015_living_continuity_eligible':bool(pass24 and pass72),'seven_day_gate_closed':pass7,'automatic_promotion':False,
            'claim_boundary':{'eligibility_requires_reverified_raw_evidence':True,'eligibility_is_not_promotion':True}}
