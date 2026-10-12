"""generation 4: noticing its own growth.

When it cannot read a problem alone - no reading of its own (a wording it learned, its reader, the v1022 core) passes
the solver and the checker - it keeps the problem (g4/unread.json, signed and bound to the individual like its other
stores, own.py): the text, its wording (the learned-template key), why it could not read it (the reason its reader gave,
and the kind of weak spot it is, in its own words) and what its parents did with it then. A problem it learned to read
in the same thought (its parents agreed and it learned the wording) is not kept: the learning is the experience. Only
what was taken as a problem is kept: what g4-solve was given, what g4-ask took as a problem, and what think took as one
(api._a_problem: a reading was written, or its parents did not say it is not a problem).

It notices that it has grown when it can read alone what it could not:
  learned   it learns a wording from parents who agree: the problems of that wording it could not read are read again
            alone, with what it learned (as hindsight.py looks back), and those that now pass the checker are grown
  alone     it answers alone a problem it could not read before, or reads again alone the others of its wording (a
            wording it learned, or its own reader reads it now: a later version of the child)
A thought in which it notices is one experience (discovery, theme g4:grew) in the same episode; the problems are marked
grown when the episode is finished (life._finish, and life.recover after a crash), so each is noticed once.

A growth can be given up. When two of its parents later read a wording it learned otherwise (the learned reading is
contested, learn.py), the problems it had come to read with that wording are open again ('contested': it does not read
them alone now). When its parents teach the wording again and it can read them again, it notices that too; when the
answer is not the one it had, it keeps what it had read before ('corrected_from') and says so.

A problem only its older core read (Japanese) is kept only when it was given as a problem (g4-solve) or a parent read
it as one: the older core cannot tell a problem from a question with a number in it.

What is left is what it knows it cannot read yet: its weak spots, in its own words and with counts, and what it wants
to learn: first what its parents could read and it could not, and never a story in which an amount seemed not to be
given unless its parents read one (that may be the problem's fault, not its own). Looking (g4-self, g4-reflect) changes
nothing; g4-reflect --act first tries again, alone, what it can now read (life.reflect). Nothing here is written by a
parent, and nothing is sent anywhere.
"""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
from . import own

SCHEMA='tukuyo.g4.unread/1'
MAX=1000                # problems kept: the oldest it has since learned to read go first, then the oldest
REREAD=50               # problems of one wording read again in one thought (the rest wait for the next one)
GREW='g4:grew'
JA=re.compile(r'[぀-ヿ㐀-鿿]')

# the kinds of weak spot, from the reason its reader gave (the first that matches), in its own words (English, Japanese)
KINDS=[
 ('missing',r'VAGUE|UNDERDETERMINED',('stories in which an amount seemed not to be given','量が書かれていないように見えた話')),
 ('compare',r'COMPARE_PARTIES|DIFFERENCE_SIDE|QUESTION_DIFFERENCE',('comparisons and differences whose two sides I could not tell','比べる二つが何なのか決められなかった比べや差')),
 ('question',r'QUESTION|NO_SENTENCES',('questions asked in a way I do not know yet','まだ知らない聞き方の問い')),
 ('who',r'PRONOUN',('telling who a "he", "she" or "they" is','「彼」「彼女」「彼ら」が誰なのかを決めること')),
 ('number',r'UNUSED|UNREAD_NUMBER',('numbers in a story that I do not know how to use','話の中の、使い方のわからない数')),
 ('two_ways',r'SCHEMAS_DISAGREE',('stories I can read in two ways','二通りに読める話')),
 ('pattern',r'PATTERN',('patterns','並び方（パターン）')),
 ('wrong',r'NOT_WHOLE|NEGATIVE|INCONSISTENT|^CHECK:|^SOLVE:',('stories my reading got wrong (solving or checking it showed that)','読み違えた話（解くか確かめるかでわかったもの）')),
 ('older',r'^V1022:',('problems my older core could not solve','前の世代の考え方でも解けなかった問題')),
 ('story',r'^EN:',('stories I do not know how to put together yet','まだ組み立て方を知らない話')),
]
WORDS={k:w for k,_,w in KINDS}
WORDS['contested']=('wordings my parents taught me that two of them later read otherwise','教わったのに、あとで二人の親に別に読まれた言い回し')
WORDS['other']=('problems I could not read in a way I can check','確かめられる読み方が見つからなかった問題')

def kind_of(reason):
    r=str(reason or '')
    for k,rx,_ in KINDS:
        if re.search(rx,r):return k
    return 'other'

