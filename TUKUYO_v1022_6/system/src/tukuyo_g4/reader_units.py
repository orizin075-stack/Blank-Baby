"""generation 4 (round 11): a reader by what the amounts are, not by how the sentences are worded. No LLM.

Round 10 added everyday forms one by one, each a pattern over whole sentences; on a new held-out set they read hardly
more than before (English 14 -> 15 of 60). The words around a number change from writer to writer; what the number is
does not. This reader asks of every number only what it is:

  count   an amount of a thing (9 children, $45, 12 miles), with who or what it belongs to and what happened to it
          (there was, came, was eaten)
  rate    an amount of one thing for each of another (6 dollars per day, 4 batteries in a pack, 250 mL in a glass,
          4 cups for 2 loaves)
  cmp     an amount said against another (3 pounds less than the puppy, 6 times as much, half as long)
  frac    a part of another amount (one third of the 36 cupcakes, one fifth off)

and of the question only what it asks for: the unit (pounds, children, dollars for each friend), whose it is, and in
what way (the total, what is left, how many more are needed, the difference). Then a few laws, the same for every
wording and both languages, are tried in a fixed order:

  part     a part of an amount is the fraction times the amount
  compare  an amount said against another is that one plus, minus, times or divided by it
  rate     a rate times an amount of what it is per gives an amount of the thing (6 dollars/day x 5 days); an amount
           of the thing divided by the rate gives how many of what it is per (28 batteries / 4 per pack)
  share    an amount over a count, when the question asks for each one (45 dollars / 5 friends)
  holding  what there is now is what there was, with what came and less what went (a start must be told)
  whole    a whole less its parts (28 crayons, 13 broken: 15 not broken), a total of parts, what is still needed

A reading is made only if every number of the text is used once by these laws (or is an ordinal or the 1 of a rate),
the units of every step agree, the answer is not just a number of the text, and exactly one way of using the laws
fits. Anything else is not read: two counts a rate could apply to, a story with a start that is not told, a question
whose holder is not the one the amounts belong to. The checker (check.py) verifies every reading on its own, as for
every reader.
"""
from __future__ import annotations
import re
from fractions import Fraction
from . import numbers as N
from .fpl import SCHEMA,fmt

READER='tukuyo.g4.reader_units/1'


class NoRead(Exception):pass
def no(why):raise NoRead(why)


class Amt:
    """one number of the text and what it is (or an amount a law made from others)"""
    __slots__=('k','v','raw','span','u','per','kind','role','op','tags','who','sent','inq','base','of','name','used','ref','start','verb','adjs',
               'derived','order','zero','stuff','kept','pos','end','aux','subj','lead','src','dozen','more','noun','clause','atags')
    def __init__(s,**kw):
        for x in s.__slots__:setattr(s,x,None)
        s.tags=frozenset();s.adjs=frozenset();s.used=False;s.ref=False;s.derived=False;s.zero=False;s.kept=False
        for k,v in kw.items():setattr(s,k,v)
    def __repr__(s):
        return f"<{s.kind} {fmt(s.v) if s.v is not None else s.name} {s.u}{'/'+str(s.per) if s.per else ''} {s.role or ''}{s.op or ''} {sorted(s.tags)}>"


class Tgt:
    __slots__=('u','per','tags','mode','verb','notadj','raw','stuff','geo','kind','np')
    def __init__(s,**kw):
        for x in s.__slots__:setattr(s,x,None)
        s.tags=frozenset()
        for k,v in kw.items():setattr(s,k,v)
    def __repr__(s):return f"<ask {s.u}{'/'+str(s.per) if s.per else ''} {s.mode} {sorted(s.tags)} verb={s.verb} not={s.notadj}>"


class Spec:
    def __init__(s,text,lang,whole_units):
        s.text=text;s.lang=lang;s.q={};s.f=[];s.unused=[];s.i=0;s.whole=whole_units
    def _name(s,stem):
        s.i+=1;return re.sub(r'[^A-Za-z0-9_]','_',stem)[:24].strip('_')+f'_{s.i}' if re.match(r'[A-Za-z]',stem or '') else f'q_{s.i}'
    def _unit(s,u,per=None):
        u=u or '1'
        return f'{u}/{per}' if per else u
    def qty(s,stem,unit,integer):
        n=s._name(stem);s.q[n]={'name':n,'unit':unit,'integer':bool(integer),'signed':False,'about':''};return n
    def bind(s,a):
        unit=s._unit(a.u,None if a.base is not None else a.per) if a.kind in ('count','rate') else ('1' if a.kind in ('frac',) or a.op in ('*','/') else s._unit(a.u))
        whole=a.kind=='count' and s.whole(a.u) and a.v.denominator==1
        a.name=s.qty(a.u if a.kind!='frac' else 'part',unit,whole)
        s.f.append({'eq':f'{a.name} = {fmt(a.v)}','span':a.span});return a.name
    def known(s,u,per,value,said):
        n=s.qty(f'{u}_per_{per}',f'{u}/{per}',True);s.f.append({'eq':f'{n} = {fmt(value)}','known':said});return n
    def known_count(s,u,value,said):
        n=s.qty(u,u,True);s.f.append({'eq':f'{n} = {fmt(value)}','known':said});return n
    def rel(s,u,expr,span,per=None,whole=None):
        n=s.qty(u or 'x',s._unit(u,per),s.whole(u) if whole is None and not per else bool(whole))
        s.f.append({'eq':f'{n} = {expr}','span':span});return n
    def done(s,ask,form):
        return {'schema':SCHEMA,'lang':s.lang,'text':s.text,'quantities':list(s.q.values()),'facts':s.f,'ask':ask,
                'answer_unit':s.q[ask]['unit'],'unused':s.unused,'reader':f'{READER}:{form}'}


def _d(spec,u,expr,span,tags,parts,role='derived',per=None,whole=None):
    """an amount a law made: its fact in the reading, and the amounts it was made of marked used"""
    for p in parts:p.used=True
    n=spec.rel(u,expr,span,per=per,whole=whole)
    t=frozenset(tags)
    return Amt(name=n,u=u,per=per,kind='rate' if per else 'count',role=role,tags=t,derived=True,span=span,
               order=min((p.order for p in parts if p.order is not None),default=0),sent=parts[-1].sent,inq=any(p.inq for p in parts))


def _holder(a):
    """the noun or name an amount is said of, when its clause says one ('A car travels at 50 miles per hour')"""
    ws=[w for w in (a.subj or []) if w not in EN_FUNC and w not in PRON and w not in ('what','how','which')]
    return _sing(ws[-1]) if ws else None


def _same_holder(r,c):
    if r.src in ('subject','subject_each') or r.sent==c.sent or c.inq:return True
    a,b=_holder(r),_holder(c)
    return not (a and b and a!=b and a not in (c.subj or []) and b not in (r.subj or []))


def _match_per(per,c):
    """is c an amount of what the rate is per? 'adult ticket' and '2 adults', 'day' and '5 school days', '大人' and '大人2人'"""
    if c.u==per:return True
    if c.noun and c.noun==per:return True
    w=per.split()
    return len(w)>1 and (c.u==w[-1] or c.u in w) and c.u not in ('dollar','cent','円')


def compose(text,lang,amts,tg,spec,ctx):
    """the laws, in their order, over the amounts; -> (ask name, form) or NoRead"""
    for a in amts:spec.bind(a)
    pool=list(amts);steps=[]
    # what everyone knows: how many legs, wheels or eyes a thing has, asked of a number of them
    fact=ctx.get('fact')
    if fact and tg.u and not any(a.kind=='rate' and a.u==tg.u for a in pool):
        for c in [a for a in pool if a.kind=='count' and a.u!=tg.u]:
            k=fact(c,tg.u)
            if k:
                n=spec.known(tg.u,c.u,k[0],k[1])
                pool.append(Amt(kind='rate',u=tg.u,per=c.u,name=n,derived=True,span=c.span,order=c.order,sent=c.sent,tags=c.tags))
                steps.append('known')
    counts=lambda:[a for a in pool if a.kind=='count' and not a.used]
    # part: a fraction of an amount
    for a in [x for x in pool if x.kind=='frac']:
        base=a.of
        if base is None or base.kind!='count':no('PART_OF_WHAT')
        if base.used:no('PART_BASE_USED')
        tags=a.tags or base.tags
        d=_d(spec,base.u,f'{a.name} * {base.name}',a.span,tags,[a],role='part')
        base.ref=True;d.adjs=a.adjs;d.zero=False;d.order=a.order;d.kept=a.kept;d.atags=base.atags   # where the whole is, the part is
        if a.op=='off':d.tags=frozenset(tags)|{'discount','off'}
        pool.append(d);steps.append('part')
    # compare: an amount said against another
    for a in [x for x in pool if x.kind=='cmp']:
        base=a.of
        if base is None:no('COMPARED_TO_WHAT')
        if base.kind!='count':no('COMPARED_TO_A_RATE')
        if a.op in '+-' and a.u and base.u!=a.u:
            conv=ctx.get('convert')
            if not conv:no('COMPARED_UNITS')
        expr={'+':f'{base.name} + {a.name}','-':f'{base.name} - {a.name}','*':f'{base.name} * {a.name}','/':f'{base.name} / {a.name}'}[a.op]
        d=_d(spec,base.u,expr,a.span,a.tags,[a],role='cmp');d.order=a.order;d.inq=a.inq
        base.ref=True;pool.append(d);steps.append('compare')
    # a measure said in two units ('1 meter and 30 centimeters', '1m30cm'): one amount in the smaller
    conv=ctx.get('convert')
    for a,b in [(x,y) for x in pool for y in pool if x.kind=='count' and y.kind=='count' and x.sent==y.sent and y.order==x.order+1]:
        if a.used or b.used or not conv or not conv(a.u,b.u):continue
        gap=ctx['sents'][a.sent][a.end:b.pos] if ctx.get('sents') and a.end is not None else None
        if gap is None or not re.fullmatch(r'\s*(?:[A-Za-zぁ-んァ-ヶ一-龯²]{1,12})\s*(?:and|と)?\s*',gap) or not re.match(r'\s*(?:'+'|'.join(map(re.escape,_unit_words(a.u)))+r')',gap):continue
        k,said=conv(a.u,b.u);n=spec.known(b.u,a.u,k,said)
        d=_d(spec,b.u,f'{a.name} * {n} + {b.name}',b.span,a.tags|b.tags,[a,b],role=b.role or 'state',whole=False)
        d.order=a.order;d.sent=a.sent;d.verb=b.verb;d.lead=a.lead;d.kept=b.kept;pool.append(d);steps.append('two_units')
    # 'How many pages does she read in a week?' at 15 pages each night: the 7 nights of a week, known
    pr=ctx.get('period')
    if pr:
        big,r=pr;small={'night':'day','morning':'day','evening':'day','afternoon':'day'}.get(r.per,r.per)
        k,said=ctx['convert'](big,small)
        n=spec.known_count(r.per,k,said)
        pool.append(Amt(kind='count',u=r.per,name=n,derived=True,span=ctx['qspan'],order=10**6,sent=None,inq=True,tags=frozenset(),role='state'))
        steps.append('known')
    # in N years, N years ago (4年後): every age then
    sh=[a for a in pool if a.kept in ('shift+','shift-')]
    if sh:
        if len(sh)!=1:no('TWO_SHIFTS')
        z=sh[0];z.used=True
        ages=[a for a in pool if a.kind=='count' and a.u==tg.u and a is not z and not a.inq and not a.used]
        if not ages:no('SHIFT_OF_NOTHING')
        for a in ages:
            d=_d(spec,tg.u,f"{a.name} {'+' if z.kept=='shift+' else '-'} {z.name}",z.span,a.tags,[a],role='state')
            d.order=a.order;d.sent=a.sent;pool.append(d)
        steps.append('years_later' if z.kept=='shift+' else 'years_before')
    # rate: a rate times an amount of what it is per; an amount over a rate
    changed=True
    while changed:
        changed=False
        for r in [x for x in pool if x.kind=='rate' and not x.used]:
            # an amount in a unit the rate is not in, converted to meet it ('6 L' for '1 dL a cup', '2 hours' at '3 m a minute')
            if conv and r.base is None:
                for c in [x for x in counts() if not x.ref and x.u not in (r.u,r.per)]:
                    for want in (r.per,r.u):
                        k=conv(c.u,want) if not any(y.u==want for y in counts() if y is not c) else None
                        if k:
                            n=spec.known(want,c.u,k[0],k[1])
                            d=_d(spec,want,f'{c.name} * {n}',c.span,c.tags,[c],role=c.role or 'state',whole=False)
                            d.order=c.order;d.sent=c.sent;d.verb=c.verb;d.inq=c.inq;pool.append(d);steps.append('convert');break
            if r.base is not None:
                # 4 cups for 2 loaves: the rate is the one over the other
                if r.base.used:no('RATIO_BASE_USED')
                nr=_d(spec,r.u,f'{r.name} / {r.base.name}',r.span,r.tags,[r.base],per=r.per,whole=False)
                nr.order=r.order;r.used=True;r.base.used=True;pool.append(nr);r=nr;changed=True
            cs=[c for c in counts() if c.per is None and _match_per(r.per,c) and c is not r.base and not c.ref and _same_holder(r,c)]
            if len(cs)>1:
                # the rate's own count when its sentence says 'on each of 9 mornings' or the question names the other
                near=[c for c in cs if c.sent==r.sent and c.order>r.order]
                if len(near)==1:cs=near
                else:no('RATE_TWO_COUNTS')
            if len(cs)==1:
                c=cs[0];role=c.role if c.role in ('state','gain','loss','act','goal','intent') else 'product'
                if r.u in ('dollar','cent','円') and role in ('gain','loss'):
                    # money for things bought is spent, for things sold is taken in
                    v=(c.verb or '')
                    role='loss' if re.match(r'(?:buy|bought|purchas|order|rent|買|かい|かっ|注文)',v) else 'gain' if re.match(r'(?:sell|sold|売|うり|うれ)',v) else 'money'
                c=cs[0];d=_d(spec,r.u,f'{r.name} * {c.name}',c.span if c.inq else r.span,c.tags|r.tags,[r,c],role=role)
                d.verb=c.verb;d.lead=c.lead;d.more=c.more;d.subj=c.subj
                d.order=max(r.order,c.order);d.adjs=c.adjs|r.adjs;pool.append(d);steps.append('rate');changed=True;continue
            if tg.u==r.per or (tg.u and _match_per(r.per,Amt(u=tg.u))):
                cs=[c for c in counts() if c.u==r.u and not c.ref]
                if len(cs)==1:
                    c=cs[0];d=_d(spec,r.per.split()[-1] if ' ' in r.per else r.per,f'{c.name} / {r.name}',c.span,c.tags,[r,c],role='groups',whole=True)
                    d.order=max(r.order,c.order);pool.append(d);steps.append('groups');changed=True;continue
                if len(cs)>1:no('RATE_TWO_TOTALS')
        # a rate in units the asked unit is converted from ('3 meters a minute' for 2 hours, asked in meters)
    left_rates=[x for x in pool if x.kind=='rate' and not x.used]
    # share: an amount over a count, asked for each one
    if tg.per:
        cs=counts()
        if left_rates:
            if len(left_rates)==1 and left_rates[0].u==tg.u and left_rates[0].per==tg.per and not cs:
                return _ask(spec,tg,left_rates[0],steps,ctx)
            no('RATE_NOT_APPLIED')
        num=[c for c in cs if c.u==tg.u and not c.ref];den=[c for c in cs if c.u!=tg.u and _match_per(tg.per,c) and not c.ref]
        if len(num)!=1 or len(den)!=1:no('SHARE_NOT_ONE_EACH')
        a,b=num[0],den[0]
        if [c for c in cs if c not in (a,b) and not c.ref]:no('SHARE_LEFT_OVER')
        if not ctx.get('equal') and not (tg.u in ('dollar','cent','円') and (a.role in ('loss','goal','state') or b.role in ('gain','loss'))):no('SHARE_NOT_SAID_EQUAL')
        d=_d(spec,tg.u,f'{a.name} / {b.name}',ctx['qspan'],a.tags,[a,b],role='share',per=tg.per,whole=spec.whole(tg.u))
        steps.append('share');return _ask(spec,tg,d,steps,ctx)
    if left_rates:no('RATE_NOT_APPLIED')
    # converted to the asked unit (3 m in cm, 6 L in dL): a known constant
    conv=ctx.get('convert')
    if conv and tg.u:
        for c in [x for x in counts() if x.u!=tg.u]:
            k=conv(c.u,tg.u)
            if k:
                n=spec.known(tg.u,c.u,k[0],k[1])
                d=_d(spec,tg.u,f'{c.name} * {n}',c.span,c.tags,[c],role=c.role if c.role in ('state','gain','loss','act','goal') else 'convert',whole=False)
                d.order=c.order;d.adjs=c.adjs;d.kept=c.kept or 'converted';d.verb=c.verb;d.more=c.more;d.lead=c.lead;d.sent=c.sent
                pool.append(d);steps.append('convert')
    return _whole(spec,tg,pool,steps,ctx)


