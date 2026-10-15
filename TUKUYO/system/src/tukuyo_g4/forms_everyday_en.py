"""generation 4 (round 10): everyday English forms that the readers before it leave unread. No LLM.

Tried after forms_en, reader_en and forms_story_en have no reading (reader.read). Each form is a pattern over the
sentences with every number put as #k (forms_en._skel), looser than forms_story_en's whole-sentence skeletons: the
subject and the thing may be said in many ways, but every number of the text must be bound (or be an optional 1), the
units must agree, and the checker (check.py) verifies the reading on its own.

  convert        How many centimeters are in 7 meters? / A movie lasted 1 hour and 40 minutes. How many minutes ...?
  measure_cmp    Kevin is 152 centimeters tall. His father is 28 centimeters taller. How tall is his father?
                 (a meter and centimeters converted: A tree is 4 meters tall. A pole is 150 centimeters taller ...)
  count_cmp      Owen scored 64 points. Lily scored 17 points fewer than Owen. How many points did Lily score?
  diff           Sara is 8. Her mother is 34 years old. How much older is her mother? / 27 boys and 31 girls: how
                 many fewer boys than girls / sold 125 on Saturday and 98 on Sunday: how many more on Saturday
  total_kinds    11 green apples and 9 red apples: find the total number of apples / packs 45 boxes in the morning
                 and 38 in the afternoon: how many boxes that day
  per_each       One bag contains 9 oranges: how many oranges are in 6 bags / a box weighs 5 kilograms: how many
                 kilograms do 8 such boxes weigh / 3 tons on each trip: in 5 trips / each of 7 vans carries 9
  fraction_of    Out of 40 balloons, one fourth are red / had 50 dollars and spent 2/5 of it / half of them
  rest           200 seats, 163 people are seated: how many seats are free / cut into 12 pieces, 7 were eaten
  spent_left     Mark had 35 dollars. After buying a game, he had 12 dollars left. How much did the game cost?
  times          Ted is 3 times as old as his son. His son is 12 / has 24 dollars, which is twice as much as Max
  unit_price     If 5 pencils cost 75 cents, how much does one pencil cost? / Tickets cost 7 dollars each ...
  two_numbers    Two numbers add up to 50. One of them is 18. / the difference between two numbers is 15 ...
  geometry       a rectangle 9 centimeters long and 4 centimeters wide: area / a square with sides of 7: perimeter
  groups_of      A farmer puts 72 eggs into cartons of 6 / a box holds 6 cans: how many boxes for 30 cans
  clock          A movie started at 2 o'clock and lasted 3 hours. At what time did it end?
  age_then       Ivy is 4 years older than her brother. Her brother is 7. How old will Ivy be in 3 years?
  dozen          bought 6 dozen eggs / bought 2 dozen eggs and used 9
  from_to        The price went up from 15 dollars to 22 dollars. By how many dollars did the price go up?
  need_more      Jonah has $30. A game costs $52. How much more money does Jonah need?

What a form cannot place is left unread: another subject, a thing the question does not ask for, a unit that does not
agree, a share of things counted one by one that is not whole.
"""
from __future__ import annotations
import re
from fractions import Fraction
from . import numbers as N
from .forms_en import _skel,_Spec
from .reader_en import sentences

FORM='tukuyo.g4.forms_everyday_en/1'

# the units these forms read, and the one way to write each
_U={}
for _c,_ws in (('centimeter','centimeter centimeters centimetre centimetres cm'),('meter','meter meters metre metres'),
               ('kilometer','kilometer kilometers kilometre kilometres km'),('millimeter','millimeter millimeters mm'),
               ('mile','mile miles'),('inch','inch inches'),('foot','foot feet'),('yard','yard yards'),
               ('gram','gram grams'),('kilogram','kilogram kilograms kg'),('pound','pound pounds'),('ounce','ounce ounces'),
               ('ton','ton tons'),('liter','liter liters litre litres'),('milliliter','milliliter milliliters millilitre millilitres ml'),
               ('gallon','gallon gallons'),('quart','quart quarts'),('cup','cup cups'),
               ('year','year years'),('month','month months'),('week','week weeks'),('day','day days'),('hour','hour hours'),
               ('minute','minute minutes'),('second','second seconds'),('dollar','dollar dollars'),('cent','cent cents'),
               ('point','point points'),('degree','degree degrees')):
    for _w in _ws.split():_U[_w]=_c
UNITW='(?:'+'|'.join(sorted(map(re.escape,_U),key=len,reverse=True))+')'
def unit(w):return _U.get((w or '').strip())

# conversions the forms make (a known constant, said as the checker reads it)
CONV={('meter','centimeter'):100,('kilometer','meter'):1000,('meter','millimeter'):1000,('centimeter','millimeter'):10,
      ('kilogram','gram'):1000,('liter','milliliter'):1000,('hour','minute'):60,('minute','second'):60,('day','hour'):24,
      ('week','day'):7,('year','month'):12,('foot','inch'):12,('yard','foot'):3,('gallon','quart'):4,('dollar','cent'):100,
      ('year','day'):365}
PLURAL={'foot':'feet','inch':'inches','century':'centuries'}
def _pl(u):return PLURAL.get(u,u+'s')
def _known(s,big,small):
    k=CONV[(big,small)];name=f'{small}s_per_{big}'
    s.qty(name,f'{small}/{big}');s.facts.append({'eq':f'{name} = {k}','known':f"{k} {_pl(small)} in {'an' if big[0] in 'aeiou' else 'a'} {big}"})
    return name

def sing(w):
    w=(w or '').strip()
    for a,b in (('ies','y'),('ches','ch'),('shes','sh'),('xes','x'),('sses','ss'),('oes','o'),('ves','f')):
        if w.endswith(a) and len(w)>len(a)+1:return w[:-len(a)]+b
    if w in ('people','children','men','women','feet','mice','geese','teeth'):
        return {'people':'person','children':'child','men':'man','women':'woman','feet':'foot','mice':'mouse','geese':'goose','teeth':'tooth'}[w]
    return w[:-1] if w.endswith('s') and not w.endswith('ss') and len(w)>2 else w

MEASURES={'centimeter','meter','kilometer','millimeter','mile','inch','foot','yard','gram','kilogram','pound','ounce','ton','liter',
          'milliliter','gallon','quart','cup','year','month','week','day','hour','minute','second','dollar','cent','degree'}
def whole(u):return u.split('/')[0] not in MEASURES

PRON={'he','she','it','they','him','her','them','we','i','you'}
def ent(x):
    """a subject as it is named: lower case, without 'the', 'a', 'an' and a trailing comma"""
    x=re.sub(r"[,;]",'',(x or '').lower()).strip()
    x=re.sub(r'^(?:the|a|an)\s+','',x)
    return x.strip()

def _same(a,b):
    a,b=ent(a),ent(b)
    return bool(a) and a==b and a not in PRON

W=r"[a-z]+(?:'s)?"
ONE=r"(?:one|a|an|each|#\d+)"         # 'One bag contains ...': 'one' is a number (an optional 1) in the skeleton
NP=r"[a-z]+(?: [a-z]+){0,2}"


# a sentence of the story that says nothing of an amount: no number, and none of these words (some, each, more, gave,
# ...). Such a sentence before the first number ('Nell collects baseball cards.') is left out of the pattern; any other
# keeps the text unread by these forms
AMOUNT_WORDS=re.compile(r"\b(?:some|any|all|each|every|more|less|fewer|few|several|many|much|most|rest|remaining|left|leftover|half|"
                        r"equal|equally|share|shared|shares|split|divide|divided|gave|give|gives|given|lost|lose|loses|ate|eat|eats|"
                        r"sold|sell|sells|bought|buy|buys|took|take|takes|used|use|uses|spent|spend|spends|broke|broken|popped|"
                        r"flew|died|added|add|got|get|gets|found|find|won|win|another|again|twice|double|triple|none|nothing|no|"
                        r"not|never|only|except|also|too|both|same|than|instead|extra|missing|lost|away|returned|borrowed|"
                        r"paid|pay|cost|costs|price|change|minus|plus|times|per|total|together|altogether|already|still|yet)\b",re.I)

def _pieces(text,nums):
    """the sentences, with 'If <clause>, <question>?' as two (the clause said, then the question), and the sentences before
    the first number that say nothing of an amount left out. Positions are those of the text, so every span is the text's"""
    out=[]
    for a,b in sentences(text):
        seg=text[a:b]
        m=re.match(r"\s*if\s+",seg,re.I)
        c=re.search(r",\s*(?=(?:how|what|find)\b)",seg,re.I) if m else None
        if m and c and not re.search(r"\b(?:would|could|had been|were to)\b",seg,re.I):
            out.append((a+m.end(),a+c.start()));out.append((a+c.end(),b));continue
        out.append((a,b))
    first=min((n.start for n in nums),default=0)
    keep=[]
    for i,(a,b) in enumerate(out):
        if b<=first and i<len(out)-1 and not AMOUNT_WORDS.search(text[a:b]):continue
        keep.append((a,b))
    return keep


def read(text):
    try:
        nums=N.find(text)
        if not nums:return None
        for sents in (sentences(text),_pieces(text,nums)):
            if not sents:continue
            sk=[_skel(text,a,b,nums) for a,b in sents]
            for f in FORMS:
                r=f(text,nums,sents,sk)
                if r:return r
    except (ArithmeticError,ValueError,KeyError,IndexError,TypeError,AttributeError,re.error):
        return None
    return None


def read_from_to(text):
    """only the form of a change from one amount to another (reader.read gives a text with 'from N ... to M' to no other)"""
    try:
        nums=N.find(text);sents=sentences(text)
        if not sents or not nums:return None
        return _from_to(text,nums,sents,[_skel(text,a,b,nums) for a,b in sents])
    except (ArithmeticError,ValueError,KeyError,IndexError,TypeError,AttributeError,re.error):
        return None


def _k(m,g):return int(m.group(g))

def _done(s,ask,unit_,form):
    r=s.done(ask,unit_,form)
    if r:r['spec']['reader']=FORM+':'+form
    return r

def _n(nums,k):return nums[k].value


# ---- converting a measure ------------------------------------------------------------------------
def _convert(text,nums,sents,sk):
    if len(sk)==1:
        m=re.fullmatch(rf"how many (?P<u2>{UNITW}) (?:are )?(?:there )?in #(?P<a>\d+) (?P<u1>{UNITW})",sk[0]) or \
          re.fullmatch(rf"#(?P<a>\d+) (?P<u1>{UNITW}) (?:is|are|equals) how many (?P<u2>{UNITW})",sk[0])
        if not m:return None
        u1,u2=unit(m['u1']),unit(m['u2'])
        if (u1,u2) not in CONV:return None
        s=_Spec(text,nums);a=s.bind('given',_k(m,'a'),u1);k=_known(s,u1,u2)
        s.qty('converted',u2);s.rel(f'converted = {a} * {k}',*sents[0]);return _done(s,'converted',u2,'convert')
    if len(sk)==2:
        a=re.search(rf"(?:lasted|lasts|is|was|took|takes|measures|measured|weighs|weighed) #(?P<a>\d+) (?P<u1>{UNITW}) and #(?P<b>\d+) (?P<u2>{UNITW})(?: (?:tall|long|high|heavy|old))?$",sk[0])
        q=re.fullmatch(rf"(?:how many (?P<u3>{UNITW}) (?:did|does|is|was) (?:it|that|he|she|the [a-z]+|[a-z]+) (?:last|take|weigh|measure|tall|long)|how (?:tall|long|heavy|high) is [a-z]+(?: [a-z]+)? in (?P<u4>{UNITW}))",sk[1])
        if not (a and q):return None
        u1,u2,u3=unit(a['u1']),unit(a['u2']),unit(q['u3'] or q['u4'])
        if u3!=u2 or (u1,u2) not in CONV:return None
        s=_Spec(text,nums);x=s.bind('big',_k(a,'a'),u1);y=s.bind('small',_k(a,'b'),u2);k=_known(s,u1,u2)
        s.qty('total',u2);s.rel(f'total = {x} * {k} + {y}',*sents[1]);return _done(s,'total',u2,'convert')
    return None


