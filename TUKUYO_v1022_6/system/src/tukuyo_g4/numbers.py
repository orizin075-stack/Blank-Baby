"""generation 4: every number a problem states, with its position in the text (Japanese and English).

find(text) -> [Num(value, start, end, raw, kind)], in text order, never overlapping
  digits   16  1,000  2.5  3/4  (fullwidth digits too)
  jbig     8万  1万5千  2億3000万 (the multipliers applied)
  kanji    三十五人  二つ (only right before a counter, so 一緒 三角形 一部 are not numbers)
  jfrac    4分の3 -> 3/4   三分の一 -> 1/3
  percent  40%  40パーセント -> 40 ; 6割 -> 60 ; 2割5分 -> 25
  half     半分 -> 1/2 ; the 半 of 2時間半 -> 1/2
  word     English number words: twenty-five, a hundred, a dozen, half, twice, double, triple, a quarter,
           two-thirds, one and a half
  ordinal  2つ目 2番目 第2 2nd, the second (a position, not an amount)
Positions refer to the original text: normalising fullwidth digits keeps every length, so a fact's span can be
checked against them. optional(n) tells the grounding check which numbers a reading may leave unused without
saying why: ordinals and the value 1 (1個あたり2ドル, one day).
"""
from __future__ import annotations
import re
from collections import namedtuple
from fractions import Fraction

Num=namedtuple('Num','value start end raw kind')
_FW=str.maketrans({**{chr(0xFF10+i):str(i) for i in range(10)},'，':',','．':'.','％':'%','／':'/'})
KD={'〇':0,'零':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'两':2}
KU={'十':10,'百':100,'千':1000}
KB={'万':10**4,'億':10**8}
KNUM='〇零一二三四五六七八九十百千万两'
COUNTERS=('つ','人','個','本','枚','匹','頭','羽','冊','台','回','日','週間','週','か月','ヶ月','カ月','ケ月','年','時間','時','分','秒','歳','才',
          '円','倍','杯','箱','袋','組','足','着','軒','階','度','皿','粒','切れ','束','缶','ページ','キロ','メートル','センチ','ミリ','リットル','グラム',
          '点','周','問','品','種類','色','曲','通','件','名','チーム','席','部屋','か所','ヶ所','カ所','箇所','パック','ダース','セット','歩','行','列')
NOT_NUMBER_AFTER_JUBUN=('な','に','だ','で','です','すぎ','過ぎ')

def kanji_value(s):
    total=0;section=0;digit=None
    for ch in s:
        if ch in KD:
            if digit is not None:return None          # 二三 is not a number
            digit=KD[ch]
        elif ch in KU:
            section+=(1 if digit is None else digit)*KU[ch];digit=None
        elif ch in KB:
            section+=digit or 0;digit=None
            if section==0:return None
            total+=section*KB[ch];section=0
        else:return None
    return total+section+(digit or 0)

def _big(m):
    """8万 / 1万5千 / 2億3000万 / 1万5000 -> value, or None when the multipliers are not in falling order"""
    parts=re.findall(r'(\d+(?:\.\d+)?)([億万千]?)',m)
    total=Fraction(0);last=None
    for num,mult in parts:
        k={'億':10**8,'万':10**4,'千':1000,'':1}[mult]
        if last is not None and k>=last:return None
        total+=Fraction(num)*k;last=k
    return total

EN_UNITS={'zero':0,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12,
          'thirteen':13,'fourteen':14,'fifteen':15,'sixteen':16,'seventeen':17,'eighteen':18,'nineteen':19}
EN_TENS={'twenty':20,'thirty':30,'forty':40,'fifty':50,'sixty':60,'seventy':70,'eighty':80,'ninety':90}
EN_SCALE={'hundred':100,'thousand':1000,'million':10**6}
EN_DEN={'half':2,'halves':2,'third':3,'thirds':3,'fourth':4,'fourths':4,'quarter':4,'quarters':4,'fifth':5,'fifths':5,'sixth':6,'sixths':6,
        'seventh':7,'sevenths':7,'eighth':8,'eighths':8,'ninth':9,'ninths':9,'tenth':10,'tenths':10}
