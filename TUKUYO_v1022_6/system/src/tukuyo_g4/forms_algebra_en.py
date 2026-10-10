"""generation 4: a number or an age told by what is done to it, read by a small grammar (no LLM), after forms_en:

  'Seven less than four times a number is 29.'   'If 6 is subtracted from five times a number, the result is 34.'
  'Lily is 31 years old. She is 7 years older than three times her son's age. How old is her son?'
  '9 years ago, Paul was 25 years old. How old is Paul now?'

The words are read the way algebra books read them: 'twice', 'k times' and 'half of' take the nearest term ('half of a
number plus 9' is x/2 + 9; 'half of the sum of a number and 9' is (x + 9)/2), 'plus' and 'minus' go left to right,
'k more than E' and 'k less than E' take everything after them. Every reading of the words that the grammar allows is
tried: if two readings give two answers the text is left unread, and so is the text if any reading is not linear or
gives no single answer. The reading written is an FPL reading like any other, solved exactly and checked by check.py.
"""
from __future__ import annotations
import re
from .forms_en import _Spec,INTRO,Q_NUM

MULT={'twice':2,'double':2,'thrice':3,'triple':3}
X_WORDS={('a','number'),('the','number'),('a','certain','number'),('the','same','number'),('that','number'),('this','number'),
         ('the','number','itself'),('itself',),('it',),('the','unknown','number'),('an','unknown','number'),('a','mystery','number'),
         ('the','original','number'),('a','secret','number'),('number',)}
ADD_OPS={('plus',):'+',('minus',):'-',('increased','by'):'+',('decreased','by'):'-'}
THAN={('more','than'):'+',('less','than'):'-',('fewer','than'):'-'}
TWO_PLACE={'sum':'+','difference':'-','product':'*','quotient':'/'}
VERBS=[('is','equal','to'),('is','the','same','as'),('is','equivalent','to'),('equals',),('gives',),('results','in'),('will','be'),
       ('yields',),('makes',),('becomes',),('is',),('was',)]
RESULT=[('the','result','is'),('the','result','will','be'),('the','answer','is'),('the','sum','is'),('the','difference','is'),
        ('you','get'),('we','get'),('i','get'),('it','becomes'),('it','gives'),('it','equals'),('we','obtain'),('you','obtain')]

def read(text,nums,sents,sk):
    for f in (_number,_ages):
        r=f(text,nums,sents,sk)
        if r:return r
    return None

def _toks(x):return re.findall(r"#\d+|[a-z]+(?:-[a-z]+)*(?:'s)?|,",x)