# ---- a measure more or less than another ---------------------------------------------------------
ADJ=r'(?:tall|long|old|high|heavy|deep|wide)'
UP={'taller','older','longer','heavier','higher','more','deeper','wider','later','farther','further'}
DOWN={'shorter','younger','lighter','lower','less','fewer','shallower','narrower','earlier'}
CMP='(?:'+'|'.join(sorted(UP|DOWN))+')'
def _measure_cmp(text,nums,sents,sk):
    if len(sk)!=3:return None
    a=re.fullmatch(rf"(?P<A>.+?) (?:is|was) #(?P<a>\d+) (?P<u>{UNITW})(?: {ADJ})?",sk[0]) or \
      re.fullmatch(rf"(?P<A>.+?) (?:weighs|weighed|measures|measured|took|takes|lasted|lasts) #(?P<a>\d+) (?P<u>{UNITW})",sk[0])
    b=re.fullmatch(rf"(?P<B>.+?) (?:is|was|weighs|weighed|measures|took|takes|lasted|lasts) #(?P<d>\d+) (?P<u2>{UNITW}) (?P<cmp>{CMP})(?: than (?P<ref>.+))?",sk[1])
    if not (a and b):return None
    if b['ref'] and not (_same(b['ref'],a['A']) or ent(b['ref']) in ('him','her','it','them','that')):return None
    if _same(a['A'],b['B']):return None
    q=re.fullmatch(rf"how (?:tall|old|long|heavy|high|deep|wide) (?:is|was) (?P<B2>.+?)(?: in (?P<u3>{UNITW}))?",sk[2]) or \
      re.fullmatch(rf"what is (?:the (?:height|age|weight|length|depth|width) of (?P<B3>.+?)|(?P<B4>.+?)'s (?:height|age|weight|length))(?: in (?P<u3>{UNITW}))?",sk[2]) or \
      re.fullmatch(rf"how many (?P<u3>{UNITW}) (?:tall|long|old|heavy|high) (?:is|was) (?P<B5>.+?)",sk[2]) or \
      re.fullmatch(rf"how many (?P<u3>{UNITW}) (?:does|did) (?P<B6>.+?) (?:weigh|measure)",sk[2])
    if not q:return None
    B2=next(v for k,v in q.groupdict().items() if k.startswith('B') and v)
    if not _same(B2,b['B']):return None
    u,u2=unit(a['u']),unit(b['u2']);u3=unit(q.groupdict().get('u3'))
    sign='+' if b['cmp'] in UP else '-'
    s=_Spec(text,nums)
    if u==u2:
        if u3 and u3!=u:return None
        x=s.bind('first',_k(a,'a'),u);d=s.bind('difference',_k(b,'d'),u)
        s.qty('second',u);s.rel(f'second = {x} {sign} {d}',*sents[2])
        if sign=='-' and _n(nums,_k(a,'a'))<_n(nums,_k(b,'d')):return None
        return _done(s,'second',u,'measure_cmp')
    if (u,u2) in CONV and u3 in (None,u2):
        x=s.bind('first',_k(a,'a'),u);d=s.bind('difference',_k(b,'d'),u2);k=_known(s,u,u2)
        s.qty('second',u2);s.rel(f'second = {x} * {k} {sign} {d}',*sents[2]);return _done(s,'second',u2,'measure_cmp')
    return None


# ---- a count more or fewer than another's --------------------------------------------------------
VERB=r'(?P<v>has|had|have|scored|collected|picked|caught|found|read|made|baked|sold|saved|won|ate|drew|planted|bought|owns|got)'
def _count_cmp(text,nums,sents,sk):
    if len(sk)!=3:return None
    a=re.fullmatch(rf"(?P<A>[a-z]+(?: [a-z]+)?) {VERB} #(?P<a>\d+) (?P<X>{NP})",sk[0])
    if not a or a['A'] in PRON:return None
    X=sing(a['X'].split()[-1])
    b=re.fullmatch(rf"(?P<B>[a-z]+(?:'s [a-z]+| [a-z]+)?) (?P<v>[a-z]+) #(?P<d>\d+)(?: (?P<X2>{NP}))? (?P<cmp>more|fewer|less)(?: (?P<X3>{NP}))? than (?P<ref>.+?)(?: (?:did|does|do|has|had|was|is))?",sk[1])
    if not b or (b['v']!=a['v'] and b['v'] not in ('has','had','have')):return None
    if b['cmp']=='less' and whole(X):return None
    if not (_same(b['ref'],a['A']) or ent(b['ref']) in ('he','she','him','her','they','them') and b['B'].startswith(('his ','her ','their '))):return None
    for xx in (b['X2'],b['X3']):
        if xx and sing(xx.split()[-1])!=X:return None
    q=re.fullmatch(rf"how many (?P<X4>{NP}) (?:did|does|do) (?P<B2>.+?) (?P<v2>[a-z]+)",sk[2]) or \
      re.fullmatch(rf"what is the number of (?P<X4>{NP}) (?P<B2>.+?) (?P<v2>[a-z]+)",sk[2])
    if not q or not _same(q['B2'],b['B']) or sing(q['X4'].split()[-1])!=X:return None
    s=_Spec(text,nums);x=s.bind('first',_k(a,'a'),X);d=s.bind('difference',_k(b,'d'),X)
    sign='+' if b['cmp']=='more' else '-'
    if sign=='-' and _n(nums,_k(a,'a'))<_n(nums,_k(b,'d')):return None
    s.qty('second',X,whole(X));s.rel(f'second = {x} {sign} {d}',*sents[2]);return _done(s,'second',X,'count_cmp')


# ---- how much more, older, fewer ---------------------------------------------------------------------
def _diff(text,nums,sents,sk):
    s=_Spec(text,nums)
    if len(sk)==3:
        # Sara is 8 years old. Her mother is 34 years old. How much older is her mother (than Sara)?
        a=re.fullmatch(rf"(?P<A>.+?) is #(?P<a>\d+)(?: years old)?",sk[0]);b=re.fullmatch(rf"(?P<B>.+?) is #(?P<b>\d+)(?: years old)?",sk[1])
        q=re.fullmatch(rf"how (?:much|many years) (?P<c>older|younger) is (?P<X>.+?)(?: than (?P<Y>.+))?",sk[2])
        if a and b and q and 'years old' in (sk[0]+sk[1]):
            first,second=(a,b) if _same(q['X'],a['A']) else (b,a) if _same(q['X'],b['B']) else (None,None)
            if first is None:return None
            other=b if first is a else a
            if q['Y'] and not _same(q['Y'],(other['A'] if other is a else other['B'])):return None
            hi,lo=(first,other) if q['c']=='older' else (other,first)
            ka,kb=_k(hi,'a' if hi is a else 'b'),_k(lo,'a' if lo is a else 'b')
            if _n(nums,ka)<=_n(nums,kb):return None
            x=s.bind('older_age',ka,'year');y=s.bind('younger_age',kb,'year')
            s.qty('difference','year',True);s.rel(f'difference = {x} - {y}',*sents[2]);return _done(s,'difference','year','diff')
        return None
    if len(sk)==2:
        # There are 27 boys and 31 girls in the choir. How many fewer boys than girls are there?
        a=re.search(rf"#(?P<a>\d+) (?P<X>{W}) and #(?P<b>\d+) (?P<Y>{W})",sk[0])
        q=re.fullmatch(rf"how many (?P<c>more|fewer) (?P<P>{W}) than (?P<Q>{W}) (?:are there|are in [a-z ]+|does [a-z ]+ have|do [a-z ]+ have)",sk[1])
        if a and q and len(nums)==2 and sk[0].startswith(('there are','there were','in ','the ')):
            names={sing(a['X']):_k(a,'a'),sing(a['Y']):_k(a,'b')}
            P,Q=sing(q['P']),sing(q['Q'])
            if set(names)!={P,Q} or P==Q:return None
            hi,lo=(P,Q) if q['c']=='more' else (Q,P)
            if _n(nums,names[hi])<=_n(nums,names[lo]):return None
            x=s.bind('larger',names[hi],hi);y=s.bind('smaller',names[lo],lo)
            if hi!=lo:
                # boys and girls are both counted as children: the difference is a number of them
                s.q['larger']['unit']='1';s.q['smaller']['unit']='1'
            s.qty('difference','1',True);s.rel(f'difference = {x} - {y}',*sents[1]);return _done(s,'difference','1','diff')
        # A shop sold 125 toys on Saturday and 98 toys on Sunday. How many more toys did it sell on Saturday?
        a=re.search(rf"(?P<v>sold|made|baked|picked|collected|read|scored|caught|ran|walked) #(?P<a>\d+) (?P<X>{W}) (?:on|in) (?P<S1>[a-z]+) and #(?P<b>\d+)(?: (?P<X2>{W}))? (?:on|in) (?P<S2>[a-z]+)",sk[0])
        q=re.fullmatch(rf"how many more (?P<X3>{W}) did (?:it|he|she|they|the [a-z]+|[a-z]+) (?P<v2>[a-z]+) (?:on|in) (?P<S3>[a-z]+)(?: than (?:on|in) (?P<S4>[a-z]+))?",sk[1])
        if a and q and len(nums)==2:
            X=sing(a['X'])
            if (a['X2'] and sing(a['X2'])!=X) or sing(q['X3'])!=X:return None
            if q['S3']==a['S1'] and q['S4'] in (None,a['S2']):hi,lo=_k(a,'a'),_k(a,'b')
            elif q['S3']==a['S2'] and q['S4'] in (None,a['S1']):hi,lo=_k(a,'b'),_k(a,'a')
            else:return None
            if _n(nums,hi)<=_n(nums,lo):return None
            x=s.bind('more',hi,X);y=s.bind('less',lo,X)
            s.qty('difference',X,True);s.rel(f'difference = {x} - {y}',*sents[1]);return _done(s,'difference',X,'diff')
    return None


# ---- the total of two kinds of one thing -------------------------------------------------------------
def _total_kinds(text,nums,sents,sk):
    if len(sk)!=2 or len(nums)!=2:return None
    a=re.search(rf"#(?P<a>\d+) (?:[a-z]+ )?(?P<X>{W}) and #(?P<b>\d+) (?:[a-z]+ )?(?P<Y>{W})",sk[0]) or \
      re.search(rf"#(?P<a>\d+) (?P<X>{W}) in the (?:morning|first [a-z]+) and #(?P<b>\d+)(?: (?P<Y>{W}))? in the (?:afternoon|evening|second [a-z]+)",sk[0])
    if not a:return None
    X=sing(a['X']);Y=sing(a['Y']) if a['Y'] else X
    if X!=Y:return None
    q=re.fullmatch(rf"(?:find|what is) the total number of (?P<Z>{W})",sk[1]) or \
      re.fullmatch(rf"how many (?P<Z>{W}) (?:are there|does (?:he|she|it|they) [a-z]+|did (?:he|she|it|they) [a-z]+) (?:altogether|in all|in total|that day|in the [a-z]+)",sk[1])
    if not q or sing(q['Z'])!=X:return None
    s=_Spec(text,nums);x=s.bind('first',_k(a,'a'),X);y=s.bind('second',_k(a,'b'),X)
    s.qty('total',X,whole(X));s.rel(f'total = {x} + {y}',*sents[1]);return _done(s,'total',X,'total_kinds')