def _key(text):
    from .learn import Store
    return Store.key_of(text)

class Unread:
    """the problems it could not read alone: {entry id: {'text', 'key', 'lang', 'why', 'reason', 'parents', 'first', 'last',
    'met', 'grown': {'seq', 'how', 'value', 'teachers'} once it can read it alone}}"""
    def __init__(s,data):s.data=Path(data);s.p=s.data/'g4'/'unread.json'
    def load(s):
        if not s.p.is_file():return {'schema':SCHEMA,'entries':{},'next':1}
        o=json.loads(s.p.read_text(encoding='utf-8'));sha=own.body_sha(o.get('entries',{}))
        if o.get('schema')!=SCHEMA or o.get('sha256')!=sha:raise ValueError('UNREAD_STORE_SEAL')
        own.check(s.data,'unread',sha,o.get('signed'))
        return o
    def _save(s,o):
        es=o['entries']
        if len(es)>MAX:
            for k,_ in sorted(es.items(),key=lambda kv:(not kv[1].get('grown'),kv[1].get('last',0)))[:len(es)-MAX]:del es[k]
        o={'schema':SCHEMA,'entries':es,'next':int(o.get('next',1)),'sha256':own.body_sha(es)}
        sg=own.sign(s.data,'unread',o['sha256'])
        if sg:o['signed']=sg
        s.p.parent.mkdir(parents=True,exist_ok=True)
        from tukuyo_common.atomic_fs import atomic_write_text
        atomic_write_text(s.p,json.dumps(o,ensure_ascii=False,sort_keys=True))
    @staticmethod
    def entry_id(text):return hashlib.sha256(' '.join(str(text).split()).encode()).hexdigest()[:24]
    def keep(s,text,key,why,reason,parents):
        """it could not read this problem alone (again); a problem it could read before and cannot now is open again"""
        o=s.load();eid=s.entry_id(text);n=int(o.get('next',1));o['next']=n+1
        e=o['entries'].get(eid) or {'text':' '.join(str(text).split()),'key':key,'lang':'ja' if JA.search(str(text)) else 'en','first':n,'met':0}
        if e.get('grown'):g=e.pop('grown');e['lost']={'seq':n,'why':'cannot_read_again','was':g.get('value')}
        e.update({'why':why,'reason':str(reason or '')[:160],'last':n,'met':int(e.get('met',0))+1})
        if parents is not None or 'parents' not in e:e['parents']=parents       # met alone: what its parents did before stays
        o['entries'][eid]=e;s._save(o);return eid
    def grow(s,marks):
        """marks: [[entry id, how ('learned' | 'own' | 'v1022'), the answer it reads now, the parents who taught it]]"""
        if not marks:return
        o=s.load();n=int(o.get('next',1));changed=False
        for eid,how,value,teachers in marks:
            e=o['entries'].get(eid)
            if e is None or e.get('grown'):continue
            e['grown']={'seq':n,'how':how,'value':str(value),**({'teachers':sorted(teachers)} if teachers else {})};changed=True
            lo=e.get('lost') or {}
            if lo.get('why')=='contested' and lo.get('was') is not None and str(lo['was'])!=str(value):
                e['grown']['corrected_from']=str(lo['was'])                    # what it had read with the contested reading
        if changed:o['next']=n+1;s._save(o)
    def lose(s,ids):
        """two parents read the wording these were read with otherwise: they are open again"""
        if not ids:return
        o=s.load();n=int(o.get('next',1));changed=False
        for eid in ids:
            e=o['entries'].get(eid)
            if e is None or not e.get('grown'):continue
            g=e.pop('grown');e['lost']={'seq':n,'why':'contested','was':g.get('value'),**({'teachers':g['teachers']} if g.get('teachers') else {})}
            e['why']='contested';e['reason']='TEMPLATE_CONTESTED';changed=True
        if changed:o['next']=n+1;s._save(o)

# ----------------------------------------------------------------------------- what a thought shows
def _g(result):return result.get('gen4') if isinstance(result.get('gen4'),dict) else result
def _mine(g):
    """its own readings (a learned wording, its reader, the v1022 core): not its parents', and not a reading reported
    only as set aside (think's v1022 story reading)"""
    return [x for x in g.get('readings') or [] if isinstance(x,dict) and x.get('route') and not str(x['route']).startswith('llm') and 'ok' in x]
