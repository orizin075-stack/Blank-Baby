#!/usr/bin/env python3
"""Re-sign a patched TUKUYO tree with a patch key (claude-patch1).

The original v1022 publisher signature cannot cover patched files, so the patched
build is signed by a separate patch key. Run it with that key's public half as
--runtime-trust-file. The original signed seed is kept as
META/TRAINED_SKILLS.v1022_original.json for provenance.

  keygen:  claude_patch_sign.py keygen --out-dir DIR
  sign:    claude_patch_sign.py sign ROOT --private-key DIR/patch_signing.key --revision v1022+claude-patch1
"""
from __future__ import annotations
import argparse,base64,hashlib,json,sys,time
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey

def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def b64(b):return base64.b64encode(b).decode()

def keygen(out):
    out.mkdir(parents=True,exist_ok=True);sk=Ed25519PrivateKey.generate()
    (out/'patch_signing.key').write_text(b64(sk.private_bytes_raw()));(out/'patch_signing.pub').write_text(b64(sk.public_key().public_bytes_raw()))
    print(json.dumps({'ok':True,'public_key':b64(sk.public_key().public_bytes_raw())}))

def sign(root,keyfile,revision):
    sk=Ed25519PrivateKey.from_private_bytes(base64.b64decode(keyfile.read_text().strip(),validate=True));pub=b64(sk.public_key().public_bytes_raw())
    meta=root/'META';seed=meta/'TRAINED_SKILLS.json';orig=meta/'TRAINED_SKILLS.v1022_original.json'
    if seed.is_file():
        env=json.loads(seed.read_text(encoding='utf-8'))
        if not orig.exists():orig.write_bytes(seed.read_bytes())
        new={'payload':env['payload'],'public_key':pub,'signature':b64(sk.sign(canon(env['payload'])))}
        seed.write_bytes(canon(new)+b'\n')
    bad=[p for p in root.rglob('*') if '__pycache__' in p.parts or p.suffix in ('.pyc','.pyo') or p.is_symlink()]
    if bad:raise SystemExit('refusing to sign: caches/symlinks present: '+str(bad[:3]))
    old=json.loads((meta/'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    files={}
    for p in sorted(root.rglob('*')):
        rel=p.relative_to(root).as_posix()
        if p.is_file() and rel not in ('META/RELEASE_MANIFEST.json','META/RELEASE_RECEIPT.json'):files[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    manifest={'schema':old['schema'],'version':old['version'],'file_count':len(files),'files':files}
    mb=json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=1).encode()+b'\n';(meta/'RELEASE_MANIFEST.json').write_bytes(mb)
    oldr=json.loads((meta/'RELEASE_RECEIPT.json').read_text(encoding='utf-8'))
    payload={'schema':oldr['payload']['schema'],'version':old['version'],'release_revision':revision,'created_utc_ns':time.time_ns(),
             'manifest_sha256':hashlib.sha256(mb).hexdigest(),'patched_from_publisher_key':oldr['public_key'] if oldr['public_key']!=pub else oldr['payload'].get('patched_from_publisher_key')}
    receipt={'schema':oldr.get('schema') or 'tukuyo.%s.release.receipt/1'%old['version'].replace('.','_'),'payload':payload,'public_key':pub,'signature':b64(sk.sign(canon(payload)))}
    (meta/'RELEASE_RECEIPT.json').write_bytes(canon(receipt)+b'\n')
    Ed25519PublicKey.from_public_bytes(base64.b64decode(pub)).verify(base64.b64decode(receipt['signature']),canon(payload))
    print(json.dumps({'ok':True,'files':len(files),'public_key':pub,'release_revision':revision}))

def main():
    ap=argparse.ArgumentParser();s=ap.add_subparsers(dest='cmd',required=True)
    k=s.add_parser('keygen');k.add_argument('--out-dir',type=Path,required=True)
    g=s.add_parser('sign');g.add_argument('root',type=Path);g.add_argument('--private-key',type=Path,required=True);g.add_argument('--revision',default='v1022+claude-patch1')
    a=ap.parse_args()
    keygen(a.out_dir) if a.cmd=='keygen' else sign(a.root.resolve(),a.private_key,a.revision)
if __name__=='__main__':main()