# ---- so much in each one ---------------------------------------------------------------------------------
HOLDV=r'(?:contains|has|holds|weighs|carries|costs|uses|needs|is|takes|can carry|can hold)'
def _per_each(text,nums,sents,sk):
    s=_Spec(text,nums)
    if len(sk)==2:
        a=re.fullmatch(rf"{ONE} (?P<G>{W}) {HOLDV} #(?P<a>\d+) (?P<X>{NP})",sk[0]) or \
          re.fullmatch(rf"{ONE} (?P<G>{W}) recipe (?:uses|needs|calls for) #(?P<a>\d+) (?P<X>{NP})",sk[0]) or \
          re.fullmatch(rf"(?:a|an|the|one) (?P<G0>{W}) (?:carries|holds|moves|takes) #(?P<a>\d+) (?P<X>{NP}) (?:on|in|for) each (?P<G>{W})",sk[0])
        if a:
            G=sing(a['G']);X=a['X'];Xh=sing(X.split()[-1])
            if unit(X.split()[0]) and len(X.split())>1:Xh=unit(X.split()[0])       # '3 tons of sand': tons
            elif unit(X):Xh=unit(X)
            q=re.fullmatch(rf"how many (?P<Z>{NP}) (?:are|is) (?:there )?in #(?P<m>\d+) (?P<G2>{W})",sk[1]) or \
              re.fullmatch(rf"how many (?P<Z>{NP}) do #(?P<m>\d+) (?:such )?(?P<G2>{W}) (?:weigh|hold|have|contain|cost|need|use|carry)(?: altogether| in all)?",sk[1]) or \
              re.fullmatch(rf"how many (?P<Z>{NP}) does (?:it|he|she|they) (?:carry|move|take|use|need) in #(?P<m>\d+) (?P<G2>{W})",sk[1]) or \
              re.fullmatch(rf"how many (?P<Z>{NP}) (?:are|is) needed for #(?P<m>\d+) (?P<G2>{W})",sk[1])
            if not q or sing(q['G2'])!=G:return None
            Z=q['Z'];Zh=unit(Z.split()[0]) if unit(Z.split()[0]) else sing(Z.split()[-1])
            if Zh!=Xh:return None
            x=s.bind('each',_k(a,'a'),f'{Xh}/{G}');m=s.bind('count',_k(q,'m'),G)
            s.qty('total',Xh,whole(Xh));s.rel(f'total = {x} * {m}',*sents[1]);return _done(s,'total',Xh,'per_each')
        # Each of 7 vans carries 9 passengers. How many passengers are carried in all?
        a=re.fullmatch(rf"each of #(?P<m>\d+) (?P<G>{W}) (?:carries|holds|has|contains|seats) #(?P<a>\d+) (?P<X>{W})",sk[0])
        q=re.fullmatch(rf"how many (?P<Z>{W}) (?:are carried|are there|are held|do they (?:carry|hold|have)) (?:in all|altogether|in total)",sk[1])
        if a and q and sing(q['Z'])==sing(a['X']):
            X=sing(a['X']);G=sing(a['G'])
            m=s.bind('count',_k(a,'m'),G);x=s.bind('each',_k(a,'a'),f'{X}/{G}')
            s.qty('total',X,True);s.rel(f'total = {x} * {m}',*sents[1]);return _done(s,'total',X,'per_each')
        # Mia reads 15 pages every day. How many pages does she read in a week?
        a=re.fullmatch(rf"(?P<A>[a-z]+) (?P<v>[a-z]+) #(?P<a>\d+) (?P<X>{W}) (?:every|each|a) day",sk[0])
        q=re.fullmatch(rf"how many (?P<Z>{W}) (?:does|will) (?:he|she|they|[a-z]+) (?P<v2>[a-z]+) in a week",sk[1])
        if a and q and sing(q['Z'])==sing(a['X']) and a['v'].rstrip('s')==q['v2'].rstrip('s'):
            X=sing(a['X']);x=s.bind('daily',_k(a,'a'),f'{X}/day');k=_known(s,'week','day')
            s.qty('total',f'{X}/week',True);s.rel(f'total = {x} * {k}',*sents[1]);return _done(s,'total',f'{X}/week','per_each')
    return None


# ---- a fraction of a whole -------------------------------------------------------------------------
def _frac(nums,k):
    v=nums[k].value
    return v if 0<v<1 else None

def _fraction_of(text,nums,sents,sk):
    s=_Spec(text,nums)
    if len(sk)==2:
        # Out of 40 balloons, one fourth are red. How many balloons are red?
        a=re.fullmatch(rf"(?:out of|of) (?:the )?#(?P<w>\d+) (?P<X>{W}),? #(?P<f>\d+) (?:of them )?(?:are|were|is) (?P<st>[a-z]+)",sk[0])
        if a:
            q=re.fullmatch(rf"how many (?:(?P<X2>{W}) (?:are|were) {a['st']}|{a['st']} (?P<X3>{W}) (?:are|were) there)",sk[1])
            f=_frac(nums,_k(a,'f'))
            if q and f and sing(q['X2'] or q['X3'])==sing(a['X']):
                X=sing(a['X']);w=s.bind('whole',_k(a,'w'),X);sh=s.bind('share',_k(a,'f'))
                if whole(X) and (_n(nums,_k(a,'w'))*f).denominator!=1:return None
                s.qty('part',X,whole(X));s.rel(f'part = {w} * {sh}',*sents[1]);return _done(s,'part',X,'fraction_of')
        # Sophie had 50 dollars and spent 2/5 of it. How many dollars did she spend?
        a=re.fullmatch(rf"(?P<A>[a-z]+) had #(?P<w>\d+) (?P<u>{UNITW}) and (?P<v>spent|saved|gave away|used) #(?P<f>\d+) of (?:it|them|that)",sk[0])
        if a:
            q=re.fullmatch(rf"how (?:many (?P<u2>{UNITW})|much(?: money)?) did (?:she|he|they|{a['A']}) (?P<v2>spend|save|give away|use)",sk[1])
            f=_frac(nums,_k(a,'f'))
            if q and f and q['v2'][:3]==a['v'][:3] and (q['u2'] is None or unit(q['u2'])==unit(a['u'])):
                u=unit(a['u']);w=s.bind('whole',_k(a,'w'),u);sh=s.bind('share',_k(a,'f'))
                s.qty('part',u);s.rel(f'part = {w} * {sh}',*sents[1]);return _done(s,'part',u,'fraction_of')
    if len(sk)==3:
        # A class of 32 students went on a trip. Half of them brought a camera. How many students brought a camera?
        a=re.fullmatch(rf"(?:a|the) [a-z]+ of #(?P<w>\d+) (?P<X>{W})(?: [a-z ]+)?",sk[0]) or re.fullmatch(rf"(?:there (?:are|were)|[a-z]+ (?:has|had)) #(?P<w>\d+) (?P<X>{W})(?: [a-z ]+)?",sk[0])
        b=re.fullmatch(rf"#(?P<f>\d+) of them (?P<vp>[a-z]+(?: [a-z]+){{0,3}})",sk[1])
        if a and b:
            q=re.fullmatch(rf"how many (?P<X2>{W}) {re.escape(b['vp'])}",sk[2])
            f=_frac(nums,_k(b,'f'))
            if q and f and sing(q['X2'])==sing(a['X']):
                X=sing(a['X'])
                if whole(X) and (_n(nums,_k(a,'w'))*f).denominator!=1:return None
                w=s.bind('whole',_k(a,'w'),X);sh=s.bind('share',_k(b,'f'))
                s.qty('part',X,whole(X));s.rel(f'part = {w} * {sh}',*sents[2]);return _done(s,'part',X,'fraction_of')
        # Ryan had 64 stickers. He gave half of them to his sister. How many stickers does he have left?
        a=re.fullmatch(rf"(?P<A>[a-z]+) had #(?P<w>\d+) (?P<X>{W})",sk[0])
        b=re.fullmatch(rf"(?:he|she|they|[a-z]+) (?:gave|gave away|ate|used|sold|lost) #(?P<f>\d+) of (?:them|it|those)(?: [a-z ]+)?",sk[1])
        q=re.fullmatch(rf"how many (?P<X2>{W}) (?:does|do) (?:he|she|they|[a-z]+) have (?:left|now)",sk[2])
        if a and b and q and _frac(nums,_k(b,'f')) and sing(q['X2'])==sing(a['X']):
            X=sing(a['X']);f=_frac(nums,_k(b,'f'))
            if whole(X) and (_n(nums,_k(a,'w'))*f).denominator!=1:return None
            w=s.bind('whole',_k(a,'w'),X);sh=s.bind('share',_k(b,'f'))
            s.qty('left',X,whole(X));s.rel(f'left = {w} - {w} * {sh}',*sents[2]);return _done(s,'left',X,'fraction_of')
    return None


# ---- the rest of a whole -------------------------------------------------------------------------
TAKEN={'seated':('person','seat'),'taken':(None,None),'eaten':(None,None),'used':(None,None),'sold':(None,None),'broken':(None,None),
       'filled':(None,None),'occupied':(None,None)}
