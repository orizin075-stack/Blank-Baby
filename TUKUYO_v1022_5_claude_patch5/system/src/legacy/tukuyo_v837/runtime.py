from __future__ import annotations
import copy, json, os, time, uuid, fcntl
from pathlib import Path
from contextlib import contextmanager
from .util import canonical, sha256_bytes, atomic_write
from .crypto import new_keypair, sign_obj, verify_obj, pub_from_private
from .model import deterministic_observation, choose_action, apply_action, ACTIONS

class RuntimeError837(RuntimeError): pass

STATE='organism_state.json'; KEY='private/runtime_authority.key'; PUB='runtime_authority.pub'; WAL='pending_tick.json'; HEAD='state_commit_head.json'
ZERO='0'*64

@contextmanager
def writer_lock(root:Path):
    root.mkdir(parents=True,exist_ok=True)
    p=root/'.runtime.lock'; f=open(p,'a+b')
    try:
        try: fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: raise RuntimeError837('RUNTIME_ALREADY_ACTIVE')
        yield
    finally:
        try: fcntl.flock(f.fileno(),fcntl.LOCK_UN)
        finally: f.close()

def _load_json(p): return json.loads(Path(p).read_text())
def _signed(payload,sk,pk): return {'payload':payload,'public_key':pk,'signature':sign_obj(sk,payload)}
def _verify(env): return verify_obj(env['public_key'],env['payload'],env['signature'])
def _event_path(root,seq): return Path(root)/'events'/f'{seq:012d}.json'
def _commit_path(root,seq): return Path(root)/'state_commits'/f'{seq:012d}.json'

def _dirs(root):
    root=Path(root); root.mkdir(parents=True,exist_ok=True)
    for d in ('private','events','state_commits','checkpoints'): (root/d).mkdir(exist_ok=True)
    return root

def _commit_env_for(state_env, previous_commit_sha, sk, pk):
    p=state_env['payload']; seq=p['continuity']['state_seq']
    payload={
      'schema':'tukuyo.organism_state_commit.v837.1',
      'individual_id':p['identity']['individual_id'],'branch_id':p['identity']['branch_id'],
      'state_seq':seq,'runtime_tick':p['runtime']['tick'],
      'state_sha256':sha256_bytes(canonical(state_env)),
      'previous_commit_sha256':previous_commit_sha,
      'event_head_sha256':p['continuity']['event_head_sha256'],'autobiographical_records':len(p['memory']['autobiographical']),'autobiographical_records_evicted':p['memory']['autobiographical_archive']['records_evicted'],'learned_action_value':p['self_model']['learned_action_value'],'learned_action_count':p['self_model']['learned_action_count'],'self_model_source_sha256':p['self_model']['derived_from_autobiography_sha256'],
    }
    return _signed(payload,sk,pk)

def _head_env_for(state_env, commit_env, sk, pk):
    p=state_env['payload']; seq=p['continuity']['state_seq']
    payload={
      'schema':'tukuyo.organism_state_commit_head.v837.1',
      'individual_id':p['identity']['individual_id'],'branch_id':p['identity']['branch_id'],
      'state_seq':seq,'state_sha256':sha256_bytes(canonical(state_env)),
      'commit_sha256':sha256_bytes(canonical(commit_env)),
    }
    return _signed(payload,sk,pk)

def _read_head(root):
    root=Path(root); hp=root/HEAD
    if not hp.exists(): raise RuntimeError837('STATE_COMMIT_HEAD_MISSING')
    env=_load_json(hp)
    if not _verify(env): raise RuntimeError837('STATE_COMMIT_HEAD_SIGNATURE_INVALID')
    return env

def _tail_commit(root):
    root=Path(root); h=_read_head(root); seq=h['payload']['state_seq']; cp=_commit_path(root,seq)
    if not cp.exists(): raise RuntimeError837('STATE_COMMIT_MISSING')
    env=_load_json(cp)
    if not _verify(env): raise RuntimeError837('STATE_COMMIT_SIGNATURE_INVALID')
    if sha256_bytes(canonical(env))!=h['payload']['commit_sha256']: raise RuntimeError837('STATE_COMMIT_HEAD_MISMATCH')
    return env

