import ast, copy, json, os
from pathlib import Path
import pytest
from tukuyo_g4 import api
from tukuyo_v1023r import development as policy, niche
from tukuyo_v1023r.agent import ResearchAgent
from tukuyo_v1022 import developmental_life as dev, metabolism
from test_v1019 import run
from test_v1019_1 import fingerprint, crash

@pytest.mark.parametrize('owner,item,unit',[
    ('ユーナ','ノート','冊'),('凛','ビー玉','個'),
    ('ミーラ','カード','枚'),('葵','ケーキ','個')])
def test_long_vowel_is_preserved_in_names_and_items(owner,item,unit):
    q=f'{owner}は{item}を13{unit}持っています。{owner}は{item}を4{unit}買いました。今、{owner}は{item}を何{unit}持っていますか？'
    assert api.solve(q,llm='off')['answer']=='17'
    q=f'{owner}は{item}を何{unit}か持っています。{owner}は{item}を4{unit}買いました。今、{owner}は{item}を何{unit}持っていますか？'
    assert api.solve(q,llm='off')['answer'] is None

def pick(options,weights):
    return max(options,key=lambda o:(round(sum(weights.get(k,0)*v for k,v in o['signals'].items()),6),o['id']))['id']

VALUES={'curiosity':.4,'truthfulness':.75,'survival':.8,'integrity':.8}

def test_need_and_experience_generate_different_goals_from_the_same_model():
    a=ResearchAgent();m=policy.memory();args=(100,50000,{0:0,1:0},niche.ECON)
    full=policy.propose(a,m,9500,*args);hungry=policy.propose(a,m,3000,*args)
    assert pick(full,VALUES)=='learn_rule' and pick(hungry,VALUES)=='secure_energy'
    experienced=copy.deepcopy(m);experienced['failures']=[{'seq':i,'x':i} for i in (1,2,3)]
    repair=policy.propose(a,experienced,9500,*args)
    assert pick(repair,VALUES)=='repair_prediction'
    # Removing experience removes the repair goal, not just its printed label.
    assert 'repair_prediction' not in {o['id'] for o in full}

def test_soul_value_ablation_changes_the_action():
    a=ResearchAgent();m=policy.memory();locked={0:0,1:0}
    opts=policy.propose(a,m,8500,100,50000,locked,niche.ECON)
    curious=pick(opts,{**VALUES,'curiosity':1.,'survival':.1})
    frugal=pick(opts,{**VALUES,'curiosity':0.,'survival':1.})
    assert curious=='learn_rule' and frugal=='secure_energy'
    assert policy.enact(a,m,curious,8500,100,50000,locked,niche.ECON,1)[1]=='probe'
    assert policy.enact(a,m,frugal,8500,100,50000,locked,niche.ECON,1)[1]=='work'

def test_empty_reservoir_does_not_create_imaginary_income():
    a=ResearchAgent();m=policy.memory()
    opts=policy.propose(a,m,6500,100,0,{0:0,1:0},niche.ECON)
    assert pick(opts,VALUES)=='rest'
    assert policy.enact(a,m,'secure_energy',6500,100,0,{0:0,1:0},niche.ECON,1)[1]=='rest'

def test_failure_retires_the_model_without_erasing_episodes():
    a=ResearchAgent();a.observe({'kind':'work','n':0,'x':1,'y':1})
    m=policy.memory();m['failures']=[{'seq':i,'x':i} for i in (1,2,3)]
    b,act,x,reset=policy.enact(a,m,'repair_prediction',9000,100,50000,{0:0,1:0},niche.ECON,4)
    assert reset and act=='probe' and x==3 and b.to_compact()['n_obs']==0
    assert a.to_compact()['n_obs']==1 and len(m['failures'])==3

def test_planner_has_no_secret_environment_or_runtime_access():
    tree=ast.parse((Path(__file__).resolve().parents[1]/'src/tukuyo_v1023r/development.py').read_text())
    imports=[]
    for n in ast.walk(tree):
        if isinstance(n,ast.Import):imports.extend(x.name for x in n.names)
        elif isinstance(n,ast.ImportFrom):imports.append(n.module)
    assert set(imports)=={'__future__','copy','agent'}
    assert 'seed' not in policy.propose.__code__.co_varnames
    assert 'world' not in policy.enact.__code__.co_varnames

