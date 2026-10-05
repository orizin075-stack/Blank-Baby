from __future__ import annotations
import hashlib, json, os, time
from pathlib import Path
from statistics import mean
from tukuyo_common.atomic_fs import atomic_write_json, atomic_write_bytes
from tukuyo_v977.whole_state import audit as whole_audit, canon, sha_obj, sync as whole_sync
from tukuyo_v1013.realtime_continuity import (
    start as realtime_start, tick as realtime_tick, audit as realtime_audit,
    witness_request as realtime_witness_request, export_anchor as realtime_export_anchor,
    state_path as realtime_state_path,
)
from tukuyo_v1014.recovery import create_checkpoint, status as recovery_status, audit_checkpoint

SCHEMA='tukuyo.v1014_3.long_run_campaign/1'
EVENT_SCHEMA='tukuyo.v1014_3.campaign_event/1'
EVIDENCE_SCHEMA='tukuyo.v1014_3.campaign_evidence/1'
PROFILES={'24h':86400,'72h':259200,'7d':604800}
ZERO='0'*64

def root(data): return Path(data)/'v1014_3'
def state_path(data): return root(data)/'CAMPAIGN.json'
def events_dir(data): return root(data)/'events'
def requests_dir(data): return root(data)/'witness_requests'
def anchors_dir(data): return root(data)/'anchors'

