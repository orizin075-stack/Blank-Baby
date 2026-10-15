from pathlib import Path
import base64,copy,hashlib,json,os,shutil,subprocess,sys,tempfile,time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from tukuyo_v977.whole_state import canon,sha_obj
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'run_tukuyo.py';VER=ROOT/'tools/v1015_4_independent_verifier.py'

def run(d,*args,ok=True,env=None):
    e={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT/'src'),'TUKUYO_ENDURANCE_RUNNER_SESSION':'v1015-4-test'};e.update(env or {})
    cmd=[sys.executable,'-B',str(RUN)];anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if anchor:cmd += ['--runtime-trust-file',anchor]
    cmd += ['--data',str(d),*map(str,args)]
    p=subprocess.run(cmd,cwd=ROOT,env=e,text=True,capture_output=True,timeout=240)
    try:r=json.loads(p.stdout) if p.stdout.strip() else {}
    except Exception:raise AssertionError(p.stdout+p.stderr)
    if ok and (p.returncode!=0 or not r.get('ok',False)):raise AssertionError((p.returncode,p.stdout,p.stderr))
    return r,p.returncode

def keypair(base,name='w'):
    sk=Ed25519PrivateKey.generate();kp=base/(name+'.key');pp=base/(name+'.pub');kp.write_text(base64.b64encode(sk.private_bytes_raw()).decode());pp.write_text(base64.b64encode(sk.public_key().public_bytes_raw()).decode());return sk,kp,pp

def sign(sk,req,out):
    r=json.loads(Path(req).read_text());pub=base64.b64encode(sk.public_key().public_bytes_raw()).decode();p={'schema':'tukuyo.v1013.witness_payload/1','run_id':r['run_id'],'identity':r['identity'],'seq':r['seq'],'head_sha256':r['head_sha256'],'request_sha256':r['request_sha256'],'witnessed_utc_ns':time.time_ns()};env={'schema':'tukuyo.v1013.witness_receipt/1','payload':p,'public_key':pub,'signature':base64.b64encode(sk.sign(canon(p))).decode()};Path(out).write_bytes(canon(env)+b'\n');return out

def publisher_anchor():
    p=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR');assert p and Path(p).is_file(),p;return Path(p)

def independent(bundle,pub_anchor,wit_anchor,ok=True):
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':''}
    p=subprocess.run([sys.executable,'-B',str(VER),str(bundle),'--publisher-trust-file',str(pub_anchor),'--witness-trust-file',str(wit_anchor)],cwd=Path(bundle).parent,env=env,text=True,capture_output=True,timeout=120)
    try:r=json.loads(p.stdout)
    except Exception:raise AssertionError(p.stdout+p.stderr)
    if ok and (p.returncode or not r.get('ok')):raise AssertionError((p.returncode,r,p.stderr))
    if not ok and p.returncode==0:raise AssertionError(('expected failure',r))
    return r

def make_success(td):
    d=td/'data';w=td/'w';w.mkdir();sk,_,pub=keypair(w);run(d,'init','--individual-id','V10154-SUCCESS')
    x,_=run(d,'endurance-exec-init','--profile','24h','--target-seconds','1','--tick-seconds','10','--checkpoint-seconds','30','--witness-seconds','10','--living-seconds','10')
    sr=w/'start.json';sign(sk,x['start_witness_request'],sr);a,_=run(d,'endurance-exec-accept-witness',sr,'--witness-trust-file',pub);assert a['phase']=='RUNNING'
    time.sleep(1.05);p,_=run(d,'endurance-exec-pump')
    for _ in range(4):
        if p.get('witness_request'):break
        time.sleep(.2);p,_=run(d,'endurance-exec-pump')
    assert p.get('witness_request'),p
    er=w/'end.json';sign(sk,p['witness_request'],er);f,_=run(d,'endurance-exec-accept-witness',er,'--witness-trust-file',pub);assert f['phase']=='PROTOCOL_COMPLETE',f
    out=td/'portable.json';r,_=run(d,'endurance-repro-export','--out',out,'--witness-trust-file',pub);assert r['outcome']=='SUCCESS'
    return d,pub,out

