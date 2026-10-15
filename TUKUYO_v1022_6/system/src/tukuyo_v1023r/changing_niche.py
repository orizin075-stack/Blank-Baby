"""Environment-only changing-device backend and observation replay."""
from __future__ import annotations
import hashlib,copy
from . import niche
from .agent import ResearchAgent,switches
from .worlds import DeviceWorld
CLAIMS={'research_niche_in_real_metabolism':True,'lab_death_is_runtime_death':True,
        'inherits_only_provisional_public_observations':True,'agent_sees_world_secret':False,
        'agent_sees_change_schedule':False,'open_ended_real_world_research':False}
SCHEMA='tukuyo.v1022_8_2.changing_niche/1';ECON=niche.ECON

def scope(seed,niche_id,interval):
    return hashlib.sha256(f'adaptive-niche/1|{seed}|{niche_id}|{interval}|{niche.spec(seed,niche_id)}'.encode()).hexdigest()
def world(seed,niche_id,rid,counters,tick,interval):
    phase=(tick-1)//interval if interval else 0
    key=seed if phase==0 else hashlib.sha256(f'adaptive-phase|{seed}|{phase}'.encode()).hexdigest()
    tier,noise=niche.spec(seed,niche_id);w=DeviceWorld(key,'niche|'+niche_id,tier,noise,stream=rid)
    w.n_probe,w.n_trial,w.n_work=counters['probe'],counters['trial'],counters['work'];return w
def new_record(seed,family,niche_id,interval,born_at=0):
    return {'family':family,'niche':niche_id,'world_commitment':scope(seed,niche_id,interval),
            'agent':ResearchAgent().to_compact(),'counters':{'probe':0,'trial':0,'work':0},
            'public_observations_commitment':None,'born_at':born_at,
            'stats':{'probes':0,'trials':0,'works':0,'works_paid':0,'injuries':0,'rests':0}}
def validate(r):
    if (type(r) is not dict or set(r)!={'schema','claim_boundary','runtimes','econ'}
        or r['schema']!=SCHEMA or r['claim_boundary']!=CLAIMS or r['econ']!=ECON):raise ValueError('ADAPTIVE_NICHE_SCHEMA')
    if len(r['runtimes'])>64:raise ValueError('ADAPTIVE_NICHE_BOUND')
    for rec in r['runtimes'].values():
        if (type(rec['born_at']) is not int or not 0<=rec['born_at']<=4096 or len(rec['agent']['L1'])!=32
            or set(rec['counters'])!={'probe','trial','work'}
            or any(type(v) is not int or not 0<=v<=4096 for v in rec['counters'].values())):raise ValueError('ADAPTIVE_NICHE_RECORD')
def tick(data,seed,rec,rid,energy,remaining,reservoir,global_tick,interval,actions=True):
    from tukuyo_v1022 import adaptive_life as dev
    w=world(seed,rec['niche'],rid,rec['counters'],global_tick,interval);a=ResearchAgent.from_compact(copy.deepcopy(rec['agent']));offer=w.work_offer()
    prepared=dev.prepare(data,a,offer['locked'],energy,max(1,remaining),reservoir,{**ECON,'horizon':remaining},global_tick,enabled=actions)
    a=prepared['agent'];act=prepared['row']['action'];x=prepared['row']['input'];o=None;credit=extra=0
    row={'action':act,'status_before':a.status,'method':a.method}
    if act=='work':
        o=w.work(offer,x);extra=ECON['work'];a.observe(o);rec['stats']['works']+=1
        if o['y']:credit=min(ECON['reward'],reservoir,max(0,ECON['cap']-energy));rec['stats']['works_paid']+=int(credit>0)
        else:extra+=ECON['fail_penalty'];rec['stats']['injuries']+=1
        row.update({'switches':switches(x),'lamp':o['y']})
    else:
        w.skip_work(offer)
        if act=='probe':o=w.probe(x);extra=ECON['probe'];a.observe(o);rec['stats']['probes']+=1
        elif act=='trial':o=w.trial();extra=ECON['probe'];a.observe(o,prediction=a.predict_trial(o['x']));rec['stats']['trials']+=1
        else:rec['stats']['rests']+=1
        if o is not None:row.update({'switches':switches(o['x']),'sensor':o['y']})
    row['development']=dev.complete(data,prepared,a,o,credit,extra)
    rec['agent']=copy.deepcopy(a.to_compact());rec['counters']={'probe':w.n_probe,'trial':w.n_trial,'work':w.n_work}
    row.update({'status_after':a.status,'law':a.claim['law'] if a.claim else None});return act,credit,extra,row