def _read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def _sha_file(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest() if Path(p).is_file() else None

def _process_rss_bytes():
    p=Path('/proc/self/status')
    if p.is_file():
        for line in p.read_text(errors='ignore').splitlines():
            if line.startswith('VmRSS:'):
                try:return int(line.split()[1])*1024
                except Exception:return None
    try:
        import resource
        v=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(v*(1024 if os.name!='darwin' else 1))
    except Exception:return None

def _data_bytes(data):
    total=0;files=0
    for p in Path(data).rglob('*'):
        if p.is_file():
            try: total+=p.stat().st_size;files+=1
            except OSError: pass
    return total,files

def _resource_sample(data):
    total,files=_data_bytes(data)
    try:load1=os.getloadavg()[0]
    except Exception:load1=None
    return {'rss_bytes':_process_rss_bytes(),'data_bytes':total,'data_files':files,'load1':load1,'sampled_utc_ns':time.time_ns()}

def _scan_events(data):
    out=[]
    d=events_dir(data)
    if not d.is_dir():return out
    for p in sorted(d.glob('*.json')):
        try:out.append(_read(p))
        except Exception:out.append({'_malformed':p.name})
    return out

def _append_event(data,kind,detail=None):
    data=Path(data);d=events_dir(data);d.mkdir(parents=True,exist_ok=True)
    evs=_scan_events(data);seq=len(evs)+1;prev=ZERO if not evs else sha_obj(evs[-1])
    ev={'schema':EVENT_SCHEMA,'seq':seq,'kind':kind,'utc_ns':time.time_ns(),'pid':os.getpid(),'previous_event_sha256':prev,'detail':detail or {}}
    atomic_write_json(d/f'{seq:08d}.json',ev)
    return ev

def _rebuild_state_head(data,st):
    evs=_scan_events(data);st=dict(st);st['event_count']=len(evs);st['event_head_sha256']=ZERO if not evs else sha_obj(evs[-1]);atomic_write_json(state_path(data),st);return st

def _next_due(st,key,default):
    v=st.get(key);return int(v if v is not None else default)

def start(data,profile='24h',target_seconds=None,tick_seconds=300,checkpoint_seconds=3600,note=''):
    data=Path(data)
    if state_path(data).exists(): raise ValueError('CAMPAIGN_ALREADY_EXISTS')
    if profile not in PROFILES and target_seconds is None:raise ValueError('UNKNOWN_CAMPAIGN_PROFILE')
    target=PROFILES.get(profile) if target_seconds is None else int(target_seconds)
    tick_seconds=max(1,int(tick_seconds));checkpoint_seconds=max(1,int(checkpoint_seconds))
    if target<1:raise ValueError('CAMPAIGN_TARGET_MIN_1S')
    if realtime_state_path(data).exists():
        rt=_read(realtime_state_path(data))
        if int(rt.get('target_seconds',-1))!=target:raise ValueError('EXISTING_REALTIME_TARGET_MISMATCH')
        run_id=rt['run_id']
    else:
        rr=realtime_start(data,profile,target,note or 'long-run-campaign-start');run_id=rr['run_id'];whole_sync(data)
    cp=create_checkpoint(data,'campaign-start')
    reqd=requests_dir(data);reqd.mkdir(parents=True,exist_ok=True);anchd=anchors_dir(data);anchd.mkdir(parents=True,exist_ok=True)
    sreq=reqd/'start_request.json';realtime_witness_request(data,sreq)
    anchor=anchd/'start_anchor.json';realtime_export_anchor(data,anchor)
    now=time.time_ns();st={'schema':SCHEMA,'version':'v1014.3','profile':profile,'target_seconds':target,'run_id':run_id,
      'created_utc_ns':now,'tick_seconds':tick_seconds,'checkpoint_seconds':checkpoint_seconds,
      'last_tick_utc_ns':now,'last_checkpoint_utc_ns':now,'steps':0,'checkpoints':1,'restart_observations':0,
      'crash_recovery_observations':0,'event_count':0,'event_head_sha256':ZERO,
      'start_checkpoint':str(cp.get('path')),'start_witness_request':str(sreq),'start_anchor':str(anchor),
      'claim_boundary':{'local_wall_clock_not_formal_duration_proof':True,'external_witness_pair_required':True,
       '24h_completed':False,'72h_completed':False,'7day_completed':False,'literal_life_established':False,'consciousness_established':False}}
    atomic_write_json(state_path(data),st)
    ev=_append_event(data,'CAMPAIGN_START',{'run_id':run_id,'checkpoint':cp.get('path'),'resource':_resource_sample(data),'note':str(note)[:240]})
    st=_rebuild_state_head(data,st)
    return {'ok':True,'version':'v1014.3','run_id':run_id,'profile':profile,'target_seconds':target,'campaign_event_seq':ev['seq'],
      'start_witness_request':str(sreq),'start_anchor':str(anchor),'checkpoint':cp.get('path')}

def step(data,note='',force_checkpoint=False,startup_recovery=None):
    data=Path(data)
    if not state_path(data).is_file():raise ValueError('CAMPAIGN_MISSING')
    st=_read(state_path(data));rt_before=realtime_audit(data,subaudits=True)
    if not rt_before.get('ok'):raise ValueError('CAMPAIGN_REALTIME_PRECHECK:'+','.join(rt_before.get('errors',[])[:3]))
    now=time.time_ns();elapsed_since_tick=(now-int(st.get('last_tick_utc_ns',now)))/1e9
    # A manual step is itself a heartbeat even when called sooner than the planned cadence.
    tick=realtime_tick(data,note or f'campaign-step-{int(st.get("steps",0))+1}');whole_sync(data)
    now2=time.time_ns();do_cp=bool(force_checkpoint or (now2-int(st.get('last_checkpoint_utc_ns',now2)))/1e9>=_next_due(st,'checkpoint_seconds',3600))
    cp=None
    if do_cp:
        cp=create_checkpoint(data,f'campaign-step-{int(st.get("steps",0))+1}')
    actions=list((startup_recovery or {}).get('actions',[]) or [])
    crash_actions=[a for a in actions if any(k in a for k in ('RESTORE','CHECKPOINT','REALTIME','PENDING','ORPHAN'))]
    detail={'note':str(note)[:240],'realtime_tick':tick,'checkpoint':cp.get('path') if cp else None,
      'startup_recovery_actions':actions,'resource':_resource_sample(data),'whole_audit_ok':bool(whole_audit(data).get('ok')),
      'elapsed_since_previous_step_seconds':round(elapsed_since_tick,6)}
    ev=_append_event(data,'CAMPAIGN_STEP',detail)
    st['steps']=int(st.get('steps',0))+1;st['last_tick_utc_ns']=now2
    if cp:st['checkpoints']=int(st.get('checkpoints',0))+1;st['last_checkpoint_utc_ns']=now2
    if tick.get('process_instance_id'):st['restart_observations']=int(st.get('restart_observations',0))+1
    if crash_actions:st['crash_recovery_observations']=int(st.get('crash_recovery_observations',0))+1
    st=_rebuild_state_head(data,st)
    a=realtime_audit(data)
    return {'ok':bool(a.get('ok')),'version':'v1014.3','run_id':st['run_id'],'step':st['steps'],'campaign_event_seq':ev['seq'],
      'checkpoint_created':bool(cp),'startup_recovery_actions':actions,'realtime_events':a.get('events'),'distinct_process_instances':a.get('distinct_process_instances'),
      'local_elapsed_seconds':a.get('local_elapsed_seconds')}

def end_request(data,out=None):
    data=Path(data)
    if not state_path(data).is_file():raise ValueError('CAMPAIGN_MISSING')
    if out is None:out=requests_dir(data)/'end_request.json'
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True);r=realtime_witness_request(data,out)
    ev=_append_event(data,'END_WITNESS_REQUEST',{'path':str(out),'request_sha256':r.get('request_sha256')})
    st=_rebuild_state_head(data,_read(state_path(data)))
    return {'ok':True,'version':'v1014.3','path':str(out),'campaign_event_seq':ev['seq'],'request_sha256':r.get('request_sha256')}

