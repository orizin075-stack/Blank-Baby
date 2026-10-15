import copy,json,os,shutil,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
from test_v1022_5_fusion import ROOT,run
from tukuyo_v1022 import identity_ledger as il
from tukuyo_v977 import whole_state as whole
from tukuyo_v978 import heart_loop as heart
from tukuyo_g4 import api,solve,check
def cli(data,*args,ledger=None,crash=None):
    c=[sys.executable,'-B',str(ROOT/'run_tukuyo.py')]
    if ledger:c+=['--identity-ledger',str(ledger),'--identity-ledger-trust-file',str(ledger/'witness.pub')]
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    if crash:env['TUKUYO_CRASH_POINT']=crash
    p=subprocess.run(c+['--data',str(data),*map(str,args)],capture_output=True,text=True,env=env,timeout=240)
    return p if crash else (p.returncode,json.loads(p.stdout))
def files(d):return {p.relative_to(d).as_posix():p.read_bytes() for p in Path(d).rglob('*') if p.is_file()}
def fixture(tmp_path):
    d=tmp_path/'parent';run(d,'init','--individual-id','HISTORY-PARENT');l=tmp_path/'outboard';il.create(l);il.enroll(d,l,l/'witness.pub');return d,l
@pytest.mark.parametrize('phrase',['a few','several','some','an unknown number of','an unspecified number of','an undetermined number of','an unreported number of','a small number of','a handful of'])
def test_unknown_initial_stock_is_not_zero(phrase):
    assert api.solve(f'Nora has {phrase} pencils. Nora buys 6 more pencils. How many pencils does Nora have now?',llm='off')['answer'] is None
def test_independent_checker_rejects_old_formal_correct_but_incomplete_translation():
    text='Anna has a few apples. She buys 4 more apples. How many apples now?'
    spec={'schema':'tukuyo.g4.fpl/1','lang':'en','text':text,'quantities':[{'name':'gain','unit':'apple','integer':True}],'facts':[{'eq':'gain = 4','span':'4 more apples'}],'ask':'gain','answer_unit':'apple','unused':[]}
    answer=solve.solve(spec);assert answer['ok'];r=check.check(spec,answer['values']);assert not r['ok'] and 'UNKNOWN_QUANTITY_NOT_ACCOUNTED' in r['failures']
    forged=copy.deepcopy(spec);forged['quantities'][0]['unknown_source']={'start':0,'text':'Anna has a few apples.'};assert not check.check(forged,answer['values'])['ok']
    isolated=copy.deepcopy(spec);isolated['quantities'].append({'name':'start','unit':'apple','integer':True,'unknown_source':{'start':0,'text':'Anna has a few apples.'}});assert not check.check(isolated,{'gain':'4','start':'7'})['ok']
def test_exact_stock_and_irrelevant_unknown_do_not_get_blanket_refusal():
    assert api.solve('Maria has 18 marbles and buys 7 marbles. How many marbles does she have now?',llm='off')['answer']=='25'
    assert api.solve('Nora has 9 pencils and some apples. How many pencils does Nora have?',llm='off')['answer']=='9'
def test_cli_unknown_is_withheld_in_both_public_routes(tmp_path):
    d=tmp_path/'d';run(d,'init');q='Anna has a few apples. She buys 4 more apples. How many apples now?';assert run(d,'g4-solve',q,'--llm','off')['answer'] is None;r=run(d,'think',q,'--llm','off');assert r['answer'] is None and r['uncertain'];assert run(d,'whole-audit')['ok']
def test_unwitnessed_clone_histories_are_locally_valid_but_external_fork_is_rejected(tmp_path):
    d,l=fixture(tmp_path);a=tmp_path/'a';b=tmp_path/'b';shutil.copytree(d,a);shutil.copytree(d,b)
    for root,theme in ((a,'fork-X'),(b,'fork-Y')):heart.process_experience(root,'learning',.8,.8,theme);whole.sync(root);assert whole.audit(root)['ok']
    assert whole._live_identity(a)==whole._live_identity(b) and whole._key_paths(a)[1].read_bytes()==whole._key_paths(b)[1].read_bytes()
    il.publish(a,l,l/'witness.pub');before=files(b)
    with pytest.raises(ValueError,match='HISTORY_FORK'):il.publish(b,l,l/'witness.pub')
    assert files(b)==before
