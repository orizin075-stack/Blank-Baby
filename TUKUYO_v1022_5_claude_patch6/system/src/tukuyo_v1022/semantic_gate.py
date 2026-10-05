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
    s=unicodedata.normalize('NFKC',str(q)).replace('平方センチメートル','平方cm').replace('平方メートル','平方m')
    s=re.sub(r'(cm|mm|km|m)2(?![\d])',r'平方\1',s)          # claude-patch6: cm² is a unit with an exponent
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
B_INC6=('飛んでき','とんでき','飛んで来','やって来','入ってき','入って来','はいってき','戻ってき','もどってき','返ってき','かえってき','帰ってき','乗ってきま')   # claude-patch6
B_DEC6=('借りられ','かりられ','持っていかれ','もっていかれ','食べられ','たべられ','取られ','とられ')   # passive: taken from the holder
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
        # claude-patch6: the longest matching stem decides (飛んできました is 飛んでき+, not 飛んで-)
        dl=max((len(x) for x in B_DEC+B_DEC6 if core.startswith(x)),default=0);il=max((len(x) for x in B_INC+B_INC6 if core.startswith(x)),default=0)
        if dl==il:return None
        dec=dl>il
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

# ---- claude-patch6: Parser B reads WHAT is asked before reading any value.
# patch5's change readers added up every gain and loss for 「…あげたのは何個？」 and 「妹は何個持っていますか？」,
# so they "independently" agreed with the producer's wrong remainder. These readers are again written only
# for this file: own question-role patterns, own stock / event splitter, own stems.
B_STATE=r'(?:あり|あっ|ある|い(?:ます|まし|る|た|て)|持って|もって|入って|はいって|咲いて|さいて|乗って|のって|泳いで|およいで|すわって|座って|飼って)'
B_GIVE=('あげ','渡し','わたし','配っ','配り','くばっ','くばり','プレゼント')
def _b_qrole(q):
    if re.search(r'はじめ|初め|最初|もともと|元々|もとは|\bat first\b|\bin the beginning\b|\bto (?:begin|start) with\b|\boriginally\b',q,re.I):return 'initial'
    if re.search(r'(?:る|う|く|す|つ|む|ぶ|ぐ|ぬ)前(?:は|に)',q):return 'before'
    if re.search(r'(?:た|だ)(?:の|数)(?:は|が)',q) and not re.search(r'(?:てい|でい|ってい)たの',q):return 'event'
    m=re.search(r'何\s*'+CNT+r'\s*([^\d、。？?]{1,8}?)(?:まし)?たか',q)
    if m and not re.match(r'(?:あり|い|持ってい|もってい|乗ってい|のってい|入ってい|残ってい|にな|あっ)',m[1]):return 'event'
    if not re.search(r'\b(?:have|has|had)\b',q,re.I) and (re.search(r'\b(?:did|does|do)\s+\w+\s+(?:give|eat|use|spend|get|receive|buy|find|win|make|read)\b',q,re.I)
            or re.search(r'\bhow many\s+(?:\w+\s+)?(?:flew away|left|came|arrived|got off|got on|went home|ran away)\b',q,re.I)):return 'event'
    return 'remain'

def _b_stem(v):
    k=re.match(r'[一-鿿]+',v);base=k.group() if k else v[:2]
    if re.search(r'(?:て|で)(?:き|来)',v):return base+'+'          # 飛んできた
    if re.search(r'(?:て|で)(?:いっ|いき|行)',v):return base+'-'    # 飛んでいった
    return base

