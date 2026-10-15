"""claude-patch3: exact quantity / time / calendar questions (Japanese + simple English).

Covered (whole question must match one form, otherwise None):
  unit conversion      「3.5kmは何m？」「2時間15分は何分？」「90分は何時間何分？」 "How many minutes are in 3 hours?"
  clock arithmetic     「午前9時40分から50分後は何時何分？」「14時20分の1時間45分前は？」
  weekday arithmetic   「今日は月曜日です。10日後は何曜日？」
  calendar             「2026年10月5日の30日後は何月何日？」「2026年10月5日は何曜日？」 (proleptic Gregorian, via datetime)
  percent / 割         「5000円の2割引きは？」「3000円の15%引きは？」「800円の2割増しは？」「1200円の25%は？」
  fixed constants      「1ダースは何個？」「3ダースは何本？」 (dozen, week, hour, minute, day only; 1年/1か月 are refused)
Every answer carries a proof that proofs.check recomputes from the question text alone.
"""
from __future__ import annotations
import datetime,re,unicodedata
from fractions import Fraction

LEN={'mm':Fraction(1,1000),'cm':Fraction(1,100),'m':1,'km':1000}
MASS={'mg':Fraction(1,1000),'g':1,'kg':1000,'t':1000000}
VOL={'mL':1,'dL':100,'L':1000}
TIME={'秒':Fraction(1,60),'分':1,'時間':60,'日':1440,'週間':10080}
DIMS=[LEN,MASS,VOL,TIME]
ALIAS=[('キロメートル','km'),('センチメートル','cm'),('ミリメートル','mm'),('メートル','m'),('センチ','cm'),('キログラム','kg'),('ミリグラム','mg'),('グラム','g'),('トン','t'),
       ('ミリリットル','mL'),('デシリットル','dL'),('リットル','L'),('ml','mL'),('dl','dL'),('l','L')]
EN_UNIT={'millimeter':'mm','millimeters':'mm','centimeter':'cm','centimeters':'cm','meter':'m','meters':'m','kilometer':'km','kilometers':'km','km':'km','m':'m','cm':'cm','mm':'mm',
         'gram':'g','grams':'g','kilogram':'kg','kilograms':'kg','kg':'kg','g':'g','milliliter':'mL','milliliters':'mL','liter':'L','liters':'L',
         'second':'秒','seconds':'秒','minute':'分','minutes':'分','hour':'時間','hours':'時間','day':'日','days':'日','week':'週間','weeks':'週間'}
WEEK='月火水木金土日'
CONST={'ダース':12,'グロス':144}
NUM=r'(\d+(?:\.\d+)?)'

def _n(s):
    s=unicodedata.normalize('NFKC',str(s)).strip()
    s=re.sub(r'[?？。.!！\s]+$','',s)
    return s
def _units(s):
    for a,b in ALIAS:s=re.sub(a+r'(?![a-zA-Z])',b,s) if re.fullmatch(r'[a-zA-Z]+',a) else s.replace(a,b)
    return s
def _dim(u):
    for d in DIMS:
        if u in d:return d
    return None
def _fmt(v):
    v=Fraction(v);return str(v.numerator) if v.denominator==1 else format(float(v),'.12g')
UNITS_RE=r'(km|cm|mm|kg|mg|mL|dL|L|t|g|m|時間|分|秒|日|週間)'

def _parse_amount(s):
    """「2時間15分」「1km200m」「3.5km」 -> (value in base unit, dim, units used)"""
    parts=list(re.finditer(NUM+r'\s*'+UNITS_RE,s))
    if not parts or ''.join(p.group() for p in parts)!=re.sub(r'\s','',s):return None
    d=_dim(parts[0][2])
    if any(_dim(p[2]) is not d for p in parts):return None
    return sum(Fraction(p[1])*Fraction(d[p[2]]) for p in parts),d,[p[2] for p in parts]

def _conversion(s):
    m=re.fullmatch(r'(.+?)(?:は|って|を)\s*何\s*'+UNITS_RE+r'(?:何\s*'+UNITS_RE+r')?(?:ですか|か|になる|になりますか)?',s)
    if not m:return None
    a=_parse_amount(_units(m[1]))
    if not a:return None
    v,d,used=a
    if m[2] not in d or (m[3] and m[3] not in d):return None
    if m[3]:                                                   # 何時間何分
        big,small=Fraction(d[m[2]]),Fraction(d[m[3]])
        if big<=small:return None
        q,r=divmod(v,big)
        if Fraction(q).denominator!=1 or (r/small).denominator!=1:return None
        ans=f'{int(q)}{m[2]}{_fmt(r/small)}{m[3]}'
        return {'answer':ans,'kind':'conversion','expression':f'{_fmt(v)}={int(q)}*{_fmt(big)}+{_fmt(r)}'}
    out=v/Fraction(d[m[2]])
    return {'answer':_fmt(out),'kind':'conversion','unit':m[2],'expression':f'{_fmt(v)}/{_fmt(d[m[2]])}'}

