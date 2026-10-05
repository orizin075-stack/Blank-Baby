"""claude-patch3: more word-problem schemas, same rules as wordprob.py (full number coverage, exact,
non-negative, fail closed). Called from wordprob._ja / wordprob._en.

  equation     「ある数に7を足すと20になります。ある数は？」「ある数を2倍して3を足すと11」 (one unknown, solved by
               inverting the operations; the answer is substituted back before it is returned)
  per period   「1日に15ページずつ読むと150ページは何日」「毎月800円ずつ貯金すると6か月で何円」「1分間に12枚…96枚は何分」
  distribute   「60個のあめを1人5個ずつ配ると何人に配れる」
  part-whole   「生徒が32人。そのうち男子は17人。女子は何人」
  difference   「赤い花が18本、白い花が24本。白い花は赤い花より何本多い」
  each item    「1個120円のパンと1本90円の牛乳をそれぞれ2つずつ買うと全部でいくら」
English: "N times as many / twice as many", "costs N dollars ... how much do 3 X and 2 Y cost",
         "share N X equally among M Y".
"""
from __future__ import annotations
import re
from fractions import Fraction

NUM=r'(\d+(?:\.\d+)?)'
X=r'(?:ある数|ある整数|□|x|X)'
OPS=[(r'(?:に|へ)?'+NUM+r'を(?:足し|足す|たし|たす|加え|加える|プラスし|プラスす)','+'),(r'(?:から)?'+NUM+r'を(?:引い|引く|ひい|ひく|マイナスし|マイナスす)','-'),
     (r'(?:に)?'+NUM+r'を(?:かけ|かける|掛け|掛ける)','*'),(r'を'+NUM+r'倍(?:に)?(?:し|す)','*'),(r'(?:を)?'+NUM+r'で(?:割っ|割る|わっ|わる)','/')]

def _f(v):
    v=Fraction(v);return str(v.numerator) if v.denominator==1 else f'{v.numerator}/{v.denominator}'

def equation(t,q):
    if not re.search(X+r'(?:は|を求め)',q):return None
    m=re.search(X+r'(.{1,60}?)(?:と|たら|ら|れば)[、,]?'+NUM+r'(?:に|と)?(?:なり|なる|なった|です|だ)',t)
    if not m:return None
    rest=m[1];ops=[];pos=0
    while pos<len(rest):
        rest_=rest[pos:]
        for pat,op in OPS:
            mm=re.match(r'[、,]?\s*(?:それに|さらに|次に|その数に|その数を|そこに|そこから)?\s*'+pat+r'(?:て|た|る|と|、)?',rest_)
            if mm:ops.append((op,Fraction(mm[1])));pos+=mm.end();break
        else:return None
    if not ops or len(ops)>4:return None
    y=Fraction(m[2]);expr=m[2];x=y
    for op,n in reversed(ops):
        if op=='+':x-=n;expr=f'({expr}-{_f(n)})'
        elif op=='-':x+=n;expr=f'({expr}+{_f(n)})'
        elif op=='*':
            if n==0:return None
            x/=n;expr=f'({expr}/{_f(n)})'
        else:x*=n;expr=f'({expr}*{_f(n)})'
    chk=x                                                   # substitute back
    for op,n in ops:chk=chk+n if op=='+' else chk-n if op=='-' else chk*n if op=='*' else chk/n
    if chk!=y:return None
    return {'expression':expr,'value':x,'schema':'one_unknown_equation','unit':'','trace':[m.span()],'check':'substituted_back'}

