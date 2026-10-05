"""claude-patch2: bounded arithmetic word problems (Japanese + simple English).

Schemas: change (gain/loss sequence), combine, equal groups (each x groups), unit price,
rate x time (and its inverses), equal sharing / grouping, comparison (older/younger, more/less),
metric unit conversion. Every schema produces an arithmetic expression that proofs.check
re-evaluates exactly.

Safety rules (any violation -> None, i.e. "not handled" -> the caller abstains):
  * COVERAGE: every number in the text must be consumed by the schema (distractor numbers -> abstain)
  * hedged / hypothetical / negated events are refused (予定, つもり, かもしれ, なかった ...)
  * verbs whose effect on "what I have now" is context dependent (sell, return, lend, borrow, lose,
    ship, donate ...) are NOT in the lexicon: those stay in v1022's teacher-learned domain
  * results must be exact (sharing must divide evenly) and non-negative
"""
from __future__ import annotations
import re,unicodedata
from fractions import Fraction

UNIT_ALIASES=[('キロメートル','km'),('センチメートル','cm'),('ミリメートル','mm'),('メートル','m'),('センチ','cm'),('キログラム','kg'),('ミリグラム','mg'),('グラム','g'),
              ('ミリリットル','mL'),('デシリットル','dL'),('リットル','L'),('才','歳')]
DIM={'km':('len',1000),'m':('len',1),'cm':('len',Fraction(1,100)),'mm':('len',Fraction(1,1000)),'kg':('mass',1000),'g':('mass',1),'mg':('mass',Fraction(1,1000)),
     'L':('vol',1000),'dL':('vol',100),'mL':('vol',1),'時間':('time',60),'分':('time',1),'秒':('time',Fraction(1,60))}
CNT='ページ|パック|ケース|時間|個|枚|本|冊|台|人|円|匹|頭|羽|杯|回|点|粒|袋|箱|束|歳|足|着|軒|つ|km|cm|mm|kg|mg|mL|dL|L|g|m|分|秒'
NUM=r'(\d+(?:\.\d+)?)'
QTY=re.compile(NUM+r'\s*('+CNT+r')(?![a-zA-Z])')
JA=re.compile(r'[぀-ヿ一-鿿]')
HEDGE=re.compile(r'予定|つもり|かもしれ|らしい|と言|と聞|明日|来週|夢|想像|もし|なら|ぐらい|くらい|ほど|約|およそ|だいたい|ほぼ|以上|以下|未満|少なくとも|最大|最低|高々|せいぜい|ずつ減|〜|~|～|か(?=\d)|または|もしくは|不明|かどうか')
NEG=re.compile(r'(?:ません|なかった|ないで|なくて|ず(?:に)?)')
NONOCCURRENCE=re.compile(r'ません|なかった|(?<!少)ない|なくて|ずに')
# effects on "what we have now". Context-dependent verbs (売る 販売 出荷 入荷 仕入れ 補充 返品 寄付 譲る なくす 紛失 盗む 借りる 貸す 落とす) are deliberately absent.
PLUS_JA=r'入れ|加わ|増やし|もら|拾|買い足|増え|作っ|作り|作った|咲い|咲き|生まれ|乗っ|乗り|乗って|来た|来ました|やって来|やってき|入って|入り|入った|加え|足し|集め|釣っ|釣れ|届い|焼い|実っ'
MINUS_JA=r'飛び立|取り出|切り取|去っ|去り|抜い|抜き|減らし|あげ|食べ|使っ|使い|使う|使った|捨て|配っ|配り|配る|渡し|渡す|割れ|割っ|減っ|減り|降り|帰っ|帰り|出て行|出ていっ|出ていき|出た|飛んで行|飛んでいっ|飛び去|払っ|払い|飲ん|飲み|枯れ|切っ'
INIT_JA=r'(?:が|を|は)?(?:あります|ある|あって|あり|ありました|あった|持っています|持っていて|持っている|持ってい|いました|いて|います|いる|乗っていて|乗っています|乗っていました|入っていて|入っています|入っている|残っていて|咲いていて|咲いています|貯めていて|貯金していて)'
ASK_JA=re.compile(r'何('+CNT+r')|いくら|いくつ|何歳|どれだけ|どのくらい|どれくらい|何キロ')

