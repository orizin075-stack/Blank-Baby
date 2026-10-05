"""Research expeditions of a live individual (V1023r preview, claude-patch5).

An expedition = one stay of `ticks` in one hidden-rule world with its own
energy ledger.  The individual's Heart picks the research temperament, the
open-world agent decides every tick, the result is committed into the
individual's signed state, and the Heart experiences the outcome.

Separation:
  * the world key lives in <data>/v1023r_world/ (environment side).  This
    module hands the agent only observation callables; agent.py never sees
    the key (tests check the import graph).
  * an expedition's death is the death of the expedition ledger, NOT of the
    individual.  Wiring it into the real metabolism is a later step.

Audit (research-audit):
  * the signed commit chain of the state (tukuyo_v1022.store),
  * every journal's hash chain and its head recorded in the state,
  * the world commitment made before the expedition started,
  * every recorded observation recomputed from the world key,
  * the agent replayed from the recorded observations reproduces the
    recorded beliefs, claims and decisions' inputs,
  * the energy ledger is conserved.
"""
from __future__ import annotations
import hashlib,json,os,secrets
from pathlib import Path
from tukuyo_common.atomic_fs import atomic_write_bytes,atomic_write_text
from tukuyo_v977 import whole_state as whole
from tukuyo_v1019.transaction import transactional
from tukuyo_v1022 import store
from .worlds import DeviceWorld,_u
from .agent import ResearchAgent,switches
from .ecology import REGIMES,Ledger

NS='v1023r';COMPONENT='open_world_research_v1023r';SCHEMA='tukuyo.v1023r.research/1';WORLD_DIR='v1023r_world'
CLAIMS_PATCH5={'hidden_rule_world_research':True,'experiments_chosen_by_information_value':True,'method_change_when_language_fails':True,
        'claims_only_after_replication':True,'expedition_death_is_individual_death':False,'open_ended_real_world_research':False,
        'consciousness_established':False}
# claude-patch6: the agent also builds laws from a fixed grammar written by the patch author; it does not invent new kinds of laws.
# A state written by patch5 is accepted and gets this boundary on its next save.
CLAIMS={**CLAIMS_PATCH5,'invents_laws_inside_a_fixed_grammar':True,'invents_new_kinds_of_laws':False}
TEMPERAMENTS={'thorough':{'science_at':0.5,'signals':{'curiosity':0.8,'truthfulness':0.6,'survival':-0.1}},
              'frugal':{'science_at':0.9,'signals':{'survival':0.7,'curiosity':0.1,'truthfulness':0.2}}}

def _validate(s):
    if s.get('schema')!=SCHEMA or s.get('claim_boundary') not in (CLAIMS,CLAIMS_PATCH5):raise ValueError('V1023R_SCHEMA')
    if type(s.get('expeditions')) is not list or len(s['expeditions'])>512:raise ValueError('V1023R_BOUND')
    if type(s.get('laws')) is not dict or len(s['laws'])>64:raise ValueError('V1023R_LAWS')
def _default(data):
    return {'schema':SCHEMA,'individual_id':whole._live_identity(data)['individual_id'],'expeditions':[],'laws':{},'claim_boundary':CLAIMS}
def state(data):
    if not (Path(data)/NS/'commits').exists():return _default(data)
    return store.load(data,NS,COMPONENT,_validate)
def _world_key(data,create=False):
    p=Path(data)/WORLD_DIR/'WORLD_KEY'
    if not p.exists():
        if not create:raise ValueError('V1023R_WORLD_KEY_MISSING')
        atomic_write_text(p,secrets.token_hex(32),mode=0o600)
    return p.read_text().strip()
def _world_spec(key,world_id):
    tier=1+int(_u(key,'spec-tier|'+world_id,0)*4);noise=(0.0,0.05,0.1)[int(_u(key,'spec-noise|'+world_id,0)*3)]
    return tier,noise
def _commitment(key,world_id,tier,noise):
    return hashlib.sha256(f'v1023r-world|{key}|{world_id}|{tier}|{noise}'.encode()).hexdigest()
def _journal_path(data,eid):return Path(data)/NS/'journal'/f'{eid}.jsonl'
def _write_journal(data,eid,rows):
    prev='0'*64;lines=[]
    for r in rows:
        rec={'prev':prev,**r};prev=hashlib.sha256(whole.canon(rec)).hexdigest();lines.append(whole.canon(rec).decode())
    atomic_write_bytes(_journal_path(data,eid),('\n'.join(lines)+'\n').encode());return prev
