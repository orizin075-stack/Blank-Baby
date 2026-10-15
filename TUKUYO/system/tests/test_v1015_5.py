from pathlib import Path
import base64,copy,hashlib,json,os,shutil,subprocess,sys,tempfile,time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'run_tukuyo.py';VER=ROOT/'tools/v1015_5_independent_verifier.py'
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha_obj(x):return hashlib.sha256(canon(x)).hexdigest()
def run(d,*args,ok=True):
 e={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT/'src'),'TUKUYO_ENDURANCE_RUNNER_SESSION':'v1015-5-test'};cmd=[sys.executable,'-B',str(RUN)];a=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR');
 if a:cmd += ['--runtime-trust-file',a]
 cmd += ['--data',str(d),*map(str,args)];p=subprocess.run(cmd,cwd=ROOT,env=e,text=True,capture_output=True,timeout=240)
 try:r=json.loads(p.stdout) if p.stdout.strip() else {}
 except Exception:raise AssertionError(p.stdout+p.stderr)
 if ok and (p.returncode or not r.get('ok')):raise AssertionError((p.returncode,r,p.stderr))
 if not ok and p.returncode==0 and r.get('ok'):raise AssertionError(('expected fail',r))
 return r,p.returncode
def kp(td,name):
 sk=Ed25519PrivateKey.generate();pr=td/f'{name}.key';pu=td/f'{name}.pub';pr.write_text(base64.b64encode(sk.private_bytes_raw()).decode());pu.write_text(base64.b64encode(sk.public_key().public_bytes_raw()).decode());return sk,pr,pu
def manifest_sha():return hashlib.sha256((ROOT/'META/RELEASE_MANIFEST.json').read_bytes()).hexdigest()
def issue(td,sk,pub,profile='24h',ttl=120,nonce=None):
 now=time.time_ns();p={'schema':'tukuyo.v1015_5.challenge_payload/1','nonce':nonce or os.urandom(32).hex(),'issued_utc_ns':now,'expires_utc_ns':now+int(ttl*1e9),'profile':profile,'release_manifest_sha256':manifest_sha(),'subject':'fresh-test'};p['challenge_id']=sha_obj(p);env={'schema':'tukuyo.v1015_5.challenge/1','payload':p,'public_key':pub.read_text().strip(),'signature':base64.b64encode(sk.sign(canon(p))).decode()};q=td/f'ch-{p["challenge_id"][:8]}.json';q.write_bytes(canon(env)+b'\n');return q
def sign_witness(sk,req,out):
 r=json.loads(Path(req).read_text());pub=base64.b64encode(sk.public_key().public_bytes_raw()).decode();p={'schema':'tukuyo.v1013.witness_payload/1','run_id':r['run_id'],'identity':r['identity'],'seq':r['seq'],'head_sha256':r['head_sha256'],'request_sha256':r['request_sha256'],'witnessed_utc_ns':time.time_ns()};env={'schema':'tukuyo.v1013.witness_receipt/1','payload':p,'public_key':pub,'signature':base64.b64encode(sk.sign(canon(p))).decode()};Path(out).write_bytes(canon(env)+b'\n')
def publisher():
 a=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR');assert a and Path(a).is_file();return Path(a)
def indep(bundle,wpub,cpub,ch,ok=True):
 p=subprocess.run([sys.executable,'-B',str(VER),str(bundle),'--publisher-trust-file',str(publisher()),'--witness-trust-file',str(wpub),'--challenge-trust-file',str(cpub),'--expected-challenge-file',str(ch)],cwd=bundle.parent,env={**os.environ,'PYTHONPATH':'','PYTHONDONTWRITEBYTECODE':'1'},text=True,capture_output=True,timeout=120);r=json.loads(p.stdout)
 if ok and (p.returncode or not r.get('ok')):raise AssertionError((p.returncode,r,p.stderr))
 if not ok and p.returncode==0:raise AssertionError(('expected reject',r))
 return r