def test_goal_writes_require_the_owner_transaction(tmp_path):
    with pytest.raises(ValueError,match='DEVELOPMENT_OWNER_TRANSACTION_REQUIRED'):
        dev.prepare(tmp_path,ResearchAgent(),{0:0,1:0},6500,100,50000,niche.ECON)
    with pytest.raises(ValueError,match='DEVELOPMENT_OWNER_TRANSACTION_REQUIRED'):
        dev.complete(tmp_path,{},ResearchAgent(),None,0,0)
    assert not list(tmp_path.iterdir())

def start(d,seed='development-38',actions=True,max_age=64):
    run(d,'init','--individual-id','DEVELOPMENT-TEST','--blank-learning')
    args=['metabolism-init','--families','2','--seed',seed,'--reservoir','90000',
          '--regeneration','2200','--max-age',str(max_age),'--developmental-goals']
    if not actions:args.append('--no-actions')
    return run(d,*args)[0]

def test_real_runtime_teacher_free_goals_restart_and_recovery(tmp_path):
    d=tmp_path/'d';start(d)
    run(d,'metabolism-step','--ticks','16')
    st=metabolism.preflight(d)
    for rid in st['active']:
        p=metabolism.child(d,rid);s=dev.load(p)
        assert len(s['episodes'])==16 and s['individual_id']==st['runtimes'][rid]['individual_id']
        assert s['last_agent']==st['research']['runtimes'][rid]['agent']
        assert {r['origin'] for r in s['episodes']}=={'simulation'}
        assert run(p,'developmental-audit')[0]['ok']
    saved={r:dev.load(metabolism.child(d,r)) for r in st['active']}
    assert any(s['memory']['switches']>0 for s in saved.values())
    assert any(r['credit']>0 for s in saved.values() for r in s['episodes'])
    run(d,'realtime-start');run(d,'realtime-tick')
    cp=run(d,'recovery-checkpoint')[0]
    for _ in range(3):
        run(d,'metabolism-step','--ticks','2')
        run(d,'recovery-restore',cp['path'],'--trust-file',d/'v1014/recovery.pub')
        assert run(d,'metabolism-audit')[0]['tick']==16
        assert run(d,'whole-audit')[0]['ok']
        for r,s in saved.items():assert dev.load(metabolism.child(d,r))==s
    run(d,'metabolism-step','--ticks','1')
    assert run(d,'metabolism-audit')[0]['tick']==17

def test_no_actions_control_has_no_learning_or_rewards(tmp_path):
    d=tmp_path/'d';start(d,actions=False)
    st=run(d,'metabolism-step','--ticks','4')[0]
    assert st['attempts']==0 and st['living_energy']==10600
    for rid in ('R000000','R000001'):
        s=dev.load(metabolism.child(d,rid))
        assert all(r['action']=='rest' and r['credit']==0 and r['observation'] is None for r in s['episodes'])
        assert dev.audit(metabolism.child(d,rid))['ok']

def test_development_before_save_crash_rolls_back_all_bytes(tmp_path):
    d=tmp_path/'d';start(d);before=fingerprint(d)
    crash(d,'development:before_save','metabolism-step','--ticks','1')
    assert run(d,'metabolism-audit')[0]['tick']==0
    assert fingerprint(d)==before and run(d,'whole-audit')[0]['ok']

def test_forged_goal_cache_is_not_adopted(tmp_path):
    d=tmp_path/'d';start(d);run(d,'metabolism-step','--ticks','1')
    p=metabolism.child(d,'R000000');f=p/dev.NS/'STATE.json';o=json.loads(f.read_text())
    o['state']['episodes'][0]['goal']='secure_energy';f.write_text(json.dumps(o))
    assert not dev.audit(p)['ok'] and not metabolism.audit(d)['ok']