PERIOD={'日':'日','週':'週間','週間':'週間','か月':'か月','ヶ月':'か月','カ月':'か月','月':'か月','時間':'時間','分間':'分','分':'分','秒':'秒','年':'年'}
PER_RE=r'(?:1\s*(日|週間?|か月|ヶ月|カ月|時間|分間|分|秒|年)(?:に|で|あたり|当たり)|毎(日|週|月|時間|分|秒|年))\s*'+NUM+r'\s*(個|枚|本|冊|台|人|円|ページ|回|問|km|m|L|mL|g|kg|匹|羽)(?:ずつ)?'
def per_period(t,q,cnt):
    m=re.search(PER_RE,t)
    if not m:return None
    p=PERIOD[m[1] or m[2]];r=Fraction(m[3]);u=m[4]
    rest=t[:m.start()]+'#'*(m.end()-m.start())+t[m.end():]
    nums=list(re.finditer(r'\d+(?:\.\d+)?',rest))
    if len(nums)!=1:return None
    n=nums[0];after=rest[n.end():n.end()+4];
    pm=re.match(r'\s*(日間?|週間|か月|ヶ月|カ月|時間|分間?|秒|年間?)',after);um=re.match(r'\s*'+re.escape(u),after)
    a=re.search(r'何(日|週間|か月|ヶ月|カ月|時間|分|秒|年)',q)
    if pm and PERIOD.get(pm[1].replace('間','') if pm[1] not in ('時間','週間') else pm[1],None)==p and (re.search(r'何'+re.escape(u),q) or (u=='円' and re.search(r'いくら|何円',q))):
        v=r*Fraction(n.group())
        return {'expression':f'{m[3]}*{n.group()}','value':v,'schema':'rate_per_period_x_periods','unit':u,'trace':[m.span(),(n.start(),n.end()+len(pm.group()))]}
    if um and a and PERIOD.get(a[1])==p:
        v=Fraction(n.group())/r
        if v.denominator!=1:return None
        return {'expression':f'{n.group()}/{m[3]}','value':v,'schema':'total_div_rate_per_period','unit':a[1],'trace':[m.span(),n.span()]}
    return None

def distribute(t,q,cnt):
    m=re.search(NUM+r'\s*('+cnt+r')(?:の[^、。を]{1,10})?を\s*1\s*(人|つ|袋|箱|皿|組|台)(?:に|あたり)?\s*'+NUM+r'\s*\2ずつ(?:配|分け|わけ|入れ|のせ|乗せ)',t)
    if not m or not re.search(r'何'+re.escape(m[3]),q):return None
    n,k=Fraction(m[1]),Fraction(m[4])
    if k==0 or (n/k).denominator!=1:return None
    return {'expression':f'{m[1]}/{m[4]}','value':n/k,'schema':'distribute_each','unit':m[3],'trace':[m.span()]}

def part_whole(t,q,cnt):
    m=re.search(r'(?:は|が)\s*'+NUM+r'\s*('+cnt+r')(?:います|あります|いる|ある|です)?[。、,]\s*(?:その)?うち[、,]?\s*([^、。はが]{1,8})(?:は|が)\s*'+NUM+r'\s*\2',t)
    if not m:return None
    a=re.search(r'([^、。はが]{1,8})(?:は|が)\s*何'+re.escape(m[2]),q)
    if not a or a[1]==m[3]:return None
    v=Fraction(m[1])-Fraction(m[4])
    if v<0:return None
    return {'expression':f'{m[1]}-{m[4]}','value':v,'schema':'part_whole','unit':m[2],'trace':[m.span()]}

def difference(t,q,cnt):
    items=list(re.finditer(r'([^、。はがの0-9]{1,8})(?:が|は)\s*'+NUM+r'\s*('+cnt+r')',t))
    a=re.search(r'([^、。はがの]{1,8})(?:は|が)\s*([^、。はがの]{1,8})より\s*何('+cnt+r')\s*(多い|少ない|多く|少なく|長い|短い|高い|低い|重い|軽い)',q)
    if not a or len(items)!=2:return None
    vals={re.sub(r'^(?:[、,]|また|そして)','',x[1]):x for x in items}
    if a[1] not in vals or a[2] not in vals or a[1]==a[2]:return None
    x,y=vals[a[1]],vals[a[2]]
    if x[3]!=a[3] or y[3]!=a[3]:return None
    v=Fraction(x[2])-Fraction(y[2]) if a[4] in ('多い','多く','長い','高い','重い') else Fraction(y[2])-Fraction(x[2])
    if v<0:return None
    return {'expression':f'{x[2]}-{y[2]}' if a[4] in ('多い','多く','長い','高い','重い') else f'{y[2]}-{x[2]}','value':v,'schema':'difference','unit':a[3],'trace':[x.span(),y.span()]}

def each_item_price(t,q,cnt):
    e=re.search(r'それぞれ\s*'+NUM+r'\s*(?:つ|'+cnt+r')ずつ',t)
    if not e or not re.search(r'いくら|何円|代金',q):return None
    items=list(re.finditer(r'1\s*('+cnt+r')\s*'+NUM+r'円',t))
    if len(items)<2:return None
    v=sum(Fraction(i[2]) for i in items)*Fraction(e[1])
    return {'expression':'('+'+'.join(i[2] for i in items)+f')*{e[1]}','value':v,'schema':'each_item_price','unit':'円','trace':[*[i.span() for i in items],e.span()]}

