"""Signed, per-individual developmental episodes in the real metabolism.

These are explicitly SIMULATED device experiences. No teacher calls, physical
truth certification or consciousness inference is made by this module.
"""
from __future__ import annotations
import copy, math
from pathlib import Path
from tukuyo_v977 import whole_state as whole
from tukuyo_v978 import heart_loop
from tukuyo_common.journal import last_event, load_events
from tukuyo_common.atomic_fs import maybe_crash
from tukuyo_v1023r import development as policy
from tukuyo_v1023r.agent import ResearchAgent
from . import store

NS='developmental_life'; COMPONENT='developmental_life_v1022_8_1'
SCHEMA='tukuyo.v1022_8_1.developmental_life/1'
CLAIMS={'internally_generated_bounded_goal_instances':True,
        'heart_values_affect_goal_selection':True,
        'goals_control_actions':True, 'simulation_origin':True,
        'teacher_calls':0, 'external_scheduler_required':True,
        'goal_vocabulary_designed':True, 'open_ended_goal_invention':False,
        'physical_world_observation':False, 'consciousness_established':False,
        'functional_germination_gate_completed':False, '24h_completed':False}

def validate(s):
    if s.get('schema')!=SCHEMA or s.get('claim_boundary')!=CLAIMS:
        raise ValueError('DEVELOPMENT_SCHEMA')
    rows=s.get('episodes')
    if type(rows) is not list or len(rows)>512 or s.get('policy')!=policy.POLICY:
        raise ValueError('DEVELOPMENT_BOUND')
    for i,r in enumerate(rows,1):
        if r.get('seq')!=i or r.get('goal') not in policy.GOALS or r.get('origin')!='simulation':
            raise ValueError('DEVELOPMENT_EPISODE')
        if r.get('action') not in ('probe','trial','work','rest'):
            raise ValueError('DEVELOPMENT_ACTION')
        if any(type(r.get(k)) is not int or r[k]<0 for k in ('energy','remaining','reservoir','credit','extra_cost')):
            raise ValueError('DEVELOPMENT_RESOURCE')
        if type(r.get('reset_model')) is not bool or type(r.get('enabled')) is not bool:
            raise ValueError('DEVELOPMENT_MODE')
        o=r.get('observation')
        if o is not None and (type(o.get('x')) is not int or not 0<=o['x']<32 or
                type(o.get('y')) is not int or o['y'] not in (0,1)):
            raise ValueError('DEVELOPMENT_OBSERVATION')

def load(data, initial_agent=None):
    if (Path(data)/NS/'commits').exists():
        s=store.load(data,NS,COMPONENT,validate)
        if s['individual_id']!=whole._live_identity(data)['individual_id']:
            raise ValueError('DEVELOPMENT_IDENTITY')
        return s
    return {'schema':SCHEMA,'policy':policy.POLICY,
            'individual_id':whole._live_identity(data)['individual_id'],
            'initial_agent':copy.deepcopy(initial_agent), 'last_agent':copy.deepcopy(initial_agent),
            'memory':policy.memory(),'episodes':[],'claim_boundary':CLAIMS}

