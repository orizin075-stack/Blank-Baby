"""generation 4: everyday English story forms the story reader (reader_en) leaves unread (v1022.8.0). No LLM.

Tried only after reader_en has no reading. Each form is an exact pattern over the sentences with every number put as
#k (forms_en._skel), and writes its reading in the formal problem language, which the checker verifies on its own
(every number bound or declared unused, units that agree, one answer):

  what is left of groups     3 packs with 5 pieces in each; she chews 4: how many are left
  the rest of a whole        40 seats, 26 are taken: how many are empty; 25 children, 13 are girls: how many are boys;
                             120 students, 45 of them take the bus: how many do not
  several taken away         8 slices; Mia eats 3 and Leo eats 2 / spent 7 dollars on a book and 4 on a snack
  so much each day           ran 3 kilometers every morning for 5 days; grew 3 centimeters each week for 4 weeks
  one of a pack              a pack of 6 juice boxes costs 9 dollars: how much does one cost
  age                        is 11 years old: how old in 6 years / 6 years ago; her sister is 4 years older
  a share of a whole         half / a quarter / one third of them; it is one third full
  what was gained            had 7, won some more and now has 16: how many did he win
  groups of                  64 apples in boxes of 8 / put them into bags of 6: how many boxes
  average speed              drove 150 kilometers in 3 hours: what was the average speed in kilometers per hour
  things bought at a price   3 pens at 2 dollars each and 2 erasers at 1 dollar each
  change from a bill         a hat for 15 dollars and a scarf for 12 dollars; paid with a 50-dollar bill
  two amounts together       picked 23 and her mother picked 31; 15 pages on Monday and 22 on Tuesday
  how many more              has 24 cows and 17 sheep: how many more cows than sheep; 12 points in the first game and 9
                             in the second: how many more in the first
  a change of a measure      the temperature was 18 degrees and rose by 7 degrees
  kinds of one thing         8 red cars and 6 blue cars: how many cars
  a clock                    starts at 3 o'clock and lasts 2 hours: at what hour does it end (within the 12 hours)
  holds                      a water bottle holds 500 milliliters: how many milliliters do 3 bottles hold

Anything else is left unread.
"""
from __future__ import annotations
import re
from fractions import Fraction
from . import numbers as N
from .forms_en import _skel,_Spec
from .reader_en import sentences

FORM='tukuyo.g4.forms_story_en/1'
W=r"[a-z]+(?:'s)?"
NAMEW=r"(?:mr\. |mrs\. |ms\. |dr\. )?[a-z]+"
PRON=r'(?:he|she|they|it|we|i|you)'
SUBJ=rf"(?:(?:a|an|the) [a-z]+(?: [a-z]+)?|{NAMEW}|{PRON})"


MEASURES={'liter','milliliter','kilogram','gram','meter','centimeter','kilometer','mile','foot','feet','inch','yard','hour','minute','second',
          'dollar','cent','degree','pound','ounce','gallon','cup','day','week','month','year'}
def whole(u):
    """things counted one by one (marbles, people): a share of them must be whole ('a third of 40 marbles' is not read)"""
    return u.split('/')[0] not in MEASURES


def sing(w):
    w=w.strip()
    for a,b in (('ies','y'),('ches','ch'),('shes','sh'),('xes','x'),('sses','ss'),('oes','o')):
        if w.endswith(a):return w[:-len(a)]+b
    return w[:-1] if w.endswith('s') and not w.endswith('ss') else w


def read(text):
    try:
        nums=N.find(text);sents=sentences(text)
        if not sents or not nums:return None
        sk=[_skel(text,a,b,nums) for a,b in sents]
        for f in FORMS:
            r=f(text,nums,sents,sk)
            if r:return r
    except (ArithmeticError,ValueError,KeyError,IndexError,TypeError,AttributeError,re.error):
        return None
    return None


def _k(m,g):return int(m.group(g))


def _done(s,ask,unit,form):
    r=s.done(ask,unit,form)
    if r:r['spec']['reader']=FORM+':'+form
    return r


