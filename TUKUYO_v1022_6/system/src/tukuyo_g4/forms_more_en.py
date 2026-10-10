"""generation 4: more English questions that are not stories, read by exact patterns (no LLM), after forms_en:

  a pattern that continues   terms on consecutive days, months or numbered places; the pattern must be confirmed by
                             the terms given: a constant step (3 terms or more), a constant factor or steps that grow
                             by a constant (4 terms or more). Three terms whose steps differ are left unread: more than
                             one pattern fits them (2, 4, 8 is doubling, and also steps that grow by 2). A question
                             about a total so far is not a question about the next term, and is left unread
  the mean of listed numbers one list of 3 numbers or more; a count the text states must be in the same sentence, after
                             'in', 'over', 'for'..., and must be the length of the list; a question that asks for more
                             than the mean (rounded, after a next game...) is left unread
  a ratio                    'the ratio of A to B is p:q', 'for every p A ..., B ... q', 'A and B shared ... in the
                             ratio p:q', 'two numbers are in the ratio p:q', 'n A and the rest are B'
  perimeter and area         rectangles, squares, equilateral triangles and regular polygons, a missing side from an
                             area; the question must be about the thing measured; no unit is ever converted
  two unknown numbers        their sum and one of them, their sum and their difference, their difference and one
  together again             things that happen every 4 days and every 6 days (or every 3rd and every 5th visitor):
                             when they happen together again; things that come in groups of 12 and 18 when there are as
                             many of each: the smallest number of them (the least common multiple). A question about
                             the boxes or packs is not a question about the things in them, and is left unread

In a ratio, the verbs must agree: 'for every 2 laps Ana swims' is not about the laps Ana ran.

Every reading is an FPL reading like any other: solved exactly and checked by check.py. A sentence that does not fit
its form leaves the whole text unread. Relations only use the names and the literals 0 and 1 (FPL): a perimeter is
the sum of its sides, a count of listed numbers is a sum of ones.
"""
from __future__ import annotations
import re
from . import numbers as N
from .forms_en import _Spec

def read(text,nums,sents,sk):
    for f in (_sequence,_mean,_ratio,_geometry,_two_numbers,_together):
        r=f(text,nums,sents,sk)
        if r:return r
    from .forms_algebra_en import read as algebra
    return algebra(text,nums,sents,sk)

def _ks(x):return [int(k) for k in re.findall(r'#(\d+)',x)]
def _amounts(nums,text):return [k for k,n in enumerate(nums) if not N.optional(n,text)]
def _sing(w):
    w=w.strip()
    for a,b in (('ies','y'),('ves','f'),('sses','ss'),('xes','x'),('ches','ch'),('shes','sh')):
        if w.endswith(a) and len(w)>len(a)+1:return w[:-len(a)]+b
    return w[:-1] if w.endswith('s') and not w.endswith('ss') and len(w)>2 else w
ART=r'(?:the |a |an |his |her |their |its |our |my )?'
COUNT_WORD=re.compile(r'#(\d+)(?= (?:numbers?|of the (?:two )?numbers|of them)\b)')

def _restore(sk,nums):
    """'two numbers', 'one of the numbers', 'one number': these number words belong to the wording of the form, so they
    are put back as words; returns the skeletons and the indexes put back"""
    back=set()
    def put(m):
        k=int(m.group(1));n=nums[k]
        if n.kind=='word' and n.value in (1,2):back.add(k);return n.raw.lower()
        return m.group(0)
    return [COUNT_WORD.sub(put,x) for x in sk],back

def _spec(text,nums,back):
    s=_Spec(text,nums)
    for k in sorted(back):
        if not N.optional(nums[k],text):
            s.unused(k,'part of the wording: how many numbers there are or which one is meant ('+nums[k].raw+' number...)')
    return s
def _np(x):
    """a short noun phrase, compared without articles and plural endings"""
    x=re.sub(r"^(?:the|a|an|his|her|their|its|our|my|some|all) ",'',x.strip())
    ws=x.split()
    return ' '.join(ws[:-1]+[_sing(ws[-1])]) if ws else ''

# ----------------------------------------------------------------------------- a pattern that continues
DAYS=['monday','tuesday','wednesday','thursday','friday','saturday','sunday']
MONTHS=['january','february','march','april','may','june','july','august','september','october','november','december']
SO_FAR=re.compile(r"\b(?:in all|altogether|all together|in total|total|so far|combined|together|sum|by the end|after|until|through|from|between|and)\b")
CONT=re.compile(r'(?:if|when|assuming) (?:this|the|that) pattern (?:continues|keeps going|goes on),? how many (?P<noun>[a-z][a-z-]*)\b(?P<rest>.*)')

PLACE=r'(?:on|in|for|at|during|to) (?:the )?(?:(?P<day>'+'|'.join(DAYS)+r')|(?P<month>'+'|'.join(MONTHS)+r')|#(?P<k>\d+) (?P<noun>[a-z]+))\b'

def _place(m,nums):
    if not m:return None
    if m.group('day'):return 'day',DAYS.index(m.group('day'))
    if m.group('month'):return 'month',MONTHS.index(m.group('month'))
    k=int(m.group('k'))
    if nums[k].kind!='ordinal' or nums[k].value.denominator!=1:return None
    return 'ord:'+_sing(m.group('noun')),int(nums[k].value)

def _position(seg,nums):
    """the place a term belongs to, in the words after it: ('day', i) | ('month', i) | ('ord:<noun>', i) | None"""
    return _place(re.match(r'\s*(?:[a-z-]+ ){0,4}?'+PLACE,seg),nums)

def _at(x,k):return re.search(rf'#{k}(?!\d)',x).start()