def _unit_words(u):
    """the ways a unit is written right after its number"""
    ws=[w for w,c in _EU.items() if c==u]+[w for w,c in _JC.items() if c==u]
    return sorted(set(ws),key=len,reverse=True) or [u]


_CAPS_NOT_NAMES=frozenset('the a an there then later after before on in at if how what when where which who why she he they it her his '
                          'their its we you i my our your this that these those each every one two three four five six seven eight nine ten '
                          'last next first second some all both mr mrs ms dr by for with from during while so but and or yesterday today '
                          'tomorrow monday tuesday wednesday thursday friday saturday sunday january february march april may june july '
                          'august september october november december moving with'.split())
def _names(sen):
    en={w for w in re.findall(r"\b([A-Z][a-z]+)\b",sen or '') if w.lower() not in _CAPS_NOT_NAMES}
    ja=set(re.findall(r'([一-龯ァ-ヶーぁ-ん]{1,6}?)(?:さん|くん|ちゃん)',sen or ''))
    return en|ja


def _full(a):return a.tags|(a.atags or frozenset())
def _distinct_full(a,others):
    """what tells a from the others, the words after it too ('on Monday')"""
    return _full(a)-frozenset().union(*[_full(o) for o in others]) if others else _full(a)


def _distinct(a,others):
    return a.tags-frozenset().union(*[o.tags for o in others]) if others else a.tags


def _whole(spec,tg,pool,steps,ctx):
    """the last law: the amounts of the asked unit, put together by the question"""
    cs=[a for a in pool if a.kind=='count' and not a.used]
    if not [a for a in cs if a.u==tg.u]:
        # the part named by its own noun: 'Owls made up one fourth of the 48 birds ... How many owls'
        parts=[a for a in cs if a.role=='part' and tg.u in a.tags]
        if len(parts)==1:tg.u=parts[0].u
    other=[a for a in cs if a.u!=tg.u and not a.ref]
    if other:
        # an amount of another kind of thing that no law and not the question needs ('Sam is 9 years old. He has 3
        # boxes of 6 pencils'): set aside, with the reason. Never one the laws made, one in the question, one of the asked
        # thing's unit or of a unit it converts to, or of a unit any rate or comparison of the problem is in
        near={tg.u,tg.per}|{x.u for x in pool if x.kind in ('rate','cmp')}|{x.per for x in pool if x.kind=='rate'}
        conv=ctx.get('convert')
        asked_sents={x.sent for x in pool if x.kind=='count' and x.u==tg.u and not x.derived}
        # nor one beside an amount the laws used ('3 cars and 2 vans ... 4 people in each car')
        asked_sents|={x.sent for x in pool if not x.derived and x not in other and x.kind in ('count','rate','cmp','frac')}
        if 'known' in steps:no('LEFT_OVER_AFTER_A_KNOWN_FACT')
        if tg.mode=='total' and any(x.u not in EN_MEASURE and x.u not in J_MEASURE for x in other):no('LEFT_OVER_IN_ALL')
        for a in other:
            if a.derived or a.inq or a.u in near or (conv and (conv(a.u,tg.u) or conv(tg.u,a.u))) or a.v==0 or \
                    (a.u in TIME and not (a.u=='year' and re.search(r'\byears?\s+old\b',a.clause or '',re.I))) or a.u in ('日','週','か月','年','時間','分','秒','回') or a.sent in asked_sents:
                no('LEFT_OVER:'+','.join(sorted({str(x.u) for x in other})))
        if len({a.u for a in other})!=len(other):no('LEFT_OVER_SAME_KIND')
        for a in other:
            a.used=True
            spec.f=[f for f in spec.f if not f['eq'].startswith(a.name+' = ')];spec.q.pop(a.name,None)
            spec.unused.append({'raw':a.raw,'why':f'an amount of another thing ({a.u}) the question does not ask about' if spec.lang=='en'
                                else f'問いと関わらない別のものの量 ({a.u})'})
        steps.append('set_aside')
    cs=[a for a in cs if a.u==tg.u]
    if not cs:no('NOTHING_OF_THE_ASKED_UNIT')
    # 'How many red balls in total?' after '4 red balls and 6 blue balls': only what is of the kind asked
    kind=(tg.np or frozenset())-{tg.u,'more','fewer','less','total','extra','other'}
    if kind:
        other_kind=[a for a in cs if a.adjs and not (kind&(a.adjs|a.tags))]
        if other_kind:
            cs=[a for a in cs if a not in other_kind]
            for a in other_kind:
                if not a.derived:no('ASKS_ONE_KIND_OF_SEVERAL')
    mode=tg.mode;qs=ctx['qspan']
    live=[a for a in cs if not a.ref]
    # geometry asked: area, perimeter
    if tg.geo:return _geometry(spec,tg,cs,steps,ctx)
    if mode=='unsure':no('HOW_MANY_MORE_OF_WHAT')
    if mode=='total' and any((x.verb=='left' and x.role=='state') for x in cs if not x.derived):
        no('TOTAL_OF_WHAT_WAS_AND_WHAT_IS_LEFT')
    if mode=='total':
        # a story that tells totals of its own ('The first and second bags contain a total of 11 apples'): its parts may overlap
        if any(re.search(r'\b(?:total|in all|altogether|together|combined)\b|合わせて|あわせて|全部で|合計',x.clause or x.span or '') for x in cs if not x.derived):
            no('TOTALS_IN_THE_STORY')
        ht=tg.tags-(tg.np or frozenset())
        if ctx.get('owners') is not None:ht=ht&ctx['owners']
        if ht and len(cs)>=2:
            # 'how many car robots does Bob have in total': only what is Bob's
            mine=[a for a in cs if _distinct(a,[x for x in cs if x is not a])&ht]
            if mine and all(x.ref or x.used or (x.derived and x.kept!='converted') for x in cs if x not in mine) and not any(_distinct(x,mine)&ht for x in cs if x not in mine):cs=mine
        if len(cs)<2:
            if len(cs)==1 and cs[0].derived:return _ask(spec,tg,cs[0],steps,ctx)
            no('TOTAL_OF_ONE')
        roles={_kind(a) for a in cs}
        if len(roles)>1:no('TOTAL_OF_MIXED:'+','.join(sorted(roles)))
        d=_d(spec,tg.u,' + '.join(a.name for a in cs),qs,frozenset().union(*[a.tags for a in cs]),cs,role='total')
        steps.append('total');return _ask(spec,tg,d,steps,ctx)
    if mode in ('now','left') and not (len(live)==1 and live[0].derived and not any(a.zero or a.role in ('gain','loss') for a in cs)):
        return _holding(spec,tg,cs,steps,ctx)
    if mode=='need':
        if len(live)!=2:no('NEED_NOT_TWO')
        goal=[a for a in live if a.role=='goal']
        if not goal:
            # 'A hiking trail is 12 miles long. Rita has walked 5 miles of it': what is had or done, and the whole wanted
            have=[a for a in live if a.role in ('act','gain') or a.verb in ('have','has','had','saved')]
            if len(have)==1:goal=[a for a in live if a is not have[0]]
            else:goal=[a for a in live if a.role=='state' and a.lead in ('a','an','the','one','this','that','each','every')]
        have=[a for a in live if a not in goal]
        if len(goal)!=1 or len(have)!=1:no('NEED_GOAL_NOT_TOLD')
        d=_d(spec,tg.u,f'{goal[0].name} - {have[0].name}',qs,goal[0].tags,live,role='need');steps.append('need')
        return _ask(spec,tg,d,steps,ctx)
    if mode=='diff':
        if len(live)!=2:no('DIFF_NOT_TWO')
        a,b=live
        big=ctx.get('diff_order')
        if big is None:no('DIFF_ORDER')
        x,y=(a,b) if big(a,b) else (b,a)
        d=_d(spec,tg.u,f'{x.name} - {y.name}',qs,x.tags,live,role='diff');steps.append('diff')
        return _ask(spec,tg,d,steps,ctx)
    if mode=='change':
        # two states and the question asks what went (or came) between them
        st=[a for a in live if a.role=='state']
        if len(st)!=2 or len(live)!=2:no('CHANGE_NOT_TWO_STATES')
        a,b=sorted(st,key=lambda x:x.order)
        sn=ctx.get('sents') or []
        nm=lambda x:_names(sn[x.sent]) if x.sent is not None and x.sent<len(sn) else set()
        if nm(a) and nm(b) and nm(a)!=nm(b):no('CHANGE_OF_TWO_HOLDERS')
        sign=ctx.get('qsign')
        if sign=='loss':d=_d(spec,tg.u,f'{a.name} - {b.name}',qs,a.tags,live,role='change')
        elif sign=='gain':d=_d(spec,tg.u,f'{b.name} - {a.name}',qs,a.tags,live,role='change')
        else:no('CHANGE_SIGN')
        steps.append('change');return _ask(spec,tg,d,steps,ctx)
    if mode=='rest':
        # 'A box of 28 crayons has 13 broken ones. How many crayons are not broken?': the whole less the part said so
        if len(live)!=2:no('REST_NOT_TWO')
        adj=ctx.get('notadj')
        part=[a for a in live if adj and (adj in a.adjs or adj in a.tags or (a.verb or '')==adj or adj in (a.span or ''))];whole=[a for a in live if a not in part]
        if len(part)!=1 or len(whole)!=1 or whole[0].order>part[0].order:no('REST_WHOLE')
        d=_d(spec,tg.u,f'{whole[0].name} - {part[0].name}',qs,whole[0].tags,live,role='rest');steps.append('rest')
        return _ask(spec,tg,d,steps,ctx)
    # the whole less its container: 'A crate of oranges weighs 18 kg. The empty crate weighs 2 kg. How much do the oranges weigh?'
    box=[a for a in live if a.kept=='container']
    if len(live)==2 and len(box)==1 and mode in ('amount',):
        whole=[a for a in live if a is not box[0]][0]
        if tg.tags&_distinct(whole,box) and not tg.tags&_distinct(box[0],[whole]):
            d=_d(spec,tg.u,f'{whole.name} - {box[0].name}',qs,whole.tags,live,role='rest');steps.append('container')
            return _ask(spec,tg,d,steps,ctx)
    # one amount of the asked unit that a law made, the others it was made from
    if len(live)==1 and live[0].derived:
        a=live[0]
        rest=[x for x in cs if x is not a]
        if tg.tags and rest:
            # the question names the one asked: what tells it from the others must be in the question, and nothing of theirs
            mine=_distinct_full(a,rest);theirs=frozenset().union(*[_distinct_full(x,[a]) for x in rest])
            if theirs&tg.tags and not mine&tg.tags:no('ASKS_ANOTHER_HOLDER')
            if theirs&tg.tags and mine&tg.tags:no('ASKS_WHICH_HOLDER')
        return _ask(spec,tg,a,steps,ctx)
    if len(live)==2 and all(a.derived for a in live) is False and any(a.derived for a in live) and tg.tags:
        pass
    # the question names one of several amounts: the one whose words it has, and not another's
    if len(cs)>=2 and tg.tags:
        pick=[a for a in cs if _distinct_full(a,[x for x in cs if x is not a])&tg.tags]
        if len(pick)==1 and pick[0].derived and all(x.ref or x.used or (x.derived and x.kept!='converted') for x in cs if x is not pick[0]) and \
                not any(_distinct_full(x,[pick[0]])&tg.tags for x in cs if x is not pick[0]):
            return _ask(spec,tg,pick[0],steps,ctx)
    no('NO_LAW_FOR_THE_QUESTION')