def test_guarded_duplicate_writers_have_only_one_canonical_advancement(tmp_path):
    d,l=fixture(tmp_path);a=tmp_path/'a';b=tmp_path/'b';shutil.copytree(d,a);shutil.copytree(d,b)
    with ThreadPoolExecutor(2) as pool:outcomes=list(pool.map(lambda row:cli(row[0],'heart-experience','learning','.8','.8','--theme',row[1],ledger=l),[(a,'parallel-X'),(b,'parallel-Y')]))
    assert sorted(c for c,r in outcomes)==[0,1];good=[root for root,(code,_) in zip((a,b),outcomes) if code==0][0];assert il.check(good,l,l/'witness.pub')['ok']
def test_registered_cli_cannot_silently_drop_witness(tmp_path):
    d,l=fixture(tmp_path);before=files(d);code,r=cli(d,'heart-experience','learning','.8','.8');assert code and 'EXTERNAL_WITNESS_REQUIRED' in r['error'];assert files(d)==before
def test_same_id_and_key_clone_cannot_register_as_a_new_branch(tmp_path):
    d,l=fixture(tmp_path);c=tmp_path/'copy';shutil.copytree(d,c)
    with pytest.raises(ValueError,match='DISTINCT_ID_AND_KEY'):il.register_branch(d,c,l,l/'witness.pub')
def test_explicit_living_branch_uses_a_distinct_identity_and_keys(tmp_path):
    d,l=fixture(tmp_path);c=tmp_path/'child';run(c,'init','--individual-id','BRANCH-CHILD');r=il.register_branch(d,c,l,l/'witness.pub');assert r['new_identity_required'] and r['death_successor'] is False;assert il.check(c,l,l/'witness.pub')['ok'] and il.check(d,l,l/'witness.pub')['ok']
def test_old_checkpoint_cannot_rewind_registered_canonical_history(tmp_path):
    d,l=fixture(tmp_path);c=tmp_path/'old';shutil.copytree(d,c);assert cli(d,'heart-experience','learning','.8','.8','--theme','future',ledger=l)[0]==0
    with pytest.raises(ValueError,match='RESTORED_OR_ROLLED_BACK'):il.check(c,l,l/'witness.pub')
    before=files(d);code,r=cli(d,'recovery-restore','unused-checkpoint.json',ledger=l);assert code and 'RESTORE_REQUIRES_DISTINCT_BRANCH' in r['error'];assert files(d)==before
def test_witnessed_death_rejects_alive_backup(tmp_path):
    d,l=fixture(tmp_path);old=tmp_path/'old';shutil.copytree(d,old);assert cli(d,'organism2-init',ledger=l)[0]==0
    for _ in range(3):
        code,r=cli(d,'organism2-update','INJURY','--amount','1',ledger=l)
        if code:break
    assert il.check(d,l,l/'witness.pub')['observed_lifecycle']=='DEAD'
    with pytest.raises(ValueError,match='DEAD_RESTORE'):il.check(old,l,l/'witness.pub')
def test_external_key_and_ledger_cannot_be_inside_individual(tmp_path):
    d=tmp_path/'d';run(d,'init');l=d/'ledger';il.create(l)
    with pytest.raises(ValueError,match='OUTSIDE_INDIVIDUAL'):il.enroll(d,l,l/'witness.pub')
def test_missing_receipt_recovers_only_exact_witnessed_state(tmp_path):
    d,l=fixture(tmp_path);p=d/il.NS/'RECEIPT.json';original=p.read_bytes();p.unlink();assert il.recover_receipt(d,l,l/'witness.pub')['ok'] and p.read_bytes()==original
    heart.process_experience(d,'learning',.8,.8,'unpublished');whole.sync(d);p.unlink()
    with pytest.raises(ValueError,match='RECOVERY_HEAD'):il.recover_receipt(d,l,l/'witness.pub')
