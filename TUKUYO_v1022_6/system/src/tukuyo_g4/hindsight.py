"""generation 4: looking back.

When its parents' readings disagree, or only one of them reads a problem, the child withholds the answer, and it cannot
tell who was wrong. It keeps the disagreement: the text, its wording (the learned-template key) and what each parent's
reading answered (g4/unresolved.json, signed and bound to the individual like its other stores, own.py).

When the child later learns that wording from parents who agree (api.solve learns it, or confirms it), it looks back:
the learned reading answers the old text too, and each parent whose old reading gave that answer was right, each other
one was wrong. These become experiences of the same kinds as the ones it has at once (parent_help, parent_error, theme
g4:hindsight), so its record of each parent also hears about the readings it could not judge at the time. The answer
it looks back with is only as sure as the learned reading itself: parents who agreed, and the checker.
"""
from __future__ import annotations
import hashlib,json,os
from pathlib import Path
from . import own

SCHEMA='tukuyo.g4.unresolved/1'
MAX=1000        # disagreements kept, oldest dropped first

def _sha(o):return own.body_sha(o)

class Unresolved:
    def __init__(s,data):s.data=Path(data);s.p=s.data/'g4'/'unresolved.json'
    def load(s):
        if not s.p.is_file():return {'schema':SCHEMA,'entries':{},'next':1}
        o=json.loads(s.p.read_text(encoding='utf-8'));sha=_sha(o.get('entries',{}))
        if o.get('schema')!=SCHEMA or o.get('sha256')!=sha:raise ValueError('UNRESOLVED_STORE_SEAL')
        own.check(s.data,'unresolved',sha,o.get('signed'))
        return o
    def _save(s,o):
        o={'schema':SCHEMA,'entries':o['entries'],'next':int(o.get('next',1)),'sha256':_sha(o['entries'])}
        sg=own.sign(s.data,'unresolved',o['sha256'])
        if sg:o['signed']=sg
        s.p.parent.mkdir(parents=True,exist_ok=True);tmp=s.p.with_suffix('.tmp')
        tmp.write_text(json.dumps(o,ensure_ascii=False,sort_keys=True),encoding='utf-8');os.replace(tmp,s.p)
    @staticmethod
    def entry_id(text):return hashlib.sha256(' '.join(str(text).split()).encode()).hexdigest()[:24]
    def keep(s,text,key,values,reason):
        """values: {parent: the answer its reading gave}; the latest reading of a parent replaces its earlier one"""
        if not values or not key:return None
        o=s.load();eid=s.entry_id(text);e=o['entries'].get(eid) or {'text':text,'key':key,'values':{}}
        e['values'].update({p:str(v) for p,v in values.items()});e['reason']=reason;e['seq']=int(o.get('next',1));o['next']=e['seq']+1
        o['entries'][eid]=e
        if len(o['entries'])>MAX:
            for k,_ in sorted(o['entries'].items(),key=lambda kv:kv[1].get('seq',0))[:len(o['entries'])-MAX]:del o['entries'][k]
        s._save(o);return eid
    def of(s,key):return sorted(((k,e) for k,e in s.load()['entries'].items() if e.get('key')==key),key=lambda kv:kv[1].get('seq',0))
    def drop(s,ids):
        if not ids:return
        o=s.load()
        for k in ids:o['entries'].pop(k,None)
        s._save(o)

def keep(data,text,key,readings,reason):
    """api.solve: a disagreement (or a single voice) among its parents' valid readings, kept to look back on later"""
    values={r['parent']:r['value'] for r in readings if r.get('ok') and r.get('parent') and str(r.get('route','')).startswith('llm')}
    if data is None or not values:return None
    try:return Unresolved(data).keep(text,key,values,reason)
    except ValueError:return None          # a store that is not its own is not written to; the audits report it

def look_back(data,key):
    """the kept disagreements of this wording, answered with its learned reading:
    [{'id','text','answer','parents':{parent:{'value','right'}}}]; a text the reading cannot answer is left for later"""
    from .learn import Store,instantiate
    from .api import evaluate
    try:t=Store(Path(data)/'g4').load()['templates'].get(key);kept=Unresolved(data).of(key)
    except ValueError:return []
    if not t:return []
    out=[]
    for eid,e in kept:
        spec=instantiate(t,e['text']);r=evaluate(spec,'learned') if spec else {'ok':False}
        if not r.get('ok'):continue
        out.append({'id':eid,'text':e['text'],'answer':r['value'],
                    'parents':{p:{'value':v,'right':str(v)==str(r['value'])} for p,v in sorted(e['values'].items())}})
    return out