def _b_story(s):
    """first sentence = the stock (one amount + a being/holding verb); every later amount = an event with its
    own verb text and the words right before it. None unless every number of the body is read."""
    sents=_b_sentences(s);q=_b_question(sents)
    if q is None or q!=sents[-1] or len(sents)<2:return None
    body=sents[:-1]
    m=re.search(r'(\d+(?:\.\d+)?)\s*('+CNT+r')\s*(?:の[^\d、。]{0,6})?\s*(?:が|を|は)?'+B_STATE,body[0])
    if not m or len(_b_nums(body[0]))!=1:return None
    head=body[0][:m.start()]
    noun=re.search(r'([^\d、。はがをに]{1,8})(?:が|を|は)\s*$',head);owner=re.match(r'^([^\d、。]{1,8}?)(?:は|には|に)',head)
    events=[];text='。'.join(body[1:])
    for ev in re.finditer(r'([^\d。、]{0,10})(\d+(?:\.\d+)?)\s*('+CNT+r')([^\d、。]*)',text):
        if ev[3]!=m[2]:return None
        verb=re.sub(r'^(?:[をがは]|さらに|また)+','',ev[4].strip())
        events.append({'n':Fraction(ev[2]),'pre':ev[1],'verb':verb})
    for i in range(len(events)-2,-1,-1):           # 「兄に15枚、弟に10枚あげました」: a listed amount takes the next verb
        if not events[i]['verb']:events[i]['verb']=events[i+1]['verb']
    if 1+len(events)!=len(_b_nums(' '.join(body))):return None
    return {'q':q,'stock':Fraction(m[1]),'unit':m[2],'noun':noun[1] if noun else None,'owner':owner[1] if owner else None,'events':events}

def _b_roles(s,toks):
    """initial / before / event / received. The value of these never depends on whether a verb adds or removes."""
    if HEDGE.search(s) or re.search(r'ません|なかっ|ない[^ぶ]|ずつ|倍|%|割|より|ちがい|違い|差',s):return None
    st=_b_story(s)
    if not st:return None
    q=st['q'];role=_b_qrole(q)
    if _b_numcount(toks)!=1+len(st['events']):return None
    if role=='initial':
        who=re.search(r'([^\d、。はが]{1,8})(?:は|が)\s*何',q)
        if who and who[1] not in (st['noun'] or '',st['owner'] or '') and not re.search(r'はじめ|最初|初め',who[1]):return None
        return _fmt(st['stock'])
    if role=='before':
        bm=re.search(r'([^\d、。]{1,5}?)(?:る|う|く|す|つ|む|ぶ|ぐ|ぬ)前',q)
        if not bm or not st['events'] or _b_stem(st['events'][0]['verb'])!=_b_stem(bm[1]):return None
        return _fmt(st['stock'])
    if role!='event':return None
    nm=re.search(r'(?:([^\d、。]{1,6}?)に)?([^\d、。に]{1,8}?)(?:た|だ)(?:の|数)(?:は|が)',q)
    if nm:
        stem=_b_stem(nm[2]);hits=[e for e in st['events'] if _b_stem(e['verb'])==stem]
        if nm[1]:hits=[e for e in hits if (nm[1]+'に') in e['pre']]
    else:
        am=re.search(r'(?:([^\d、。はが]{1,8})(?:は|が))?\s*何\s*'+CNT+r'\s*([^\d、。？?]{1,8}?)(?:まし)?たか',q)
        if not am:return None
        if am[1] and am[2].startswith(('もらい','もらっ','受け取')):
            hits=[e for e in st['events'] if (am[1]+'に') in e['pre'] and e['verb'].startswith(B_GIVE)]
        else:
            if am[1] and am[1] not in (st['owner'] or '',):return None
            hits=[e for e in st['events'] if _b_stem(e['verb'])==_b_stem(am[2])]
    if not hits:return None
    return _fmt(sum(e['n'] for e in hits))

def _b_change_role_ok(s):
    """a gains/losses total is only the answer to a plain 'how many now' question about the stock itself"""
    st=_b_story(s)
    if not st:return True                       # not this shape; the change reader decides on its own
    if _b_qrole(st['q'])!='remain':return False
    who=re.search(r'^(?:今|いま|現在)?([^\d、。何]{1,8}?)(?:は|が|には)(?!じめ)',st['q'])
    if who and who[1] not in (st['noun'] or '',st['owner'] or '') and not re.match(r'残り|のこり|全部|ぜんぶ|合わせて|あわせて',who[1]):return False
    for e in st['events']:
        named=re.search(r'([^\d、。はがをにでから]{1,8})(?:を|が)\s*$',e['pre'])
        if named and st['noun'] and named[1]!=st['noun']:return False
    return True