def _sequence(text,nums,sents,sk):
    if len(sk)<2:return None
    mq=CONT.fullmatch(sk[-1])
    if not mq or SO_FAR.search(mq.group('rest')):return None
    data=' '.join(sk[:-1])
    terms=[];noun=None
    for x in sk[:-1]:
        ks=[k for k in _ks(x) if nums[k].kind!='ordinal']
        for i,k in enumerate(ks):
            # the words after the number, up to the next term of this sentence
            seg=x[_at(x,k)+len(f'#{k}'):(_at(x,ks[i+1]) if i+1<len(ks) else len(x))]
            w=re.match(r'\s*([a-z][a-z-]*)',seg)
            if not w:return None
            noun=noun or _sing(w.group(1))
            if _sing(w.group(1))!=noun and terms and not re.match(r'\s*(?:on|in|for|at|during|to)\b',seg):return None
            pos=_position(seg,nums)
            # 'On the first day, Ben found 3 shells.': the place before the only term of its sentence
            if pos is None and len(ks)==1:pos=_place(re.match(PLACE+r',? ',x),nums)
            if pos is None:return None
            terms.append((pos,k))
    if len(terms)<3 or any(k not in [t for _,t in terms] for k in _amounts(nums,text) if k in _ks(data)):return None
    kinds={p[0] for p,_ in terms}
    if len(kinds)!=1:return None
    kind=kinds.pop();cycle={'day':7,'month':12}.get(kind)
    idx=[p[1] for p,_ in terms]
    for a,b in zip(idx,idx[1:]):
        if (b-a)%(cycle or 10**9)!=1 or (not cycle and b-a!=1):return None
    if _sing(mq.group('noun'))!=noun:return None
    qpos=_position(' '+re.sub(r'^.*?(?= (?:on|in|for|at|during|to) )','',mq.group('rest'),count=1),nums)
    if qpos is None or qpos[0]!=kind:return None
    ahead=(qpos[1]-idx[-1])%cycle if cycle else qpos[1]-idx[-1]
    if not 1<=ahead<=6:return None
    v=[nums[k].value for _,k in terms];d=[b-a for a,b in zip(v,v[1:])]
    fits={}
    if len(set(d))==1:
        nxt=v[-1];out=[]
        for _ in range(ahead):nxt+=d[0];out.append(nxt)
        fits['step']=out
    if len(v)>=4 and all(x!=0 for x in v) and len({b/a for a,b in zip(v,v[1:])})==1:
        r=v[1]/v[0];nxt=v[-1];out=[]
        for _ in range(ahead):nxt*=r;out.append(nxt)
        fits['factor']=out
    if len(v)>=4 and len(set(d))>1 and len({b-a for a,b in zip(d,d[1:])})==1:
        inc=d[1]-d[0];nxt=v[-1];dd=d[-1];out=[]
        for _ in range(ahead):dd+=inc;nxt+=dd;out.append(nxt)
        fits['growing_step']=out
    if not fits or len({tuple(x) for x in fits.values()})!=1:return None
    how=next(iter(fits))
    s=_Spec(text,nums);a=sents[0][0];b=sents[-2][1];qa,qb=sents[-1]
    names=[s.bind(f't{i+1}',k,about=f'the term for place {i+1}') for i,(_,k) in enumerate(terms)]
    whole=all(x.denominator==1 for x in v)
    if how=='step':
        st=s.qty('step',signed=True,about='the same step between the terms')
        for x,y in zip(names,names[1:]):s.rel(f'{st} = {y} - {x}',a,b)
        prev=names[-1]
        for j in range(ahead):nm=s.qty(f'next{j+1}',integer=whole,about='the next term');s.rel(f'{nm} = {prev} + {st}',qa,qb);prev=nm
    elif how=='factor':
        f=s.qty('factor',about='the same factor between the terms')
        for x,y in zip(names,names[1:]):s.rel(f'{f} = {y} / {x}',a,b)
        prev=names[-1]
        for j in range(ahead):nm=s.qty(f'next{j+1}',integer=whole,about='the next term');s.rel(f'{nm} = {prev} * {f}',qa,qb);prev=nm
    else:
        ds=[s.qty(f'd{i+1}',signed=True,about='a step between two terms') for i in range(len(names)-1)]
        for dn,(x,y) in zip(ds,zip(names,names[1:])):s.rel(f'{dn} = {y} - {x}',a,b)
        inc=s.qty('growth',signed=True,about='how much each step grows')
        for x,y in zip(ds,ds[1:]):s.rel(f'{inc} = {y} - {x}',a,b)
        prev=names[-1];pd=ds[-1]
        for j in range(ahead):
            dn=s.qty(f'dnext{j+1}',signed=True,about='the next step');s.rel(f'{dn} = {pd} + {inc}',qa,qb)
            nm=s.qty(f'next{j+1}',integer=whole,about='the next term');s.rel(f'{nm} = {prev} + {dn}',qa,qb);prev=nm;pd=dn
    return s.done(prev,'','sequence:'+how)

# ----------------------------------------------------------------------------- the mean of listed numbers
QMEAN=re.compile(r'(?:what (?:is|was|were) (?:the |her |his |their |its )?|find (?:the |her |his |their |its )?|calculate (?:the )?|determine (?:the )?|compute (?:the )?)'
                 r'(?:mean|average|arithmetic mean)\b(?P<tail>(?: [a-z\'-]+){0,10})')
MORE_THAN_MEAN=re.compile(r"\b(?:round|rounded|nearest|if|after|next|more|less|than|without|excluding|except|median|mode|range|total|sum|"
                          r"new|increase|decrease|change|other|remaining|rest|difference|percent|would|another|added|removed|drop|dropped|highest|lowest)\b")
LIST=re.compile(r'#\d+(?: ?[a-z%]+)?(?:, #\d+(?: ?[a-z%]+)?)+,? and #\d+|#\d+(?:, #\d+){2,}')
WHEN=r'(?:on|in) (?:'+'|'.join(DAYS+MONTHS)+r')'
LIST_WHEN=re.compile(r'#\d+(?: [a-z]+)? '+WHEN+r'(?:, #\d+ '+WHEN+r')*,? and #\d+ '+WHEN)

def _mean(text,nums,sents,sk):
    mq=QMEAN.fullmatch(sk[-1]) if len(sk)>=2 else None
    if not mq or MORE_THAN_MEAN.search(mq.group('tail')):return None
    lists=[(i,m) for i,x in enumerate(sk[:-1]) for m in LIST.finditer(x)]
    when=[(i,m) for i,x in enumerate(sk[:-1]) for m in LIST_WHEN.finditer(x)]
    if when:
        # '12 cakes on Monday, 15 on Tuesday, ...': one number for each day (or month), every day a different one
        if len(when)!=1 or lists:return None
        i,m=when[0];items=_ks(m.group());days=re.findall(WHEN,m.group())
        if len(set(days))!=len(days):return None
    else:
        if len(lists)!=1:return None
        i,m=lists[0];items=_ks(m.group())
        units={re.sub(r'#\d+','',x).strip() for x in re.split(r',? and |, ',m.group()) if re.sub(r'#\d+','',x).strip()}
        if len(units)>1:return None
    if len(items)<3 or any(nums[k].kind in ('ordinal',) for k in items):return None
    others=[k for k in _amounts(nums,text) if k not in items]
    s=_Spec(text,nums);la=sents[i][0];lb=sents[i][1]
    names=[s.bind(f'x{j+1}',k,about='a listed number') for j,k in enumerate(items)]
    total=s.qty('total',integer=all(nums[k].value.denominator==1 for k in items),about='the sum of the listed numbers')
    s.rel(f"{total} = {' + '.join(names)}",la,lb)
    if others:
        # 'in four games', 'over 5 days': the count the text states, in the sentence of the list
        k=others[0]
        if len(others)!=1 or nums[k].value!=len(items) or not re.search(r'\b(?:in|over|for|from|during|across|of) (?:the |these |those |her |his |their |its )?(?:last |past |first )?#'+str(k)+r' [a-z]+',sk[i]):return None
        count=s.bind('count',k,about='how many numbers there are')
    else:
        count=s.qty('count',integer=True,about='how many numbers are listed');s.rel(f"{count} = {' + '.join('1' for _ in names)}",la,lb)
    mean=s.qty('mean',about='the mean');s.rel(f'{mean} = {total} / {count}',*sents[-1])
    return s.done(mean,'','mean')

