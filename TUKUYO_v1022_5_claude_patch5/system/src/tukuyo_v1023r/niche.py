"""Research niche inside the REAL metabolism (claude-patch5, opt-in: metabolism-init --research-world).

Each family lives next to one hidden-rule device (its niche).  Every tick each
living runtime's research agent proposes probe / trial / work / rest; the
runtime's own Heart accepts it or rests; the outcome moves real energy:
  * work pays from the shared reservoir only when the true lamp turns on,
  * a failed work attempt is an injury (burned energy),
  * experiments burn energy and pay nothing directly.
Energy exhaustion is the runtime's real, irreversible death (organism2), and a
successor of the same family may inherit the parent's CONFIRMED law (public
knowledge only) when the ecology was started with learning enabled.

The world secret is derived from the ecology's owner seed; the agent receives
observations only.
"""
from __future__ import annotations
import hashlib
from .worlds import DeviceWorld,_u
from .agent import ResearchAgent,switches

ECON={'start':6500,'base':300,'probe':150,'work':300,'reward':1400,'fail_penalty':700,'cap':10000,'science_at':0.6}
CLAIMS={'research_niche_in_real_metabolism':True,'lab_death_is_runtime_death':True,'inherits_only_confirmed_public_laws':True,
        'agent_sees_world_secret':False,'open_ended_real_world_research':False}

def spec(seed,niche):
    tier=1+int(_u(seed,'niche-tier|'+niche,0)*4);noise=(0.0,0.05,0.1)[int(_u(seed,'niche-noise|'+niche,0)*3)]
    return tier,noise
def world(seed,niche,rid,counters):
    tier,noise=spec(seed,niche);w=DeviceWorld(seed,'niche|'+niche,tier,noise,stream=rid)
    w.n_probe,w.n_trial,w.n_work=counters['probe'],counters['trial'],counters['work'];return w
def new_record(seed,family,niche,inherited_claim=None):
    """niche: N0, N1, ... in founder order; a successor lives in its parent's niche (same seed -> same niches)."""
    a=ResearchAgent(prior_claim=inherited_claim)
    return {'family':family,'niche':niche,'world_commitment':hashlib.sha256(f'v1023r-niche|{seed}|{niche}|{spec(seed,niche)}'.encode()).hexdigest(),
            'agent':a.to_compact(),'counters':{'probe':0,'trial':0,'work':0},'inherited_law':inherited_claim['law'] if inherited_claim else None,
            'stats':{'probes':0,'trials':0,'works':0,'works_paid':0,'injuries':0,'rests':0}}
def validate(r):
    if type(r) is not dict or set(r)!={'schema','claim_boundary','runtimes','econ'} or r['claim_boundary']!=CLAIMS or r['econ']!=ECON:raise ValueError('V1023R_NICHE_SCHEMA')
    if len(r['runtimes'])>64:raise ValueError('V1023R_NICHE_BOUND')
    for rec in r['runtimes'].values():
        if len(rec['agent']['L1'])!=32 or any(type(v) is not int or v<0 for v in rec['counters'].values()):raise ValueError('V1023R_NICHE_RECORD')
def tick(seed,rec,rid,energy,remaining,heart_choose,reservoir):
    """One real tick for one runtime. Returns (action,credit,extra_cost,row,heart_feedback_ok)."""
    w=world(seed,rec['niche'],rid,rec['counters']);a=ResearchAgent.from_compact(rec['agent']);offer=w.work_offer()
    econ={**ECON,'horizon':remaining}
    act,x,sc=a.decide(offer['locked'],energy,max(1,remaining),econ)
    er=energy/10000
    if act=='work':sig={'survival':sc.get('work_ev',0)/300,'curiosity':.1*er}
    elif act in ('probe','trial'):sig={'curiosity':1.0*er+.2,'survival':.15,'truthfulness':.2 if act=='trial' else 0}
    else:sig={'survival':.2}
    chosen=heart_choose([{'id':act if act!='rest' else 'idle','signals':sig},{'id':'rest','signals':{'survival':.3 if sc.get('work_ev',0)<0 and act=='work' else 0.,'integrity':.1}}])
    if chosen=='rest':act='rest'
    credit=0;extra=0;row={'action':act,'agent_status':a.status}
    if act=='work':
        o=w.work(offer,x);extra=ECON['work'];a.observe(o);rec['stats']['works']+=1
        if o['y']:credit=min(ECON['reward'],reservoir,max(0,10000-energy));rec['stats']['works_paid']+=1
        else:extra+=ECON['fail_penalty'];rec['stats']['injuries']+=1
        row.update({'switches':switches(x),'lamp':o['y']})
    else:
        w.skip_work(offer)
        if act=='probe':o=w.probe(x);extra=ECON['probe'];a.observe(o);rec['stats']['probes']+=1;row.update({'switches':switches(x),'sensor':o['y']})
        elif act=='trial':o=w.trial();p=a.predict_trial(o['x']);extra=ECON['probe'];a.observe(o,prediction=p);rec['stats']['trials']+=1;row.update({'switches':switches(o['x']),'sensor':o['y'],'prediction':p})
        else:rec['stats']['rests']+=1
    rec['agent']=a.to_compact();rec['counters']={'probe':w.n_probe,'trial':w.n_trial,'work':w.n_work}
    row.update({'status_after':a.status,'law':a.claim['law'] if a.claim else None})
    return act,credit,extra,row
def summary(r,seed=None):
    rows={}
    for rid,rec in r['runtimes'].items():
        ag=rec['agent'];rows[rid]={'family':rec['family'],'niche':rec['niche'],'niche_truth_for_owner':None if seed is None else dict(zip(('tier','noise'),spec(seed,rec['niche']))),'status':ag['status'],'method':ag['method'],'law':ag['claim']['law'] if ag['claim'] else None,
            'inherited_law':rec['inherited_law'],**rec['stats']}
        if seed is not None and ag['claim']:
            rows[rid]['law_correct_for_owner']=ag['claim']['table']==world(seed,rec['niche'],'reveal',{'probe':0,'trial':0,'work':0}).reveal()['table']
    return rows