EN_GIVE=r'(?:gave|gives|give|handed|hands)'
def _b_en_roles(s,toks):
    if HEDGE.search(s) or re.search(r"\b(?:not|never)\b|n't\b",s,re.I):return None
    sents=[x.strip() for x in re.split(r'(?<=[.?!])\s+',s.strip()) if x.strip()]
    if len(sents)<2:return None
    q=sents[-1];role=_b_qrole(q);body=' '.join(sents[:-1])
    st=re.match(r'\s*([A-Z][a-z]+|There)\s+(?:has|had|have|are|were)\s+(\d+)\s+([a-z]+)',sents[0])
    if not st or len(_b_nums(body))!=_b_numcount(toks):return None
    if role=='initial':
        w=re.search(r'\b(?:did|does)\s+([A-Za-z]+)\s+have\b',q)
        if not w or w[1].lower()!=st[1].lower():return None
        return _fmt(Fraction(st[2]))
    if role!='event':return None
    ev=_b_en_events(sents[1:-1])
    if ev is None or 1+len(ev)!=len(_b_nums(body)):return None
    g=re.search(r'\b(?:did|does)\s+\w+\s+'+EN_GIVE+r'\b(?:\s+(?:away|\w+))?(?:\s+to\s+(\w+))?\s*\??$',q,re.I)
    if g:
        hits=[n for n,v,to in ev if re.fullmatch(EN_GIVE,v,re.I) and (not g[1] or (to or '').lower()==g[1].lower())]
        return _fmt(sum(hits)) if hits else None
    lv=re.search(r'\bhow many\s+(?:\w+\s+)?(flew away|left|came|arrived|got off|got on|went home|ran away)\b',q,re.I)
    if lv:
        hits=[n for n,v,to in ev if v.lower()==lv[1].lower()]
        return _fmt(sum(hits)) if hits else None
    v=re.search(r'\b(?:did|does)\s+\w+\s+(eat|use|spend|get|receive|buy|find|win|make|read)\b',q,re.I)
    if v:
        forms={'eat':'ate|eats','use':'used|uses','spend':'spent|spends','get':'got|gets','receive':'received|receives','buy':'bought|buys','find':'found|finds',
               'win':'won|wins','make':'made|makes','read':'read|reads'}[v[1].lower()]
        hits=[n for n,vv,to in ev if re.fullmatch(forms,vv,re.I)]
        return _fmt(sum(hits)) if hits else None
    return None

EN_EVENT_VERBS=r'gave|gives|handed|hands|ate|eats|used|uses|spent|spends|got|gets|received|receives|bought|buys|found|finds|won|wins|made|makes|read|reads|drank|drinks|broke|breaks|collected|collects|picked|picks'
EN_SUBJ_VERBS=r'flew away|left|came|arrived|got off|got on|went home|ran away'
def _b_en_events(sents):
    """(amount, verb, recipient) for every amount after the first sentence. A verb governs the amounts after it
    in its sentence until another verb (「gave 8 to Joe and 5 to Amy」); 「6 children got off」 puts the verb after."""
    out=[]
    for x in sents:
        verb=None
        for t in re.finditer(r'\b('+EN_EVENT_VERBS+r')\b|(\d+)(?:\s+more)?(?:\s+([a-z]+))?(?:\s+('+EN_SUBJ_VERBS+r')\b)?([^\d]*)',x,re.I):
            if t[1]:verb=t[1];continue
            if t[4]:out.append((Fraction(t[2]),t[4],None));continue
            if verb is None:return None
            to=re.match(r'\s*(?:\w+\s+)?to\s+(\w+)',(t[3] and ' '+t[3] or '')+t[5]) if re.fullmatch(EN_GIVE,verb,re.I) else None
            out.append((Fraction(t[2]),verb,to[1] if to else None))
    return out