def make_success(td,ch=None):
 d=td/'data';keys=td/'keys';keys.mkdir(exist_ok=True);wsk,_,wpub=kp(keys,'w');csk,_,cpub=kp(keys,'c');ch=ch or issue(td,csk,cpub);run(d,'init','--individual-id','V10155')
 s,_=run(d,'endurance-challenge-init','--challenge-file',ch,'--challenge-trust-file',cpub,'--profile','24h','--target-seconds','1','--tick-seconds','10','--checkpoint-seconds','30','--witness-seconds','10','--living-seconds','10')
 sr=td/'start.json';sign_witness(wsk,s['start_witness_request'],sr);run(d,'endurance-exec-accept-witness',sr,'--witness-trust-file',wpub);time.sleep(1.05);p,_=run(d,'endurance-exec-pump')
 for _ in range(4):
  if p.get('witness_request'):break
  time.sleep(.15);p,_=run(d,'endurance-exec-pump')
 assert p.get('witness_request'),p
 er=td/'end.json';sign_witness(wsk,p['witness_request'],er);f,_=run(d,'endurance-exec-accept-witness',er,'--witness-trust-file',wpub);assert f['phase']=='PROTOCOL_COMPLETE',f
 out=td/'challenged.json';run(d,'endurance-challenge-repro-export','--out',out,'--witness-trust-file',wpub,'--challenge-trust-file',cpub)
 return d,wpub,cpub,ch,out,csk
def test_fresh_challenge_success_portable_after_data_root_deleted():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);d,w,c,ch,b,_=make_success(td);saved=td/'saved.json';shutil.copy2(b,saved);shutil.rmtree(d);r=indep(saved,w,c,ch);assert r['claim_boundary']['fresh_external_challenge_verified'] and not r['claim_boundary']['24h_completed']
def test_prior_success_bundle_rejected_against_new_external_challenge():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);d,w,c,ch,b,csk=make_success(td);ch2=issue(td,csk,c,nonce='11'*32);r=indep(b,w,c,ch2,False);assert 'EXPECTED_CHALLENGE_MISMATCH' in r['errors'] or 'CHALLENGE_BINDING' in r['errors'],r
def test_expired_challenge_rejected_before_campaign_start():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);keys=td/'k';keys.mkdir();sk,_,pub=kp(keys,'c');ch=issue(td,sk,pub,ttl=-1);d=td/'d';run(d,'init','--individual-id','EXP');r,_=run(d,'endurance-challenge-init','--challenge-file',ch,'--challenge-trust-file',pub,'--profile','24h','--target-seconds','1',ok=False);assert 'CHALLENGE_EXPIRED' in r.get('errors',[]),r
def test_challenge_trust_swap_and_tamper_rejected():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);d,w,c,ch,b,_=make_success(td);k=td/'other';k.mkdir();_,_,c2=kp(k,'x');r=indep(b,w,c2,ch,False);assert any('CHALLENGE' in x for x in r['errors'])
  x=json.loads(b.read_text());x['challenge_envelope']['payload']['subject']='forged';x.pop('bundle_sha256',None);x['bundle_sha256']=sha_obj(x);bad=td/'bad.json';bad.write_bytes(canon(x)+b'\n');r=indep(bad,w,c,ch,False);assert any('CHALLENGE' in q for q in r['errors'])
def test_failure_bundle_also_bound_to_fresh_challenge():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);keys=td/'k';keys.mkdir();_,_,wpub=kp(keys,'w');csk,_,cpub=kp(keys,'c');ch=issue(td,csk,cpub);d=td/'d';run(d,'init','--individual-id','FAIL');run(d,'endurance-challenge-init','--challenge-file',ch,'--challenge-trust-file',cpub,'--profile','24h','--target-seconds','30','--tick-seconds','10');run(d,'endurance-exec-abort','--reason','negative');out=td/'fail.json';e,_=run(d,'endurance-challenge-repro-export','--out',out,'--witness-trust-file',wpub,'--challenge-trust-file',cpub);assert e['outcome']=='FAILURE';r=indep(out,wpub,cpub,ch);assert r['outcome']=='FAILURE'