def _kanji(s):
    kd={'〇':0,'零':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9};ku={'十':10,'百':100,'千':1000}
    def conv(m):
        t=m.group(1);total=sec=part=0
        for c in t:
            if c in kd:part=part*10+kd[c] if part else kd[c]
            elif c in ku:sec+=(part or 1)*ku[c];part=0
            elif c=='万':total+=(sec+part or 1)*10000;sec=part=0
        return str(total+sec+part)
    return re.sub(r'([〇零一二三四五六七八九十百千万]+)(?=\s*(?:'+CNT+r'|キロ|メートル|グラム|リットル|センチ|ミリ|才))',conv,s)

def _norm(s):
    s=unicodedata.normalize('NFKC',str(s)).strip()
    s=_kanji(s)
    for a,b in UNIT_ALIASES:s=s.replace(a,b)
    return s

def _fmt(v):
    v=Fraction(v);return str(v.numerator) if v.denominator==1 else str(v)
def _covered(t,used_spans):
    for m in re.finditer(r'\d+(?:\.\d+)?',t):
        if not any(a<=m.start() and m.end()<=b for a,b in used_spans):return False
    return True
def _conv(v,u,target):
    if u==target:return v
    if u in DIM and target in DIM and DIM[u][0]==DIM[target][0]:return v*Fraction(DIM[u][1])/Fraction(DIM[target][1])
    raise ValueError('UNIT')
def _ok(expr,value,schema,unit,trace):
    if value<0:return None
    return {'expression':expr,'value':value,'schema':schema,'unit':unit,'trace':trace}

# ---------------------------------------------------------------- Japanese schemas
def _ja_rate(t,q):
    m=re.search(r'(時速|分速|秒速)'+NUM+r'(km|m)',t)
    if m:
        per={'時速':'時間','分速':'分','秒速':'秒'}[m[1]];rate=Fraction(m[2]);ru=m[3];rest=t[:m.start()]+'#'*(m.end()-m.start())+t[m.end():]
        # claude-patch4: 「2時間30分」「12分30秒」 are ONE duration (v1022.5 read only 2時間 and answered 12 for 15)
        comp=re.search(NUM+r'時間'+NUM+r'分|'+NUM+r'分'+NUM+r'秒',rest)
        if comp:
            mins=Fraction(comp[1])*60+Fraction(comp[2]) if comp[1] else Fraction(comp[3])+Fraction(comp[4])/60
            rest2=rest[:comp.start()]+'#'*(comp.end()-comp.start())+rest[comp.end():]
            a=re.search(r'何(km|m)|どれだけ進|どのくらい進|どれくらい進',q)
            if QTY.search(rest2) or not a:return None
            target=a[1] or ru;tv=_conv(mins,'分',per);v=_conv(rate*tv,ru,target)
            return _ok(f'{m[2]}*{_fmt(tv)}'+('' if target==ru else f'*{_fmt(Fraction(DIM[ru][1])/DIM[target][1])}'),v,'rate_x_time',target,[m.span(),comp.span()])
        qs=[x for x in QTY.finditer(rest)]
        times=[x for x in qs if x[2] in ('時間','分','秒')];dists=[x for x in qs if x[2] in ('km','m','cm')]
        if len(qs)!=1:return None
        a=re.search(r'何(km|m|時間|分|秒)|どれだけ進|どのくらい進|どれくらい進',q)
        if not a:return None
        if times and not dists:
            if a[1] not in ('km','m') and a[1] is not None:return None
            target=a[1] if a[1] in ('km','m') else ru
            tv=_conv(Fraction(times[0][1]),times[0][2],per);v=_conv(rate*tv,ru,target)
            return _ok(f'{m[2]}*{_fmt(tv)}'+('' if target==ru else f'*{_fmt(Fraction(DIM[ru][1])/DIM[target][1])}'),v,'rate_x_time',target,[(m.span()),times[0].span()])
        if dists and a[1] in ('時間','分','秒'):
            dv=_conv(Fraction(dists[0][1]),dists[0][2],ru);tv=dv/rate;v=_conv(tv,per,a[1])
            return _ok(f'({_fmt(dv)}/{m[2]})'+('' if a[1]==per else f'*{_fmt(Fraction(DIM[per][1])/DIM[a[1]][1])}'),v,'distance_div_rate',a[1],[m.span(),dists[0].span()])
        return None
    m=re.search(r'(時速|分速|秒速)何(km|m)',q)
    if m:
        per={'時速':'時間','分速':'分','秒速':'秒'}[m[1]];qs=list(QTY.finditer(t))
        times=[x for x in qs if x[2] in ('時間','分','秒')];dists=[x for x in qs if x[2] in ('km','m')]
        if len(times)!=1 or len(dists)!=1 or len(qs)!=2:return None
        tv=_conv(Fraction(times[0][1]),times[0][2],per);dv=_conv(Fraction(dists[0][1]),dists[0][2],m[2])
        return _ok(f'{_fmt(dv)}/{_fmt(tv)}',dv/tv,'distance_div_time',m[2],[times[0].span(),dists[0].span()])
    return None