def _b_en_change_role_ok(s):
    sents=[x.strip() for x in re.split(r'(?<=[.?!])\s+',s.strip()) if x.strip()]
    if len(sents)<2:return True
    q=sents[-1];st=re.match(r'\s*([A-Z][a-z]+)\s+(?:has|had|have)\b',sents[0])
    if _b_qrole(q)!='remain':return False
    w=re.search(r'\b(?:does|did|do)\s+([A-Za-z]+)\s+have\b',q)
    if w and st and w[1].lower() not in (st[1].lower(),'he','she','they'):return False
    if w and not st and w[1].lower() not in ('he','she','they'):return False
    return True

# ---- claude-patch6: Parser B for the families of mathprob.py, read from this file's own tokens.
# Same contract: a value only when every numeric token is used; otherwise None (never a guess).
def _b_vals(toks):return [t for t in toks if t['kind'] not in ('per_unit_one','label')]
def _b_after(s,t,n=4):return s[t['span'][1]:t['span'][1]+n]
def _b_counter(s,t):
    m=re.match(r'\s*(km|cm|mm|kg|mg|mL|dL|L|g|m|[^\d\s、,。と]{1,2})',_b_after(s,t,6))
    return m[1] if m else None

def _b_avg(s,toks):
    if not re.search(r'平均|\baverage\b|\bmean\b',s,re.I):return None
    v=_b_vals(toks);cnt=[t for t in v if re.match(r'\s*(?:回|人|日間|日|教科|試合|週|チーム|個|本|冊)\s*(?:の|で|間)',_b_after(s,t,5))]
    one=[t for t in v if t['value']==1 and re.match(r'\s*(?:日|人|回|試合|週)\s*(?:あたり|の)?\s*平均',_b_after(s,t,8))]
    vals=[t for t in v if t not in cnt and t not in one]
    if len(cnt)>1 or len(vals)<2 or len({_b_counter(s,t) for t in vals})!=1:return None
    if cnt and cnt[0]['value']!=len(vals):return None
    if not cnt and re.search(r'\b(?:of|the)\s+\d+\s+[a-z]+\s+(?:are|were)\b',s,re.I):return None
    return _fmt(sum(t['value'] for t in vals)/len(vals))

def _b_lcm(s,toks):
    lcm=re.search(r'最小公倍数|(?:least|lowest|smallest) common multiple',s,re.I);g=re.search(r'最大公約数|(?:greatest|highest|largest) common (?:divisor|factor)',s,re.I)
    if bool(lcm)==bool(g):return None
    v=_b_vals(toks)
    if not 2<=len(v)<=4 or any(t['value'].denominator!=1 or t['value']<=0 for t in v):return None
    ns=[int(t['value']) for t in v];acc=ns[0]
    for x in ns[1:]:
        a,b=acc,x
        while b:a,b=b,a%b
        acc=acc*x//a if lcm else a
    return _fmt(acc)

def _b_next(s,toks):
    if not re.search(r'次の数|つぎの数|次に来る|\bcomes? next\b|\bnext number\b',s,re.I):return None
    v=[t['value'] for t in _b_vals(toks)]
    if len(v)<4:return None
    steps=[b-a for a,b in zip(v,v[1:])]
    if len(set(steps))==1:return _fmt(v[-1]+steps[0])
    if 0 in v[:-1]:return None
    rs=[b/a for a,b in zip(v,v[1:])]
    if len(set(rs))==1 and rs[0].denominator==1:return _fmt(v[-1]*rs[0])
    return None

