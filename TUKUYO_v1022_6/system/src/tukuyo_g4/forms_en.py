"""generation 4: English questions that are not stories, read by exact patterns (no LLM).

  the greatest common factor / least common multiple of listed whole numbers
  speed, distance or time from the other two ("A train travels 240 km in 3 hours. What is its speed?")
  a number found from what is done to it ("I think of a number. If I divide it by 4, I get 9. What is the number?")

read(text) -> {'spec': FPL reading} when every sentence of the text belongs to one of these forms, else None (the
story reader then reads the text). Nothing is converted between units: a form whose units would need converting is
left unread.
"""
from __future__ import annotations
import re
from . import numbers as N
from .reader_en import sentences

FORM='tukuyo.g4.forms_en/1'

def _lit(v):return str(v.numerator) if v.denominator==1 else f'{v.numerator}/{v.denominator}'

def _skel(t,a,b,nums):
    """t[a:b] in lower case, each number replaced by #k (k indexes nums), spaces collapsed, end punctuation dropped"""
    out=[];i=a
    for k,n in enumerate(nums):
        if n.start<a or n.end>b:continue
        out.append(t[i:n.start].lower());out.append(f'#{k}');i=n.end
    out.append(t[i:b].lower())
    return re.sub(r'\s+',' ',''.join(out)).strip().rstrip('.?!').strip()

class _Spec:
    def __init__(s,text,nums):s.text=text;s.nums=nums;s.q={};s.facts=[];s.bound=set()
    def qty(s,name,unit='1',integer=False,signed=False,about=''):
        s.q[name]={'name':name,'unit':unit,'integer':integer,'signed':signed,'about':about};return name
    def bind(s,name,k,unit='1',about=''):
        n=s.nums[k];s.qty(name,unit,n.value.denominator==1 and unit=='1',about=about)
        s.facts.append({'eq':f'{name} = {_lit(n.value)}','span':s.around(n)});s.bound.add(k);return name
    def rel(s,eq,a,b):s.facts.append({'eq':eq,'span':s.text[a:b].strip()})
    def around(s,n):
        """the number with the word before it and the word after it"""
        a=n.start;b=n.end
        m=re.search(r'\S+\s+$',s.text[:a]);a=m.start() if m else a
        m=re.match(r'\s*[A-Za-z]+',s.text[b:]);b=b+m.end() if m else b
        return s.text[a:b].strip()
    def done(s,ask,unit,form):
        if any(k not in s.bound and not N.optional(n,s.text) for k,n in enumerate(s.nums)):return None
        return {'spec':{'schema':'tukuyo.g4.fpl/1','lang':'en','text':s.text,'quantities':list(s.q.values()),'facts':s.facts,
                        'ask':ask,'answer_unit':unit,'unused':[],'reader':FORM+':'+form}}

def read(text):
    try:return _read(text)
    except (ArithmeticError,ValueError,KeyError,IndexError,TypeError,AttributeError) as e:
        return {'spec':None,'reason':'FORMS:INTERNAL:'+type(e).__name__}

def _read(text):
    nums=N.find(text)
    sents=sentences(text)
    if not sents or not nums:return None
    sk=[_skel(text,a,b,nums) for a,b in sents]
    for f in (_gcd_lcm,_motion,_number):
        r=f(text,nums,sents,sk)
        if r:return r
    return None

# ---- greatest common factor / least common multiple -------------------------------
GL=re.compile(r"(?:what is|what's|find|determine|calculate|compute) the (greatest common factor|greatest common divisor|highest common factor|"
              r"gcf|gcd|hcf|least common multiple|lowest common multiple|lcm) of (#\d+(?:(?:, | and |, and )#\d+)+)")
def _gcd_lcm(text,nums,sents,sk):
    if len(sk)!=1:return None
    m=GL.fullmatch(sk[0])
    if not m:return None
    ks=[int(x) for x in re.findall(r'#(\d+)',m.group(2))]
    if len(ks)>4 or any(nums[k].value.denominator!=1 or nums[k].value<=0 or nums[k].kind not in ('digits','word') for k in ks):return None
    s=_Spec(text,nums);names=[s.bind(f'n{i+1}',k,about='a listed number') for i,k in enumerate(ks)]
    fn='gcd' if m.group(1) in ('greatest common factor','greatest common divisor','highest common factor','gcf','gcd','hcf') else 'lcm'
    expr=names[0]
    for n in names[1:]:expr=f'{fn}({expr}, {n})'
    r=s.qty('result',integer=True,about=m.group(1));s.rel(f'{r} = {expr}',*sents[0])
    return s.done(r,'',fn)

