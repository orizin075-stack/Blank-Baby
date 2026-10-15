import ast,base64,copy,json
from pathlib import Path
import pytest
from tukuyo_v1023r import adaptive_development as policy,niche
from tukuyo_v1023r.agent import ResearchAgent
from tukuyo_v1022 import adaptive_life as dev,metabolism
from tukuyo_v977 import whole_state as whole
from tukuyo_v1018 import succession
from tukuyo_v1019.transaction import ACTIVE
from test_v1019 import run
from test_v1019_1 import fingerprint,crash

def pick(opts):
    w={'curiosity':.4,'truthfulness':.75,'survival':.8,'integrity':.8}
    return max(opts,key=lambda o:(round(sum(w.get(k,0)*v for k,v in o['signals'].items())-.3*o['signals'].get('threat',0),6),o['id']))['id']
def row(seq,goal,o,p,reset=False):
    return {'seq':seq,'goal':goal,'observation':o,'prediction':p,'reset_model':reset,
            'surprise':o is not None and abs(o['y']-p)>=.8,'progress':False}

def test_noise_free_counterexample_quarantines_and_retires_model():
    a=ResearchAgent();m=policy.memory()
    for i in range(10):a.observe({'kind':'work','n':i,'x':0,'y':1})
    assert a.p_on(0)>.99
    o={'kind':'work','n':10,'x':0,'y':0};m=policy.advance(m,row(11,'secure_energy',o,a.p_on(0)))
    assert m['pending_shift']==11 and '0' in m['blocked']
    opts=policy.propose(a,m,3800,100,50000,{0:0,1:0},niche.ECON)
    assert pick(opts)=='repair_prediction' and 'secure_energy' not in {o['id'] for o in opts}
    b,act,x,reset=policy.enact(a,m,'repair_prediction',3800,100,50000,{0:0,1:0},niche.ECON,12)
    assert reset and act=='probe' and b.to_compact()['n_obs']==1 and a.to_compact()['n_obs']==10
    assert b.p_on(0)<a.p_on(0)

def test_one_noisy_conflict_requires_replication_before_reset():
    m=policy.memory();o={'kind':'probe','n':0,'x':0,'y':0}
    m=policy.advance(m,row(1,'learn_rule',o,.99));assert m['pending_shift'] is None
    m=policy.advance(m,row(2,'repair_prediction',{**o,'n':1},.99));assert m['pending_shift']==1

def test_failed_work_needs_two_positive_retests_to_unblock():
    m=policy.advance(policy.memory(),row(1,'secure_energy',{'kind':'work','n':0,'x':4,'y':0},.6))
    m=policy.advance(m,row(2,'learn_rule',{'kind':'probe','n':0,'x':4,'y':1},.5));assert '4' in m['blocked']
    m=policy.advance(m,row(3,'learn_rule',{'kind':'probe','n':1,'x':4,'y':1},.5));assert '4' not in m['blocked']

def test_table_cell_information_and_total_energy_feasibility():
    a=ResearchAgent();a.method='TABLE';m=policy.memory()
    for i in range(20):a.observe({'kind':'probe','n':i,'x':0,'y':1})
    assert policy.experiment(a,m,{},9000)!=0
    opts=policy.propose(a,m,3000,100,50000,{0:0,1:0},{**niche.ECON,'reward':550})
    assert 'secure_energy' not in {o['id'] for o in opts}

def test_policy_has_no_secret_schedule_or_runtime_access():
    tree=ast.parse((Path(__file__).resolve().parents[1]/'src/tukuyo_v1023r/adaptive_development.py').read_text());imports=[]
    for n in ast.walk(tree):
        if isinstance(n,ast.Import):imports.extend(x.name for x in n.names)
        elif isinstance(n,ast.ImportFrom):imports.append(n.module)
    assert set(imports)=={'__future__','copy','agent','development'}
    assert not {'seed','phase','interval','global_tick'}&set(policy.propose.__code__.co_varnames)
    assert not {'seed','phase','interval','global_tick'}&set(policy.enact.__code__.co_varnames)

def test_adaptive_writes_require_owner_transaction(tmp_path):
    with pytest.raises(ValueError,match='ADAPTIVE_OWNER_TRANSACTION_REQUIRED'):
        dev.prepare(tmp_path,ResearchAgent(),{},6500,32,90000,niche.ECON,1)
    assert not list(tmp_path.iterdir())