def _kind(a):
    if a.role in ('gain','loss'):return 'event:'+str(a.verb or '')
    if a.role in ('act',):return 'act:'+str(a.verb or '')
    return 'amount'


def _holding(spec,tg,cs,steps,ctx):
    """what there is now: a start told (or said to be none), what came, what went"""
    cs=sorted(cs,key=lambda a:a.order)
    starts=[a for a in cs if a.role in ('state','whole') or a.zero]
    events=[a for a in cs if a not in starts]
    if not starts and tg.mode=='left' and events and events[0].role=='gain' and not events[0].more and len(events)>1 and \
            all(a.role=='loss' for a in events[1:]):
        # 'bought 2 dozen eggs and used 9 of them. How many eggs does she have left?': what is left of what came
        starts=[events[0]];events=events[1:]
    if len(starts)!=1:no('HOLDING_START:'+str(len(starts)))
    s=starts[0]
    # the question asks about the holder of the start, not another one the story names; what happened was done by that
    # holder (or to a place: 'The fish tank had 22 fish. Ben added 8 more fish')
    sn=ctx.get('sents') or []
    own=_names(sn[s.sent]) if s.sent is not None and s.sent<len(sn) else set()
    if own:
        for a in events:
            other=_names(sn[a.sent]) if a.sent is not None and a.sent<len(sn) else set()
            if other and not other&own:no('AN_EVENT_OF_ANOTHER_HOLDER')
    for nm in ctx.get('qnames') or ():
        if s.sent is not None and s.sent<len(sn) and nm not in sn[s.sent] and any(nm in x for i,x in enumerate(sn[:-1]) if i!=s.sent):
            no('ASKS_ANOTHER_HOLDER')
    if any(a.order<s.order for a in events):no('HOLDING_EVENT_BEFORE_START')
    if any(a.role not in ('gain','loss') for a in events):no('HOLDING_NOT_AN_EVENT')
    if not events:no('HOLDING_NOTHING_HAPPENED')
    if s.zero:
        if any(a.role=='loss' for a in events):no('HOLDING_LOSS_FROM_NONE')
        expr=' + '.join(a.name for a in events)
    else:
        expr=s.name+''.join((' + ' if a.role=='gain' else ' - ')+a.name for a in events)
    d=_d(spec,tg.u,expr,ctx['qspan'],s.tags,cs,role='now');steps.append('holding')
    return _ask(spec,tg,d,steps,ctx)


def _geometry(spec,tg,cs,steps,ctx):
    live=[a for a in cs if not a.ref]
    if tg.geo=='perimeter' and ctx.get('shape') in ('triangle','polygon_sides') and len(live)>=3:
        d=_d(spec,tg.u,' + '.join(a.name for a in live),ctx['qspan'],frozenset(),live,role='perimeter');steps.append('perimeter')
        return _ask(spec,tg,d,steps,ctx)
    if tg.geo=='perimeter' and ctx.get('shape')=='square' and len(live)==1:
        k=spec.known(tg.u,'side',4,'a square has 4 sides of the same length');k_=k
        d=_d(spec,tg.u,f'{k_} * {live[0].name}',ctx['qspan'],frozenset(),live,role='perimeter');steps.append('perimeter')
        return _ask(spec,tg,d,steps,ctx)
    if tg.geo=='perimeter' and ctx.get('shape')=='rectangle' and len(live)==2:
        d=_d(spec,tg.u,f'{live[0].name} + {live[1].name} + {live[0].name} + {live[1].name}',ctx['qspan'],frozenset(),live,role='perimeter')
        steps.append('perimeter');return _ask(spec,tg,d,steps,ctx)
    no('GEOMETRY_NOT_READ')


def _ask(spec,tg,a,steps,ctx):
    if not a.derived:no('ANSWER_IS_A_NUMBER_OF_THE_TEXT')
    return a.name,'+'.join(steps) or 'one'


def area(spec,tg,cs,ctx):
    """N U by M U, a rectangle N long and M wide: the area in U^2"""
    live=[a for a in cs if not a.ref and not a.used]
    if len(live)!=2 or live[0].u!=live[1].u:no('AREA_NOT_TWO_SIDES')
    for a in live:a.used=True
    n=spec.rel(f'{live[0].u}^2',f'{live[0].name} * {live[1].name}',ctx['qspan'],whole=False)
    return n


# ============================================================================= English
from .reader_en import sentences as _sentences,tokens as _tokens,sing as _sing,V,GAIN,LOSE,JOIN,LEAVE,TRANSFER,HAVE,BE,ACT,COST,PRON,DET,PREP,CONJ
_EU={}
for _c,_ws in (('centimeter','centimeter centimeters centimetre centimetres cm'),('meter','meter meters metre metres m'),
               ('kilometer','kilometer kilometers kilometre kilometres km'),('millimeter','millimeter millimeters mm'),
               ('mile','mile miles'),('inch','inch inches'),('foot','foot feet ft'),('yard','yard yards'),
               ('gram','gram grams g'),('kilogram','kilogram kilograms kg'),('pound','pound pounds lb lbs'),('ounce','ounce ounces oz'),
               ('ton','ton tons'),('liter','liter liters litre litres'),('milliliter','milliliter milliliters millilitre millilitres ml'),
               ('gallon','gallon gallons'),('quart','quart quarts'),('pint','pint pints'),
               ('year','year years'),('month','month months'),('week','week weeks'),('day','day days'),('hour','hour hours'),
               ('minute','minute minutes'),('second','second seconds'),('dollar','dollar dollars bucks'),('cent','cent cents')):
    for _w in _ws.split():_EU[_w]=_c
LENGTH={'centimeter','meter','kilometer','millimeter','mile','inch','foot','yard'}
WEIGHT={'gram','kilogram','pound','ounce','ton'}
VOLUME={'liter','milliliter','gallon','quart','pint'}
TIME={'year','month','week','day','hour','minute','second'}
MONEY={'dollar','cent'}
EN_MEASURE=LENGTH|WEIGHT|VOLUME|TIME|MONEY|{'degree'}
EN_CONV={('meter','centimeter'):(100,'100 centimeters in a meter'),('kilometer','meter'):(1000,'1000 meters in a kilometer'),
         ('meter','millimeter'):(1000,'1000 millimeters in a meter'),('centimeter','millimeter'):(10,'10 millimeters in a centimeter'),
         ('kilogram','gram'):(1000,'1000 grams in a kilogram'),('liter','milliliter'):(1000,'1000 milliliters in a liter'),
         ('hour','minute'):(60,'60 minutes in an hour'),('minute','second'):(60,'60 seconds in a minute'),('day','hour'):(24,'24 hours in a day'),
         ('week','day'):(7,'7 days in a week'),('year','month'):(12,'12 months in a year'),('foot','inch'):(12,'12 inches in a foot'),
         ('yard','foot'):(3,'3 feet in a yard'),('gallon','quart'):(4,'4 quarts in a gallon'),('dollar','cent'):(100,'100 cents in a dollar'),
         ('pound','ounce'):(16,'16 ounces in a pound'),('yard','inch'):(36,'36 inches in a yard'),('mile','foot'):(5280,'5280 feet in a mile')}
def _econv(a,b):return EN_CONV.get((a,b))

def _cu(w):
    w=(w or '').lower().strip()
    return _EU.get(w) or _sing(w)

# a verb said of an amount, and which way it changes a holding
E_GAIN=(GAIN|JOIN|V('picked|added|hatched|born|arrived|received|got|gained|caught|found|bought|collected|earned|baked|made|grew|planted|saved'))-V('cut|cuts|took|takes|put|puts|make|makes|draw|drew|write|wrote|paint|painted')
E_LOSS=(LOSE|TRANSFER|V('moved|eaten|given|taken|broken|thrown|lost|used|sold|spent|popped|removed|died|escaped|flew|left|gave|ate|cuts|trims|trimmed|chops|chopped'))-V('share|shares|shared')
E_STATE=HAVE|BE|V('weighs|weigh|weighed|measures|measured|costs|cost|holds|hold|contains|lasts|lasted|takes|take|took|fills|fill|filled')
COMPAR={'less':'-','fewer':'-','more':'+','younger':'-','older':'+','shorter':'-','taller':'+','longer':'+','heavier':'+','lighter':'-',
        'cheaper':'-','smaller':'-','bigger':'+','larger':'+','higher':'+','lower':'-','faster':'+','slower':'-','farther':'+','further':'+',
        'deeper':'+','wider':'+','narrower':'-','thinner':'-','thicker':'+'}
STOPW=PRON|DET|PREP|CONJ|V('is|are|was|were|be|been|has|have|had|will|would|can|could|should|must|did|does|do|not|than|as|times|each|every|per|apiece',
                         'now|then|left|altogether|together|total|in|all|both|only|just|also|still|again|evenly|equally|more|less|fewer|long|tall',
                         'old|high|wide|deep|far|away|much|many|how|what|which|there|here|ones|one')|set(COMPAR)
EN_FUNC=STOPW|V('how|many|much|what|find|the|of|in|did|does|do|is|are|was|were|will|would|be|for|to|a|an|and|or|its|their|his|her|it','total',
                'number','amount','altogether','left','now','after','before','both','sum','each','per','one','all','there','that','this','these','those',
                'can','could','must','should','need','needs','with','by','at','on','from','into','if','so','than','much','many','more','fewer','less')
ZERO_START=re.compile(r"\b(?:start(?:s|ed)? (?:out )?(?:empty|with (?:none|nothing|no \w+))|(?:was|were|is|are) (?:completely )?empty|(?:had|has|have) no \w+ (?:at first|to (?:start|begin) with)|nobody|no one was)\b",re.I)


VAGUE_EN=re.compile(r"\b(?:some|several|a few|few|a couple|many|a lot|lots|a while|a bit|a number of|plenty|numerous|various|a handful|"
                    r"more than one|any)\b(?!\s+of\s+(?:the|them|those|these|it|his|her|their)\b)",re.I)
NOT_MINE_Q=re.compile(r"\b(?:about|approximately|roughly|estimate|round(?:ed)?|nearest|shortest|longest|least|most|greatest|smallest|largest|"
                      r"fewest|minimum|maximum|same|equal|equally|average|mean)\b",re.I)


def _verbish(w):
    return w in E_GAIN or w in E_LOSS or w in E_STATE or w in ACT or w in COST or (w.endswith('ed') and len(w)>4 and w not in ('red','bed','seed','need','speed','feed','weed','shed','sled','hundred','bread'))


class _Sent:
    def __init__(s,text,a,b,nums,idx):
        s.a=a;s.b=b;s.idx=idx;s.t=_tokens(text,a,b,nums);s.low=text[a:b].lower()


def read_en(text):
    try:return _read_en(text)
    except NoRead as e:return {'spec':None,'reason':'UNITS:'+str(e)}
    except Exception as e:  # noqa: BLE001 - a fault of this reader is no reading, never a crash of the solve
        return {'spec':None,'reason':'UNITS:INTERNAL:'+type(e).__name__}