# ----------------------------------------------------------------------------- ratios
NP=r'[a-z][a-z-]*(?: [a-z][a-z-]*)?'
R_OF=re.compile(r'(?:(?:at|in|on|for|during|among|from) [a-z\' -]+? )?(?:the )?ratio of '+ART+r'(?P<a>'+NP+r') to '+ART+r'(?P<b>'+NP+r')(?: (?:in|at|on|of|among) [a-z\' ]+?)? (?:is|was|are|were) #(?P<p>\d+) ?: ?#(?P<q>\d+)')
R_ATTR=re.compile(r'(?:the )?(?P<attr>[a-z ]+?) (?:of|by) (?P<a>[a-z]+) and (?P<b>[a-z]+) (?:is|are|was|were) in the ratio(?: of)? #(?P<p>\d+) ?: ?#(?P<q>\d+)')
R_EVERY=re.compile(r'for every #(?P<p>\d+) (?P<an>[a-z][a-z -]*?) (?P<a>[a-z]+) (?P<av>[a-z]+), (?P<b>[a-z]+) (?P<bv>[a-z]+) #(?P<q>\d+)(?: (?P<bn>[a-z][a-z -]*))?')
R_SHARE=re.compile(r'(?P<a>[a-z]+) and (?P<b>[a-z]+) (?:shared|split|divided|share|split up) (?:some |the |their |a (?:bag|box|pile|jar|set) of )?(?P<n>'+NP+r') in the ratio(?: of)? #(?P<p>\d+) ?: ?#(?P<q>\d+)')
R_TWO=re.compile(r'(?:the )?two numbers are in the ratio(?: of)? #(?P<p>\d+) ?: ?#(?P<q>\d+)')
R_REST=re.compile(r'(?:.*? )?#(?P<n>\d+) (?P<x>'+NP+r') and (?:the )?rest (?:of them )?(?:are|were) (?P<y>'+NP+r')')
K_THERE=re.compile(r'(?:if )?there (?:are|were|is) #(?P<n>\d+) (?P<x>'+NP+r')(?: (?:in|at|on) [a-z\' ]+)?')
K_NUMBER=re.compile(r'(?:if )?the number of '+ART+r'(?P<x>'+NP+r') (?:is|was) #(?P<n>\d+)')
K_ATTR=re.compile(r'(?:the )?(?P<attr>[a-z ]+?) (?:of|by) (?P<x>[a-z]+) (?:is|was) #(?P<n>\d+) (?P<u>[a-z]+)')
K_DID=re.compile(r'(?P<x>[a-z]+) (?P<xv>[a-z]+) #(?P<n>\d+)(?: (?P<xn>[a-z][a-z -]*))?')
K_SUM=re.compile(r'(?:their|the) (?P<what>sum|difference)(?: (?:of|between) (?:the |these )?(?:two )?numbers)? (?:is|was) #(?P<n>\d+)')
K_HAS=re.compile(r'(?:a |an |the |his |her |their )?[a-z][a-z\' -]*? (?:has|had|have) #(?P<n>\d+) (?P<x>'+NP+r')(?: (?:in|at|on) [a-z\' ]+)?')
Q_TOTAL=re.compile(r'how many (?P<y>[a-z][a-z -]*?) (?:are|were|is) (?:there )?(?:in all|in total|total|altogether|combined)|'
                   r'how many (?P<y2>[a-z][a-z -]*?) (?:does|did|do) (?:the |a |an )?[a-z ]+? have (?:in all|in total|total|altogether)')
R_RATE=re.compile(r'(?:.*? )?(?:uses|use|used|needs|need|needed|requires|require|required|calls for|takes|take|took|makes|make|made) '
                  r'#(?P<p>\d+) (?P<a>[a-z][a-z\' -]*?) for (?:every|each) #(?P<q>\d+) (?P<b>[a-z][a-z\' -]*)')
K_ANY=re.compile(r'(?:[a-z][a-z\' -]*? )?#(?P<n>\d+) (?P<x>[a-z][a-z\' -]*)')
Q_HOW=re.compile(r'how many (?P<y>[a-z][a-z\' -]*?) (?:are|is|will|would|do|does|did|should|must|can|could) .+')
MEASURE={'cup','liter','litre','ounce','gram','kilogram','kg','pound','gallon','quart','pint','ml','milliliter','teaspoon','tablespoon',
         'meter','metre','mile','kilometer','km','foot','feet','inch','yard','hour','minute','second'}
CHANGE=re.compile(r"\b(?:some|more|fewer|less|half|twice|double|doubled|triple|tripled|each|every|per|all|none|left|remaining|rest|"
                  r"gave|give|gives|lost|lose|loses|ate|eat|eats|sold|sell|sells|spent|spend|took|take|takes|added|add|adds|removed|remove|"
                  r"cut|cuts|broke|broken|increased|increase|decreased|decrease|shared|share|split|divided|divide|used|use|uses|enlarged|"
                  r"enlarge|shrank|shrink|extended|extend|borrowed|returned|other|another|also|too|again|then|after|before|later|but|"
                  r"however|except|only|not|no|never|square|equal|same|circle|circular|round|triangle|triangular|cube|box|than|times|"
                  r"bigger|smaller|larger|longer|shorter|wider|narrower|taller|ratio|total|sum|difference|each|both|any|many|much)\b")

def _context_ok(x):
    """a sentence without numbers that only sets the scene ('Kim was painting a door.'): no word that could change or
    add to what the other sentences give"""
    return not re.search(r'#\d',x) and len(x.split())<=15 and not CHANGE.search(x)

def _norm(x):
    """a noun phrase without articles, every word singular ('cups of sugar' -> 'cup of sugar')"""
    x=re.sub(r"^(?:the|a|an|his|her|their|its|our|my|some) ",'',x.strip())
    return ' '.join(_sing(w) for w in x.split())

def _clauses(sk):
    """each sentence as clauses (words, sentence index, role): 'if A, B' and 'B if A' give a condition A; 'A, find B'"""
    out=[]
    for i,x in enumerate(sk):
        last=i==len(sk)-1;role='q' if last else 'main'
        m=re.fullmatch(r'(?:if|when|since) (?P<a>[^,]+), (?P<b>.+)',x)
        if m:out+=[(m.group('a'),i,'if'),(m.group('b'),i,role)];continue
        m=re.fullmatch(r'(?P<a>[^,]+), (?P<b>(?:find|what|how|calculate|determine) .+)',x) if last else None
        if m:out+=[(m.group('a'),i,'main'),(m.group('b'),i,'q')];continue
        m=re.fullmatch(r'(?P<b>(?:find|what|how) .+?) if (?P<a>[^,]+)',x) if last else None
        if m:out+=[(m.group('a'),i,'if'),(m.group('b'),i,'q')];continue
        out.append((x,i,role))
    return out
Q_MANY=re.compile(r'how many (?P<y>'+NP+r') (?:are|were|is) (?:there|in [a-z\' ]+)(?: in [a-z\' ]+)?|find (?:out )?the number of '+ART+r'(?P<y2>'+NP+r')(?: [a-z\' ]+)?|'
                  r'how many (?P<y3>'+NP+r') (?:does|do|did) (?:the |a )?[a-z]+ (?:have|contain|hold)')