def _ja_price(t,q):
    if not re.search(r'いくら|何円|代金|おつり|お釣り',q):return None
    total=[];spans=[];expr=[]
    for m in re.finditer(r'1\s*('+CNT+r')'+NUM+r'円',t):                      # 1本150円 ... 2本
        c=m[1];rest=[x for x in QTY.finditer(t) if x[2]==c and x.start()>m.end()]
        if len(rest)!=1:return None
        total.append(Fraction(m[2])*Fraction(rest[0][1]));spans+= [m.span(),rest[0].span()];expr.append(f'{m[2]}*{rest[0][1]}')
    for m in re.finditer(NUM+r'円の[^、。を]{1,12}を'+NUM+r'\s*('+CNT+r')',t):     # 150円のジュースを2本
        if any(m.start()<b and a0<m.end() for a0,b in spans):continue
        if m[3]=='円':return None
        total.append(Fraction(m[1])*Fraction(m[2]));spans.append(m.span());expr.append(f'{m[1]}*{m[2]}')
    if not total:return None
    pay=re.search(NUM+r'円(?:を)?(?:出し|払っ|渡し|持って|札で|で(?=[、,]))',t)
    if re.search(r'おつり|お釣り',q):
        if not pay:return None
        v=Fraction(pay[1])-sum(total);spans.append(pay.span())
        if not _covered(t,spans):return None
        return _ok(f'{pay[1]}-('+'+'.join(expr)+')',v,'unit_price_change','円',spans)
    if pay or not _covered(t,spans):return None
    return _ok('+'.join(expr),sum(total),'unit_price','円',spans)

def _ja_groups(t,q):
    a=ASK_JA.search(q)
    m=re.search(NUM+r'\s*('+CNT+r')に'+NUM+r'\s*('+CNT+r')ずつ',t)
    if m and not re.search(r'分け|わけ|余',t):
        if a and a[1] and a[1]!=m[4]:return None
        if not re.search(r'全部で|全部|合わせて|あわせて|合計|いくつ|何'+m[4],q) or not _covered(t,[m.span()]):return None
        return _ok(f'{m[1]}*{m[3]}',Fraction(m[1])*Fraction(m[3]),'equal_groups',m[4],[m.span()])
    m=re.search(r'1\s*('+CNT+r')に'+NUM+r'\s*('+CNT+r')入り(?:の[^、。が]{1,10})?が'+NUM+r'\s*\1',t)
    if m:per,unit,cnt=m[2],m[3],m[4]
    else:
        m=re.search(r'(?:1\s*(?:箱|袋|パック|ケース|束|皿|かご|缶|瓶)に?)?'+NUM+r'\s*('+CNT+r')入りの[^、。を]{0,10}?を'+NUM+r'\s*(?:つ|'+CNT+r')',t)
        if m:per,unit,cnt=m[1],m[2],m[3]
    if m:
        if a and a[1] and a[1]!=unit:return None
        if not re.search(r'全部で|全部|合わせて|あわせて|合計|何'+unit,q) or not _covered(t,[m.span()]):return None
        return _ok(f'{per}*{cnt}',Fraction(per)*Fraction(cnt),'per_container',unit,[m.span()])
    return None