class _Grammar:
    """every reading of a span of words as an expression: ('x', name) | ('k', index of the number) | (op, a, b)"""
    def __init__(g,t,nums,atom):g.t=t;g.nums=nums;g.atom=atom;g.memo={}
    def num(g,i):
        m=re.fullmatch(r'#(\d+)',g.t[i]) if i<len(g.t) else None
        return int(m.group(1)) if m else None
    def plain(g,k):
        n=g.nums[k];return n.kind in ('digits','word','decimal','fraction') and n.raw.lower() not in MULT and 'half' not in n.raw.lower()
    def frac(g,k):
        n=g.nums[k];return n.kind=='word' and n.value<1 and n.raw.lower() not in MULT
    def add(g,i,j):
        key=('a',i,j)
        if key in g.memo:return g.memo[key]
        g.memo[key]=[]
        out=list(g.mul(i,j))
        for m in range(i+1,j-1):
            for w,op in ADD_OPS.items():
                if tuple(g.t[m:m+len(w)])==w:out+=[(op,a,b) for a in g.add(i,m) for b in g.mul(m+len(w),j)]
            for w,op in THAN.items():
                if tuple(g.t[m:m+2])==w:
                    lefts=g.mul(i,m)+(g.mul(i,m-1) if g.t[m-1]=='years' else [])
                    out+=[(op,b,a) for a in lefts for b in g.add(m+2,j)]
        g.memo[key]=out;return out
    def mul(g,i,j):
        key=('m',i,j)
        if key in g.memo:return g.memo[key]
        g.memo[key]=[]
        out=[];t=g.t
        if j<=i:return out
        a=g.atom(t[i:j],i,j)
        if a:out.append(a)
        k=g.num(i)
        if j-i==1 and k is not None and g.plain(k):out.append(('k',k))
        if k is not None and j-i>=3 and t[i+1]=='times' and g.plain(k):out+=[('*',('k',k),e) for e in g.mul(i+2,j)]
        if k is not None and g.nums[k].raw.lower() in MULT and j-i>=2:out+=[('*',('k',k),e) for e in g.mul(i+1,j)]
        if k is not None and (g.frac(k) or 'half' in g.nums[k].raw.lower()) and j-i>=2:
            st=i+2 if t[i+1]=='of' else i+1
            out+=[('*',('k',k),e) for e in g.mul(st,j)]
        kk=g.num(j-1)
        if kk is not None and j-i>=4 and g.plain(kk):
            for w,op in ((('multiplied','by'),'*'),(('divided','by'),'/'),(('times',),'*')):
                if tuple(t[j-1-len(w):j-1])==w:out+=[(op,e,('k',kk)) for e in g.mul(i,j-1-len(w))]
        st=i+1 if t[i]=='the' else i
        if st+2<j and t[st] in TWO_PLACE and t[st+1] in ('of','between'):
            for m in range(st+3,j-1):
                if t[m]=='and':out+=[(TWO_PLACE[t[st]],a,b) for a in g.add(st+2,m) for b in g.add(m+1,j)]
        g.memo[key]=out;return out

def _fpl(e,names):
    if e[0]=='x':return e[1]
    if e[0]=='k':return names[e[1]]
    return f'({_fpl(e[1],names)} {e[0]} {_fpl(e[2],names)})'

def _consts(e,acc):
    if e[0]=='k':acc.append(e[1])
    elif e[0] in '+-*/':_consts(e[1],acc);_consts(e[2],acc)
    return acc

def _build(text,nums,unknowns,eqs,ask,form):
    """eqs: [(lhs, rhs, (a, b))] -> the reading, or None if a number is left out"""
    s=_Spec(text,nums);names={}
    for nm,about in unknowns:s.qty(nm,signed=(nm=='number'),about=about)
    for lhs,rhs,span in eqs:
        for k in _consts(lhs,[])+_consts(rhs,[]):
            if k not in names:names[k]=s.bind(f'c{len(names)+1}',k,about=nums[k].raw)
    for lhs,rhs,span in eqs:s.rel(f'{_fpl(lhs,names)} = {_fpl(rhs,names)}',*span)
    return s.done(ask,'',form)

def _only_answer(text,nums,unknowns,choices,ask,form):
    """choices: for each sentence, every reading of it. One answer from every combination, or None."""
    from .solve import solve
    import itertools
    combos=list(itertools.islice(itertools.product(*choices),0,65))
    if not combos or len(combos)>64:return None
    answers=set();first=None
    for c in combos:
        r=_build(text,nums,unknowns,list(c),ask,form)
        if not r:return None
        got=solve(r['spec'])
        if not got.get('ok'):return None
        answers.add(got['answer']);first=first or r
    return first if len(answers)==1 else None

# ----------------------------------------------------------------------------- a number
def _x_atom(ws,i,j):return ('x','number') if tuple(ws) in X_WORDS else None