def _read_en(text):
    nums=N.find(text);ss=_sentences(text)
    if not ss or not nums:no('NOTHING')
    sents=[_Sent(text,a,b,nums,i) for i,(a,b) in enumerate(ss)]
    q=sents[-1];qt=text[q.a:q.b].strip()
    if not (qt.endswith('?') or re.match(r'\s*(?:find|calculate|determine|what|how)\b',qt,re.I)):no('NO_QUESTION')
    # what these laws do not read: an estimate, the least or greatest of something, making amounts the same, 'up to N'
    if NOT_MINE_Q.search(qt):no('QUESTION_NOT_FOR_THESE_LAWS')
    if re.search(r'\bup to\s+\$?\d',text,re.I):no('UP_TO')
    stm_t=text[:q.a]
    # an amount not said ('some girls', 'for a while', 'a few'), an event that undoes another without a number ('gave them back')
    if VAGUE_EN.search(stm_t):no('AN_AMOUNT_NOT_SAID')
    for mb in re.finditer(r'\b(?:back|returned|returns|return)\b',stm_t,re.I):
        near=stm_t[max(0,mb.start()-25):mb.end()+12]
        if not re.search(r'\d',near):no('AN_EVENT_WITHOUT_AMOUNT')
    # things bought or wanted that have no price ('a ball and a $45 bike', 'a pencil for 15 cents and an eraser')
    for a0,b0 in ss[:-1]+[ss[-1]]:
        sen=text[a0:b0]
        if re.search(r'\b(?:buy|buys|bought|purchase[sd]?|order(?:s|ed)?|want(?:s|ed)? to buy|pay(?:s)? for|paid for)\b',sen,re.I):
            items=len(re.findall(r'\b(?:a|an|one)\s+(?:\$\d[\d.,]*\s+)?[a-z]+',sen,re.I));prices=len(re.findall(r'\$\s*\d|\d[\d.,]*\s*(?:dollars?|cents?)\b',sen,re.I))
            if items>=2 and prices and items>prices:no('AN_ITEM_WITHOUT_PRICE')
    if len(set(re.findall(r'\b(triangle|square|rectangle|circle|pentagon|hexagon|cube|polygon)s?\b',text,re.I)))>1:no('TWO_SHAPES')
    amts=[];order=0;clock=[]
    for s in sents:
        skip=set()
        for i,t in enumerate(s.t):
            if t.kind!='num' or i in skip:continue
            n=t.num
            if n.kind=='ordinal' or N.optional(n,text) and not _one_is_base(s,i):continue
            if re.match(r"\s*(?:o'clock|o’clock|a\.m\.|p\.m\.|am\b|pm\b)",text[n.end:n.end+8],re.I) or re.match(r':\d\d',text[n.end:n.end+3]):
                clock.append(n.raw);continue
            a=_amount(text,s,i,sents);a.order=order;order+=1;a.inq=s is q;a.k=nums.index(n)
            amts.append(a)
            if a.dozen:
                dn,thing,sp=a.dozen;skip.add(i+1)
                if not thing:no('DOZEN_OF_WHAT')
                amts.append(Amt(kind='rate',v=dn.value,raw=dn.raw,u=thing,per='dozen',span=sp,sent=s.idx,order=order,inq=a.inq,pos=dn.start,end=dn.end))
                order+=1
    if not amts:no('NO_AMOUNTS')
    tg=_question_en(text,q,amts,sents)
    _resolve_en(text,amts,sents,tg)
    spec=Spec(text,'en',lambda u:(u or '') not in EN_MEASURE and '^' not in (u or ''))
    for raw in clock:spec.unused.append({'raw':raw,'why':'a time of day, not an amount'})
    # 'in a week' with a rate each night: what everyone knows of a week, a day, an hour, a year
    pm=re.search(r"\b(?:in|during|over|for)\s+(?:a|an|one)\s+(week|day|hour|year|minute|month)\b",qt,re.I)
    if pm and not any(a.inq and a.kind=='count' for a in amts):
        big=pm.group(1).lower();rates=[a for a in amts if a.kind=='rate' and a.per]
        per={'night':'day','morning':'day','evening':'day','afternoon':'day'}
        if len(rates)==1 and _econv(big,per.get(rates[0].per,rates[0].per)):
            ctx_period=(big,rates[0])
        else:ctx_period=None
    else:ctx_period=None
    ctx={'qspan':qt,'convert':_econv,'notadj':tg.notadj,'sents':[text[x.a:x.b] for x in sents],
         'equal':bool(re.search(r'\b(?:evenly|equally|equal|the same (?:number|amount))\b',text,re.I)),
         'qnames':[w for w in re.findall(r"(?<=[a-z,] )([A-Z][a-z]+)",qt) if w not in ('I',)]}
    # a question about what there is (are, is, have) after things came or went: what there is now
    if tg.mode=='amount' and not tg.per and re.search(r"\bhow (?:many|much)\b[^?]*\b(?:are|is)\b(?! being)|\b(?:does|do)\b[^?]*\bhave\b|\bhas\b",qt,re.I) and \
            any(a.role in ('gain','loss') for a in amts if a.kind=='count'):
        tg.mode='now'
    for shape in ('triangle','square','rectangle'):
        if re.search(r'\b'+shape+r's?\b',text,re.I):ctx['shape']=shape
    if tg.mode=='diff':ctx['diff_order']=tg.kind
    if tg.mode=='change':ctx['qsign']=tg.verb
    ctx['fact']=_fact_en;ctx['period']=ctx_period
    if tg.u=='year':
        for a in amts:
            if a.inq and a.kind=='count' and a.u=='year':
                if re.search(r'\b(?:in|after)\s+$',text[max(0,a.pos-6):a.pos],re.I) or re.match(r'\s*years?\s+(?:from now|later)',text[a.end:a.end+20],re.I):a.kept='shift+'
                elif re.match(r'\s*years?\s+ago',text[a.end:a.end+12],re.I):a.kept='shift-'
    # 'Kim had 4 dollars and 50 cents. How many cents does she have?': what was had, asked of now, with nothing told between
    past=[a for a in amts if a.kind=='count' and not a.inq]
    if tg.mode in ('amount','now') and re.search(r"\b(?:does|do)\b[^?]*\bhave\b|\b(?:has|have)\b",qt,re.I) and not re.search(r"\b(?:did|had|was|were)\b",qt,re.I) and \
            past and all((a.verb or '') in ('had','was','were','owned','kept','held') for a in past):
        no('ASKS_NOW_OF_WHAT_WAS')
    if ZERO_START.search(text):
        amts.append(Amt(kind='count',u=tg.u,zero=True,role='state',order=-1,tags=frozenset(),span=qt))
    if tg.geo=='area':
        if re.search(r'\b(?:triangle|trapezoid|circle|parallelogram|rhombus)s?\b',text,re.I):no('AREA_OF_ANOTHER_SHAPE')
        for a in amts:spec.bind(a) if not a.zero else None
        live=[a for a in amts if a.kind=='count' and not a.zero]
        if len(live)!=2 or live[0].u!=live[1].u or live[0].u not in LENGTH or len(amts)!=2:no('AREA_NOT_TWO_SIDES')
        if live[0].u!=tg.u:no('AREA_IN_ANOTHER_UNIT')
        n=spec.rel(f'{live[0].u}^2',f'{live[0].name} * {live[1].name}',qt,whole=False)
        ask,form=n,'area'
    else:
        real=[a for a in amts if not a.zero]
        ask,form=compose(text,'en',real,tg,spec,ctx) if not any(a.zero for a in amts) else _compose_zero(text,amts,tg,spec,ctx)
    return {'spec':spec.done(ask,form)}


def _compose_zero(text,amts,tg,spec,ctx):
    z=[a for a in amts if a.zero][0];real=[a for a in amts if not a.zero]
    for a in real:spec.bind(a)
    pool=real+[z]
    for a in pool:a.used=False
    if any(a.kind!='count' for a in real):no('ZERO_START_WITH_RATES')
    return _whole(spec,Tgt(u=tg.u,mode='now',tags=tg.tags,per=None,geo=None),pool,[],ctx)


def _one_is_base(s,i):
    """'One foot is 12 inches': the 1 is the base of a rate, bound with it"""
    nxt=[t for t in s.t[i+1:i+5]]
    return bool(s.t[i].num.value==1 and nxt and nxt[0].kind=='word' and _cu(nxt[0].low) in EN_MEASURE|{_sing(nxt[0].low)} and
                any(t.kind=='word' and t.low in ('is','equals','has','makes') for t in nxt[1:3]))


def _np(s,i):
    """the noun phrase right after token i: (head, adjectives, stuff, index after it)"""
    j=i+1;ws=[]
    while j<len(s.t):
        t=s.t[j]
        if t.kind!='word':break
        w=t.low
        if w in ('more','fewer','less') and not ws and j+1<len(s.t) and s.t[j+1].kind=='word' and s.t[j+1].low not in STOPW and not _verbish(s.t[j+1].low):j+=1;continue
        if w in ('ones','one') and ws:ws.append(w);j+=1;break
        nx=s.t[j+1].low if j+1<len(s.t) and s.t[j+1].kind=='word' else None
        if not ws and re.search(r'(?:en|ed)$',w) and nx and (nx in ('ones','one') or (nx.endswith('s') and _sing(nx)!=nx and nx not in STOPW)):ws.append(w);j+=1;continue
        noun=w.endswith('s') and _sing(w)!=w and not w.endswith('ed')
        if w in STOPW or (_verbish(w) and w not in _EU and not noun) or (w.endswith('ly') and w not in ('family','jelly','belly','lily','fly','butterfly')):break
        ws.append(w);j+=1
        # the phrase ends at its first plural ('5 friends split', '4 quart jars'): what follows is a verb or the rest
        if noun and w not in ('pants','glasses','scissors','clothes','jeans','shorts'):break
    stuff=None
    if ws and j+1<len(s.t) and s.t[j].kind=='word' and s.t[j].low=='of' and s.t[j+1].kind=='word' and s.t[j+1].low not in STOPW:
        stuff=_sing(s.t[j+1].low);j+=2
    if not ws:return None,frozenset(),stuff,j
    return ws[-1],frozenset(_sing(w) for w in ws[:-1]),stuff,j


def _words(s,a=0,b=None):
    return [t.low for t in s.t[a:b] if t.kind=='word']


def _content(ws):
    return frozenset(_sing(w) for w in ws if w not in EN_FUNC and w not in _EU and not w.endswith('ly'))


def _subject(s,i):
    """the words before the first verb of the clause holding token i ('Adult tickets are $14 and child tickets are $9':
    child tickets for the 9)"""
    k=i
    while k>0 and not (s.t[k-1].kind=='punct' and s.t[k-1].w in ',;:'):
        if s.t[k-1].kind=='word' and s.t[k-1].low in ('and','but','while','whereas') and k<i and \
                any(t.kind=='word' and (t.low in ('is','are','was','were','has','have','had') or _verbish(t.low)) for t in s.t[k:i]):break
        k-=1
    ws=[]
    for t in s.t[k:i]:
        if t.kind=='word' and (_verbish(t.low) or t.low in ('is','are','was','were','has','have','had','will','can','does','did')):break
        if t.kind=='word':ws.append(t.low)
        elif t.kind=='num' and t.num.value==1:ws.append('one')
    return ws


def _amount(text,s,i,sents):
    t=s.t[i];n=t.num;money=i>0 and s.t[i-1].kind=='money'
    if i+1<len(s.t) and s.t[i+1].kind=='num' and s.t[i+1].num.raw.lower()=='dozen':
        # '2 dozen eggs': 2 dozens, and the dozen (12 in each) bound as a rate of the thing after it
        head,adjs,stuff,j=_np(s,i+1)
        a=Amt(v=n.value,raw=n.raw,sent=s.idx,kind='count',u='dozen',pos=n.start,end=n.end,adjs=adjs,tags=frozenset([_sing(head)]) if head else frozenset())
        a.span=_span(text,s,i,j);a.verb=next((w for w in reversed(_words(s,0,i)) if _verbish(w) or w in E_STATE),None);a.subj=_subject(s,i)
        a.dozen=(s.t[i+1].num,_cu(head) if head else None,_span(text,s,i+1,j))
        return a
    head,adjs,stuff,j=_np(s,i)
    a=Amt(v=n.value,raw=n.raw,sent=s.idx,kind='count',adjs=adjs,stuff=stuff,pos=n.start,end=n.end)
    w1=_words(s,i+1,i+2);a.more={'more':'+','fewer':'-','less':'-'}.get(w1[0]) if w1 and head and head not in COMPAR else None
    after=_words(s,j,j+6);before=_words(s,max(0,i-6),i)
    a.span=_span(text,s,i,j)
    cut=[m.end() for m in re.finditer(r'[,;]|\bbut\b',text[s.a:n.start])];c0=s.a+(cut[-1] if cut else 0)
    c1=re.search(r'[,;]|\bbut\b|$',text[n.end:s.b]);a.clause=text[c0:n.end+(c1.start() if c1 else 0)]
    # the verb of the amount: right after it (4 penguins were moved), else the nearest before it in its sentence
    vb=None;a.aux=False
    for t2 in s.t[j:j+3]:
        if t2.kind!='word':break
        w=t2.low
        if w in ('were','was','are','is','been','be','got'):a.aux=True;continue
        if _verbish(w) or w in ('left',):vb=w;a.src='after'
        else:a.aux=False
        break
    if vb is None:
        for w in reversed(before+_words(s,0,max(0,i-6))[::-1][:0]):
            if _verbish(w) or w in E_STATE:vb=w;break
        if vb is None:
            for w in reversed(_words(s,0,i)):
                if _verbish(w) or w in E_STATE:vb=w;break
    a.verb=vb
    subj=_subject(s,i);a.subj=subj;a.lead=subj[0] if subj else None
    a.tags=_content(subj)|(_content([head]) if head and _cu(head) not in EN_MEASURE else frozenset())|adjs|(frozenset([stuff]) if stuff else frozenset())
    # the words right after it ('340 tickets on Friday'): up to the next number, 'and', 'than' or a comma
    seg=[]
    for t2 in s.t[j:j+6]:
        if t2.kind!='word' or t2.low in ('and','than','but','or','while'):break
        seg.append(t2.low)
    a.atags=frozenset(w for w in _content(seg) if not _verbish(w))       # only what a comparison points to
    # '3-foot board': a measure of the thing after it
    m=re.match(r'-([A-Za-z]+)',text[n.end:n.end+16])
    if m and _cu(m.group(1)) in EN_MEASURE:
        a.u=_cu(m.group(1));a.tags=a.tags|_content(_words(s,i+1,i+4))
    elif money or (head and _cu(head) in MONEY):
        a.u='dollar' if money else _cu(head)
        if money and head and _cu(head) not in MONEY:
            # '$3 boxes of crackers': a price for each; 'a $75 jacket': the price of one
            if head.endswith('s') and _sing(head)!=head and not (i>1 and s.t[i-2].kind=='word' and s.t[i-2].low in ('a','an','one','the','this','that')):
                a.kind='rate';a.per=_sing(head);a.tags=a.tags|{_sing(head)}
            else:a.tags=a.tags|{_sing(head)}
    elif head:
        a.u=_cu(head)
        if adjs&{'square','cubic'} and a.u in LENGTH:a.u=a.u+('^2' if 'square' in adjs else '^3')
    if 'empty' in _words(s,max(0,i-4),i) or 'empty' in adjs:a.kept='container'
    # 'N of them', 'N of the cookies', 'N broken ones'
    if head in (None,'one','ones') or (head is None and after[:1]==['of']):
        if after[:1]==['of'] and len(after)>1:
            w=after[2] if after[1] in ('the','his','her','their','its','those','these','them') and len(after)>2 and after[1]!='them' else after[1]
            a.u=None if w in ('them','those','these','it') else _cu(w)
        if head in ('one','ones') or (after[:1]==['of'] and a.u is None):a.u=None;a.stuff='@antecedent'
        elif a.u is None:a.stuff='@bare'
    # what the number is: a rate, a comparison, a part
    nxt=after
    if nxt[:1]==['per'] and len(nxt)>1:a.kind='rate';a.per=_cu(nxt[1])
    elif nxt[:1] in (['a'],['an']) and len(nxt)>1 and nxt[1] not in STOPW and not _verbish(nxt[1]) and j+1<len(s.t) and s.t[j+1].kind=='word':a.kind='rate';a.per=_cu(nxt[1])
    elif nxt[:2] in (['in','each'],['on','each'],['for','each'],['to','each'],['into','each'],['with','each']) and len(nxt)>2:
        if nxt[2]=='of':a.kind='rate';a.per='@each_of'
        else:a.kind='rate';a.per=_cu(nxt[2])
    elif nxt[:1] in (['every'],['each']) and len(nxt)>1 and nxt[1] not in STOPW and not _verbish(nxt[1]):a.kind='rate';a.per=_cu(nxt[1])
    elif nxt[:2]==['to','a'] and len(nxt)>2 and head is None:a.kind='rate';a.per=_cu(nxt[2]);a.u=a.u or '@subject'
    elif nxt[:1]==['apiece'] or (nxt[:1]==['each'] and (len(nxt)==1 or nxt[1] in STOPW)):a.kind='rate';a.per='@receiver'
    # 'Three friends each brought 12 sandwiches': each before the verb
    if a.kind=='count':
        bw=_words(s,max(0,i-4),i)
        if 'each' in bw and bw.index('each')<len(bw)-1 and bw[bw.index('each')-1:bw.index('each')] and not any(w in ('of','in','on','for') for w in bw[bw.index('each')-1:bw.index('each')]):
            a.kind='rate';a.per='@each_subject'
    # comparisons: '3 pounds less than the puppy', '6 times as much', 'half as long', '175 more tickets ... than on Friday'
    cw=[w for w in after[:4]]
    comp=next((w for w in (([head] if head in COMPAR else [])+cw[:2]) if w in COMPAR),None)
    if head in COMPAR:a.u=None
    rest=_words(s,j,None)
    if n.raw.lower() in ('twice','double','triple') or (cw[:1]==['times'] and len(cw)>1 and cw[1] in ('as','more')):
        a.kind='cmp';a.op='*';a.u=None
        if cw[:1]==['times']:a.tags=_content(subj)
    elif n.value<1 and cw[:1]==['as'] and n.kind=='word':a.kind='cmp';a.op='*';a.u=None;a.tags=_content(subj)
    elif a.more and 'than' in rest[:8] and a.kind=='count':
        a.kind='cmp';a.op=a.more;comp='more' if a.more=='+' else 'fewer'
    elif comp and (('than' in rest[:8]) or not any(x in rest[:3] for x in ('of',))):
        if a.kind=='count' or a.kind=='rate':
            a.kind='cmp';a.op=COMPAR[comp]
            if a.u is None and head not in COMPAR:a.u=None
    if a.kind=='cmp':
        th=rest.index('than') if 'than' in rest else None
        a.of=('@than',tuple(_content(rest[th+1:th+5]))) if th is not None else ('@prev',None)
        a.tags=_content(subj)|(_content(rest[:th]) if th is not None else frozenset())
        if comp in ('older','younger') and a.u is None:a.u='year'
    # parts: 'one third of the 36 cupcakes', 'one fifth off'
    if n.value<1 and a.kind=='count' and n.kind in ('word','digits'):
        if after[:1]==['of']:
            a.kind='frac';a.tags=_content(subj)
            ahead=text[n.end:n.end+40]
            if re.match(r"\s+of\s+(?:the\s+|his\s+|her\s+|their\s+|its\s+|these\s+|those\s+)?\$?\d",ahead):a.of='@next'
            elif re.match(r"\s+of\s+(?:it|them|those|these)\b",ahead,re.I):a.of='@prev'
            else:no('PART_OF_AN_AMOUNT_NOT_GIVEN')
        elif after[:1]==['off']:a.kind='frac';a.op='off';a.of='@price'
    if a.kind=='count' and a.u is None and head is None and a.stuff is None:a.stuff='@bare'
    return a