def _checkpoint(root,state_env):
    seq=state_env['payload']['continuity']['state_seq']
    p=Path(root)/'checkpoints'/f'{seq:012d}.json'
    atomic_write(p,canonical(state_env))

def _base_state(individual_id, lineage_id, branch_id, pk, *, parent=None, inherited=None):
    inherited=inherited or {}
    tick=int(inherited.get('runtime_tick',0)); sim=int(inherited.get('simulated_seconds',0))
    return {
      'schema':'tukuyo.organism_state.v837.1',
      'identity':{
        'individual_id':individual_id,'lineage_id':lineage_id,'branch_id':branch_id,
        'identity_public_key':pk,'parent_individual_id':None if not parent else parent['individual_id'],
      },
      'continuity':{
        'state_seq':0,'event_head_sha256':ZERO,'previous_state_sha256':inherited.get('fork_origin_state_sha256',ZERO),
        'restart_observations':0,
      },
      'lifecycle':{'status':'alive','birth_tick':tick,'death_tick':None,'death_reason':None,'death_certificate':None},
      'resources':copy.deepcopy(inherited.get('resources',{'energy':100.0,'metabolic_reserve':1500.0,'compute_credit':100000.0,'storage_credit':100000.0})),
      'health':copy.deepcopy(inherited.get('health',{'integrity':100.0,'maintenance_state':'nominal'})),
      'capabilities':copy.deepcopy(inherited.get('capabilities',{
        'capability_generation':0,'public_capabilities':[], 'active_grammar_sha256':None,'learned_repairs':[]
      })),
      'metabolism':copy.deepcopy(inherited.get('metabolism',{
        'mode':'active','initial_total_energy':1600.0,'maintenance_debt':0.0,'metabolic_ticks':0,'sleep_ticks':0,'hibernate_ticks':0,'maintenance_ticks':0,
        'cumulative_costs':{'energy_burn':0.0,'reserve_draw':0.0,'conversion_loss':0.0,'compute':0.0,'storage':0.0},
        'last_cost':{'energy':0.0,'compute':0.0,'storage':0.0},'last_decision_reason':'init'
      })),
      'memory':copy.deepcopy(inherited.get('memory',{'working':{},'episodic':[],'semantic':{},'autobiographical':[],'autobiographical_archive':{'records_evicted':0,'action_value_sum':{},'action_count':{}}})),
      'self_model':copy.deepcopy(inherited.get('self_model',{'persistent_traits':{},'learned_action_value':{},'learned_action_count':{},'derived_from_autobiography_sha256':None,'last_update_tick':tick})),
      'world_model':copy.deepcopy(inherited.get('world_model',{'last_observation':None,'experience_profile':'balanced'})),
      'other_models':copy.deepcopy(inherited.get('other_models',{})),
      'goals':copy.deepcopy(inherited.get('goals',{'active':['survive','maintain_integrity']})),
      'commitments':copy.deepcopy(inherited.get('commitments',[])),
      'preferences':copy.deepcopy(inherited.get('preferences',{'risk_tolerance':0.2})),
      'affect':copy.deepcopy(inherited.get('affect',{'valence':0.5,'arousal':0.2,'fatigue':0.0})),
      'lineage':{
        'fork_depth':0 if not parent else int(parent['fork_depth'])+1,
        'fork_origin_state_sha256':None if not parent else inherited['fork_origin_state_sha256'],
        'parent_branch_id':None if not parent else parent['branch_id'],
      },
      'relationships':copy.deepcopy(inherited.get('relationships',{})),
      'authority_receipts':copy.deepcopy(inherited.get('authority_receipts',[])),
      'runtime':{
        'tick':tick,'simulated_seconds':sim,'tick_seconds':60,'checkpoint_interval':60,
        'action_counts':copy.deepcopy(inherited.get('action_counts',{a:0 for a in ACTIONS})),
        'policy_wrong':0,'invariant_violations':0,
      },
      'provenance':{
        'created_unix_ns':time.time_ns(),'accelerated_time_is_not_wall_clock':True,
        'rollback_detection_scope':'state/commit/event material present in this root; whole-root rollback requires an external anchor',
        'v836_parent_complete_sha256':'19582bf86ff5ee82ba141881c3d5096560fd02943bb5e154d354822e7646479b',
      },
    }

