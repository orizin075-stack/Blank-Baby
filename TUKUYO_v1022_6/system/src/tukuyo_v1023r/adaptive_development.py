"""Finite goals with a revisable model; no secret world/phase inputs."""
from __future__ import annotations
import copy
from .agent import ResearchAgent,free_inputs
from .development import GOALS,economics
POLICY='tukuyo.v1022_8_2.adaptive_goals/1'

def memory():
    return {'active':None,'switches':0,'failures':[],'revisions':0,'last_reset_seq':0,
            'completed':{g:0 for g in GOALS},'pending_shift':None,'blocked':{},'recent':[],'probe_conflicts':{}}

def working(agent,mem,locked,econ,energy):
    xs=[x for x in free_inputs(locked) if str(x) not in mem['blocked']]
    if not xs:return None,0.,float('-inf')
    x=max(xs,key=lambda x:(round(agent.p_on(x),9),-x));p=agent.p_on(x)
    return x,p,p*econ['reward']-econ['work']-econ['fail_penalty']*(1-p)-econ['base']

def experiment(agent,mem,locked,energy):
    gain=agent.table_gain if agent.method=='TABLE' else agent.info_gain
    xs=list(range(32))
    if energy<5500:
        feasible=[x for x in free_inputs(locked) if str(x) not in mem['blocked']]
        if feasible:xs=feasible
    need=max(0.,(5500-energy)/5500)
    return max(xs,key=lambda x:(round(gain(x)+need*.6*agent.p_on(x),9),-agent.count[x],-x))

def propose(agent,mem,energy,remaining,reservoir,locked,econ):
    e=economics(econ,reservoir,energy);x,p,net=working(agent,mem,locked,e,energy)
    need=max(0.,(7500-energy)/7500);can_probe=energy>e['base']+e['probe'] and remaining>1 and reservoir>0
    rows=[{'id':'rest','signals':{'survival':.25,'integrity':.1},'reason':'avoid_unprofitable_extra_cost','criterion':{'extra_cost':0}}]
    if mem['pending_shift'] and can_probe:
        rows.append({'id':'repair_prediction','signals':{'survival':1.5+4*need,'truthfulness':2.,'curiosity':.6},
                     'reason':'trusted_or_replicated_counterexample','criterion':{'retire_model_before_work':True}})
    else:
        if x is not None and energy>e['base']+e['work'] and net>0:
            rows.append({'id':'secure_energy','signals':{'survival':.65+4*need,'curiosity':.05,'truthfulness':.05,
                        'threat':(1-p) if energy<=e['base']+e['work']+e['fail_penalty'] else 0.},
                         'reason':'positive_total_energy_expectation','criterion':{'energy_at_least':7500}})
        if can_probe and agent.entropy_bits()>.1:
            rows.append({'id':'learn_rule','signals':{'curiosity':min(2.,agent.entropy_bits()/4)+.4,
                         'survival':1.2*need if net<=0 else .2*need,'truthfulness':.2},
                         'reason':'unresolved_model_or_unprofitable_action','criterion':{'entropy_reduction':.02}})
        if can_probe and energy>=6500 and (agent.rep is not None or agent.want_replication()):
            rows.append({'id':'verify_rule','signals':{'truthfulness':1.7,'curiosity':.6,'survival':-.3*need},
                         'reason':'replication_with_energy_reserve','criterion':{'status':'CONFIRMED'}})
        unresolved=[r for r in mem['failures'] if r['seq']>mem['last_reset_seq']]
        if can_probe and unresolved:
            rows.append({'id':'repair_prediction','signals':{'truthfulness':.9,'curiosity':.6,'survival':.3},
                         'reason':'retest_noisy_counterexample','criterion':{'retest_input':unresolved[-1]['x']}})
    if len(rows)==1:rows.append({'id':'secure_energy','signals':{'survival':-.5},'reason':'no_affordable_profitable_action','criterion':{'energy_at_least':7500}})
    return rows

def enact(agent,mem,goal,energy,remaining,reservoir,locked,econ,seq):
    if goal not in GOALS:raise ValueError('ADAPTIVE_UNKNOWN_GOAL')
    a=ResearchAgent.from_compact(copy.deepcopy(agent.to_compact()));reset=False
    if goal=='repair_prediction' and mem['pending_shift'] is not None:
        a=ResearchAgent(invent=agent.invent);reset=True
        for r in mem['recent']:
            if r['seq']>=mem['pending_shift']:a.observe(copy.deepcopy(r['observation']))
    if goal=='rest':return a,'rest',None,reset
    e=economics(econ,reservoir,energy)
    if goal=='secure_energy':
        x,p,net=working(a,mem,locked,e,energy)
        if mem['pending_shift'] is None and x is not None and energy>e['base']+e['work'] and net>0:return a,'work',x,reset
        return a,'rest',None,reset
    if energy<=e['base']+e['probe'] or remaining<=1 or reservoir<=0:return a,'rest',None,reset
    if goal=='verify_rule':
        if a.rep is None and a.want_replication():a.start_replication();a._advance_confirmation()
        if a.rep is not None:
            if a.rep['queue']:return a,'probe',a.rep['queue'][0],reset
            return a,'trial',None,reset
    unresolved=[r for r in mem['failures'] if r['seq']>mem['last_reset_seq']]
    if goal=='repair_prediction' and not reset and unresolved:return a,'probe',unresolved[-1]['x'],reset
    return a,'probe',experiment(a,mem,locked,energy),reset

def result_metrics(before,after,goal,observation,credit,prediction):
    from .development import result_metrics as base_metrics
    return base_metrics(before,after,goal,observation,credit,prediction)

def advance(mem,row):
    m=copy.deepcopy(mem);o=row['observation'];seq=row['seq']
    if m['active']!=row['goal']:m['switches']+=int(m['active'] is not None);m['active']=row['goal']
    if row['reset_model']:
        m['revisions']+=1;m['last_reset_seq']=seq;m['pending_shift']=None;m['failures']=[];m['probe_conflicts']={}
        m['recent']=[r for r in m['recent'] if r['seq']>=mem['pending_shift']]
    if o is not None:
        m['recent']=(m['recent']+[{'seq':seq,'observation':copy.deepcopy(o)}])[-32:];key=str(o['x'])
        if o['kind']=='work':
            if o['y']==0:m['blocked'][key]={'seq':seq,'positive_retests':0}
            else:m['blocked'].pop(key,None)
        elif key in m['blocked']:
            b=m['blocked'][key];b['positive_retests']=b['positive_retests']+1 if o['y'] else 0
            if b['positive_retests']>=2:m['blocked'].pop(key)
        if row['surprise']:
            m['failures']=(m['failures']+[{'seq':seq,'x':o['x'],'kind':o['kind']}])[-12:]
            if o['kind']=='work':m['pending_shift']=m['pending_shift'] or seq
            else:
                rec=m['probe_conflicts'].get(key,{'seq':seq,'y':o['y'],'count':0})
                if rec['y']==o['y']:rec['count']+=1
                else:rec={'seq':seq,'y':o['y'],'count':1}
                m['probe_conflicts'][key]=rec
                if rec['count']>=2:m['pending_shift']=m['pending_shift'] or rec['seq']
        elif row['goal']=='repair_prediction' and not row['reset_model']:
            m['failures']=[r for r in m['failures'] if r['x']!=o['x']];m['probe_conflicts'].pop(key,None)
    if row['progress']:m['completed'][row['goal']]+=1
    return m