# ---- what is left of groups ------------------------------------------------------------
def _groups_left(text,nums,sents,sk):
    if len(sk)!=3:return None
    a=re.fullmatch(rf"{NAMEW} (?:has|had|have|bought|buys) #(?P<g>\d+) (?P<G>{W}) of (?P<what>[a-z ]+?) with #(?P<n>\d+) (?P<I>{W}) in each (?P<G2>{W})",sk[0])
    b=re.fullmatch(rf"(?:{PRON}|{NAMEW}) (?:eats|ate|chews|chewed|uses|used|gives away|gave away|loses|lost|sells|sold) #(?P<k>\d+) (?P<I2>{W})(?: [a-z ]+)?",sk[1])
    q=re.fullmatch(rf"how many (?P<I3>{W})(?: of [a-z ]+)? (?:are|is|does {W} have|do {W} have) left",sk[2])
    if not (a and b and q) or not (sing(a['I'])==sing(b['I2'])==sing(q['I3'])) or sing(a['G'])!=sing(a['G2']):return None
    s=_Spec(text,nums);u=sing(a['I']);gu=sing(a['G'])
    g=s.bind('groups',_k(a,'g'),gu);n=s.bind('each',_k(a,'n'),f'{u}/{gu}');k=s.bind('gone',_k(b,'k'),u)
    s.qty('left',u,True);s.rel(f'left = {g} * {n} - {k}',*sents[2]);return _done(s,'left',u,'groups_left')


# ---- the rest of a whole -----------------------------------------------------------------
OPP={('taken','empty'),('taken','free'),('taken','available'),('occupied','empty'),('occupied','free'),('filled','empty'),('full','empty'),
     ('used','unused'),('sold','unsold'),('broken','unbroken'),('girls','boys'),('boys','girls'),('men','women'),('women','men'),
     ('adults','children'),('children','adults'),('red','not red'),('open','closed'),('closed','open'),('on','off'),('off','on')}
def _rest(text,nums,sents,sk):
    if len(sk)!=3:return None
    a=re.fullmatch(rf"(?:(?:a|an|the) [a-z]+(?: [a-z]+)? (?:has|had|holds|seats)|there (?:are|were)) #(?P<w>\d+) (?P<X>{W})(?: (?:at|in|on) (?:a|an|the) [a-z]+(?: [a-z]+)?)?",sk[0])
    if not a:return None
    X=sing(a['X'])
    b=re.fullmatch(rf"#(?P<p>\d+)(?: (?P<X2>{W}))?(?: of them)? (?:are|were|is) (?P<st>[a-z]+)",sk[1])
    c=re.fullmatch(rf"#(?P<p>\d+)(?: (?P<X2>{W}))? of them (?P<vp>[a-z]+(?: [a-z]+){{0,3}})",sk[1]) or re.fullmatch(rf"#(?P<p>\d+) (?P<X2>{W}) (?P<vp>[a-z]+(?: [a-z]+){{0,3}})",sk[1])
    q=re.fullmatch(rf"how many(?: (?P<X3>{W}))? (?:are|were) (?P<st>[a-z]+(?: [a-z]+)?)",sk[2]) or \
      re.fullmatch(rf"how many(?: (?P<X3>{W}))? (?:do|did) not (?P<vp>[a-z]+(?: [a-z]+){{0,3}})",sk[2])
    if not q:return None
    if q.groupdict().get('X3') and sing(q['X3'])!=X and (q['X3'],) and not (b and b['st']==q['X3']):
        # 'How many are boys?' has no noun; 'How many seats are empty?' names the whole
        if sing(q['X3'])!=X:return None
    ok=False
    if b and 'st' in q.groupdict() and q['st']:
        if (b['X2'] is None or sing(b['X2'])==X) and ((b['st'],q['st']) in OPP or q['st']=='not '+b['st']):ok=True
    if not ok and c and 'vp' in q.groupdict() and q['vp'] and (c['X2'] is None or sing(c['X2'])==X) and c['vp']==q['vp']:ok=True
    if not ok:return None
    m=b if (b and 'st' in q.groupdict() and q['st']) else c
    s=_Spec(text,nums);w=s.bind('whole',_k(a,'w'),X);p=s.bind('part',_k(m,'p'),X)
    s.qty('rest',X,True);s.rel(f'rest = {w} - {p}',*sents[2]);return _done(s,'rest',X,'rest')