def _b_shape(s,toks):
    area=bool(re.search(r'面積|\barea\b',s,re.I));per=bool(re.search(r'まわり|周り|周の長さ|\bperimeter\b',s,re.I))
    if area==per:return None
    v=[t for t in _b_vals(toks) if t['dim']=='len'];allv=_b_vals(toks)
    one_side=[t for t in allv if t['value']==1 and re.match(r'\s*辺',_b_after(s,t,2))]
    if len(v)+len(one_side)!=len(allv) or len({t['unit'] for t in v})!=1:return None
    def near(word):
        hits=[t for t in v if re.search(word+r'[^\d]{0,4}$',s[max(0,t['span'][0]-8):t['span'][0]],re.I) or re.match(r'\s*(?:cm|m|km|mm)\s+'+word,s[t['span'][1]:t['span'][1]+12],re.I)]
        return hits[0] if len(hits)==1 else None
    if re.search(r'正方形|\bsquare\b',s,re.I) and len(v)==1:
        x=v[0]['value'];return _fmt(x*x if area else 4*x)
    if re.search(r'長方形|\brectangle\b',s,re.I) and len(v)==2:
        a,b=near(r'(?:たて|縦)'),near(r'(?:よこ|横)')
        if not (a and b):a,b=near(r'long|length'),near(r'wide|width')
        if not (a and b) or a is b:return None
        return _fmt(a['value']*b['value'] if area else 2*(a['value']+b['value']))
    if re.search(r'三角形',s) and area and len(v)==2:
        a,b=near('底辺'),near('高さ')
        if not (a and b) or a is b:return None
        return _fmt(a['value']*b['value']/2)
    return None

def _b_partof(s,toks):
    v=_b_vals(toks)
    m=re.search(r'(\d+(?:\.\d+)?)\s*[^\d、。]{0,2}\s*の\s*(\d+)\s*分の\s*(\d+)',s)
    if m and len(v)==3:
        if Fraction(m[2])==0:return None
        r=Fraction(m[1])*Fraction(m[3])/Fraction(m[2])
        return _fmt(r) if r.denominator==1 or not re.search(r'\d\s*(?:人|個|本|枚|冊|匹|円)',s) else None
    p=[t for t in v if t['kind']=='percent']
    if len(p)==1 and len(v)==2 and re.search(r'そのうち|うち',s) and not re.search(r'引き|引|増し|値上|割引|off|discount',s,re.I):
        base=[t for t in v if t is not p[0]][0];r=base['value']*p[0]['value']/100
        return _fmt(r) if r.denominator==1 else None
    return None