def _read_journal(data,eid):
    rows=[];prev='0'*64
    for line in _journal_path(data,eid).read_text().splitlines():
        rec=json.loads(line)
        if rec.get('prev')!=prev:raise ValueError('V1023R_JOURNAL_CHAIN:'+eid)
        prev=hashlib.sha256(whole.canon(rec)).hexdigest();rows.append(rec)
    return rows,prev

def _expedition(world,agent,econ,science_at,journal):
    """The tick loop shared by run() and the replay audit."""
    led=Ledger(econ['start']);alive=True;death=None;econ={**econ,'science_at':science_at}
    for tick in range(econ['horizon']):
        offer=world.work_offer();led.book(tick,'base',-econ['base'])
        if led.energy<=0:alive=False;death=tick;journal.append({'tick':tick,'action':'death','energy':led.energy});break
        act,x,sc=agent.decide(offer['locked'],led.energy,econ['horizon']-tick,econ)
        row={'tick':tick,'locked':{str(k):v for k,v in offer['locked'].items()},'action':act,'scores':sc}
        if act=='work':
            o=world.work(offer,x);led.book(tick,'work_cost',-econ['work'])
            if o['y']:led.book(tick,'work_reward',econ['reward'])
            elif econ.get('fail_penalty'):led.book(tick,'work_failure_injury',-econ['fail_penalty'])
            agent.observe(o);row['obs']=o
        else:
            world.skip_work(offer)
            if act=='probe':o=world.probe(x);led.book(tick,'probe_cost',-econ['probe']);agent.observe(o);row['obs']=o
            elif act=='trial':
                o=world.trial();pred=agent.predict_trial(o['x']);led.book(tick,'trial_cost',-econ['probe']);agent.observe(o,prediction=pred);row['obs']=o;row['prediction']=pred
        led.cap(tick,econ['cap']);row['energy']=led.energy;row['status']=agent.status
        if agent.events and (len(journal)==0 or journal[-1].get('n_events')!=len(agent.events)):row['event']=agent.events[-1]
        row['n_events']=len(agent.events);journal.append(row)
        if led.energy<=0:alive=False;death=tick;break
    return led,alive,death

@transactional()
def run(data,world_id='W1',ticks=120,regime='costly_failure',tier=None,noise=None):
    if regime not in REGIMES:raise ValueError('V1023R_REGIME')
    if type(ticks) is not int or not 10<=ticks<=400:raise ValueError('V1023R_TICKS')
    if not world_id.isalnum() or len(world_id)>16:raise ValueError('V1023R_WORLD_ID')
    from tukuyo_v978 import heart_loop
    s=state(data);key=_world_key(data,create=True)
    t0,n0=_world_spec(key,world_id);tier=tier or t0;noise=n0 if noise is None else noise
    eid=f"E{len(s['expeditions'])+1:06d}";commit=_commitment(key,world_id,tier,noise)
    # The Heart (soul values + emotion) chooses how this individual does research.
    choice=heart_loop.choose(data,[{'id':k,'signals':v['signals']} for k,v in TEMPERAMENTS.items()],context=f'v1023r-{eid}')['chosen']
    prior=s['laws'].get(world_id)
    world=DeviceWorld(key,world_id,tier,noise,stream=eid)
    agent=ResearchAgent(prior_claim=prior)
    econ={**REGIMES[regime],'horizon':ticks};journal=[]
    led,alive,death=_expedition(world,agent,econ,TEMPERAMENTS[choice]['science_at'],journal)
    head=_write_journal(data,eid,journal);rv=world.reveal()
    rep=agent.report();claim=agent.claim
    verdict={'law_correct':None if claim is None else claim['table']==rv['table'],
             'claim_bound_held':None if claim is None else world.true_agreement(claim['table'])>=claim['claimed_min_agreement_99'],
             'true_tier':rv['tier'],'true_noise':rv['noise']}
    ex={'expedition':eid,'world_id':world_id,'world_commitment':commit,'regime':regime,'ticks':ticks,'temperament':choice,
        'started_with_inherited_law':prior['law'] if prior else None,'journal_head':head,'journal_rows':len(journal),
        'alive':alive,'death_tick':death,'final_energy':led.energy,'ledger':{'start':led.start,'income':led.income,'spent':led.spent},
        'status':agent.status,'method':agent.method,'claim':None if claim is None else {k:v for k,v in claim.items()},
        'events':[e['event'] for e in agent.events][-24:],'observations':len(agent.obs),'environment_verdict':verdict,
        'law_invention':agent.invent}
    s=dict(s);laws=dict(s['laws']);s['claim_boundary']=CLAIMS
    if claim is not None:laws[world_id]={k:v for k,v in claim.items() if k!='inherited'}|{'expedition':claim.get('expedition',eid) if claim.get('inherited') else eid}
    elif prior and any(e['event']=='REFUTED' for e in agent.events):laws.pop(world_id,None)
    ex['law_after']=laws.get(world_id)
    s['expeditions']=s['expeditions']+[ex];s['laws']=laws
    _validate(s);store.save(data,NS,COMPONENT,s)
    good=alive and (claim is not None or agent.method=='TABLE')
    heart_loop.process_experience(data,'discovery' if claim is not None else 'learning',0.6 if good else (-0.4 if not alive else 0.1),0.5,'open_world_research','')
    try:
        from tukuyo_v993.relation_bound import sync as relation_sync
        from tukuyo_v995.other_agent_trust import sync as peer_sync
        relation_sync(data);peer_sync(data)
    except ImportError:pass
    whole.sync(data)
    return {'ok':True,'version':'v1023r-preview',**{k:ex[k] for k in ('expedition','world_id','temperament','started_with_inherited_law','alive','death_tick','final_energy','status','method','claim','environment_verdict','events')},
            'report':rep,'claim_boundary':CLAIMS}