# ---- several taken away ------------------------------------------------------------------
TAKE=r'(?:eats|ate|takes|took|uses|used|drinks|drank|gives away|gave away|sells|sold|spends|spent|loses|lost)'
def _several_away(text,nums,sents,sk):
    if len(sk)!=3:return None
    a=re.fullmatch(rf"(?:(?:a|an|the) [a-z]+(?: [a-z]+)? (?:is|was) cut into|{NAMEW} (?:has|had|have|baked|bakes|made|makes|bought|buys|picked|picks|collected)|there (?:are|were)) #(?P<n>\d+) (?P<X>{W})(?: [a-z ]+)?",sk[0])
    if not a:return None
    X=sing(a['X'])
    b=re.fullmatch(rf"(?:{NAMEW}|{PRON}) {TAKE} #(?P<x>\d+)(?: (?P<X1>{W}))?(?: (?:on|for) (?:a|an|the) [a-z]+)?(?:,)? and (?:(?:{NAMEW}|{PRON}) {TAKE} )?#(?P<y>\d+)(?: (?P<X2>{W}))?(?: (?:on|for) (?:a|an|the) [a-z]+)?",sk[1])
    q=re.fullmatch(rf"how (?:many (?P<X3>{W})|much(?: money)?) (?:are|is|does {W} have|do {W} have) left",sk[2])
    if not (b and q):return None
    for g in ('X1','X2'):
        if b[g] and sing(b[g])!=X:return None
    if q['X3'] and sing(q['X3'])!=X:return None
    if not q['X3'] and X!='dollar':return None
    s=_Spec(text,nums);n=s.bind('start',_k(a,'n'),X);x=s.bind('first',_k(b,'x'),X);y=s.bind('second',_k(b,'y'),X)
    s.qty('left',X,X!='dollar');s.rel(f'left = {n} - {x} - {y}',*sents[2]);return _done(s,'left',X,'several_away')


# ---- so much each day ----------------------------------------------------------------------
PERIOD={'day':'day','days':'day','morning':'day','mornings':'day','night':'day','evening':'day','week':'week','weeks':'week','month':'month','months':'month','year':'year','years':'year'}
def _each_period(text,nums,sents,sk):
    if len(sk) not in (2,3):return None
    i=len(sk)-2
    m=re.fullmatch(rf"(?:{NAMEW}|{PRON}) (?P<v>[a-z]+) #(?P<r>\d+) (?P<X>{W})(?: [a-z]+)? (?:every|each|a|per) (?P<p>day|morning|night|evening|week|month|year) for #(?P<n>\d+) (?P<P>days|weeks|months|years)",sk[i])
    if not m or PERIOD[m['p']]!=PERIOD[m['P']]:return None
    X=sing(m['X']);P=PERIOD[m['p']]
    if len(sk)==2:
        q=re.fullmatch(rf"how (?:many (?P<X3>{W})|much(?: money)?|far) (?:did|does|will|has|had) (?:{PRON}|{NAMEW}) [a-z]+(?: in all| altogether| in total)?",sk[1])
        if not q or (q['X3'] and sing(q['X3'])!=X):return None
        s=_Spec(text,nums);r=s.bind('rate',_k(m,'r'),f'{X}/{P}');n=s.bind('periods',_k(m,'n'),P)
        s.qty('total',X);s.rel(f'total = {r} * {n}',*sents[1]);return _done(s,'total',X,'each_period')
    a=re.fullmatch(rf"(?:a|an|the) [a-z]+ (?:was|is) #(?P<s>\d+) (?P<X>{W}) (?P<adj>tall|long|high|deep)",sk[0])
    q=re.fullmatch(rf"how (?P<adj>tall|long|high|deep) is (?:it|the [a-z]+) now",sk[2])
    if not (a and q and sing(a['X'])==X and a['adj']==q['adj'] and m['v'] in ('grew','grows','grow','rose','rises')):return None
    s=_Spec(text,nums);st=s.bind('start',_k(a,'s'),X);r=s.bind('rate',_k(m,'r'),f'{X}/{P}');n=s.bind('periods',_k(m,'n'),P)
    s.qty('now',X);s.rel(f'now = {st} + {r} * {n}',*sents[2]);return _done(s,'now',X,'each_period')