Q_DID=re.compile(r'how many (?:(?P<yn>[a-z][a-z -]*?) )?(?:did|does|will|would) (?P<y>[a-z]+) (?P<yv>[a-z]+)')
Q_CMP=re.compile(r'how many (?P<cmp>more|fewer|less) (?:(?P<yn>[a-z][a-z -]*?) )?(?:did|does|will|would) (?P<y>[a-z]+) (?P<yv>[a-z]+) than (?P<z>[a-z]+)')
Q_ATTR=re.compile(r'(?:find|what is|what was) (?:the )?(?P<attr>[a-z ]+?) (?:of|by) (?P<y>[a-z]+)')
Q_TWO=re.compile(r'(?:what is|find|what\'s) the (?P<which>larger|smaller|bigger|greater|lesser|largest|smallest) (?:number|one|of the two(?: numbers)?)|'
                 r'(?:what is|find) the (?P<diff>difference|sum) (?:between|of) the (?:two )?numbers')

IRREGULAR={'swam':'swim','swum':'swim','ran':'run','ate':'eat','eaten':'eat','made':'make','sold':'sell','bought':'buy','wrote':'write',
 'written':'write','drew':'draw','drawn':'draw','drove':'drive','driven':'drive','rode':'ride','ridden':'ride','took':'take','taken':'take',
 'gave':'give','given':'give','got':'get','gotten':'get','had':'have','has':'have','did':'do','does':'do','went':'go','goes':'go','caught':'catch',
 'threw':'throw','thrown':'throw','grew':'grow','grown':'grow','found':'find','won':'win','spent':'spend','paid':'pay','saw':'see','seen':'see',
 'built':'build','sang':'sing','sung':'sing','dug':'dig','fed':'feed','held':'hold','kept':'keep','lost':'lose','sent':'send','told':'tell',
 'brought':'bring','flew':'fly','flown':'fly','wore':'wear','broke':'break','chose':'choose','fell':'fall','hid':'hide','shook':'shake',
 'stole':'steal','knew':'know','drank':'drink','drunk':'drink','began':'begin','begun':'begin','spun':'spin','swung':'swing'}
def _bases(w):
    """the forms a verb could come from ('swims' swim, 'swam' swim, 'picked' pick)"""
    out={w}
    if w in IRREGULAR:out.add(IRREGULAR[w])
    if w.endswith(('ies','ied')):out.add(w[:-3]+'y')
    if w.endswith('es'):out.add(w[:-2])
    if w.endswith('s') and not w.endswith('ss'):out.add(w[:-1])
    if w.endswith('ed'):
        out.update((w[:-2],w[:-1]))
        if len(w)>4 and w[-3]==w[-4]:out.add(w[:-3])
    return out
def _same_verb(a,b):return bool(_bases(a)&_bases(b))
GOT=('get','receive','have','take','keep')

def _ratio_equation(s,ka,kb,pa,pb,span):
    """A : B = p : q, as A * q = B * p"""
    s.rel(f'{ka} * {pb} = {kb} * {pa}',*span)

def _ratio(text,nums,sents,sk):
    if len(sk)<2 or len(sk)>4:return None
    sk,back=_restore(sk,nums)
    cl=_clauses(sk);qs=[c for c in cl if c[2]=='q']
    if len(qs)!=1:return None
    q,qi,_=qs[0];body=[c for c in cl if c[2]!='q']
    # exactly one clause gives the ratio; the clauses that only set the scene are left aside
    found=[(c,rx,m) for c in body for rx in (R_OF,R_ATTR,R_EVERY,R_SHARE,R_TWO,R_RATE) for m in [rx.fullmatch(c[0])] if m]
    if len(found)!=1:return None
    c0,rx,m=found[0];s=_spec(text,nums,back);span=sents[c0[1]]
    others=[c for c in body if c is not c0 and not _context_ok(c[0])]
    def bind_ratio():
        return s.bind('ratio_first',int(m.group('p')),about='the first number of the ratio'),s.bind('ratio_second',int(m.group('q')),about='the second number of the ratio')
    if rx is R_TWO:
        if len(others)!=1:return None
        mk=K_SUM.fullmatch(others[0][0]);mq=Q_TWO.fullmatch(q)
        if not mk or not mq:return None
        pa,pb=bind_ratio();a=s.qty('first',about='the first number');b=s.qty('second',about='the second number')
        _ratio_equation(s,a,b,pa,pb,span);n=s.bind('given',int(mk.group('n')),about='their '+mk.group('what'))
        p,qq=nums[int(m.group('p'))].value,nums[int(m.group('q'))].value
        big,small=(b,a) if qq>p else (a,b)
        if p==qq:return None
        if mk.group('what')=='sum':s.rel(f'{a} + {b} = {n}',*sents[others[0][1]])
        else:s.rel(f'{big} - {small} = {n}',*sents[others[0][1]])
        if mq.group('which'):
            ans=big if mq.group('which') in ('larger','bigger','greater','largest') else small
            return s.done(ans,'','ratio:two_numbers')
        r=s.qty('result',about='the asked '+mq.group('diff'))
        s.rel(f'{r} = {big} - {small}' if mq.group('diff')=='difference' else f'{r} = {a} + {b}',*sents[qi])
        return s.done(r,'','ratio:two_numbers')
    if rx is R_RATE:
        return _rate(text,nums,sents,s,m,span,others,q,qi,bind_ratio)
    if rx is R_OF:
        A,B=_np(m.group('a')),_np(m.group('b'))
        if not A or not B or A==B or len(others)!=1:return None
        x2,j,_=others[0]
        mr=R_REST.fullmatch(x2);mk=None
        if mr:
            X,Y=_np(mr.group('x')),_np(mr.group('y'))
            if {X,Y}!={A,B}:return None
        else:
            mk=K_THERE.fullmatch(x2) or K_NUMBER.fullmatch(x2) or K_HAS.fullmatch(x2)
            if not mk:return None
            X=_np(mk.group('x'))
        if X not in (A,B):return None
        mt=Q_TOTAL.fullmatch(q);mq=None if mt else Q_MANY.fullmatch(q)
        if not mq and not mt:return None
        pa,pb=bind_ratio();a=s.qty('first',integer=True,about=m.group('a'));b=s.qty('second',integer=True,about=m.group('b'))
        _ratio_equation(s,a,b,pa,pb,span);kn=s.bind('known',int((mr or mk).group('n')),about='the number of '+X)
        s.rel(f'{a if X==A else b} = {kn}',*sents[j])
        if mq:
            Y=_np(mq.group('y') or mq.group('y2') or mq.group('y3'))
            if Y not in (A,B) or X==Y:return None
            return s.done(b if Y==B else a,'','ratio:of')
        # 'how many animals are there in total': both kinds together (a question about one of them is not a total)
        if _np(mt.group('y') or mt.group('y2')) in (A,B):return None
        t=s.qty('total',integer=True,about='both together');s.rel(f'{t} = {a} + {b}',*sents[qi])
        return s.done(t,'','ratio:total')
    if rx is R_ATTR:
        if len(others)!=1:return None
        mk=K_ATTR.fullmatch(others[0][0]);mq=Q_ATTR.fullmatch(q)
        if not mk or not mq:return None
        A,B=m.group('a'),m.group('b');X,Y=mk.group('x'),mq.group('y')
        if {X,Y}!={A,B} or _np(mk.group('attr'))!=_np(m.group('attr')) or _np(mq.group('attr'))!=_np(m.group('attr')):return None
        u=_sing(mk.group('u'))
        pa,pb=bind_ratio();a=s.qty('first',unit=u,about=f'{m.group("attr")} of {A}');b=s.qty('second',unit=u,about=f'{m.group("attr")} of {B}')
        _ratio_equation(s,a,b,pa,pb,span);kn=s.bind('known',int(mk.group('n')),unit=u,about=f'{m.group("attr")} of {X}')
        s.rel(f'{a if X==A else b} = {kn}',*sents[others[0][1]])
        return s.done(b if Y==B else a,u,'ratio:attribute')
    # for every p A, B q   |   A and B shared n in the ratio p:q
    A,B=m.group('a'),m.group('b')
    if A==B or len(others)!=1:return None
    mk=K_DID.fullmatch(others[0][0])
    if not mk or mk.group('x') not in (A,B):return None
    X=mk.group('x')
    mc=Q_CMP.fullmatch(q);md=None if mc else Q_DID.fullmatch(q)
    mq=mc or md
    if not mq:return None
    Y=mq.group('y')
    if rx is R_EVERY:
        noun=_np(m.group('an'));bn=m.group('bn')
        if bn and _np(bn)!=noun:return None
        if mk.group('xn') and _np(mk.group('xn'))!=noun:return None
        verb={A:m.group('av'),B:m.group('bv')}
        if not _same_verb(mk.group('xv'),verb[X]) or Y not in verb or not _same_verb(mq.group('yv'),verb[Y]):return None
    else:
        noun=_np(m.group('n'))
        if not any(_same_verb(mk.group('xv'),g) for g in GOT) or not any(_same_verb(mq.group('yv'),g) for g in GOT):return None
        if mk.group('xn') and _np(mk.group('xn'))!=noun:return None
    if mq.group('yn') and _np(mq.group('yn'))!=noun:return None
    pa,pb=bind_ratio();a=s.qty('first',integer=True,about=f'{noun} of {A}');b=s.qty('second',integer=True,about=f'{noun} of {B}')
    _ratio_equation(s,a,b,pa,pb,span);kn=s.bind('known',int(mk.group('n')),about=f'{noun} of {X}')
    s.rel(f'{a if X==A else b} = {kn}',*sents[others[0][1]])
    if md:
        if Y not in (A,B) or Y==X:return None
        return s.done(b if Y==B else a,'','ratio:'+('every' if rx is R_EVERY else 'shared'))
    Z=mc.group('z')
    if {Y,Z}!={A,B}:return None
    yq,zq=(a,b) if Y==A else (b,a)
    r=s.qty('result',integer=True,about=f'how many {mc.group("cmp")}')
    s.rel(f'{r} = {yq} - {zq}' if mc.group('cmp')=='more' else f'{r} = {zq} - {yq}',*sents[qi])
    return s.done(r,'','ratio:compare')