EN_ORD={'first':1,'second':2,'third':3,'fourth':4,'fifth':5,'sixth':6,'seventh':7,'eighth':8,'ninth':9,'tenth':10,'eleventh':11,'twelfth':12}
EN_MULT={'twice':2,'double':2,'doubled':2,'triple':3,'tripled':3,'thrice':3,'quadruple':4}
ORD_DET={'the','his','her','its','their','my','your','our','every','each'}

def optional(n):
    return n.kind=='ordinal' or n.value==1

def _en(text,taken):
    toks=[(m.group().lower(),m.start(),m.end()) for m in re.finditer(r'[A-Za-z]+',text)]
    n=len(toks);out=[]
    def gap(a,b):return text[toks[a][2]:toks[b][1]]
    def adj(a,b):return gap(a,b) in (' ','-')
    def phrase(i):
        """a cardinal from toks[i]: (value, next index) or None"""
        value=0;cur=None;j=i;scaled=False
        if toks[i][0]=='a':
            if i+1<n and adj(i,i+1) and toks[i+1][0] in EN_SCALE:cur=1;j=i+1
            else:return None
        while j<n:
            if j>i and not adj(j-1,j):break
            t=toks[j][0]
            if t=='and':
                if j+1<n and adj(j,j+1) and (toks[j+1][0] in EN_UNITS or toks[j+1][0] in EN_TENS) and (scaled or cur is not None and cur%100==0 and cur>0):
                    j+=1;continue
                break
            if t in EN_UNITS:
                if cur is not None and not (cur%100==0 and cur>0 or cur%10==0 and cur%100!=0 and EN_UNITS[t]<10):break
                cur=(cur or 0)+EN_UNITS[t]
            elif t in EN_TENS:
                if cur is not None and not (cur%100==0 and cur>0):break
                cur=(cur or 0)+EN_TENS[t]
            elif t=='hundred':
                if cur is None or cur>=100:break
                cur*=100
            elif t in ('thousand','million'):
                if cur is None:break
                value+=cur*EN_SCALE[t];cur=None;scaled=True
            else:break
            j+=1
        if j==i or (cur is None and not scaled):return None
        return Fraction(value+(cur or 0)),j
    i=0
    while i<n:
        w,s,e=toks[i]
        if any(a<e and s<b for a,b in taken):i+=1;continue
        prev=toks[i-1][0] if i and adj(i-1,i) else ''
        if w in EN_MULT:out.append(Num(Fraction(EN_MULT[w]),s,e,text[s:e],'word'));i+=1;continue
        if w=='a' and i+1<n and adj(i,i+1) and toks[i+1][0] in ('dozen','half','third','quarter','fifth','sixth','seventh','eighth','ninth','tenth'):
            nxt,_,e2=toks[i+1];out.append(Num(Fraction(12) if nxt=='dozen' else Fraction(1,EN_DEN[nxt]),s,e2,text[s:e2],'word'));i+=2;continue
        if w=='half':out.append(Num(Fraction(1,2),s,e,text[s:e],'word'));i+=1;continue
        if w=='dozen':out.append(Num(Fraction(12),s,e,text[s:e],'word'));i+=1;continue
        if w in EN_ORD and prev in ORD_DET:out.append(Num(Fraction(EN_ORD[w]),s,e,text[s:e],'ordinal'));i+=1;continue
        r=phrase(i)
        if not r:i+=1;continue
        v,j=r;end=toks[j-1][2]
        if j<n and adj(j-1,j) and toks[j][0] in EN_DEN and 0<v<=20:          # two thirds, three-quarters
            out.append(Num(v/EN_DEN[toks[j][0]],s,toks[j][2],text[s:toks[j][2]],'word'));i=j+1;continue
        if j+2<n and toks[j][0]=='and' and toks[j+1][0]=='a' and adj(j-1,j) and adj(j,j+1) and adj(j+1,j+2) and toks[j+2][0] in ('half','quarter','third'):
            out.append(Num(v+Fraction(1,EN_DEN[toks[j+2][0]]),s,toks[j+2][2],text[s:toks[j+2][2]],'word'));i=j+3;continue
        if j<n and adj(j-1,j) and toks[j][0]=='dozen':
            out.append(Num(v*12,s,toks[j][2],text[s:toks[j][2]],'word'));i=j+1;continue
        out.append(Num(v,s,end,text[s:end],'word'));i=j
    return out