# ---------------------------------------------------------------- English
MULT={'twice':2,'double':2,'three times':3,'four times':4,'five times':5,'half':Fraction(1,2)}
def en_times(s):
    nums=list(re.finditer(r'\d+(?:\.\d+)?',s))
    m=re.search(r'(?:(\d+) times|(twice|three times|four times|five times|half)) as many',s)
    if not m or not re.match(r'how many',s.split('. ')[-1].strip()) and 'how many' not in s:return None
    k=Fraction(m[1]) if m[1] else Fraction(MULT[m[2]])
    base=[x for x in nums if not (m[1] and x.start()==m.start(1))]
    if len(base)!=1:return None
    # claude-patch6: who has k times as many, who is compared against, whose amount is given, who is asked.
    # 「Ann has 30. Ann has 3 times as many as Kim. How many does Kim have?」 is 30/3, not 3*30.
    name=r"([a-z]+)(?:'s)?"
    subj=re.search(name+r' (?:has|have|had|owns|collected|picked|made|read|scored) (?:exactly )?'+re.escape(m.group())+r'\b(?: (?!as\b)\w+)?(?: as (?!many)'+name+r')?',s)
    own=re.search(name+r' (?:has|have|had|owns|collected|picked|made|read|scored) '+re.escape(base[0].group())+r'\b',s)
    ask=re.search(r'how many \w+ (?:does|do|did|will) '+name+r' ',s)
    ctx=re.search(r'\b(?:and|but) '+re.escape(m.group())+r' (?:on|in|at|during) ([a-z]+)\b',s)
    if ctx and not subj:
        # 「Lisa read 12 pages on Monday and twice as many on Tuesday. How many pages did she read on Tuesday?」
        q=s[s.rfind('how many'):]
        if not re.search(r'\b(?:on|in|at|during) '+re.escape(ctx[1])+r'\b',q) or re.search(re.escape(base[0].group())+r' \w+ (?:on|in|at|during) '+re.escape(ctx[1])+r'\b',s):return None
        v=k*Fraction(base[0].group())
        return {'expression':f'{_f(k)}*{base[0].group()}','value':v,'schema':'times_as_many','unit':'','trace':[m.span(),base[0].span()]} if v.denominator==1 else None
    if not (subj and own and ask) or ask[1] in ('he','she','they','it'):return None
    who,than,owner,asked=subj[1],subj[2],own[1],ask[1]
    if asked==who and owner!=who and (than is None or than==owner):v=k*Fraction(base[0].group());expr=f'{_f(k)}*{base[0].group()}'
    elif than is not None and asked==than and owner==who:v=Fraction(base[0].group())/k;expr=f'{base[0].group()}/{_f(k)}'
    else:return None
    if v.denominator!=1:return None
    return {'expression':expr,'value':v,'schema':'times_as_many','unit':'','trace':[m.span(),base[0].span()]}

def en_prices(s):
    prices={}
    for m in re.finditer(r'\b(?:a|an|one|each) (\w+?)s? costs? (\d+(?:\.\d+)?) (?:dollars?|yen|cents?|euros?)',s):prices[m[1]]=Fraction(m[2])
    q=re.search(r'how much (?:do|does|would|will)? ?((?:\d+ \w+?s?(?:,| and)? ?)+) (?:cost|be)',s)
    if not prices or not q:return None
    parts=re.findall(r'(\d+) (\w+?)s?(?=,| and|$)',q[1].strip())
    if not parts or any(p[1] not in prices for p in parts):return None
    used={p[1] for p in parts}
    if len(re.findall(r'\d+(?:\.\d+)?',s))!=len(prices)+len(parts):return None
    v=sum(Fraction(n)*prices[w] for n,w in parts)
    return {'expression':'+'.join(f'{n}*{_f(prices[w])}' for n,w in parts),'value':v,'schema':'unit_prices','unit':'','trace':[]}

def en_share(s):
    m=re.search(r'(?:share|divide|split) (\d+) (\w+) (?:equally )?(?:among|between|by) (\d+) (\w+)',s)
    if not m or not re.search(r'\beach\b',s) or len(re.findall(r'\d+(?:\.\d+)?',s))!=2:return None
    n,k=Fraction(m[1]),Fraction(m[3])
    if k==0 or (n/k).denominator!=1:return None
    return {'expression':f'{m[1]}/{m[3]}','value':n/k,'schema':'equal_sharing','unit':m[2],'trace':[m.span()]}