PEOPLE={'person','people','child','student','guest','kid','passenger','adult'}
def _rest(text,nums,sents,sk):
    if len(sk)!=3:return None
    s=_Spec(text,nums)
    # A theater has 200 seats. 163 people are seated. How many seats are free?
    a=re.fullmatch(rf"(?:a|an|the) (?:[a-z]+ )?[a-z]+ (?:has|had|holds|seats) #(?P<w>\d+) (?P<X>{W})",sk[0]) or \
      re.fullmatch(rf"(?:a|an|the) (?:[a-z]+ )?[a-z]+ (?:was|is) cut into #(?P<w>\d+) (?P<X>{W})",sk[0]) or \
      re.fullmatch(rf"[a-z]+'s (?:[a-z]+ )?[a-z]+ has #(?P<w>\d+) (?P<X>{W})",sk[0])
    if a:
        X=sing(a['X'])
        b=re.fullmatch(rf"#(?P<p>\d+) (?P<Y>{W}) (?:are|were|is|was) (?P<st>seated|taken|eaten|used|sold|broken|filled|occupied)",sk[1]) or \
          re.fullmatch(rf"(?:he|she|they|[a-z]+) (?:has|have|had) (?P<st>read|used|eaten|sold|done|written) #(?P<p>\d+) (?P<Y>{W})",sk[1])
        if not b:return None
        Y=sing(b['Y'])
        if not (Y==X or b['st']=='seated' and X in ('seat','chair','bench') and Y in PEOPLE):return None
        q=re.fullmatch(rf"how many (?P<Z>{W}) (?:are|were) (?:free|empty|left|not {b['st']}|still (?:free|empty))",sk[2]) or \
          re.fullmatch(rf"how many (?P<Z>{W}) (?:does|do) (?:he|she|they|[a-z]+) still have to (?:read|do|write|use)",sk[2])
        if not q or sing(q['Z'])!=X:return None
        w=s.bind('whole',_k(a,'w'),X);p=s.bind('part',_k(b,'p'),X)
        if _n(nums,_k(b,'p'))>_n(nums,_k(a,'w')):return None
        s.qty('rest',X,whole(X));s.rel(f'rest = {w} - {p}',*sents[2]);return _done(s,'rest',X,'rest')
    # A train leaves with 210 passengers. At the next station, 45 people get off. How many passengers are still on the train?
    a=re.fullmatch(rf"(?:a|the) (?P<V>bus|train|boat|ship|plane|van) (?:leaves|left|starts|started|has|had) with #(?P<w>\d+) (?P<X>{W})",sk[0])
    b=re.fullmatch(rf"(?:at the (?:next|first) (?:station|stop),? )?#(?P<p>\d+) (?P<Y>{W}) (?:get|got) off(?: at the (?:next|first) (?:station|stop))?",sk[1])
    if a and b:
        X,Y=sing(a['X']),sing(b['Y'])
        if not (X==Y or X in PEOPLE and Y in PEOPLE):return None
        q=re.fullmatch(rf"how many (?P<Z>{W}) are (?:still )?on the {a['V']}(?: now)?",sk[2])
        if not q or sing(q['Z'])!=X:return None
        w=s.bind('start',_k(a,'w'),'person');p=s.bind('off',_k(b,'p'),'person')
        if _n(nums,_k(b,'p'))>_n(nums,_k(a,'w')):return None
        s.qty('left','person',True);s.rel(f'left = {w} - {p}',*sents[2]);return _done(s,'left','person','rest')
    # A rope is 90 centimeters long. Ben cuts off 35 centimeters. How long is the rope now?
    a=re.fullmatch(rf"(?:a|the) (?P<T>{W}) is #(?P<w>\d+) (?P<u>{UNITW}) long",sk[0])
    b=re.fullmatch(rf"(?:[a-z]+|he|she|they) (?:cuts|cut) off #(?P<p>\d+) (?P<u2>{UNITW})(?: [a-z ]+)?",sk[1])
    q=re.fullmatch(rf"how long is the (?P<T2>{W}) now",sk[2])
    if a and b and q and q['T2']==a['T'] and unit(a['u'])==unit(b['u2']):
        u=unit(a['u']);w=s.bind('length',_k(a,'w'),u);p=s.bind('cut',_k(b,'p'),u)
        if _n(nums,_k(b,'p'))>_n(nums,_k(a,'w')):return None
        s.qty('left',u);s.rel(f'left = {w} - {p}',*sents[2]);return _done(s,'left',u,'rest')
    return None


# ---- what was spent, from what was left ---------------------------------------------------------
def _spent_left(text,nums,sents,sk):
    if len(sk)!=3:return None
    a=re.fullmatch(rf"(?P<A>[a-z]+) had #(?P<w>\d+) (?P<u>dollars|cents)",sk[0])
    b=re.fullmatch(rf"after buying (?:a|an|the) (?P<I>{NP}),? (?:he|she|they|{a['A'] if a else 'xx'}) had #(?P<l>\d+) (?P<u2>dollars|cents) left",sk[1]) if a else None
    q=re.fullmatch(rf"how much did the (?P<I2>{NP}) cost",sk[2])
    if a and b and q and q['I2']==b['I'] and a['u']==b['u2']:
        if _n(nums,_k(b,'l'))>_n(nums,_k(a,'w')):return None
        u=unit(a['u']);s=_Spec(text,nums);w=s.bind('had',_k(a,'w'),u);l=s.bind('left',_k(b,'l'),u)
        s.qty('cost',u);s.rel(f'cost = {w} - {l}',*sents[2]);return _done(s,'cost',u,'spent_left')
    return None


# ---- so many times as much -----------------------------------------------------------------------------
def _times(text,nums,sents,sk):
    s=_Spec(text,nums)
    if len(sk)==3:
        # Ted is 3 times as old as his son. His son is 12. How old is Ted?
        a=re.fullmatch(rf"(?P<A>.+?) is #(?P<k>\d+)(?: times)? as old as (?P<B>.+)",sk[0])
        b=re.fullmatch(rf"(?P<B2>.+?) is #(?P<b>\d+)(?: years old)?",sk[1])
        q=re.fullmatch(rf"how old is (?P<A2>.+)",sk[2])
        if a and b and q and _same(a['B'],b['B2']) and _same(q['A2'],a['A']) and nums[_k(a,'k')].value>1:
            k=s.bind('times',_k(a,'k'));x=s.bind('base_age',_k(b,'b'),'year')
            s.qty('age','year',True);s.rel(f'age = {k} * {x}',*sents[2]);return _done(s,'age','year','times')
        # Zoe has 25 stamps. Her brother has 3 times as many stamps. How many stamps does her brother have?
        a=re.fullmatch(rf"(?P<A>[a-z]+) has #(?P<a>\d+) (?P<X>{W})",sk[0])
        b=re.fullmatch(rf"(?P<B>(?:his|her|their) [a-z]+|[a-z]+) has #(?P<k>\d+)(?: times)? as many(?: (?P<X2>{W}))?(?: as (?P<ref>[a-z]+))?",sk[1])
        q=re.fullmatch(rf"how many (?P<X3>{W}) does (?P<B2>.+?) have",sk[2])
        if a and b and q and _same(q['B2'],b['B']) and (b['ref'] is None or _same(b['ref'],a['A']) or b['ref'] in ('her','him')) \
           and sing(q['X3'])==sing(a['X']) and (b['X2'] is None or sing(b['X2'])==sing(a['X'])):
            X=sing(a['X']);x=s.bind('base',_k(a,'a'),X);k=s.bind('times',_k(b,'k'))
            s.qty('other',X,True);s.rel(f'other = {k} * {x}',*sents[2]);return _done(s,'other',X,'times')
    if len(sk)==2:
        # Leo has 24 dollars, which is twice as much as Max. How much does Max have?
        a=re.fullmatch(rf"(?P<A>[a-z]+) has #(?P<a>\d+) (?P<u>dollars|cents),? which is #(?P<k>\d+)(?: times)? as much as (?P<B>[a-z]+)",sk[0])
        q=re.fullmatch(rf"how much (?:money )?does (?P<B2>[a-z]+) have",sk[1])
        if a and q and a['B']==q['B2'] and nums[_k(a,'k')].value>1:
            u=unit(a['u']);x=s.bind('known',_k(a,'a'),u);k=s.bind('times',_k(a,'k'))
            s.qty('other',u);s.rel(f'other = {x} / {k}',*sents[1]);return _done(s,'other',u,'times')
        # A farmer has 18 cows and twice as many sheep. How many sheep does the farmer have?
        a=re.fullmatch(rf"(?:a|the) (?P<A>[a-z]+) has #(?P<a>\d+) (?P<X>{W}) and #(?P<k>\d+)(?: times)? as many (?P<Y>{W})",sk[0])
        q=re.fullmatch(rf"how many (?P<Y2>{W}) does the (?P<A2>[a-z]+) have",sk[1])
        if a and q and a['A']==q['A2'] and sing(q['Y2'])==sing(a['Y']) and sing(a['Y'])!=sing(a['X']):
            Y=sing(a['Y']);x=s.bind('base',_k(a,'a'),'1');k=s.bind('times',_k(a,'k'))
            s.qty('other','1',True);s.rel(f'other = {k} * {x}',*sents[1]);return _done(s,'other',Y,'times')
    return None


# ---- the price of one, and how many for a sum ---------------------------------------------------------
def _unit_price(text,nums,sents,sk):
    s=_Spec(text,nums)
    if len(sk)==1:
        m=re.fullmatch(rf"if #(?P<n>\d+) (?P<X>{W}) cost #(?P<p>\d+) (?P<u>dollars|cents),? how much does {ONE} (?P<X2>{W}) cost(?: in (?P<u2>dollars|cents))?",sk[0])
        if m and sing(m['X'])==sing(m['X2']) and (m['u2'] is None or m['u2']==m['u']):
            X=sing(m['X']);u=unit(m['u']);n=s.bind('count',_k(m,'n'),X);p=s.bind('price',_k(m,'p'),u)
            for k,x in enumerate(nums):
                if x.value==1 and k not in s.bound:s.unused(k,'the one of "one '+m['X2']+'": the price asked is of one')
            s.qty('each',f'{u}/{X}');s.rel(f'each = {p} / {n}',*sents[0]);return _done(s,'each',f'{u}/{X}','unit_price')
        return None
    if len(sk)==2:
        a=re.fullmatch(rf"(?P<X>{W}) cost #(?P<p>\d+) (?P<u>dollars|cents) each",sk[0])
        q=re.fullmatch(rf"how many (?P<X2>{W}) can (?:you|we|he|she|they|[a-z]+) buy with #(?P<m>\d+) (?P<u2>dollars|cents)",sk[1])
        if a and q and sing(a['X'])==sing(q['X2']) and a['u']==q['u2']:
            X=sing(a['X']);u=unit(a['u'])
            if (_n(nums,_k(q,'m'))/_n(nums,_k(a,'p'))).denominator!=1:return None
            p=s.bind('price',_k(a,'p'),f'{u}/{X}');m=s.bind('money',_k(q,'m'),u)
            s.qty('count',X,True);s.rel(f'count = {m} / {p}',*sents[1]);return _done(s,'count',X,'unit_price')
    return None


# ---- two numbers --------------------------------------------------------------------------------------
def _two_numbers(text,nums,sents,sk):
    if len(sk)!=3:return None
    s=_Spec(text,nums)
    a=re.fullmatch(r"(?:#(?P<two>\d+) numbers add up to|the sum of #(?P<two2>\d+) numbers is) #(?P<s>\d+)",sk[0])
    b=re.fullmatch(r"(?:one|#\d+) (?:of them|number|of the numbers) is #(?P<a>\d+)",sk[1])
    q=re.fullmatch(r"what is the other(?: number)?",sk[2])
    if a and b and q and nums[_k(a,'two') if a['two'] else _k(a,'two2')].value==2:
        s.unused(_k(a,'two') if a['two'] else _k(a,'two2'),'how many numbers there are');t=s.bind('sum',_k(a,'s'));x=s.bind('one',_k(b,'a'))
        s.qty('other');s.rel(f'other = {t} - {x}',*sents[2]);return _done(s,'other','1','two_numbers')
    a=re.fullmatch(r"the difference between #(?P<two>\d+) numbers is #(?P<d>\d+)",sk[0])
    b=re.fullmatch(r"the (?P<w>larger|bigger|greater|smaller) (?:number|one) is #(?P<a>\d+)",sk[1])
    q=re.fullmatch(r"what is the (?P<w2>larger|bigger|greater|smaller) (?:number|one)",sk[2])
    if a and b and q and nums[_k(a,'two')].value==2 and (b['w']=='smaller')!=(q['w2']=='smaller'):
        s.unused(_k(a,'two'),'how many numbers there are');d=s.bind('difference',_k(a,'d'));x=s.bind('given',_k(b,'a'))
        s.qty('other');s.rel(f"other = {x} {'-' if q['w2']=='smaller' else '+'} {d}",*sents[2]);return _done(s,'other','1','two_numbers')
    return None


