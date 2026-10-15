#!/usr/bin/env python3
import argparse,base64,datetime,email.utils,hashlib,json,pathlib,ssl,time,urllib.request,subprocess,sys,urllib.parse,os
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
HERE=pathlib.Path(__file__).resolve().parents[1];WD=HERE/'wallclock';LEDGER=WD/'ledger.json';KEY=WD/'host_private_key.pem';PUB=WD/'host_public_key.b64'
def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def H(b):return hashlib.sha256(b).hexdigest()
def dir_hash(root):
 root=pathlib.Path(root).resolve();items=[]
 for p in sorted(root.rglob('*')):
  if p.is_symlink():raise RuntimeError('symlink in fork state')
  if p.is_file():items.append({'path':p.relative_to(root).as_posix(),'sha256':H(p.read_bytes()),'bytes':p.stat().st_size})
 return H(canon(items))
def probe_hash(root,script):
 q=subprocess.run([sys.executable,str(script),str(root)],capture_output=True,text=True,timeout=20)
 if q.returncode!=0:raise RuntimeError('probe failed')
 try:o=json.loads(q.stdout)
 except Exception:raise RuntimeError('probe output not json')
 return H(canon(o))
def anchor_dates():
 urls=['https://www.python.org/','https://pypi.org/','https://www.cloudflare.com/'];vals=[];raw=[];hosts=set()
 for u in urls:
  try:
   q=urllib.request.Request(u,method='HEAD',headers={'User-Agent':'tukuyo-v932-anchor'})
   with urllib.request.urlopen(q,timeout=8,context=ssl.create_default_context()) as r:d=r.headers.get('Date')
   ts=int(email.utils.parsedate_to_datetime(d).timestamp());host=urllib.parse.urlparse(u).hostname;vals.append(ts);hosts.add(host);raw.append({'url':u,'date':d,'unix':ts})
  except Exception as e:raw.append({'url':u,'error':type(e).__name__})
 if len(vals)<2 or len(hosts)<2:raise RuntimeError('need >=2 independent hosts')
 if max(vals)-min(vals)>300:raise RuntimeError('anchor disagreement')
 vals.sort();return vals[len(vals)//2],raw
def sign_entry(payload,sk):return {'payload':payload,'signature_b64':base64.b64encode(sk.sign(canon(payload))).decode()}
def load_key():return serialization.load_pem_private_key(KEY.read_bytes(),password=None)
def snapshot(cfg):
 return {'A':{'byte':dir_hash(cfg['fork_a']),'behavior':probe_hash(cfg['fork_a'],cfg['probe_script'])},'B':{'byte':dir_hash(cfg['fork_b']),'behavior':probe_hash(cfg['fork_b'],cfg['probe_script'])}}
def init(a):
 if LEDGER.exists():raise RuntimeError('ledger already exists; refusing reset')
 if KEY.exists() or PUB.exists():raise RuntimeError('PARTIAL_INIT_STATE')
 fa=pathlib.Path(a.fork_a).resolve();fb=pathlib.Path(a.fork_b).resolve();ps=pathlib.Path(a.probe_script).resolve()
 if not fa.is_dir() or not fb.is_dir() or not ps.is_file():raise RuntimeError('fork roots and probe script required')
 cfg={'fork_a':str(fa),'fork_b':str(fb),'probe_script':str(ps),'probe_script_sha256':H(ps.read_bytes())}
 ts,anchors=anchor_dates();snap=snapshot(cfg);sk=Ed25519PrivateKey.generate();key_bytes=sk.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption());pub_text=base64.b64encode(sk.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode();payload={'schema':'tukuyo.wallclock30.entry.v4','index':0,'anchor_unix':ts,'anchor_sources':anchors,'local_unix':int(time.time()),'prev_entry_sha256':None,'snapshot':snap};d={'schema':'tukuyo.wallclock30.ledger.v4','required_span_seconds':2592000,'min_checkpoints':6,'config':cfg,'entries':[sign_entry(payload,sk)]}
 WD.mkdir(exist_ok=True);tk=WD/'host_private_key.pem.tmp';tp=WD/'host_public_key.b64.tmp';tl=WD/'ledger.json.tmp'
 try:
  tk.write_bytes(key_bytes);tk.chmod(0o600);tp.write_text(pub_text);tl.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');os.replace(tk,KEY);os.replace(tp,PUB);os.replace(tl,LEDGER)
 except Exception:
  for x in (tk,tp,tl):x.unlink(missing_ok=True)
  raise
 print(json.dumps({'ok':True,'started_at_anchor_unix':ts}))
def checkpoint(a):
 d=json.loads(LEDGER.read_text());cfg=d['config'];ps=pathlib.Path(cfg['probe_script']);
 if H(ps.read_bytes())!=cfg['probe_script_sha256']:raise SystemExit('probe script changed')
 sk=load_key();prev=d['entries'][-1];ts,anchors=anchor_dates();payload={'schema':'tukuyo.wallclock30.entry.v4','index':len(d['entries']),'anchor_unix':ts,'anchor_sources':anchors,'local_unix':int(time.time()),'prev_entry_sha256':H(canon(prev)),'snapshot':snapshot(cfg)};d['entries'].append(sign_entry(payload,sk));LEDGER.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps({'ok':True,'index':payload['index']}))