# ---- speed, distance, time --------------------------------------------------------
MOVE=r'(?:travels|travelled|traveled|drives|drove|runs|ran|walks|walked|flies|flew|goes|went|rides|rode|covers|covered|swims|swam|cycles|cycled|moves|moved|sails|sailed|jogs|jogged|bikes|biked|skates|skated|hikes|hiked)'
MOVE_BASE=r'(?:travel|drive|run|walk|fly|go|ride|cover|swim|cycle|move|sail|jog|bike|skate|hike)'
SUBJ=r"(?P<subj>(?:a|an|the|his|her|their|my|our) [a-z]+(?: [a-z]+)?|[a-z]+|it|he|she|they|we|i|you)"
LEN={'km':'kilometer','kilometer':'kilometer','kilometers':'kilometer','kilometre':'kilometer','kilometres':'kilometer','mile':'mile','miles':'mile',
     'meter':'meter','meters':'meter','metre':'meter','metres':'meter','m':'meter','foot':'foot','feet':'foot','ft':'foot','yard':'yard','yards':'yard'}
TIME={'hour':'hour','hours':'hour','hr':'hour','hrs':'hour','h':'hour','minute':'minute','minutes':'minute','min':'minute','mins':'minute',
      'second':'second','seconds':'second','sec':'second','secs':'second','s':'second'}
L=r'(?P<{}>'+'|'.join(sorted(LEN,key=len,reverse=True))+r')'
T=r'(?P<{}>'+'|'.join(sorted(TIME,key=len,reverse=True))+r')'
PER=r'(?:per|an|a|each|every)'
PRONOUNS=('it','he','she','they','we','i','you')
D_T=re.compile(SUBJ+r' '+MOVE+r' (?:a distance of )?#(?P<d>\d+) '+L.format('lu')+r' in #(?P<t>\d+) '+T.format('tu'))
SPEED=re.compile(SUBJ+r' (?:'+MOVE+r'|is (?:moving|traveling|travelling|going|driving|running|flying))(?: at)? (?:a (?:constant |steady |an average |average )?(?:speed|rate) of |an average speed of )?#(?P<s>\d+) '
                 +L.format('lu')+r' '+PER+r' '+T.format('tu'))
SPEED2=re.compile(SUBJ+r"(?:'s)? (?:average )?speed is #(?P<s>\d+) "+L.format('lu')+r' '+PER+r' '+T.format('tu'))
FOR_T=re.compile(SUBJ+r' (?:'+MOVE+r'|is (?:moving|traveling|travelling|going|driving|running|flying)) for #(?P<t>\d+) '+T.format('tu'))
Q_SPEED=re.compile(r"(?:what (?:is|was) (?:(?:its|his|her|their) |the (?:[a-z]+ )?(?:[a-z]+'s )?)?(?:average )?speed(?: of (?P<subj>(?:the|a|an) [a-z]+(?: [a-z]+)?))?|"
                   r"how fast (?:is|was|does|did|do) (?P<subj2>[a-z]+(?: [a-z]+){0,2}?)(?: "+MOVE_BASE+r"| moving| going| traveling| travelling)?)"
                   r"(?: in "+L.format('qlu')+r" "+PER+r" "+T.format('qtu')+r")?")
Q_SPEED2=re.compile(r"how many "+L.format('qlu')+r" "+PER+r" "+T.format('qtu')+r" (?:does|did|do|is|was) (?P<subj>[a-z]+(?: [a-z]+){0,2}?) (?:"+MOVE_BASE+r"|going|moving|traveling|travelling)")
Q_DIST=re.compile(r"how (?:far|many "+L.format('qlu')+r") (?:does|did|will|can|could|would|do) (?P<subj>[a-z]+(?: [a-z]+){0,2}?) "+MOVE_BASE+r"(?: in #(?P<t>\d+) "+T.format('tu')+r")?(?: in all| altogether| in total)?")
Q_TIME=re.compile(r"how (?:long|many "+T.format('qtu')+r") (?:does|did|will|would) (?:it take (?P<subj>[a-z]+(?: [a-z]+){0,2}?) to "+MOVE_BASE+r"|(?P<subj2>[a-z]+(?: [a-z]+){0,2}?) take to "+MOVE_BASE+r")(?: #(?P<d>\d+) "+L.format('dlu')+r")?")