# ---- area and perimeter -------------------------------------------------------------------------------
def _geometry(text,nums,sents,sk):
    if len(sk)!=2:return None
    s=_Spec(text,nums)
    a=re.fullmatch(rf"(?:a|an|the) (?:[a-z]+ )?(?P<T>{W}) is #(?P<l>\d+) (?P<u>{UNITW}) long and #(?P<w>\d+) (?P<u2>{UNITW}) wide",sk[0])
    q=re.fullmatch(rf"what is (?:its|the) area(?: of the {W})?(?: in square (?P<u3>{UNITW}))?",sk[1])
    if a and q and unit(a['u'])==unit(a['u2']) and (q['u3'] is None or unit(q['u3'])==unit(a['u'])):
        u=unit(a['u']);l=s.bind('length',_k(a,'l'),u);w=s.bind('width',_k(a,'w'),u)
        s.qty('area',f'{u}^2');s.rel(f'area = {l} * {w}',*sents[1]);return _done(s,'area',f'{u}^2','geometry')
    a=re.fullmatch(rf"(?:a|the) square has sides of #(?P<l>\d+) (?P<u>{UNITW})",sk[0]) or re.fullmatch(rf"each side of (?:a|the) square is #(?P<l>\d+) (?P<u>{UNITW})(?: long)?",sk[0])
    q=re.fullmatch(rf"what is (?:its|the) perimeter(?: of the square)?(?: in (?P<u3>{UNITW}))?",sk[1])
    if a and q and (q['u3'] is None or unit(q['u3'])==unit(a['u'])):
        u=unit(a['u']);l=s.bind('side',_k(a,'l'),u);s.qty('sides','1');s.facts.append({'eq':'sides = 4','known':'a square has 4 sides'})
        s.qty('perimeter',u);s.rel(f'perimeter = sides * {l}',*sents[1]);return _done(s,'perimeter',u,'geometry')
    return None


# ---- groups of a size ----------------------------------------------------------------------------------
def _groups_of(text,nums,sents,sk):
    if len(sk)!=2:return None
    s=_Spec(text,nums)
    # A farmer puts 72 eggs into cartons of 6. How many cartons does he fill?
    a=re.fullmatch(rf"(?:a|an|the) [a-z]+ (?:puts|put|packs|packed|places|placed) #(?P<n>\d+) (?P<X>{W}) into (?P<G>{W}) of #(?P<k>\d+)",sk[0])
    q=re.fullmatch(rf"how many (?P<G2>{W}) (?:does|did) (?:he|she|they|it) (?:fill|need|use)",sk[1])
    if a and q and sing(q['G2'])==sing(a['G']):
        X,G=sing(a['X']),sing(a['G'])
        if (_n(nums,_k(a,'n'))/_n(nums,_k(a,'k'))).denominator!=1:return None
        n=s.bind('total',_k(a,'n'),X);k=s.bind('size',_k(a,'k'),f'{X}/{G}')
        s.qty('groups',G,True);s.rel(f'groups = {n} / {k}',*sents[1]);return _done(s,'groups',G,'groups_of')
    # A box holds 6 cans. How many boxes are needed for 30 cans?
    a=re.fullmatch(rf"(?:a|an|one|each) (?P<G>{W}) (?:holds|can hold|takes|fits) #(?P<k>\d+) (?P<X>{W})",sk[0])
    q=re.fullmatch(rf"how many (?P<G2>{W}) are needed (?:for|to hold|to pack) #(?P<n>\d+) (?P<X2>{W})",sk[1])
    if a and q and sing(q['G2'])==sing(a['G']) and sing(q['X2'])==sing(a['X']):
        X,G=sing(a['X']),sing(a['G']);k=s.bind('size',_k(a,'k'),f'{X}/{G}');n=s.bind('total',_k(q,'n'),X)
        s.qty('groups',G,True);s.rel(f'groups = ceil({n} / {k})',*sents[1]);return _done(s,'groups',G,'groups_of')
    return None


# ---- a clock --------------------------------------------------------------------------------------------
def _clock(text,nums,sents,sk):
    if len(sk)!=2:return None
    a=re.fullmatch(r"(?:a|the) [a-z]+(?: [a-z]+)? (?:started|starts|began|begins) at #(?P<h>\d+) o'clock and (?:lasted|lasts) #(?P<d>\d+) hours?",sk[0])
    q=re.fullmatch(r"at what (?:time|hour) (?:did|does|will) it end",sk[1])
    if not (a and q):return None
    h,d=_n(nums,_k(a,'h')),_n(nums,_k(a,'d'))
    if not (1<=h<=12 and h+d<=12):return None
    s=_Spec(text,nums);x=s.bind('start',_k(a,'h'),'hour');y=s.bind('length',_k(a,'d'),'hour')
    s.qty('end','hour',True);s.rel(f'end = {x} + {y}',*sents[1]);return _done(s,'end','hour','clock')


# ---- an age then -------------------------------------------------------------------------------------
def _age_then(text,nums,sents,sk):
    if len(sk)!=3:return None
    a=re.fullmatch(rf"(?P<A>[a-z]+) is #(?P<d>\d+) years (?P<c>older|younger) than (?P<B>(?:his|her|their) [a-z]+|[a-z]+)",sk[0])
    b=re.fullmatch(rf"(?P<B2>(?:his|her|their) [a-z]+|[a-z]+) is #(?P<b>\d+)(?: years old)?",sk[1])
    q=re.fullmatch(rf"how old will (?P<A2>[a-z]+) be in #(?P<n>\d+) years",sk[2])
    if not (a and b and q) or a['B']!=b['B2'] or q['A2']!=a['A']:return None
    s=_Spec(text,nums);d=s.bind('difference',_k(a,'d'),'year');x=s.bind('other_age',_k(b,'b'),'year');n=s.bind('years',_k(q,'n'),'year')
    sign='+' if a['c']=='older' else '-'
    s.qty('age_then','year',True);s.rel(f'age_then = {x} {sign} {d} + {n}',*sents[2]);return _done(s,'age_then','year','age_then')


# ---- a dozen ---------------------------------------------------------------------------------------------
def _dozen(text,nums,sents,sk):
    s=_Spec(text,nums)
    if len(sk)==2:
        a=re.fullmatch(rf"(?P<A>.+?) (?:bought|buys|has|had) #(?P<n>\d+) #(?P<dz>\d+) (?P<X>{W})",sk[0])
        q=re.fullmatch(rf"how many (?P<X2>{W}) did (?:she|he|they|it|[a-z]+) buy",sk[1]) or re.fullmatch(rf"how many (?P<X2>{W}) (?:does|do) (?:she|he|they|it|[a-z]+) have",sk[1])
        if a and q and nums[_k(a,'dz')].raw.lower()=='dozen' and sing(q['X2'])==sing(a['X']):
            X=sing(a['X']);n=s.bind('dozens',_k(a,'n'),'dozen');k=s.bind('per_dozen',_k(a,'dz'),f'{X}/dozen')
            s.qty('total',X,True);s.rel(f'total = {n} * {k}',*sents[1]);return _done(s,'total',X,'dozen')
    return None


# ---- a change from one amount to another -------------------------------------------------------------
UPV=r'(?:went up|rose|increased|grew|climbed)';DOWNV=r'(?:went down|fell|dropped|decreased|shrank)'
def _from_to(text,nums,sents,sk):
    if len(sk)!=2:return None
    a=re.fullmatch(rf"(?P<T>.+?) (?P<v>{UPV}|{DOWNV}) from #(?P<a>\d+) (?P<u>{UNITW}) to #(?P<b>\d+) (?P<u2>{UNITW})",sk[0])
    q=re.fullmatch(rf"by how (?:many (?P<u3>{UNITW})|much) did (?:the [a-z]+|it|her [a-z]+|his [a-z]+) (?P<v2>go up|rise|increase|grow|climb|go down|fall|drop|decrease|shrink)",sk[1])
    if not (a and q) or unit(a['u'])!=unit(a['u2']) or (q['u3'] and unit(q['u3'])!=unit(a['u'])):return None
    up=bool(re.fullmatch(UPV,a['v']));upq=q['v2'] in ('go up','rise','increase','grow','climb')
    if up!=upq:return None
    x,y=_n(nums,_k(a,'a')),_n(nums,_k(a,'b'))
    if (y<=x) if up else (y>=x):return None
    u=unit(a['u']);s=_Spec(text,nums);f=s.bind('from',_k(a,'a'),u);t=s.bind('to',_k(a,'b'),u)
    s.qty('change',u);s.rel(f"change = {t} - {f}" if up else f"change = {f} - {t}",*sents[1]);return _done(s,'change',u,'from_to')


# ---- how much more is needed --------------------------------------------------------------------------
def _need_more(text,nums,sents,sk):
    if len(sk)!=3:return None
    a=re.fullmatch(r"(?P<A>[a-z]+) has #(?P<a>\d+)(?: dollars)?",sk[0])
    b=re.fullmatch(r"(?:a|an|the) (?:[a-z]+ )?[a-z]+ costs #(?P<b>\d+)(?: dollars)?",sk[1])
    q=re.fullmatch(r"how much more(?: money)? does (?P<A2>[a-z]+) need",sk[2])
    if not (a and b and q) or a['A']!=q['A2']:return None
    if not ('$' in text or 'dollar' in text.lower()):return None
    if _n(nums,_k(b,'b'))<=_n(nums,_k(a,'a')):return None
    s=_Spec(text,nums);x=s.bind('has',_k(a,'a'),'dollar');y=s.bind('price',_k(b,'b'),'dollar')
    s.qty('need','dollar');s.rel(f'need = {y} - {x}',*sents[2]);return _done(s,'need','dollar','need_more')


# ---- so much each period, for some periods ------------------------------------------------------------
PERIOD={'day':'day','days':'day','week':'week','weeks':'week','month':'month','months':'month','hour':'hour','hours':'hour','minute':'minute','minutes':'minute','year':'year','years':'year'}
PER=r'(?:day|week|month|hour|minute|year)'
def _rate_time(text,nums,sents,sk):
    if len(sk)!=2:return None
    s=_Spec(text,nums)
    # A car travels 60 miles in one hour. How far does it travel in 5 hours?
    a=re.fullmatch(rf"(?:a|an|the) (?P<T>{W}) (?:travels|goes|moves|drives|flies|runs|walks|swims) #(?P<a>\d+) (?P<u>{UNITW}) (?:in|every|each) (?:{ONE} )?(?P<p>{PER})",sk[0])
    if a:
        q=re.fullmatch(rf"how (?:far|many (?P<u2>{UNITW})) (?:does|will|can) (?:it|the {a['T']}) (?:travel|go|move|drive|fly|run|walk|swim) in #(?P<m>\d+) (?P<p2>{PER}s?)",sk[1])
        if q and PERIOD[q['p2']]==a['p'] and (q['u2'] is None or unit(q['u2'])==unit(a['u'])):
            u=unit(a['u']);p=a['p'];x=s.bind('speed',_k(a,'a'),f'{u}/{p}');m=s.bind('time',_k(q,'m'),p)
            s.qty('distance',u);s.rel(f'distance = {x} * {m}',*sents[1]);return _done(s,'distance',u,'rate_time')
    # Eva puts 3 dollars in her piggy bank each day. How much has she put in after 9 days?
    a=re.fullmatch(rf"(?P<A>[a-z]+) (?P<v>puts|saves|earns|spends|gets|adds) #(?P<a>\d+) (?P<u>dollars|cents)(?: (?:in|into|to) (?:her|his|their|the) [a-z]+(?: [a-z]+)?)? (?:each|every|a|per) (?P<p>{PER})",sk[0])
    if a:
        q=re.fullmatch(rf"how (?:much(?: money)?|many (?P<u2>dollars|cents)) (?:has|will|does|did) (?:she|he|they|{a['A']}) (?:put in|saved?|earned?|spent?|got|get|added?)(?: in)? (?:after|in) #(?P<m>\d+) (?P<p2>{PER}s?)",sk[1])
        if q and PERIOD[q['p2']]==a['p'] and (q['u2'] is None or unit(q['u2'])==unit(a['u'])):
            u=unit(a['u']);p=a['p'];x=s.bind('each',_k(a,'a'),f'{u}/{p}');m=s.bind('time',_k(q,'m'),p)
            s.qty('total',u);s.rel(f'total = {x} * {m}',*sents[1]);return _done(s,'total',u,'rate_time')
    # Noah walks 2 kilometers to school and 2 kilometers back home every day. How many kilometers does he walk in 5 days?
    a=re.fullmatch(rf"(?P<A>[a-z]+) (?P<v>walks|runs|rides|drives|cycles) #(?P<a>\d+) (?P<u>{UNITW}) to (?:the )?[a-z]+ and #(?P<b>\d+) (?P<u2>{UNITW}) back(?: home)? (?:every|each) day",sk[0])
    if a:
        q=re.fullmatch(rf"how (?:many (?P<u3>{UNITW})|far) does (?:he|she|{a['A']}) (?:walk|run|ride|drive|cycle) in #(?P<m>\d+) days",sk[1])
        if q and unit(a['u'])==unit(a['u2']) and (q['u3'] is None or unit(q['u3'])==unit(a['u'])):
            u=unit(a['u']);x=s.bind('there',_k(a,'a'),f'{u}/day');y=s.bind('back',_k(a,'b'),f'{u}/day');m=s.bind('days',_k(q,'m'),'day')
            s.qty('total',u);s.rel(f'total = ({x} + {y}) * {m}',*sents[1]);return _done(s,'total',u,'rate_time')
    return None