def _span(text,s,i,j):
    t0=s.t[max(0,i-3)].s;t1=s.t[min(len(s.t)-1,max(i,j-1))].e
    return text[t0:t1].strip()


def _resolve_en(text,amts,sents,tg):
    """what each amount's words leave open: the thing of 'N of them', a bare number, what a rate or comparison is of"""
    for x,a in enumerate(amts):
        s=sents[a.sent]
        if a.kind in ('count','rate') and (a.stuff=='@antecedent' or a.stuff=='@bare'):
            prev=[b for b in amts[:x] if b.u and b.kind in ('count','rate')]
            # a list: 'sides of 5, 6 and 7 centimeters'
            later=[b for b in amts[x+1:] if b.sent==a.sent and b.u]
            gap=text[a.end:later[0].pos] if later else ''
            if later and re.fullmatch(r'[\s\d,]*(?:,|\band\b|\bor\b)[\s,]*',gap or 'x') :a.u=later[0].u;a.stuff=None;continue
            low=s.low
            ws=_words(s)
            if a.stuff=='@bare' and prev:
                # 'This week it sold 31': the thing of the same verb before
                same=[b for b in prev if b.verb and a.verb and b.verb==a.verb and b.kind=='count']
                if same:a.u=same[-1].u;a.stuff=None;a.tags=a.tags|same[-1].tags;continue
                # 'Mr. Park is 41': an age, when ages are told or asked
                if a.verb in ('is','was','are','were') and (tg.u=='year' or any(b.u=='year' for b in amts)):a.u='year';a.stuff=None;continue
                # 'packs of 4' (the thing of the sentence per pack)
            if a.stuff=='@antecedent' and prev:a.u=prev[-1].u;a.stuff=None;continue
            if a.stuff=='@bare':
                bw=_words(s,0,None)
                m=re.search(r'\b(\w+) of '+re.escape(a.raw.lower())+r'\b',low)
                if m:
                    cont=_sing(m.group(1));thing=_thing_of(s,amts,a)
                    if thing:a.kind='rate';a.u=thing;a.per=cont;a.stuff=None;continue
                if a.verb in ('is','was','are','were') and (tg.u=='year' or any(b.u=='year' for b in amts) or re.search(r'\b(?:age|old)\b',text,re.I)):
                    a.u='year';a.stuff=None;continue
            no('AMOUNT_OF_WHAT:'+str(a.raw))
        if a.u=='@subject':
            thing=_thing_of(sents[a.sent],amts,a)
            if not thing:no('RATE_OF_WHAT')
            a.u=thing
        if a.kind=='rate' and a.u is None:
            thing=_thing_of(sents[a.sent],amts,a)
            if not thing:no('RATE_OF_WHAT')
            a.u=thing
        if a.kind=='rate' and a.per=='@each_of':
            nxt=[b for b in amts[x+1:] if b.sent==a.sent]
            if not nxt or nxt[0].kind!='count':no('EACH_OF_WHAT')
            a.per=nxt[0].u
        if a.kind=='rate' and a.per in ('@receiver','@each_subject'):
            cs=[b for b in amts if b.sent==a.sent and b is not a and b.kind=='count' and b.u!=a.u]
            if not cs and a.per=='@receiver':
                sw=[w for w in _subject(s,_tok_index(s,a)) if w not in EN_FUNC]
                if sw and sw[-1].endswith('s') and _sing(sw[-1])!=sw[-1]:a.per=_cu(sw[-1]);a.src='subject_each';continue
            if len(cs)!=1:no('EACH_WHO')
            a.per=cs[0].u
    # the subject of a sentence 'A glass holds 250 milliliters', 'One foot is 12 inches', 'Adult tickets are $14'
    for a in amts:
        if a.kind!='count' or a.inq and False:continue
        s=sents[a.sent];subj=_subject(s,_tok_index(s,a))
        if not subj:continue
        lead=subj[0];head=subj[-1]
        if head in ('rent','price','cost','fee','fare','charge','rate','toll') and len(subj)>=2 and subj[-2] not in EN_FUNC:head=subj[-2];subj=subj[:-1]
        if 'of' in subj:
            head=subj[subj.index('of')-1] if subj.index('of')>0 else head
        verb=next((t.low for t in s.t if t.kind=='word' and (t.low in E_STATE or t.low in ('fills','makes','gives','holds','carries'))),None)
        if a.verb in ('holds','hold','held','contains','contained','has','had','fills','filled','makes','made','is','was','weighs','weighed','costs','cost',
                      'carries','carried','are','were','measures','lasts','gets','earns','pays','charges','uses','needs','takes','serves','feeds') and \
                (lead in ('a','an','one','each','every') or (head.endswith('s') and _sing(head)!=head and a.u in MONEY)):
            per=_cu(head)
            if per==a.u or not per or per in ('it','he','she'):continue
            # 'One cat has only 3 legs': one of them, not each of them
            if re.search(r'\b(?:only|just|but|still|also|even|alone)\b',a.clause or '',re.I):continue
            if lead=='one' and a.verb not in ('is','equals','makes'):continue
            if lead in ('a','an','one','each','every') or a.u in MONEY:
                adj=[_sing(w) for w in subj[:-1] if w not in ('a','an','one','each','every','the') and w not in EN_FUNC]
                if 'of' in subj:adj=[]
                a.kind='rate';a.per=(' '.join(adj+[per]) if a.u in MONEY and adj else per);a.src='subject'
                # 'One foot is 12 inches': the 1 is the rate's base
                one=[b for b in amts if b.sent==a.sent and b.order<a.order and b.v==1 and b.kind=='count' and _cu(b.u or '')==per]
                if one:a.base=one[0]
    # a rate of one thing that nothing else counts is the amount of that one thing ('A video game costs $52',
    # 'A puppy weighs 4 kilograms'), unless the question asks for it or for each one
    for a in amts:
        if a.kind=='rate' and a.src=='subject' and a.base is None:
            if not any(b.kind=='count' and b is not a and _match_per(a.per,b) for b in amts) and tg.u!=a.per and tg.per!=a.per:
                a.kind='count';a.tags=a.tags|frozenset(a.per.split());a.per=None
    # what a comparison and a part are of
    for x,a in enumerate(amts):
        if a.kind=='cmp':
            how,words=a.of
            cs=[b for b in amts[:x]+amts[x+1:] if b.kind=='count' and (a.op in '*/' or b.u==a.u or a.u is None)]
            if how=='@than' and words:
                ws=set(words)
                m=[b for b in cs if ws<=b.tags|(b.atags or frozenset())]
                if len(m)>1:m=[b for b in m if not (b.tags&(a.tags-ws-m[0].tags.intersection(*[x.tags for x in m])))] or m
                if not m and set(words)&{'he','him','she','her','they','them','it'}:m=[b for b in cs if b.order<a.order][-1:]
                if len(m)!=1:
                    m2=[b for b in m if b.sent!=a.sent or b.order<a.order]
                    if len(m2)!=1:no('COMPARED_TO_WHICH')
                    m=m2
                a.of=m[0]
            else:
                prev=[b for b in cs if b.order<a.order]
                if not prev:no('COMPARED_TO_NOTHING')
                a.of=prev[-1]
            if a.u is None and a.op in '+-':a.u=a.of.u
        if a.kind=='frac':
            if a.of=='@next':
                nx=[b for b in amts[x+1:] if b.sent==a.sent and b.kind=='count']
                if not nx:no('PART_OF_NOTHING')
                a.of=nx[0]
            elif a.of=='@prev':
                pv=[b for b in amts[:x] if b.kind=='count']
                if not pv:no('PART_OF_NOTHING')
                a.of=pv[-1]
            elif a.of=='@price':
                pv=[b for b in amts if b.sent==a.sent and b.kind=='count' and b.u in MONEY]
                if len(pv)!=1:no('OFF_WHAT')
                a.of=pv[0]
    for a in amts:
        if a.kind in ('count','rate') and not a.u:no('NO_UNIT')
    _ratios(text,amts,sents)
    for a in amts:
        if a.kind=='count':a.role=_role_en(a)
    # 'Adult train tickets are $14 ... 2 adults': the rate is per what the count counts
    for r in amts:
        if r.kind=='rate' and r.per and ' ' in r.per:
            cs=[c for c in amts if c.kind=='count' and c is not r and _match_per(r.per,c)]
            if len(cs)==1:r.per=cs[0].u


INTENT_EN=re.compile(r"\b(?:plans?|planned|planning|wants?|wanted|hopes?|hoped|wish(?:es|ed)?|will|would|going to|tomorrow|tonight|next|might|may|"
                     r"should|could|intends?|expects?|tries|trying|try|decides? to|is about to|later today)\b",re.I)
def _fact_en(c,u):
    """'a spider has 8 legs' (fpl.KNOWN_FACTS): the number of u one c has, said as the checker reads it"""
    from .fpl import KNOWN_FACTS
    for art in ('a','an'):
        for w in (u+'s',{'foot':'feet'}.get(u,u+'s')):
            said=f'{art} {c.u} has {{}} {w}'
            for k,v in KNOWN_FACTS.items():
                if k.startswith(f'{art} {c.u} has ') and k.endswith(' '+w):return (v,k)
    return None


def _role_en(a):
    """what happened to an amount: 'state' (there was, there is, was left), 'gain', 'loss', 'act' (read, walked); an
    event only planned or wished ('plans to give 4 apples tomorrow') is no event"""
    r=_role_en0(a)
    if r in ('gain','loss','act') and a.clause and INTENT_EN.search(a.clause):return 'intent'
    return r


def _role_en0(a):
    v=a.verb
    if v is None:return 'state'
    if a.src=='after':
        if v=='left':return 'state' if a.aux else 'loss'
        if v in JOIN or v in E_GAIN:return 'gain'
        if v in E_LOSS or v in LEAVE:return 'loss'
        return 'state'
    if v in ('need','needs','needed','want','wants','wanted','requires','required','costs','cost'):return 'goal'
    if a.u in MONEY and (v in ('bought','buys','buy','spent','spends','spend','paid','pays','pay','purchased','ordered','rented') or re.search(r'\bfor\s*\$?\s*$',a.clause[:max(0,(a.clause or '').find(a.raw))] if a.clause else '')):
        return 'loss'
    if a.u in MONEY and v in ('sold','sells','sell','earned','earns','earn','made','makes','received','got','gets','found','saved'):return 'gain'
    if v in E_STATE or v in HAVE:return 'state'
    if v in E_GAIN:return 'gain'
    if v in E_LOSS:return 'loss'
    if v in ACT:return 'act'
    return 'state'


RATIO=re.compile(r"^\s*[a-z]+(?:\s+of\s+[a-z]+)?\s+(?:to (?:make|bake|feed|serve|fill|buy|cook)|makes?|bakes?|serves?|feeds?|fills?|for)\s+$",re.I)
def _ratios(text,amts,sents):
    """'4 cups of flour to make 2 loaves': one amount for another, the rate of the first per the second, when the question
    names another amount of the second ('for 6 loaves')"""
    for a in amts:
        if a.kind!='count' or a.inq:continue
        nxt=[b for b in amts if b.sent==a.sent and b.order==a.order+1 and b.kind=='count']
        if not nxt:continue
        b=nxt[0];between=text[a.end:b.pos]
        if not RATIO.match(between):continue
        if not any(c.inq and c.kind=='count' and c.u==b.u for c in amts):continue
        a.kind='rate';a.per=b.u;a.base=b


