"""v1022.7.8: one individual, one history (evidence_gen4/REVIEW_2026-10-13.md §3). The CLI with a canon kept outside the
data directory (TUKUYO_CANON): a copy, a branch, a backup put back and a copy of one that died are refused; the owner
says which copy is the individual. Without a canon nothing changes."""
import json,os,shutil,subprocess,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
Q='Tom has 3 apples. He buys 4 more apples. How many apples does he have now?'

def _cli(canon=None):
    env={k:v for k,v in os.environ.items() if not k.startswith(('TUKUYO_ANTHROPIC','TUKUYO_OPENAI','TUKUYO_GEMINI','TUKUYO_LLM','TUKUYO_CRASH','TUKUYO_CHATGPT','TUKUYO_CANON','TUKUYO_G4_WITNESS'))}
    env['PYTHONDONTWRITEBYTECODE']='1'
    if canon:env['TUKUYO_CANON']=str(canon)
    cmd=[sys.executable,'-B',str(ROOT/'run_tukuyo.py')];anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if anchor:cmd+=['--runtime-trust-file',anchor]
    def cli(d,*a):
        p=subprocess.run(cmd+['--data',str(d),*a],cwd=ROOT,env=env,capture_output=True,text=True,timeout=300)
        try:return json.loads(p.stdout)
        except ValueError:return {'ok':False,'rc':p.returncode,'stderr':p.stderr[-400:]}
    return cli

def test_a_copy_a_branch_and_a_put_back_backup_are_told(tmp_path):
    canon=tmp_path/'canon';C=_cli(canon);plain=_cli()
    a=tmp_path/'a';assert C(a,'init','--individual-id','CANON-TEST')['ok'];assert C(a,'organism2-init')['ok']
    assert C(a,'g4-solve','--llm','off','--',Q)['answer']=='7'
    st=C(a,'identity-canon-status');assert st['state']=='IN_SYNC' and st['lines']>=2
    shutil.copytree(a,tmp_path/'backup');shutil.copytree(a,tmp_path/'copy');shutil.copytree(a,tmp_path/'branch')
    # the copy: the individual lives on, the copy is left behind
    assert C(a,'g4-solve','--llm','off','--',Q)['answer']=='7'
    r=C(tmp_path/'copy','g4-solve','--llm','off','--',Q);assert not r['ok'] and r['error'].endswith('CANON_BEHIND')
    assert C(tmp_path/'copy','whole-audit')['errors']==['CANON_BEHIND'] and C(a,'whole-audit')['ok']
    assert C(tmp_path/'copy','identity-canon-status')['state']=='BEHIND'          # looking is never refused
    # the branch: it lived on by itself without the canon; it may not come back, and it does not take the turn by looking
    assert plain(tmp_path/'branch','organism2-update','REST','--amount','0.2')['ok']
    r=C(tmp_path/'branch','g4-solve','--llm','off','--',Q);assert not r['ok'] and r['error'].endswith('CANON_BRANCH')
    assert C(tmp_path/'branch','whole-audit')['errors']==['CANON_BRANCH']
    assert C(a,'g4-solve','--llm','off','--',Q)['answer']=='7'
    # the backup put back: refused until the owner says it is the individual; then the newer copy is left behind
    shutil.move(str(a),str(tmp_path/'newer'));shutil.copytree(tmp_path/'backup',a)
    r=C(a,'g4-solve','--llm','off','--',Q);assert r['error'].endswith('CANON_BEHIND')
    look=C(a,'identity-canon-adopt');assert look['ok'] and look['adopted'] is None and look['would_record']=='restore'
    assert C(a,'identity-canon-adopt','--yes')['adopted']['kind']=='restore'
    assert C(a,'g4-solve','--llm','off','--',Q)['answer']=='7'
    assert C(tmp_path/'newer','g4-solve','--llm','off','--',Q)['error'].endswith('CANON_BEHIND')
    au=C(a,'identity-canon-audit');assert au['ok'] and au['kinds'].get('restore')==1 and au['kinds'].get('genesis')==1
    # without a canon, nothing changes (as before v1022.7.8): every copy lives on
    assert plain(tmp_path/'copy','g4-solve','--llm','off','--',Q)['answer']=='7' and plain(tmp_path/'copy','whole-audit')['ok']

def test_a_copy_of_an_individual_that_died_does_not_live_on(tmp_path):
    canon=tmp_path/'canon';C=_cli(canon)
    a=tmp_path/'a';assert C(a,'init','--individual-id','CANON-DEATH')['ok'];assert C(a,'organism2-init')['ok']
    shutil.copytree(a,tmp_path/'before_death')
    for _ in range(6):C(a,'organism2-update','INJURY','--amount','1.0')
    assert C(a,'organism2-status')['state']['death_irreversible'] is True
    au=C(a,'identity-canon-audit');assert au['ok'] and au['state']=='DEAD_SELF' and au['kinds'].get('death')==1
    r=C(tmp_path/'before_death','g4-solve','--llm','off','--',Q);assert not r['ok'] and r['error'].endswith('CANON_DEAD')
    assert C(tmp_path/'before_death','whole-audit')['errors']==['CANON_DEAD'] and C(a,'whole-audit')['ok']
    r=C(tmp_path/'before_death','identity-canon-adopt','--yes');assert not r['ok'] and r['error'].endswith('CANON_DEAD_NOT_ADOPTED')

def test_the_canon_is_kept_outside_and_is_its_own(tmp_path):
    from tukuyo_v1022 import canon as K
    canon=tmp_path/'canon';C=_cli(canon)
    a=tmp_path/'a';assert C(a,'init','--individual-id','CANON-OWN')['ok'];assert C(a,'organism2-init')['ok']
    inside=_cli(a/'canon_here');r=inside(a,'organism2-update','REST');assert not r['ok'] and r['error'].endswith('CANON_INSIDE_DATA')
    # a command that stopped after it changed the individual, before its line: the next one goes on (its mark is there)
    os.environ[K.ENV]=str(canon)
    try:
        K.guard(a,'organism2-update');p=a/'v1007'/'ORGANISM2_STATE.json';s=json.loads(p.read_text());s['energy']=s['energy']-1
        p.write_text(json.dumps(s))                                   # changed, and no line written
        assert K.status(a)['state']=='IN_SYNC'
    finally:os.environ.pop(K.ENV,None)
    assert C(a,'organism2-update','REST')['ok'] and C(a,'identity-canon-audit')['ok']
    # a line changed by hand is not the individual's
    f=next(canon.glob('*.canon.jsonl'));ls=f.read_text().splitlines();e=json.loads(ls[-1]);e['payload']['kind']='restore'
    f.write_text('\n'.join(ls[:-1]+[json.dumps(e)])+'\n')
    r=C(a,'organism2-update','REST');assert not r['ok'] and 'CANON_NOT_ITS_OWN' in r['error']