def _ja_share(t,q):
    m=re.search(NUM+r'\s*('+CNT+r')(?:の[^、。を]{1,10})?を'+NUM+r'\s*(人|つ|'+CNT+r')(?:で|に)(?:同じ数ずつ|等しく|均等に|同じように|同じだけ|同じ数に)?(?:分け|わけ|配)',t)
    if m and re.search(r'1\s*'+re.escape(m[4])+r'(?:あたり|分|に|は)*(?:何'+m[2]+r'|いくつ)',q):
        n,k=Fraction(m[1]),Fraction(m[3])
        if k==0 or (n/k).denominator!=1 or not _covered(t,[m.span(),*[x.span() for x in re.finditer(r'1\s*'+re.escape(m[4]),t) if x.start()>=m.end()]]):return None
        spans=[m.span(),*[x.span() for x in re.finditer(r'1\s*'+re.escape(m[4]),t) if x.start()>=m.end()]]
        return _ok(f'{m[1]}/{m[3]}',n/k,'equal_sharing',m[2],spans)
    m=re.search(NUM+r'\s*('+CNT+r')(?:の[^、。を]{1,10})?を'+NUM+r'\s*\2ずつ[^、。]{0,8}?(?:分け|わけ|入れ|配|まとめ)',t)
    if m:
        a=re.search(r'何('+CNT+r')',q)
        if not a or a[1]==m[2]:return None
        n,k=Fraction(m[1]),Fraction(m[3])
        if k==0 or (n/k).denominator!=1 or re.search(r'余',t) or not _covered(t,[m.span()]):return None
        return _ok(f'{m[1]}/{m[3]}',n/k,'grouping',a[1],[m.span()])
    return None

LESS='年下|少な|低|短|軽|安|小さ|遅く|若'
MORE='年上|多|高|長|重|大き'
def _ja_compare(t,q):
    rel=list(re.finditer(r'([^、。はがの]{1,8})は([^、。はがの]{1,8})より(?:も)?'+NUM+r'\s*('+CNT+r')(?:だけ)?('+LESS+'|'+MORE+')',t))
    if len(rel)!=1:return None
    r=rel[0];b,a,d,u,w=r[1],r[2],r[3],r[4],r[5]
    base=list(re.finditer(re.escape(a)+r'(?:は|が)(?:[^、。はが]{1,10}?を)?'+NUM+r'\s*('+CNT+r')(?:で|です|だ|、|。|$|持って|あり|あります|いる|います)',t))
    if len(base)!=1 or base[0][2]!=u:return None
    if not re.search(re.escape(b)+r'(?:は|の)?(?:何'+u+'|いくつ|何歳|いくら)',q):return None
    sign=-1 if re.fullmatch(LESS,w) else 1
    spans=[r.span(),base[0].span()]
    if not _covered(t,spans):return None
    return _ok(f'{base[0][1]}{"-" if sign<0 else "+"}{d}',Fraction(base[0][1])+sign*Fraction(d),'comparison',u,spans)

class _Q:
    def __init__(s,v,u,a,b,txt):s.v,s.u,s.a,s.b,s.txt=v,u,a,b,txt
    def __getitem__(s,i):return {0:s.txt,1:s.v,2:s.u}[i]
    def start(s):return s.a
    def end(s):return s.b
    def span(s):return (s.a,s.b)
    def group(s):return s.txt