def prepare(data, agent, locked, energy, remaining, reservoir, econ, enabled=True):
    from tukuyo_v1019.transaction import ACTIVE
    if not ACTIVE.get():raise ValueError('DEVELOPMENT_OWNER_TRANSACTION_REQUIRED')
    from tukuyo_v1019.lifecycle import require_alive
    require_alive(data)
    s=copy.deepcopy(load(data,agent.to_compact()))
    if s['last_agent']!=agent.to_compact():raise ValueError('DEVELOPMENT_MODEL_DRIFT')
    seq=len(s['episodes'])+1
    options=policy.propose(agent,s['memory'],energy,remaining,reservoir,locked,econ)
    h=heart_loop.load(data);soul=whole.load_soul(data)
    weights=heart_loop._decision_core_values(data,soul)
    for k,v in h['value_bias'].items():weights[k]=max(0,min(1,weights.get(k,0)+v))
    if enabled:
        choice=heart_loop.choose(data,options,context=f'developmental-goal-{seq}')
        goal=choice['chosen']; event=choice['event']['event_sha256']
    else: goal='rest';event=None
    a,action,x,reset=policy.enact(agent,s['memory'],goal,energy,remaining,reservoir,locked,econ,seq)
    row={'seq':seq,'origin':'simulation','energy':energy,'remaining':remaining,
         'reservoir':reservoir,'econ':dict(econ),'locked':{str(k):v for k,v in locked.items()},
         'options':options,'weights':weights,'enabled':bool(enabled),'goal':goal,
         'heart_choice_event':event,'soul_before_sha256':whole.sha_obj(soul),
         'action':action,'input':x,'reset_model':reset,
         'model_before_sha256':whole.sha_obj(agent.to_compact()),
         'prediction':a.p_on(x) if x is not None else None}
    return {'state':s,'row':row,'agent':a,'before_observation':copy.deepcopy(a.to_compact())}

def complete(data, prepared, agent, observation, credit, extra_cost):
    from tukuyo_v1019.transaction import ACTIVE
    if not ACTIVE.get():raise ValueError('DEVELOPMENT_OWNER_TRANSACTION_REQUIRED')
    s=prepared['state'];r=prepared['row'];before=ResearchAgent.from_compact(prepared['before_observation'])
    # trial input is chosen by the environment. The prediction must still be
    # computed from the pre-observation model, not from its updated belief.
    if observation is not None and r['input'] is None:
        r['input']=observation['x'];r['prediction']=before.p_on(observation['x'])
    r.update({'observation':copy.deepcopy(observation),'credit':credit,'extra_cost':extra_cost,
              **policy.result_metrics(before,agent,r['goal'],observation,credit,r['prediction']),
              'model_after_sha256':whole.sha_obj(agent.to_compact())})
    s['memory']=policy.advance(s['memory'],r)
    s['episodes'].append(r);s['last_agent']=copy.deepcopy(agent.to_compact())
    if r['enabled']:
        # Feedback is bound to the chosen GOAL; this is the very choice that
        # caused the observed action. Simulation stays labelled in the theme.
        val=max(-1.,min(1.,(credit-extra_cost)/600))
        if r['goal'] in ('learn_rule','verify_rule','repair_prediction'):
            val=max(-1.,min(1., .4*int(r['progress'])-.5*int(r['surprise'])-extra_cost/2000))
        heart_loop.feedback(data,r['goal'],val,.25,'simulation:developmental_device')
        if r['progress'] and r['goal'] in ('learn_rule','verify_rule','repair_prediction'):
            heart_loop.process_experience(data,'learning',.3,.2,'simulation:developmental_device')
    validate(s);maybe_crash('development:before_save');store.save(data,NS,COMPONENT,s)
    return {'goal':r['goal'],'reason':next(o['reason'] for o in r['options'] if o['id']==r['goal']),
            'goal_switches':s['memory']['switches'],'model_revisions':s['memory']['revisions'],
            'surprise':r['surprise'],'progress':r['progress'],'origin':'simulation'}

