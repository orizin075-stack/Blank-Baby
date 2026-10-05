"""Energy ecology for the V1023r research preview (claude-patch5).

One organism lives in one hidden-rule world for a fixed horizon.  Each tick it
does exactly one thing: run an experiment, run a replication trial, work, or
rest.  Experiments cost energy and pay nothing directly; work pays only when
the TRUE lamp turns on.  Energy that reaches zero is death.  Every unit of
energy is booked in a ledger whose conservation is checked.

Policies compared on the same worlds:
  research        the open-world agent; experiments chosen by information gain,
                  research continues only while its value exceeds its cost
  random_research same agent and same stopping rule, experiments chosen at random
  doing           same beliefs, never experiments: learns only from work outcomes
  naive           works every tick with random free switches, learns nothing
  oracle          knows the law (upper bound; not a learner)
"""
from __future__ import annotations
import random
from .worlds import DeviceWorld,INPUTS,bit
from .agent import ResearchAgent,free_inputs

ECON={'start':40,'base':1,'probe':1,'work':3,'reward':8,'fail_penalty':0,'horizon':120,'cap':200}
REGIMES={'safe_failure':ECON,'costly_failure':{**ECON,'fail_penalty':6}}
POLICIES=('research','random_research','doing','naive','oracle')

class Ledger:
    def __init__(self,start):self.start=start;self.energy=start;self.income=0;self.spent=0;self.rows=[]
    def book(self,tick,kind,amount):
        if amount>=0:self.income+=amount
        else:self.spent+=-amount
        self.energy+=amount;self.rows.append((tick,kind,amount))
    def cap(self,tick,cap):
        if self.energy>cap:self.book(tick,'overflow_discarded',cap-self.energy)
    def check(self):
        return self.start+self.income-self.spent==self.energy and sum(a for _,_,a in self.rows)==self.energy-self.start

def run_episode(world,policy,econ=ECON,seed=0,journal=None,prior_claim=None):
    rng=random.Random(f'policy|{policy}|{seed}');led=Ledger(econ['start']);agent=None if policy in ('naive','oracle') else ResearchAgent(choose='random' if policy=='random_research' else 'info_gain',prior_claim=prior_claim)
    truth=world.reveal()['table'] if policy=='oracle' else None
    actions={'probe':0,'trial':0,'work':0,'rest':0};earned=0;alive=True;death_tick=None
    for tick in range(econ['horizon']):
        offer=world.work_offer();remaining=econ['horizon']-tick;act='rest';detail=None
        led.book(tick,'base',-econ['base'])
        if led.energy<=0:alive=False;death_tick=tick;break
        if policy=='oracle':
            xs=[x for x in free_inputs(offer['locked']) if bit(truth,x)]
            act,x=('work',xs[0]) if xs and led.energy>econ['work']+econ['fail_penalty'] else ('rest',None)
        elif policy=='naive':
            xs=free_inputs(offer['locked']);act,x=('work',xs[int(rng.random()*len(xs))]) if led.energy>econ['work']+econ['fail_penalty'] else ('rest',None)
        else:
            act,x,_sc=agent.decide(offer['locked'],led.energy,remaining,econ,science=True,experiments=policy!='doing',rng=rng)
        if act=='work':
            o=world.work(offer,x);led.book(tick,'work_cost',-econ['work'])
            if o['y']:led.book(tick,'work_reward',econ['reward']);earned+=1
            elif econ.get('fail_penalty'):led.book(tick,'work_failure_injury',-econ['fail_penalty'])
            if agent:agent.observe(o)
        else:
            world.skip_work(offer)
            if act=='probe':
                o=world.probe(x);led.book(tick,'probe_cost',-econ['probe']);agent.observe(o)
            elif act=='trial':
                o=world.trial();pred=agent.predict_trial(o['x']);led.book(tick,'trial_cost',-econ['probe']);agent.observe(o,prediction=pred)
        actions[act]+=1;led.cap(tick,econ['cap'])
        if journal is not None:journal.append({'tick':tick,'action':act,'energy':led.energy,**({'report':agent.report()} if agent and act in ('probe','trial') and tick%5==0 else {})})
        if led.energy<=0:alive=False;death_tick=tick;break
    rv=world.reveal();res={'policy':policy,'alive':alive,'death_tick':death_tick,'final_energy':led.energy,'actions':actions,'successful_work':earned,
        'ledger_conserved':led.check(),'world':{'tier':rv['tier'],'noise':rv['noise']}}
    if agent:
        rep=agent.report();res['claim']=claim_full=agent.claim;res['status']=agent.status;res['method']=agent.method;res['events']=[e['event'] for e in agent.events]
        claim=agent.claim
        res['law_claimed']=claim is not None
        res['law_correct']=bool(claim and claim['table']==rv['table'])
        res['wrong_law_claimed']=bool(claim and claim['table']!=rv['table'])
        res['claim_bound_held']=None if not claim else world.true_agreement(claim['table'])>=claim['claimed_min_agreement_99']
        res['unexplained']=agent.method=='TABLE'
        res['report']=rep
    return res
