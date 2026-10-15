"""Compact signed state and full personal journal; culture is provisional."""
from __future__ import annotations
import base64,copy,json,math
from pathlib import Path
from tukuyo_v977 import whole_state as whole
from tukuyo_v978 import heart_loop
from tukuyo_v1018 import succession
from tukuyo_v1019.transaction import ACTIVE
from tukuyo_common.atomic_fs import atomic_write_bytes,maybe_crash
from tukuyo_common.journal import load_events
from tukuyo_v1023r import adaptive_development as policy
from tukuyo_v1023r.agent import ResearchAgent
from . import store

NS='adaptive_life';COMPONENT='adaptive_life_v1022_8_2';SCHEMA='tukuyo.v1022_8_2.adaptive_life/1'
SEED_SCHEMA='tukuyo.v1022_8_2.public_observations/1'
CLAIMS={'bounded_adaptive_goals':True,'observations_are_simulation':True,
        'compact_state_full_experience_journal':True,'old_biography_not_erased_by_model_reset':True,
        'public_observations_inherited_as_evidence_not_truth':True,'teacher_calls':0,
        'external_scheduler_required':True,'open_ended_goal_invention':False,
        'physical_truth_proven':False,'consciousness_established':False,'24h_completed':False}

def journal(data):return Path(data)/NS/'EPISODES.jsonl'
def seed_path(data):return Path(data)/NS/'PUBLIC_SEED.json'
def validate(s):
    if s.get('schema')!=SCHEMA or s.get('policy')!=policy.POLICY or s.get('claim_boundary')!=CLAIMS:raise ValueError('ADAPTIVE_SCHEMA')
    if type(s.get('episode_count')) is not int or not 0<=s['episode_count']<=2048:raise ValueError('ADAPTIVE_BOUND')
    m=s['memory']
    if len(m['recent'])>32 or len(m['blocked'])>32 or len(m['failures'])>12 or len(m['probe_conflicts'])>32:raise ValueError('ADAPTIVE_MEMORY_BOUND')
    if len(s['last_agent']['count'])!=32 or sum(s['last_agent']['count'])!=s['last_agent']['n_obs']:raise ValueError('ADAPTIVE_MODEL_COUNT')

def _seed(data,scope=None):
    p=seed_path(data)
    if not p.exists():return None
    env=json.loads(p.read_text());v=env.get('payload',{});st=succession.ensure_state(data)[0]
    if st['role']!='SUCCESSOR' or env.get('public_key')!=st['parent_succession_public_key'] or not whole._verify(env,st['parent_succession_public_key']):raise ValueError('ADAPTIVE_SEED_PARENT_KEY')
    if (v.get('schema')!=SEED_SCHEMA or v.get('origin')!='simulation' or v.get('kind')!='provisional_public_observations'
        or v.get('target_individual_id')!=whole._live_identity(data)['individual_id']
        or v.get('source_individual_id')!=st['parent_individual_id'] or v.get('family_lineage_id')!=st['family_lineage_id']):raise ValueError('ADAPTIVE_SEED_BINDING')
    if v.get('confirmed_truth') is not False:raise ValueError('ADAPTIVE_SEED_TRUTH')
    if scope is not None and v.get('environment_commitment')!=scope:raise ValueError('ADAPTIVE_SEED_SCOPE')
    rows=v.get('observations')
    if type(rows) is not list or not 1<=len(rows)<=16:raise ValueError('ADAPTIVE_SEED_BOUND')
    for r in rows:
        o=r['observation']
        if (set(r)!={'global_tick','observation'} or set(o)!={'kind','n','x','y'}
            or type(r['global_tick']) is not int or not 1<=r['global_tick']<=4096
            or type(o['n']) is not int or not 0<=o['n']<=4096 or o.get('kind') not in ('work','probe','trial')):raise ValueError('ADAPTIVE_SEED_OBSERVATION')
        if type(o['x']) is not int or not 0<=o['x']<32 or type(o['y']) is not int or o['y'] not in (0,1):raise ValueError('ADAPTIVE_SEED_OBSERVATION')
    return env

def import_seed(data,envelope,scope):
    if not ACTIVE.get():raise ValueError('ADAPTIVE_OWNER_TRANSACTION_REQUIRED')
    if seed_path(data).exists() or (Path(data)/NS/'commits').exists():raise ValueError('ADAPTIVE_SEED_REPLAY')
    atomic_write_bytes(seed_path(data),whole.canon(envelope)+b'\n');_seed(data,scope);whole.sync(data)
    return whole.sha_obj(envelope)

