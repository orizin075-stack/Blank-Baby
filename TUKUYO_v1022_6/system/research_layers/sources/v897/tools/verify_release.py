import argparse,base64,hashlib,json,pathlib,sys,tempfile,zipfile,shutil
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

def canon(o): return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def H(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def safe_extract(zp,dst):
    with zipfile.ZipFile(zp) as z:
        for i in z.infolist():
            p=pathlib.PurePosixPath(i.filename)
            if p.is_absolute() or '..' in p.parts: raise ValueError('unsafe zip path')
        z.extractall(dst)
    roots=[p for p in pathlib.Path(dst).iterdir() if p.is_dir()]
    if len(roots)!=1: raise ValueError('zip must contain one root directory')
    return roots[0]
def verify(root,trusted):
    r=pathlib.Path(root); bad=[]
    try:
        rec=json.loads((r/'RELEASE_MANIFEST_RECEIPT.json').read_text())
        embedded=rec['payload']['release_authority_public_key_b64']
        if embedded!=trusted: bad.append('TRUST_ROOT_MISMATCH')
        Ed25519PublicKey.from_public_bytes(base64.b64decode(trusted)).verify(base64.b64decode(rec['signature_b64']),canon(rec['payload']))
    except Exception as e: return {'ok':False,'bad':bad+['RELEASE_SIGNATURE:'+type(e).__name__]}
    try: man=json.loads((r/'PACKAGE_MANIFEST.json').read_text())
    except Exception as e: return {'ok':False,'bad':bad+['MANIFEST:'+type(e).__name__]}
    actual=set()
    for p in r.rglob('*'):
        rel=p.relative_to(r).as_posix()
        if p.is_symlink(): bad.append('SYMLINK:'+rel); continue
        if p.is_file():
            if '__pycache__/' in rel or rel.startswith('__pycache__/') or '.pytest_cache/' in rel or rel.startswith('.pytest_cache/') or rel.endswith('.pyc'): bad.append('CACHE_ARTIFACT:'+rel)
            actual.add(rel)
    expected=set(man)|{'PACKAGE_MANIFEST.json','PACKAGE_MANIFEST.sha256','RELEASE_MANIFEST_RECEIPT.json'}
    for x in sorted(actual-expected): bad.append('UNEXPECTED_FILE:'+x)
    for x in sorted(expected-actual): bad.append('MISSING_FILE:'+x)
    for rel,h in man.items():
        if (r/rel).is_file() and H(r/rel)!=h: bad.append('HASH:'+rel)
    msha=H(r/'PACKAGE_MANIFEST.json') if (r/'PACKAGE_MANIFEST.json').exists() else ''
    if (r/'PACKAGE_MANIFEST.sha256').read_text().strip()!=msha: bad.append('MANIFEST_SHA')
    if rec['payload'].get('package_manifest_sha256')!=msha: bad.append('RECEIPT_BINDING')
    for rel,h in rec['payload'].get('critical_sha256',{}).items():
        if not (r/rel).is_file() or H(r/rel)!=h: bad.append('CRITICAL_HASH:'+rel)
    return {'ok':not bad,'bad':bad,'version':rec['payload'].get('version'),'trust_epoch':rec['payload'].get('trust_epoch'),'file_count':len(actual),'critical_checked':len(rec['payload'].get('critical_sha256',{}))}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('package'); ap.add_argument('--trusted-pubkey-b64',required=True); a=ap.parse_args()
    p=pathlib.Path(a.package); td=None
    try:
        if p.is_file() and p.suffix.lower()=='.zip':
            td=tempfile.mkdtemp(prefix='tukuyo_verify_'); root=safe_extract(p,td)
        else: root=p
        out=verify(root,a.trusted_pubkey_b64); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out['ok'] else 1)
    finally:
        if td: shutil.rmtree(td,ignore_errors=True)
if __name__=='__main__': main()