# ---- several groups with so much each, of a kind of thing, and a total ----------------------------------
def _groups_weight(text,nums,sents,sk):
    if len(sk)!=3:return None
    # Nina buys 5 bags of rice. Each bag weighs 2 kilograms. What is the total weight of the rice in kilograms?
    a=re.fullmatch(rf"(?P<A>[a-z]+) (?:buys|bought|has|had) #(?P<m>\d+) (?P<G>{W}) of (?P<X>[a-z]+)",sk[0])
    b=re.fullmatch(rf"each (?P<G2>{W}) (?:weighs|holds|contains) #(?P<a>\d+) (?P<u>{UNITW})",sk[1])
    q=re.fullmatch(rf"what is the total (?:weight|amount) of the (?P<X2>[a-z]+)(?: in (?P<u2>{UNITW}))?",sk[2]) or \
      re.fullmatch(rf"how many (?P<u2>{UNITW}) of (?P<X2>[a-z]+) (?:does|did) (?:she|he|they|[a-z]+) (?:buy|have)(?: in all| altogether)?",sk[2])
    if not (a and b and q) or sing(a['G'])!=sing(b['G2']) or q['X2']!=a['X'] or (q['u2'] and unit(q['u2'])!=unit(b['u'])):return None
    G=sing(a['G']);u=unit(b['u']);s=_Spec(text,nums);m=s.bind('groups',_k(a,'m'),G);x=s.bind('each',_k(b,'a'),f'{u}/{G}')
    s.qty('total',u);s.rel(f'total = {m} * {x}',*sents[2]);return _done(s,'total',u,'groups_weight')


# ---- groups and loose ones, groups and some given away -------------------------------------------------
def _groups_more(text,nums,sents,sk):
    s=_Spec(text,nums)
    if len(sk)==2:
        # There are 5 boxes with 9 apples in each box and 7 loose apples. How many apples are there in total?
        a=re.fullmatch(rf"there (?:are|were) #(?P<g>\d+) (?P<G>{W}) with #(?P<n>\d+) (?P<X>{W}) in each (?P<G2>{W}) and #(?P<k>\d+) (?:loose|extra|other|more) (?P<X2>{W})",sk[0])
        q=re.fullmatch(rf"how many (?P<X3>{W}) are there (?:in total|in all|altogether)",sk[1])
        if a and q and sing(a['G'])==sing(a['G2']) and sing(a['X'])==sing(a['X2'])==sing(q['X3']):
            X,G=sing(a['X']),sing(a['G']);g=s.bind('groups',_k(a,'g'),G);n=s.bind('each',_k(a,'n'),f'{X}/{G}');k=s.bind('loose',_k(a,'k'),X)
            s.qty('total',X,True);s.rel(f'total = {g} * {n} + {k}',*sents[1]);return _done(s,'total',X,'groups_more')
    if len(sk)==3:
        # Olivia has 3 boxes of markers with 10 markers in each. She gives away 8 markers. How many markers does she have left?
        a=re.fullmatch(rf"(?P<A>[a-z]+) (?:has|had|bought|buys) #(?P<g>\d+) (?P<G>{W}) of (?P<X>{W}) with #(?P<n>\d+)(?: (?P<X2>{W}))? in each(?: (?P<G2>{W}))?",sk[0])
        b=re.fullmatch(rf"(?:she|he|they|[a-z]+) (?:gives away|gave away|gives|gave|uses|used|loses|lost|sells|sold) #(?P<k>\d+) (?P<X3>{W})(?: [a-z ]+)?",sk[1])
        q=re.fullmatch(rf"how many (?P<X4>{W}) (?:does|do) (?:she|he|they|[a-z]+) have (?:left|now)",sk[2])
        if a and b and q:
            X=sing(a['X']);G=sing(a['G'])
            if any(v and sing(v)!=X for v in (a['X2'],b['X3'],q['X4'])) or (a['G2'] and sing(a['G2'])!=G):return None
            g=s.bind('groups',_k(a,'g'),G);n=s.bind('each',_k(a,'n'),f'{X}/{G}');k=s.bind('given',_k(b,'k'),X)
            if _n(nums,_k(a,'g'))*_n(nums,_k(a,'n'))<_n(nums,_k(b,'k')):return None
            s.qty('left',X,True);s.rel(f'left = {g} * {n} - {k}',*sents[2]);return _done(s,'left',X,'groups_more')
    return None


# ---- the rest of a measure ----------------------------------------------------------------------------------
def _rest_measure(text,nums,sents,sk):
    if len(sk)!=3:return None
    # A pool is filled with 1200 liters of water. 350 liters are drained. How much water is left?
    a=re.fullmatch(rf"(?:a|an|the) (?P<T>{W}) (?:is filled with|holds|has|contains|had) #(?P<w>\d+) (?P<u>{UNITW})(?: of (?P<X>[a-z]+))?",sk[0])
    b=re.fullmatch(rf"#(?P<p>\d+) (?P<u2>{UNITW})(?: of (?P<X2>[a-z]+))? (?:are|were|is|was) (?:drained|used|poured out|removed|taken out|drunk)",sk[1])
    q=re.fullmatch(rf"how (?:much (?P<X3>[a-z]+)|many (?P<u3>{UNITW})(?: of (?P<X4>[a-z]+))?) (?:is|are) left(?: in the (?P<T2>{W}))?",sk[2])
    if not (a and b and q) or unit(a['u'])!=unit(b['u2']) or (q['u3'] and unit(q['u3'])!=unit(a['u'])):return None
    if q['T2'] and q['T2']!=a['T']:return None
    stuff={x for x in (a['X'],b['X2'],q['X3'],q['X4']) if x}
    if len(stuff)>1:return None
    if _n(nums,_k(b,'p'))>_n(nums,_k(a,'w')):return None
    u=unit(a['u']);s=_Spec(text,nums);w=s.bind('start',_k(a,'w'),u);p=s.bind('removed',_k(b,'p'),u)
    s.qty('left',u);s.rel(f'left = {w} - {p}',*sents[2]);return _done(s,'left',u,'rest_measure')


# ---- the others of a whole (boys and girls) -------------------------------------------------------------------
OTHER={'boys':'girls','girls':'boys','men':'women','women':'men','adults':'children','children':'adults'}
def _rest_kind(text,nums,sents,sk):
    if len(sk)!=3:return None
    a=re.fullmatch(rf"there (?:are|were) #(?P<w>\d+) (?P<X>students|children|people|kids|players|members|guests|campers) (?:in|at|on) (?:a|an|the) [a-z]+(?: [a-z]+)?",sk[0])
    b=re.fullmatch(rf"#(?P<p>\d+) of them (?:are|were) (?P<k>boys|girls|men|women|adults|children)",sk[1])
    if not (a and b):return None
    q=re.fullmatch(rf"how many (?P<k2>boys|girls|men|women|adults|children) (?:are|were) (?:there|in the [a-z]+(?: [a-z]+)?)",sk[2])
    if not q or q['k2']!=OTHER.get(b['k']):return None
    if _n(nums,_k(b,'p'))>_n(nums,_k(a,'w')):return None
    s=_Spec(text,nums);w=s.bind('whole',_k(a,'w'),'person');p=s.bind('part',_k(b,'p'),'person')
    s.qty('rest','person',True);s.rel(f'rest = {w} - {p}',*sents[2]);return _done(s,'rest','person','rest_kind')


# ---- younger or older than someone who is so old ---------------------------------------------------------------
def _age_who(text,nums,sents,sk):
    if len(sk)!=2:return None
    a=re.fullmatch(rf"(?P<A>[a-z]+) is #(?P<d>\d+) years (?P<c>older|younger) than (?P<B>(?:his|her|their) [a-z]+|[a-z]+),? who is #(?P<b>\d+)(?: years old)?",sk[0])
    q=re.fullmatch(rf"how old is (?P<A2>[a-z]+)",sk[1])
    if not (a and q) or a['A']!=q['A2']:return None
    if a['c']=='younger' and _n(nums,_k(a,'d'))>=_n(nums,_k(a,'b')):return None
    s=_Spec(text,nums);d=s.bind('difference',_k(a,'d'),'year');x=s.bind('other_age',_k(a,'b'),'year')
    s.qty('age','year',True);s.rel(f"age = {x} {'+' if a['c']=='older' else '-'} {d}",*sents[1]);return _done(s,'age','year','age_who')


# ---- one of a kind took longer than another ----------------------------------------------------------------------
def _another(text,nums,sents,sk):
    if len(sk)!=3:return None
    a=re.fullmatch(rf"(?:a|the|one) (?P<N>{W}) (?:finished|completed|ran|did|read|took) (?:(?:a|the) [a-z]+ )?in #(?P<a>\d+) (?P<u>{UNITW})",sk[0])
    b=re.fullmatch(rf"(?:another|a second|the second|the other|(?:a|the) #\d+) (?P<N2>{W}) took #(?P<d>\d+) (?P<u2>{UNITW}) (?P<c>longer|less|more|shorter)",sk[1])
    q=re.fullmatch(rf"how long did the (?:second|other|#\d+) (?P<N3>{W}) take",sk[2])
    if not (a and b and q) or not (a['N']==b['N2']==q['N3']) or unit(a['u'])!=unit(b['u2']):return None
    u=unit(a['u']);sign='+' if b['c'] in ('longer','more') else '-'
    if sign=='-' and _n(nums,_k(b,'d'))>=_n(nums,_k(a,'a')):return None
    s=_Spec(text,nums);x=s.bind('first',_k(a,'a'),u);d=s.bind('difference',_k(b,'d'),u)
    s.qty('second',u);s.rel(f'second = {x} {sign} {d}',*sents[2]);return _done(s,'second',u,'another')


