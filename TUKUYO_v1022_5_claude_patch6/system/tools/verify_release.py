#!/usr/bin/env python3
import argparse,base64,hashlib,json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
SC='tukuyo.v1022.release.manifest/1';RS='tukuyo.v1022.release.receipt/1';PS='tukuyo.v1022.release.receipt_payload/1';VER='v1022'
def c(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def h(b):return hashlib.sha256(b).hexdigest()
def verify(root,key):
 root=Path(root);bad=[]
 try:
  kb=base64.b64decode(key.strip(),validate=True)
  if len(kb)!=32:raise ValueError('KEYLEN')
  mb=(root/'META/RELEASE_MANIFEST.json').read_bytes();m=json.loads(mb);r=json.loads((root/'META/RELEASE_RECEIPT.json').read_bytes());p=r['payload'];files=m.get('files',{})
  if m.get('schema')!=SC or m.get('version')!=VER or m.get('file_count')!=len(files):bad.append('MANIFEST_SCHEMA')
  if r.get('schema')!=RS or r.get('public_key')!=key.strip():bad.append('TRUST_ROOT_MISMATCH')
  if p.get('schema')!=PS or p.get('version')!=VER or p.get('manifest_sha256')!=h(mb):bad.append('RECEIPT_BINDING')
  try:Ed25519PublicKey.from_public_bytes(kb).verify(base64.b64decode(r['signature'],validate=True),c(p))
  except (InvalidSignature,ValueError,TypeError):bad.append('RELEASE_SIGNATURE')
  exp=set(files)|{'META/RELEASE_MANIFEST.json','META/RELEASE_RECEIPT.json'};act=set()
  for x in root.rglob('*'):
   rel=x.relative_to(root).as_posix()
   if x.is_symlink():bad.append('SYMLINK:'+rel)
   if '__pycache__' in x.parts or '.pytest_cache' in x.parts or x.suffix in ('.pyc','.pyo'):bad.append('CACHE:'+rel)
   if x.is_file() or x.is_symlink():act.add(rel)
  for f in act-exp:bad.append('UNEXPECTED:'+f)
  for f in exp-act:bad.append('MISSING:'+f)
  for name,d in files.items():
   q=Path(name)
   if q.is_absolute() or '..' in q.parts or q.as_posix()!=name or '\\' in name or ':' in name:bad.append('BADPATH:'+name);continue
   x=root/name
   if x.is_file() and not x.is_symlink() and h(x.read_bytes())!=d:bad.append('HASH:'+name)
 except Exception as e:bad.append('MALFORMED:'+type(e).__name__)
 return {'ok':not bad,'bad':sorted(set(bad)),'verified_files':len(files)}
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('root',nargs='?',default='.');a.add_argument('--trusted-pubkey-file',required=True);x=a.parse_args();k=Path(x.trusted_pubkey_file).read_text().strip();r=verify(x.root,k);print(json.dumps(r,sort_keys=True));raise SystemExit(0 if r['ok'] else 1)
