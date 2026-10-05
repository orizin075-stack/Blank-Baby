from __future__ import annotations
import json, hashlib, os, tempfile
from pathlib import Path


def canonical(obj)->bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()

def sha256_bytes(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def sha256_file(p)->str:
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1024*1024), b''): h.update(c)
    return h.hexdigest()

def atomic_write(path:Path, data:bytes):
    path=Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'.', dir=str(path.parent))
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
        dfd=os.open(str(path.parent), os.O_DIRECTORY)
        try: os.fsync(dfd)
        finally: os.close(dfd)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