def _initial(data,initial_agent=None):
    env=_seed(data);a=ResearchAgent.from_compact(copy.deepcopy(initial_agent)) if initial_agent else ResearchAgent();m=policy.memory()
    if env:
        a=ResearchAgent()
        for r in env['payload']['observations']:
            o=copy.deepcopy(r['observation']);a.observe(o);m['recent'].append({'seq':0,'observation':o})
            if o['kind']=='work' and o['y']==0:m['blocked'][str(o['x'])]={'seq':0,'positive_retests':0}
    return {'schema':SCHEMA,'policy':policy.POLICY,'individual_id':whole._live_identity(data)['individual_id'],
            'initial_agent':copy.deepcopy(a.to_compact()),'last_agent':copy.deepcopy(a.to_compact()),
            'initial_memory':copy.deepcopy(m),'memory':m,'episode_count':0,'journal_head':whole.ZERO,
            'last_episode':None,'public_seed_sha256':whole.sha_obj(env) if env else None,'claim_boundary':CLAIMS}

def load(data,initial_agent=None):
    if not ACTIVE.get():
        from tukuyo_v1014.recovery import enforce_restore_frontier
        enforce_restore_frontier(data)
    if (Path(data)/NS/'commits').exists():
        s=store.load(data,NS,COMPONENT,validate)
        if s['individual_id']!=whole._live_identity(data)['individual_id']:raise ValueError('ADAPTIVE_IDENTITY')
        env=_seed(data)
        if s['public_seed_sha256']!=(whole.sha_obj(env) if env else None):raise ValueError('ADAPTIVE_SEED_HEAD')
        return s
    return _initial(data,initial_agent)

def initial_agent(data):return ResearchAgent.from_compact(load(data)['initial_agent'])

def episodes(data,state=None):
    s=state or load(data);rows=[];prev=whole.ZERO
    for i,r in enumerate(load_events(journal(data)),1):
        if r.get('seq')!=i or r.get('previous')!=prev:raise ValueError('ADAPTIVE_JOURNAL_CHAIN')
        if whole.sha_obj({k:v for k,v in r.items() if k!='sha256'})!=r.get('sha256'):raise ValueError('ADAPTIVE_JOURNAL_HASH')
        prev=r['sha256'];rows.append(r)
    if len(rows)!=s['episode_count'] or prev!=s['journal_head']:raise ValueError('ADAPTIVE_JOURNAL_HEAD')
    return rows

def prepare(data,agent,locked,energy,remaining,reservoir,econ,global_tick,enabled=True):
    if not ACTIVE.get():raise ValueError('ADAPTIVE_OWNER_TRANSACTION_REQUIRED')
    from tukuyo_v1019.lifecycle import require_alive
    require_alive(data);s=copy.deepcopy(load(data,agent.to_compact()))
    if s['last_agent']!=agent.to_compact():raise ValueError('ADAPTIVE_MODEL_DRIFT')
    seq=s['episode_count']+1;opts=policy.propose(agent,s['memory'],energy,remaining,reservoir,locked,econ)
    h=heart_loop.load(data);soul=whole.load_soul(data);weights=heart_loop._decision_core_values(data,soul)
    for k,v in h['value_bias'].items():weights[k]=max(0,min(1,weights.get(k,0)+v))
    choice=heart_loop.choose(data,opts,context=f'adaptive-goal-{seq}') if enabled else None;goal=choice['chosen'] if choice else 'rest'
    a,act,x,reset=policy.enact(agent,s['memory'],goal,energy,remaining,reservoir,locked,econ,seq)
    r={'seq':seq,'global_tick':global_tick,'origin':'simulation','energy':energy,'remaining':remaining,
       'reservoir':reservoir,'econ':dict(econ),'locked':{str(k):v for k,v in locked.items()},'options':opts,
       'weights':weights,'emotion':copy.deepcopy(h['emotion']),'enabled':bool(enabled),'goal':goal,
       'heart_choice_event':choice['event']['event_sha256'] if choice else None,'soul_before_sha256':whole.sha_obj(soul),
       'action':act,'input':x,'reset_model':reset,'model_before_sha256':whole.sha_obj(agent.to_compact()),
       'prediction':a.p_on(x) if x is not None else None}
    return {'state':s,'row':r,'agent':a,'before_observation':copy.deepcopy(a.to_compact())}