def _autobio_material(p):
    return {'archive':p['memory']['autobiographical_archive'],'records':p['memory']['autobiographical']}

def _recompute_self_model(p):
    archive=p['memory']['autobiographical_archive']; sums=dict(archive.get('action_value_sum',{})); counts=dict(archive.get('action_count',{}))
    for rec in p['memory']['autobiographical']:
        for action,st in rec.get('action_stats',{}).items():
            sums[action]=float(sums.get(action,0.0))+float(st['value_sum']); counts[action]=int(counts.get(action,0))+int(st['count'])
    vals={a:round(float(sums[a])/counts[a],6) for a in counts if counts[a]>0}
    p['self_model']['learned_action_value']=vals; p['self_model']['learned_action_count']={a:int(counts[a]) for a in counts}; p['self_model']['derived_from_autobiography_sha256']=sha256_bytes(canonical(_autobio_material(p))); p['self_model']['last_update_tick']=p['runtime']['tick']
    return p

def _consolidate_autobiography(p, window=60):
    eps=[e for e in p['memory']['episodic'] if e['tick']>p['self_model'].get('last_consolidated_tick',0)]
    if not eps: return p
    stats={}; pe=0.0
    for e in eps:
        a=e['action']; st=stats.setdefault(a,{'count':0,'value_sum':0.0}); st['count']+=1; st['value_sum']=round(st['value_sum']+float(e.get('experienced_value',0.0)),6); pe+=float(e.get('prediction_error',0.0))
    rec={'schema':'tukuyo.autobiographical_record.v837.1','start_tick':eps[0]['tick'],'end_tick':eps[-1]['tick'],'action_stats':stats,'mean_prediction_error':round(pe/len(eps),6),'experience_profile':p['world_model']['experience_profile']}
    p['memory']['autobiographical'].append(rec); p['self_model']['last_consolidated_tick']=eps[-1]['tick']
    while len(p['memory']['autobiographical'])>128:
        old=p['memory']['autobiographical'].pop(0); ar=p['memory']['autobiographical_archive']; ar['records_evicted']+=1
        for a,st in old['action_stats'].items():
            ar['action_value_sum'][a]=round(float(ar['action_value_sum'].get(a,0.0))+float(st['value_sum']),6); ar['action_count'][a]=int(ar['action_count'].get(a,0))+int(st['count'])
    _recompute_self_model(p); return p

def _self_model_consistent(p):
    import copy
    q=copy.deepcopy(p); expected_hash=q['self_model'].get('derived_from_autobiography_sha256'); expected_vals=q['self_model'].get('learned_action_value'); expected_counts=q['self_model'].get('learned_action_count'); _recompute_self_model(q)
    return q['self_model']['derived_from_autobiography_sha256']==expected_hash and q['self_model']['learned_action_value']==expected_vals and q['self_model']['learned_action_count']==expected_counts