def _sentence(g,t,lo):
    """every reading of a sentence about the number as (lhs, rhs)"""
    if t and t[0] in ('if','when'):t=t[1:];lo+=1
    out=[]
    if ',' in t:
        c=t.index(',');head,tail=t[:c],t[c+1:]
        for w in RESULT:
            if tuple(tail[:len(w)])==w:
                e3=g.add(lo+c+1+len(w),lo+len(t))
                for m in range(1,len(head)-2):
                    if head[m]!='is':continue
                    for op,(w1,w2) in (('+',('added','to')),('-',('subtracted','from'))):
                        if head[m+1:m+3]==[w1,w2]:
                            out+=[((op,b,a),c3) for a in g.add(lo,lo+m) for b in g.add(lo+m+3,lo+c) for c3 in e3]
        return out
    for m in range(1,len(t)-1):
        for w in VERBS:
            if tuple(t[m:m+len(w)])==w:out+=[(a,b) for a in g.add(lo,lo+m) for b in g.add(lo+m+len(w),lo+len(t))]
    return out

def _number(text,nums,sents,sk):
    if len(sk) not in (2,3) or not Q_NUM.fullmatch(sk[-1]):return None
    if len(sk)==3 and not INTRO.fullmatch(sk[0]):return None
    t=_toks(sk[-2]);g=_Grammar(t,nums,_x_atom)
    readings=_sentence(g,t,0)
    if not readings:return None
    span=sents[-2]
    return _only_answer(text,nums,[('number','the number')],[[(a,b,span) for a,b in readings]],'number','number:grammar')

# ----------------------------------------------------------------------------- ages
REL={'son','daughter','brother','sister','father','mother','cousin','friend','granddaughter','grandson','grandmother','grandfather',
     'uncle','aunt','niece','nephew','wife','husband','dad','mom','child','teacher','neighbor','neighbour','grandma','grandpa'}
NOT_NAMES={'i','a','an','the','if','when','in','on','how','what','find','he','she','his','her','they','their','it','its','after','before',
           'today','now','this','that','there','then','years','year','ago','old','age','ages','and','but','so','some','one','two','three'}

def _ages(text,nums,sents,sk):
    if len(sk)<2 or len(sk)>4 or not re.search(r'\byears? old\b|\bage\b|\bhow old\b',' '.join(sk)):return None
    caps={w.lower() for w in re.findall(r"\b([A-Z][a-z]+)(?:'s)?\b",text)}-NOT_NAMES
    state={'last':None}
    def person(ws):
        ws=[w[:-2] if w.endswith("'s") else w for w in ws]
        if len(ws)==1 and ws[0] in caps:return ws[0]
        if len(ws)==1 and ws[0] in ('he','she','him','his','her'):return state['last']
        if len(ws)==2 and ws[0] in ('his','her','their','the') and ws[1] in REL:return 'rel_'+ws[1]
        if len(ws)==2 and ws[0] in caps and ws[1] in REL:return 'rel_'+ws[1]
        return None
    def age_of(ws):
        """the age of a person: 'his son's age', 'the age of Steven', 'her age', 'Vidya's present age', 'his son'"""
        ws=list(ws)
        if ws[-2:-1] and ws[-1]=='age' and ws[-2] in ('present','current'):ws=ws[:-2]+['age']
        if len(ws)==2 and ws==[ws[0],'age'] and ws[0] in ('his','her'):return state['last']
        if ws[-1:]==['age'] and len(ws)>=2 and ws[-2].endswith("'s"):return person(ws[:-1])
        if ws[:3]==['the','age','of']:return person(ws[3:])
        return person(ws)
    def atom(ws,i,j):
        p=age_of(ws);return ('x','age_'+p) if p else None
    eqs=[];asked=None
    for n,x in enumerate(sk):
        t=_toks(x);span=sents[n]
        if n==len(sk)-1:
            asked=_age_question(t,person)
            continue
        r=_age_sentence(t,nums,person,age_of,atom)
        if not r:return None
        eqs.append([(a,b,span) for a,b in r])
        # who 'he', 'she', 'his' or 'her' means next: the first person named in a sentence that names one before any
        # pronoun ('Kate is 12 years old. His age is 4 times the age of Robbie.': 'his' is Kate)
        for w in t:
            b=w[:-2] if w.endswith("'s") else w
            if b in ('he','she','his','her','him'):break
            if b in caps:state['last']=b;break
    if not asked or not eqs:return None
    people=set()
    for ch in eqs:
        for a,b,_ in ch:_people(a,people);_people(b,people)
    if 'age_'+asked not in people:return None
    unknowns=[(p,'the age of '+p[4:].replace('rel_','the ')) for p in sorted(people)]
    return _only_answer(text,nums,unknowns,eqs,'age_'+asked,'age')