def _same_subject(a,b):
    if a is None or b is None or a in PRONOUNS or b in PRONOUNS:return True
    strip=lambda x:re.sub(r'^(?:a|an|the|his|her|their|my|our) ','',x)
    return strip(a)==strip(b)

def _motion(text,nums,sents,sk):
    if len(sk)<2 or len(sk)>3:return None
    facts={};subj=[]
    for i,x in enumerate(sk[:-1]):
        m=None
        for kind,rx in (('dt',D_T),('speed',SPEED),('speed',SPEED2),('time',FOR_T)):
            m=rx.fullmatch(x)
            if m:break
        if not m or kind in facts or (kind=='dt' and ('speed' in facts or 'time' in facts)) or (kind!='dt' and 'dt' in facts):return None
        facts[kind]=(m,i);subj.append(m.group('subj'))
    q=sk[-1];qa,qb=sents[-1]
    s=_Spec(text,nums)
    def unit_of(m,g,table):
        u=m.groupdict().get(g);return table[u] if u else None
    for kind,rx in (('speed',Q_SPEED),('speed',Q_SPEED2),('dist',Q_DIST),('time',Q_TIME)):
        mq=rx.fullmatch(q)
        if mq:break
    else:return None
    qs=mq.groupdict().get('subj') or mq.groupdict().get('subj2')
    if any(not _same_subject(a,b) for a in subj+[qs] for b in subj+[qs]):return None
    if kind=='speed':
        if set(facts)!={'dt'}:return None
        m,i=facts['dt'];lu,tu=LEN[m.group('lu')],TIME[m.group('tu')]
        if (mq.groupdict().get('qlu') and LEN[mq.group('qlu')]!=lu) or (mq.groupdict().get('qtu') and TIME[mq.group('qtu')]!=tu):return None
        d=s.bind('distance',int(m.group('d')),lu,'the distance');t=s.bind('time',int(m.group('t')),tu,'the time')
        v=s.qty('speed',f'{lu}/{tu}',about='the speed');s.rel(f'{v} = {d} / {t}',*sents[i])
        return s.done(v,f'{lu}/{tu}','speed')
    if 'speed' not in facts or 'dt' in facts:return None
    m,i=facts['speed'];lu,tu=LEN[m.group('lu')],TIME[m.group('tu')]
    v=s.bind('speed',int(m.group('s')),f'{lu}/{tu}','the speed')
    if kind=='dist':
        if (mq.groupdict().get('qlu') and LEN[mq.group('qlu')]!=lu):return None
        if mq.group('t') is not None:
            if 'time' in facts or TIME[mq.group('tu')]!=tu:return None
            t=s.bind('time',int(mq.group('t')),tu,'the time')
        else:
            if 'time' not in facts:return None
            mt,j=facts['time']
            if TIME[mt.group('tu')]!=tu:return None
            t=s.bind('time',int(mt.group('t')),tu,'the time')
        d=s.qty('distance',lu,about='the distance');s.rel(f'{d} = {v} * {t}',*sents[i])
        return s.done(d,lu,'distance')
    if kind=='time':
        if 'time' in facts or mq.group('d') is None:return None
        if LEN[mq.group('dlu')]!=lu or (mq.groupdict().get('qtu') and TIME[mq.group('qtu')]!=tu):return None
        d=s.bind('distance',int(mq.group('d')),lu,'the distance')
        t=s.qty('time',tu,about='the time');s.rel(f'{t} = {d} / {v}',qa,qb)
        return s.done(t,tu,'time')
    return None

# ---- a number from what is done to it ---------------------------------------------
WHO=r'(?:i|you|we|he|she|they|[a-z]+)'
INTRO=re.compile(r"(?:i am thinking of|i'm thinking of|i think of|think of|i have|there is|"+WHO+r" (?:thinks|thought|is thinking|was thinking) of|"
                 +WHO+r" (?:picks|picked|chose|chooses|has)) a (?:certain |secret |mystery )?number")
IT=r'(?:it|the number|a number|that number|this number|the result|the answer)'
OP=re.compile(r'(?:(?P<div>divide '+IT+r' by #(?P<dk>\d+))|(?P<mul>multiply '+IT+r' by #(?P<mk>\d+))|(?P<add>add #(?P<ak>\d+)(?: to '+IT+r')?)|'
              r'(?P<sub>(?:subtract|take away) #(?P<sk>\d+)(?: from '+IT+r')?)|(?P<word>#(?P<wk>\d+) '+IT+r'))')