def complete(data,prepared,agent,observation,credit,extra_cost):
    if not ACTIVE.get():raise ValueError('ADAPTIVE_OWNER_TRANSACTION_REQUIRED')
    s=prepared['state'];r=prepared['row'];before=ResearchAgent.from_compact(prepared['before_observation'])
    if observation is not None and r['input'] is None:r['input']=observation['x'];r['prediction']=before.p_on(observation['x'])
    r.update({'observation':copy.deepcopy(observation),'credit':credit,'extra_cost':extra_cost,
              **policy.result_metrics(before,agent,r['goal'],observation,credit,r['prediction']),
              'model_after_sha256':whole.sha_obj(agent.to_compact()),'previous':s['journal_head']});r['sha256']=whole.sha_obj(r)
    s['memory']=policy.advance(s['memory'],r);s['last_agent']=copy.deepcopy(agent.to_compact())
    s['episode_count']=r['seq'];s['journal_head']=r['sha256'];s['last_episode']=copy.deepcopy(r)
    if r['enabled']:
        val=max(-1.,min(1.,(credit-extra_cost)/600))
        if r['goal']!='secure_energy':val=max(-1.,min(1.,.4*int(r['progress'])-.5*int(r['surprise'])-extra_cost/2000))
        heart_loop.feedback(data,r['goal'],val,.25,'simulation:adaptive_device')
        if r['progress'] and r['goal'] in ('learn_rule','repair_prediction','verify_rule'):heart_loop.process_experience(data,'learning',.3,.2,'simulation:adaptive_device')
    old=journal(data).read_bytes() if journal(data).exists() else b''
    atomic_write_bytes(journal(data),old+whole.canon(r)+b'\n');maybe_crash('adaptive:after_journal');validate(s);store.save(data,NS,COMPONENT,s)
    return {'goal':r['goal'],'reason':next(o['reason'] for o in r['options'] if o['id']==r['goal']),
            'goal_switches':s['memory']['switches'],'model_revisions':s['memory']['revisions'],'surprise':r['surprise'],'origin':'simulation'}

def seed_payload(data,target_id,scope):
    from tukuyo_v1007 import organism2
    if organism2.load(data)['lifecycle']!='DEAD':raise ValueError('ADAPTIVE_SEED_MORTALITY')
    s=load(data);by_seq={r['seq']:r for r in episodes(data,s)};chosen={}
    for e in s['memory']['recent']:
        if e['seq'] in by_seq:
            row=by_seq[e['seq']];chosen[row['observation']['x']]={'global_tick':row['global_tick'],'observation':row['observation']}
    obs=list(chosen.values())[-16:]
    if not obs:return None
    st=succession.ensure_state(data)[0]
    return {'schema':SEED_SCHEMA,'kind':'provisional_public_observations','origin':'simulation',
            'source_individual_id':s['individual_id'],'target_individual_id':target_id,'family_lineage_id':st['family_lineage_id'],
            'environment_commitment':scope,'source_journal_head':s['journal_head'],'observations':obs,'confirmed_truth':False}

def export_seed(data,target_id,scope):
    if not ACTIVE.get():raise ValueError('ADAPTIVE_OWNER_TRANSACTION_REQUIRED')
    pl=seed_payload(data,target_id,scope)
    if pl is None:return None
    sk,pub=succession._ensure_key(data)
    return {'payload':pl,'public_key':pub,'signature':base64.b64encode(sk.sign(whole.canon(pl))).decode()}

