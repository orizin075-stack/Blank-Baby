from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path

SCHEMA='tukuyo.v967.integrated_ledger/1'

def canon(o):
    return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()

def sha(o):
    return hashlib.sha256(canon(o)).hexdigest()

def root(data): return Path(data)/'research_v967'
def ledger_path(data): return root(data)/'INTEGRATED_LEDGER.json'
def family_registry_path(data): return root(data)/'FAMILY_REGISTRY.json'

def load_ledger(data):
    p=ledger_path(data)
    if not p.exists(): return {'schema':SCHEMA,'events':[]}
    x=json.loads(p.read_text(encoding='utf-8'))
    if x.get('schema')!=SCHEMA or not isinstance(x.get('events'),list): raise ValueError('V967_LEDGER_SCHEMA')
    prev='0'*64
    for i,e in enumerate(x['events']):
        if e.get('seq')!=i+1 or e.get('prev_sha256')!=prev: raise ValueError('V967_LEDGER_CHAIN')
        body={k:v for k,v in e.items() if k!='event_sha256'}
        if e.get('event_sha256')!=sha(body): raise ValueError('V967_LEDGER_HASH')
        prev=e['event_sha256']
    return x

def append_event(data,kind,payload):
    x=load_ledger(data); prev=x['events'][-1]['event_sha256'] if x['events'] else '0'*64
    e={'seq':len(x['events'])+1,'kind':str(kind),'timestamp_utc':datetime.now(timezone.utc).isoformat(),'payload_sha256':sha(payload),'payload':payload,'prev_sha256':prev}
    e['event_sha256']=sha(e)
    x['events'].append(e);p=ledger_path(data);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(x)+b'\n')
    try:
        if (Path(data)/'state'/'integration_state.json').is_file():
            from tukuyo_v977.whole_state import sync as _whole_sync
            _whole_sync(data)
    except ImportError:
        pass
    return e

def save_family(data,proposal,evaluator_summary,promotion_summary):
    p=family_registry_path(data);p.parent.mkdir(parents=True,exist_ok=True)
    s={'schema':'tukuyo.v967.family_registry/1','entries':[]}
    if p.exists(): s=json.loads(p.read_text(encoding='utf-8'))
    cid=proposal['candidate_sha256']
    if any(e.get('candidate_sha256')==cid for e in s['entries']): raise ValueError('DUPLICATE_FAMILY_PROMOTION')
    e={'candidate_sha256':cid,'proposal':proposal,'evaluator_summary':evaluator_summary,'promotion_summary':promotion_summary,'status':'ACTIVE_BOUNDED_FAMILY'}
    s['entries'].append(e);p.write_bytes(canon(s)+b'\n');return e

def family_eval(data,candidate_sha256,a,b):
    from tukuyo_v965.family_synthesis import evaluate
    p=family_registry_path(data)
    if not p.exists(): raise ValueError('FAMILY_REGISTRY_MISSING')
    s=json.loads(p.read_text(encoding='utf-8'));xs=[e for e in s.get('entries',[]) if e.get('candidate_sha256')==candidate_sha256 and e.get('status')=='ACTIVE_BOUNDED_FAMILY']
    if len(xs)!=1: raise ValueError('FAMILY_NOT_ACTIVE')
    return {'status':'RESOLVED_V967_FAMILY','candidate_sha256':candidate_sha256,'answer':evaluate(xs[0]['proposal'],int(a),int(b))}

def system_status(data,base_status=None):
    data=Path(data); led=load_ledger(data)
    counts={}
    for e in led['events']: counts[e['kind']]=counts.get(e['kind'],0)+1
    fam=0
    fp=family_registry_path(data)
    if fp.exists(): fam=len(json.loads(fp.read_text(encoding='utf-8')).get('entries',[]))
    inherited=0; ip=data/'inherited_research_v962'/'PUBLIC_CAPABILITIES.json'
    if ip.exists(): inherited=len(json.loads(ip.read_text(encoding='utf-8')).get('entries',[]))
    prim=0; pp=data/'research_registry_v958'/'ACTIVE_PRIMITIVES.json'
    if pp.exists(): prim=len(json.loads(pp.read_text(encoding='utf-8')).get('entries',[]))
    return {'ok':True,'version':'v977','integration':'V977_WHOLE_INDIVIDUAL_INTEGRATION','individual_initialized':(data/'state/integration_state.json').is_file(),
            'base_status':base_status,'integrated_event_count':len(led['events']),'event_counts':counts,'active_v967_families':fam,'inherited_public_capabilities':inherited,
            'v958_registry_entries':prim,'authority_private_keys_in_runtime':False,'general_l5':False,'general_l6':False}
