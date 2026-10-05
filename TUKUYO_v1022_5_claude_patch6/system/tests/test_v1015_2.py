from pathlib import Path
import base64,json,os,subprocess,sys,tempfile,time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from tukuyo_v977.whole_state import canon
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'run_tukuyo.py'

def run(d,*args,ok=True):
    e={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT/'src')}
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

def test_execution_waits_for_external_start_witness():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','V10152-WAIT');x,_=run(d,'endurance-exec-init','--profile','24h','--target-seconds','30','--tick-seconds','10','--checkpoint-seconds','30','--witness-seconds','5','--living-seconds','10')
        p,_=run(d,'endurance-exec-pump');assert p['phase']=='WAITING_START_WITNESS' and p['waiting_for']['kind']=='START',p

def test_short_authenticated_protocol_never_claims_24h():
    with tempfile.TemporaryDirectory() as td:
        td=Path(td);d=td/'d';w=td/'external';w.mkdir();sk,kp,pub=keypair(w)
        run(d,'init','--individual-id','V10152-SHORT');x,_=run(d,'endurance-exec-init','--profile','24h','--target-seconds','1','--tick-seconds','10','--checkpoint-seconds','30','--witness-seconds','5','--living-seconds','10')
        sr=w/'start.json';sign(sk,x['start_witness_request'],sr);a,_=run(d,'endurance-exec-accept-witness',sr,'--witness-trust-file',pub);assert a['phase']=='RUNNING',a
        time.sleep(1.05);p,_=run(d,'endurance-exec-pump')
        if not p.get('witness_request'):
            time.sleep(.2);p,_=run(d,'endurance-exec-pump')
        assert p.get('witness_request') and p['phase']=='FINAL_WITNESS_PENDING',p
        er=w/'end.json';sign(sk,p['witness_request'],er);f,_=run(d,'endurance-exec-accept-witness',er,'--witness-trust-file',pub);assert f['phase']=='PROTOCOL_COMPLETE' and f['evidence_audit']['ok'],f
        cb=f['evidence_audit']['claim_boundary'];assert cb['formal_duration_complete'] and not cb['24h_completed'] and not cb['72h_completed'] and not cb['7day_completed'],f
        z,_=run(d,'endurance-exec-audit','--witness-trust-file',pub);assert z['ok'] and not z['claim_boundary']['24h_completed'],z

def test_witness_trust_rotation_is_rejected():
    with tempfile.TemporaryDirectory() as td:
        td=Path(td);d=td/'d';w1=td/'w1';w2=td/'w2';w1.mkdir();w2.mkdir();sk1,k1,p1=keypair(w1);sk2,k2,p2=keypair(w2)
        run(d,'init','--individual-id','V10152-ROT');x,_=run(d,'endurance-exec-init','--profile','24h','--target-seconds','30','--tick-seconds','10','--checkpoint-seconds','30','--witness-seconds','1','--living-seconds','30')
        r1=w1/'s.json';sign(sk1,x['start_witness_request'],r1);run(d,'endurance-exec-accept-witness',r1,'--witness-trust-file',p1)
        time.sleep(1.05);p,_=run(d,'endurance-exec-pump');rq=p.get('witness_request')
        if not rq:
            time.sleep(.2);p,_=run(d,'endurance-exec-pump');rq=p.get('witness_request')
        assert rq,p
        r2=w2/'m.json';sign(sk2,rq,r2);bad,rc=run(d,'endurance-exec-accept-witness',r2,'--witness-trust-file',p2,ok=False);assert rc!=0 and bad['errors']==['WITNESS_TRUST_ROTATION_NOT_AUTHORIZED'],bad

def test_witness_agent_rejects_private_key_inside_data_root():
    with tempfile.TemporaryDirectory() as td:
        td=Path(td);d=td/'d';d.mkdir();sk=Ed25519PrivateKey.generate();k=d/'secret.key';k.write_text(base64.b64encode(sk.private_bytes_raw()).decode());req=d/'r.json';req.write_text('{}')
        p=subprocess.run([sys.executable,'-B',str(ROOT/'tools/v1015_2_witness_agent.py'),'sign',str(req),'--private-key',str(k),'--out',str(td/'o.json'),'--data-root',str(d)],cwd=ROOT,text=True,capture_output=True)
        assert p.returncode!=0 and 'WITNESS_PRIVATE_KEY_MUST_BE_OUTSIDE_DATA_ROOT' in p.stdout,p.stdout+p.stderr
