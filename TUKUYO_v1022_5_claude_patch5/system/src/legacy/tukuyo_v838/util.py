from __future__ import annotations
import hashlib,json,os,tempfile,unicodedata
from pathlib import Path

def canonical(obj): return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def sha256_file(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def atomic_write(path,data):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=str(path.parent))
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
        dfd=os.open(str(path.parent),os.O_DIRECTORY)
        try: os.fsync(dfd)
        finally: os.close(dfd)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def norm(s):
    return ' '.join(unicodedata.normalize('NFKC',str(s)).strip().split())