def test_success_bundle_is_portable_and_independently_verified_without_data_root():
    with tempfile.TemporaryDirectory() as td0:
        td=Path(td0);d,pub,bundle=make_success(td);saved=td/'saved.json';shutil.copy2(bundle,saved);shutil.rmtree(d)
        r=independent(saved,publisher_anchor(),pub);assert r['outcome']=='SUCCESS' and r['detail']['claim_boundary']['formal_duration_complete'] and not r['claim_boundary']['24h_completed'],r
        assert r['claim_boundary']['portable_no_data_root_required'] and not r['claim_boundary']['independent_verifier_imports_tukuyo_modules']

def test_realtime_tamper_rejected_even_if_inner_and_outer_hashes_recomputed():
    with tempfile.TemporaryDirectory() as td0:
        td=Path(td0);d,pub,bundle=make_success(td);x=json.loads(bundle.read_text());src=x['source_evidence'];src['realtime_events'][0]['payload']['note']='forged'
        z=dict(src);z.pop('bundle_sha256',None);src['bundle_sha256']=sha_obj(z);x.pop('bundle_sha256',None);x['bundle_sha256']=sha_obj(x);bad=td/'tampered.json';bad.write_bytes(canon(x)+b'\n')
        r=independent(bad,publisher_anchor(),pub,False);assert any('REALTIME_EVENT_SIGNATURE' in e for e in r['errors']),r

def test_release_manifest_or_binding_tamper_is_rejected():
    with tempfile.TemporaryDirectory() as td0:
        td=Path(td0);d,pub,bundle=make_success(td);x=json.loads(bundle.read_text())
        mb=base64.b64decode(x['release_manifest_bytes_b64']);m=json.loads(mb);m['version']='v9999';x['release_manifest_bytes_b64']=base64.b64encode(canon(m)).decode();x['release_binding']['manifest_sha256']='0'*64
        x.pop('bundle_sha256',None);x['bundle_sha256']=sha_obj(x);bad=td/'release_forged.json';bad.write_bytes(canon(x)+b'\n')
        r=independent(bad,publisher_anchor(),pub,False);assert any(e.startswith('RELEASE_') for e in r['errors']),r

def test_external_witness_trust_swap_is_rejected():
    with tempfile.TemporaryDirectory() as td0:
        td=Path(td0);d,pub,bundle=make_success(td);other=td/'other';other.mkdir();_,_,pub2=keypair(other,'x')
        r=independent(bundle,publisher_anchor(),pub2,False);assert 'BUNDLE_WITNESS_TRUST_MISMATCH' in r['errors'] or any('WITNESS' in e for e in r['errors']),r

def test_failure_bundle_is_portable_but_can_never_be_promoted_to_success():
    with tempfile.TemporaryDirectory() as td0:
        td=Path(td0);d=td/'data';w=td/'w';w.mkdir();_,_,pub=keypair(w);run(d,'init','--individual-id','V10154-FAIL');run(d,'endurance-exec-init','--profile','24h','--target-seconds','30','--tick-seconds','10');a,_=run(d,'endurance-exec-abort','--reason','negative_control');assert a['terminal_state']=='FAILED'
        bundle=td/'failure_portable.json';e,_=run(d,'endurance-repro-export','--out',bundle,'--witness-trust-file',pub);assert e['outcome']=='FAILURE'
        good=independent(bundle,publisher_anchor(),pub);assert good['outcome']=='FAILURE' and not good['claim_boundary']['24h_completed']
        x=json.loads(bundle.read_text());src=x['source_evidence'];src['claim_boundary']['24h_completed']=True;z=dict(src);z.pop('bundle_sha256',None);src['bundle_sha256']=sha_obj(z);x.pop('bundle_sha256',None);x['bundle_sha256']=sha_obj(x);bad=td/'forged_success.json';bad.write_bytes(canon(x)+b'\n')
        r=independent(bad,publisher_anchor(),pub,False);assert 'FAILURE_SUCCESS_CLAIM' in r['errors'],r