def _rate(text,nums,sents,s,m,span,others,q,qi,bind_ratio):
    """'a recipe uses 3 cups of sugar for every 4 cups of flour' and one amount of either: the other amount"""
    A,B=_norm(m.group('a')),_norm(m.group('b'))
    if not A or not B or A==B:return None
    known=None
    mq=re.fullmatch(r'(?P<q>.+?) for #(?P<n>\d+) (?P<x>[a-z][a-z\' -]*)',q)
    if mq and not others:known=(_norm(mq.group('x')),int(mq.group('n')),sents[qi]);q=mq.group('q')
    elif len(others)==1 and not mq:
        mk=K_ANY.fullmatch(others[0][0])
        if mk:known=(_norm(mk.group('x')),int(mk.group('n')),sents[others[0][1]])
    my=Q_HOW.fullmatch(q)
    if not known or not my:return None
    X,n,kspan=known;Y=_norm(my.group('y'))
    if X not in (A,B) or Y not in (A,B) or X==Y:return None
    whole=lambda P:P.split()[0] not in MEASURE
    pa,pb=bind_ratio();a=s.qty('first',integer=whole(A),about=m.group('a'));b=s.qty('second',integer=whole(B),about=m.group('b'))
    _ratio_equation(s,a,b,pa,pb,span);kn=s.bind('known',n,about=X)
    s.rel(f'{a if X==A else b} = {kn}',*kspan)
    return s.done(b if Y==B else a,'','ratio:rate')

# ----------------------------------------------------------------------------- perimeter and area
LEN={'km':'kilometer','kilometer':'kilometer','kilometers':'kilometer','kilometre':'kilometer','kilometres':'kilometer',
     'm':'meter','meter':'meter','meters':'meter','metre':'meter','metres':'meter','cm':'centimeter','centimeter':'centimeter','centimeters':'centimeter',
     'centimetre':'centimeter','centimetres':'centimeter','mm':'millimeter','millimeter':'millimeter','millimeters':'millimeter',
     'mile':'mile','miles':'mile','yard':'yard','yards':'yard','yd':'yard','foot':'foot','feet':'foot','ft':'foot','inch':'inch','inches':'inch','in':'inch'}
LU=r'(?:'+'|'.join(sorted(LEN,key=len,reverse=True))+r')'
AREA=r'(?:square|sq\.?|sq) (?P<au>'+LU+r')'
SIDES={'triangle':3,'square':4,'pentagon':5,'hexagon':6,'heptagon':7,'octagon':8,'nonagon':9,'decagon':10}
DIMS=[re.compile(r'(?P<obj>.+?) (?:is|measures|measured|was|were|are) #(?P<x>\d+) (?P<xu>'+LU+r') (?P<xd>long|wide|high|tall|in length|in width)(?:,)? and #(?P<y>\d+) (?P<yu>'+LU+r') (?P<yd>long|wide|high|tall|in length|in width)'),
      re.compile(r'(?P<obj>.+?) (?:is|measures|measured|was|were|are) #(?P<x>\d+) (?P<xu>'+LU+r') by #(?P<y>\d+) (?P<yu>'+LU+r')'),
      re.compile(r'(?P<obj>.+?) (?:has|had|have|with) a length of #(?P<x>\d+) (?P<xu>'+LU+r') and a width of #(?P<y>\d+) (?P<yu>'+LU+r')'),
      re.compile(r'the length of (?P<obj>.+?) is #(?P<x>\d+) (?P<xu>'+LU+r') and (?:its|the) width(?: of [a-z ]+)? is #(?P<y>\d+) (?P<yu>'+LU+r')')]
SQUARE=re.compile(r'(?P<obj>(?:a|the|each) square [a-z ]*?|.*?\bsquare\b.*?) (?:has|with) (?:sides|a side|each side|a side length|side lengths?) (?:of|measuring) #(?P<x>\d+) (?P<xu>'+LU+r')|'
                  r'the side of (?P<obj2>(?:a|the) square [a-z ]*?) (?:is|measures) #(?P<x2>\d+) (?P<xu2>'+LU+r')')
Q_PA=re.compile(r'(?:what is|what was|find|calculate|determine) (?:the |its |their )?(?P<what>perimeter|area)(?: of .+)?')
PERI=re.compile(r'(?:the )?(?:total )?perimeter of (?:a |an |the |this )?(?P<shape>.+?) is #(?P<p>\d+) (?P<u>'+LU+r')')
Q_SIDE=re.compile(r'(?:how long is|find the length of|what is the length of|find the measure of|what is the measure of|find the|what is the) (?:each|one) side(?: of .+)?|'
                  r'find (?:the )?(?:length|measure) of each side(?: of .+)?|how long is each side(?: of .+)?|find the length of ribbon required to border each side')