# ---- bought by weight and paid with a bill -----------------------------------------------------------------------
def _bill_rate(text,nums,sents,sk):
    if len(sk)!=3:return None
    a=re.fullmatch(rf"(?P<A>[a-z]+) (?:bought|buys) #(?P<q>\d+) (?P<u>{UNITW}) of (?P<X>[a-z]+) at #(?P<p>\d+) (?P<m>dollars|cents) (?:per|a|each) (?P<u2>{UNITW})",sk[0])
    b=re.fullmatch(r"(?:she|he|they|[a-z]+) paid with a #(?P<b>\d+)-(?P<m2>dollar|cent) bill",sk[1])
    q=re.fullmatch(r"(?:what was|how much was|how much is) (?:her|his|their|the) change|how much change did (?:she|he|they) get",sk[2])
    if not (a and b and q) or unit(a['u'])!=unit(a['u2']) or unit(a['m'])!=unit(b['m2']):return None
    u,m=unit(a['u']),unit(a['m'])
    if _n(nums,_k(a,'q'))*_n(nums,_k(a,'p'))>_n(nums,_k(b,'b')):return None
    s=_Spec(text,nums);x=s.bind('amount',_k(a,'q'),u);p=s.bind('price',_k(a,'p'),f'{m}/{u}');bb=s.bind('bill',_k(b,'b'),m)
    s.qty('change',m);s.rel(f'change = {bb} - {x} * {p}',*sents[2]);return _done(s,'change',m,'bill_rate')


# ---- forms of the third-party wording (round 10): 'was able to', 'while', 'If ..., how many ...' -------------------------
WHO=r"(?:[a-z]+(?:'s [a-z]+)?|his [a-z]+(?: [a-z]+)?|her [a-z]+(?: [a-z]+)?|their [a-z]+|mr\. [a-z]+|mrs\. [a-z]+|ms\. [a-z]+)"
ABLE=r"(?:was able to |were able to |managed to )?"
def _lemma(v):
    v=v.lower()
    for a,b in (('ied','y'),('ies','y'),('ught','tch'),('ed',''),('es',''),('s','')):
        if v.endswith(a) and len(v)>len(a)+2:return v[:-len(a)]+b
    return v
SAME_ACT={'collect':'gather','gather':'gather','pick':'gather','get':'get','obtain':'get','make':'make','prepare':'make','bake':'make',
          'sell':'sell','sold':'sell','catch':'catch','caught':'catch','ate':'eat','eat':'eat','take':'take','took':'take','hire':'hire',
          'buy':'buy','bought':'buy','find':'find','found':'find','read':'read','plant':'plant','give':'give','gave':'give',
          'travel':'travel','travell':'travel','walk':'walk','run':'run','ran':'run','score':'score','save':'save','donate':'donate'}
def _acts(v):
    """the acts a verb may name ('baked' -> bake -> make; 'collected' -> collect -> gather)"""
    v=v.lower();c={v,_lemma(v)}
    for a,b in (('ied','y'),('ies','y'),('ed','e'),('ed',''),('d',''),('es',''),('s',''),('ing',''),('ing','e')):
        if v.endswith(a) and len(v)>len(a)+2:c.add(v[:-len(a)]+b)
    if len(v)>4 and v.endswith('ed') and v[-3]==v[-4]:c.add(v[:-3])          # 'planned' -> plan
    return {SAME_ACT.get(x,x) for x in c}
def _act(v):return min(_acts(v))
def _same_act(a,b):return bool(_acts(a)&_acts(b))

def _two_sum(text,nums,sents,sk):
    """two people (or one, twice) did so much of one thing: how many did they do in all"""
    if len(nums)!=2 or len(sk)<2:return None
    stm=sk[:-1];q=sk[-1]
    a=b=None
    for x in stm:
        a=re.search(rf"(?P<A>{WHO}) {ABLE}(?P<v>[a-z]+)(?: up)? #(?P<a>\d+) (?:different )?(?P<X>[a-z]+(?: [a-z]+)?)(?: [a-z ,']+?)?,? (?:while|and) (?P<B>{WHO}) {ABLE}(?P<v2>[a-z]+)(?: up)? #(?P<b>\d+)(?: (?:more )?(?P<X2>[a-z]+(?: [a-z]+)?))?(?: [a-z ,']+)?$",x) or a
        # the same one, twice: 'Helen baked 435 chocolate chip cookies yesterday and 139 cookies this morning'
        b=re.fullmatch(rf"(?P<A>{WHO}) (?P<v>[a-z]+) #(?P<a>\d+) (?:[a-z-]+ ){{0,3}}?(?P<X>[a-z]+)(?: (?:of [a-z]+|by [a-z]+|yesterday|today|this [a-z]+|last [a-z]+|in the [a-z]+|on [a-z]+))? and #(?P<b>\d+) (?:[a-z-]+ ){{0,3}}?(?P<X2>[a-z]+)(?: (?:of [a-z]+|by [a-z]+|across [a-z ]+|yesterday|today|this [a-z]+|last [a-z]+|in the [a-z]+|on [a-z]+))?",x) or b
    one=False
    if a and _same_act(a['v'],a['v2']):
        X=sing(a['X'].split()[-1])
        if a['X2'] and sing(a['X2'].split()[-1])!=X and not a['X2'].startswith(('from','in','at','on','to','around','this','that')):return None
    elif b and (sing(b['X'])==sing(b['X2']) or unit(b['X'])==unit(b['X2'])!=None):
        a=b;one=True;X=unit(a['X']) or sing(a['X'])
    else:return None
    m=re.fullmatch(rf"how many (?P<Z>[a-z]+(?: [a-z]+){{0,2}}) (?:did|do|were|was) (?:they|(?P<C>{WHO}) and (?P<D>{WHO})|(?P<E>{WHO}))(?: {ABLE.strip()})?(?: able to)? (?P<v3>[a-z]+)(?: [a-z ']+)?",q) or \
      re.fullmatch(rf"what is the total (?P<Z>distance|number of [a-z]+|weight) (?:that )?(?:they|he|she|(?P<E>{WHO})) (?P<v3>[a-z]+)(?: [a-z ']+)?",q)
    if not m:return None
    Zw=m['Z'].split()[-1]
    if m['Z']=='distance':
        if X not in ('mile','kilometer','meter','foot','yard'):return None
    elif sing(Zw)!=X and unit(Zw)!=X:return None
    if not _same_act(m['v3'],a['v']):return None
    if one:
        if m.groupdict().get('C') or (m['E'] and not (_same(m['E'],a['A']) or ent(m['E'])==ent(a['A']))):return None
    else:
        if m['E'] or (m['C'] and not ({ent(m['C']),ent(m['D'])}=={ent(a['A']),ent(a['B'])})):return None
    if re.search(r'\b(?:each|more than|left|remain|rest|difference|more|fewer|less)\b',q):return None
    s=_Spec(text,nums);x=s.bind('first',_k(a,'a'),X);y=s.bind('second',_k(a,'b'),X)
    s.qty('total',X,whole(X));s.rel(f'total = {x} + {y}',*sents[-1]);return _done(s,'total',X,'two_sum')


def _need(text,nums,sents,sk):
    """so much is needed, so much is had: how much more is needed"""
    if len(nums)!=2 or len(sk)<3:return None
    stm=' || '.join(sk[:-1]);q=sk[-1]
    need=re.search(rf"(?:needs|need|will need|is planning to use|plans to use|requires|require)(?: to (?:use|buy|have))? #(?P<a>\d+) (?P<u>{UNITW}|lbs?\.?)(?: of (?P<M>[a-z]+))?",stm) or \
         re.search(rf"the total needed is #(?P<a>\d+) (?P<u>{UNITW}|lbs?\.?)",stm)
    have=re.search(rf"(?:has|have|already has|already gave (?:him|her|them)|stored) #(?P<b>\d+) (?P<u2>{UNITW}|lbs?\.?)(?: of (?P<M2>[a-z]+))?",stm) or \
         re.search(rf"already has #(?P<b>\d+) (?P<u2>{UNITW}|lbs?\.?)",stm)
    if not (need and have):return None
    # 450 lbs. of sugar needed and 287 lbs. of flour had: not the same stuff
    m1,m2=need.groupdict().get('M'),have.groupdict().get('M2')
    qm=re.search(r"how much (?:more |additional )?([a-z]+)",q)
    named={x.split()[-1] for x in (m1,m2) if x}|({qm.group(1)} if qm and qm.group(1) not in ('more','additional','does','do','will','did') else set())
    if len(named)>1:return None
    u1,u2=unit(need['u'].rstrip('.')) or 'pound',unit(have['u2'].rstrip('.')) or 'pound'
    if u1!=u2:return None
    if not re.fullmatch(r"how (?:much|many (?:[a-z]+ )?[a-z]+) (?:more |additional )?(?:[a-z]+ )?(?:does|do|will|did) (?:he|she|they|[a-z]+) (?:still )?need(?: to (?:buy|add|get))?|how much (?:[a-z]+ )?(?:does|do) (?:he|she|they) still need",q):return None
    if _n(nums,_k(need,'a'))<=_n(nums,_k(have,'b')):return None
    s=_Spec(text,nums);x=s.bind('needed',_k(need,'a'),u1);y=s.bind('had',_k(have,'b'),u1)
    s.qty('more',u1);s.rel(f'more = {x} - {y}',*sents[-1]);return _done(s,'more',u1,'need')


def _each_times(text,nums,sents,sk):
    """so many in each of so many: in all"""
    if len(nums)!=2:return None
    stm=' || '.join(sk[:-1]);q=sk[-1]
    pats=[rf"#(?P<a>\d+) (?P<X>[a-z]+(?: [a-z]+){{0,2}}) (?:in|on|from) each of (?:his |her |their |the )?#(?P<b>\d+) (?P<G>[a-z]+(?: [a-z]+)?)",
          rf"#(?P<b>\d+) (?:different )?(?P<G>[a-z]+(?: [a-z]+)?),? each (?:containing|with|having|holding) #(?P<a>\d+) (?:different )?(?P<X>[a-z]+(?: [a-z]+){{0,3}})",
          rf"each (?P<G>[a-z]+) (?:has|have|contains|holds|is juggling|can hold) #(?P<a>\d+) (?P<X>[a-z]+(?: [a-z]+)?)(?: [a-z ]+)? (?:and|\|\|) there are #(?P<b>\d+) (?P<G2>[a-z]+)",
          rf"there are #(?P<a>\d+) (?P<X>[a-z]+) on a (?P<G>[a-z]+) \|\| you have #(?P<b>\d+) (?P<G2>[a-z]+) of [a-z]+",
          rf"(?P<X>[a-z]+(?: [a-z-]+)?) can be purchased in (?P<G>[a-z]+) of #(?P<a>\d+) \|\| [a-z]+ buys #(?P<b>\d+) (?P<G2>[a-z]+)",
          rf"(?:make|made|bought|buy|have|has) #(?P<b>\d+) (?P<G>[a-z]+)(?: of [a-z]+)? and each (?P<G2>[a-z]+) (?:can )?(?:fill|fills|hold|holds|has|have|contains|serve|serves) #(?P<a>\d+) (?P<X>[a-z]+)"]
    m=None
    for pt in pats:
        m=re.search(pt,stm)
        if m:break
    if not m:return None
    gd=m.groupdict();G=sing(gd['G'].split()[-1])
    if gd.get('G2') and sing(gd['G2'])!=G:return None
    X=sing(gd['X'].split()[-1])
    qm=re.fullmatch(rf"how many (?:different )?(?P<Z>[a-z]+(?: [a-z]+){{0,3}}) (?:does|do|did|are|will|can|were)(?: [a-z' ]+)?",q) or re.fullmatch(rf"how many (?P<Z>[a-z]+(?: [a-z]+){{0,3}}) (?:are|were) (?:there )?(?:in all|in total|altogether|needed|harvested)(?: [a-z ]+)?",q)
    if not qm:return None
    Z=qm['Z'].split();Zh=sing(Z[-1]) if Z[-1] not in ('of',) else None
    if Zh!=X and not (len(Z)>=3 and Z[1]=='of' and sing(Z[-1])==X) and not (sing(Z[0])==X):return None
    if re.search(r'\b(?:left|remain|more|fewer|less|each|per|difference|share|shared|equally)\b',q.replace('each day','')):return None
    s=_Spec(text,nums);a=s.bind('each',_k(m,'a'),f'{X}/{G}');b=s.bind('groups',_k(m,'b'),G)
    s.qty('total',X,whole(X));s.rel(f'total = {a} * {b}',*sents[-1]);return _done(s,'total',X,'each_times')