def start(d,age=16,actions=True,culture=True):
    run(d,'init','--individual-id','ADAPTIVE-TEST','--blank-learning')
    args=['metabolism-init','--families','2','--seed','development-38','--reservoir','90000','--regeneration','2200',
          '--max-age',str(age),'--adaptive-goals','--world-change-interval','8','--max-ticks','1024']
    if not actions:args.append('--no-actions')
    if not culture:args.append('--no-research-culture')
    return run(d,*args)[0]

def test_real_culture_signature_parent_recipient_scope_new_biography(tmp_path):
    d=tmp_path/'d';start(d,age=8);run(d,'metabolism-step','--ticks','9');s=metabolism.preflight(d)
    event=next(e for e in s['successions'] if e['public_observations_commitment']);p=metabolism.child(d,event['parent']);c=metabolism.child(d,event['child'])
    cs=dev.load(c);env=dev._seed(c);pl=env['payload']
    assert cs['episode_count']==1 and cs['initial_agent']['n_obs']>0 and cs['initial_agent']['status']!='CONFIRMED'
    assert pl['confirmed_truth'] is False and pl['origin']=='simulation'
    assert pl['target_individual_id']==cs['individual_id'] and pl['source_individual_id']!=cs['individual_id']
    assert set(pl['observations'][0])=={'global_tick','observation'}
    assert dev.audit(c,use_memo=False)['ok'] and run(c,'whole-audit')[0]['ok']
    assert whole._key_paths(c)[1].read_text()!=whole._key_paths(p)[1].read_text()
    assert whole.soul_path(c).read_bytes()!=whole.soul_path(p).read_bytes()
    token=ACTIVE.set(True)
    try:
        with pytest.raises(ValueError,match='ADAPTIVE_SEED_REPLAY'):dev.import_seed(c,env,pl['environment_commitment'])
    finally:ACTIVE.reset(token)
    with pytest.raises(ValueError,match='ADAPTIVE_SEED_SCOPE'):dev._seed(c,'0'*64)
    forged=copy.deepcopy(env);forged['payload']['target_individual_id']='OTHER'
    sk,pub=succession._ensure_key(p);forged['signature']=base64.b64encode(sk.sign(whole.canon(forged['payload']))).decode()
    dev.seed_path(c).write_bytes(whole.canon(forged)+b'\n')
    assert not dev.audit(c,use_memo=False)['ok'] and not metabolism.audit(d)['ok']

def test_real_no_actions_and_culture_off_controls(tmp_path):
    d=tmp_path/'passive';start(d,age=128,actions=False);s=run(d,'metabolism-step','--ticks','24')[0]
    assert s['active_runtime_count']==0 and s['correct']==0 and s['actual_successions']==0
    assert {e['cause'] for e in s['deaths']}=={'ENERGY'} and run(d,'whole-audit')[0]['ok']
    d=tmp_path/'culture-off';start(d,age=8,culture=False);s=run(d,'metabolism-step','--ticks','8')[0]
    assert s['actual_successions']>=1
    for e in s['successions']:
        c=metabolism.child(d,e['child']);assert not dev.seed_path(c).exists()
        assert dev.initial_agent(c).to_compact()['n_obs']==0

def test_journal_tamper_rejected_in_memo_and_fresh_replay(tmp_path):
    d=tmp_path/'d';start(d);run(d,'metabolism-step','--ticks','4');p=metabolism.child(d,'R000000');assert dev.audit(p)['ok']
    data=dev.journal(p).read_bytes();r=json.loads(data.splitlines()[0]);r['goal']='FORGED'
    dev.journal(p).write_bytes(whole.canon(r)+b'\n'+b'\n'.join(data.splitlines()[1:])+b'\n')
    assert not dev.audit(p)['ok'] and not dev.audit(p,use_memo=False)['ok']
    assert not run(p,'whole-audit',ok=False)[0]['ok'] and not metabolism.audit(d)['ok']

def test_journal_crash_rolls_back_prepared_crash_redoes(tmp_path):
    d=tmp_path/'d';start(d);before=fingerprint(d)
    crash(d,'adaptive:after_journal','metabolism-step','--ticks','1')
    assert run(d,'metabolism-audit')[0]['tick']==0 and fingerprint(d)==before
    crash(d,'lineage:after_prepare','metabolism-step','--ticks','1')
    assert run(d,'metabolism-audit')[0]['tick']==1 and run(d,'whole-audit')[0]['ok']