_MEMO={}
def audit(data,seed,rec,rid,interval,use_memo=True):
    from tukuyo_v1022 import adaptive_life as dev
    s=dev.load(data);rows=dev.episodes(data,s)
    if any(r['global_tick']!=rec['born_at']+r['seq'] for r in rows):raise ValueError('ADAPTIVE_WORLD_TIME')
    if rec['world_commitment']!=scope(seed,rec['niche'],interval):raise ValueError('ADAPTIVE_WORLD_SCOPE')
    env=dev._seed(data,rec['world_commitment'])
    if rec['public_observations_commitment']!=(dev.whole.sha_obj(env) if env else None):raise ValueError('ADAPTIVE_PUBLIC_SEED_HEAD')
    if rows and s['last_agent']!=rec['agent']:raise ValueError('ADAPTIVE_OWNER_MODEL_BINDING')
    if not rows and s['initial_agent']!=rec['agent']:raise ValueError('ADAPTIVE_INITIAL_MODEL_BINDING')
    jb=dev.journal(data).read_bytes() if dev.journal(data).exists() else b''
    key=(rec['world_commitment'],rid,s['individual_id']);cached=_MEMO.get(key) if use_memo else None
    count=0;counters={'probe':0,'trial':0,'work':0}
    if cached and jb.startswith(cached['journal']):count=cached['count'];counters=dict(cached['counters'])
    for r in rows[count:]:
        w=world(seed,rec['niche'],rid,counters,r['global_tick'],interval);offer=w.work_offer()
        if r['locked']!={str(k):v for k,v in offer['locked'].items()}:raise ValueError('ADAPTIVE_WORLD_OFFER')
        if r['action']=='work':obs=w.work(offer,r['input'])
        else:
            w.skip_work(offer);obs=w.probe(r['input']) if r['action']=='probe' else w.trial() if r['action']=='trial' else None
        if obs!=r['observation']:raise ValueError('ADAPTIVE_WORLD_OBSERVATION')
        counters={'probe':w.n_probe,'trial':w.n_trial,'work':w.n_work}
    if counters!=rec['counters']:raise ValueError('ADAPTIVE_WORLD_COUNTERS')
    stats={'probes':0,'trials':0,'works':0,'works_paid':0,'injuries':0,'rests':0}
    for r in rows:
        stats[{'probe':'probes','trial':'trials','work':'works','rest':'rests'}[r['action']]]+=1
        if r['action']=='work':stats['works_paid']+=int(r['credit']>0);stats['injuries']+=int(not r['observation']['y'])
    if stats!=rec['stats']:raise ValueError('ADAPTIVE_WORLD_STATS')
    if len(_MEMO)>128:_MEMO.clear()
    _MEMO[key]={'count':len(rows),'journal':jb,'counters':counters};return True
def audit_seed(child_data,parent_data,commitment):
    from tukuyo_v1022 import adaptive_life as dev
    env=dev._seed(child_data,commitment)
    if env is None:return True
    if env['payload']!=dev.seed_payload(parent_data,dev.whole._live_identity(child_data)['individual_id'],commitment):raise ValueError('ADAPTIVE_PUBLIC_PARENT_JOURNAL')
    return True
def summary(r,seed=None,tick=1,interval=0):
    rows={}
    for rid,rec in r['runtimes'].items():
        a=rec['agent'];rows[rid]={'family':rec['family'],'niche':rec['niche'],'status':a['status'],'method':a['method'],
          'law':a['claim']['law'] if a['claim'] else None,'public_observations_commitment':rec['public_observations_commitment'],**rec['stats']}
        if seed is not None:
            w=world(seed,rec['niche'],'audit',{'probe':0,'trial':0,'work':0},max(1,tick),interval)
            rows[rid]['niche_truth_for_owner']={'tier':w.tier,'noise':w.noise,'phase':(max(1,tick)-1)//interval if interval else 0}
            if a['claim']:rows[rid]['law_correct_for_owner']=a['claim']['table']==w.reveal()['table']
    return rows
