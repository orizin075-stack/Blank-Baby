#!/usr/bin/env python3
import argparse,base64,hashlib,json,pathlib,sys
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
p=argparse.ArgumentParser();p.add_argument('root',nargs='?',default='.');p.add_argument('--trusted-pubkey-b64',required=True);a=p.parse_args();r=pathlib.Path(a.root);bad=[]
H=lambda b:hashlib.sha256(b).hexdigest()
try: rec=json.loads((r/'RELEASE_MANIFEST_RECEIPT.json').read_text());pay=rec['payload']
except Exception as e: print(json.dumps({'ok':False,'bad':['RECEIPT_PARSE']}));raise SystemExit(1)
try:
 if H(base64.b64decode(a.trusted_pubkey_b64))!=H(base64.b64decode(pay['release_authority_public_key_b64'])):bad.append('TRUST_ROOT_MISMATCH')
 Ed25519PublicKey.from_public_bytes(base64.b64decode(a.trusted_pubkey_b64)).verify(base64.b64decode(rec['signature_b64']),json.dumps(pay,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
except Exception:bad.append('RELEASE_SIGNATURE')
try: man_bytes=(r/'PACKAGE_MANIFEST.json').read_bytes();man=json.loads(man_bytes)
except Exception: man={};man_bytes=b'';bad.append('MANIFEST_PARSE')
mh=H(man_bytes)
if mh!=pay.get('manifest_sha256'):bad.append('MANIFEST_HASH')
try:
 if (r/'PACKAGE_MANIFEST.sha256').read_text().strip()!=mh:bad.append('MANIFEST_SHA_FILE')
except Exception:bad.append('MANIFEST_SHA_FILE')
actual=set();special={'PACKAGE_MANIFEST.json','PACKAGE_MANIFEST.sha256','RELEASE_MANIFEST_RECEIPT.json'}
for f in r.rglob('*'):
 rel=f.relative_to(r).as_posix()
 if f.is_symlink():bad.append('SYMLINK_ARTIFACT:'+rel);continue
 if not f.is_file():continue
 if '__pycache__' in f.parts or '.pytest_cache' in f.parts or f.suffix=='.pyc':bad.append('CACHE_ARTIFACT:'+rel)
 if rel not in special:actual.add(rel)
for x in sorted(actual-set(man)):bad.append('UNEXPECTED_FILE:'+x)
for x in sorted(set(man)-actual):bad.append('MISSING_FILE:'+x)
for x,m in man.items():
 q=r/x
 if not q.exists():continue
 b=q.read_bytes()
 if H(b)!=m.get('sha256'):bad.append('HASH:'+x)
 if len(b)!=m.get('bytes'):bad.append('SIZE:'+x)
crit=pay.get('critical_sha256',{})
if set(crit)!=set(man):bad.append('CRITICAL_COVERAGE')
for x,h in crit.items():
 q=r/x
 if not q.exists() or H(q.read_bytes())!=h:bad.append('CRITICAL_HASH:'+x)
print(json.dumps({'ok':not bad,'bad':bad,'file_count':len(man)},sort_keys=True));raise SystemExit(0 if not bad else 1)
