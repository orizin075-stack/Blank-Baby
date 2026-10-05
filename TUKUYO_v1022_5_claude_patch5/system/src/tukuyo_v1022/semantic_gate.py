"""claude-patch4: final commit gate for quantitative answers, written SEPARATELY from every producer.

A numeric answer is committed only when all three hold:
  (1) a producer proposed it,
  (2) its proof replays (proofs.check, done by the caller),
  (3) this gate passes:
      a. COVERAGE  - every numeric token of the question (incl. compound amounts like 2時間30分,
                     percentages, 割) is explained by a number in the proof (directly, by a unit
                     conversion, or as a percentage factor). Per-unit "1" (1個120円, 1人に) and
                     class labels (3年2組) are the only exemptions.
      b. ROLES     - container asked with the contents' counter (「箱は全部で何個」), a part asked
                     of an unsplit total (「りんごとみかんが合わせて20個…りんごは？」), operations
                     aimed at different objects (「商品Aを20%引き、商品Bを…」), hedged quantities.
      c. PARSER B  - for families this module can read on its own (rate x duration, percent / yen
                     price chains, calendar / weekday / clock, unit conversion; claude-patch5 adds
                     gains/losses, unit price x count and change, equal groups / sharing,
                     comparisons, one-unknown equations, simple English gains/losses) its own value must
                     equal the producer's. Disagreement blocks; agreement is recorded as
                     independent_parser='AGREE'. Otherwise 'UNDECIDED' (never reported as independent).

This file must not import any producer module (wordprob*, deliberation*, meta_reasoning*, hypothesis*,
qtime, nl_arith, cognition, logic2, kqa, proofs). tests/test_claude_patch4.py enforces that.
"""
from __future__ import annotations
import datetime,json,re,unicodedata
from fractions import Fraction