def test_wrong_pin_tampered_journal_and_deleted_binding_fail_closed(tmp_path):
    d,l=fixture(tmp_path);fake=tmp_path/'fake';il.create(fake)
    with pytest.raises(ValueError,match='TRUST_PIN'):il.check(d,l,fake/'witness.pub')
    p=l/'JOURNAL.jsonl';raw=p.read_bytes();env=json.loads(raw);env['payload']['snapshot']['lifecycle']='DEAD';p.write_text(json.dumps(env)+'\n')
    with pytest.raises(ValueError,match='SIGNATURE'):il.check(d,l,l/'witness.pub')
    p.write_bytes(raw);(d/il.NS/'BINDING.json').unlink();assert il.requires(d) and not whole.audit(d)['ok']
@pytest.mark.parametrize('point',['identity_ledger:after_prepare','identity_ledger:after_journal'])
def test_external_commit_crash_redoes_once_and_recovers_local_receipt(tmp_path,point):
    d,l=fixture(tmp_path);heart.process_experience(d,'learning',.8,.8,'ahead');whole.sync(d);p=cli(d,'identity-ledger-publish',ledger=l,crash=point);assert p.returncode in (-9,137);code,r=cli(d,'identity-ledger-recover-receipt',ledger=l);assert code==0 and r['exact_witnessed_state_required'];assert il.check(d,l,l/'witness.pub')['ok'];assert len((l/'JOURNAL.jsonl').read_text().splitlines())==2
def test_reused_individual_id_with_a_new_whole_key_cannot_enroll(tmp_path):
    d,l=fixture(tmp_path);other=tmp_path/'other';run(other,'init','--individual-id','HISTORY-PARENT');assert whole._key_paths(d)[1].read_bytes()!=whole._key_paths(other)[1].read_bytes();before=files(other)
    with pytest.raises(ValueError,match='ID_OR_KEY_ALREADY_REGISTERED'):il.enroll(other,l,l/'witness.pub')
    assert files(other)==before
def test_standalone_verifier_checks_current_branch_and_rejects_stale_copy(tmp_path):
    d,l=fixture(tmp_path);old=tmp_path/'old';shutil.copytree(d,old);assert cli(d,'heart-experience','learning','.8','.8','--theme','next',ledger=l)[0]==0
    def raw(root):
        p=subprocess.run([sys.executable,'-B',str(ROOT/'tools/identity_ledger_verifier.py'),'--ledger',str(l),'--trust-file',str(l/'witness.pub'),'--data',str(root)],capture_output=True,text=True);return p.returncode,json.loads(p.stdout)
    code,r=raw(d);assert code==0 and r['events']==2 and not r['physical_uniqueness_proven'];code,r=raw(old);assert code==1 and 'LOCAL_STALE_OR_FORKED' in str(r['errors'])
    child=tmp_path/'child';run(child,'init','--individual-id','BRANCH-RAW');il.register_branch(d,child,l,l/'witness.pub');assert raw(child)[0]==0 and raw(d)[0]==0
def test_missing_witness_refuses_and_whole_ledger_rollback_is_an_explicit_boundary(tmp_path):
    d,l=fixture(tmp_path);old=tmp_path/'old';oldledger=tmp_path/'oldledger';shutil.copytree(d,old);shutil.copytree(l,oldledger);assert cli(d,'heart-experience','learning','.8','.8','--theme','next',ledger=l)[0]==0;assert cli(d,'whole-audit',ledger=tmp_path/'missing')[0]==1
    with pytest.raises(ValueError,match='RESTORED_OR_ROLLED_BACK'):il.check(old,l,l/'witness.pub')
    assert il.check(old,oldledger,oldledger/'witness.pub')['ok']