def _merge_compound(ms):
    """claude-patch4: adjacent amounts of one dimension, larger unit first (1L200mL, 3m40cm, 2時間15分) are one quantity"""
    out=[]
    for m in ms:
        q=_Q(m[1],m[2],m.start(),m.end(),m.group())
        if out and out[-1].b==q.a and q.u in DIM and out[-1].u in DIM and DIM[q.u][0]==DIM[out[-1].u][0] and Fraction(DIM[out[-1].u][1])>Fraction(DIM[q.u][1]):
            p=out.pop();v=Fraction(p.v)*Fraction(DIM[p.u][1])/Fraction(DIM[q.u][1])+Fraction(q.v)
            q=_Q(str(v),q.u,p.a,q.b,p.txt+q.txt)
        out.append(q)
    return out
def _ja_change(t,q,qpos):
    a=ASK_JA.search(q)
    qs=_merge_compound(list(QTY.finditer(t)))
    if not qs:return None
    asked=a[1] if a and a[1] else ('円' if (a and a.group()=='いくら') or re.search(r'おつり|お釣り|残金',q) else None)
    if asked is None and len({x[2] for x in qs})==1:asked=qs[0][2]
    want=re.search(r'残り|残って|残る|残った|今|現在|全部で|合わせて|あわせて|合計|みんなで|全員で|になり|になった|になる|おつり|お釣り',q)
    if not want or not asked:return None
    if any(x[2]!=asked and not (x[2] in DIM and asked in DIM and DIM[x[2]][0]==DIM[asked][0]) for x in qs):return None
    events=[];spans=[]
    for i,x in enumerate(qs):
        end=qs[i+1].start() if i+1<len(qs) else len(t)
        ph=t[x.end():end];ph_clause=re.split(r'[。]',ph)[0]
        in_question=x.start()>=qpos
        if NEG.search(ph_clause):return None
        if HEDGE.search(ph_clause) and not in_question:return None
        if re.match(INIT_JA,ph_clause) or re.match(r'^(?:[、と]|$)',ph_clause) or (i==0 and re.match(r'^の[^、。]{1,10}から',ph_clause)):
            kind=0
        else:
            body=re.sub(r'^(?:の[^、。を]{1,10}?を|を|が|は|分を?)?\s*(?:さらに|また|あとから|後から)?\s*','',ph_clause)
            if re.match(MINUS_JA,body) or (x[2]=='円' and re.match(r'買っ|買い|買う|買った|支払',body)):kind=-1
            elif re.match(PLUS_JA,body) or re.match(r'買っ|買い|買う|買った',body):kind=1
            else:return None
        events.append((x,kind));spans.append(x.span())
    if not _covered(t,spans):return None
    v=Fraction(0);expr=[];trace=[]
    first=True
    for x,k in events:
        val=_conv(Fraction(x[1]),x[2],asked)
        if k==0:
            if not first and not re.search(r'全部で|合わせて|あわせて|合計|みんなで|全員で',q):return None
            v+=val;expr.append(('+' if expr else '')+_fmt(val))
        else:
            if first and k<0:return None
            v+=k*val;expr.append(('-' if k<0 else '+')+_fmt(val))
        trace.append({'quantity':str(x.group()),'effect':k});first=False
    if all(k==0 for _,k in events) and len(events)<2:return None
    return _ok(''.join(expr),v,'change_sequence' if any(k for _,k in events) else 'combine',asked,trace)