def _parents(g):
    """what its parents did with the problem: 'agreed', 'disagreed', 'one' (one valid reading), 'could_not', or None"""
    ps=[x for x in g.get('readings') or [] if isinstance(x,dict) and str(x.get('route','')).startswith('llm') and str(x.get('reason') or '')!='LLM:LLM_NOT_CONFIGURED']
    if not ps:return None
    ok=[x for x in ps if x.get('ok')]
    if not ok:return 'could_not'
    vals={str(x.get('value')) for x in ok}
    if len(vals)>1:return 'disagreed'
    return 'agreed' if len({x.get('parent') for x in ok})>=2 or len(ok)>=2 else 'one'

def cannot_read(result):
    """what this result shows it could not read alone: {'why', 'reason', 'parents'}, or None: it read the problem itself
    (even when it then held back), it learned to read it in this thought, a wording it had learned was contested (kept
    as contested, learn.py), one of its stores is not its own (the audits say so), or the text was not taken as a
    problem"""
    if not isinstance(result,dict) or result.get('kind') in ('question','reflection'):return None
    g=_g(result)
    if not isinstance(g,dict):return None
    mine=_mine(g)
    if not mine or any(x.get('ok') for x in mine) or g.get('learned'):return None
    rs=[str(x.get('reason') or '') for x in mine]
    if any(r=='TEMPLATE_CONTESTED' or r.endswith(('_STORE_SEAL','_NOT_ITS_OWN','_NOT_SIGNED')) for r in rs):return None
    if 'gen4' in result:
        from .api import _a_problem
        if not _a_problem(g):return None
    # only the older core read it (Japanese): it cannot tell a problem from a question with a number in it ('2018年の
    # ワールドカップで…'), so it keeps it only when it was given as a problem (g4-solve) or a parent read it as one
    given='kind' not in result and 'gen4' not in result
    if all(x.get('route')=='v1022' for x in mine) and not given and not any(isinstance(x,dict) and (x.get('ok') or x.get('spec')) for x in g.get('readings') or []):
        return None
    reason=next((str(x.get('reason') or '') for x in mine if x.get('route') in ('own','v1022')),rs[0])
    return {'why':kind_of(reason),'reason':reason,'parents':_parents(g)}

def _answered_alone(result):
    """(the answer, its own reading that gave it) when it answered with a reading of its own, else None"""
    g=_g(result)
    if not isinstance(g,dict) or result.get('answer') is None:return None
    a=str(g.get('value') if g.get('value') is not None else result.get('answer'))
    x=next((x for x in _mine(g) if x.get('ok') and str(x.get('value'))==a),None)
    return (a,x) if x else None

def _how(x):
    r=str(x.get('route'))
    return 'learned' if r=='learned' else ('v1022' if r=='v1022' else 'own')

def _teachers(data,x):
    """the parents who taught the wording a learned reading came from"""
    if x.get('route')!='learned' or not x.get('template') or data is None:return []
    from .learn import Store
    try:t=Store(Path(data)/'g4').load()['templates'].get(x['template']) or {}
    except ValueError:return []
    return sorted((t.get('provenance') or {}).get('parents') or [])

def alone(data,text):
    """can it read this problem alone now? (the answer, how, the parents who taught it) or None. It changes nothing: no
    parent is asked, nothing is learned, and nothing is recorded"""
    from .api import solve
    try:r=solve(text,llm='off',data=data,learn=False)
    except Exception:  # noqa: BLE001 - a problem it cannot read again is simply still unread
        return None
    a=_answered_alone(r)
    return (a[0],_how(a[1]),_teachers(data,a[1])) if a else None

def may_notice(data,result,text=None):
    """cheap: could this result show growth? (it learned a wording, or answered alone, and it keeps unread problems)"""
    if data is None or not isinstance(result,dict) or result.get('kind') in ('question','reflection'):return False
    g=_g(result)
    if not isinstance(g,dict) or not (g.get('learned') or (text and _answered_alone(result))):return False
    return (Path(data)/'g4'/'unread.json').is_file()

def keep(data,text,miss):
    """life.record: a problem it could not read alone, kept (a store that is not its own is not written to; the audits
    report it)"""
    if data is None or not text or not miss:return None
    try:return Unread(data).keep(text,_key(text),miss['why'],miss['reason'],miss['parents'])
    except ValueError:return None