def _pos(text,a):
    return a.pos or 0


def _tok_index(s,a):
    for i,t in enumerate(s.t):
        if t.kind=='num' and t.num.raw==a.raw and t.num.value==a.v:return i
    return 0


def _thing_of(s,amts,a):
    """the thing a rate is of when its words do not say: the counted thing of its sentence ('63 eggs are packed 9 to a
    basket', 'Batteries come in packs of 4')"""
    cs=[b for b in amts if b.sent==a.sent and b is not a and b.kind=='count' and b.u and b.u not in EN_MEASURE]
    if len(cs)==1:return cs[0].u
    ws=_subject(s,_tok_index(s,a))
    ws=[w for w in ws if w not in EN_FUNC]
    if ws:return _cu(ws[-1])
    return None


_Q_UNIT=re.compile(r"\b(?:in|,)\s+(?:square\s+)?([a-z]+)\s*[,?.]?",re.I)
def _question_en(text,q,amts,sents):
    low=text[q.a:q.b].lower();ws=_words(q)
    tg=Tgt(mode='amount')
    story_units={a.u for a in amts if a.u}
    m=re.search(r"\bhow (many|much)\s+(?:more\s+|fewer\s+|less\s+)?(?:\$?\d[\d,.]*\s+)?((?:[a-z'-]+\s+){0,3}?)(?:are|is|do|does|did|were|was|will|would|can|could|should|must|have|has|had|went|go|in|on|of|to|for|does|it|he|she|they|we|you)\b",low)
    if not m:m=re.search(r"\bhow (many|much)\s+(?:more\s+|fewer\s+|less\s+)?((?:[a-z'-]+\s*){0,3})\??$",low)
    noun=None
    if m and m.group(2).strip():
        nw=[w for w in m.group(2).split() if w not in ('more','fewer','less','total','extra','of')]
        while nw and nw[-1] in ('long','tall','high','wide','deep','far','old','heavy','away'):nw=nw[:-1]
        if nw:noun=nw[-1];tg.tags=_content(nw[:-1]);tg.np=frozenset(_sing(w) for w in nw)
    mu=re.search(r"\bin\s+(square\s+)?([a-z]+)\s*(?:[,?.]|$)",low) or re.search(r",\s*in\s+(square\s+)?([a-z]+)\s*,",low)
    unit_in=_cu(mu.group(2)) if mu and _cu(mu.group(2)) in EN_MEASURE else None
    sq=bool(mu and mu.group(1))
    if noun and _cu(noun) in EN_MEASURE:tg.u=_cu(noun)
    elif noun and noun in ('money',):tg.u=unit_in or ('cent' if story_units&MONEY=={'cent'} else 'dollar')
    elif noun and m.group(1)=='much':
        st={a.u for a in amts if a.stuff==_sing(noun) or _sing(noun) in a.tags}
        tg.u=unit_in or (st.pop() if len(st)==1 else None);tg.stuff=_sing(noun)
    elif noun:tg.u=_cu(noun)
    if not tg.u:
        mk=re.search(r"\bwhat (?:is|was|will be|would be)\s+(?:(?:the|its|his|her|their|each|every|one|a|an)\s+)?(?:[a-z]+'s\s+)?(?:total\s+)?([a-z]+)(?:\s+of\b)?",low) or \
           re.search(r"\b(?:find|calculate|determine)\s+the\s+(?:total\s+)?([a-z]+)",low)
        mh=re.search(r"\bhow (long|far|tall|high|old|heavy|wide|deep)\b",low)
        kind=mk.group(1) if mk else None
        if kind in ('number','total','sum','amount') :
            mo=re.search(r"\b(?:number|total|sum|amount) of (?:the |their |his |her |its |all |our |my |your )?([a-z]+)",low)
            if mo:tg.u='year' if mo.group(1) in ('ages','age') else _cu(mo.group(1))
        word=kind or (mh.group(1) if mh else None)
        if re.search(r"\bwhat (?:does|did|do|will)\b.*\bcost\b|\bhow much (?:does|did|do|will|would)\b.*\b(?:cost|pay|spend|charge)\b|\bhow much money\b",low):word='cost'
        if re.search(r"\bhow much (?:does|did|do|will|would)\b.*\bweigh\b|\bwhat distance\b",low):word='weight' if 'weigh' in low else 'distance'
        fam={'weight':WEIGHT,'heavy':WEIGHT,'distance':LENGTH,'far':LENGTH,'length':LENGTH,'long':LENGTH|TIME,'tall':LENGTH,'high':LENGTH,
             'height':LENGTH,'wide':LENGTH,'deep':LENGTH,'width':LENGTH,'perimeter':LENGTH,'age':{'year'},'old':{'year'},'cost':MONEY,
             'price':MONEY,'fare':MONEY,'share':MONEY,'discount':MONEY,'charge':MONEY,'bill':MONEY,'change':MONEY,'pay':MONEY,'area':LENGTH}.get(word)
        if word in ('area','perimeter'):tg.geo=word
        if fam:
            if unit_in and unit_in in fam:tg.u=unit_in
            else:
                us=story_units&fam
                if len(us)==1:tg.u=us.pop()
                elif fam=={'year'}:tg.u='year'
                else:no('ASKED_UNIT_NOT_ONE')
        if mk and not tg.u and kind not in ('number','total','sum','amount'):no('QUESTION_FORM')
        tag_ws=re.sub(r"\b(?:what|is|was|the|of|in|find|how|does|did|do)\b",' ',low)
        tg.tags=_content(re.findall(r"[a-z]+",tag_ws))-{word or ''}
    if unit_in and tg.u and tg.u!=unit_in and tg.u in EN_MEASURE:tg.u=unit_in
    if not tg.u:no('ASKED_UNIT')
    if tg.geo=='area' or sq:tg.geo='area';tg.u=unit_in or tg.u
    # who or what the question is about: its words that are not the unit, the question words or the verbs
    tg.tags=tg.tags|_content(re.findall(r"[a-z]+",re.split(r"\s+if\s+",re.split(r",\s*(?=(?:how|what|find)\b)",low)[-1])[0]))
    tg.tags=frozenset(w for w in tg.tags if w!=tg.u and not _verbish(w) and w not in ('long','tall','far','old','weigh','cost','money'))
    # for each one
    asked=re.split(r",\s*(?=(?:how|what|find)\b)",low)[-1]
    asked=re.split(r"\s+if\s+",asked)[0]
    pe=re.search(r"\b(?:each|per|one|a single|every)\s+([a-z]+)(?:'s)?",asked)
    if pe and not re.search(r"\beach of\b",asked):
        per=_cu(pe.group(1))
        if per!=tg.u and per not in EN_FUNC:
            if re.search(r"\b(?:each|per|one|every)\s+"+re.escape(pe.group(1))+r"\b",asked):tg.per=per
    # in what way
    if re.search(r"\bnot\s+([a-z]+)",low) and not re.search(r"\bdo(?:es)? not\b|\bdid not\b",low):tg.mode='rest';tg.notadj=re.search(r"\bnot\s+([a-z]+)",low).group(1)
    elif re.search(r"\bhow (?:many|much) more\b",low) and re.search(r"\b(?:must|need|needs|needed|to finish|to reach|to get|to buy|to have|to make|to complete|left to|still)\b",low):tg.mode='need'
    elif re.search(r"\bhow (?:many|much) (?:more|fewer|less)\b[^?]*\bthan\b|\bhow much (?:older|younger|taller|shorter|longer|heavier|lighter|more expensive|cheaper)\b",low):tg.mode='diff'
    elif re.search(r"\b(?:left|remain|remaining)\b",low):tg.mode='left'
    elif re.search(r"\b(?:still|now|in the end|after both|after all)\b",low):tg.mode='now'
    elif re.search(r"\b(?:total|in all|altogether|all together|together|combined|both|sum|in that week|over both|in all|that day|that week|that month|that year|all day)\b",low):tg.mode='total'
    if re.search(r"\bhow (?:many|much) (?:more|fewer|less)\b",low) and tg.mode not in ('need','diff'):tg.mode='unsure'
    qv=next((w for w in re.findall(r"[a-z]+",asked) if w in E_LOSS or w in E_GAIN),None)
    if tg.mode in ('amount','total','now') and re.match(r"\s*how (?:many|much)\b",asked) and qv and sum(1 for a in amts if a.kind=='count' and not a.inq and a.verb and (a.verb in E_STATE or a.verb=='left'))>=2:
        tg.mode='change';tg.verb='loss' if qv in E_LOSS else 'gain'
    return tg


# ============================================================================= Japanese
# the counters, and one way to write each (the units of the reading); container words a rate may be per ('9こ入りのかご')
from . import reader_ja as _J
_JC=dict(_J._C)
_JC.update({'ぱい':'杯','ばい':'杯','章':'章','しょう':'章','晩':'晩','ばん':'晩','試合':'試合','しあい':'試合','ダース':'ダース','カップ':'カップ',
            'ひき':'匹','びき':'匹','ぴき':'匹','さい':'才','つ':'個','か所':'か所','ヶ所':'か所','m²':'m^2','cm²':'cm^2','km²':'km^2','往復':'往復'})
JCNT='|'.join(sorted(map(re.escape,_JC),key=len,reverse=True))
J_MEASURE={'kg','g','t','km','m','cm','mm','L','mL','dL','時間','分','秒','日','週','か月','年','度','円','才','m^2','cm^2','km^2'}
J_CONV={('m','cm'):(100,'1 m = 100 cm'),('km','m'):(1000,'1 km = 1000 m'),('cm','mm'):(10,'1 cm = 10 mm'),('m','mm'):(1000,'1 m = 1000 mm'),
        ('kg','g'):(1000,'1 kg = 1000 g'),('L','mL'):(1000,'1 L = 1000 mL'),('L','dL'):(10,'1 L = 10 dL'),('dL','mL'):(100,'1 dL = 100 mL'),
        ('t','kg'):(1000,'1 t = 1000 kg'),('時間','分'):(60,'1時間 = 60分'),('分','秒'):(60,'1分 = 60秒'),('週','日'):(7,'1週間 = 7日'),
        ('年','か月'):(12,'1年 = 12か月'),('日','時間'):(24,'1日 = 24時間'),('ダース','個'):(12,'1ダース = 12個')}
def _jconv(a,b):
    if a=='ダース' and b in J_GENERIC:return (12,'1ダース = 12')
    return J_CONV.get((a,b))
J_GAIN=re.compile(_J.PLUS)
J_LOSS=re.compile(_J.MINUS+r'|うつり|移り|うつっ|移っ|出ていき|出て行|切り取り|きりとり|切りとり|売っ')
J_LEFT=re.compile(r'のこ|残')
J_HAVE=re.compile(r'持って|もって|ためて|貯めて|ためました|貯めました')
J_CMP={'多':'+','少な':'-','若':'-','年上':'+','年下':'-','高':'+','低':'-','長':'+','短':'-','重':'+','軽':'-','安':'-','大き':'+','小さ':'-',
       '遠':'+','近':'-','早':'-','おそ':'+','遅':'+','広':'+','せま':'-','狭':'-'}
J_CMPRE='|'.join(sorted(map(re.escape,J_CMP),key=len,reverse=True))
J_TOTAL=re.compile(r'全部で|ぜんぶで|合わせて|あわせて|合計|ごうけい|みんなで|両方|りょうほう|全体で|合わせると|あわせると|この\d+(?:週間|日間|日|か月|年)')
J_NOW=re.compile(r'今(?!日|週|月|年|度|回)|(?:^|、)\s*いま|なりましたか|なりますか|最後|さいご')
J_NEED=re.compile(r'あと\s*何|あと\s*いくら|まだ\s*何|足りな|たりな|必要')
J_DIFF=re.compile(r'(?:何|いくつ|いくら)[^。]*?(?:多い|少ない|多く|少なく|長い|短い|高い|安い|ちがい|違い)|差')
J_FUNC=set('こと もの とき ところ ため よう それ これ その この あの 何 いくつ いくら 全部 ぜんぶ 合計 あと まだ 今 いま 1人 1つ'.split())
J_KANA_FUNC=set('この その あの どの ここ そこ あと まだ もう また など だけ まで から より ので のに けど ても でも とき ころ ほど くらい ぐらい それ これ どれ みな みんな ぜんぶ'.split())
# what is said of a holder (its weight, length, price), not a holder
J_PROP=set('体重 重さ おもさ 長さ ながさ 高さ たかさ 身長 しんちょう ねだん 値段 代金 だいきん 時間 きょり 距離 道のり みちのり 面積 数 かず 点 年れい 年齢 量 速さ はやさ 全長 料金 運賃'.split())


def _jtags(s):
    """the nouns of a clause: what comes before a particle (は が を の に で と も より から)"""
    out=set()
    for m in re.finditer(r'([一-龯ァ-ヶーa-zA-Zぁ-ん々]+?)(?:さん|くん|ちゃん)?(?=は|が|を|の|に|で|と|も|より|から|へ|、)',s):
        w=m.group(1)
        w=re.sub(r'^(?:[ぁ-ん]{1,2})(?=[一-龯ァ-ヶー])','',w)
        w=re.sub(r'(?:入り|いり|だけ|用|たち)$','',w)
        # a word of two kana (なし, かご) only as a whole word, not the end of one ('貝がら' is not 貝 and がら)
        if re.fullmatch(r'[ぁ-ん]{2}',w) and not (m.start()==0 or s[m.start()-1] in '、。はがをにでとのもへや '):continue
        if w and w not in J_FUNC and w not in J_PROP and w not in J_KANA_FUNC and not re.fullmatch(r'[ぁ-ん]',w) and not re.search(r'\d',w) and not w.startswith('何'):out.add(w)
    return frozenset(out)


def read_ja_text(text):
    """the Japanese front end on its own (the guards of reader_ja.read are its caller's)"""
    t=_J._norm(text);sents=_J._sents(t)
    if len(sents)<1:return {'spec':None,'reason':'UNITS:EMPTY'}
    q=_J._question(sents)
    if q is None:return {'spec':None,'reason':'UNITS:NO_QUESTION'}
    r=form_ja(t,sents[:-1],q)
    if isinstance(r,dict):r['text']=text;return {'spec':r}
    return {'spec':None,'reason':'UNITS:'+str(r)}


