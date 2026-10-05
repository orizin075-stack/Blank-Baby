from __future__ import annotations
import json, os, signal, tempfile, uuid
from pathlib import Path

TMP_TAG='.tukuyo-atomic-'

def _fsync_dir(path):
    p=Path(path)
    try:
        fd=os.open(str(p), os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)
    except OSError:
        pass

def maybe_crash(point):
    """Test-only deterministic crash injection. Inert unless exact env point is set."""
    if os.environ.get('TUKUYO_CRASH_POINT','')==str(point):
        os.kill(os.getpid(), signal.SIGKILL)

def atomic_write_bytes(path, data, mode=None, crashpoint=None):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);b=bytes(data)
    tmp=p.parent/(f'.{p.name}{TMP_TAG}{os.getpid()}-{uuid.uuid4().hex}')
    try:
        with tmp.open('wb') as f:
            if crashpoint and os.environ.get('TUKUYO_CRASH_POINT')==f'{crashpoint}:mid_tmp':
                cut=max(1,len(b)//2) if b else 0
                f.write(b[:cut]);f.flush();os.fsync(f.fileno());maybe_crash(f'{crashpoint}:mid_tmp')
            f.write(b);f.flush();os.fsync(f.fileno())
        if mode is not None: os.chmod(tmp,mode)
        if crashpoint: maybe_crash(f'{crashpoint}:after_tmp_fsync')
        os.replace(tmp,p);_fsync_dir(p.parent)
        if mode is not None: os.chmod(p,mode)
        if crashpoint: maybe_crash(f'{crashpoint}:after_replace')
        return p
    finally:
        # Normal exceptions should not strand temp files. SIGKILL intentionally does.
        try:
            if tmp.exists(): tmp.unlink()
        except OSError: pass

def atomic_write_text(path, text, encoding='utf-8', mode=None, crashpoint=None):
    return atomic_write_bytes(path,str(text).encode(encoding),mode=mode,crashpoint=crashpoint)

def atomic_write_json(path,obj,canon=None,crashpoint=None):
    if canon is None:
        raw=json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()+b'\n'
    else:
        raw=canon(obj)+b'\n'
    return atomic_write_bytes(path,raw,crashpoint=crashpoint)

def durable_unlink(path):
    p=Path(path)
    try:p.unlink()
    except FileNotFoundError:return False
    _fsync_dir(p.parent);return True

def cleanup_orphan_temps(root):
    root=Path(root);removed=[]
    if not root.exists():return removed
    for p in root.rglob('*'):
        if p.is_file() and TMP_TAG in p.name:
            try:p.unlink();removed.append(str(p.relative_to(root)))
            except OSError:pass
    return removed