def init_runtime(root, individual_id='TUKUYO-v837-organism-001', *, initial_energy=100.0, initial_reserve=1500.0, initial_health=100.0, maintenance_debt=0.0, experience_profile='balanced'):
    root=_dirs(root)
    if (root/STATE).exists(): raise RuntimeError837('ALREADY_INITIALIZED')
    sk,pk=new_keypair(); atomic_write(root/KEY,sk.encode()); os.chmod(root/KEY,0o600); atomic_write(root/PUB,pk.encode())
    state=_base_state(individual_id,str(uuid.uuid4()),str(uuid.uuid4()),pk)
    state['resources']['energy']=float(initial_energy); state['resources']['metabolic_reserve']=float(initial_reserve); state['health']['integrity']=float(initial_health); state['metabolism']['maintenance_debt']=float(maintenance_debt); state['metabolism']['initial_total_energy']=round(float(initial_energy)+float(initial_reserve),9); state['world_model']['experience_profile']=str(experience_profile); _recompute_self_model(state)
    env=_signed(state,sk,pk); commit=_commit_env_for(env,ZERO,sk,pk)
    head=_head_env_for(env,commit,sk,pk)
    atomic_write(root/STATE,canonical(env)); atomic_write(_commit_path(root,0),canonical(commit)); atomic_write(root/HEAD,canonical(head)); _checkpoint(root,env)
    return env

def _verify_state_env(root,env, *, rollback=True):
    root=Path(root)
    if not _verify(env): raise RuntimeError837('STATE_SIGNATURE_INVALID')
    pk=(root/PUB).read_text().strip()
    if pk!=env['public_key']: raise RuntimeError837('STATE_PUBLIC_KEY_MISMATCH')
    if env['payload']['identity']['identity_public_key']!=pk: raise RuntimeError837('IDENTITY_KEY_MISMATCH')
    if rollback:
        head=_read_head(root); q=head['payload']; p=env['payload']; actual=sha256_bytes(canonical(env))
        if q['individual_id']!=p['identity']['individual_id'] or q['branch_id']!=p['identity']['branch_id']:
            raise RuntimeError837('STATE_COMMIT_IDENTITY_MISMATCH')
        if q['state_seq']!=p['continuity']['state_seq'] or q['state_sha256']!=actual:
            raise RuntimeError837('STATE_ROLLBACK_DETECTED')
        _tail_commit(root)
    return env

def load_verified_state(root):
    root=Path(root); return _verify_state_env(root,_load_json(root/STATE),rollback=True)

def _verify_invariants(p):
    try:
        if p['continuity']['state_seq']<0 or p['runtime']['tick']<0: return False
        if p['runtime']['simulated_seconds'] != p['runtime']['tick']*p['runtime']['tick_seconds']: return False
        if not (0<=p['resources']['energy']<=100 and p['resources']['metabolic_reserve']>=0 and p['resources']['compute_credit']>=0 and p['resources']['storage_credit']>=0 and 0<=p['health']['integrity']<=100): return False
        m=p['metabolism']; lhs=m['initial_total_energy']; rhs=p['resources']['energy']+p['resources']['metabolic_reserve']+m['cumulative_costs']['energy_burn']+m['cumulative_costs']['conversion_loss']
        if abs(lhs-rhs)>1e-5: return False
        if m['mode'] not in ('active','sleep','hibernating','dead'): return False
        if p['lifecycle']['status'] not in ('alive','dead'): return False
        if not p['identity']['individual_id'] or not p['identity']['lineage_id'] or not p['identity']['branch_id']: return False
        if not (-1<=p['affect']['valence']<=1 and 0<=p['affect']['arousal']<=1 and 0<=p['affect']['fatigue']<=1): return False
        if len(p['memory']['episodic'])>256 or len(p['memory']['autobiographical'])>128: return False
        if not _self_model_consistent(p): return False
        return True
    except Exception: return False