_MEMO={}
def audit(data,use_memo=True):
    try:
        s=load(data);rs=episodes(data,s);initial=_initial(data)
        if s['initial_agent']!=initial['initial_agent'] or s['initial_memory']!=initial['initial_memory']:raise ValueError('ADAPTIVE_INITIAL_REPLAY')
        if not rs:return {'ok':True,'episodes':0,'errors':[],'claim_boundary':CLAIMS}
        envelopes=[json.loads(p.read_text()) for p in sorted((Path(data)/NS/'commits').glob('*.json'))]
        if len(envelopes)!=len(rs):raise ValueError('ADAPTIVE_COMMIT_COUNT')
        commits=[whole.sha_obj(e) for e in envelopes];hb=heart_loop.events_path(data).read_bytes();jb=journal(data).read_bytes()
        key=(s['individual_id'],whole._key_paths(data)[1].read_text().strip());cached=_MEMO.get(key) if use_memo else None
        start=0;mem=copy.deepcopy(s['initial_memory']);a=ResearchAgent.from_compact(copy.deepcopy(s['initial_agent']))
        if cached and commits[:cached['count']]==cached['commits'] and jb.startswith(cached['journal']) and hb.startswith(cached['heart']):
            start=cached['count'];mem=copy.deepcopy(cached['memory']);a=ResearchAgent.from_compact(copy.deepcopy(cached['agent']))
        choices={e['event_sha256']:e for e in load_events(heart_loop.events_path(data)) if e.get('type')=='ACTION_SELECTION'}
        for i in range(start,len(rs)):
            r=rs[i];a=ResearchAgent.from_compact(copy.deepcopy(a.to_compact()));locked={int(k):v for k,v in r['locked'].items()}
            if r['origin']!='simulation' or r['model_before_sha256']!=whole.sha_obj(a.to_compact()):raise ValueError('ADAPTIVE_MODEL_BEFORE')
            opts=policy.propose(a,mem,r['energy'],r['remaining'],r['reservoir'],locked,r['econ'])
            if opts!=r['options']:raise ValueError('ADAPTIVE_GOAL_REPLAY')
            if r['enabled']:
                def score(o):
                    sig=o['signals'];v=sum(r['weights'].get(k,0)*x for k,x in sig.items())
                    v+=sig.get('trust',0)*r['emotion']['trust']*.35;v-=sig.get('threat',0)*(.3+r['emotion']['threat']*.7)
                    return round(v,6),o['id']
                scores=[score(o) for o in opts];ev=choices.get(r['heart_choice_event'])
                if max(scores)[1]!=r['goal'] or not ev or ev['chosen']!=r['goal'] or ev['context']!=f"adaptive-goal-{r['seq']}":raise ValueError('ADAPTIVE_HEART_BINDING')
                if sorted(scores)!=sorted((e['score'],e['id']) for e in ev['scores']):raise ValueError('ADAPTIVE_HEART_SCORES')
            elif r['goal']!='rest' or r['heart_choice_event'] is not None:raise ValueError('ADAPTIVE_DISABLED')
            a,act,x,reset=policy.enact(a,mem,r['goal'],r['energy'],r['remaining'],r['reservoir'],locked,r['econ'],r['seq'])
            if act!=r['action'] or reset!=r['reset_model'] or (act!='trial' and x!=r['input']):raise ValueError('ADAPTIVE_ACTION_REPLAY')
            before=ResearchAgent.from_compact(copy.deepcopy(a.to_compact()));o=r['observation']
            if o is None:
                if act!='rest' or r['prediction'] is not None:raise ValueError('ADAPTIVE_OBSERVATION_MISSING')
            else:
                if o['kind']!=act or o['x']!=r['input'] or not math.isclose(before.p_on(o['x']),r['prediction'],abs_tol=1e-12):raise ValueError('ADAPTIVE_OBSERVATION_BINDING')
                a.observe(o,prediction=a.predict_trial(o['x']) if act=='trial' else None)
            extra=(r['econ']['probe'] if act in ('probe','trial') else r['econ']['work']+(1-o['y'])*r['econ']['fail_penalty'] if act=='work' else 0)
            credit=(min(r['econ']['reward'],r['reservoir'],max(0,r['econ']['cap']-r['energy'])) if act=='work' and o['y'] else 0)
            metrics=policy.result_metrics(before,a,r['goal'],o,credit,r['prediction'])
            if extra!=r['extra_cost'] or credit!=r['credit'] or any(r[k]!=v for k,v in metrics.items()):raise ValueError('ADAPTIVE_OUTCOME_REPLAY')
            if whole.sha_obj(a.to_compact())!=r['model_after_sha256']:raise ValueError('ADAPTIVE_MODEL_AFTER')
            mem=policy.advance(mem,r);st=envelopes[i]['payload']['state']
            if (st['episode_count']!=i+1 or st['journal_head']!=r['sha256'] or st['last_episode']!=r or st['individual_id']!=s['individual_id']
                or st['memory']!=mem or st['last_agent']!=a.to_compact() or st['initial_agent']!=s['initial_agent']
                or st['initial_memory']!=s['initial_memory'] or st['public_seed_sha256']!=s['public_seed_sha256']):raise ValueError('ADAPTIVE_COMMIT_REPLAY')
        if s['memory']!=mem or s['last_agent']!=a.to_compact():raise ValueError('ADAPTIVE_FINAL_REPLAY')
        if len(_MEMO)>128:_MEMO.clear()
        _MEMO[key]={'count':len(rs),'commits':commits,'journal':jb,'heart':hb,'memory':copy.deepcopy(mem),'agent':copy.deepcopy(a.to_compact())}
        return {'ok':True,'episodes':len(rs),'errors':[],'replayed_from':start,'goal_switches':mem['switches'],'model_revisions':mem['revisions'],'claim_boundary':CLAIMS}
    except Exception as e:return {'ok':False,'errors':[str(e)],'claim_boundary':CLAIMS}

def status(data):
    s=load(data);return {'ok':True,'version':'v1022.8.2','individual_id':s['individual_id'],'episodes':s['episode_count'],
                      'memory':s['memory'],'last_episode':s['last_episode'],'public_seed_sha256':s['public_seed_sha256'],'claim_boundary':CLAIMS}
