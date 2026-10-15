import argparse,base64,hashlib,json,pathlib,sys
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
p=argparse.ArgumentParser();p.add_argument('root',nargs='?',default='.');p.add_argument('--trusted-pubkey-b64',required=True);a=p.parse_args();r=pathlib.Path(a.root);bad=[]
H=lambda b:hashlib.sha256(b).hexdigest(); rec=json.loads((r/'RELEASE_MANIFEST_RECEIPT.json').read_text());pay=rec['payload'];
if H(base64.b64decode(a.trusted_pubkey_b64))!=H(base64.b64decode(pay['release_authority_public_key_b64'])):bad.append('TRUST_ROOT_MISMATCH')
try:Ed25519PublicKey.from_public_bytes(base64.b64decode(a.trusted_pubkey_b64)).verify(base64.b64decode(rec['signature_b64']),json.dumps(pay,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
except Exception:bad.append('RELEASE_SIGNATURE')
man=json.loads((r/'PACKAGE_MANIFEST.json').read_text());
if H((r/'PACKAGE_MANIFEST.json').read_bytes())!=pay['manifest_sha256']:bad.append('MANIFEST_HASH')
actual=set()
for f in r.rglob('*'):
 if f.is_file() and f.name not in {'PACKAGE_MANIFEST.json','PACKAGE_MANIFEST.sha256','RELEASE_MANIFEST_RECEIPT.json'} and '__pycache__' not in f.parts and '.pytest_cache' not in f.parts: actual.add(f.relative_to(r).as_posix())
for x in actual-set(man):bad.append('UNEXPECTED_FILE:'+x)
for x in set(man)-actual:bad.append('MISSING_FILE:'+x)
for x,m in man.items():
 q=r/x
 if q.exists() and H(q.read_bytes())!=m['sha256']:bad.append('HASH:'+x)
for x,h in pay['critical_sha256'].items():
 q=r/x
 if not q.exists() or H(q.read_bytes())!=h:bad.append('CRITICAL_HASH:'+x)
print(json.dumps({'ok':not bad,'bad':bad,'file_count':len(man)},sort_keys=True));raise SystemExit(0 if not bad else 1)