def form_ja(t,stm,q):
    """a form of reader_ja (its guards are run before it): a reading, or the reason it is not read"""
    try:return _read_ja(t,stm,q)
    except NoRead as e:return str(e)
    except Exception as e:  # noqa: BLE001 - a fault of this reader is no reading, never a crash of the solve
        return 'INTERNAL:'+type(e).__name__


def _jcounter(s,e):
    m=re.match(r'\s*('+JCNT+r')',s[e:])
    return (_JC[m.group(1)],e+m.end()) if m else (None,e)


def _read_ja(t,stm,q):
    if re.search(r'何\s*(?:'+JCNT+r')?\s*目|何番|何位|何時(?!間)|何曜|何月|何日目',q):no('ASKS_A_POSITION')
    if re.search(r'いちばん|一番|最も|もっとも|最大|最小|最低|最高|同じ|ひとしく|平均|およそ|約|四捨五入|切り上げ|切り捨て',q):no('QUESTION_NOT_FOR_THESE_LAWS')
    sents=stm+[q];amts=[];order=0;pos=0;starts=[];restate=[];frames=set()
    # something bought with no amount or price beside what has one ('ペンを3本と消しゴムを買いました')
    for x in stm:
        if re.search(r'買|かい|かっ|注文|払',x) and (re.search(r'\d\s*(?:'+JCNT+r')\s*と\s*[^、。0-9]{1,8}?を',x) or
                                              re.search(r'(?:^|[、をとは])[^、。0-9]{1,8}?と[^、。0-9]{0,8}?\d',x) and not re.search(r'\d[^、。]*と[^、。]*\d',x)):
            no('AN_ITEM_WITHOUT_AMOUNT')
    for si,s in enumerate(sents):
        nums=N.find(s)
        for n in nums:
            if n.kind=='ordinal':continue
            if si==len(sents)-1 and n.value==1 and re.match(r'1\s*(?:'+JCNT+r')(?:の[^\s、。]{1,6}?)?(?:分|あたり|当たり)?(?:は|に|が|には|では)?\s*(?:何|いくら)',s[n.start:]):continue
            fr=re.match(r'1\s*('+JCNT+r')\s*(?:のうち|の中で|のなかで)',s[n.start:])
            if fr and si<len(sents)-1:frames.add(_JC[fr.group(1)]);restate.append(n.raw);continue
            fq=re.match(r'1\s*('+JCNT+r')\s*(?:で|に|では)',s[n.start:])
            if fq and si==len(sents)-1 and n.value==1 and _JC[fq.group(1)] in frames:restate.append(n.raw);continue
            if si==len(sents)-1 and re.search(r'この\s*$',s[:n.start]) and re.match(r'\s*(?:週間|日間|か月|ヶ月|年間|時間|日)',s[n.end:]):
                restate.append(n.raw);continue
            if re.match(r'\s*つの辺',s[n.end:]) and re.search(r'三角形|四角形|長方形|正方形',''.join(sents)):restate.append(n.raw);continue
            a=_jamount(s,si,n,nums,si==len(sents)-1)
            if a is None:continue
            a.order=order;order+=1;amts.append(a)
    if not amts:no('NO_AMOUNTS')
    # '87点から92点にのびました': the value before and the value after the change
    for a,b in zip(amts,amts[1:]):
        if a.verb=='from' and b.sent==a.sent and b.u==a.u and re.match(r'\s*(?:'+JCNT+r')?\s*から\s*$',sents[a.sent][a.end:b.pos]):
            b.role='state';b.verb='to'
    tg=_jquestion(q,amts,sents);_FACT_Q['q']=q
    _jresolve(amts,sents,tg)
    # a question about what there is (…ですか) after things came or went, and a start told: what there is now. The 1 of a
    # rate ('1ぱい50円で') is no start
    st=[a for a in amts if a.kind=='count' and not a.inq and a.role=='state' and a.kept!='base']
    # '水は全部で何dLになりましたか' after water was added: what there is now, not a sum of what was and what came
    if tg.mode=='total' and re.search(r'なりましたか|なりますか|(?:^|、)\s*今',q) and st and any(a.role in ('gain','loss') for a in amts if a.kind=='count' and not a.inq):
        tg.mode='now'
    if tg.mode=='amount' and not tg.per and not any(a.inq for a in amts) and re.search(r'(?:ますか|ですか)[。？?]?$',q) and st and \
            any(a.role in ('gain','loss') for a in amts if a.kind=='count' and not a.inq):
        tg.mode='now'
    # '2人の年れいの合計': the two whose ages are told, said again
    if tg.u=='才':
        ages=[a for a in amts if a.u=='才' and not a.inq]
        for a in [x for x in amts if x.inq and x.u=='人' and x.v==len(ages)]:amts.remove(a);restate.append(a.raw)
    spec=Spec(t,'ja',lambda u:(u or '') not in J_MEASURE and '^' not in (u or ''))
    # 'the 1 of the question' (1人あたり何円, 1箱には何本): the unit asked, not an amount
    for m in re.finditer(r'(?<![\d.])1\s*(?:'+JCNT+r')(?:の[^\s、。]{1,6}?)?(?:分|あたり|当たり)?(?:は|に|が|には|では)?\s*(?:何|いくら)',q):
        spec.unused.append({'raw':'1','why':'「1…何」の1 (問いの単位)'})
    for raw in restate:spec.unused.append({'raw':raw,'why':'話の期間や形の言いかえ (量ではない)'})
    owners=set(re.findall(r'([一-龯ァ-ヶーぁ-ん]{1,6}?)(?:さん|くん|ちゃん)?の',q))|set(re.findall(r'([一-龯ァ-ヶーぁ-ん]{1,6}?)(?:さん|くん|ちゃん)',q))
    owners={re.sub(r'^(?:[ぁ-ん]{1,2})(?=[一-龯ァ-ヶー])','',w) for w in owners}
    ctx_owners=frozenset(w for w in owners if w and w not in J_PROP and w not in J_FUNC)
    ctx={'owners':ctx_owners,'qspan':q,'convert':_jconv,'notadj':tg.notadj,'sents':sents,'qnames':re.findall(r'([一-龯ァ-ヶーぁ-ん]{1,6}?)(?:さん|くん|ちゃん)',q),
         'equal':bool(re.search(r'同じ数|おなじ数|等分|とうぶん|ずつ|均等|同じだけ|同じように',t))}
    if tg.mode=='diff':ctx['diff_order']=tg.kind
    if tg.mode=='change':ctx['qsign']=tg.verb
    ctx['fact']=_fact_ja
    if tg.u=='才':
        for a in amts:
            if a.inq and a.kind=='count' and a.u=='年' and re.match(r'\s*年\s*(?:後|ご|たった|経った)',q[a.end:a.end+6]):a.kept='shift+';a.u='才'
            elif a.inq and a.kind=='count' and a.u=='年' and re.match(r'\s*年\s*前',q[a.end:a.end+4]):a.kept='shift-';a.u='才'
    for shape,w in (('triangle','三角形'),('square','正方形'),('rectangle','長方形')):
        if w in t:ctx['shape']=shape
    if re.search(r'誰も|だれも|何も|なにも|からっぽ|空っぽ|空で',''.join(stm)) and tg.mode in ('now','left'):
        amts.append(Amt(kind='count',u=tg.u,zero=True,role='state',order=-1,tags=frozenset(),span=q))
    if tg.geo=='area':
        if re.search(r'三角形|台形|円|平行四辺形|ひし形',t):no('AREA_OF_ANOTHER_SHAPE')
        for a in amts:spec.bind(a)
        live=[a for a in amts if a.kind=='count']
        if len(live)!=2 or live[0].u!=live[1].u or len(amts)!=2:no('AREA_NOT_TWO_SIDES')
        if live[0].u!=tg.u:no('AREA_IN_ANOTHER_UNIT')
        n=spec.rel(f'{live[0].u}^2',f'{live[0].name} * {live[1].name}',q,whole=False)
        return spec.done(n,'area')
    if any(a.zero for a in amts):ask,form=_compose_zero(t,amts,tg,spec,ctx)
    else:ask,form=compose(t,'ja',amts,tg,spec,ctx)
    return spec.done(ask,form)


def _jamount(s,si,n,nums,inq):
    e=n.end;c,e2=_jcounter(s,e)
    a=Amt(v=n.value,raw=n.raw,sent=si,inq=inq,kind='count',pos=n.start,end=n.end)
    a.noun=_noun_before(s,a)
    clause_a=max(s.rfind('、',0,n.start),-1)+1;clause_b=s.find('、',e2);clause_b=len(s) if clause_b<0 else clause_b
    clause=s[clause_a:clause_b];a.span=s[max(clause_a,n.start-8):min(len(s),e2+6)].strip('、。 ') or s
    before=s[clause_a:n.start];after=s[e2:clause_b]
    listed=False
    if not re.search(r'[ぁ-ん]{2,}',after) and clause_b<len(s):
        # a list ('1つ目のバス停で9人、2つ目で14人乗りました'): the verb at its end, after its last number, is said of each
        ld=list(re.finditer(r'\d',s[e2:]));after=s[e2+ld[-1].end():] if ld else s[e2:];listed=True
    a.tags=_jtags(before)|_jtags(after)
    if n.kind=='jfrac' or (n.kind=='half'):
        # 'その3分の1', 'Yの半分', 'ねだんの5分の1だけ安く'
        a.kind='frac';a.u=None
        if re.search(r'(?:その|それの)\s*$',s[max(0,n.start-4):n.start]) or n.kind=='half' and re.search(r'その\s*$',s[max(0,n.start-4):n.start]):a.of='@prev'
        else:
            m=re.search(r'([^\s、。のはが]+)の\s*$',s[clause_a:n.start])
            a.of=('@than',(m.group(1),)) if m else '@prev'
        if re.match(r'(?:だけ)?\s*(?:安|やす|引|びき|割引|わりびき)',s[e:]):a.op='off'
        if n.kind=='half' and re.match(r'\s*の長さ|\s*の重さ|\s*です|\s*の',s[e:]):a.kind='cmp';a.op='*';a.u=None
        a.tags=_jtags(s[clause_a:n.start])
        return a
    if c is None:
        if re.match(r'\s*倍',s[e:]):
            a.kind='cmp';a.op='*';a.u=None
            m=re.search(r'([^\s、。のはが]+)の\s*$',s[clause_a:n.start])
            a.of=('@than',(m.group(1),)) if m else '@prev';a.tags=_jtags(s[clause_a:n.start])-({m.group(1)} if m else set())
            return a
        no('NO_COUNTER:'+n.raw)
    a.u=c
    mx=re.match(r'\s*の\s*([一-龯ァ-ヶー]{1,4})',s[e2:])
    if c=='個' and mx and s[e:e2].strip() in ('つ',):a.u=_JC.get(mx.group(1),mx.group(1))
    # 'みかん入りの箱の重さは18kg、箱だけの重さは2kg': the container alone
    if re.search(r'(?:だけ|のみ|空の|から(?:っぽ)?の)[^、。0-9]{0,6}$',before):a.kept='container'
    # 'N C から M C に': a value before and after a change
    if re.match(r'\s*から',s[e2:]):a.role='state';a.verb='from'
    # the verb said of it: what follows in its clause
    nd=re.search(r'\d',after)
    if nd and not listed:
        if re.fullmatch(r'\s*(?:と|や|、|,|か|および|及び)\s*',after[:nd.start()]):
            # '250mLと0.5Lを使いました': a list, the verb after its last number said of each
            ld=list(re.finditer(r'\d',after));after=after[ld[-1].end():]
        else:after=after[:nd.start()]                 # '5個売って7個仕入れました': the 5's verb is 売って, not 仕入れ
    if a.verb=='from':pass
    elif re.search(r'(?:その|この)\s*うち|その中から|そのなかから',s[clause_a:n.start]) and (J_GAIN.search(after) or J_LOSS.search(after) or
                                                                                        re.search(r'ました',after)):
        a.role='loss';a.verb='taken_out'
    elif re.search(r'(?:別|べつ|ほか|他)の[^、。]{0,8}から',s[clause_a:clause_b]):a.role='other';a.verb='other_stock'   # '別の在庫から3個'
    elif J_LEFT.search(after[:8]) and re.search(r'(?:て|で)(?:い|お)|ました|ます',after):a.role='state';a.verb='left'
    elif J_LOSS.search(after) and not re.search(r'ずつ',after[:3]):a.role='loss';a.verb=J_LOSS.search(after).group(0)
    elif J_GAIN.search(after):a.role='gain';a.verb=J_GAIN.search(after).group(0)
    elif J_HAVE.search(after):a.role='state';a.verb='have'
    elif re.search(_J.STATE,after):a.role='state'
    elif re.search(r'(?:き|ぎ|し|ち|に|び|み|り|い|え|け|せ|て|ね|べ|め|れ)ました',after):a.role='act';a.verb='did'
    else:a.role='state'
    # a rate: 'N C ずつ', '1 C1 に N C', 'C1 につき', '各C1 に', '毎C1', '1 C1 N C', 'N C入りの X', '時速N km'
    pre=s[max(clause_a,n.start-12):n.start]
    if re.search(r'時速\s*$',pre):a.kind='rate';a.per='時間';return a
    if re.search(r'分速\s*$',pre):a.kind='rate';a.per='分';return a
    if re.search(r'秒速\s*$',pre):a.kind='rate';a.per='秒';return a
    m=re.match(r'\s*入り(?:の|で)\s*([^\s、。をがはでに0-9]{1,6}?)(?:を|が|に|で|は|、|。|$)',s[e2:])
    if m:
        cont=m.group(1);a.kind='rate';a.per=_JC.get(cont,cont);return a
    m=re.search(r'(?:(?<![\d.])1\s*('+JCNT+r')(?!目)|各\s*('+JCNT+r'|[^\s、。0-9にで]{1,3})|毎\s*('+JCNT+r'|[^\s、。0-9にで]{1,3})|([^\s、。0-9]{1,4}?)(?:につき|あたり|ごとに))\s*(?:に|で|は)?\s*(?:[^\s、。0-9]{0,8}?)$',s[clause_a:n.start])
    one_ok=m and m.group(1) and (re.search(r'1\s*(?:'+JCNT+r')\s*(?:に|で|あたり|当たり|につき|分)',s[clause_a:n.start]) or re.match(r'\s*ずつ',s[e2:]) or c=='円'
                                 or not _jconv(_JC[m.group(1)],c))     # '1m30cm' is one length, '1日4往復' a rate
    if m and (one_ok or m.group(2) or m.group(3) or m.group(4)):
        g=m.group(1) or m.group(2) or m.group(3) or m.group(4)
        a.kind='rate';a.per=_JC.get(g,g)
        if a.per in ('晩','夜','朝','夕方','ばん','よる','あさ') and m.group(3):a.per='日'       # 毎晩 9ページずつ: each day
        if m.group(1):a.base='@one'
        return a
    if re.match(r'\s*ずつ',s[e2:]):a.kind='rate';a.per='@each'
    mn=re.search(r'(?:^|[、はがをにでとのもへ])([一-龯ァ-ヶーぁ-ん]{1,6}?)\s*$',s[clause_a:n.start])
    if c=='円' and a.kind=='count' and mn and mn.group(1) not in J_PROP and mn.group(1) not in J_FUNC:
        a.kept=('price_of',mn.group(1))
    # a comparison: 'YよりN C 多い', 'N C 短く'
    mc=re.match(r'\s*(?:だけ)?\s*('+J_CMPRE+r')',s[e2:])
    if mc and a.kind=='count':
        a.kind='cmp';a.op=J_CMP[mc.group(1)]
        m=re.search(r'([^\s、。のはが]+?)(?:さん|くん)?より',s[clause_a:n.start])
        a.of=('@than',(m.group(1),)) if m else '@prev'
        a.tags=_jtags(s[clause_a:n.start])-({m.group(1)} if m else set())
    return a