def noticed(data,result,text=None):
    """(experiences, marks): the problems it could not read alone that this thought shows it can now read alone; one
    experience for the thought, however many it notices. The marks are applied when the episode is finished"""
    if not may_notice(data,result,text):return [],[]
    g=_g(result)
    try:es=Unread(data).load()['entries']
    except ValueError:return [],[]
    keys=set();answered=_answered_alone(result) if text else None
    if g.get('learned'):keys.add(g['learned'])
    if answered:keys.add(_key(text))
    this=Unread.entry_id(text) if text else None
    marks=[];n=0
    for eid,e in sorted(es.items(),key=lambda kv:kv[1].get('first',0)):
        if e.get('grown') or e.get('key') not in keys:continue
        if eid==this and answered:
            marks.append([eid,_how(answered[1]),answered[0],_teachers(data,answered[1])]);continue
        if n>=REREAD:continue
        n+=1;a=alone(data,e['text'])
        if a:marks.append([eid,a[1],a[0],a[2]])
    if not marks:return [],[]
    return [('discovery',0.4,0.25,GREW,'')],marks

def lost(data,result):
    """the problems it had come to read with a wording its parents now read otherwise (the reading was contested in this
    thought): given up when the episode is finished"""
    if data is None or not isinstance(result,dict):return []
    g=_g(result);key=(g.get('template_contested') if isinstance(g,dict) else None) or result.get('template_contested')
    if not key or not (Path(data)/'g4'/'unread.json').is_file():return []
    try:es=Unread(data).load()['entries']
    except ValueError:return []
    return sorted(k for k,e in es.items() if e.get('key')==key and (e.get('grown') or {}).get('how')=='learned')

def lose(data,ids):
    """life._finish: give up the growth of these problems (a store that is not its own is left alone)"""
    if not ids:return
    try:Unread(data).lose(ids)
    except ValueError:pass

def grow(data,marks):
    """life._finish: mark the problems it now reads alone (a store that is not its own is left alone; the audits report it)"""
    if not marks:return
    try:Unread(data).grow(marks)
    except ValueError:pass

# ----------------------------------------------------------------------------- what it knows of its growth
PARENT_NAMES={'claude':'Claude','chatgpt':'ChatGPT','gemini':'Gemini'}
def _who(ps,ja):
    ns=[PARENT_NAMES.get(p,str(p)) for p in ps]
    return '、'.join(ns) if ja else (' and '.join(ns) if len(ns)<3 else ', '.join(ns[:-1])+' and '+ns[-1])

def _how_words(how,teachers,ja,again=False):
    if how=='learned':
        who=_who(teachers,ja) if teachers else ('親' if ja else 'my parents')
        if again:return f'この言い回しを {who} から教わり直しました' if ja else f'I learned this wording again from {who}'
        return f'この言い回しを {who} から教わりました' if ja else f'I learned this wording from {who}'
    if how=='v1022':return 'いまは前の世代の考え方で解けます' if ja else 'my older core solves it now'
    return 'いまは自分の読み方で読めます' if ja else 'my own reader reads it now'

def before(data,text,result,ja=False):
    """what it says of having met this problem (or its wording) before without reading it alone, or None (voice.py)"""
    if data is None or not text:return None
    try:es=Unread(data).load()['entries']
    except (ValueError,OSError):return None
    if not es:return None
    e=es.get(Unread.entry_id(text));key=_key(text)
    same=e is None and any(x.get('key')==key for x in es.values())
    if result.get('answer') is not None:
        a=_answered_alone(result)
        if not a or not (e or same):return None
        was=((e or {}).get('grown') or {}).get('corrected_from')
        lo=(e or {}).get('lost') or {}
        if was is None and e is not None and not e.get('grown') and lo.get('why')=='contested' and lo.get('was') not in (None,a[0]):was=lo['was']
        if was is not None:
            how=_how_words(_how(a[1]),_teachers(data,a[1]),ja,again=True)
            return (f'前は、教わった読み方でこの問題を {was} と読んでいましたが、あとで二人の親がこの言い回しを別に読みました。いまは {a[0]} と読みます：{how}。' if ja else
                    f'Before, what I had learned for this wording read this problem as {was}, and two of my parents later read the wording otherwise; now I read it as {a[0]}: {how}.')
        how=_how_words(_how(a[1]),_teachers(data,a[1]),ja)
        if e:return (f'前にこの問題に会ったときは、ひとりでは読めませんでした。いまは読めます：{how}。' if ja else
                     f'I could not read this problem alone when I met it before; now I can: {how}.')
        return (f'前に同じ言い回しの問題を、ひとりでは読めませんでした。いまは読めます：{how}。' if ja else
                f'I could not read a problem worded like this alone before; now I can: {how}.')
    if e and not e.get('grown') and e.get('why')!='contested' and not any(x.get('ok') for x in _mine(_g(result))):
        return '前に会ったときも、ひとりでは読めませんでした。' if ja else 'I could not read it alone when I met it before, either.'
    return None