# one side and the area or the perimeter; a diameter or a radius (clauses of the sentences, in any order)
OBJ=r'(?:(?P<obj>(?!(?:has|had|have|with)\b).+?) )?'
MEASURED=[('area',re.compile(OBJ+r'(?:(?:has|had|have|with) )?(?:a |an )?(?:total |surface )?area of #(?P<x>\d+) '+AREA)),
          ('area',re.compile(r'(?:the |its |their )(?:total |surface )?area(?: of (?P<obj>.+?))? (?:is|was) #(?P<x>\d+) '+AREA)),
          ('perimeter',re.compile(OBJ+r'(?:(?:has|had|have|with) )?(?:a |an )?(?:total )?perimeter of #(?P<x>\d+) (?P<au>'+LU+r')')),
          ('perimeter',re.compile(r'(?:the |its |their )(?:total )?perimeter(?: of (?P<obj>.+?))? (?:is|was) #(?P<x>\d+) (?P<au>'+LU+r')'))]
SIDE_GIVEN=[re.compile(r'(?:(?P<obj>.+?) (?:is|was|were|are|measures|measured) )?#(?P<x>\d+) (?P<xu>'+LU+r') (?P<d>long|wide|tall|high|in length|in width|in height)'),
            re.compile(OBJ+r'(?:(?:has|had|have|with) )?(?:a |an )(?P<d>length|width|height|base|breadth|diameter|radius) of #(?P<x>\d+) (?P<xu>'+LU+r')'),
            re.compile(r'(?:the |its |their )(?P<d>length|width|height|base|breadth|diameter|radius)(?: of (?P<obj>.+?))? (?:is|was|measures) #(?P<x>\d+) (?P<xu>'+LU+r')')]
SIDE_ASKED=[re.compile(r'how (?P<d>long|wide|tall|high) (?:is|was|are|were) (?P<obj>.+?)'),
            re.compile(r'(?:what is|what was|what will be|find|calculate|determine) (?:the |its )?(?:required )?(?P<d>length|width|height|base|breadth|diameter|radius)(?: of (?P<obj>.+?))?'),
            re.compile(r"(?:what is|what was|find|calculate|determine) (?:the )?(?P<obj>[a-z' -]+?)'s (?P<d>length|width|height|base|diameter|radius)")]
DIM={'long':'length','length':'length','in length':'length','wide':'width','width':'width','breadth':'width','in width':'width',
     'tall':'height','high':'height','height':'height','in height':'height','base':'base','diameter':'diameter','radius':'radius'}
SOLID=r'\b(?:box|cube|room|tank|prism|cuboid|building|house|shed|aquarium|container|crate|closet|bedroom|kitchen|bathroom|garage)\b'
NOT_RECTANGLE=r'\b(?:triangle|triangular|trapezoid|trapezium|rhombus|kite|circle|circular|round|oval|ellipse|pentagon|hexagon|octagon|polygon|sector|semicircle|cylinder|sphere|disc|disk)\b'
PRONOUN={'it','its','this','that','them','they'}

Q_OBJ=re.compile(r'(?:the |this |that |a |an |its |his |her |their |our |my )?(?:[a-z-]+ ){0,2}(?P<head>[a-z-]+)(?: in (?P<qu>'+LU+r'))?')
def _same_object(q,obj,u):
    """'... of the garden' after 'a garden is ...': the question names a word of the thing measured (or no thing);
    'in meters' must be the unit given"""
    m=re.search(r'.* of (.+)$',q)
    if not m or re.fullmatch(r'(?:each|one|every) side',m.group(1)):return True
    mo=Q_OBJ.fullmatch(m.group(1))
    if not mo or (mo.group('qu') and LEN[mo.group('qu')]!=u):return False
    words={_sing(w) for w in re.findall(r'[a-z-]+',obj)}-{'a','an','the','this','that','its','his','her','their','our','my','each'}
    return _sing(mo.group('head')) in words

def _shape_sides(phrase):
    p=' '+phrase+' '
    for w,n in SIDES.items():
        if f' {w} ' in p or f' {w}al ' in p:
            if w=='triangle' and 'equilateral' not in p:return None
            if w not in ('triangle','square') and 'regular' not in p and not re.search(r'\b(?:hexagonal|pentagonal|octagonal)\b',p):return None
            return n
    for w,n in (('hexagonal',6),('pentagonal',5),('octagonal',8)):
        if w in p:return n
    return None

def _geometry(text,nums,sents,sk):
    if len(sk)<2 or len(sk)>4:return None
    q=sk[-1];s=_Spec(text,nums)
    # sentences that only set the scene ('Kim was painting a door.') are left aside
    body=[(x,i) for i,x in enumerate(sk[:-1]) if not _context_ok(x)]
    mc=re.fullmatch(r'(?:if|when) (?P<a>[^,]+), (?P<b>.+)',q)
    if mc:body.append((mc.group('a'),len(sk)-1));q=mc.group('b')
    if not body or len(body)>2:return None
    if len(body)==2:return _other_side(s,body,q,sents)
    x,i=body[0];span=sents[i]
    mq=Q_PA.fullmatch(q)
    if mq:
        for rx in DIMS:
            m=rx.fullmatch(x)
            if m:break
        else:m=None
        if m:
            if LEN[m.group('xu')]!=LEN[m.group('yu')] or (m.groupdict().get('xd') and DIM[m.group('xd')]==DIM[m.group('yd')]):return None
            solid=re.search(SOLID,m.group('obj'))
            if solid and (mq.group('what')=='perimeter' or 'height' in (DIM.get(m.groupdict().get('xd') or ''),DIM.get(m.groupdict().get('yd') or ''))):return None
            if re.search(NOT_RECTANGLE,m.group('obj')):return None
            u=LEN[m.group('xu')]
            if not _same_object(q,m.group('obj'),u):return None
            a=s.bind('side1',int(m.group('x')),unit=u,about='one side');b=s.bind('side2',int(m.group('y')),unit=u,about='the other side')
            if mq.group('what')=='perimeter':
                r=s.qty('perimeter',unit=u,about='the perimeter');s.rel(f'{r} = {a} + {b} + {a} + {b}',*sents[-1]);return s.done(r,u,'perimeter:rectangle')
            r=s.qty('area',unit=f'{u}^2',about='the area');s.rel(f'{r} = {a} * {b}',*sents[-1]);return s.done(r,f'{u}^2','area:rectangle')
        m=SQUARE.fullmatch(x)
        if m:
            k=int(m.group('x') or m.group('x2'));u=LEN[m.group('xu') or m.group('xu2')]
            if not _same_object(q,m.group('obj') or m.group('obj2'),u):return None
            a=s.bind('side',k,unit=u,about='a side')
            if mq.group('what')=='perimeter':
                r=s.qty('perimeter',unit=u,about='the perimeter');s.rel(f'{r} = {a} + {a} + {a} + {a}',*sents[-1]);return s.done(r,u,'perimeter:square')
            r=s.qty('area',unit=f'{u}^2',about='the area');s.rel(f'{r} = {a} * {a}',*sents[-1]);return s.done(r,f'{u}^2','area:square')
        return None
    m=PERI.fullmatch(x)
    if m and Q_SIDE.fullmatch(q):
        n=_shape_sides(m.group('shape'))
        if not n or not _same_object(q,m.group('shape'),LEN[m.group('u')]):return None
        u=LEN[m.group('u')];p=s.bind('perimeter',int(m.group('p')),unit=u,about='the perimeter')
        side=s.qty('side',unit=u,about='each side');s.rel(f"{p} = {' + '.join(side for _ in range(n))}",*span)
        return s.done(side,u,f'side:{n}')
    return _other_side(s,body,q,sents)