def _jresolve(amts,sents,tg):
    for x,a in enumerate(amts):
        if a.kind=='rate' and a.base=='@one':
            # the 1 of '1日20分ずつ', '1箱300円' is the rate's base, bound with it
            one=[b for b in amts if b.sent==a.sent and b.order==a.order-1 and b.v==1 and b.u==a.per]
            a.base=one[0] if one else None
            if one:one[0].kept='base'
        if a.kind=='rate' and a.per=='@each':
            # 'みんなが3こずつもらいました': each of the other amount of its sentence (or of the problem)
            sen=sents[a.sent]
            if re.search(r'ずつ[^。]*?(?:分け|わけ|配|くば|入れ|いれ|つめ|詰め|はり|貼り|のせ|乗せ|ならべ|並べ|植え|うえ)',sen[a.end:]) and tg.u!=a.u and \
                    not any(b.kind=='count' and (b.u==tg.u or b.noun==tg.u) for b in amts):
                # '1dLずつコップに分けると、何ぱい分': put out so much to each of what the question counts
                a.per=tg.u;continue
            cs=[b for b in amts if b.sent==a.sent and b is not a and b.kind=='count' and b.u!=a.u]
            clause=sen[max(sen.rfind('、',0,a.pos),-1)+1:a.pos]
            mr=re.search(r'([一-龯ァ-ヶーぁ-ん]{1,6}?)の(?:たびに|ごとに)|([一-龯ァ-ヶー]{1,5}|[ぁ-ん]{2,5})(?:に|へ)(?![ぁ-ん]*ずつ)[^、。]*$',clause)
            if not cs and mr:
                # '箱に6こずつ', 'たん生日のたびに500円ずつ': each of the receiver its clause names, counted elsewhere
                w=mr.group(1) or mr.group(2);w=_JC.get(w,w)
                cs=[b for b in amts if b is not a and b.kind=='count' and b.u!=a.u and (b.u==w or b.noun==w or any(w in x for x in b.tags))]
                if not cs:no('EACH_RECEIVER_NOT_COUNTED')
            elif not cs:cs=[b for b in amts if b is not a and b.kind=='count' and b.u!=a.u]
            if len(cs)!=1:no('EACH_OF_WHAT')
            a.per=cs[0].u
    # '大人1400円、子ども900円 ... 大人2人と子ども1人': the price for each one of them
    for a in amts:
        if isinstance(a.kept,tuple) and a.kept[0]=='price_of':
            w=a.kept[1];a.kept=None
            if any(b is not a and b.kind=='count' and b.u in J_GENERIC and _noun_before(sents[b.sent],b)==w for b in amts):
                a.kind='rate';a.per=w
    for r in [x for x in amts if x.kind=='rate']:
        for b in amts:
            if b.kind=='count' and b.u in J_GENERIC and b.noun and b.noun==r.per:b.u=b.noun
    # 'クモの足は8本です。クモ7ひきの足は': what one has, asked of several
    for a in amts:
        if a.kind!='count' or a.inq or a.u!=tg.u:continue
        qs=[b for b in amts if b.inq and b.kind=='count' and b.u!=a.u and b.u in J_GENERIC]
        if len(qs)==1 and _noun_before(sents[qs[0].sent],qs[0]) and re.match(r'\s*'+re.escape(_noun_before(sents[qs[0].sent],qs[0]))+r'\s*の',sents[a.sent]):
            a.kind='rate';a.per=qs[0].u
    # 'パン2こを作るのに小麦粉を4カップ使います。パン6こでは': the one for the other, when the question names another
    for a in amts:
        if a.kind!='count' or a.inq:continue
        nx=[b for b in amts if b.sent==a.sent and b.order==a.order+1 and b.kind=='count' and b.u!=a.u]
        if not nx:continue
        b=nx[0];sen=sents[a.sent];between=sen[a.end:b.pos]
        if re.match(r'\s*(?:'+JCNT+r')?\s*(?:を|の)?\s*(?:作る|つくる|焼く|やく|走る|はしる|進む|すすむ|作り|焼き)?(?:のに|には|ために)',between) and \
                any(c.inq and c.kind=='count' and c.u==a.u for c in amts):
            b.kind='rate';b.per=a.u;b.base=a
    # 'Xの足は8本です。X7ひきの足は': an amount said of one thing, asked for several
    for a in amts:
        if a.kind=='cmp' or a.kind=='frac':
            how=a.of
            if how=='@prev':
                pv=[b for b in amts if b.order<a.order and b.kind=='count']
                if not pv:no('COMPARED_TO_NOTHING')
                a.of=pv[-1]
            elif isinstance(how,tuple) and how[1][0] in J_PROP:
                pv=[b for b in amts if b.order<a.order and b.kind=='count']
                if not pv:no('COMPARED_TO_NOTHING')
                a.of=pv[-1]
            elif isinstance(how,tuple):
                w=re.sub(r'^(?:[ぁ-ん]{1,2})(?=[一-龯ァ-ヶー])','',how[1][0])      # as the tags are written ('お父さん': 父)
                w=re.sub(r'(?:入り|いり|だけ|用|たち)$','',w)
                # the amount whose words hold the word compared to ('Yの6倍'); not a longer one that holds them ('スコティッシュ
                # ユニコーンの3分の2' is not of the 27 ユニコーン)
                cs=[b for b in amts if b is not a and b.kind=='count' and any(w==x or w in x for x in b.tags) and b.order<a.order]
                if len(cs)!=1:
                    cs=[b for b in amts if b is not a and b.kind=='count' and b.order<a.order][-1:] if w in ('その','それ') else cs
                if len(cs)!=1:no('COMPARED_TO_WHICH')
                a.of=cs[0]
            if a.kind=='cmp' and a.op in '+-' and not a.u:a.u=a.of.u
    amts[:]=[a for a in amts if a.kept!='base' or True]
    for a in amts:
        if a.kind in ('count','rate') and not a.u:no('NO_UNIT')


J_GENERIC={'個','人','本','枚','匹','頭','羽','台','冊','杯','箱','袋'}
def _noun_before(s,a):
    """the noun right before a number with no particle: '大人2人' -> 大人, 'クモ7ひき' -> クモ"""
    m=re.search(r'(?:^|[、。はがをにでとのもへや])([一-龯ァ-ヶーぁ-ん]{1,6}?)\s*$',s[:a.pos])
    if not m:return None
    w=m.group(1)
    if re.fullmatch(r'[ぁ-ん]+',w) and w[-1] in 'はがをにでとのもへやも':
        if len(w)>2 and w[-1] in 'はがをにでとへや':return w[:-1]       # 'にわとりが'
        return None
    if len(w)>1 and w[-1] in 'はがをにでとのへや':w=w[:-1]          # not も: 子ども, くも
    return w


J_FACTS={('足','本'):{**{w:4 for w in '犬 いぬ ねこ 猫 うし 牛 うま 馬 ぶた 豚 ひつじ 羊 うさぎ ライオン ぞう ゾウ きりん キリン 子犬 子ねこ'.split()},
                     **{w:2 for w in 'にわとり ニワトリ 鳥 とり すずめ アヒル ハト ペンギン ダチョウ'.split()},
                     **{w:8 for w in 'クモ くも タコ たこ'.split()},**{w:6 for w in '虫 こん虫 昆虫 アリ あり カブトムシ チョウ'.split()}},
         ('車輪','個'):{'自転車':2,'三輪車':3,'車':4,'自動車':4,'一輪車':1},('タイヤ','本'):{'自転車':2,'三輪車':3,'車':4,'自動車':4}}
_EN_OF={'犬':'dog','いぬ':'dog','ねこ':'cat','猫':'cat','うし':'cow','牛':'cow','うま':'horse','馬':'horse','ぶた':'pig','豚':'pig','ひつじ':'sheep','羊':'sheep',
        'うさぎ':'rabbit','ライオン':'lion','ぞう':'elephant','ゾウ':'elephant','きりん':'giraffe','キリン':'giraffe','子犬':'puppy','子ねこ':'kitten',
        'にわとり':'chicken','ニワトリ':'chicken','鳥':'bird','とり':'bird','すずめ':'bird','アヒル':'duck','ハト':'bird','ペンギン':'penguin','ダチョウ':'ostrich',
        'クモ':'spider','くも':'spider','虫':'insect','こん虫':'insect','昆虫':'insect','アリ':'ant','あり':'ant','カブトムシ':'beetle','チョウ':'butterfly',
        '自転車':'bicycle','三輪車':'tricycle','車':'car','自動車':'car','一輪車':'unicycle'}
def _fact_ja(c,u):
    """what everyone knows in Japanese ('犬7ひきの足は全部で何本'), said as the checker reads it (fpl.KNOWN_FACTS)"""
    from .fpl import KNOWN_FACTS
    thing=c.noun or next(iter(c.tags),None)
    if not thing:return None
    for (part,unit),table in J_FACTS.items():
        if unit!=u or thing not in table:continue
        if not re.search(part,_FACT_Q.get('q','')):continue
        n=table[thing];en=_EN_OF.get(thing)
        w='legs' if part=='足' else 'wheels'
        k=f"{'an' if en and en[0] in 'aeiou' else 'a'} {en} has {n} {w}" if en else None
        if k and KNOWN_FACTS.get(k)==n:return (n,k)
        from .fpl import KNOWN
        from fractions import Fraction as F
        if F(n) in KNOWN:return (n,f'{thing}の{part}は{n}{u} (common knowledge)')
    return None
_FACT_Q={}


def _jquestion(q,amts,sents):
    tg=Tgt(mode='amount')
    m=re.search(r'何\s*('+JCNT+r')',q)
    if m:tg.u=_JC[m.group(1)]
    elif 'いくら' in q:tg.u='円'
    elif 'いくつ' in q:
        m2=re.search(r'([^\s、。のはがを]+)は\s*(?:全部で|あわせて)?\s*いくつ',q)
        tg.u=re.split(r'(?:た|る|の|に)',m2.group(1))[-1] if m2 else None
        if tg.u and re.fullmatch(r'(?:数|かず)',tg.u):tg.u=None
        if tg.u:tg.u=_JC.get(tg.u,tg.u)
    if not tg.u:no('ASKED_UNIT')
    # '箱は全部で何個': the boxes are asked (counted with 個), not what is in them
    mt=re.match(r'\s*([一-龯ァ-ヶーぁ-ん]{1,4})は',q)
    if mt and mt.group(1) in _JC and _JC[mt.group(1)]!=tg.u and any(a.u==_JC[mt.group(1)] for a in amts):tg.u=_JC[mt.group(1)]
    if tg.u in ('m^2','cm^2','km^2'):tg.geo='area';tg.u=tg.u.split('^')[0]
    if re.search(r'まわりの長さ|周りの長さ|周の長さ',q):tg.geo='perimeter'
    tg.tags=_jtags(q)
    mp=re.search(r'1\s*('+JCNT+r')(?:の[^\s、。]{1,6}?)?(?:分|あたり|当たり)?(?:は|に|が|には|では)?\s*(?:何|いくら)',q) or \
       re.search(r'1\s*('+JCNT+r')\s*(?:あたり|当たり)',q)
    if mp:tg.per=_JC[mp.group(1)]
    if J_NEED.search(q):tg.mode='need'
    elif J_DIFF.search(q):tg.mode='unsure'
    elif re.search(r'のこ|残',q):tg.mode='left'
    elif J_TOTAL.search(q):tg.mode='total'
    elif J_NOW.search(q):tg.mode='now'
    elif re.search(r'(?:安く|やすく)\s*なって',q):tg.mode='amount'
    mn=re.search(r'([ぁ-ん一-龯]{1,4}?)(?:て|で)いない',q)
    if mn and tg.mode=='amount':tg.mode='rest';tg.notadj=mn.group(1)
    qw=re.search(r'何|いくつ|いくら',q);qa=q[qw.start():] if qw else q
    qv=J_LOSS.search(qa) or J_GAIN.search(qa)
    if tg.mode=='amount' and qv and sum(1 for a in amts if a.kind=='count' and not a.inq and a.role=='state')>=2:
        tg.mode='change';tg.verb='loss' if J_LOSS.search(q) else 'gain'
    if False and tg.mode=='amount' and not tg.per and not any(a.inq for a in amts) and re.search(r'(?:ますか|ですか)[。？?]?$',q) and any(a.role in ('gain','loss') for a in amts if a.kind=='count' and not a.inq) \
            and any(a.role=='state' for a in amts if a.kind=='count' and not a.inq):
        tg.mode='now'
    return tg