def test_nested_restore_preserves_journal_seed_and_private_keys(tmp_path):
    d=tmp_path/'d';start(d,age=8);run(d,'metabolism-step','--ticks','9');run(d,'realtime-start');cp=run(d,'recovery-checkpoint')[0]
    s=metabolism.preflight(d)
    saved={rid:{'state':dev.load(metabolism.child(d,rid)),'key':whole._key_paths(metabolism.child(d,rid))[0].read_bytes()} for rid in s['runtimes']}
    for _ in range(3):
        run(d,'metabolism-step','--ticks','2');run(d,'recovery-restore',cp['path'],'--trust-file',d/'v1014/recovery.pub')
        assert run(d,'metabolism-audit')[0]['tick']==9 and run(d,'whole-audit')[0]['ok']
        for rid,old in saved.items():
            p=metabolism.child(d,rid);assert dev.load(p)==old['state'] and whole._key_paths(p)[0].read_bytes()==old['key']
    run(d,'metabolism-step','--ticks','1');assert run(d,'metabolism-audit')[0]['tick']==10

def test_owner_frontier_applies_before_newborn_child_reads_future_files(tmp_path):
    d=tmp_path/'d';start(d,age=8);run(d,'metabolism-step','--ticks','8');run(d,'realtime-start')
    cp=run(d,'recovery-checkpoint')[0];s=metabolism.preflight(d);rid=s['active'][0];p=metabolism.child(d,rid)
    before={q.relative_to(p).as_posix() for q in p.rglob('*') if q.is_file()}
    assert dev.load(p)['episode_count']==0 and dev.seed_path(p).exists()
    run(d,'metabolism-step','--ticks','1')
    future={q.relative_to(p).as_posix():q.read_bytes() for q in p.rglob('*') if q.is_file()
            and q.relative_to(p).as_posix() not in before and 'private' not in q.relative_to(p).parts}
    assert 'adaptive_life/commits/000000000001.json' in future
    for _ in range(3):
        run(d,'recovery-restore',cp['path'],'--trust-file',d/'v1014/recovery.pub')
        # Reproduce late future reappearance, then read the child directly.
        # No owner CLI is called in between to clean up on its behalf.
        for rel,b in future.items():
            q=p/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
        assert dev.audit(p,use_memo=False)['ok']
        assert run(p,'adaptive-audit')[0]['episodes']==0
        assert run(p,'whole-audit')[0]['ok'] and run(d,'whole-audit')[0]['ok']
        assert not (p/dev.NS/'commits').exists()
    # The same legitimate future remains possible after rollback.
    run(d,'metabolism-step','--ticks','1');assert run(d,'metabolism-audit')[0]['tick']==9

@pytest.mark.parametrize('damage',['extra','core','private_extra'])
def test_prepared_publication_accepts_only_extra_managed_files(damage,tmp_path):
    from tukuyo_v1014 import recovery
    d=tmp_path/'d';start(d,age=8);run(d,'metabolism-step','--ticks','8');run(d,'realtime-start')
    cp=run(d,'recovery-checkpoint')[0]
    crash(d,'restore:after_namespace_swap','recovery-restore',cp['path'],'--trust-file',d/'v1014/recovery.pub')
    extra=d/'v1022_ecology/runtimes/R000002/adaptive_life/FUTURE.json';extra.parent.mkdir(parents=True,exist_ok=True);extra.write_text('{}')
    if damage=='core':(d/'v977/SOUL_CORE.json').write_text('{}')
    elif damage=='private_extra':(d/'v1014/private/UNAUTHORIZED.key').write_text('test-only-not-a-key')
    before=fingerprint(d)
    if damage!='extra':
        with pytest.raises(ValueError,match='RESTORE_SWAP_READBACK'):recovery.recover_incomplete_restore(d)
        assert fingerprint(d)==before and recovery._swap_marker(d).exists()
    else:
        result=recovery.recover_incomplete_restore(d);assert result['ok'] and not extra.exists()
        receipts=list((d/'v1014/private/prepared_restore_quarantine').glob('*/QUARANTINE_RECEIPT.json'))
        assert len(receipts)==1
        assert run(d,'whole-audit')[0]['ok'] and run(d,'metabolism-audit')[0]['tick']==8