def _head(phrase):
    ws=[w for w in re.findall(r"[a-z-]+",phrase) if w not in ('a','an','the','this','that','its','his','her','their','our','my','each','new')]
    return _sing(ws[-1]) if ws else None

def _other_side(s,body,q,sents):
    """one side and the area (or the perimeter) of a rectangle, a parallelogram or a triangle, or a circle's diameter or
    radius, and the other one asked"""
    clauses=[]
    for x,i in body:
        for c in re.split(r',? and |, | with (?=(?:a |an )?(?:total |surface )?(?:area|perimeter|length|width|height|base|diameter|radius) )',x):
            clauses.append((re.sub(r'^(?:if|when) ','',c.strip()),i))
    measured=[];given=[];objs=[]
    for c,i in clauses:
        hit=None
        for what,rx in MEASURED:
            m=rx.fullmatch(c)
            if m:hit=('m',what,m);break
        if not hit:
            for rx in SIDE_GIVEN:
                m=rx.fullmatch(c)
                if m:hit=('g',DIM[m.group('d')],m);break
        if not hit:return None
        kind,what,m=hit
        (measured if kind=='m' else given).append((what,m,i))
        if m.group('obj') and m.group('obj').strip() not in PRONOUN:objs.append(m.group('obj'))
    for rx in SIDE_ASKED:
        mq=rx.fullmatch(q)
        if mq:break
    else:return None
    asked=DIM[mq.group('d')]
    if mq.group('obj') and mq.group('obj').strip() not in PRONOUN:objs.append(mq.group('obj'))
    if len(given)!=1:return None
    known,mk,ki=given[0]
    # one thing: every name of it is a word of the first name ('a rectangle swimming pool' ... 'the pool')
    if objs:
        words={_sing(w) for w in re.findall(r'[a-z-]+',objs[0])}
        if any(_head(o) not in words for o in objs[1:]):return None
    thing=' '+' '.join(objs)+' '
    u=LEN[mk.group('xu')];k=s.bind(known,int(mk.group('x')),unit=u,about='the '+known)
    if {known,asked}=={'diameter','radius'}:
        if measured:return None
        d,r=(k,s.qty('radius',unit=u,about='the radius')) if known=='diameter' else (s.qty('diameter',unit=u,about='the diameter'),k)
        s.rel(f'{d} = {r} + {r}',*sents[ki])
        return s.done(r if asked=='radius' else d,u,'circle:'+asked)
    if len(measured)!=1 or known==asked or 'diameter' in (known,asked) or 'radius' in (known,asked):return None
    what,mm,mi=measured[0]
    if LEN[mm.group('au')]!=u:return None
    pair={known,asked}
    triangle=re.search(r'\btriangle\b',thing);para=re.search(r'\b(?:parallelogram|rhombus)\b',thing)
    if triangle or para:
        if what!='area' or pair!={'base','height'}:return None
    else:
        if re.search(NOT_RECTANGLE,thing) or 'base' in pair:return None
        if 'height' in pair and re.search(SOLID,thing):return None
    r=s.qty(asked,unit=u,about='the '+asked)
    if what=='perimeter':
        p=s.bind('perimeter',int(mm.group('x')),unit=u,about='the perimeter')
        s.rel(f'{p} = {k} + {r} + {k} + {r}',*sents[mi])
        return s.done(r,u,'other_side:perimeter')
    area=s.bind('area',int(mm.group('x')),unit=f'{u}^2',about='the area')
    if triangle:s.rel(f'{area} + {area} = {k} * {r}',*sents[mi])
    else:s.rel(f'{area} = {k} * {r}',*sents[mi])
    return s.done(r,u,'other_side:'+('triangle' if triangle else 'parallelogram' if para else 'rectangle'))

# ----------------------------------------------------------------------------- two unknown numbers
T_SUM=re.compile(r'the (?P<what>sum|difference) (?:of|between) (?:the )?two numbers is #(?P<n>\d+)(?: and (?:their|the) (?P<what2>sum|difference) is #(?P<n2>\d+))?')
T_ONE=re.compile(r'(?:one of the numbers|one of them|one number|the (?P<which>larger|smaller|bigger|greater|lesser) (?:number|one)) is #(?P<n>\d+)')
T_Q=re.compile(r"(?:what is|find|what's) the (?:(?P<other>other)|(?P<which>larger|smaller|bigger|greater|lesser)) (?:number|one)")
BIG=('larger','bigger','greater')

def _two_numbers(text,nums,sents,sk):
    if len(sk) not in (2,3):return None
    sk,back=_restore(sk,nums)
    m=T_SUM.fullmatch(sk[0]);mq=T_Q.fullmatch(sk[-1])
    if not m or not mq:return None
    given={m.group('what'):int(m.group('n'))}
    if m.group('what2'):
        if m.group('what2')==m.group('what'):return None
        given[m.group('what2')]=int(m.group('n2'))
    one=None
    if len(sk)==3:
        mo=T_ONE.fullmatch(sk[1])
        if not mo or len(given)!=1:return None
        one=(mo.group('which'),int(mo.group('n')))
    elif len(given)!=2:return None
    s=_spec(text,nums,back)
    if one and one[0] is None:
        # 'one of the numbers is k': the other one is known only from their sum (with their difference it could be
        # k + d or k - d)
        if set(given)!={'sum'} or not mq.group('other'):return None
        g=s.bind('sum',given['sum'],about='their sum');v=s.bind('one',one[1],about='one of the numbers')
        other=s.qty('other',about='the other number');s.rel(f'{v} + {other} = {g}',sents[0][0],sents[1][1])
        return s.done(other,'','two_numbers:other')
    if mq.group('other'):return None
    big=s.qty('larger',about='the larger number');small=s.qty('smaller',about='the smaller number')
    for what,k in given.items():
        g=s.bind(what,k,about='their '+what)
        s.rel(f'{big} + {small} = {g}' if what=='sum' else f'{big} - {small} = {g}',*sents[0])
    if one:
        known=big if one[0] in BIG else small
        v=s.bind('one',one[1],about='the '+one[0]+' number');s.rel(f'{known} = {v}',*sents[1])
    return s.done(big if mq.group('which') in BIG else small,'','two_numbers')

# ----------------------------------------------------------------------------- together again (least common multiple)
TIME_U={'second':'second','seconds':'second','minute':'minute','minutes':'minute','hour':'hour','hours':'hour','day':'day','days':'day',
        'week':'week','weeks':'week','month':'month','months':'month','year':'year','years':'year'}