def _b_divide(s,toks):
    v=_b_vals(toks)
    if len(v)!=2 or not re.search(r'ずつ',s):return None
    per=[t for t in v if re.match(r'\s*[^\d\s、。]{1,2}\s*ずつ',_b_after(s,t,6))]
    if len(per)!=1:return None
    k=per[0]['value'];n=[t for t in v if t is not per[0]][0]['value']
    if k<=0 or n.denominator!=1 or k.denominator!=1 or n<=k and not re.search(r'あまり|余り',s):return None
    q=_b_question(_b_sentences(s)) or ''
    if re.search(r'あまり|余り',q) and not re.search(r'何\s*(?:人|台|つ|組|回)\s*(?:に|分|で|できて|配れて)',q):return _fmt(int(n)%int(k))
    if re.search(r'何\s*(?:台|脚|艘|そう)\s*(?:いり|要り|必要)|全員[^。]*何\s*(?:台|つ|脚|列|組|回)',q):return _fmt(-(-int(n)//int(k)))
    if re.search(r'でき|作れ|つくれ|配れ|分けられ',q) and re.search(r'いくつ|何',q):return _fmt(int(n)//int(k))
    return None

def _b_regroup(s,toks):
    """N receivers, k each, r left over (or short) -> how many at first"""
    v=_b_vals(toks)
    if len(v)!=3 or not re.search(r'はじめ|初め|最初|もともと',s):return None
    each=[t for t in v if re.match(r'\s*[^\d\s、。]{1,2}\s*ずつ',_b_after(s,t,6))]
    rest=[t for t in v if re.match(r'\s*[^\d\s、。]{1,2}\s*(?:あまり|余り|足りな|足りま|たりな|たりま)',_b_after(s,t,8))]
    if len(each)!=1 or len(rest)!=1 or each[0] is rest[0]:return None
    n=[t for t in v if t is not each[0] and t is not rest[0]][0]
    if n['span'][0]>each[0]['span'][0]:return None
    sign=-1 if re.match(r'\s*[^\d\s、。]{1,2}\s*(?:足り|たり)',_b_after(s,rest[0],8)) else 1
    return _fmt(n['value']*each[0]['value']+sign*rest[0]['value'])

def _b_other_part(s,toks):
    """everyone minus those described: 「36人…めがねをかけている人は9人…かけていない人は何人」"""
    v=_b_vals(toks);q=_b_question(_b_sentences(s)) or ''
    if len(v)!=2 or not re.search(r'(?:ていない|でない|ない)\s*(?:人|もの)?\s*(?:は|が)\s*何',q):return None
    a,b=v
    if not re.search(r'(?:ている|でいる|の)\s*(?:人|もの)?\s*(?:は|が)\s*$',s[max(0,b['span'][0]-12):b['span'][0]]):return None
    return _fmt(a['value']-b['value']) if a['value']>=b['value'] else None

def _b_age(s,toks):
    v=_b_vals(toks)
    if len(v)!=2 or not re.search(r'歳',s):return None
    r=re.search(r'(\d+)\s*(?:歳|才)\s*(年下|年上|若い|上)',s)
    if not r:return None
    base=[t for t in v if t['span'][0]!=r.start(1)]
    if len(base)!=1:return None
    d=Fraction(r[1]);x=base[0]['value']
    who=re.search(r'([^\s、。]{1,8})\s*(?:は|が)\s*([^\s、。]{1,8})\s*より\s*\d',s)
    q=_b_question(_b_sentences(s)) or ''
    if not who or not re.search(re.escape(who[1])+r'\s*(?:は|が)',q):return None
    if not re.search(re.escape(who[2])+r'\s*(?:は|が)\s*\d+',s):return None
    return _fmt(x-d if r[2] in ('年下','若い') else x+d)

def _b_speed(s,toks):
    v=_b_vals(toks)
    if len(v)!=2:return None
    m=re.search(r'(時速|分速|秒速)\s*(\d+(?:\.\d+)?)\s*(km|m)',s)
    q=_b_question(_b_sentences(s)) or s
    if m:
        per={'時速':'時間','分速':'分','秒速':'秒'}[m[1]]
        a=re.search(r'何\s*(時間|分|秒)',q)
        d=[t for t in v if t['span'][0]!=m.start(2) and t['dim']=='len']
        if not a or len(d)!=1:return None
        tv=d[0]['value']*LEN[d[0]['unit']]/LEN[m[3]]/Fraction(m[2])*TIME[per]/TIME[a[1]]
        return _fmt(tv)
    m=re.search(r'時速\s*何\s*(km|m)|分速\s*何\s*(km|m)',q)
    if m:
        d=[t for t in v if t['dim']=='len'];tm=[t for t in v if t['dim']=='time']
        if len(d)!=1 or len(tm)!=1:return None
        unit=m[1] or m[2];per='時間' if m[1] else '分'
        return _fmt(d[0]['value']*LEN[d[0]['unit']]/LEN[unit]/(tm[0]['value']*TIME[tm[0]['unit']]/TIME[per]))
    m=re.search(r'travels?\s+(\d+(?:\.\d+)?)\s*(km|miles|kilometers|meters)\s+in\s+(\d+(?:\.\d+)?)\s*(hours?|minutes?)[^?]*\bspeed\b',s,re.I)
    if m:return _fmt(Fraction(m[1])/Fraction(m[3])) if Fraction(m[3]) else None
    return None

def _b_daily(s,toks):
    v=_b_vals(toks)
    if len(v)!=2 or not re.search(r'ずつ',s):return None
    rate=[t for t in v if re.match(r'\s*[^\d\s、。]{1,3}\s*ずつ',_b_after(s,t,7))]
    if len(rate)!=1 or not re.search(r'毎日|1\s*日\s*(?:に|あたり)',s[:rate[0]['span'][0]]):return None
    d=[t for t in v if t is not rate[0]][0]
    unit=re.match(r'\s*(日間?|週間?)',_b_after(s,d,4))
    if not unit:return None
    days=d['value']*(7 if unit[1].startswith('週') else 1)
    return _fmt(rate[0]['value']*days)

def _b_coins_and_items(s,toks):
    """paid with bills / coins (or a stated sum), bought priced items: sum or change"""
    v=_b_vals(toks);q=_b_question(_b_sentences(s)) or ''
    if not re.search(r'円',s) or not re.search(r'おつり|お釣り|合計|全部で|いくら|代金',q):return None
    used=set();total=Fraction(0)
    for m in re.finditer(r'1\s*(?:個|本|冊|枚|つ)\s*(\d+)\s*円の\s*[^、。\d]{1,10}?を\s*(\d+)\s*(?:個|本|冊|枚|つ)',s):
        total+=Fraction(m[1])*Fraction(m[2]);used|={m.start(1),m.start(2)}
    for m in re.finditer(r'(?<![\d.])(\d+)\s*円の\s*[^、。\d]{1,10}?(?=と|を|、)',s):
        if m.start(1) in used:continue
        if re.match(r'を\s*\d',s[m.end():m.end()+3]):return None
        total+=Fraction(m[1]);used.add(m.start(1))
    if not used:return None
    if re.search(r'おつり|お釣り',q):
        pay=re.search(r'(\d+)\s*円\s*(?:札|玉)?\s*(?:を)?\s*(?:(\d+)\s*枚)?\s*(?:で|出|払)',s)
        if not pay or pay.start(1) in used:return None
        used.add(pay.start(1))
        if pay[2]:used.add(pay.start(2))
        paid=Fraction(pay[1])*Fraction(pay[2] or 1);r=paid-total
    else:r=total
    starts={t['span'][0] for t in v}
    ones={t['span'][0] for t in toks if t['kind']=='per_unit_one'}
    if starts-ones!=used-ones or r<0:return None
    return _fmt(r)

def _b_groups_en(s,toks):
    v=_b_vals(toks)
    if len(v)!=2:return None
    if re.search(r'\bwith\s+\d+\s+\w+\s+(?:in|on)\s+each\b|\bholds?\s+\d+\b[^?]*\bin\s+\d+\b|\bcosts?\s+\d+(?:\.\d+)?\s+\w+\s+each\b',s,re.I):
        return _fmt(v[0]['value']*v[1]['value'])
    return None

PB6=(_b_avg,_b_lcm,_b_next,_b_shape,_b_partof,_b_divide,_b_regroup,_b_other_part,_b_age,_b_speed,_b_daily,_b_coins_and_items,_b_groups_en)

def parser_b(q):
    s=normalize(q);toks=tokens(q)
    try:
        cal=_b_calendar(s)
        if cal:return cal
        ja=bool(re.search(r'[぀-ヿ一-鿿]',s))
        for f in (_b_roles,_b_en_roles)+PB6:
            v=f(s,toks)
            if v is not None:return ('value',v)
        for f in (_b_rate,_b_price,_b_conversion,_b_unit_price,_b_groups,_b_compare,_b_equation,_b_change,_b_en_change):
            if f is _b_change and not _b_change_role_ok(s):continue
            if f is _b_en_change and (ja or not _b_en_change_role_ok(s)):continue
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
QUANT_KINDS={'arithmetic','deliberation','meta_derivation','hypothesis','inventory','qtime','situation','mathprob'}
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