# ---- one of a pack ---------------------------------------------------------------------
def _one_of_pack(text,nums,sents,sk):
    if len(sk)==2:
        a=re.fullmatch(rf"(?:a|one) (?P<G>{W}) of #(?P<n>\d+) (?P<X>[a-z]+(?: [a-z]+)?) costs? #(?P<p>\d+) (?P<cur>dollars|cents)",sk[0])
        q=re.fullmatch(rf"how much does (?:#(?P<one>\d+)|each|a|an) (?P<X2>[a-z]+(?: [a-z]+)?) cost(?: in (?P<cur2>dollars|cents))?",sk[1])
        if not (a and q) or sing(a['X'].split()[-1])!=sing(q['X2'].split()[-1]) or (q['cur2'] and q['cur2']!=a['cur']):return None
        if q['one'] and nums[_k(q,'one')].value!=1:return None
        X=sing(a['X'].split()[-1]);cur=sing(a['cur'])
        s=_Spec(text,nums);n=s.bind('count',_k(a,'n'),X);p=s.bind('price',_k(a,'p'),cur)
        if q['one']:s.unused(_k(q,'one'),'one: the price of one is asked')
        s.qty('each',f'{cur}/{X}');s.rel(f'each = {p} / {n}',*sents[1]);return _done(s,'each',cur,'one_of_pack')
    if len(sk)==1:
        m=re.fullmatch(rf"if #(?P<n>\d+) (?P<X>{W}) costs? #(?P<p>\d+) (?P<cur>dollars|cents), how much does (?:one|each|a|an) (?P<X2>{W}) cost(?: in (?P<cur2>dollars|cents))?",sk[0])
        if not m or sing(m['X'])!=sing(m['X2']) or (m['cur2'] and m['cur2']!=m['cur']):return None
        X=sing(m['X']);cur=sing(m['cur'])
        s=_Spec(text,nums);n=s.bind('count',_k(m,'n'),X);p=s.bind('price',_k(m,'p'),cur)
        s.qty('each',f'{cur}/{X}');s.rel(f'each = {p} / {n}',*sents[0]);return _done(s,'each',cur,'one_of_pack')
    return None


# ---- age -------------------------------------------------------------------------------------
def _age(text,nums,sents,sk):
    if len(sk)!=2:return None
    a=re.fullmatch(rf"(?P<who>{NAMEW}) is #(?P<a>\d+)(?: years old)?",sk[0])
    if not a:return None
    q=re.fullmatch(rf"how old (?:will|would) (?:{PRON}|{a['who']}) be in #(?P<b>\d+) years",sk[1]);sign='+'
    if not q:
        q=re.fullmatch(rf"how old was (?:{PRON}|{a['who']}) #(?P<b>\d+) years ago",sk[1]);sign='-'
    if q:
        s=_Spec(text,nums);x=s.bind('age',_k(a,'a'),'year');y=s.bind('years',_k(q,'b'),'year')
        s.qty('then','year',True);s.rel(f'then = {x} {sign} {y}',*sents[1]);return _done(s,'then','year','age')
    return None


def _age_cmp(text,nums,sents,sk):
    if len(sk)!=3:return None
    a=re.fullmatch(rf"(?P<who>{NAMEW}) is #(?P<a>\d+) years old",sk[0])
    b=re.fullmatch(rf"(?P<rel>(?:his|her|their) [a-z]+) is #(?P<d>\d+) years (?P<cmp>older|younger)",sk[1])
    q=re.fullmatch(rf"how old is (?P<rel>(?:his|her|their) [a-z]+)",sk[2])
    if not (a and b and q) or b['rel']!=q['rel']:return None
    s=_Spec(text,nums);x=s.bind('age',_k(a,'a'),'year');d=s.bind('difference',_k(b,'d'),'year')
    s.qty('other','year',True);s.rel(f"other = {x} {'+' if b['cmp']=='older' else '-'} {d}",*sents[2]);return _done(s,'other','year','age')