def audit(data):
    try:
        s=load(data)
        if not s['episodes']:return {'ok':True,'episodes':0,'errors':[],'claim_boundary':CLAIMS}
        a=ResearchAgent.from_compact(copy.deepcopy(s['initial_agent']));mem=policy.memory()
        choices={e['event_sha256']:e for e in load_events(heart_loop.events_path(data))
                 if e.get('type')=='ACTION_SELECTION'}
        for r in s['episodes']:
            # The living niche starts every tick from sufficient statistics.
            # Replay must use the same reconstruction boundary: an incrementally
            # accumulated likelihood can differ by a few floating point bits
            # from sum(L1/L0), changing a recorded entropy-based goal signal.
            a=ResearchAgent.from_compact(copy.deepcopy(a.to_compact()))
            if whole.sha_obj(a.to_compact())!=r['model_before_sha256']:
                raise ValueError('DEVELOPMENT_MODEL_BEFORE')
            locked={int(k):v for k,v in r['locked'].items()}
            opts=policy.propose(a,mem,r['energy'],r['remaining'],r['reservoir'],locked,r['econ'])
            if opts!=r['options']:raise ValueError('DEVELOPMENT_GOAL_REPLAY')
            if r['enabled']:
                scores=[(round(sum(r['weights'].get(k,0)*v for k,v in o['signals'].items()),6),o['id']) for o in opts]
                if max(scores)[1]!=r['goal']:raise ValueError('DEVELOPMENT_VALUE_REPLAY')
                ev=choices.get(r['heart_choice_event'])
                if not ev or ev['chosen']!=r['goal'] or ev['context']!=f"developmental-goal-{r['seq']}":
                    raise ValueError('DEVELOPMENT_HEART_BINDING')
                if sorted((score,ident) for score,ident in scores)!=sorted((e['score'],e['id']) for e in ev['scores']):
                    raise ValueError('DEVELOPMENT_HEART_SCORES')
            elif r['goal']!='rest' or r['heart_choice_event'] is not None:
                raise ValueError('DEVELOPMENT_DISABLED_ACTION')
            a,act,x,reset=policy.enact(a,mem,r['goal'],r['energy'],r['remaining'],r['reservoir'],locked,r['econ'],r['seq'])
            if act!=r['action'] or reset!=r['reset_model'] or (act!='trial' and x!=r['input']):
                raise ValueError('DEVELOPMENT_ACTION_REPLAY')
            before=ResearchAgent.from_compact(copy.deepcopy(a.to_compact()));o=r['observation']
            if o is None:
                if act!='rest' or r['prediction'] is not None:raise ValueError('DEVELOPMENT_MISSING_OBSERVATION')
            else:
                if o['kind']!=act or o['x']!=r['input']:raise ValueError('DEVELOPMENT_OBSERVATION_BINDING')
                if not math.isclose(before.p_on(o['x']),r['prediction'],abs_tol=1e-12):
                    raise ValueError('DEVELOPMENT_PREDICTION_REPLAY')
                pred=a.predict_trial(o['x']) if act=='trial' else None
                a.observe(o,prediction=pred)
            expected_cost=(r['econ']['probe'] if act in ('probe','trial') else
                           r['econ']['work']+r['econ']['fail_penalty']*(1-o['y']) if act=='work' else 0)
            expected_credit=(min(r['econ']['reward'],r['reservoir'],max(0,r['econ']['cap']-r['energy']))
                             if act=='work' and o['y'] else 0)
            if (r['credit'],r['extra_cost'])!=(expected_credit,expected_cost):raise ValueError('DEVELOPMENT_ECONOMY_REPLAY')
            metrics=policy.result_metrics(before,a,r['goal'],o,r['credit'],r['prediction'])
            if any(r[k]!=v for k,v in metrics.items()):raise ValueError('DEVELOPMENT_OUTCOME_REPLAY')
            if whole.sha_obj(a.to_compact())!=r['model_after_sha256']:raise ValueError('DEVELOPMENT_MODEL_AFTER')
            mem=policy.advance(mem,r)
        if mem!=s['memory'] or a.to_compact()!=s['last_agent']:raise ValueError('DEVELOPMENT_FINAL_REPLAY')
        return {'ok':True,'episodes':len(s['episodes']),'errors':[],
                'model_revisions':mem['revisions'],'goal_switches':mem['switches'],
                'replayed_goal_action_learning_outcome':True,'physical_truth_verified':False,'claim_boundary':CLAIMS}
    except Exception as e:return {'ok':False,'errors':[str(e)],'claim_boundary':CLAIMS}

def status(data):
    s=load(data);return {'ok':True,'version':'v1022.8.1',
        'individual_id':s['individual_id'],'episodes':len(s['episodes']),
        'memory':s['memory'],'last_episode':s['episodes'][-1] if s['episodes'] else None,
        'claim_boundary':CLAIMS}