def recover(root):
    root=Path(root); wp=root/WAL
    if not wp.exists(): return False
    tx=_load_json(wp); pk=(root/PUB).read_text().strip()
    if tx.get('public_key')!=pk or not verify_obj(pk,tx['payload'],tx['signature']): raise RuntimeError837('WAL_SIGNATURE_INVALID')
    p=tx['payload']; event_path=root/p['event_rel']; state_path=root/STATE; commit_path=root/p['commit_rel']
    if event_path.exists() and sha256_bytes(event_path.read_bytes())!=p['event_file_sha256']: raise RuntimeError837('RECOVERY_EVENT_CONFLICT')
    if not event_path.exists(): atomic_write(event_path,canonical(p['event_env']))
    current_state_sha=sha256_bytes(state_path.read_bytes()) if state_path.exists() else None
    if current_state_sha not in (p['previous_state_file_sha256'],p['state_file_sha256']): raise RuntimeError837('RECOVERY_STATE_CONFLICT')
    if current_state_sha!=p['state_file_sha256']: atomic_write(state_path,canonical(p['state_env']))
    if commit_path.exists() and sha256_bytes(commit_path.read_bytes())!=p['commit_file_sha256']: raise RuntimeError837('RECOVERY_COMMIT_CONFLICT')
    if not commit_path.exists(): atomic_write(commit_path,canonical(p['commit_env']))
    head_path=root/HEAD
    current_head_sha=sha256_bytes(head_path.read_bytes()) if head_path.exists() else None
    if current_head_sha not in (p['previous_head_file_sha256'],p['head_file_sha256']): raise RuntimeError837('RECOVERY_HEAD_CONFLICT')
    if current_head_sha!=p['head_file_sha256']: atomic_write(head_path,canonical(p['head_env']))
    if p['checkpoint']: _checkpoint(root,p['state_env'])
    wp.unlink(); return True

def tick_once(root):
    root=Path(root)
    with writer_lock(root):
        recover(root)
        cur=load_verified_state(root); p=cur['payload']; sk=(root/KEY).read_text().strip(); pk=cur['public_key']
        if pub_from_private(sk)!=pk: raise RuntimeError837('PRIVATE_KEY_MISMATCH')
        if p['lifecycle']['status']!='alive': raise RuntimeError837('ORGANISM_NOT_ALIVE')
        obs=deterministic_observation(p['runtime']['tick']+1); action,reason=choose_action(p,obs)
        nxt,episode=apply_action(p,action,reason,obs)
        nxt['runtime']['tick']=p['runtime']['tick']+1; nxt['runtime']['simulated_seconds']=nxt['runtime']['tick']*nxt['runtime']['tick_seconds']
        if nxt['runtime']['tick']%60==0: _consolidate_autobiography(nxt)
        nxt['continuity']['state_seq']=p['continuity']['state_seq']+1
        nxt['continuity']['previous_state_sha256']=sha256_bytes(canonical(cur))
        seq=nxt['continuity']['state_seq']
        ev_payload={
          'schema':'tukuyo.organism_event.v837.1','individual_id':p['identity']['individual_id'],'branch_id':p['identity']['branch_id'],
          'state_seq':seq,'runtime_tick':nxt['runtime']['tick'],'previous_event_sha256':p['continuity']['event_head_sha256'],
          'action':action,'decision_reason':reason,'episode':episode,'post_energy':nxt['resources']['energy'],'post_reserve':nxt['resources']['metabolic_reserve'],'post_health':nxt['health']['integrity'],'metabolism_mode':nxt['metabolism']['mode'],
        }
        ev_env=_signed(ev_payload,sk,pk); ev_sha=sha256_bytes(canonical(ev_env)); nxt['continuity']['event_head_sha256']=ev_sha
        if not _verify_invariants(nxt):
            nxt['runtime']['invariant_violations']+=1; raise RuntimeError837('INVARIANT_VIOLATION')
        st_env=_signed(nxt,sk,pk); previous_head=_read_head(root); previous_commit_sha=previous_head['payload']['commit_sha256']
        commit_env=_commit_env_for(st_env,previous_commit_sha,sk,pk); head_env=_head_env_for(st_env,commit_env,sk,pk)
        event_rel=f'events/{seq:012d}.json'; commit_rel=f'state_commits/{seq:012d}.json'; checkpoint=(seq%nxt['runtime']['checkpoint_interval']==0)
        txp={
          'schema':'tukuyo.tick_tx.v837.1','state_seq':seq,
          'event_rel':event_rel,'event_env':ev_env,'event_file_sha256':ev_sha,
          'state_env':st_env,'state_file_sha256':sha256_bytes(canonical(st_env)),'previous_state_file_sha256':sha256_bytes(canonical(cur)),
          'commit_rel':commit_rel,'commit_env':commit_env,'commit_file_sha256':sha256_bytes(canonical(commit_env)),
          'head_env':head_env,'head_file_sha256':sha256_bytes(canonical(head_env)),'previous_head_file_sha256':sha256_bytes(canonical(previous_head)),
          'checkpoint':checkpoint,
        }
        tx={'payload':txp,'public_key':pk,'signature':sign_obj(sk,txp)}
        atomic_write(root/WAL,canonical(tx))
        if os.environ.get('TUKUYO_V837_CRASH_AFTER')=='wal': os._exit(91)
        atomic_write(_event_path(root,seq),canonical(ev_env))
        if os.environ.get('TUKUYO_V837_CRASH_AFTER')=='event': os._exit(92)
        atomic_write(root/STATE,canonical(st_env))
        if os.environ.get('TUKUYO_V837_CRASH_AFTER')=='state': os._exit(93)
        atomic_write(_commit_path(root,seq),canonical(commit_env))
        if os.environ.get('TUKUYO_V837_CRASH_AFTER')=='commit': os._exit(94)
        atomic_write(root/HEAD,canonical(head_env))
        if os.environ.get('TUKUYO_V837_CRASH_AFTER')=='head': os._exit(95)
        if checkpoint: _checkpoint(root,st_env)
        (root/WAL).unlink()
        return st_env