# ---- a share of a whole ----------------------------------------------------------------------
def _share_of(text,nums,sents,sk):
    if len(sk)!=3:return None
    a=re.fullmatch(rf"(?:(?:a|an|the) [a-z]+(?: [a-z]+)? (?:has|holds|contains|had)|there (?:are|were)) #(?P<w>\d+) (?P<X>{W})(?: of [a-z]+)?(?: (?:in|at|on) (?:a|an|the) [a-z]+)?",sk[0])
    if not a:return None
    X=sing(a['X'])
    b=re.fullmatch(rf"#(?P<f>\d+) of them (?:are|were|is) (?P<st>[a-z]+)",sk[1]) or re.fullmatch(rf"#(?P<f>\d+) of them (?P<vp>[a-z]+(?: [a-z]+){{0,3}})",sk[1]) \
      or re.fullmatch(rf"it is #(?P<f>\d+) full",sk[1])
    if not b:return None
    f=nums[_k(b,'f')]
    if f.kind!='word' or not (0<f.value<1):return None
    gd=b.groupdict()
    if gd.get('st'):
        q=re.fullmatch(rf"how many (?:{gd['st']} (?P<X3>{W})|(?P<X4>{W}) are {gd['st']})(?: are there)?",sk[2])
    elif gd.get('vp'):
        q=re.fullmatch(rf"how many (?P<X3>{W}) {gd['vp']}",sk[2])
    else:
        q=re.fullmatch(rf"how many (?P<X3>{W})(?: of [a-z]+)? (?:are|is) in the [a-z]+",sk[2])
    if not q:return None
    xs=[v for k,v in q.groupdict().items() if k in ('X3','X4') and v]
    if not xs or sing(xs[0])!=X:return None
    s=_Spec(text,nums);w=s.bind('whole',_k(a,'w'),X);sh=s.bind('share',_k(b,'f'),'1')
    s.qty('part',X,whole(X));s.rel(f'part = {w} * {sh}',*sents[2]);return _done(s,'part',X,'share_of')


# ---- what was gained ---------------------------------------------------------------------------
GAIN=r'(?:won|got|found|bought|received|picked|collected|caught|earned)'
def _gained(text,nums,sents,sk):
    if len(sk)!=3:return None
    a=re.fullmatch(rf"(?P<who>{NAMEW}) had #(?P<a>\d+) (?P<X>{W})",sk[0])
    b=re.fullmatch(rf"(?:{PRON}|{NAMEW}) (?P<v>{GAIN}) some more(?: (?P<X1>{W}))? and now (?:has|had) #(?P<b>\d+) (?P<X2>{W})",sk[1])
    q=re.fullmatch(rf"how many (?P<X3>{W}) did (?:{PRON}|{NAMEW}) (?P<v>[a-z]+)",sk[2])
    if not (a and b and q) or not (sing(a['X'])==sing(b['X2'])==sing(q['X3'])) or (b['X1'] and sing(b['X1'])!=sing(a['X'])):return None
    X=sing(a['X'])
    s=_Spec(text,nums);x=s.bind('before',_k(a,'a'),X);y=s.bind('after',_k(b,'b'),X)
    s.qty('gained',X,True);s.rel(f'gained = {y} - {x}',*sents[2]);return _done(s,'gained',X,'gained')


# ---- groups of ---------------------------------------------------------------------------------
def _groups_of(text,nums,sents,sk):
    if len(sk)!=2:return None
    a=re.fullmatch(rf"(?:(?:a|an|the) [a-z]+(?: [a-z]+)? has|{SUBJ} (?:made|makes|baked|bakes|picked|picks|packed|packs) #(?P<n2>\d+) (?P<X2>{W}) and (?:put|puts|packed|packs) them into) ?(?:#(?P<n>\d+) (?P<X>{W}) in )?(?P<G>boxes|bags|packs|groups|rows|crates|baskets|cartons|jars) of #(?P<k>\d+)",sk[0])
    if not a:return None
    n=a['n'] or a['n2'];X=a['X'] or a['X2']
    if n is None or X is None:return None
    q=re.fullmatch(rf"how many (?P<G2>{W}) (?:are there|did (?:{PRON}|{NAMEW}|the [a-z]+) (?:fill|fills|make|need|use)|are needed|does (?:{PRON}|{NAMEW}|the [a-z]+) (?:fill|need))",sk[1])
    if not q or sing(q['G2'])!=sing(a['G']):return None
    G=sing(a['G']);X=sing(X)
    s=_Spec(text,nums);t=s.bind('total',int(n),X);k=s.bind('size',_k(a,'k'),f'{X}/{G}')
    s.qty('groups',G,True);s.rel(f'groups = {t} / {k}',*sents[1]);return _done(s,'groups',G,'groups_of')


