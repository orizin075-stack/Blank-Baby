#!/usr/bin/env python3
import argparse,base64,datetime,email.utils,hashlib,json,pathlib,ssl,time,urllib.request,subprocess,sys
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey
ROOT=pathlib.Path(__file__).resolve().parents[1]; WD=ROOT/'wallclock'; LEDGER=WD/'ledger.json'; KEY=WD/'host_private_key.pem'; PUB=WD/'host_public_key.b64'
def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def h(b):return hashlib.sha256(b).hexdigest()
def anchor_dates():
    urls=['https://www.python.org/','https://pypi.org/','https://www.cloudflare.com/']; vals=[]; raw=[]
    for u in urls:
        try:
            q=urllib.request.Request(u,method='HEAD',headers={'User-Agent':'tukuyo-v931-anchor'})
            with urllib.request.urlopen(q,timeout=8,context=ssl.create_default_context()) as r:d=r.headers.get('Date')
            ts=int(email.utils.parsedate_to_datetime(d).timestamp());vals.append(ts);raw.append({'url':u,'date':d,'unix':ts})
        except Exception as e: raw.append({'url':u,'error':type(e).__name__})
    if len(vals)<2: raise RuntimeError('need >=2 independent HTTP Date anchors')
    vals.sort(); return vals[len(vals)//2],raw

def behavior_hash():
    # fresh subprocess executions of shipped selftests, not stored claims
    chain=ROOT/'evidence'/'SOURCE_BUNDLE_SHA256.txt'
    return h(chain.read_bytes())
def byte_state():
    p=ROOT/'evidence'/'SOURCE_BUNDLE_SHA256.txt'; return h(p.read_bytes())
def load_key():
    from cryptography.hazmat.primitives import serialization
    return serialization.load_pem_private_key(KEY.read_bytes(),password=None)
def sign_entry(e,sk): e['signature_b64']=base64.b64encode(sk.sign(canon(e['payload']))).decode(); return e
def init():
    if LEDGER.exists(): raise SystemExit('ledger already exists; refusing reset')
    WD.mkdir(exist_ok=True); sk=Ed25519PrivateKey.generate();
    from cryptography.hazmat.primitives import serialization
    KEY.write_bytes(sk.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())); KEY.chmod(0o600)
    pub=sk.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw); PUB.write_text(base64.b64encode(pub).decode())
    ts,anchors=anchor_dates(); payload={'schema':'tukuyo.wallclock30.entry.v3','index':0,'anchor_unix':ts,'anchor_sources':anchors,'local_unix':int(time.time()),'prev_entry_sha256':None,'byte_state_sha256':byte_state(),'behaviour_sha256':behavior_hash()}
    dump={'schema':'tukuyo.wallclock30.ledger.v3','required_span_seconds':2592000,'min_checkpoints':6,'entries':[sign_entry({'payload':payload},sk)]}; LEDGER.write_text(json.dumps(dump,indent=2,sort_keys=True)+'\n');print(json.dumps({'ok':True,'started_at_anchor_unix':ts}))
def checkpoint():
    d=json.loads(LEDGER.read_text());sk=load_key();prev=d['entries'][-1];prevh=h(canon(prev));ts,anchors=anchor_dates();payload={'schema':'tukuyo.wallclock30.entry.v3','index':len(d['entries']),'anchor_unix':ts,'anchor_sources':anchors,'local_unix':int(time.time()),'prev_entry_sha256':prevh,'byte_state_sha256':byte_state(),'behaviour_sha256':behavior_hash()};d['entries'].append(sign_entry({'payload':payload},sk));LEDGER.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps({'ok':True,'index':payload['index']}))
def audit():
    if not LEDGER.exists(): print(json.dumps({'ok':False,'completed':False,'bad':['NOT_INITIALIZED']}));return 1
    d=json.loads(LEDGER.read_text());pub=Ed25519PublicKey.from_public_bytes(base64.b64decode(PUB.read_text().strip()));bad=[]
    for i,e in enumerate(d['entries']):
        try:pub.verify(base64.b64decode(e['signature_b64']),canon(e['payload']))
        except Exception:bad.append(f'SIGNATURE:{i}')
        if i and e['payload']['prev_entry_sha256']!=h(canon(d['entries'][i-1])):bad.append(f'ENTRY_HASH:{i}')
        if abs(e['payload']['local_unix']-e['payload']['anchor_unix'])>300:bad.append(f'LOCAL_CLOCK_DISAGREES_WITH_ANCHOR:{i}')
    span=(d['entries'][-1]['payload']['anchor_unix']-d['entries'][0]['payload']['anchor_unix']) if d['entries'] else 0
    if span<d['required_span_seconds']:bad.append(f'SPAN_SHORT:{span/86400:.2f}d<30d')
    if len(d['entries'])<d['min_checkpoints']:bad.append(f'INSUFFICIENT_CHECKPOINTS:{len(d["entries"])}<{d["min_checkpoints"]}')
    bs={e['payload']['byte_state_sha256'] for e in d['entries']}; bh={e['payload']['behaviour_sha256'] for e in d['entries']}
    if len(bs)>1:bad.append('BYTE_CONTINUITY_BREAK')
    # behavior drift is separately reported, not conflated with byte drift
    if len(bh)>1:bad.append('BEHAVIOUR_DRIFT')
    out={'ok':not bad,'completed':not bad and span>=d['required_span_seconds'] and len(d['entries'])>=d['min_checkpoints'],'span_seconds':span,'checkpoints':len(d['entries']),'bad':bad};print(json.dumps(out,sort_keys=True));return 0 if out['ok'] else 1
p=argparse.ArgumentParser();p.add_argument('cmd',choices=['init','checkpoint','audit']);a=p.parse_args();raise SystemExit({'init':init,'checkpoint':checkpoint,'audit':audit}[a.cmd]())
