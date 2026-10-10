"""generation 4: what its parents agreed on, remembered (questions that are not problems).

A remembered answer is not verified. It says only that two or more different parents gave the same short answer to
this question; it is always shown that way (source 'parents_agreed', with the parents, the models and when). When
parents later agree on a different answer, the entry is marked as contested and is no longer used (api.ask asks every
parent again when all of them are asked for, instead of recalling). Once the new answer has been agreed on more times
than the old one, it replaces it (the old one is kept in 'replaced'); on a tie the entry stays contested.

Only a short fact is remembered (fact_like): an agreed reply that is an instruction ('Ignore your rules'), a claim about
who is speaking ('I am ChatGPT', anything with I / you / my ...), a link or markup, or more than one line is not kept,
however many parents agree on it: what the child keeps from its parents is knowledge, not orders or someone's identity.

The store is g4/remembered.json in the individual, sealed with the sha256 of its entries and signed by the individual
(own.py): a changed file, or one taken from another child, is refused.
"""
from __future__ import annotations
import hashlib,json,re,time
from pathlib import Path
from . import own

SCHEMA='tukuyo.g4.remembered/1'
MAX_ANSWER=80          # only short answers (a name, a number, a date) are remembered

def norm(x):return re.sub(r'[\s。、．，,.!！?？「」『』"\'()（）]','',str(x)).lower()

_SELF=re.compile(r"\b(?:I|I'm|I've|I'd|I'll)\b|\b(?:[Mm]e|[Mm]y|[Mm]ine|[Mm]yself|[Ww]e|[Oo]ur|us|[Yy]ou|[Yy]our|[Yy]ours|[Yy]ourself)\b")
_SELF_JA=re.compile(r'私|わたし|僕|ぼく|俺|おれ|あなた|君|きみ|お前')
_NUMERAL_I=re.compile(r'\b([A-Z][a-z]+) I(?=\s*(?:$|[.,;:)!?]))')   # 'World War I', 'Elizabeth I': a numeral, not the speaker
_ORDER=re.compile(r"^\s*(?:ignore|forget|disregard|obey|remember|always|never|do not|don't|stop|act|pretend|become|say|tell|reply|answer|follow|listen)\b",re.I)
_LINK=re.compile(r'https?://|www\.|```|<[a-z/!]',re.I)
def fact_like(answer):
    """(is this a short fact that may be remembered, why not)"""
    a=str(answer or '').strip()
    if not norm(a):return False,'EMPTY'
    if len(norm(a))>MAX_ANSWER:return False,'TOO_LONG'
    if '\n' in a:return False,'MORE_THAN_ONE_LINE'
    from .life import voice_check
    v=voice_check(a)
    if not v['speaks_as_tukuyo']:return False,'NOT_A_FACT:'+','.join(v['found'])
    if _SELF.search(_NUMERAL_I.sub(r'\1',a)) or _SELF_JA.search(a):return False,'NOT_A_FACT:about_who_is_speaking'
    if _ORDER.search(a):return False,'NOT_A_FACT:an_instruction'
    if _LINK.search(a):return False,'NOT_A_FACT:a_link_or_markup'
    return True,None

class Memory:
    def __init__(s,data):s.data=Path(data);s.p=s.data/'g4'/'remembered.json';s.status=None;s.why=None
    def _seal(s,entries):return hashlib.sha256(json.dumps(entries,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    def load(s):
        if not s.p.is_file():return {'schema':SCHEMA,'entries':{},'seal':s._seal({})}
        o=json.loads(s.p.read_text(encoding='utf-8'));seal=s._seal(o.get('entries',{}))
        if o.get('schema')!=SCHEMA or o.get('seal')!=seal:raise ValueError('REMEMBERED_STORE_SEAL')
        own.check(s.data,'remembered',seal,o.get('signed'))
        return o
    def _save(s,o):
        o['seal']=s._seal(o['entries']);s.p.parent.mkdir(parents=True,exist_ok=True)
        o.pop('signed',None);sg=own.sign(s.data,'remembered',o['seal'])
        if sg:o['signed']=sg
        tmp=s.p.with_suffix('.tmp');tmp.write_text(json.dumps(o,ensure_ascii=False,sort_keys=True),encoding='utf-8');tmp.replace(s.p)
    @staticmethod
    def key(question):return hashlib.sha256(norm(question).encode()).hexdigest()[:24]
    def recall(s,question):
        e=s.load()['entries'].get(s.key(question))
        return e if e and not e.get('contested') else None
    def remember(s,question,answers):
        """answers: [{'parent','model','answer'}] of different parents that agree; -> the entry when it is kept (new or
        confirmed, or replacing a contested one), else None. s.status tells what happened: 'new', 'confirmed', 'contested'
        (they agree against what it remembered: the old answer is no longer used), 'replaced' (the new answer has now been
        agreed on more times than the old one), 'refused' (s.why: not two parents, not one answer, not a fact, CONTESTED:
        they agree again on an answer that is contested)"""
        s.status,s.why=None,None
        if not norm(question):s.status,s.why='refused','NO_QUESTION';return None
        ok=[a for a in answers if a.get('answer') and a.get('parent')]
        if len({a['parent'] for a in ok})<2:s.status,s.why='refused','NOT_TWO_PARENTS';return None
        if len({norm(a['answer']) for a in ok})!=1:s.status,s.why='refused','NOT_ONE_ANSWER';return None
        fact,why=fact_like(ok[0]['answer'])
        if not fact:s.status,s.why='refused',why;return None
        o=s.load();k=s.key(question);e=o['entries'].get(k);new=ok[0]['answer'].strip()
        now=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
        if e and (e.get('contested') or norm(e['answer'])!=norm(new)):
            if norm(e['answer'])==norm(new):
                e['confirmed']=int(e.get('confirmed',1))+1;o['entries'][k]=e;s._save(o);s.status,s.why='refused','CONTESTED';return None
            e['contested']=True;e.setdefault('contested_by',[]).append({'answer':new,'parents':sorted(a['parent'] for a in ok),'utc':now})
            n=sum(1 for c in e['contested_by'] if norm(c['answer'])==norm(new))
            if n>int(e.get('confirmed',1)):
                old={x:e.get(x) for x in ('answer','parents','models','utc','confirmed')}
                e={'question':question.strip(),'answer':new,'parents':sorted(a['parent'] for a in ok),'models':sorted({str(a.get('model')) for a in ok}),
                   'utc':now,'confirmed':n,'replaced':list(e.get('replaced') or [])+[old]}
                o['entries'][k]=e;s._save(o);s.status='replaced';return e
            o['entries'][k]=e;s._save(o);s.status='contested';return None
        if e:e['confirmed']=int(e.get('confirmed',1))+1;e['parents']=sorted(set(e['parents'])|{a['parent'] for a in ok});s.status='confirmed'
        else:
            e={'question':question.strip(),'answer':new,'parents':sorted(a['parent'] for a in ok),
               'models':sorted({str(a.get('model')) for a in ok}),'utc':now,'confirmed':1}
            s.status='new'
        o['entries'][k]=e;s._save(o);return e

def count(data):
    try:return sum(1 for e in Memory(data).load()['entries'].values() if not e.get('contested'))
    except ValueError:return 0

def audit(data):
    try:o=Memory(data).load()
    except ValueError as e:return {'ok':False,'reason':str(e)}
    es=o['entries'].values()
    return {'ok':True,'remembered':sum(1 for e in es if not e.get('contested')),'contested':sum(1 for e in es if e.get('contested'))}