# ---- average speed -----------------------------------------------------------------------------
def _avg_speed(text,nums,sents,sk):
    if len(sk)!=2:return None
    a=re.fullmatch(rf"(?:{NAMEW}|{PRON}|the [a-z]+) (?:drove|traveled|travelled|ran|walked|rode|flew|cycled|biked|swam|hiked) #(?P<d>\d+) (?P<L>kilometers|miles|meters) in #(?P<t>\d+) (?P<T>hours|minutes)",sk[0])
    q=re.fullmatch(rf"what (?:was|is) (?:his|her|its|their|the) average speed in (?P<L2>kilometers|miles|meters) per (?P<T2>hour|minute)",sk[1])
    if not (a and q) or a['L']!=q['L2'] or sing(a['T'])!=q['T2']:return None
    L=sing(a['L']);T=q['T2']
    s=_Spec(text,nums);d=s.bind('distance',_k(a,'d'),L);t=s.bind('time',_k(a,'t'),T)
    s.qty('speed',f'{L}/{T}');s.rel(f'speed = {d} / {t}',*sents[1]);return _done(s,'speed',f'{L}/{T}','avg_speed')


# ---- things bought at a price; change from a bill ------------------------------------------------
def _bought(text,nums,sents,sk):
    if len(sk)==2:
        a=re.fullmatch(rf"(?:{NAMEW}|{PRON}) (?:bought|buys) #(?P<a>\d+) (?P<X>{W}) at #(?P<p>\d+) (?P<c1>dollars?|cents?) each and #(?P<b>\d+) (?P<Y>{W}) at #(?P<q>\d+) (?P<c2>dollars?|cents?) each",sk[0])
        q=re.fullmatch(rf"how much (?:money )?did (?:{PRON}|{NAMEW}) spend(?: in all| altogether| in total)?",sk[1])
        if not (a and q) or sing(a['c1'])!=sing(a['c2']):return None
        cur=sing(a['c1']);X,Y=sing(a['X']),sing(a['Y'])
        s=_Spec(text,nums);x=s.bind('count1',_k(a,'a'),X);p=s.bind('price1',_k(a,'p'),f'{cur}/{X}');y=s.bind('count2',_k(a,'b'),Y);r=s.bind('price2',_k(a,'q'),f'{cur}/{Y}')
        s.qty('cost',cur);s.rel(f'cost = {x} * {p} + {y} * {r}',*sents[1]);return _done(s,'cost',cur,'bought')
    if len(sk)==3:
        a=re.fullmatch(rf"(?:{NAMEW}|{PRON}) (?:bought|buys) (?:a|an|the) [a-z]+ for #(?P<p>\d+) dollars and (?:a|an|the) [a-z]+ for #(?P<q>\d+) dollars",sk[0])
        b=re.fullmatch(rf"(?:{PRON}|{NAMEW}) (?:paid|pays|gave the cashier) (?:with )?(?:a|an) #(?P<m>\d+)-dollar bill",sk[1])
        q=re.fullmatch(rf"how much change did (?:{PRON}|{NAMEW}) (?:get|receive)(?: back)?",sk[2])
        if not (a and b and q):return None
        s=_Spec(text,nums);x=s.bind('price1',_k(a,'p'),'dollar');y=s.bind('price2',_k(a,'q'),'dollar');m=s.bind('paid',_k(b,'m'),'dollar')
        s.qty('change','dollar');s.rel(f'change = {m} - {x} - {y}',*sents[2]);return _done(s,'change','dollar','bought')
    return None


# ---- two amounts together; how many more ------------------------------------------------------------
def _together(text,nums,sents,sk):
    if len(sk)!=2:return None
    a=re.fullmatch(rf"(?:{NAMEW}|{PRON}) (?P<v>[a-z]+) #(?P<a>\d+) (?P<X>{W})(?: on (?P<d1>[a-z]+))? and (?:(?P<who2>(?:his|her|their) [a-z]+|{NAMEW}) (?P<v2>[a-z]+) #(?P<b>\d+)(?: (?P<X2>{W}))?|#(?P<c>\d+) (?P<X3>{W}) on (?P<d2>[a-z]+))",sk[0])
    if not a:return None
    X=sing(a['X'])
    for g in ('X2','X3'):
        if a[g] and sing(a[g])!=X:return None
    if a['v2'] and a['v2']!=a['v']:return None
    q=re.fullmatch(rf"how many (?P<X4>{W}) did (?:they|{PRON}|{NAMEW}) (?P<v>[a-z]+) (?:together|in all|altogether|in total|in both days|in the #(?P<dd>\d+) days)",sk[1])
    if not q or sing(q['X4'])!=X:return None
    if q['dd'] and (nums[_k(q,'dd')].value!=2 or not (a['d1'] and a['d2'])):return None
    k2=a['b'] or a['c']
    s=_Spec(text,nums);x=s.bind('first',_k(a,'a'),X);y=s.bind('second',int(k2),X)
    if q['dd']:s.unused(_k(q,'dd'),'the two days named before, not an amount')
    s.qty('total',X,True);s.rel(f'total = {x} + {y}',*sents[1]);return _done(s,'total',X,'together')