def _into_groups(text,nums,sents,sk):
    """so many put in groups of so many: how many groups (whole only)"""
    if len(nums)!=2:return None
    stm=' || '.join(sk[:-1]);q=sk[-1]
    tot=re.search(rf"(?:has|had|bought|buys|prepared|made|gathered all|collected|place|placed) #(?P<a>\d+) (?:[a-z-]+ ){{0,3}}?(?P<X>[a-z]+)",stm)
    per=re.search(rf"(?:boxes|bags|packets|bottles|bracelets|shelves|cans|jars) which can (?:contain|hold) #(?P<b>\d+) (?P<X2>[a-z]+)|#(?P<b2>\d+) (?:pieces of (?:this |the )?)?(?P<X3>[a-z]+) (?:is|are) in each (?P<G2>[a-z]+)|every (?P<G3>[a-z]+) (?:can carry|can hold|holds|needs to contain)(?: a maximum of)? #(?P<b3>\d+) (?P<X4>[a-z]+(?: [a-z]+)?)",stm)
    if not (tot and per):return None
    k='b' if per['b'] else 'b2' if per['b2'] else 'b3'
    X=sing(tot['X']);Xp=sing((per['X2'] or per['X3'] or per['X4']).split()[-1])
    if Xp not in (X,'piece','stone') and not (Xp=='seed' and X=='seedling'):return None
    qm=re.fullmatch(rf"how many (?P<G>[a-z]+)(?: of [a-z ]+)? (?:will|do|does|did|are|were) (?:she|he|they|there)?\s*(?:use|need|be|be filled|filled|have)?(?: [a-z ]+)?",q)
    if not qm:return None
    G=sing(qm['G'])
    if per['G2'] and sing(per['G2'])!=G or per['G3'] and sing(per['G3'])!=G:return None
    if re.search(r'\b(?:left|remain|more|not full|rest)\b',q):return None
    a,b=_n(nums,_k(tot,'a')),_n(nums,_k(per,k))
    if (a/b).denominator!=1:return None
    s=_Spec(text,nums);x=s.bind('total',_k(tot,'a'),X);y=s.bind('size',_k(per,k),f'{X}/{G}')
    s.qty('groups',G,True);s.rel(f'groups = {x} / {y}',*sents[-1]);return _done(s,'groups',G,'into_groups')


def _start_now(text,nums,sents,sk):
    """had so many at first, so many now (or left): how many came or went"""
    if len(nums)!=2 or len(sk)<3:return None
    stm=' || '.join(sk[:-1]);q=sk[-1]
    a=re.search(rf"(?P<S>[a-z]+)? ?(?:initially had|originally had|originally has|had|got a box of|had a box of) #(?P<a>\d+) (?P<X>[a-z]+)",stm)
    b=re.search(rf"(?P<S2>\b(?:he|she|they|[a-z]+)) (?:now has|now had|only had|has|had|was left with(?: her| his)?(?: [a-z]+)?|and now has) #(?P<b>\d+)(?: (?P<X2>[a-z]+))? ?(?:left|now|in all)?",stm[a.end():] if a else '')
    if not (a and b):return None
    # the later amount is the same one's: a pronoun, the same name, or a clause of the same sentence ('... and now has')
    subj=ent(a['S']) if a['S'] else ''
    s2=b['S2']
    if s2 not in ('he','she','they','now','and') and s2!=subj:return None
    if not re.search(r'\b(?:now|left|only|originally|initially)\b',stm):return None
    first,last=_n(nums,_k(a,'a')),None
    # positions: b was searched after a, its group index is in the sliced string
    kb=int(b.group('b'));last=nums[kb].value
    X=sing(a['X'])
    if b['X2'] and sing(b['X2']) not in (X,'piece'):return None
    up=re.fullmatch(rf"how many (?:[a-z]+ )?(?P<Z>[a-z]+)(?: of [a-z]+)? did (?:he|she|they|[a-z]+) (?:receive|get|find|gain|collect|buy)(?: [a-z ']+)?",q)
    down=re.fullmatch(rf"how many (?:[a-z]+ )?(?P<Z>[a-z]+)?(?: of [a-z]+)? ?(?:did (?:he|she|they|[a-z]+) (?:send away|give away|give|lose|use|eat|sell)|had been (?:lost|given away|lost or given away|used|eaten|sold))(?: [a-z ']+)?",q)
    if up and last>first and (up['Z'] is None or sing(up['Z']) in (X,'piece')):
        s=_Spec(text,nums);x=s.bind('before',_k(a,'a'),X);y=s.bind('after',kb,X)
        s.qty('gained',X,True);s.rel(f'gained = {y} - {x}',*sents[-1]);return _done(s,'gained',X,'start_now')
    if down and last<first and (down['Z'] is None or sing(down['Z']) in (X,'piece')):
        s=_Spec(text,nums);x=s.bind('before',_k(a,'a'),X);y=s.bind('after',kb,X)
        s.qty('gone',X,True);s.rel(f'gone = {x} - {y}',*sents[-1]);return _done(s,'gone',X,'start_now')
    return None


def _price_cut(text,nums,sents,sk):
    """a price and a discount (or what was paid): how much was spent or saved"""
    if len(nums)!=2 or '$' not in text:return None
    stm=' || '.join(sk[:-1]);q=sk[-1]
    a=re.search(r"(?:originally cost|initial price of [a-z ]+ is|original price of [a-z ]+ is|regular price of [a-z ]+ is) \$#(?P<a>\d+)",stm)
    b=re.search(r"(?:get|got) a \$#(?P<b>\d+) discount",stm);c=re.search(r"(?:got it for|bought it for|paid) \$#(?P<b>\d+)",stm)
    if not a or not (b or c):return None
    if b and re.fullmatch(r"how much did (?:he|she|they) (?:actually )?(?:spend|pay)(?: [a-z ']+)?",q):
        if _n(nums,_k(b,'b'))>=_n(nums,_k(a,'a')):return None
        s=_Spec(text,nums);x=s.bind('price',_k(a,'a'),'dollar');y=s.bind('discount',_k(b,'b'),'dollar')
        s.qty('paid','dollar');s.rel(f'paid = {x} - {y}',*sents[-1]);return _done(s,'paid','dollar','price_cut')
    if c and re.fullmatch(r"how much (?:money )?(?:was|were|did) (?:he|she|they) (?:able to )?save(?: [a-z ']+)?",q):
        if _n(nums,_k(c,'b'))>=_n(nums,_k(a,'a')):return None
        s=_Spec(text,nums);x=s.bind('price',_k(a,'a'),'dollar');y=s.bind('paid',_k(c,'b'),'dollar')
        s.qty('saved','dollar');s.rel(f'saved = {x} - {y}',*sents[-1]);return _done(s,'saved','dollar','price_cut')
    return None


def _budget_left(text,nums,sents,sk):
    if len(nums)!=2 or '$' not in text:return None
    stm=' || '.join(sk[:-1]);q=sk[-1]
    a=re.search(r"(?:having|with|had|has) \$#(?P<a>\d+)(?: for (?:his|her|their) budget)?",stm)
    b=re.search(r"(?:bought|buys|spent|paid)(?: [a-z' ]+?)? (?:for )?\$#(?P<b>\d+)",stm[a.end():] if a else '')
    if not (a and b) or not re.fullmatch(r"how much (?:money )?(?:does|did|will) (?:he|she|they|[a-z]+) have left(?: [a-z ']+)?",q):return None
    kb=int(b.group('b'))
    if nums[kb].value>=_n(nums,_k(a,'a')):return None
    s=_Spec(text,nums);x=s.bind('budget',_k(a,'a'),'dollar');y=s.bind('spent',kb,'dollar')
    s.qty('left','dollar');s.rel(f'left = {x} - {y}',*sents[-1]);return _done(s,'left','dollar','budget_left')


def _rest_colour(text,nums,sents,sk):
    """so many in all, so many of one kind and the rest of another: how many of the other"""
    if len(nums)!=2 or len(sk)!=3:return None
    a=re.fullmatch(r"there (?:were|are) #(?P<a>\d+) (?P<X>[a-z]+(?: of [a-z]+)?) in (?:a|the) [a-z]+",sk[0])
    b=re.fullmatch(r"#(?P<b>\d+)(?: (?:pieces|of them))? (?:were|are) (?P<c1>[a-z]+) and the rest (?:were|are) (?P<c2>[a-z]+)",sk[1])
    q=re.fullmatch(r"how many (?:(?P<Z>[a-z]+) )?(?:were|are) (?P<c3>[a-z]+)",sk[2])
    if not (a and b and q) or q['c3']!=b['c2']:return None
    if _n(nums,_k(b,'b'))>_n(nums,_k(a,'a')):return None
    X=sing(a['X'].split()[0]);s=_Spec(text,nums);x=s.bind('total',_k(a,'a'),X);y=s.bind('first_kind',_k(b,'b'),X)
    s.qty('rest',X,True);s.rel(f'rest = {x} - {y}',*sents[-1]);return _done(s,'rest',X,'rest_colour')


def _change_cents(text,nums,sents,sk):
    """bought for so many cents, paid with a bill of so many dollars: the change in cents"""
    if len(nums)!=2 or len(sk)!=3:return None
    a=re.fullmatch(r"(?P<A>[a-z]+) bought (?:a|an) [a-z]+(?: [a-z]+)? for #(?P<a>\d+) cents",sk[0])
    b=re.fullmatch(r"(?:he|she|they|[a-z]+) paid with a #(?P<b>\d+)-dollar bill",sk[1])
    q=re.fullmatch(r"how much change (?:will|did|does) (?:he|she|they|[a-z]+) get",sk[2])
    if not (a and b and q):return None
    if _n(nums,_k(a,'a'))>=_n(nums,_k(b,'b'))*100:return None
    s=_Spec(text,nums);x=s.bind('price',_k(a,'a'),'cent');y=s.bind('bill',_k(b,'b'),'dollar');k=_known(s,'dollar','cent')
    s.qty('change','cent');s.rel(f'change = {y} * {k} - {x}',*sents[-1]);return _done(s,'change','cent','change_cents')


FORMS=(_convert,_measure_cmp,_count_cmp,_diff,_total_kinds,_per_each,_fraction_of,_rest,_spent_left,_times,_unit_price,_two_numbers,
       _geometry,_groups_of,_clock,_age_then,_dozen,_from_to,_need_more,_rate_time,_groups_weight,_groups_more,_rest_measure,_rest_kind,
       _age_who,_another,_bill_rate,_two_sum,_need,_each_times,_into_groups,_start_now,_price_cut,_budget_left,_rest_colour,_change_cents)