def _people(e,acc):
    if e[0]=='x':acc.add(e[1])
    elif e[0] in '+-*/':_people(e[1],acc);_people(e[2],acc)

def _age_question(t,person):
    s=' '.join(t)
    for rx in (r'how old is (?P<p>.+?)(?: now| at present| today)?',r'find (?:the )?(?:present )?age of (?P<p>.+?)',
               r"(?:find|what is|what's) (?P<p>.+?'s)(?: present| current)? age",r'what is the (?:present )?age of (?P<p>.+?)'):
        m=re.fullmatch(rx,s)
        if m:return person(m.group('p').split())
    return None

def _age_sentence(t,nums,person,age_of,atom):
    """every reading of one sentence about ages as (lhs, rhs)"""
    g=_Grammar(t,nums,atom);s=' '.join(t);L=len(t)
    def k_at(w):
        m=re.fullmatch(r'#(\d+)',w);return int(m.group(1)) if m else None
    def P(ws):
        p=person(ws);return ('x','age_'+p) if p else None
    # in k years, P will be m years old | k years ago, P was m years old
    m=re.fullmatch(r'in (#\d+) years ?,? (.+?) will be (#\d+)(?: years old)?',s) or re.fullmatch(r'(.+?) will be (#\d+)(?: years old)? in (#\d+) years',s)
    if m:
        if s.startswith('in '):k,who,v=m.group(1),m.group(2),m.group(3)
        else:who,v,k=m.group(1),m.group(2),m.group(3)
        p=P(who.split())
        return [(('+',p,('k',k_at(k))),('k',k_at(v)))] if p else None
    m=re.fullmatch(r'(#\d+) years ago ?,? (.+?) was (#\d+)(?: years old)?',s) or re.fullmatch(r'(.+?) was (#\d+)(?: years old)? (#\d+) years ago',s)
    if m:
        if s[0]=='#':k,who,v=m.group(1),m.group(2),m.group(3)
        else:who,v,k=m.group(1),m.group(2),m.group(3)
        p=P(who.split())
        return [(('-',p,('k',k_at(k))),('k',k_at(v)))] if p else None
    # P is k years old
    m=re.fullmatch(r'(.+?) (?:is|was) (#\d+) years old',s)
    if m:
        p=P(m.group(1).split())
        return [(p,('k',k_at(m.group(2))))] if p else None
    # P is k years older / younger than E
    m=re.fullmatch(r'(.+?) is (#\d+) years? (older|younger) than (.+)',s)
    if m:
        p=P(m.group(1).split());k=('k',k_at(m.group(2)))
        if not p:return None
        st=len(m.group(1).split())+5
        return [(p,('+' if m.group(3)=='older' else '-',e,k)) for e in g.add(st,L)] or None
    # P is k times as old as E
    m=re.fullmatch(r'(.+?) is ((?:#\d+ times)|#\d+) as old as (.+)',s)
    if m:
        p=P(m.group(1).split());c=k_at(m.group(2).split()[0])
        if not p or c is None:return None
        st=len(m.group(1).split())+1+len(m.group(2).split())+3
        return [(p,('*',('k',c),e)) for e in g.add(st,L)] or None
    # the age of P is E
    for n in range(2,L-1):
        if t[n]=='is':
            p=age_of(t[:n])
            if p:
                rs=[(('x','age_'+p),e) for e in g.add(n+1,L)]
                if rs:return rs
    return None
