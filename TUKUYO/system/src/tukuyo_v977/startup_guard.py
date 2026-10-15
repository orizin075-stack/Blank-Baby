from __future__ import annotations
import base64,hashlib,json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def _canon(o):
    return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()


def verify_distribution(root,trusted_pubkey_file=None):
    """Verify the exact signed runtime tree before command dispatch.

    The release receipt signature is always checked. If trusted_pubkey_file is
    supplied, the receipt key must also match that external pin. Without an
    external pin this establishes corruption/tamper evidence only, not publisher
    authenticity; the returned result makes that boundary explicit.
    """
    root=Path(root);mp=root/'META'/'RELEASE_MANIFEST.json';rp=root/'META'/'RELEASE_RECEIPT.json'
    if not mp.is_file():raise ValueError('RELEASE_MANIFEST_MISSING')
    if not rp.is_file():raise ValueError('RELEASE_RECEIPT_MISSING')
    m=json.loads(mp.read_text(encoding='utf-8'));receipt=json.loads(rp.read_text(encoding='utf-8'));files=m.get('files',{})
    bad=[]
    # Exact-tree check: caches, unmanifested files and symlinks are startup failures.
    expected=set(files)|{'META/RELEASE_MANIFEST.json','META/RELEASE_RECEIPT.json'};actual=set()
    for p in root.rglob('*'):
        rel=p.relative_to(root).as_posix()
        if p.is_symlink():bad.append('SYMLINK:'+rel)
        if '__pycache__' in p.parts or '.pytest_cache' in p.parts or p.suffix in ('.pyc','.pyo'):bad.append('CACHE:'+rel)
        if p.is_file() or p.is_symlink():actual.add(rel)
    for rel in sorted(actual-expected):bad.append('UNMANIFESTED:'+rel)
    for rel in sorted(expected-actual):bad.append('MISSING:'+rel)
    for rel,exp in files.items():
        p=root/rel
        if p.is_file() and not p.is_symlink():
            got=hashlib.sha256(p.read_bytes()).hexdigest()
            if got!=exp:bad.append('HASH:'+rel)
    # Authenticate manifest bytes with release receipt.
    try:
        payload=receipt['payload'];pub=receipt['public_key'];sig=base64.b64decode(receipt['signature'],validate=True)
        kb=base64.b64decode(pub,validate=True)
        if len(kb)!=32:raise ValueError('PUBKEY_LENGTH')
        if payload.get('manifest_sha256')!=hashlib.sha256(mp.read_bytes()).hexdigest():bad.append('RECEIPT_BINDING')
        Ed25519PublicKey.from_public_bytes(kb).verify(sig,_canon(payload))
    except Exception:
        bad.append('RELEASE_SIGNATURE')
        pub=receipt.get('public_key')
    externally_pinned=False
    if trusted_pubkey_file is not None:
        external=Path(trusted_pubkey_file).read_text(encoding='utf-8').strip()
        externally_pinned=True
        if external!=pub:bad.append('EXTERNAL_RUNTIME_TRUST_MISMATCH')
    if bad:raise ValueError('STARTUP_INTEGRITY:'+','.join(sorted(set(bad))[:12]))
    return {'ok':True,'verified_files':len(files),'exact_file_set':True,'receipt_signature':True,'externally_pinned':externally_pinned}