def audit(data):
    errs=[];out={'ok':False,'version':'v1023r-preview'}
    try:s=state(data)
    except Exception as e:return {**out,'errors':['V1023R_STATE:'+str(e)]}
    try:key=_world_key(data)
    except Exception:key=None
    replayed=0
    for ex in s['expeditions']:
        eid=ex['expedition']
        try:rows,head=_read_journal(data,eid)
        except Exception as e:errs.append(str(e));continue
        if head!=ex['journal_head'] or len(rows)!=ex['journal_rows']:errs.append('V1023R_JOURNAL_HEAD:'+eid);continue
        led=ex['ledger']
        if led['start']+led['income']-led['spent']!=ex['final_energy']:errs.append('V1023R_LEDGER:'+eid)
        if key is None:continue
        # The world must be the one committed to before the expedition began.
        world=None
        for tier in (1,2,3,4,5):
            for noise in (0.0,0.05,0.1):
                if _commitment(key,ex['world_id'],tier,noise)==ex['world_commitment']:world=DeviceWorld(key,ex['world_id'],tier,noise,stream=eid)
        if world is None:errs.append('V1023R_WORLD_COMMITMENT:'+eid);continue
        # Replay: same world, same agent, same prior -> identical journal.
        prior=None
        for e in s['expeditions']:
            if e['expedition']==eid:break
            if e['world_id']==ex['world_id']:prior=e['law_after']
        if (prior is None)!=(ex['started_with_inherited_law'] is None):errs.append('V1023R_PRIOR_BINDING:'+eid)
        # an expedition recorded before claude-patch6 is replayed without law invention, as it was run
        agent=ResearchAgent(prior_claim=prior,invent=bool(ex.get('law_invention')));journal=[]
        econ={**REGIMES[ex['regime']],'horizon':ex['ticks']}
        try:
            led2,alive,death=_expedition(world,agent,econ,TEMPERAMENTS[ex['temperament']]['science_at'],journal)
            prev='0'*64
            for r in journal:prev=hashlib.sha256(whole.canon({'prev':prev,**json.loads(whole.canon(r))})).hexdigest()
            if prev!=ex['journal_head']:errs.append('V1023R_REPLAY_MISMATCH:'+eid)
            if (agent.claim or None)!=(ex['claim'] or None) or led2.energy!=ex['final_energy']:errs.append('V1023R_REPLAY_RESULT:'+eid)
            replayed+=1
        except Exception as e:errs.append('V1023R_REPLAY:'+eid+':'+type(e).__name__)
    return {**out,'ok':not errs,'errors':errs,'expeditions':len(s['expeditions']),'replayed_from_world_key':replayed,
            'laws':{k:v['law'] for k,v in s['laws'].items()},'claim_boundary':CLAIMS}

def status(data):
    s=state(data);last=s['expeditions'][-1] if s['expeditions'] else None
    return {'ok':True,'version':'v1023r-preview','expeditions':len(s['expeditions']),'laws':{k:v['law'] for k,v in s['laws'].items()},
            'last':None if last is None else {k:last[k] for k in ('expedition','world_id','temperament','alive','final_energy','status','method','claim','environment_verdict')},
            'claim_boundary':CLAIMS}