EVERY=re.compile(r'\bevery #(?P<k>\d+)(?:st|nd|rd|th)?(?: (?P<u>[a-z]+))?')
CONTAINER=re.compile(r'(?:group|bag|box|pack|package|packet|set|bundle|flock|load|container|row|team|pile|stack|crate|carton|case|batch|herd|bunch|tray|roll)\b')
GROUP_W=r'(?:groups|bags|boxes|packs|packages|packets|sets|bundles|flocks|loads|containers|rows|teams|piles|stacks|crates|cartons|cases|batches|herds|bunches|trays|rolls)'
FUNCTION_W=r'(?:and|or|but|to|for|each|every|while|in|on|at|with|that|which|who|from|of|the|a|an|so|if|when|as)\b'
GROUP=re.compile(r'(?:(?P<item>[a-z][a-z-]*) (?:(?:were|are|was|is|come|comes|came) )?)?(?:in |into )?(?P<g>'+GROUP_W+r') of #(?P<k>\d+)'
                 r'(?: (?!'+FUNCTION_W+r')(?P<item2>[a-z][a-z-]*(?: (?!'+FUNCTION_W+r')[a-z][a-z-]*)?))?')
SAME=re.compile(r'\b(?:same|equal|identical) (?:total )?(?:number|numbers|amount|amounts|quantity|quantities)\b|\bas many\b')
# they happen together now: 'she did both today', 'they just rang together', 'at the same time'
TOGETHER_NOW=re.compile(r"\bat the same time\b|\b(?:both|all three|all|together)\b.*\b(?:today|now|just)\b|\b(?:today|now|just)\b.*\b(?:both|all three|together)\b|\btoday's\b")
Q_LEAST=re.compile(r"(?:what is|what's|find) the (?:smallest|least|minimum|fewest|lowest)(?: possible)?(?: total)? (?:number|amount) of (?P<rest>.+)")

def _together(text,nums,sents,sk):
    if len(sk)<2 or len(sk)>4:return None
    q=sk[-1];body=sk[:-1];data=' '.join(body)
    every=[m for x in body for m in EVERY.finditer(x)]
    if len(every)>=2:return _again(text,nums,sents,sk,q,body,every)
    groups=[m for x in body for m in GROUP.finditer(x)]
    # 'the same number of pens and pencils', not 'the same number of boxes of each'
    same=[m for m in SAME.finditer(data+' '+q)]
    if any(CONTAINER.match(_norm(re.sub(r'^of (?:the )?','',(data+' '+q)[m.end():].strip()))) for m in same):return None
    if len(groups)>=2 and same:return _least(text,nums,sents,sk,q,groups)
    return None

def _leftover(s,nums,text,used,n):
    """the numbers that are not periods or group sizes: 'three lights' (as many as there are periods) is checked
    against them; 'one light ... another' is part of the wording. Anything else: not this form"""
    for k,v in enumerate(nums):
        if k in used or N.optional(v,text):continue
        if v.value==n and v.kind in ('word','digits'):
            c=s.bind(f'how_many{k}',k,about='how many there are');s.rel(f"{c} = {' + '.join('1' for _ in range(n))}",*_sent_of(s.text,v))
        elif v.kind=='word' and v.value==1:s.unused(k,'part of the wording: one of them ('+v.raw+')')
        else:return False
    return True

def _sent_of(text,n):
    from .reader_en import sentences
    return next((a,b) for a,b in sentences(text) if a<=n.start<b)

def _again(text,nums,sents,sk,q,body,every):
    ks=[int(m.group('k')) for m in every]
    if len(ks)>3:return None
    ordinal=all(nums[k].kind=='ordinal' for k in ks)
    if not ordinal and any(nums[k].kind=='ordinal' for k in ks):return None
    if ordinal:
        # 'every 3rd visitor gets a sticker and every 5th visitor gets a balloon': which one is the first to get both
        nouns={_sing(m.group('u') or '') for m in every}-{''}
        if len(nouns)!=1:return None
        noun=nouns.pop()
        mq=re.fullmatch(r'which (?P<n>[a-z]+) will be the (?:first|#(?P<f>\d+))(?: one)? to (?:get|win|receive) (?:both|all three)(?: [a-z ]+)?|'
                        r'how many (?P<n2>[a-z]+) must (?:call|come|visit|arrive|enter) before (?:someone|one|a [a-z]+) (?:gets|wins|receives) both(?: [a-z ]+)?',q)
        if not mq or _sing(mq.group('n') or mq.group('n2'))!=noun:return None
        if mq.group('f') and nums[int(mq.group('f'))].value!=1:return None
        u='';form='lcm:first_both'
        if noun=='day' or noun in TIME_U:return None
    else:
        us={TIME_U.get(m.group('u') or '') for m in every}
        if len(us)!=1 or None in us:return None
        u=us.pop()
        # when they happen together again: the question says 'again' (they were together before), and asks in the unit given
        mq=re.fullmatch(r'(?:.*? )?how many (?P<u>[a-z]+)\b.*',q)
        if not mq or TIME_U.get(mq.group('u'))!=u or not re.search(r'\bagain\b',q):return None
        if not re.search(r'\b(?:same|together|both|all three|all)\b',q):return None
        # 'again' from when they last happened together: the text must say that this is now ('she swam today' alone
        # leaves the day of the next run open)
        if not any(TOGETHER_NOW.search(x) for x in body+[re.sub(r'\bagain\b.*','',q)]):return None
        form='lcm:again'
    s=_Spec(text,nums)
    names=[s.bind(f'every{i+1}',k,unit=u or '1',about='how often one of them happens') for i,k in enumerate(ks)]
    if not _leftover(s,nums,text,set(ks),len(ks)):return None
    expr=names[0]
    for n in names[1:]:expr=f'lcm({expr}, {n})'
    r=s.qty('together',unit=u or '1',integer=True,about='when they happen together again');s.rel(f'{r} = {expr}',*sents[-1])
    return s.done(r,u,form)

def _least(text,nums,sents,sk,q,groups):
    """things that come in groups of 12 and of 18, as many of each: the smallest number of them"""
    if len(groups)>3:return None
    mq=Q_LEAST.fullmatch(q)
    if not mq:return None
    heads=set()
    for m in groups:
        it=m.group('item2') or m.group('item')
        if not it:return None
        heads.add(_sing(it.split()[-1]))
    rest=_norm(mq.group('rest'))
    # the question is about the things themselves ('the smallest number of hot dogs'), not about the boxes or packs
    # they come in
    if CONTAINER.match(rest):return None
    noun=re.match(r"(?:(?!"+FUNCTION_W+r"|she|he|they|it|can|could|will|would|did|does|has|have|had|is|are|was|were)[a-z'-]+ ?)+",rest)
    if not noun or _sing(noun.group().split()[-1]) not in heads:return None
    ks=[int(m.group('k')) for m in groups]
    s=_Spec(text,nums)
    names=[s.bind(f'group{i+1}',k,about='the size of one group') for i,k in enumerate(ks)]
    if not _leftover(s,nums,text,set(ks),len(ks)):return None
    expr=names[0]
    for n in names[1:]:expr=f'lcm({expr}, {n})'
    r=s.qty('least',integer=True,about='the smallest number with as many of each');s.rel(f'{r} = {expr}',*sents[-1])
    return s.done(r,'','lcm:groups')