def _how_many_more(text,nums,sents,sk):
    if len(sk)!=2:return None
    a=re.fullmatch(rf"(?:(?:a|an|the) [a-z]+|{NAMEW}) (?:has|had|have) #(?P<a>\d+) (?P<X>{W}) and #(?P<b>\d+) (?P<Y>{W})",sk[0])
    q=re.fullmatch(rf"how many more (?P<X2>{W}) than (?P<Y2>{W}) (?:does|did|do) (?:the [a-z]+|{NAMEW}|{PRON}) (?:have|has)",sk[1]) if a else None
    if a and q and sing(a['X'])==sing(q['X2']) and sing(a['Y'])==sing(q['Y2']):
        # the two kinds are counted alike (animals, things): the difference is in either one
        s=_Spec(text,nums);x=s.bind('first',_k(a,'a'),'thing');y=s.bind('second',_k(a,'b'),'thing')
        s.qty('difference','thing',True);s.rel(f'difference = {x} - {y}',*sents[1]);return _done(s,'difference','thing','how_many_more')
    a=re.fullmatch(rf"(?:{NAMEW}|{PRON}) (?P<v>scored|got|earned|read|ran|won|made) #(?P<a>\d+) (?P<X>{W}) in the (?P<o1>#\d+|[a-z]+) (?P<G>[a-z]+) and #(?P<b>\d+) (?P<X2>{W}) in the (?P<o2>#\d+|[a-z]+) (?P<G2>[a-z]+)",sk[0])
    if not a or sing(a['X'])!=sing(a['X2']) or a['G']!=a['G2']:return None
    q=re.fullmatch(rf"how many more (?P<X3>{W}) did (?:{PRON}|{NAMEW}) [a-z]+ in the (?P<o>#\d+|[a-z]+) {a['G']}",sk[1])
    o=lambda x:nums[int(x[1:])].value if x.startswith('#') else x
    if not q or sing(q['X3'])!=sing(a['X']) or o(q['o']) not in (o(a['o1']),o(a['o2'])) or o(a['o1'])==o(a['o2']):return None
    X=sing(a['X']);hi,lo=('a','b') if o(q['o'])==o(a['o1']) else ('b','a')
    s=_Spec(text,nums);x=s.bind('asked',_k(a,hi),X);y=s.bind('other',_k(a,lo),X)
    s.qty('difference',X,True);s.rel(f'difference = {x} - {y}',*sents[1]);return _done(s,'difference',X,'how_many_more')


# ---- a change of a measure; kinds of one thing; a clock; holds -------------------------------------
def _measure_change(text,nums,sents,sk):
    if len(sk)!=2:return None
    a=re.fullmatch(rf"the (?P<m>temperature|water level|price) was #(?P<a>\d+) (?P<U>degrees|centimeters|meters|dollars)(?: in the [a-z]+| at [a-z]+)? and (?P<v>rose|went up|increased|dropped|fell|went down|decreased) by #(?P<b>\d+) (?P<U2>degrees|centimeters|meters|dollars)(?: by [a-z]+)?",sk[0])
    q=re.fullmatch(rf"what (?:was|is) the (?P<m>temperature|water level|price)(?: at [a-z]+| then| now)?",sk[1])
    if not (a and q) or a['U']!=a['U2'] or a['m']!=q['m']:return None
    U=sing(a['U']);sign='+' if a['v'] in ('rose','went up','increased') else '-'
    s=_Spec(text,nums);x=s.bind('before',_k(a,'a'),U);y=s.bind('change',_k(a,'b'),U)
    s.qty('after',U,False,signed=True);s.rel(f'after = {x} {sign} {y}',*sents[1]);return _done(s,'after',U,'measure_change')


