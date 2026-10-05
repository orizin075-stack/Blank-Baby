from __future__ import annotations
import hashlib,json,time
from pathlib import Path

def _sha(b):return hashlib.sha256(b).hexdigest()
def _j(path):
 p=Path(path)
 if not p.exists():return []
 with p.open('r',encoding='utf-8') as f:return [json.loads(x) for x in f if x.strip()]
def _tail_digest(rows,start=0):
 h=hashlib.sha256()
 for r in rows[start:]:h.update(json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()+b'\n')
 return h.hexdigest()
def _canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def _sources(d):
 d=Path(d)
 return {
  'soul':d/'v977/SOUL_EVENTS.jsonl',
  'heart':d/'v978/HEART_EVENTS.jsonl',
  'conversation':d/'v996/CONVERSATION_GROUNDING_EVENTS.jsonl',
  'semantic':d/'v998/SEMANTIC_INFERENCE_EVENTS.jsonl',
  'knowledge':d/'v1001/knowledge.jsonl',
 }
def _summary(name,p,retain):
 rows=_j(p);cut=max(0,len(rows)-retain);prefix=rows[:cut];raw=p.read_bytes() if p.exists() else b''
 rec={'path':p.as_posix(),'count':len(rows),'compacted_prefix_count':cut,'retained_recent_count':len(rows)-cut,
      'prefix_sha256':_tail_digest(prefix),'source_size':len(raw),'source_prefix_sha256':_sha(raw)}
 if prefix:
  if name=='knowledge':rec['source_counts']={k:sum(1 for r in prefix if r.get('source')==k) for k in sorted({r.get('source','') for r in prefix})}
  elif name in ('soul','heart'):rec['kind_counts']={k:sum(1 for r in prefix if r.get('kind',r.get('type',''))==k) for k in sorted({r.get('kind',r.get('type','')) for r in prefix})}
 return rec,rows[-retain:]
def compact(data,retain=128):
 d=Path(data);out=d/'v1012';out.mkdir(parents=True,exist_ok=True);retain=max(16,int(retain))
 summary={};recent={}
 for name,p in _sources(d).items():
  rec,tail=_summary(name,p,retain);rec['path']=str(Path(rec['path']).relative_to(d));summary[name]=rec;recent[name]=tail
 checkpoint={'schema':'tukuyo.v1012_1.memory_checkpoint/1','created_unix':int(time.time()),'retain':retain,'sources':summary,
   'policy':'NON_DESTRUCTIVE_CHECKPOINT_WITH_BOUNDED_WORKING_VIEW; canonical journals retained for full audit.',
   'claim_boundary':{'canonical_history_deleted':False,'identity_preserving_compaction_checkpoint':True,'lossless_full_replay_retained':True,'working_view_is_bounded':True}}
 checkpoint['checkpoint_sha256']=_sha(_canon(checkpoint))
 cp=out/'MEMORY_COMPACTION_CHECKPOINT.json';cp.write_text(json.dumps(checkpoint,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
 # This is the part normal cognition may consume. It is bounded by retain and is
 # cryptographically tied to the checkpoint; it never replaces canonical journals.
 working={'schema':'tukuyo.v1012_1.working_memory/1','checkpoint_sha256':checkpoint['checkpoint_sha256'],'retain':retain,
          'recent':recent,'summaries':{k:{x:y for x,y in v.items() if x not in ('source_prefix_sha256','prefix_sha256')} for k,v in summary.items()}}
 working['working_memory_sha256']=_sha(_canon(working));wp=out/'WORKING_MEMORY.json';wp.write_text(json.dumps(working,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
 return {'ok':True,'version':'v1012.1','checkpoint':checkpoint,'working_memory':{'path':str(wp),'sha256':working['working_memory_sha256']},'path':str(cp)}
def audit(data):
 d=Path(data);p=d/'v1012/MEMORY_COMPACTION_CHECKPOINT.json';wp=d/'v1012/WORKING_MEMORY.json'
 if not p.exists():return {'ok':False,'version':'v1012.1','errors':['CHECKPOINT_MISSING']}
 q=json.loads(p.read_text(encoding='utf-8'));got=q.pop('checkpoint_sha256',None);errs=[]
 if got!=_sha(_canon(q)):errs.append('CHECKPOINT_HASH')
 current=_sources(d)
 for name,rec in q.get('sources',{}).items():
  pp=current.get(name)
  if pp is None:errs.append('UNKNOWN_SOURCE:'+name);continue
  raw=pp.read_bytes() if pp.exists() else b'';size=int(rec.get('source_size',0))
  # size=0 is a valid empty prefix: first creation after checkpoint is an append.
  if len(raw)<size or _sha(raw[:size])!=rec.get('source_prefix_sha256'):errs.append('SOURCE_PREFIX_DRIFT:'+name)
 if not wp.exists():errs.append('WORKING_MEMORY_MISSING')
 else:
  try:
   w=json.loads(wp.read_text(encoding='utf-8'));wh=w.pop('working_memory_sha256',None)
   if wh!=_sha(_canon(w)):errs.append('WORKING_MEMORY_HASH')
   if w.get('checkpoint_sha256')!=got:errs.append('WORKING_MEMORY_BINDING')
  except Exception as e:errs.append('WORKING_MEMORY_MALFORMED:'+type(e).__name__)
 return {'ok':not errs,'version':'v1012.1','errors':errs,'checkpoint_sha256':got,'source_count':len(q.get('sources',{}))}