def audit(a):
 if not LEDGER.exists():
  bad=['PARTIAL_INIT_STATE'] if (KEY.exists() or PUB.exists()) else ['NOT_INITIALIZED'];print(json.dumps({'ok':False,'elapsed_complete':False,'experiment_pass':False,'bad':bad}));return 1
 d=json.loads(LEDGER.read_text());pub=Ed25519PublicKey.from_public_bytes(base64.b64decode(PUB.read_text().strip()));bad=[];es=d['entries']
 for i,e in enumerate(es):
  try:pub.verify(base64.b64decode(e['signature_b64']),canon(e['payload']))
  except Exception:bad.append(f'SIGNATURE:{i}')
  p=e['payload']
  if p.get('index')!=i:bad.append(f'INDEX:{i}')
  if i and p.get('prev_entry_sha256')!=H(canon(es[i-1])):bad.append(f'ENTRY_HASH:{i}')
  if i and p.get('anchor_unix',0)<es[i-1]['payload'].get('anchor_unix',0):bad.append(f'ANCHOR_ROLLBACK:{i}')
  if abs(p.get('local_unix',0)-p.get('anchor_unix',0))>300:bad.append(f'LOCAL_CLOCK_DISAGREES_WITH_ANCHOR:{i}')
 span=es[-1]['payload']['anchor_unix']-es[0]['payload']['anchor_unix'] if es else 0;enough=span>=d['required_span_seconds'] and len(es)>=d['min_checkpoints']
 A0=es[0]['payload']['snapshot']['A'];Af=es[-1]['payload']['snapshot']['A'];B0=es[0]['payload']['snapshot']['B'];Bf=es[-1]['payload']['snapshot']['B']
 a_stable=all(e['payload']['snapshot']['A']==A0 for e in es);b_changed=(Bf!=B0);behavior_diverged=(Bf['behavior']!=A0['behavior'])
 elapsed_complete=enough and not bad;experiment_pass=elapsed_complete and a_stable and b_changed and behavior_diverged
 out={'ok':not bad,'elapsed_complete':elapsed_complete,'experiment_pass':experiment_pass,'span_seconds':span,'checkpoints':len(es),'control_A_stable':a_stable,'fork_B_changed':b_changed,'behavior_diverged':behavior_diverged,'bad':bad};print(json.dumps(out,sort_keys=True));return 0 if not bad else 1
def main():
 p=argparse.ArgumentParser();sp=p.add_subparsers(dest='cmd',required=True);i=sp.add_parser('init');i.add_argument('--fork-a',required=True);i.add_argument('--fork-b',required=True);i.add_argument('--probe-script',required=True);sp.add_parser('checkpoint');sp.add_parser('audit');a=p.parse_args()
 try:return {'init':init,'checkpoint':checkpoint,'audit':audit}[a.cmd](a)
 except Exception as e:print(json.dumps({'ok':False,'error':type(e).__name__+':'+str(e)}));return 1
if __name__=='__main__':raise SystemExit(main())
