from __future__ import annotations
import json,os
from pathlib import Path
ZERO='0'*64

def _line(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n'
def migrate_boxed_json(old_path,journal_path,head_path,schema,sha_obj,identity_key=None):
    old_path=Path(old_path);journal_path=Path(journal_path);head_path=Path(head_path)
    if journal_path.exists():return
    journal_path.parent.mkdir(parents=True,exist_ok=True);events=[];individual_id=None
    if old_path.exists():
        try:
            box=json.loads(old_path.read_text(encoding='utf-8'));events=list(box.get('events') or []);individual_id=box.get('individual_id')
        except Exception:events=[]
    tmp=journal_path.with_suffix(journal_path.suffix+'.tmp')
    with tmp.open('w',encoding='utf-8',newline='\n') as f:
        for e in events:f.write(_line(e))
    os.replace(tmp,journal_path)
    head={'schema':schema,'count':len(events),'head_sha256':events[-1].get('event_sha256',ZERO) if events else ZERO,'journal_size':journal_path.stat().st_size}
    if identity_key and individual_id:head[identity_key]=individual_id
    head['head_record_sha256']=sha_obj(head);head_path.write_text(_line(head),encoding='utf-8')
def load_events(path):
    p=Path(path)
    if not p.exists():return []
    with p.open('r',encoding='utf-8') as f:return [json.loads(x) for x in f if x.strip()]
def last_event(path):
    p=Path(path)
    if not p.exists() or p.stat().st_size==0:return None
    with p.open('rb') as f:
        f.seek(0,2);pos=f.tell();buf=b''
        while pos>0:
            step=min(4096,pos);pos-=step;f.seek(pos);buf=f.read(step)+buf
            lines=[x for x in buf.splitlines() if x.strip()]
            if len(lines)>=2 or pos==0:return json.loads(lines[-1].decode('utf-8')) if lines else None
    return None
def append_event(journal_path,head_path,event,head_schema,sha_obj,identity=None):
    jp=Path(journal_path);hp=Path(head_path);jp.parent.mkdir(parents=True,exist_ok=True)
    with jp.open('a',encoding='utf-8',newline='\n') as f:f.write(_line(event));f.flush();os.fsync(f.fileno())
    head={'schema':head_schema,'count':int(event.get('seq',0)),'head_sha256':event.get('event_sha256',ZERO),'journal_size':jp.stat().st_size}
    if identity is not None:head['individual_id']=identity
    head['head_record_sha256']=sha_obj(head);hp.write_text(_line(head),encoding='utf-8');return event
def read_from_offset(path,offset):
    p=Path(path);offset=max(0,int(offset or 0));size=p.stat().st_size if p.exists() else 0
    if offset>size:raise ValueError('JOURNAL_OFFSET_AHEAD')
    if not p.exists() or offset==size:return [],size
    with p.open('rb') as f:f.seek(offset);raw=f.read()
    return [json.loads(x.decode('utf-8')) for x in raw.splitlines() if x.strip()],size


def prefix_last_event(path,offset):
    """Return the last complete event in the journal prefix ending at *offset*.

    Cached derived states record the journal byte length they were built from.
    After checkpoint rollback a future cache may have an offset beyond the live
    journal or may refer to a different prefix.  This helper verifies the prefix
    boundary without loading the entire journal.
    """
    p=Path(path);offset=max(0,int(offset or 0));size=p.stat().st_size if p.exists() else 0
    if offset>size:raise ValueError('JOURNAL_OFFSET_AHEAD')
    if offset==0:return None
    with p.open('rb') as f:
        f.seek(offset-1)
        if f.read(1)!=b'\n':raise ValueError('JOURNAL_OFFSET_NOT_BOUNDARY')
        end=offset-1;pos=end;buf=b''
        while pos>0:
            step=min(4096,pos);pos-=step;f.seek(pos);chunk=f.read(step);buf=chunk+buf
            idx=buf.rfind(b'\n',0,max(0,len(buf)-1))
            if idx>=0:
                line=buf[idx+1:].strip();return json.loads(line.decode('utf-8')) if line else None
        line=buf.strip();return json.loads(line.decode('utf-8')) if line else None