def find(text):
    t=text.translate(_FW);taken=[];out=[]
    def add(v,s,e,kind):
        if v is None or any(a<e and s<b for a,b in taken):return
        taken.append((s,e));out.append(Num(Fraction(v),s,e,text[s:e],kind))
    K=f'[{KNUM}]+'
    for m in re.finditer(rf'(\d+(?:\.\d+)?|{K})分の(\d+(?:\.\d+)?|{K})',t):
        a=Fraction(m.group(1)) if m.group(1)[0].isdigit() else kanji_value(m.group(1))
        b=Fraction(m.group(2)) if m.group(2)[0].isdigit() else kanji_value(m.group(2))
        if a:add(Fraction(b)/a,m.start(),m.end(),'jfrac')
    for m in re.finditer(r'(\d+(?:\.\d+)?)\s*(?:%|パーセント)',t):add(Fraction(m.group(1)),m.start(),m.end(),'percent')
    for m in re.finditer(r'(\d+|[一二三四五六七八九十])割(?:(\d|[一二三四五六七八九])分)?',t):
        a=int(m.group(1)) if m.group(1).isdigit() else kanji_value(m.group(1));b=m.group(2)
        b=0 if not b else int(b) if b.isdigit() else kanji_value(b)
        add(10*a+b,m.start(),m.end(),'percent')
    for m in re.finditer(r'(?:\d+(?:\.\d+)?[億万千])+(?:\d+(?:\.\d+)?)?',t):
        if m.end()<len(t) and t[m.end()-1]=='千' and t[m.end():m.end()+1]=='葉':continue
        add(_big(m.group()),m.start(),m.end(),'jbig')
    for m in re.finditer(r'第\s*(\d+)|(\d+)\s*(?:つ目|番目|日目|回目|個目|人目|週目|年目|か月目|ヶ月目|位|st\b|nd\b|rd\b|th\b)',t):
        g=m.group(1) or m.group(2);s=m.start(1) if m.group(1) else m.start(2);add(int(g),s,s+len(g),'ordinal')
    for m in re.finditer(r'(?<![\d.,/])\d{1,3}(?:,\d{3})+(?:\.\d+)?(?![\d])|(?<![\d.])\d+(?:\.\d+)?(?:/\d+(?![\d.]))?',t):
        g=m.group().replace(',','')
        try:v=Fraction(g)
        except (ValueError,ZeroDivisionError):continue
        add(v,m.start(),m.end(),'digits')
    for m in re.finditer(rf'{K}',t):
        s,e=m.start(),m.end();rest=t[e:e+4]
        if not rest.startswith(COUNTERS):continue
        if m.group()=='十' and rest.startswith('分') and t[e+1:e+3].startswith(NOT_NUMBER_AFTER_JUBUN):continue
        if t[s-1:s] in ('唯','統','同','万'):continue
        add(kanji_value(m.group()),s,e,'kanji')
    for m in re.finditer(r'半分|(?:(?<=時間)|(?<=か月)|(?<=ヶ月)|(?<=カ月)|(?<=年)|(?<=日))半',t):add(Fraction(1,2),m.start(),m.end(),'half')
    for n in _en(t,taken):add(n.value,n.start,n.end,n.kind)
    return sorted(out,key=lambda n:n.start)