SEP=r'(?:, and then |, then |, and | and then | then | and |, )'
GET=r'(?:i|you|we|he|she|they|[a-z]+|the result|the answer|it) (?:get|gets|got|will get|would get|obtain|obtains|end up with|ends up with|is|equals|will be|becomes)'
DECL=[
 (re.compile(r'a number (?:divided by) #(?P<k>\d+) (?:is|equals|gives) #(?P<r>\d+)'),'{x} / {k}'),
 (re.compile(r'a number (?:multiplied by|times) #(?P<k>\d+) (?:is|equals|gives) #(?P<r>\d+)'),'{x} * {k}'),
 (re.compile(r'a number (?:plus|increased by|added to) #(?P<k>\d+) (?:is|equals|gives) #(?P<r>\d+)'),'{x} + {k}'),
 (re.compile(r'a number (?:minus|decreased by) #(?P<k>\d+) (?:is|equals|gives) #(?P<r>\d+)'),'{x} - {k}'),
 (re.compile(r'#(?P<k>\d+) more than a number is #(?P<r>\d+)'),'{x} + {k}'),
 (re.compile(r'#(?P<k>\d+) (?:less|fewer) than a number is #(?P<r>\d+)'),'{x} - {k}'),
 (re.compile(r'#(?P<k>\d+) (?:times )?(?:a|the) number is #(?P<r>\d+)'),'{k} * {x}'),
 (re.compile(r'#(?P<k>\d+) of a number is #(?P<r>\d+)'),'{k} * {x}'),
 (re.compile(r'the sum of a number and #(?P<k>\d+) is #(?P<r>\d+)'),'{x} + {k}'),
 (re.compile(r'the product of a number and #(?P<k>\d+) is #(?P<r>\d+)'),'{x} * {k}'),
 (re.compile(r'#(?P<k>\d+) (?:more|less|fewer) than #(?P<m>\d+) times a number is #(?P<r>\d+)'),None),
]
Q_NUM=re.compile(r"(?:what is|what was|what's|find|find out) (?:the|that|this) (?:original |mystery |secret |unknown )?number|what (?:number is it|is it|was it|"
                 r"number did "+WHO+r" (?:think of|pick|choose|start with))")
TIMES_WORDS={'double':2,'twice':2,'triple':3,'thrice':3}

def _number(text,nums,sents,sk):
    if len(sk) not in (2,3) or not Q_NUM.fullmatch(sk[-1]):return None
    if len(sk)==3 and not INTRO.fullmatch(sk[0]):return None
    body=sk[-2];a,b=sents[-2]
    s=_Spec(text,nums);x=s.qty('number',signed=True,about='the number')
    m=re.fullmatch(r'(?:if|when) '+WHO+r' (?P<ops>.+?), '+GET+r' #(?P<r>\d+)',body) or re.fullmatch(r'(?P<ops>.+?),? and '+GET+r' #(?P<r>\d+)',body)
    if m:
        ops=re.split(SEP,m.group('ops'))
        expr=x
        for i,o in enumerate(ops):
            mo=OP.fullmatch(o)
            if not mo:return None
            if mo.group('word'):
                k=int(mo.group('wk'))
                if nums[k].raw.lower() not in TIMES_WORDS:return None
                expr=f'({expr}) * {s.bind(f"c{i+1}",k,about=nums[k].raw.lower())}'
            elif mo.group('div'):expr=f'({expr}) / {s.bind(f"c{i+1}",int(mo.group("dk")),about="divided by")}'
            elif mo.group('mul'):expr=f'({expr}) * {s.bind(f"c{i+1}",int(mo.group("mk")),about="multiplied by")}'
            elif mo.group('add'):expr=f'({expr}) + {s.bind(f"c{i+1}",int(mo.group("ak")),about="added")}'
            else:expr=f'({expr}) - {s.bind(f"c{i+1}",int(mo.group("sk")),about="subtracted")}'
        r=s.bind('result',int(m.group('r')),about='the result')
        s.rel(f'{expr} = {r}',a,b)
        return s.done(x,'','number')
    for rx,tpl in DECL:
        md=rx.fullmatch(body)
        if not md:continue
        k=s.bind('c1',int(md.group('k')),about='the given number');r=s.bind('result',int(md.group('r')),about='the result')
        if tpl is None:
            mm=s.bind('c2',int(md.group('m')),about='times')
            sign='+' if re.search(r'#\d+ more than',body) else '-'
            s.rel(f'{mm} * {x} {sign} {k} = {r}',a,b)
        else:s.rel(f'{tpl.format(x=x,k=k)} = {r}',a,b)
        return s.done(x,'','number')
    return None