def _kinds(text,nums,sents,sk):
    if len(sk)!=2:return None
    a=re.fullmatch(rf"there (?:are|were) #(?P<a>\d+) (?P<A>[a-z]+) (?P<X>{W}) and #(?P<b>\d+) (?P<B>[a-z]+) (?P<Y>{W})(?: in (?:a|an|the) [a-z]+(?: [a-z]+)?)?",sk[0])
    q=re.fullmatch(rf"how many (?P<X2>{W}) (?:are|were) (?:in|at|on) the [a-z]+(?: [a-z]+)?",sk[1])
    if not (a and q) or not (sing(a['X'])==sing(a['Y'])==sing(q['X2'])) or a['A']==a['B']:return None
    X=sing(a['X'])
    s=_Spec(text,nums);x=s.bind('first',_k(a,'a'),X);y=s.bind('second',_k(a,'b'),X)
    s.qty('total',X,True);s.rel(f'total = {x} + {y}',*sents[1]);return _done(s,'total',X,'kinds')


def _clock(text,nums,sents,sk):
    if len(sk)!=2:return None
    a=re.fullmatch(r"(?:a|an|the) [a-z]+ starts at #(?P<a>\d+) o'clock and lasts #(?P<b>\d+) hours?",sk[0])
    q=re.fullmatch(r"(?:at )?what (?:hour|time) does it (?:end|finish)",sk[1])
    if not (a and q):return None
    if nums[_k(a,'a')].value+nums[_k(a,'b')].value>12:return None
    s=_Spec(text,nums);x=s.bind('start',_k(a,'a'),'hour');y=s.bind('length',_k(a,'b'),'hour')
    s.qty('end','hour',True);s.rel(f'end = {x} + {y}',*sents[1]);return _done(s,'end','hour','clock')


def _holds(text,nums,sents,sk):
    if len(sk)!=2:return None
    a=re.fullmatch(rf"(?:a|an|one|each) (?P<C>[a-z]+(?: [a-z]+)?) (?:holds|contains|weighs) #(?P<a>\d+) (?P<U>{W})",sk[0])
    q=re.fullmatch(rf"how many (?P<U2>{W}) (?:do|would|will|can) #(?P<b>\d+) (?P<C2>{W}) (?:hold|contain|weigh)(?: in all| altogether)?",sk[1])
    if not (a and q) or sing(a['U'])!=sing(q['U2']) or sing(a['C'].split()[-1])!=sing(q['C2']):return None
    U=sing(a['U']);C=sing(q['C2'])
    s=_Spec(text,nums);x=s.bind('each',_k(a,'a'),f'{U}/{C}');y=s.bind('count',_k(q,'b'),C)
    s.qty('total',U);s.rel(f'total = {x} * {y}',*sents[1]);return _done(s,'total',U,'holds')


def _tables(text,nums,sents,sk):
    if len(sk)!=3:return None
    a=re.fullmatch(rf"there (?:are|were) #(?P<g>\d+) (?P<G>{W}) with #(?P<n>\d+) (?P<X>{W}) (?:at|on|in) each (?P<G2>{W})",sk[0])
    b=re.fullmatch(rf"#(?P<k>\d+) (?P<X2>{W}) (?:are|were) (?P<st>[a-z]+)",sk[1])
    q=re.fullmatch(rf"how many (?P<X3>{W}) (?:are|were) (?P<st>[a-z]+)",sk[2])
    if not (a and b and q) or not (sing(a['X'])==sing(b['X2'])==sing(q['X3'])) or sing(a['G'])!=sing(a['G2']) or (b['st'],q['st']) not in OPP|{(y,x) for x,y in OPP}:return None
    X,G=sing(a['X']),sing(a['G'])
    s=_Spec(text,nums);g=s.bind('groups',_k(a,'g'),G);n=s.bind('each',_k(a,'n'),f'{X}/{G}');k=s.bind('part',_k(b,'k'),X)
    s.qty('rest',X,True);s.rel(f'rest = {g} * {n} - {k}',*sents[2]);return _done(s,'rest',X,'tables')


FORMS=(_groups_left,_tables,_rest,_several_away,_each_period,_one_of_pack,_age,_age_cmp,_share_of,_gained,_groups_of,_avg_speed,_bought,
       _together,_how_many_more,_measure_change,_kinds,_clock,_holds)