def run_ticks(root,n):
    out=None
    for _ in range(int(n)): out=tick_once(root)
    return out

def create_fork(parent_root, child_root, child_individual_id=None):
    parent_root=Path(parent_root); child_root=Path(child_root)
    if (parent_root/WAL).exists(): raise RuntimeError837('PARENT_PENDING_TRANSACTION')
    pa=audit(parent_root)
    if not pa['ok']: raise RuntimeError837('PARENT_AUDIT_FAILED')
    penv=load_verified_state(parent_root); p=penv['payload']; pid=p['identity']['individual_id']
    cid=child_individual_id or f'{pid}-fork-{uuid.uuid4().hex[:10]}'
    if cid==pid: raise RuntimeError837('SAME_INDIVIDUAL_ID_FORBIDDEN')
    child_root=_dirs(child_root)
    if (child_root/STATE).exists(): raise RuntimeError837('CHILD_ALREADY_INITIALIZED')
    sk,pk=new_keypair(); atomic_write(child_root/KEY,sk.encode()); os.chmod(child_root/KEY,0o600); atomic_write(child_root/PUB,pk.encode())
    inherited={
      'runtime_tick':p['runtime']['tick'],'simulated_seconds':p['runtime']['simulated_seconds'],
      'resources':p['resources'],'health':p['health'],'capabilities':p['capabilities'],'metabolism':p['metabolism'],'memory':p['memory'],
      'self_model':p['self_model'],'world_model':p['world_model'],'other_models':p['other_models'],'goals':p['goals'],
      'commitments':p['commitments'],'preferences':p['preferences'],'affect':p['affect'],'relationships':p['relationships'],
      'authority_receipts':p['authority_receipts'],'action_counts':p['runtime']['action_counts'],
      'fork_origin_state_sha256':sha256_bytes(canonical(penv)),
    }
    parent={'individual_id':pid,'branch_id':p['identity']['branch_id'],'fork_depth':p['lineage']['fork_depth']}
    c=_base_state(cid,p['identity']['lineage_id'],str(uuid.uuid4()),pk,parent=parent,inherited=inherited)
    env=_signed(c,sk,pk); commit=_commit_env_for(env,ZERO,sk,pk); head=_head_env_for(env,commit,sk,pk)
    atomic_write(child_root/STATE,canonical(env)); atomic_write(_commit_path(child_root,0),canonical(commit)); atomic_write(child_root/HEAD,canonical(head)); _checkpoint(child_root,env)
    return env