def audit(data,start_witness=None,end_witness=None,witness_trust_file=None,require_complete=False):
    data=Path(data);errs=[]
    if not state_path(data).is_file():return {'ok':False,'version':'v1014.3','errors':['CAMPAIGN_MISSING']}
    st=_read(state_path(data));evs=_scan_events(data);prev=ZERO;resources=[]
    for i,ev in enumerate(evs,1):
        if ev.get('_malformed'):errs.append('CAMPAIGN_EVENT_MALFORMED:'+str(ev['_malformed']));continue
        if ev.get('schema')!=EVENT_SCHEMA or ev.get('seq')!=i:errs.append(f'CAMPAIGN_EVENT_SCHEMA_SEQ:{i}')
        if ev.get('previous_event_sha256')!=prev:errs.append(f'CAMPAIGN_EVENT_CHAIN:{i}')
        prev=sha_obj(ev)
        r=(ev.get('detail') or {}).get('resource')
        if isinstance(r,dict):resources.append(r)
    if st.get('event_count')!=len(evs) or st.get('event_head_sha256')!=prev:errs.append('CAMPAIGN_STATE_HEAD_MISMATCH')
    rt=realtime_audit(data,start_witness=start_witness,end_witness=end_witness,witness_trust_file=witness_trust_file,require_complete=require_complete)
    if not rt.get('ok'):errs.extend('REALTIME:'+x for x in rt.get('errors',[]))
    wa=whole_audit(data)
    if not wa.get('ok'):errs.append('WHOLE_AUDIT')
    rs=recovery_status(data)
    bad_cp=[]
    for row in rs.get('checkpoints',[]):
        if not row.get('ok'):bad_cp.append(row.get('path') or row.get('checkpoint_id'))
    if bad_cp:errs.append('RECOVERY_CHECKPOINT_AUDIT')
    rss=[x.get('rss_bytes') for x in resources if isinstance(x.get('rss_bytes'),int)]
    db=[x.get('data_bytes') for x in resources if isinstance(x.get('data_bytes'),int)]
    complete=bool(rt.get('externally_anchored_complete'))
    profile=st.get('profile')
    claims={'24h_completed':bool(complete and int(st['target_seconds'])>=86400),'72h_completed':bool(complete and int(st['target_seconds'])>=259200),
      '7day_completed':bool(complete and int(st['target_seconds'])>=604800),'formal_duration_complete':complete,
      'local_clock_alone_is_not_formal_proof':True,'literal_life_established':False,'consciousness_established':False}
    return {'ok':not errs,'version':'v1014.3','errors':errs,'run_id':st['run_id'],'profile':profile,'target_seconds':st['target_seconds'],
      'campaign_events':len(evs),'steps':st.get('steps',0),'checkpoints':st.get('checkpoints',0),'crash_recovery_observations':st.get('crash_recovery_observations',0),
      'realtime':rt,'recovery_checkpoint_count':rs.get('count',0),'whole_audit_ok':wa.get('ok',False),
      'resource_summary':{'samples':len(resources),'rss_peak_bytes':max(rss) if rss else None,'rss_mean_bytes':int(mean(rss)) if rss else None,
         'data_peak_bytes':max(db) if db else None,'data_last_bytes':db[-1] if db else None},'claim_boundary':claims}

def evidence(data,out,start_witness=None,end_witness=None,witness_trust_file=None,require_complete=False):
    data=Path(data);out=Path(out);a=audit(data,start_witness,end_witness,witness_trust_file,require_complete)
    st=_read(state_path(data));evs=_scan_events(data)
    rt_events=Path(data)/'v1013'/'REALTIME_EVENTS.jsonl'
    obj={'schema':EVIDENCE_SCHEMA,'version':'v1014.3','generated_utc_ns':time.time_ns(),'campaign_state':st,'campaign_events':evs,
      'audit':a,'bindings':{'realtime_events_sha256':_sha_file(rt_events),'realtime_state_sha256':_sha_file(realtime_state_path(data)),
      'whole_state_sha256':_sha_file(Path(data)/'state'/'integration_state.json')},
      'claim_boundary':{'evidence_bundle_is_locally_generated':True,'formal_time_claim_requires_verified_external_witness_pair':True,
       'third_party_reproduction':False,'external_H4':'PENDING'}}
    obj['bundle_sha256']=sha_obj(obj);atomic_write_bytes(out,canon(obj)+b'\n')
    return {'ok':a.get('ok',False),'version':'v1014.3','out':str(out),'bundle_sha256':obj['bundle_sha256'],'audit':a}

def status(data):return audit(data)