# ------------------------------------------------------------------ tokenizer (own implementation)
_KD={'〇':0,'零':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
_KU={'十':10,'百':100,'千':1000}
def _kanji_num(t):
    total=sec=part=0
    for c in t:
        if c in _KD:part=part*10+_KD[c] if part else _KD[c]
        elif c in _KU:sec+=(part or 1)*_KU[c];part=0
        elif c=='万':total+=(sec+part or 1)*10000;sec=part=0
        else:return None
    return total+sec+part

LEN={'mm':Fraction(1,1000),'cm':Fraction(1,100),'m':Fraction(1),'km':Fraction(1000)}
MASS={'mg':Fraction(1,1000),'g':Fraction(1),'kg':Fraction(1000)}
VOL={'mL':Fraction(1),'dL':Fraction(100),'L':Fraction(1000)}
TIME={'秒':Fraction(1,60),'分':Fraction(1),'時間':Fraction(60),'日':Fraction(1440),'週間':Fraction(10080)}
DIMS={'len':LEN,'mass':MASS,'vol':VOL,'time':TIME}
WORD_UNITS=[('キロメートル','km'),('センチメートル','cm'),('ミリメートル','mm'),('メートル','m'),('センチ','cm'),('キログラム','kg'),('ミリグラム','mg'),('グラム','g'),
            ('ミリリットル','mL'),('デシリットル','dL'),('リットル','L')]
EN_UNIT={'km':'km','kilometer':'km','kilometers':'km','meter':'m','meters':'m','m':'m','cm':'cm','centimeter':'cm','centimeters':'cm','kg':'kg','kilogram':'kg','kilograms':'kg',
         'g':'g','gram':'g','grams':'g','hour':'時間','hours':'時間','minute':'分','minutes':'分','second':'秒','seconds':'秒','liter':'L','liters':'L','milliliters':'mL'}
UNIT_RE=r'(km|cm|mm|kg|mg|mL|dL|L|g|m|時間|分|秒|日|週間)'

def _dim(u):
    for d,t in DIMS.items():
        if u in t:return d
    return None

def normalize(q):
    s=unicodedata.normalize('NFKC',str(q))
    for a,b in WORD_UNITS:s=s.replace(a,b)
    s=re.sub(r'[〇零一二三四五六七八九十百千万]+(?=\s*(?:個|枚|本|冊|台|人|円|匹|頭|羽|杯|回|点|粒|袋|箱|束|歳|才|つ|日|時間|分|秒|年|月|週間|割|ページ|km|m|cm|kg|g|L))',
             lambda m:str(_kanji_num(m.group())) if _kanji_num(m.group()) is not None else m.group(),s)
    return s

def tokens(q):
    """numeric tokens: {'value','unit','dim','kind','group','span'}"""
    s=normalize(q);out=[];taken=[]
    def free(a,b):return all(b<=x or a>=y for x,y in taken)
    def add(m,kind,value,unit=None,group=None,span=None):
        sp=span or m.span();out.append({'text':s[sp[0]:sp[1]],'value':Fraction(value),'unit':unit,'dim':_dim(unit) if unit else None,'kind':kind,'group':group,'span':sp})
    g=0
    for m in re.finditer(r'(\d{4})年(\d{1,2})月(\d{1,2})日',s):
        if free(*m.span()):taken.append(m.span());g+=1;[add(m,'date',m[i],None,g,m.span(i)) for i in (1,2,3)]
    for m in re.finditer(r'(\d+)年(\d+)組|第(\d+)|(\d+)号|(\d+)番目?|(\d+)年生',s):
        if free(*m.span()):taken.append(m.span());[add(m,'label',m[i],None,None,m.span(i)) for i in range(1,7) if m[i]]
    for m in re.finditer(r'(?:午前|午後)?(\d{1,2})時(?!間)(?:(\d{1,2})分)?',s):
        if free(*m.span()):taken.append(m.span());g+=1;[add(m,'clock',m[i],None,g,m.span(i)) for i in (1,2) if m[i]]
    for m in re.finditer(r'(\d+(?:\.\d+)?)\s*(時間|分)\s*(\d+(?:\.\d+)?)\s*(分|秒)|(\d+(?:\.\d+)?)\s*(km|m|L|kg)\s*(\d+(?:\.\d+)?)\s*(m|cm|mm|mL|dL|g)(?![a-zA-Z])',s):
        if free(*m.span()):
            taken.append(m.span());g+=1
            if m[1]:add(m,'num',m[1],m[2],g,m.span(1));add(m,'num',m[3],m[4],g,m.span(3))
            else:add(m,'num',m[5],m[6],g,m.span(5));add(m,'num',m[7],m[8],g,m.span(7))
    for m in re.finditer(r'(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)\s*(?:and\s*)?(\d+)\s*minutes?',s,re.I):
        if free(*m.span()):taken.append(m.span());g+=1;add(m,'num',m[1],'時間',g,m.span(1));add(m,'num',m[2],'分',g,m.span(2))
    for m in re.finditer(r'(\d+(?:\.\d+)?)\s*(?:%|パーセント|percent)',s,re.I):
        if free(*m.span()):taken.append(m.span());add(m,'percent',m[1],None,None,m.span(1))
    for m in re.finditer(r'(\d+)\s*割(?:\s*(\d)\s*分)?',s):
        if free(*m.span()):taken.append(m.span());add(m,'wari',Fraction(int(m[1]),10)+(Fraction(int(m[2]),100) if m[2] else 0),None,None,m.span())
    for m in re.finditer(r'(\d+(?:\.\d+)?)',s):
        if not free(*m.span()):continue
        after=s[m.end():m.end()+12];before=s[max(0,m.start()-6):m.start()]
        um=re.match(r'\s*'+UNIT_RE+r'(?![a-zA-Z])',after);em=re.match(r'\s*([a-zA-Z]+)',after)
        unit=um[1] if um else (EN_UNIT.get(em[1].lower()) if em else None)
        if m.group()=='1' and (re.match(r'\s*(?:個|枚|本|冊|台|人|袋|箱|束|パック|ケース|日|時間|分間?|秒|週間?|か月|ヶ月|年|皿|組|回|杯|ページ|L|kg|km|m|g)\s*(?:に|あたり|当たり|で|の|につき|何|は何|\d)',after)
                               or re.match(r'\s*(?:個|本|冊|枚|袋|箱)\s*\d',after) or re.search(r'\b(?:per|each|every|a|an)\s*$',before)):
            add(m,'per_unit_one',1);continue
        add(m,'num',m.group(),unit)
    return out

# ------------------------------------------------------------------ proof numbers and explanation
TEXT_KEYS={'source_query','query','question','normalized_query','clause','text','surface','explanation','label','answer','definition','records','task'}
def _proof_numbers(proof):
    """numbers the proof actually computes with; question text copied into the proof never counts"""
    vals=[]
    def walk(x,key=None):
        if key in TEXT_KEYS:return
        if isinstance(x,dict):
            for k,v in x.items():walk(v,k)
        elif isinstance(x,(list,tuple)):
            for v in x:walk(v,key)
        elif isinstance(x,bool) or x is None:return
        elif isinstance(x,(int,float)):vals.append(str(x))
        elif isinstance(x,str) and re.fullmatch(r'[\w\s.+\-*/()%#]{1,240}',x,re.A) and not re.search(r'[a-zA-Z]{3,}\s+[a-zA-Z]{2,}',x):vals.append(x)
    walk(proof)
    nums=set()
    for v in vals:
        for m in re.finditer(r'(?<![\w.])(\d+(?:\.\d+)?)(?:/(\d+(?:\.\d+)?))?',v):
            try:nums.add(Fraction(m[1])/Fraction(m[2]) if m[2] else Fraction(m[1]))
            except (ZeroDivisionError,ValueError):pass
            nums.add(Fraction(m[1]))
            if m[2]:nums.add(Fraction(m[2]))
    return nums

def _explained(t,P,groups):
    v=t['value']
    if t['kind'] in ('per_unit_one','label'):return True
    if v in P:return True
    if t['dim']:
        table=DIMS[t['dim']]
        if any(v*table[t['unit']]/f in P for f in table.values()):return True
    if t['group'] is not None and t['dim']:
        table=DIMS[t['dim']];total=groups.get(t['group'])
        if total is not None and any(total/f in P for f in table.values()):return True
    if t['kind']=='percent':return bool({v/100,1-v/100,1+v/100,100-v,100+v}&P)
    if t['kind']=='wari':return bool({v,1-v,1+v,v*100,100-v*100,100+v*100,v*10}&P)
    return False

# ------------------------------------------------------------------ role checks
CONT=r'(?:箱|袋|パック|ケース|束|かご|皿|缶|瓶)'
HEDGE=re.compile(r'予定|つもり|かもしれ|だろう|らしい|約\s*\d|およそ|(?<![のれ])(?:ぐらい|くらい)|(?<!先)ほど|程度|たぶん|多分|(?:何個|何人|何本|何枚|何冊|いくつ)か(?![？?。!！な]|$)|たくさん|\bmaybe\b|\babout\s+\d|\bapproximately\b|\bmight\b|\bsome\b|\bseveral\b',re.I)
def _roles(q,answer):
    s=normalize(q)
    if re.search(CONT+r'(?:は|の数は|が)?\s*(?:全部で|合わせて|合計|あわせて)?\s*(?:何個|いくつ|何つ)',s) and not re.search(r'中身|中に|入って(?:いる|る)?(?:もの|数)',s):
        pk=re.search(r'1\s*'+CONT+r'\s*(?:に|あたり)?\s*(\d+)\s*個\s*入り[^。]*?(\d+)\s*'+CONT,s) or re.search(r'(\d+)\s*個\s*入り(?:の)?[^。]{0,6}?(?:を|が)?\s*(\d+)\s*(?:'+CONT+r'|つ)',s)
        if pk and str(answer)==str(int(pk[1])*int(pk[2])):return 'CONTAINER_OR_CONTENT_AMBIGUOUS'   # contents total given for a container question
    m=re.search(r'([^、。はがを\d]{1,10})と([^、。はがを\d]{1,10})(?:が|は)?\s*(?:合わせて|全部で|合計で?|あわせて)\s*(\d+)',s)
    if m:
        qm=re.search(r'([^、。はがを\d]{1,10})(?:は|が)\s*(?:何|いくつ)',s[m.end():])
        if qm and qm[1] in (m[1],m[2]) and str(answer)==m[3]:return 'PART_ASKED_OF_UNSPLIT_TOTAL'
    objs=set(re.findall(r'(?:商品|品物|品)?([A-ZＡ-Ｚa-z])を\s*\d+\s*(?:%|パーセント|割|円)',s))
    if len(objs)>=2:return 'AMBIGUOUS_OPERATION_TARGET'
    if HEDGE.search(s):return 'HEDGED_QUANTITY'
    return None

# ------------------------------------------------------------------ parser B (independent readings)
WEEK='月火水木金土日'
def _num(x):return Fraction(x)
def _fmt(v):
    v=Fraction(v);return str(v.numerator) if v.denominator==1 else format(float(v),'.12g')

def _b_rate(s,toks):
    m=re.search(r'(時速|分速|秒速)\s*(\d+(?:\.\d+)?)\s*(km|m)',s)
    if m:per={'時速':'時間','分速':'分','秒速':'秒'}[m[1]];rate=_num(m[2]);ru=m[3]
    else:
        m=re.search(r'(\d+(?:\.\d+)?)\s*(km|m|kilometers?|meters?)\s*(?:per|an|a|/)\s*(hour|h|minute|min)\b',s,re.I)
        if not m:return None
        per={'hour':'時間','h':'時間','minute':'分','min':'分'}[m[3].lower()];rate=_num(m[1]);ru=EN_UNIT.get(m[2].lower(),m[2])
    durs=[t for t in toks if t['dim']=='time' and not (t['span'][0]>=m.start() and t['span'][1]<=m.end())]
    others=[t for t in toks if t['kind'] not in ('per_unit_one','label') and t['dim']!='time' and not (m.start()<=t['span'][0]<m.end())]
    if not durs or others:return None
    groups={t['group'] for t in durs}
    if len(groups)>1 or (None in groups and len(durs)>1):return None
    minutes=sum(t['value']*TIME[t['unit']] for t in durs)
    a=re.search(r'何\s*(km|m)|how far|how many (kilometers|km|meters|m)\b',s,re.I)
    if not a:return None
    target=(a[1] or EN_UNIT.get((a[2] or '').lower(),ru)) if (a[1] or a[2]) else ru
    if _dim(target)!='len':return None
    dist=rate*minutes/TIME[per]*LEN[ru]/LEN[target]
    return _fmt(dist)

DOWN=r'(?:引き|引|割引き?|値引き?|オフ|off|安く|discount(?:ed)?(?:\s+by)?|reduced\s+by|less)'
UP=r'(?:増し|増|値上げ|アップ|上乗せ|高く|raise[ds]?(?:\s+by)?|increased?\s+by|more)'
def _b_price(s,toks):
    if re.search(r'おつり|お釣り|change\b',s,re.I):return None
    base=re.search(r'(\d+(?:\.\d+)?)\s*(円|dollars?|yen)',s,re.I)
    if not base:return None
    ops=[]
    for m in re.finditer(r'(\d+(?:\.\d+)?)\s*(%|パーセント|percent|割|円|dollars?)\s*(?:を|に|だけ|分)?\s*('+DOWN+'|'+UP+')|(?:'+'(discounted|reduced|raised|increased)'+r')\s*by\s*(\d+(?:\.\d+)?)\s*(%|percent|dollars?)',s[base.end():],re.I):
        if m[1]:val,kind,dirw=_num(m[1]),m[2],m[3]
        else:val,kind,dirw=_num(m[5]),m[6],m[4]
        sign=-1 if re.fullmatch(DOWN,dirw,re.I) or (dirw or '').lower() in ('discounted','reduced') else 1
        k='pct' if kind in ('%','パーセント') or kind.lower()=='percent' else 'wari' if kind=='割' else 'abs'
        ops.append((k,val,sign))
    if not ops:return None
    used=1+len(ops)
    if len([t for t in toks if t['kind'] not in ('per_unit_one','label')])!=used:return None
    v=_num(base[1])
    for k,val,sign in ops:
        if k=='pct':v=v*(1+sign*val/100)
        elif k=='wari':v=v*(1+sign*val/10)
        else:v=v+sign*val
    if v<0:return None
    return _fmt(v)

def _b_calendar(s):
    m=re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日(?:の|から)\s*(\d+)日(後|前)',s)
    if m:
        d=datetime.date(int(m[1]),int(m[2]),int(m[3]))+datetime.timedelta(days=int(m[4])*(1 if m[5]=='後' else -1))
        return ('date',d)
    m=re.fullmatch(r'\s*(\d{4})年(\d{1,2})月(\d{1,2})日(?:は|って)\s*何曜日?\s*(?:ですか|か)?\s*[?？]?\s*',s)
    if m:return ('weekday',WEEK[datetime.date(int(m[1]),int(m[2]),int(m[3])).weekday()])
    m=re.search(r'(?:今日|きょう)は\s*([月火水木金土日])曜日?.*?(\d+)日(後|前)',s)
    if m:return ('weekday',WEEK[(WEEK.index(m[1])+int(m[2])*(1 if m[3]=='後' else -1))%7])
    m=re.search(r'(午前|午後)?(\d{1,2})時(?!間)(?:(\d{1,2})分)?(?:から|の)\s*(?:(\d+)時間)?(?:(\d+)分)?(後|前)',s)
    if m and (m[4] or m[5]):
        h=int(m[2]);mi=int(m[3] or 0)
        if m[1]=='午後' and h<12:h+=12
        if m[1]=='午前' and h==12:h=0
        t=h*60+mi+(1 if m[6]=='後' else -1)*(int(m[4] or 0)*60+int(m[5] or 0))
        if 0<=t<1440:return ('clock',divmod(t,60))
    return None

def _b_conversion(s,toks):
    m=re.search(r'(?:は|って)\s*何\s*'+UNIT_RE+r'(?:\s*何\s*'+UNIT_RE+r')?\s*(?:ですか|か)?\s*[?？]?\s*$',s)
    if not m:
        e=re.search(r'how many (\w+) (?:are )?(?:there )?in',s,re.I)
        if not e:return None
        target=EN_UNIT.get(e[1].lower());second=None
    else:target,second=m[1],m[2]
    q=[t for t in toks if t['kind']=='num']
    if not q or not target or any(t['dim']!=_dim(target) for t in q) or len({t['group'] for t in q})>1:return None
    if len(q)>1 and q[0]['group'] is None:return None
    total=sum(t['value']*DIMS[t['dim']][t['unit']] for t in q)
    if second:
        big,small=DIMS[_dim(target)][target],DIMS[_dim(target)][second]
        a,b=divmod(total,big)
        return f'{int(a)}{target}{_fmt(b/small)}{second}'
    return _fmt(total/DIMS[_dim(target)][target])

# ---- claude-patch5: Parser B for the common word-problem families.
# Written from scratch for this file (own clause splitter, own verb lexicon, own question reader).
# Every reader returns None unless it can account for EVERY numeric token of the question by itself,
# so an AGREE always means "a second, separately written reading used all the numbers the same way".
CNT=r'(?:個|こ|枚|まい|本|ほん|ぽん|ぼん|冊|さつ|台|人|にん|匹|ひき|ぴき|びき|頭|羽|わ|杯|粒|袋|箱|束|つ|ページ|まい|cm|mL|L|kg|g|m|円|点|回|台|脚|足|着|輪|切れ|玉|房)'
B_DEC=('降り','おり','下車','飲み','飲ん','のみ','のん','食べ','たべ','使い','使っ','使う','つかい','つかっ','あげ','渡し','わたし','落とし','おとし','なくし','無くし','失くし','減っ','減り','へっ','へり','捨て','すて',
       '割れ','われ','飛んで','とんで','飛び去','逃げ','にげ','帰っ','帰り','かえっ','かえり','出て行','でていっ','食われ','こぼれ','こわれ','壊れ','配っ','配り','くばっ','くばり','取り出し','とりだし','引い','ひい','切り取','売れ')
B_INC=('もらい','もらっ','貰い','貰っ','買い','買っ','かい','かっ','増え','ふえ','拾い','拾っ','ひろい','ひろっ','追加し','足し','たし','来まし','来た','きまし','きた','入れ','いれ','加わ','くわわ','作り','作っ','つくり','つくっ',
       '咲い','咲き','さい','さき','生まれ','うまれ','届い','とどい','集め','あつめ','見つけ','みつけ','借り','かり','乗ってき','のってき','やってき','増やし','ふやし')
B_AMBIG=('売っ','売り','売る','返品','仕入','貸し','貸す','かし','返し','返す','預け','あずけ','払っ','はらっ','交換','両替','借りて','かりて')
def _b_sentences(s):
    return [x.strip() for x in re.split(r'[。．!！?？\n]+',s) if x.strip()]
def _b_question(sents):
    qs=[x for x in sents if re.search(r'何|いくつ|いくら|how many|how much',x,re.I)]
    return qs[-1] if len(qs)==1 else None
def _b_numcount(toks):return len([t for t in toks if t['kind'] not in ('per_unit_one','label')])
def _b_nums(x):return [Fraction(n) for n in re.findall(r'\d+(?:\.\d+)?',x)]

def _b_change(s,toks):
    """initial amount, then gains/losses described by an unambiguous verb each, then 'how many now/left'."""
    sents=_b_sentences(s);q=_b_question(sents)
    if q is None or HEDGE.search(s) or re.search(r'ません|なかっ|ない[^ぶ]|ずつ|倍|円|%|割|何(?:人|個|本|枚|冊|匹)?(?:多|少)|ちがい|違い|差|より',s):return None
    if not re.search(r'残り|のこり|今|いま|現在|全部で|ぜんぶで|合わせて|あわせて|になり|になって|になった|は何|はいくつ',q):return None
    body=[x for x in sents if x is not q]
    if not body:return None
    m=re.search(r'(\d+(?:\.\d+)?)\s*('+CNT+r')\s*(?:の[^\d、。]{0,6})?\s*(?:あり|あっ|ある|い(?:ます|まし|る|た)|持って|もって|入って|はいって|咲いて|さいて|乗って|のって|泳いで|およいで|すわって|座って|飼って|かって)',body[0])
    if not m or len(_b_nums(body[0]))!=1:return None
    c=m[2];total=Fraction(m[1]);used=1
    rest=' '.join(body[1:])+(' '+q if _b_nums(q) else '')
    for ev in re.finditer(r'(\d+(?:\.\d+)?)\s*('+CNT+r')([^\d]*)',rest):
        if ev[2]!=c:return None
        tail=ev[3]
        if any(a in tail for a in B_AMBIG):return None
        core=re.sub(r'^(?:[\s、]|[をがはにへ](?![らりるれろいう]))*(?:さらに|また|あとから|後から|その後|そのあと|新しく|あたらしく)?(?:[\s、]|[をがはにへ](?![らりるれろいう]))*','',tail)
        core=re.sub(r'^[^\s、。]{1,6}?を','',core) if not core.startswith(B_DEC+B_INC) else core
        dec=core.startswith(B_DEC);inc=core.startswith(B_INC)
        if bool(dec)==bool(inc):return None
        total+=Fraction(ev[1])*(-1 if dec else 1);used+=1
    if used<2 or used!=_b_numcount(toks) or total<0:return None
    return _fmt(total)

ITEM_CNT=r'(個|本|冊|枚|袋|台|箱|パック|杯|皿|つ|足|着|個入り|kg|g|L)'
def _b_unit_price(s,toks):
    """price per item x number of items (several items allowed), optionally paid with a bill -> change."""
    if HEDGE.search(s) or re.search(r'%|パーセント|割|引き|値上げ|ずつ|倍|あまり|余り',s):return None
    q=_b_question(_b_sentences(s))
    if q is None:return None
    total=Fraction(0);used=0;spans=[]
    for m in re.finditer(r'1\s*'+ITEM_CNT+r'\s*(\d+(?:\.\d+)?)\s*円の\s*[^、。を\d]{1,14}?\s*を\s*(\d+(?:\.\d+)?)\s*(?:\1|つ)',s):
        total+=Fraction(m[2])*Fraction(m[3]);used+=2;spans.append(m.span())
    for m in re.finditer(r'(?<!1)(?<![\d.])(\d+(?:\.\d+)?)\s*円の\s*[^、。を\d]{1,14}?\s*を\s*(\d+(?:\.\d+)?)\s*'+ITEM_CNT,s):
        if any(a<=m.start()<b for a,b in spans):continue
        total+=Fraction(m[1])*Fraction(m[2]);used+=2;spans.append(m.span())
    if not used:return None
    pay=re.search(r'(\d+(?:\.\d+)?)\s*円(?:札|玉)?\s*(?:を|で)?\s*(?:出|だ|払|はら|渡|わた)',s)
    asks_change=re.search(r'おつり|お釣り|おつりは|残り|のこり',q)
    if asks_change:
        if not pay or any(a<=pay.start()<b for a,b in spans):return None
        used+=1;total=Fraction(pay[1])-total
        if total<0:return None
    elif pay or not re.search(r'代金|いくら|何円|合計|全部で|ぜんぶで|あわせて|合わせて',q):return None
    if used!=_b_numcount(toks):return None
    return _fmt(total)

GRP=r'(人|箱|袋|皿|列|組|台|日|週|週間|か月|ヶ月|回|チーム|班|かご|ケース|パック|段|ページ)'
def _b_groups(s,toks):
    """equal groups: N per group x M groups; N shared equally by M; N handed out M each (how many people / remainder)."""
    if HEDGE.search(s) or re.search(r'円|%|割|倍|より',s):return None
    q=_b_question(_b_sentences(s))
    if q is None:return None
    n=_b_numcount(toks)
    if re.search(CONT+r'\s*(?:は|が|の数)',q) or re.search(r'できます|できる|作れ|つくれ|何\s*(?:グループ|組|チーム|班|列)',q):
        # the question asks for a number of groups: only the partition reading (same counter) applies
        m=re.search(r'(\d+)\s*('+CNT+r')[^？?]*?(\d+)\s*\2\s*ずつ',s)
        if m and n==2 and int(m[3]):
            a,b=int(m[1]),int(m[3])
            if re.search(r'あまり|余り|のこり|残り',q):return str(a%b)
            return str(a//b)
        return None
    m=re.search(r'(\d+)\s*(人|にん)[^？?]*?1\s*(?:人|にん)\s*(?:に|あたり|につき)?\s*(\d+(?:\.\d+)?)\s*('+CNT+r')\s*ずつ',s)
    if m and n==2 and m[4] not in ('人','にん') and re.search(r'全部で|ぜんぶで|合わせて|あわせて|みんなで|何'+CNT+'|いくつ',q):return _fmt(Fraction(m[1])*Fraction(m[3]))
    m=re.search(r'(\d+(?:\.\d+)?)\s*('+CNT+r')\s*ずつ[^。]*?(\d+)\s*'+GRP,s) or re.search(r'(?<![\d.])([2-9]|\d{2,})\s*'+GRP+r'\s*(?:に|へ|で|の)?[^。\d]{0,10}?(\d+(?:\.\d+)?)\s*('+CNT+r')\s*ずつ',s)
    if m and m.re.pattern.startswith('(?<!') and m[2]==m[4]:m=None      # 「35人…5人ずつ」 is a partition, not a product
    if m and n==2 and re.search(r'全部で|ぜんぶで|合わせて|あわせて|みんなで|何'+CNT+'|いくつ|何'+CNT+r'?(?:いり|必要)',q) and not re.search(r'何\s*'+GRP+r'(?!.*何)',q):
        return _fmt(Fraction(m[1])*Fraction(m[3]))
    m=re.search(r'1\s*'+GRP+r'\s*(?:に|あたり|につき|の)?\s*(\d+(?:\.\d+)?)\s*('+CNT+r')[^。]*?(\d+)\s*\1',s)
    if m and n==2 and re.search(r'全部で|ぜんぶで|合わせて|あわせて|何'+CNT+'|いくつ',q):return _fmt(Fraction(m[2])*Fraction(m[4]))
    m=re.search(r'(\d+)\s*('+CNT+r')[^？?]*?(\d+)\s*(?:人|にん)\s*で\s*(?:同じ数ずつ|おなじ数ずつ|等しく|同じように|同じ数に|なかよく)?\s*(?:分け|わけ)',s)
    if m and n==2 and re.search(r'1\s*人|ひとり|一人',q) and not re.search(r'あまり|余り',q):
        a,b=int(m[1]),int(m[3])
        return _fmt(Fraction(a,b)) if b and a%b==0 else None
    m=re.search(r'(\d+)\s*('+CNT+r')[^？?]*?1\s*(?:人|にん)\s*(?:に|あたり)?\s*(\d+)\s*\2\s*ずつ\s*(?:配|くば|分け|わけ|あげ)',s)
    if m and n==2:
        a,b=int(m[1]),int(m[3])
        if not b:return None
        if re.search(r'あまり|余り|のこり|残り',q):return str(a%b)
        if re.search(r'何人|なんにん',q):return str(a//b)
    return None

def _b_compare(s,toks):
    """A has N; B has M more / fewer than A (or K times A); question about B, the total, or the difference."""
    if HEDGE.search(s) or re.search(r'%|割|ずつ',s):return None
    sents=_b_sentences(s);q=_b_question(sents)
    if q is None or _b_numcount(toks)!=2:return None
    m1=re.search(r'([^\s、。は]{1,8})\s*は\s*[^\d。]{0,12}?(\d+(?:\.\d+)?)\s*('+CNT+r')\s*(?:持って|もって|あり|あっ|い(?:ます|まし)|です|集め|あつめ|拾い|読み|よみ|作り|つくり|買い|かい|もらい|飼って|食べ|たべ|とり|取り|釣り|つり|の)',s)
    m2=re.search(r'([^\s、。は]{1,8})\s*は\s*([^\s、。は]{1,8})\s*より\s*(\d+(?:\.\d+)?)\s*('+CNT+r')\s*(多|おお|少な|すくな)',s)
    m3=re.search(r'([^\s、。は]{1,8})\s*は\s*([^\s、。は]{1,8})\s*の\s*(\d+(?:\.\d+)?)\s*倍',s)
    if m1 and (m2 or m3):
        a_name=re.sub(r'^(?:[^\s、。]*?の)','',m1[1]);a=Fraction(m1[2])
        if m2:
            b_name,ref=m2[1],m2[2]
            if ref not in (m1[1],a_name) and not m1[1].endswith(ref):return None
            if m2[4]!=m1[3]:return None
            b=a+Fraction(m2[3])*(1 if m2[5] in ('多','おお') else -1)
        else:
            b_name,ref=m3[1],m3[2]
            if ref not in (m1[1],a_name) and not m1[1].endswith(ref):return None
            b=a*Fraction(m3[3])
        if b<0:return None
        if re.search(r'合わせて|あわせて|全部で|ぜんぶで|二人で|2人で|ふたりで',q):return _fmt(a+b)
        if re.search(re.escape(b_name)+r'\s*(?:は|が|の)',q) and not re.search(re.escape(a_name)+r'\s*(?:は|が)',q):return _fmt(b)
        return None
    if re.search(r'ちがい|違い|差|何\s*'+CNT+r'?\s*(?:多|少)|どちらが',q):
        vals=[t['value'] for t in toks if t['kind'] not in ('per_unit_one','label')]
        units={t['unit'] for t in toks if t['kind']=='num'}
        if len(vals)==2 and not re.search(r'より|倍|もらい|あげ|食べ|使',s) and len(units)<=1:return _fmt(abs(vals[0]-vals[1]))
    return None

EQ_OP=[(r'に\s*(\d+(?:\.\d+)?)\s*を?\s*(?:足|た|加|くわ)','add'),(r'から\s*(\d+(?:\.\d+)?)\s*を?\s*(?:引|ひ)','sub'),(r'を\s*(\d+(?:\.\d+)?)\s*倍','mul'),
       (r'に\s*(\d+(?:\.\d+)?)\s*を?\s*(?:かけ|掛け)','mul'),(r'を\s*(\d+(?:\.\d+)?)\s*で\s*(?:割|わ)','div')]
def _b_equation(s,toks):
    """'ある数' / '□' with up to two operations then '= K': solved backwards, then checked forwards."""
    m=re.search(r'(ある数|□|ある整数)(.*?)(?:と|たら|ところ|すると|したら)\s*(\d+(?:\.\d+)?)\s*(?:に|と)?\s*(?:なり|なる|なった|でした|です|になり)',s)
    if not m or HEDGE.search(s):return None
    body=m[2];ops=[];pos=0
    chain=re.split(r'(?:して|し、|てから|、|して、)',body)
    for part in chain:
        part=part.strip()
        if not part:continue
        hit=None
        for pat,kind in EQ_OP:
            mm=re.match(r'\s*'+pat,part)
            if mm:hit=(kind,Fraction(mm[1]));break
        if not hit:
            mm=re.match(r'\s*(\d+(?:\.\d+)?)\s*を?\s*(?:足|た|加|くわ)',part) or None
            if mm:hit=('add',Fraction(mm[1]))
            mm2=re.match(r'\s*(\d+(?:\.\d+)?)\s*を?\s*(?:引|ひ)',part)
            if mm2:hit=('sub',Fraction(mm2[1]))
            mm3=re.match(r'\s*(\d+(?:\.\d+)?)\s*倍',part)
            if mm3:hit=('mul',Fraction(mm3[1]))
        if not hit:return None
        ops.append(hit)
    if not 1<=len(ops)<=2:return None
    if _b_numcount(toks)!=len(ops)+1:return None
    x=Fraction(m[3])
    for kind,v in reversed(ops):
        if kind=='add':x-=v
        elif kind=='sub':x+=v
        elif kind=='mul':
            if v==0:return None
            x/=v
        else:x*=v
    y=x
    for kind,v in ops:
        y={'add':y+v,'sub':y-v,'mul':y*v,'div':y/v if v else None}[kind]
        if y is None:return None
    if y!=Fraction(m[3]):return None
    return _fmt(x)

EN_DEC=r'(?:ate|eats|eat|gave away|gives away|give away|lost|loses|lose|used|uses|use|broke|breaks|dropped|drops|spent|spends)'
EN_INC=r'(?:got|gets|get|found|finds|find|received|receives|bought|buys|buy|picked|picks|collected|collects|was given|is given|won|wins|made|makes|baked|bakes)'
def _b_en_change(s,toks):
    if HEDGE.search(s) or re.search(r'\beach\b|\btimes\b|\btwice\b|\bper\b|\bmore than\b|\bfewer than\b|\bless than\b|\bsold\b|\bsells\b|\blent\b|\bborrowed\b|\$|dollars?|\bcents?\b',s,re.I):return None
    if not re.search(r'how many[^.?]*\b(?:left|now|in all|altogether|in total|remain)',s,re.I):return None
    m=re.search(r'\b(?:has|had|have|there (?:are|were)|owns?|owned)\s+(\d+)\s+([a-z]+)',s,re.I)
    if not m:return None
    total=Fraction(m[1]);used=1
    for ev in re.finditer(r'\b('+EN_DEC+'|'+EN_INC+r')\s+(?:\w+\s+){0,2}?(\d+)\b',s[m.end():],re.I):
        total+=Fraction(ev[2])*(-1 if re.fullmatch(EN_DEC,ev[1],re.I) else 1);used+=1
    if used<2 or used!=_b_numcount(toks) or total<0:return None
    return _fmt(total)

def parser_b(q):
    s=normalize(q);toks=tokens(q)
    try:
        cal=_b_calendar(s)
        if cal:return cal
        for f in (_b_rate,_b_price,_b_conversion,_b_unit_price,_b_groups,_b_compare,_b_equation,_b_change,_b_en_change):
            v=f(s,toks)
            if v is not None:return ('value',v)
    except (ValueError,ZeroDivisionError,OverflowError):return None
    return None

def _agree(b,answer):
    a=unicodedata.normalize('NFKC',str(answer)).replace(' ','')
    kind,v=b
    if kind=='value':
        nums=re.findall(r'\d+(?:\.\d+)?',a)
        if re.search(r'時間|[a-zA-Z]',v):return v in a
        return bool(nums) and any(Fraction(n)==Fraction(v) for n in nums) and len(nums)==1
    if kind=='date':
        m=re.search(r'(?:(\d{4})年)?(\d{1,2})月(\d{1,2})日',a)
        return bool(m) and int(m[2])==v.month and int(m[3])==v.day and (not m[1] or int(m[1])==v.year)
    if kind=='weekday':return a.startswith(v)
    if kind=='clock':
        m=re.search(r'(午前|午後)?(\d{1,2})時(\d{1,2})分',a)
        if not m:return False
        h=int(m[2])+(12 if m[1]=='午後' and int(m[2])<12 else 0)-(12 if m[1]=='午前' and int(m[2])==12 else 0)
        return (h,int(m[3]))==tuple(v)
    return False

# ------------------------------------------------------------------ the gate
QUANT_KINDS={'arithmetic','deliberation','meta_derivation','hypothesis','inventory','qtime'}
def audit(query,answer,proof):
    if not isinstance(proof,dict) or proof.get('kind') not in QUANT_KINDS:return {'ok':True,'applied':False}
    toks=tokens(query);P=_proof_numbers(proof)
    groups={}
    for t in toks:
        if t['group'] is not None and t['dim']:groups[t['group']]=groups.get(t['group'],0)+t['value']*DIMS[t['dim']][t['unit']]
    b=parser_b(query)
    agreed=b is not None and _agree(b,answer)
    if b is not None and not agreed:
        return {'ok':False,'applied':True,'reason':'INDEPENDENT_PARSER_DISAGREES','independent_reading':str(b[1])}
    # parser B consumed the question with its own tokenizer when it agreed; otherwise every token must be explained
    unexplained=[] if agreed else [t['text'] for t in toks if t['kind'] in ('date','clock') or not _explained(t,P,groups)]
    if unexplained:return {'ok':False,'applied':True,'reason':'UNCOVERED_NUMERIC_OR_OPERATION','unexplained':unexplained}
    role=_roles(query,answer)
    if role:return {'ok':False,'applied':True,'reason':role}
    return {'ok':True,'applied':True,'coverage':'ALL_NUMERIC_TOKENS_EXPLAINED','independent_parser':'AGREE' if agreed else 'UNDECIDED','tokens':len(toks)}
