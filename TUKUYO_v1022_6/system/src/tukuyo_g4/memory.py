"""generation 4: what its parents agreed on, remembered (questions that are not problems).

A remembered answer is not verified. It says only that two or more different parents gave the same short answer to
this question; it is always shown that way (source 'parents_agreed', with the parents, the models and when). When
parents later agree on a different answer, the entry is marked as contested and is no longer used.

The store is g4/remembered.json in the individual, sealed with the sha256 of its entries: a changed file is refused.
"""
from __future__ import annotations
import hashlib,json,re,time
from pathlib import Path

SCHEMA='tukuyo.g4.remembered/1'
MAX_ANSWER=80          # only short answers (a name, a number, a date) are remembered

def norm(x):return re.sub(r'[\s。、．，,.!！?？「」『』"\'()（）]','',str(x)).lower()

class Memory:
    def __init__(s,data):s.p=Path(data)/'g4'/'remembered.json'
    def _seal(s,entries):return hashlib.sha256(json.dumps(entries,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    def load(s):
        if not s.p.is_file():return {'schema':SCHEMA,'entries':{},'seal':s._seal({})}
        o=json.loads(s.p.read_text(encoding='utf-8'))
        if o.get('schema')!=SCHEMA or o.get('seal')!=s._seal(o.get('entries',{})):raise ValueError('REMEMBERED_STORE_SEAL')
        return o
    def _save(s,o):
        o['seal']=s._seal(o['entries']);s.p.parent.mkdir(parents=True,exist_ok=True)
        tmp=s.p.with_suffix('.tmp');tmp.write_text(json.dumps(o,ensure_ascii=False,sort_keys=True),encoding='utf-8');tmp.replace(s.p)
    @staticmethod
    def key(question):return hashlib.sha256(norm(question).encode()).hexdigest()[:24]
    def recall(s,question):
        e=s.load()['entries'].get(s.key(question))
        return e if e and not e.get('contested') else None
    def remember(s,question,answers):
        """answers: [{'parent','model','answer'}] of different parents that agree; -> the entry, or None when not kept"""
        if not norm(question):return None
        ok=[a for a in answers if a.get('answer') and a.get('parent')]
        if len({a['parent'] for a in ok})<2 or len({norm(a['answer']) for a in ok})!=1 or len(norm(ok[0]['answer']))>MAX_ANSWER:return None
        o=s.load();k=s.key(question);e=o['entries'].get(k)
        if e and norm(e['answer'])!=norm(ok[0]['answer']):
            e['contested']=True;e.setdefault('contested_by',[]).append({'answer':ok[0]['answer'],'parents':sorted(a['parent'] for a in ok),
                                                                      'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
        elif e:e['confirmed']=int(e.get('confirmed',1))+1;e['parents']=sorted(set(e['parents'])|{a['parent'] for a in ok})
        else:
            e={'question':question.strip(),'answer':ok[0]['answer'].strip(),'parents':sorted(a['parent'] for a in ok),
               'models':sorted({str(a.get('model')) for a in ok}),'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'confirmed':1}
        o['entries'][k]=e;s._save(o);return e

def count(data):
    try:return sum(1 for e in Memory(data).load()['entries'].values() if not e.get('contested'))
    except ValueError:return 0

def audit(data):
    try:o=Memory(data).load()
    except ValueError as e:return {'ok':False,'reason':str(e)}
    es=o['entries'].values()
    return {'ok':True,'remembered':sum(1 for e in es if not e.get('contested')),'contested':sum(1 for e in es if e.get('contested'))}
