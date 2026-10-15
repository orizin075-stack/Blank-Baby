from pathlib import Path
import base64,json,os,subprocess,sys,tempfile,time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from tukuyo_v977.whole_state import canon,sha_obj
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'run_tukuyo.py'

def run(d,*args,ok=True,env=None):
    e={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT/'src')};e.update(env or {})
    cmd=[sys.executable,'-B',str(RUN)]
    anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if anchor:cmd += ['--runtime-trust-file',anchor]
    cmd += ['--data',str(d),*map(str,args)]
    p=subprocess.run(cmd,cwd=ROOT,env=e,text=True,capture_output=True,timeout=180)
    try:r=json.loads(p.stdout) if p.stdout.strip() else {}
    except Exception:raise AssertionError(p.stdout+p.stderr)
    if ok and (p.returncode!=0 or not r.get('ok',False)):raise AssertionError(p.stdout+p.stderr)
    return r,p.returncode

def keypair(base):
    sk=Ed25519PrivateKey.generate();kp=base/'w.key';pp=base/'w.pub';kp.write_text(base64.b64encode(sk.private_bytes_raw()).decode());pp.write_text(base64.b64encode(sk.public_key().public_bytes_raw()).decode());return sk,kp,pp

def sign(sk,req,out):
    r=json.loads(Path(req).read_text());pub=base64.b64encode(sk.public_key().public_bytes_raw()).decode();p={'schema':'tukuyo.v1013.witness_payload/1','run_id':r['run_id'],'identity':r['identity'],'seq':r['seq'],'head_sha256':r['head_sha256'],'request_sha256':r['request_sha256'],'witnessed_utc_ns':time.time_ns()};env={'schema':'tukuyo.v1013.witness_receipt/1','payload':p,'public_key':pub,'signature':base64.b64encode(sk.sign(canon(p))).decode()};Path(out).write_bytes(canon(env)+b'\n');return out

def init_exec(d,session='runner-A',target='30',tick='10'):
    run(d,'init','--individual-id','V10153-TEST',env={'TUKUYO_ENDURANCE_RUNNER_SESSION':session})
    return run(d,'endurance-exec-init','--profile','24h','--target-seconds',target,'--tick-seconds',tick,'--checkpoint-seconds','30','--witness-seconds',tick,'--living-seconds','30',env={'TUKUYO_ENDURANCE_RUNNER_SESSION':session})[0]

def test_runner_restart_is_counted_by_runner_session_not_cli_process():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';init_exec(d,'runner-A')
        a,_=run(d,'endurance-exec-resume','--note','same runner',env={'TUKUYO_ENDURANCE_RUNNER_SESSION':'runner-A'})
        assert a['runner_session_count']==1 and a['resume_count']==0,a
        b,_=run(d,'endurance-exec-resume','--note','runner restarted',env={'TUKUYO_ENDURANCE_RUNNER_SESSION':'runner-B'})
        assert b['runner_session_count']==2 and b['resume_count']==1,b
        c,_=run(d,'endurance-exec-resume','--note','same restarted runner',env={'TUKUYO_ENDURANCE_RUNNER_SESSION':'runner-B'})
        assert c['runner_session_count']==2 and c['resume_count']==1,c

def test_resume_gap_becomes_irreversible_terminal_failure_with_evidence():
    with tempfile.TemporaryDirectory() as td:
        td=Path(td);d=td/'d';w=td/'w';w.mkdir();sk,kp,pub=keypair(w);x=init_exec(d,'runner-A','30','1')
        sr=w/'start.json';sign(sk,x['start_witness_request'],sr);run(d,'endurance-exec-accept-witness',sr,'--witness-trust-file',pub,env={'TUKUYO_ENDURANCE_RUNNER_SESSION':'runner-A'})
        run(d,'endurance-exec-pump',env={'TUKUYO_ENDURANCE_RUNNER_SESSION':'runner-A'})
        p=d/'v1015_2'/'EXECUTION_STATE.json';st=json.loads(p.read_text());st['last_pump_utc_ns']=time.time_ns()-6_000_000_000;p.write_text(json.dumps(st,ensure_ascii=False,sort_keys=True)+'\n')
        bad,rc=run(d,'endurance-exec-resume','--witness-trust-file',pub,'--note','late restart',ok=False,env={'TUKUYO_ENDURANCE_RUNNER_SESSION':'runner-B'})
        assert rc!=0 and bad['terminal_state']=='FAILED' and any('RESUME_TICK_GAP_EXCEEDED' in e for e in bad['errors']),bad
        fp=Path(bad['failure_evidence']);assert fp.is_file()
        fa,_=run(d,'endurance-failure-evidence-audit',fp,'--witness-trust-file',pub);assert fa['ok'] and not fa['claim_boundary']['24h_completed'],fa
        again,rc=run(d,'endurance-exec-pump',ok=False,env={'TUKUYO_ENDURANCE_RUNNER_SESSION':'runner-C'});assert rc!=0 and again['phase']=='FAILED',again

def test_operator_abort_is_terminal_and_failure_record_is_auditable():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';init_exec(d)
        a,_=run(d,'endurance-exec-abort','--reason','maintenance_cancelled');assert a['terminal_state']=='FAILED',a
        fp=Path(a['failure_evidence']);fa,_=run(d,'endurance-failure-evidence-audit',fp);assert fa['ok'] and fa['claim_boundary']['failure_evidence_is_auditable_not_successful'],fa
        au,rc=run(d,'endurance-exec-audit',ok=False);assert rc!=0 and au['record_ok'] and not au['protocol_success'],au
        p,rc=run(d,'endurance-exec-pump',ok=False);assert rc!=0 and p['phase']=='FAILED',p

def test_failure_bundle_cannot_be_rewritten_into_success_claim():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';init_exec(d);a,_=run(d,'endurance-exec-abort','--reason','negative_control');fp=Path(a['failure_evidence'])
        x=json.loads(fp.read_text());x['claim_boundary']['24h_completed']=True;x.pop('bundle_sha256',None);x['bundle_sha256']=sha_obj(x);bad=Path(td)/'forged.json';bad.write_bytes(canon(x)+b'\n')
        r,rc=run(d,'endurance-failure-evidence-audit',bad,ok=False);assert rc!=0 and 'FAILURE_BUNDLE_SUCCESS_CLAIM' in r['errors'],r

def test_release_binding_mismatch_fails_closed():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';init_exec(d)
        p=d/'v1015_3'/'RESUME_STATE.json';st=json.loads(p.read_text());st['release_binding']['manifest_sha256']='0'*64;p.write_text(json.dumps(st,ensure_ascii=False,sort_keys=True)+'\n')
        r,rc=run(d,'endurance-exec-resume','--note','mismatched release',ok=False,env={'TUKUYO_ENDURANCE_RUNNER_SESSION':'runner-B'})
        assert rc!=0 and r['terminal_state']=='FAILED' and any('RELEASE_BINDING_CHANGED:manifest_sha256' in e for e in r['errors']),r