def _en_conversion(s):
    s=s.lower()
    m=re.fullmatch(r'how many (\w+) (?:are )?(?:there )?in ([\d.]+) (\w+)',s) or re.fullmatch(r'(?:convert )?([\d.]+) (\w+) (?:to|into|in) (\w+)',s)
    if not m:return None
    if s.startswith('how'):tu,v,fu=m[1],m[2],m[3]
    else:v,fu,tu=m[1],m[2],m[3]
    fu,tu=EN_UNIT.get(fu),EN_UNIT.get(tu)
    if not fu or not tu:return None
    d=_dim(fu)
    if d is None or tu not in d:return None
    out=Fraction(v)*Fraction(d[fu])/Fraction(d[tu])
    return {'answer':_fmt(out),'kind':'conversion','unit':tu,'expression':f'{v}*{_fmt(d[fu])}/{_fmt(d[tu])}'}

def _clock(s):
    m=re.fullmatch(r'(午前|午後)?\s*(\d{1,2})時(?:(\d{1,2})分)?(?:から|の)\s*((?:\d+時間)?(?:\d+分)?)(後|前)(?:は|って)?\s*何時(?:何分)?(?:ですか|か|になる)?',s)
    if not m or not m[4]:return None
    h,mi=int(m[2]),int(m[3] or 0)
    if m[1] and not 0<=h<=12 or not m[1] and not 0<=h<=24 or not 0<=mi<60:return None
    if m[1]=='午後' and h<12:h+=12
    if m[1]=='午前' and h==12:h=0
    dm=re.fullmatch(r'(?:(\d+)時間)?(?:(\d+)分)?',m[4]);delta=int(dm[1] or 0)*60+int(dm[2] or 0)
    t=h*60+mi+(delta if m[5]=='後' else -delta)
    if not 0<=t<24*60:return None                      # crossing midnight: refuse rather than guess the day
    H,M=divmod(t,60)
    if m[1]:ans=f'{"午前" if H<12 else "午後"}{H if H<=12 else H-12}時{M}分' if not (H==12) else f'午後0時{M}分'
    else:ans=f'{H}時{M}分'
    return {'answer':ans,'kind':'clock','minutes':t}

def _weekday(s):
    m=re.fullmatch(r'(?:今日|きょう)は\s*([月火水木金土日])曜日?(?:です|だ)?[。、,]?\s*(\d+)日(後|前)(?:は|って)?\s*何曜日?(?:ですか|か|になる)?',s)
    if not m:return None
    i=(WEEK.index(m[1])+(int(m[2]) if m[3]=='後' else -int(m[2])))%7
    return {'answer':WEEK[i]+'曜日','kind':'weekday'}

def _calendar(s):
    m=re.fullmatch(r'(\d{4})年(\d{1,2})月(\d{1,2})日(?:の|から)\s*(\d+)日(後|前)(?:は|って)?\s*(?:何年)?何月何日(?:ですか|か|になる)?',s)
    if m:
        d=datetime.date(int(m[1]),int(m[2]),int(m[3]))+datetime.timedelta(days=int(m[4])*(1 if m[5]=='後' else -1))
        same_year=d.year==int(m[1])
        return {'answer':(f'{d.month}月{d.day}日' if same_year else f'{d.year}年{d.month}月{d.day}日'),'kind':'calendar','date':d.isoformat()}
    m=re.fullmatch(r'(\d{4})年(\d{1,2})月(\d{1,2})日(?:は|って)\s*何曜日?(?:ですか|か)?',s)
    if m:
        d=datetime.date(int(m[1]),int(m[2]),int(m[3]))
        return {'answer':WEEK[d.weekday()]+'曜日','kind':'calendar','date':d.isoformat()}
    return None

def _percent(s):
    m=re.fullmatch(NUM+r'円の\s*(?:(\d+)割(\d)分|(\d+)割|'+NUM+r'\s*(?:%|パーセント))\s*(引き|引|オフ|増し|増|)(?:は|って)?\s*(?:いくら|何円)?(?:ですか|か|になる)?',s)
    if not m:return None
    base=Fraction(m[1])
    if m[2]:rate=Fraction(int(m[2])*10+int(m[3]),100)
    elif m[4]:rate=Fraction(int(m[4]),10)
    else:rate=Fraction(m[5])/100
    if not 0<=rate<=1 and m[6] in ('引き','引','オフ'):return None
    mode=m[6]
    v=base*(1-rate) if mode in ('引き','引','オフ') else base*(1+rate) if mode in ('増し','増') else base*rate
    return {'answer':_fmt(v),'kind':'percent','expression':f'{m[1]}*'+('(1-' if mode in ('引き','引','オフ') else '(1+' if mode in ('増し','増') else '(')+f'{_fmt(rate)})'}

def _const(s):
    m=re.fullmatch(r'(\d+(?:\.\d+)?)?\s*(ダース|グロス)(?:は|って)\s*何(個|本|枚|冊|人|つ)?(?:ですか|か)?',s)
    if not m:return None
    n=Fraction(m[1] or 1)*CONST[m[2]]
    return {'answer':_fmt(n),'kind':'constant','expression':f'{m[1] or 1}*{CONST[m[2]]}'}

def solve(query):
    s=_n(query)
    if len(s)>200:return None
    try:
        if re.search(r'[぀-ヿ一-鿿]',s):
            for f in (_calendar,_weekday,_clock,_percent,_const,_conversion):
                r=f(s)
                if r:return {**r,'source_query':str(query)}
        else:
            r=_en_conversion(s)
            if r:return {**r,'source_query':str(query)}
    except (ValueError,ZeroDivisionError,OverflowError):return None
    return None

def check(proof,answer):
    r=solve(proof.get('source_query',''))
    return bool(r) and r['answer']==str(answer)==proof.get('answer') and r['kind']==proof.get('qkind')