OP_DOWN=r'割引き?|値引き?|引き|引|オフ|安く'
OP_UP=r'値上げ|増し|増|アップ|高く'
def _ja_sequential_percent(t):
    """claude-patch4: a base price followed by one or more operations on THE SAME item
    (「20%引きし、さらに25%引きし、その後10%値上げ」「2割引きにし、そこから500円引き」).
    Every operation must be joined by a plain connector; anything else between them (another object
    「商品Bを」, an extra clause) refuses instead of dropping the operation."""
    ops=list(re.finditer(NUM+r'\s*(%|パーセント|割|円)\s*(?:を|に|だけ|分)?\s*('+OP_DOWN+'|'+OP_UP+r')',t))
    if not ops:return None
    refuse={'refused':'AMBIGUOUS_OR_UNCOVERED_PRICE_OPERATION'}
    if len(ops)>6:return refuse
    base=re.match(r'(?:定価|もとの値段が?|値段が)?'+NUM+r'円(?:の[^、。をはが\d]{1,8})?(?:を|は|が|から)?',t)
    if not base or base.end()>ops[0].start():return None
    if t[base.end():ops[0].start()]:return refuse
    JOIN=r'(?:しました|ました|して|し|にしました|にして|にし|されて|された|され|て|に)?[、,。]?\s*(?:さらに|次に|その後|それから|そこから|そのあと|また)?[、,]?'
    value=Fraction(base[1]);expr=base[1];trace=[base.span()]
    for k,m in enumerate(ops):
        if k>0 and not re.fullmatch(JOIN,t[ops[k-1].end():m.start()]):return refuse
        n=Fraction(m[1]);down=bool(re.fullmatch(OP_DOWN,m[3]))
        if m[2] in ('%','パーセント'):f=n
        elif m[2]=='割':f=n*10
        else:f=None
        if f is not None:
            if down and not 0<=f<=100:return refuse
            expr=f'({expr})*(100{"-" if down else "+"}{_fmt(f)})/100';value=value*(100-f if down else 100+f)/100
        else:
            expr=f'({expr}){"-" if down else "+"}{m[1]}';value=value-n if down else value+n
        trace.append(m.span())
    tail=t[ops[-1].end():]
    if re.search(r'\d',tail) or not re.fullmatch(r'(?:しました|ました|ます|します|して|し|にしました|にし|されました|された|すると|したら|にすると|にしたら|になりました|になった|に)?[、,。]?\s*(?:最終的な|最終の|最終)?(?:価格|値段|代金|金額)?(?:は|が)?\s*(?:いくら|何円)?(?:ですか|になる|になりますか|になった|になりましたか|でしょう|か)?[?？。]*',tail):
        return refuse if len(ops)>1 else None
    if value<0:return refuse
    return _ok(expr,value,'sequential_price_operations','円',trace) if _covered(t,trace) else refuse

def _ja(t):
    t=re.sub(r'\s+','',t)
    if NONOCCURRENCE.search(t) and QTY.search(t):
        return {'refused':'WORD_PROBLEM_EVENT_NOT_CONFIRMED'}
    qpos=max(t.rfind('。',0,len(t)-1)+1,0);q=t[qpos:]
    if not re.search(r'[?？]|何|いくつ|いくら|どれだけ|どのくらい',q):return None
    if HEDGE.search(t[:qpos]) or HEDGE.search(re.sub(r'たら|と(?=[何いど])','',q)):
        return {'refused':'HEDGED_OR_HYPOTHETICAL_QUANTITIES'} if QTY.search(t) else None
    percentages=_ja_sequential_percent(t)
    if percentages:return percentages
    from . import wordprob2 as _w2                      # claude-patch3
    eq=_w2.equation(t,q)
    if eq:return eq if _covered(t,eq['trace']) else {'refused':'WORD_PROBLEM_NUMBER_COVERAGE'}
    if re.search(r'%|パーセント|値引|引き|分の|割|倍|平均|余り|あまり|何通り|確率|順番|面積|体積|平方|立方',t):return None
    extra=[lambda t,q,f=f:f(t,q,CNT) for f in (_w2.each_item_price,_w2.per_period,_w2.distribute,_w2.part_whole,_w2.difference)]
    for f in (_ja_rate,_ja_price,_ja_groups,_ja_share,_ja_compare,*extra):
        try:
            r=f(t,q)
        except (ValueError,ZeroDivisionError):return None
        if r:
            return r if _covered(t,r['trace']) else {'refused':'WORD_PROBLEM_NUMBER_COVERAGE'}
    try:return _ja_change(t,q,qpos)
    except (ValueError,ZeroDivisionError):return None

