"""Deterministic local file audit + separately pinned Ed25519 release key."""
import argparse,base64,hashlib,json,pathlib,stat,sys
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def sha(x):return hashlib.sha256(x).hexdigest()
def verify(root,trust_key):
    root=pathlib.Path(root).resolve();bad=[]
    if len(base64.b64decode(trust_key,validate=True))!=32:return {'ok':False,'bad':['KEY_FORMAT']}
    try:
        manifest=json.loads((root/'META/RELEASE_MANIFEST.json').read_text())
        receipt=json.loads((root/'META/RELEASE_RECEIPT.json').read_text())
        pub=base64.b64decode(trust_key,validate=True)
        Ed25519PublicKey.from_public_bytes(pub).verify(base64.b64decode(receipt['signature_b64'],validate=True),canon(receipt['payload']))
    except Exception as e:return {'ok':False,'bad':['RELEASE_SIGNATURE_OR_FORMAT:'+type(e).__name__]}
    payload=receipt['payload']
    if payload.get('manifest_sha256')!=sha((root/'META/RELEASE_MANIFEST.json').read_bytes()):bad.append('MANIFEST_BINDING')
    if payload.get('release_public_key_sha256')!=sha(pub):bad.append('TRUST_ROOT_MISMATCH')
    expected=set(manifest['files']);actual=set()
    for p in root.rglob('*'):
        name=p.relative_to(root).as_posix()
        if p.is_symlink():bad.append('SYMLINK_ARTIFACT:'+name);continue
        if any(part in ('__pycache__','.pytest_cache','.mypy_cache','.ruff_cache') for part in p.parts):bad.append('CACHE_ARTIFACT:'+name)
        if p.is_file():actual.add(name)
    expected.update(('META/RELEASE_MANIFEST.json','META/RELEASE_RECEIPT.json'))
    for path in sorted(expected-actual):bad.append('MISSING_FILE:'+path)
    for path in sorted(actual-expected):bad.append('UNEXPECTED_FILE:'+path)
    for name,spec in manifest['files'].items():
        p=root/name
        if not p.is_file() or p.is_symlink():continue
        if p.stat().st_size!=spec['bytes'] or sha(p.read_bytes())!=spec['sha256']:bad.append('FILE_HASH:'+name)
    if payload.get('parent_sha256')!=manifest.get('parent_sha256'):bad.append('PARENT_BINDING')
    if payload.get('status_sha256')!=manifest.get('files',{}).get('STATUS.json',{}).get('sha256'):bad.append('STATUS_BINDING')
    if manifest.get('version')!=payload.get('version'):bad.append('VERSION_BINDING')
    return {'ok':not bad,'bad':sorted(set(bad)),'file_count':len(actual),'critical_checked':len(manifest['files'])}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root');ap.add_argument('--trusted-pubkey-file',required=True)
    ns=ap.parse_args();result=verify(ns.root,pathlib.Path(ns.trusted_pubkey_file).read_text().strip());print(json.dumps(result));sys.exit(0 if result['ok'] else 1)
