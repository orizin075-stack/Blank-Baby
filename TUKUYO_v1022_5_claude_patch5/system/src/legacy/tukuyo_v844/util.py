from pathlib import Path
import hashlib,json,os,tempfile
class V844Error(RuntimeError):pass
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def sha256_bytes(b):return hashlib.sha256(b).hexdigest()
def sha256_file(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def load_json(p):return json.loads(Path(p).read_text())
def atomic_json(p,obj):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(dir=p.parent,prefix='.'+p.name+'.',suffix='.tmp')
 try:
  with os.fdopen(fd,'wb') as f:f.write(canonical(obj));f.flush();os.fsync(f.fileno())
  os.replace(tmp,p)
  try:d=os.open(p.parent,os.O_DIRECTORY);os.fsync(d);os.close(d)
  except Exception:pass
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