def audit(root):
    root=Path(root); errors=[]
    if (root/WAL).exists(): errors.append('pending_transaction')
    try: st=load_verified_state(root)
    except Exception as e: return {'ok':False,'errors':[str(e)]}
    p=st['payload']; seq=p['continuity']['state_seq']; pk=st['public_key']
    # event chain
    prev=ZERO
    for s in range(1,seq+1):
        ep=_event_path(root,s)
        if not ep.exists(): errors.append(f'missing_event:{s}'); break
        env=_load_json(ep)
        if not _verify(env): errors.append(f'event_signature:{s}'); break
        q=env['payload']
        if q['state_seq']!=s: errors.append(f'event_seq:{s}'); break
        if q['individual_id']!=p['identity']['individual_id'] or q['branch_id']!=p['identity']['branch_id']: errors.append(f'event_identity:{s}'); break
        if q['previous_event_sha256']!=prev: errors.append(f'event_chain:{s}'); break
        prev=sha256_bytes(canonical(env))
    if seq and prev!=p['continuity']['event_head_sha256']: errors.append('event_head_mismatch')
    # commit chain
    prev=ZERO
    for s in range(0,seq+1):
        cp=_commit_path(root,s)
        if not cp.exists(): errors.append(f'missing_commit:{s}'); break
        env=_load_json(cp)
        if not _verify(env): errors.append(f'commit_signature:{s}'); break
        q=env['payload']
        if q['state_seq']!=s: errors.append(f'commit_seq:{s}'); break
        if q['individual_id']!=p['identity']['individual_id'] or q['branch_id']!=p['identity']['branch_id']: errors.append(f'commit_identity:{s}'); break
        if q['previous_commit_sha256']!=prev: errors.append(f'commit_chain:{s}'); break
        prev=sha256_bytes(canonical(env))
    tail=_load_json(_commit_path(root,seq))['payload'] if _commit_path(root,seq).exists() else {}
    if tail.get('state_sha256')!=sha256_bytes(canonical(st)): errors.append('state_tail_hash_mismatch')
    if not _verify_invariants(p): errors.append('state_invariant')
    # uncommitted extra artifacts are evidence inconsistency, too.
    extra_events=[x for x in (root/'events').glob('*.json') if int(x.stem)>seq]
    extra_commits=[x for x in (root/'state_commits').glob('*.json') if int(x.stem)>seq]
    if extra_events: errors.append('extra_events_beyond_state')
    if extra_commits: errors.append('extra_commits_beyond_state')
    return {
      'ok':not errors,'errors':errors,'individual_id':p['identity']['individual_id'],'lineage_id':p['identity']['lineage_id'],
      'branch_id':p['identity']['branch_id'],'state_seq':seq,'tick':p['runtime']['tick'],'simulated_seconds':p['runtime']['simulated_seconds'],
      'energy':p['resources']['energy'],'metabolic_reserve':p['resources']['metabolic_reserve'],'health':p['health']['integrity'],'lifecycle':p['lifecycle']['status'],'metabolism_mode':p['metabolism']['mode'],'maintenance_debt':p['metabolism']['maintenance_debt'],'cumulative_energy_burn':p['metabolism']['cumulative_costs']['energy_burn'],'conversion_loss':p['metabolism']['cumulative_costs']['conversion_loss'],
      'policy_wrong':p['runtime']['policy_wrong'],'invariant_violations':p['runtime']['invariant_violations'],
      'episodic_memory':len(p['memory']['episodic']),'autobiographical_records':len(p['memory']['autobiographical']),
      'event_head_sha256':p['continuity']['event_head_sha256'],'autobiographical_records':len(p['memory']['autobiographical']),'autobiographical_records_evicted':p['memory']['autobiographical_archive']['records_evicted'],'learned_action_value':p['self_model']['learned_action_value'],'learned_action_count':p['self_model']['learned_action_count'],'self_model_source_sha256':p['self_model']['derived_from_autobiography_sha256'],
    }