# ---------------------------------------------------------------- English schemas
PLUS_EN=r'got|gets|received|receives|bought|buys|found|finds|picked|picks|collected|collects|earned|earns|made|makes|won|wins|caught|baked|grew'
MINUS_EN=r'gave|gives|ate|eats|used|uses|spent|spends|threw away|broke|drank|paid'
def _en(t):
    s=t.lower().replace(',','');s=re.sub(r'\$\s*(\d)',r'\1 dollars ',s)
    if re.search(r"\b(?:not|never)\b|n't\b",s) and re.search(r'\d',s):
        return {'refused':'WORD_PROBLEM_EVENT_NOT_CONFIRMED'}
    # claude-patch3: schemas whose wording the hedge filter below would otherwise refuse
    if not re.search(r'\bpercent|%|average|probability|area|remainder\b|\bleft over\b|\bmaybe\b|\bmight\b|\babout\b|\bapproximately\b|\bwill\b|\bplans?\b|\bsome\b|\bseveral\b|\ba few\b|\bmany of\b|\ba lot\b|\bmost\b|\bpart of\b',s):
        from . import wordprob2 as _w2
        s2=re.sub(r'^if you (share|divide|split)',r'you \1',s)
        for f in ((_w2.en_times,) if re.search(r'\bas many\b',s2) else ())+(_w2.en_share,_w2.en_prices):
            r=f(s2)
            if r:return r
    if re.search(r'\bpercent|%|average|half|twice|times as|probability|area|remainder\b|\bleft over\b|\bmaybe\b|\bmight\b|\babout\b|\bapproximately\b|\bwill\b|\bplans?\b|\bif\b|\bsome\b|\bseveral\b|\ba few\b|\bmany of\b|\ba lot\b|\bmost\b|\bpart of\b',s):
        return {'refused':'HEDGED_OR_INEXACT_QUANTITIES'} if re.search(r'\d',s) and re.search(r'how (?:many|much|far|old|long)',s) else None
    sents=[x.strip() for x in re.split(r'(?<=[.?!])\s+',s) if x.strip()]
    q=sents[-1];body=' '.join(sents[:-1]) if len(sents)>1 else ''
    if not q.endswith('?') and not re.match(r'how|what',q):return None
    nums=list(re.finditer(r'\d+(?:\.\d+)?',s))
    full=body+' '+q
    # equal groups: "3 rows with 7 books each", "4 bags of 6 apples"
    m=re.search(NUM+r' (\w+) (?:with|of|that each have|each with) '+NUM+r' (\w+)(?: each| in each| on each)?',full)
    if m and re.match(r'how many',q) and len(nums)==2 and not re.search(r'\b(?:'+MINUS_EN+'|'+PLUS_EN+r')\b',full):
        return _ok(f'{m[1]}*{m[3]}',Fraction(m[1])*Fraction(m[3]),'equal_groups',m[4],[m.span()])
    # rate: "5 km per hour for 4 hours" / "5 km an hour"
    m=re.search(NUM+r' (km|miles?|meters?) (?:per|an|a|each) (hour|minute)',full);n2=re.search(NUM+r' (hours?|minutes?)',full)
    c2=re.search(NUM+r' hours? and '+NUM+r' minutes?',full)
    if m and c2 and m[3]=='hour' and len(nums)==3 and re.match(r'how (?:far|many (?:km|miles|meters))',q):
        tv=Fraction(c2[1])+Fraction(c2[2])/60
        return _ok(f'{m[1]}*{_fmt(tv)}',Fraction(m[1])*tv,'rate_x_time',m[2],[m.span(),c2.span()])
    if m and n2 and n2[2].startswith(m[3]) and len(nums)==2 and re.match(r'how (?:far|many (?:km|miles|meters))',q):
        return _ok(f'{m[1]}*{n2[1]}',Fraction(m[1])*Fraction(n2[1]),'rate_x_time',m[2],[m.span(),n2.span()])
    # comparison: "Tom is 12 years old. Amy is 4 years younger than Tom. How old is Amy?"
    rel=re.search(r'(\w+) is '+NUM+r' (years?|cm|kg|dollars?) (younger|older|shorter|taller|less|more|lighter|heavier|cheaper) than (\w+)',full)
    if rel:
        ref=rel[5]
        if ref in ('her','him','them'):                 # claude-patch3: pronoun -> the only named person, else refuse
            names=sorted({w.lower() for w in re.findall(r'\b[A-Z][a-z]+\b',t)}-{'how','what','if','the','a','an','there','then','his','her','he','she','they'})
            if len(names)!=1:return None
            ref=names[0]
        # word boundary: "brot-her is 4 years" must not be read as "her is 4 years" (patch2 bug)
        base=re.search(r'\b'+re.escape(ref)+r' is '+NUM+r' (years?|cm|kg|dollars?)',full)
        if base and len(nums)==2 and re.search(r'\b'+re.escape(rel[1])+r'\b',q):
            sign=-1 if rel[4] in ('younger','shorter','less','lighter','cheaper') else 1
            return _ok(f'{base[1]}{"-" if sign<0 else "+"}{rel[2]}',Fraction(base[1])+sign*Fraction(rel[2]),'comparison',rel[3],[rel.span(),base.span()])
        return None
    # sharing: "12 cookies shared equally among 4 children. How many does each child get?"
    m=re.search(NUM+r' (\w+) (?:are |were )?(?:shared|divided|split) (?:equally )?(?:among|between|by) '+NUM+r' (\w+)',full)
    if m and re.search(r'\beach\b',q) and len(nums)==2:
        n,k=Fraction(m[1]),Fraction(m[3])
        if k and (n/k).denominator==1:return _ok(f'{m[1]}/{m[3]}',n/k,'equal_sharing',m[2],[m.span()])
        return None
    # change / combine
    if not re.search(r'how (?:many|much|far)',q):return None
    combine=bool(re.search(r'in total|altogether|in all|total|combined',q));left=bool(re.search(r'\bleft\b|\bnow\b|\bremain',q))
    if not (combine or left):return None
    events=[];
    for i,x in enumerate(nums):
        pre=s[max(0,x.start()-40):x.start()];
        if re.search(r'\b(?:not|never|didn\'t|doesn\'t|don\'t)\b',pre):return None
        post=s[x.end():x.end()+30]
        if re.match(r' (?:more )?(?:\w+ )?(?:left|went home|went away|got off|flew away|ran away)\b',post):k=-1
        elif re.match(r' (?:more )?(?:\w+ )?(?:came|arrived|joined|got on|came in)\b',post):k=1
        elif re.search(r'\b(?:'+MINUS_EN+r')(?: \w+)? $',pre) or re.search(r'\b(?:'+MINUS_EN+r') $',pre):k=-1
        elif re.search(r'\b(?:'+PLUS_EN+r')(?: \w+)? $',pre) or re.search(r'\b(?:has|had|have|there are|there were|is|are|was|were|ran|walked|read|swam|drove|rode|saw|wrote|counted)(?: \w+)? $',pre) or re.search(r'\band $',pre):
            k=1 if re.search(r'\b(?:'+PLUS_EN+r')(?: \w+)? $',pre) else 0
        else:return None
        events.append((x,k))
    if not events or (events[0][1]<0):return None
    if left and all(k==0 for _,k in events):return None
    if combine and any(k<0 for _,k in events):return None
    v=Fraction(0);expr=[]
    for x,k in events:
        val=Fraction(x.group());v+=(-val if k<0 else val);expr.append(('-' if k<0 else ('+' if expr else ''))+x.group())
    return _ok(''.join(expr),v,'change_sequence' if any(k for _,k in events) else 'combine','',[e[0].span() for e in events])

def solve(query):
    t=_norm(query)
    if len(t)>400:return None
    return _ja(t) if JA.search(t) else _en(t)