def report(data):
    """g4-self: what it could not read alone, what it can read now and how, its weak spots and what it wants to learn
    (from its own record; it reads, it changes nothing). ValueError when the record is not its own"""
    es=sorted(Unread(data).load()['entries'].values(),key=lambda e:e.get('first',0))
    opened=[e for e in es if not e.get('grown')];grown=[e for e in es if e.get('grown')]
    names={'learned':'learned_from_parents','own':'own_reader','v1022':'older_core'}
    grew={}
    for e in grown:
        k=names.get(e['grown'].get('how'),'own_reader');grew[k]=grew.get(k,0)+1
    spots={}
    for e in opened:
        k=e.get('why') or 'other'
        q=spots.setdefault(k,{'kind':k,'what':WORDS.get(k,WORDS['other'])[0],'what_ja':WORDS.get(k,WORDS['other'])[1],'problems':0,'met':0,
                              'parents_read':0,'example':e['text'],'first':e.get('first',0)})
        q['problems']+=1;q['met']+=int(e.get('met',1));q['parents_read']+=e.get('parents')=='agreed' or k=='contested'
    weak=sorted(spots.values(),key=lambda q:(-q['problems'],-q['met'],q['first']))
    # what it wants to learn: what its parents could read and it could not first; a story whose amount seemed not to be
    # given only when its parents read one
    wants=sorted([q for q in weak if q['kind']!='missing' or q['parents_read']],key=lambda q:(-q['parents_read'],-q['problems'],-q['met'],q['first']))[:3]
    for q in weak:q.pop('first',None)
    # said in its own words, as the voice says things (the life story is told about it)
    told=[];corrected=sum(1 for e in grown if e['grown'].get('corrected_from') is not None)
    def n_(k,w):return f"{k} {w}{'s' if k!=1 else ''}"
    if es:
        how=[f"{grew[k]} with {w}" for k,w in (('learned_from_parents','what my parents taught me'),('own_reader','my own reader'),('older_core','my older core')) if grew.get(k)]
        told.append(f"I could not read {n_(len(es),'problem')} alone when I met {'them' if len(es)!=1 else 'it'}; "
                    +((f"now I can read {len(grown)} of them alone" if len(es)!=1 else 'now I can read it alone')+f" ({', '.join(how)})." if grown else
                      ('I cannot read any of them alone yet.' if len(es)!=1 else 'I cannot read it alone yet.')))
    if corrected:told.append(f"{n_(corrected,'problem')} I had first read with what I was taught, and two of my parents later read the wording otherwise; "
                             f"they taught me again, and I read {'them' if corrected!=1 else 'it'} otherwise now.")
    if weak:told.append('Where I am weak: '+', '.join(f"{q['what']} ({n_(q['problems'],'problem')})" for q in weak)+'.')
    if wants:told.append('What I want to learn: '+'; '.join(f"{q['what']} (for example: \"{q['example']}\")" for q in wants)+'.')
    return {'could_not_read':len(es),'cannot_read_yet':len(opened),'can_read_now':len(grown),'grew':grew,'corrected':corrected,'weak_spots':weak,
            'wants_to_learn':[{k:q[k] for k in ('kind','what','what_ja','problems','parents_read','example')} for q in wants],'told':told}

def look(data,limit=None):
    """g4-reflect: the problems it could not read, read again alone (nothing is written): (open entries it can read now,
    open entries it still cannot read and wants to learn), oldest first; all of them (at most MAX), or the `limit` oldest.
    ValueError when the record is not its own"""
    es=sorted(((k,e) for k,e in Unread(data).load()['entries'].items() if not e.get('grown')),key=lambda kv:kv[1].get('first',0))
    now,still=[],[]
    for eid,e in (es if limit is None else es[:max(0,int(limit))]):
        a=alone(data,e['text'])
        if a:now.append({'id':eid,'text':e['text'],'answer':a[0],'how':a[1]})
        elif e.get('why')!='missing' or e.get('parents')=='agreed':still.append({'id':eid,'text':e['text'],'why':e.get('why') or 'other'})
    return now,still,len(es)
