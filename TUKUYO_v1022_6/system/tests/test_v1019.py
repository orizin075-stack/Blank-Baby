from pathlib import Path
import json, os, subprocess, sys, tempfile
ROOT=Path(__file__).resolve().parents[1]; RUN=ROOT/'run_tukuyo.py'

def run(d,*args,ok=True):
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT/'src')}
    cmd=[sys.executable,'-B',str(RUN)]
    anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if anchor: cmd += ['--runtime-trust-file',anchor]
    cmd += ['--data',str(d),*map(str,args)]
    p=subprocess.run(cmd,cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
    try:r=json.loads(p.stdout) if p.stdout.strip() else {}
    except Exception: raise AssertionError(p.stdout+p.stderr)
    if ok and (p.returncode or not r.get('ok')): raise AssertionError((p.returncode,r,p.stderr))
    if not ok and p.returncode==0 and r.get('ok'): raise AssertionError(('expected fail',r))
    return r,p.returncode

def init(d,i): return run(d,'init','--individual-id',i)[0]
def kill(d):
    run(d,'organism2-update','INJURY','--amount','1');r,_=run(d,'organism2-update','INJURY','--amount','1');assert r['state']['lifecycle']=='DEAD'
def pub(d,p): return run(d,'succession-pubkey-export','--out',p)[0]

def test_v1019_selection_bounded_and_nonregressive():
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'P';init(d,'P');r,_=run(d,'evolution-select','research','--population','11','--seed','alpha');s=r['selection']
        assert s['selected_fitness']>=s['baseline_fitness'] and s['fitness_gain']>0 and s['max_abs_mutation']<=0.12
        assert run(d,'evolution-audit')[0]['ok'] and run(d,'whole-audit')[0]['ok']

def test_v1019_export_requires_selection_and_death():
    with tempfile.TemporaryDirectory() as t:
        td=Path(t);p=td/'P';c=td/'C';init(p,'P');init(c,'C');cp=td/'c.pub';pub(c,cp)
        r,_=run(p,'evolution-export','C','--out',td/'x.json','--child-public-key-file',cp,ok=False);assert 'SELECTION_REQUIRED' in r.get('error','')
        run(p,'evolution-select','resource');r,_=run(p,'evolution-export','C','--out',td/'x.json','--child-public-key-file',cp,ok=False);assert ('PARENT_NOT_IRREVERSIBLY_DEAD' in r.get('error','') or 'MORTALITY_STATE_REQUIRED' in r.get('error',''))

def test_v1019_three_generation_environment_shift_and_whole_state():
    with tempfile.TemporaryDirectory() as t:
        td=Path(t);p=td/'P';c=td/'C';g=td/'G';[init(d,i) for d,i in ((p,'P'),(c,'C'),(g,'G'))]
        secret='PRIVATE_V1019_'+os.urandom(8).hex();run(p,'heart-experience','learning','0.9','1.0','--theme',secret)
        run(p,'evolution-select','research','--population','11','--seed','p');kill(p);pp=td/'pc.json';ppub=td/'p.pub';cpub=td/'c.pub';pub(p,ppub);pub(c,cpub);run(p,'evolution-export','C','--out',pp,'--child-public-key-file',cpub);assert secret not in pp.read_text()
        ir,_=run(c,'evolution-import',pp,'--parent-trust-file',ppub);assert ir['generation']==1
        run(c,'evolution-select','social','--population','11','--seed','c');kill(c);cp=td/'cg.json';c2pub=td/'c2.pub';gpub=td/'g.pub';pub(c,c2pub);pub(g,gpub);run(c,'evolution-export','G','--out',cp,'--child-public-key-file',gpub);run(g,'evolution-import',cp,'--parent-trust-file',c2pub)
        gate,_=run(p,'evolution-gate-summary',c,g);assert gate['ok'] and all(gate['checks'].values())
        assert pp.stat().st_size < cp.stat().st_size < pp.stat().st_size*2
        for d in (p,c,g): assert run(d,'whole-audit')[0]['ok']

def test_v1019_wrapper_tamper_replay_and_wrong_child_rejected():
    with tempfile.TemporaryDirectory() as t:
        td=Path(t);p=td/'P';c=td/'C';x=td/'X';[init(d,i) for d,i in ((p,'P'),(c,'C'),(x,'X'))]
        run(p,'evolution-select','volatile');kill(p);ppub=td/'p.pub';cpub=td/'c.pub';pub(p,ppub);pub(c,cpub);pkg=td/'pc.json';run(p,'evolution-export','C','--out',pkg,'--child-public-key-file',cpub)
        bad=td/'bad.json';q=json.loads(pkg.read_text());q['evolution_capsule']['payload']['selected_evolution_profile']['curiosity']=0.999;bad.write_text(json.dumps(q,sort_keys=True,separators=(',',':')))
        r,_=run(c,'evolution-import',bad,'--parent-trust-file',ppub,ok=False);assert 'PACKAGE_HASH' in r.get('error','') or 'CAPSULE' in r.get('error','')
        r,_=run(x,'evolution-import',pkg,'--parent-trust-file',ppub,ok=False);assert 'WRONG_CHILD' in r.get('error','') or 'CHILD_KEY' in r.get('error','')
        run(c,'evolution-import',pkg,'--parent-trust-file',ppub);r,_=run(c,'evolution-import',pkg,'--parent-trust-file',ppub,ok=False);assert 'PACKAGE_REPLAY' in r.get('error','')

def test_v1019_inherited_profile_changes_live_heart_score():
    with tempfile.TemporaryDirectory() as t:
        td=Path(t);p=td/'P';c=td/'C';init(p,'P');init(c,'C');run(p,'evolution-select','research','--seed','live');kill(p);ppub=td/'p.pub';cpub=td/'c.pub';pub(p,ppub);pub(c,cpub);pkg=td/'pc.json';run(p,'evolution-export','C','--out',pkg,'--child-public-key-file',cpub);imp,_=run(c,'evolution-import',pkg,'--parent-trust-file',ppub)
        opts=td/'o.json';opts.write_text(json.dumps([{'id':'EXPLORE','signals':{'curiosity':1.0}},{'id':'WAIT','signals':{}}]))
        r,_=run(c,'heart-choose',opts,'--context','v1019-live');assert r['chosen']=='EXPLORE'
        score=[x['score'] for x in r['scores'] if x['id']=='EXPLORE'][0];assert abs(score-imp['runtime_inherited_value_profile']['curiosity'])<1e-9

def test_v1019_hundred_generation_trait_budget_prevents_trivial_all_one():
    from tukuyo_v1019.evolution import _candidates,DEFAULT_VALUES,TRAIT_BUDGET
    base=dict(DEFAULT_VALUES);envs=['research','social','resource','volatile'];seen=[]
    for g in range(100):
        env=envs[g%4];cs=_candidates(base,env,11,f'g{g}','fam-test',g);w=max(cs,key=lambda c:(c['fitness'],c['candidate_id']));base=dict(w['profile']);seen.append(tuple(base[k] for k in sorted(base)))
        assert abs(sum(base.values())-TRAIT_BUDGET)<1e-5
    assert any(v<0.5 for v in base.values())
    assert len(set(seen[-12:]))>1
