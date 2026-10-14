"""generation 4 (round 10): more everyday Japanese forms, tried after reader_ja's own (reader_ja.read). No LLM.

Each form reads one shape of sentence and writes the reading in the formal problem language with every number of the
text bound or declared unused with a reason; the checker (check.py) verifies it on its own.

  per_one      1袋にみかんが9個入っています。6袋では何個 / たまごを6パック買いました。1パックに10個 / バス1台に40人乗れます
  per_item     750mLのペットボトルが4本あります。全部で何mL
  zutsu        カードが8まいずつ入ったパックを3パック買いました。5まいあげました / りんごが9こずつ入った箱が5箱と、ばらの…
  measure_cmp  お父さんは健太さんより28cm高い (4mの木より150cm高い: cm で) / はるかさんはゆうきさんより17点低かった
  cmp_inverse  じゅんさんは18枚持っていて、りょうさんより6枚多い。りょうさんは何枚
  cmp_total    ゆかさんの本はとおるさんより9冊多い。とおるさんは16冊。2人の本は合わせて何冊
  diff_slots   土曜日に125こ、日曜日に98こ…土曜日は日曜日より何こ多く / 男子が27人、女子が31人…男子は女子より何人少ない
  age_then     あいさんは弟より4才年上です。弟は7才です。あいさんは3年後に何才
  finisher     1人目は50分でゴール。2人目はそれより8分おそく。2人目は何分
  rest         32枚焼き、そのうち19枚を売りました / 210ページの本のうち85ページ読みました / 90cmのロープから35cm切り取りました
               / 12切れに分けました。7切れ食べました。食べていないのは / 赤い花を18本、黄色い花を27本…15本あげました
  part         5000円の2/5を使いました / 32人のうち、半分が / そのうち20%が / その半分を妹にあげました / 1わり引き
  times        その3倍持っています / 羊は牛の2倍います / たけるさんの3倍で27さつ (たけるさんは)
  share        120こを10箱に同じ数ずつ / 96本を12人に同じ数ずつ分けます / 90cmのリボンを3等分
  buy_count    チケットは1まい700円です。4200円では何まい
  two_numbers  2つの数をたすと50になります。1つは18です
  clock        2時に始まり、3時間続きました。何時に終わりましたか
  convert      5kgのお米は何g
  from_to      1500円から2200円に上がりました。何円上がりましたか
  round_trip   学校まで2km歩いて行き、同じ道を歩いて帰ります。5日間で何km
  boxes        1箱にかんが6こ入ります。かん30こを入れるには何箱
  daily        毎日プールを25往復ずつ4日間 / 毎日15ページずつ…1週間では
"""
from __future__ import annotations
import re
from fractions import Fraction
from .reader_ja import _B,_C,CNT,_amts,_ask_unit

NUM=r'(\d+(?:\.\d+)?)'
U=lambda w:_C.get(w)
def _f(x):return Fraction(x)
MEAS={'cm','m','km','mm','kg','g','L','mL','dL','t'}
def _whole(u):return u.split('/')[0] not in MEAS|{'時間','分','秒','日','週','か月','年','度'}
def _n_amts(t):return len(_amts(t,0))
def _who(x):return re.sub(r'(?:さん|くん|ちゃん)$','',x.strip())


def _per_one(t,stm,q):
    s=''.join(stm);b=_B(t)
    m=re.search(rf'1\s*({CNT})(?:に|で|あたり|につき|すると)?\s*(?:[^、。\d]{{0,12}}?(?:が|は|を))?\s*{NUM}\s*({CNT})(?:の[^、。]{{1,6}}?)?(?:が)?(?:入っています|入ります|あります|乗れます|乗ります|使います|すわれます|運びます|です|もらえます|かかります)',s)
    if not m:return None
    G,c=U(m.group(1)),U(m.group(3))
    cnt=re.search(rf'{NUM}\s*({CNT})(?:では|で|分では|分で|働くと|乗ると|走ると|使うと|作ると|すると)',q)
    src=q
    if not cnt:
        cnt=re.search(rf'{NUM}\s*({CNT})(?:買いました|ありました|あります|持っています|作りました|つくりました)',s);src=s
    if not cnt or U(cnt.group(2))!=G:return None
    if not re.search(rf'何\s*({CNT})',q) or _ask_unit(q)!=c:return None
    if _n_amts(t)!=3:return None
    k=b.bind('each',f'{c}/{G}',_f(m.group(2)),m.group(0),integer=False);n=b.bind('count',G,_f(cnt.group(1)),cnt.group(0),integer=False)
    b.skip('1','1つあたりの量の1 (割合のもと)')
    b.rel('total',c,f'{k} * {n}',q,integer=_whole(c));return b.spec('total','per_one')


def _per_item(t,stm,q):
    s=''.join(stm);b=_B(t)
    m=re.search(rf'{NUM}\s*(mL|L|dL|g|kg|cm|m)の[^、。]*?が\s*{NUM}\s*({CNT})(?:あります|ありました)',s)
    if not m or not re.search(rf'全部で何\s*{m.group(2)}',q) or _n_amts(t)!=2:return None
    u=m.group(2);c=U(m.group(4))
    a=b.bind('each',f'{u}/{c}',_f(m.group(1)),m.group(0),integer=False);n=b.bind('count',c,_f(m.group(3)),m.group(0),integer=False)
    b.rel('total',u,f'{a} * {n}',q,integer=False);return b.spec('total','per_item')


def _zutsu(t,stm,q):
    s=''.join(stm);b=_B(t)
    m=re.search(rf'(?P<X>[^、。\d]{{1,8}}?)が\s*(?P<n>\d+)\s*(?P<c>{CNT})ずつ入った\s*(?P<G>[^、。\d]{{1,4}}?)(?:を|が)\s*(?P<g>\d+)\s*(?P<G2>{CNT})',s)
    if not m or not re.search(rf'何\s*({CNT})',q) or _ask_unit(q)!=U(m['c']):return None
    c=U(m['c']);G=U(m['G2'])
    rest=s[m.end():]
    plus=re.search(rf'ばらの{re.escape(m["X"])}が\s*{NUM}\s*({CNT})',rest)
    minus=re.search(rf'{NUM}\s*({CNT})(?:あげ|食べ|使い|なくし|売り)',rest)
    if plus and minus:return None
    n=b.bind('each',f'{c}/{G}',_f(m['n']),m.group(0),integer=False);g=b.bind('groups',G,_f(m['g']),m.group(0),integer=False)
    if plus and U(plus.group(2))==c and _n_amts(t)==3 and re.search(r'全部で|あわせて|合わせて',q):
        k=b.bind('loose',c,_f(plus.group(1)),plus.group(0));b.rel('total',c,f'{n} * {g} + {k}',q);return b.spec('total','zutsu')
    if minus and U(minus.group(2))==c and _n_amts(t)==3 and re.search(r'ありますか|のこり|残り|なりましたか',q):
        if _f(m['n'])*_f(m['g'])<_f(minus.group(1)):return None
        k=b.bind('given',c,_f(minus.group(1)),minus.group(0));b.rel('left',c,f'{n} * {g} - {k}',q);return b.spec('left','zutsu')
    return None


CMPW={'高い':1,'高かった':1,'重い':1,'重かった':1,'長い':1,'長かった':1,'多い':1,'多かった':1,'年上':1,'おそく':1,'遅く':1,
      '低い':-1,'低かった':-1,'軽い':-1,'軽かった':-1,'短い':-1,'短かった':-1,'少ない':-1,'少なかった':-1,'年下':-1,'はやく':-1,'早く':-1}
CMPR='(?:'+'|'.join(sorted(CMPW,key=len,reverse=True))+')'
ATTR=r'(?:の(?:身長|高さ|重さ|長さ|体重|点数|点|年れい|年齢))?'
MU=r'(cm|m|km|mm|kg|g|点|才|歳|円|分|L|mL)'
CONV={('m','cm'):100,('km','m'):1000,('kg','g'):1000,('L','mL'):1000}
def _measure_cmp(t,stm,q):
    if len(stm)!=2:return None
    b=_B(t)
    a=re.fullmatch(rf'(?P<A>[^、。]+?){ATTR}は\s*{NUM}\s*{MU}(?:です|でした)。?',stm[0])
    c=re.fullmatch(rf'(?P<B>[^、。]+?)は(?P<A2>[^、。]+?)より\s*{NUM}\s*{MU}\s*(?P<cmp>{CMPR})(?:です|でした)?。?',stm[1])
    k=re.fullmatch(rf'(?P<B2>[^、。]+?){ATTR}は何\s*{MU}(?:ですか|でしたか)[。？?]?',q)
    if not (a and c and k):return None
    if _who(c['A2'])!=_who(a['A']) or _who(k['B2'])!=_who(c['B']) or _who(c['B'])==_who(a['A']):return None
    u1,u2,u3=_C.get(a.group(3),a.group(3)),_C.get(c.group(4),c.group(4)),_C.get(k.group(2),k.group(2))
    sign=CMPW[c['cmp']]
    if u1==u2==u3:
        x=b.bind('first',u1,_f(a.group(2)),stm[0],integer=False);d=b.bind('difference',u1,_f(c.group(3)),stm[1],integer=False)
        if sign<0 and _f(c.group(3))>_f(a.group(2)):return None
        b.rel('second',u1,f"{x} {'+' if sign>0 else '-'} {d}",q,integer=False);return b.spec('second','measure_cmp')
    if (u1,u2) in CONV and u3==u2:
        x=b.bind('first',u1,_f(a.group(2)),stm[0],integer=False);d=b.bind('difference',u2,_f(c.group(3)),stm[1],integer=False)
        kk=b.known('per',f'{u2}/{u1}',CONV[(u1,u2)],f'1{u1} = {CONV[(u1,u2)]}{u2}')
        b.rel('second',u2,f"{x} * {kk} {'+' if sign>0 else '-'} {d}",q,integer=False);return b.spec('second','measure_cmp')
    return None


def _cmp_inverse(t,stm,q):
    if len(stm)!=1:return None
    b=_B(t)
    m=re.fullmatch(rf'(?P<A>[^、。]+?)は[^、。]*?{NUM}\s*({CNT})持っていて、(?P<B>[^、。]+?)より\s*{NUM}\s*({CNT})(?P<cmp>多い|少ない)です。?',stm[0])
    k=re.fullmatch(rf'(?P<B2>[^、。]+?)は何\s*({CNT})持っていますか[。？?]?',q)
    if not (m and k) or _who(k['B2'])!=_who(m['B']) or not (U(m.group(3))==U(m.group(6))==U(k.group(2))):return None
    c=U(m.group(3));sign=1 if m['cmp']=='多い' else -1
    if sign>0 and _f(m.group(5))>=_f(m.group(2)):return None
    x=b.bind('has',c,_f(m.group(2)),stm[0]);d=b.bind('difference',c,_f(m.group(5)),stm[0])
    b.rel('other',c,f"{x} {'-' if sign>0 else '+'} {d}",q);return b.spec('other','cmp_inverse')


def _cmp_total(t,stm,q):
    if len(stm)!=2:return None
    b=_B(t)
    if not re.search(r'2\s*人(?:の[^、。]{1,6}?)?(?:は)?\s*(?:合わせて|あわせて)\s*何',q):return None
    base=cmp=None
    for x in stm:
        base=re.fullmatch(rf'(?P<A>[^、。]+?)は(?:[^、。]*?を)?\s*{NUM}\s*({CNT})持っています。?',x) or base
        cmp=re.fullmatch(rf'(?P<B>[^、。]+?)(?:の[^、。]{{1,4}}?)?は(?P<A2>[^、。]+?)より\s*{NUM}\s*({CNT})(?P<cmp>多いです|多く持っています|少ないです|少なく持っています)。?',x) or cmp
    if not (base and cmp) or _who(cmp['A2'])!=_who(base['A']):return None
    c=U(base.group(3))
    if U(cmp.group(4))!=c or _ask_unit(q)!=c:return None
    sign='+' if cmp['cmp'].startswith('多') else '-'
    if sign=='-' and _f(cmp.group(3))>=_f(base.group(2)):return None
    x=b.bind('base',c,_f(base.group(2)),base.group(0));d=b.bind('difference',c,_f(cmp.group(3)),cmp.group(0))
    b.skip('2','2人: 人数 (合わせる人の数)')
    b.rel('other',c,f'{x} {sign} {d}',cmp.group(0));b.rel('total',c,f'{x} + other',q);return b.spec('total','cmp_total')


def _diff_slots(t,stm,q):
    s=''.join(stm);b=_B(t)
    m=re.search(rf'(?P<S1>[^、。\dはにがを]{{1,4}}?(?:曜日|日|月))に[^、。\d]*?{NUM}\s*({CNT})、\s*(?P<S2>[^、。\dはにがを]{{1,4}}?(?:曜日|日|月))に\s*{NUM}\s*({CNT})',s)
    k=re.fullmatch(rf'(?P<S3>[^、。\d]{{1,4}}?(?:曜日|日|月))は(?P<S4>[^、。\d]{{1,4}}?(?:曜日|日|月))より何\s*({CNT})(?P<cmp>多く|少なく)[^。]*?[。？?]?',q)
    if m and k and U(m.group(3))==U(m.group(6))==U(k.group(3)) and _n_amts(t)==2:
        c=U(m.group(3));v={m['S1']:(m.group(2)),m['S2']:(m.group(5))}
        if set(v)!={k['S3'],k['S4']}:return None
        hi,lo=(k['S3'],k['S4']) if k['cmp']=='多く' else (k['S4'],k['S3'])
        if _f(v[hi])<=_f(v[lo]):return None
        x=b.bind('more',c,_f(v[hi]),m.group(0));y=b.bind('less',c,_f(v[lo]),m.group(0))
        b.rel('difference',c,f'{x} - {y}',q);return b.spec('difference','diff_slots')
    m=re.search(rf'(?P<K1>[^、。\dはにがを]{{1,4}}?)が\s*{NUM}\s*人、\s*(?P<K2>[^、。\dはにがを]{{1,4}}?)が\s*{NUM}\s*人',s)
    k=re.fullmatch(rf'(?P<K3>[^、。\d]{{1,4}}?)は(?P<K4>[^、。\d]{{1,4}}?)より何人(?P<cmp>多い|少ない)ですか[。？?]?',q)
    if m and k and {m['K1'],m['K2']}=={k['K3'],k['K4']} and _n_amts(t)==2:
        v={m['K1']:m.group(2),m['K2']:m.group(4)}
        hi,lo=(k['K3'],k['K4']) if k['cmp']=='多い' else (k['K4'],k['K3'])
        if _f(v[hi])<=_f(v[lo]):return None
        x=b.bind('more','人',_f(v[hi]),m.group(0));y=b.bind('less','人',_f(v[lo]),m.group(0))
        b.rel('difference','人',f'{x} - {y}',q);return b.spec('difference','diff_slots')
    return None


def _age_then(t,stm,q):
    if len(stm)!=2:return None
    b=_B(t)
    a=re.fullmatch(rf'(?P<A>[^、。]+?)は(?P<B>[^、。]+?)より\s*{NUM}\s*(?:才|歳)(?P<c>年上|年下)です。?',stm[0])
    c=re.fullmatch(rf'(?P<B2>[^、。]+?)は\s*{NUM}\s*(?:才|歳)です。?',stm[1])
    k=re.fullmatch(rf'(?P<A2>[^、。]+?)は\s*{NUM}\s*年後に何(?:才|歳)になりますか[。？?]?',q)
    if not (a and c and k) or _who(c['B2'])!=_who(a['B']) or _who(k['A2'])!=_who(a['A']):return None
    if a['c']=='年下' and _f(a.group(3))>=_f(c.group(2)):return None
    d=b.bind('difference','才',_f(a.group(3)),stm[0]);x=b.bind('other','才',_f(c.group(2)),stm[1]);n=b.bind('years','才',_f(k.group(2)),q)
    b.rel('age','才',f"{x} {'+' if a['c']=='年上' else '-'} {d} + {n}",q);return b.spec('age','age_then')


def _finisher(t,stm,q):
    if len(stm)!=2:return None
    b=_B(t)
    a=re.fullmatch(rf'1人目は\s*{NUM}\s*(分|秒|時間)でゴールしました。?',stm[0])
    c=re.fullmatch(rf'2人目は(?:それ|1人目)より\s*{NUM}\s*(分|秒|時間)(?P<c>おそく|遅く|はやく|早く)ゴールしました。?',stm[1])
    k=re.fullmatch(rf'2人目は何\s*(分|秒|時間)かかりましたか[。？?]?',q)
    if not (a and c and k) or not (a.group(2)==c.group(2)==k.group(1)):return None
    u=_C[a.group(2)];sign='+' if c['c'] in ('おそく','遅く') else '-'
    if sign=='-' and _f(c.group(1))>=_f(a.group(1)):return None
    x=b.bind('first',u,_f(a.group(1)),stm[0]);d=b.bind('difference',u,_f(c.group(1)),stm[1])
    b.rel('second',u,f'{x} {sign} {d}',q);return b.spec('second','finisher')


def _rest(t,stm,q):
    s=''.join(stm);b=_B(t)
    if not re.search(r'残り|のこり|のこって|残って|食べていない|読んでいない|になりましたか',q):return None
    au=_ask_unit(q)
    pats=[rf'{NUM}\s*({CNT})(?:焼き|作り|つくり|買い)、\s*そのうち\s*{NUM}\s*({CNT})(?:を)?(?:売り|食べ|あげ|使い|配り)',
          rf'{NUM}\s*({CNT})の[^、。]{{1,6}}?のうち\s*{NUM}\s*({CNT})(?:を)?(?:読み|使い|食べ|売り)',
          rf'{NUM}\s*({CNT})の[^、。]{{1,6}}?から\s*{NUM}\s*({CNT})(?:を)?(?:切り取り|切りとり|使い|切り)',
          rf'{NUM}\s*({CNT})に分けました。\s*{NUM}\s*({CNT})(?:を)?食べ',
          rf'{NUM}\s*({CNT})の水が入っています。\s*{NUM}\s*({CNT})(?:を)?(?:ぬき|抜き|使い|すて|捨て)',
          rf'[^、。\d]+?が\s*{NUM}\s*({CNT})ありました。\s*{NUM}\s*({CNT})(?:を)?(?:食べ|使い|あげ|売り)']
    for p in pats:
        m=re.search(p,s)
        if m:break
    else:
        m=None
    if m:
        c1,c2=U(m.group(2)),U(m.group(4))
        if c1!=c2 or (au and au!=c1) or _n_amts(t)!=2:return None
        if au is None and not re.search(r'いくつ',q):return None
        if _f(m.group(3))>_f(m.group(1)):return None
        x=b.bind('whole',c1,_f(m.group(1)),m.group(0),integer=_whole(c1));y=b.bind('part',c1,_f(m.group(3)),m.group(0),integer=_whole(c1))
        b.rel('rest',c1,f'{x} - {y}',q,integer=_whole(c1));return b.spec('rest','rest')
    # 赤い花を18本、黄色い花を27本持っています。15本あげました。花は何本のこっていますか
    m=re.search(rf'[^、。\d]+?を\s*{NUM}\s*({CNT})、\s*[^、。\d]+?を\s*{NUM}\s*({CNT})持っています。\s*{NUM}\s*({CNT})(?:を)?(?:あげ|食べ|使い|売り)',s)
    if m and U(m.group(2))==U(m.group(4))==U(m.group(6))==au and _n_amts(t)==3:
        c=au;x=b.bind('first',c,_f(m.group(1)),m.group(0));y=b.bind('second',c,_f(m.group(3)),m.group(0));z=b.bind('given',c,_f(m.group(5)),m.group(0))
        if _f(m.group(5))>_f(m.group(1))+_f(m.group(3)):return None
        b.rel('rest',c,f'{x} + {y} - {z}',q);return b.spec('rest','rest')
    return None


FRAC={'半分':Fraction(1,2)}
def _part(t,stm,q):
    s=''.join(stm);b=_B(t);au=_ask_unit(q)
    # '赤くないあめは何こ', 'カメラを持ってこなかったのは': the other part, not read by these forms
    if re.search(r'ない|なかった|ません|以外|ほか',q):return None
    m=re.search(rf'{NUM}\s*円の\s*(\d+)\s*/\s*(\d+)を(?:使い|使って)',s)
    if m and au=='円' and re.search(r'使ったのは何円',q):
        w=b.bind('whole','円',_f(m.group(1)),m.group(0),integer=False);f=b.bind('share','1',Fraction(int(m.group(2)),int(m.group(3))),m.group(0),integer=False)
        b.rel('part','円',f'{w} * {f}',q,integer=False);return b.spec('part','part')
    m=re.search(rf'{NUM}\s*({CNT})のうち、?\s*半分が',s) or re.search(rf'{NUM}\s*({CNT})(?:入っています|あります|います)。\s*そのうち半分が',s)
    if m and au==U(m.group(2)) and _n_amts(t)==1:
        c=au
        if _whole(c) and (_f(m.group(1))/2).denominator!=1:return None
        w=b.bind('whole',c,_f(m.group(1)),m.group(0));h=b.bind('half','1',Fraction(1,2),m.group(0),integer=False)
        b.rel('part',c,f'{w} * {h}',q);return b.spec('part','part')
    m=re.search(rf'{NUM}\s*({CNT})(?:入っています|あります|います)。\s*そのうち\s*{NUM}\s*%が',s)
    if m and au==U(m.group(2)) and _n_amts(t)==1:
        c=au;v=_f(m.group(1))*_f(m.group(3))/100
        if _whole(c) and v.denominator!=1:return None
        w=b.bind('whole',c,_f(m.group(1)),m.group(0));p=b.bind('percent','1',_f(m.group(3)),m.group(0),integer=False)
        b.rel('part',c,f'{w} * {p} / 100',q);return b.spec('part','part')
    m=re.search(rf'{NUM}\s*({CNT})持っていました。\s*その半分を[^、。]*?(?:あげ|使い|売り)',s)
    if m and au==U(m.group(2)) and re.search(r'何\s*'+re.escape(m.group(2))+r'になりましたか|のこり|残り',q) and _n_amts(t)==1:
        c=au
        if _whole(c) and (_f(m.group(1))/2).denominator!=1:return None
        w=b.bind('whole',c,_f(m.group(1)),m.group(0));h=b.bind('half','1',Fraction(1,2),m.group(0)[m.group(0).index('その半分'):],integer=False)
        b.rel('left',c,f'{w} - {w} * {h}',q);return b.spec('left','part')
    m=re.search(rf'{NUM}\s*円の[^、。]*?が\s*(\d+)\s*わり引き',s)
    if m and re.search(r'(?:売りね|ねだん|代金)は何円|いくら',q) and len(re.findall(r'\d+',t))==2:          # '1わり' is not 1羽
        w=b.bind('price','円',_f(m.group(1)),m.group(0),integer=False);k=b.bind('wari','1',_f(m.group(2)),m.group(0),integer=False)
        b.known('ten','1',10,'1わりは10分の1')
        b.rel('sale','円',f'{w} - {w} * {k} / ten',q,integer=False);return b.spec('sale','part')
    return None


def _times(t,stm,q):
    s=''.join(stm);b=_B(t)
    m=re.search(rf'(?P<A>[^、。]+?)は[^、。]*?{NUM}\s*({CNT})持っています。\s*(?P<B>[^、。]+?)はその\s*{NUM}\s*倍持っています',s)
    k=re.fullmatch(rf'(?P<B2>[^、。]+?)は何\s*({CNT})持っていますか[。？?]?',q)
    if m and k and _who(k['B2'])==_who(m['B']) and U(k.group(2))==U(m.group(3)):
        c=U(m.group(3));x=b.bind('base',c,_f(m.group(2)),m.group(0));n=b.bind('times','1',_f(m.group(5)),m.group(0),integer=False)
        b.rel('other',c,f'{n} * {x}',q);return b.spec('other','times')
    m=re.search(rf'(?P<X>[^、。\d]+?)が\s*{NUM}\s*({CNT})いて、\s*(?P<Y>[^、。\d]+?)は(?P<X2>[^、。\d]+?)の\s*{NUM}\s*倍います',s)
    k=re.fullmatch(rf'(?P<Y2>[^、。\d]+?)は何\s*({CNT})いますか[。？?]?',q)
    if m and k and m['X2']==m['X'] and k['Y2']==m['Y'] and U(k.group(2))==U(m.group(3)):
        c=U(m.group(3));x=b.bind('base',c,_f(m.group(2)),m.group(0));n=b.bind('times','1',_f(m.group(6)),m.group(0),integer=False)
        b.rel('other',c,f'{n} * {x}',q);return b.spec('other','times')
    m=re.search(rf'(?P<A>[^、。]+?)の[^、。]{{1,4}}?の数は、?\s*(?P<B>[^、。]+?)の\s*{NUM}\s*倍で\s*{NUM}\s*({CNT})です',s)
    k=re.fullmatch(rf'(?P<B2>[^、。]+?)は何\s*({CNT})持っていますか[。？?]?',q)
    if m and k and _who(k['B2'])==_who(m['B']) and U(k.group(2))==U(m.group(5)):
        c=U(m.group(5))
        if (_f(m.group(4))/_f(m.group(3))).denominator!=1:return None
        n=b.bind('times','1',_f(m.group(3)),m.group(0),integer=False);x=b.bind('total',c,_f(m.group(4)),m.group(0))
        b.rel('other',c,f'{x} / {n}',q);return b.spec('other','times')
    return None


def _share(t,stm,q):
    s=''.join(stm);b=_B(t);au=_ask_unit(q)
    m=re.search(rf'{NUM}\s*({CNT})を\s*{NUM}\s*({CNT})に同じ数ずつ(?:入れ|分け|配り|くばり)',s)
    if m and au==U(m.group(2)) and re.search(rf'1\s*{m.group(4)}(?:に|は|あたり)?\s*何',q):
        c=au;G=U(m.group(4))
        if _whole(c) and (_f(m.group(1))/_f(m.group(3))).denominator!=1:return None
        n=b.bind('total',c,_f(m.group(1)),m.group(0),integer=False);g=b.bind('groups',G,_f(m.group(3)),m.group(0),integer=False)
        b.skip('1','「1…何」の1 (問いの単位)')
        b.rel('each',f'{c}/{G}',f'{n} / {g}',q,integer=_whole(c));return b.spec('each','share')
    m=re.search(rf'{NUM}\s*(cm|m|mm|km|L|mL|dL|kg|g)の[^、。]{{1,6}}?を\s*{NUM}\s*等分',s)
    if m and au==m.group(2) and re.search(r'1\s*(?:本|つ|こ|個|まい|枚)は何',q):
        u=m.group(2);n=b.bind('total',u,_f(m.group(1)),m.group(0),integer=False);k=b.bind('parts','1',_f(m.group(3)),m.group(0),integer=False)
        b.skip('1','「1…何」の1 (問いの単位)')
        b.rel('each',u,f'{n} / {k}',q,integer=False);return b.spec('each','share')
    return None


def _buy_count(t,stm,q):
    s=''.join(stm);b=_B(t)
    m=re.search(rf'1\s*({CNT})\s*{NUM}\s*円です',s);k=re.search(rf'{NUM}\s*円では何\s*({CNT})買えますか',q)
    if not (m and k) or U(m.group(1))!=U(k.group(2)) or _n_amts(t)!=3:return None
    c=U(m.group(1))
    if (_f(k.group(1))/_f(m.group(2))).denominator!=1:return None
    p=b.bind('price',f'円/{c}',_f(m.group(2)),m.group(0),integer=False);w=b.bind('money','円',_f(k.group(1)),q,integer=False)
    b.skip('1','1つあたりの量の1 (割合のもと)')
    b.rel('count',c,f'{w} / {p}',q);return b.spec('count','buy_count')


def _two_numbers(t,stm,q):
    if len(stm)!=2:return None
    b=_B(t)
    a=re.fullmatch(rf'2つの数をたすと\s*{NUM}\s*になります。?',stm[0]);c=re.fullmatch(rf'1つは\s*{NUM}\s*です。?',stm[1])
    if not (a and c and re.fullmatch(r'もう1つの数はいくつですか[。？?]?',q)):return None
    x=b.bind('sum','1',_f(a.group(1)),stm[0],integer=False);y=b.bind('one','1',_f(c.group(1)),stm[1],integer=False)
    b.skip('2','2つの数: 数の個数');b.skip('1','1つ: そのうちの1つ')
    b.rel('other','1',f'{x} - {y}',q,integer=False);return b.spec('other','two_numbers')


def _clock(t,stm,q):
    s=''.join(stm);b=_B(t)
    m=re.search(rf'{NUM}\s*時に始まり、\s*{NUM}\s*時間(?:続き|かかり)ました',s)
    if not m or not re.search(r'何時に終わりましたか',q):return None
    h,d=_f(m.group(1)),_f(m.group(2))
    if not (1<=h<=12 and h+d<=12):return None
    x=b.bind('start','時',h,m.group(0));y=b.bind('length','時',d,m.group(0))
    b.rel('end','時',f'{x} + {y}',q);return b.spec('end','clock')


CONVJ={('kg','g'):1000,('m','cm'):100,('km','m'):1000,('L','mL'):1000,('L','dL'):10,('t','kg'):1000,('cm','mm'):10}
def _convert(t,stm,q):
    if stm:return None
    b=_B(t)
    m=re.fullmatch(rf'{NUM}\s*(kg|g|m|cm|km|L|mL|dL|t|mm)の[^、。\d]{{1,8}}?は何\s*(kg|g|m|cm|km|L|mL|dL|t|mm)ですか[。？?]?',q)
    if not m or (m.group(2),m.group(3)) not in CONVJ:return None
    u1,u2=m.group(2),m.group(3);k=CONVJ[(u1,u2)]
    a=b.bind('given',u1,_f(m.group(1)),q,integer=False);kk=b.known('per',f'{u2}/{u1}',k,f'1{u1} = {k}{u2}')
    b.rel('converted',u2,f'{a} * {kk}',q,integer=False);return b.spec('converted','convert')


def _from_to(t,stm,q):
    s=''.join(stm);b=_B(t)
    m=re.search(rf'{NUM}\s*({CNT})から\s*{NUM}\s*({CNT})に(?P<v>上がり|下がり|ふえ|増え|へり|減り)ました',s)
    k=re.fullmatch(rf'何\s*({CNT})(?P<v2>上がり|下がり|ふえ|増え|へり|減り)ましたか[。？?]?',q)
    if not (m and k) or not (U(m.group(2))==U(m.group(4))==U(k.group(1))) or _n_amts(t)!=2:return None
    up=m['v'] in ('上がり','ふえ','増え')
    if up!=(k['v2'] in ('上がり','ふえ','増え')):return None
    a,c=_f(m.group(1)),_f(m.group(3))
    if (c<=a) if up else (c>=a):return None
    u=U(m.group(2));x=b.bind('from',u,a,m.group(0),integer=False);y=b.bind('to',u,c,m.group(0),integer=False)
    b.rel('change',u,f'{y} - {x}' if up else f'{x} - {y}',q,integer=False);return b.spec('change','from_to')


def _round_trip(t,stm,q):
    s=''.join(stm);b=_B(t)
    m=re.search(rf'まで\s*{NUM}\s*(km|m)歩いて行き、\s*同じ道を歩いて帰ります',s)
    k=re.search(rf'{NUM}\s*日間で何\s*(km|m)歩きますか',q)
    if not (m and k) or m.group(2)!=k.group(2) or _n_amts(t)!=2:return None
    u=m.group(2);d=b.bind('one_way',f'{u}/日',_f(m.group(1)),m.group(0),integer=False);w=b.known('legs','1',2,'行きと帰りで2回')
    n=b.bind('days','日',_f(k.group(1)),q,integer=False)
    b.rel('total',u,f'{d} * {w} * {n}',q,integer=False);return b.spec('total','round_trip')


def _boxes(t,stm,q):
    s=''.join(stm);b=_B(t)
    m=re.search(rf'1\s*({CNT})に[^、。\d]*?が\s*{NUM}\s*({CNT})入ります',s)
    k=re.search(rf'[^、。\d]*?{NUM}\s*({CNT})を入れるには何\s*({CNT})いりますか',q)
    if not (m and k) or U(m.group(1))!=U(k.group(3)) or U(m.group(3))!=U(k.group(2)) or _n_amts(t)!=3:return None
    G,c=U(m.group(1)),U(m.group(3))
    sz=b.bind('size',f'{c}/{G}',_f(m.group(2)),m.group(0),integer=False);n=b.bind('total',c,_f(k.group(1)),q,integer=False)
    b.skip('1','1つあたりの量の1 (割合のもと)')
    b.rel('groups',G,f'ceil({n} / {sz})',q);return b.spec('groups','boxes')


def _daily(t,stm,q):
    s=''.join(stm);b=_B(t)
    m=re.search(rf'毎日[^、。\d]*?{NUM}\s*({CNT})ずつ\s*{NUM}\s*日間',s)
    if m and _ask_unit(q)==U(m.group(2)) and re.search(r'全部で|あわせて|合わせて',q) and _n_amts(t)==2:
        c=U(m.group(2));r=b.bind('rate',f'{c}/日',_f(m.group(1)),m.group(0),integer=False);n=b.bind('days','日',_f(m.group(3)),m.group(0),integer=False)
        b.rel('total',c,f'{r} * {n}',q,integer=_whole(c));return b.spec('total','daily')
    m=re.search(rf'毎日\s*{NUM}\s*({CNT})ずつ[^、。\d]*?(?:読み|食べ|走り|歩き|作り)ます',s)
    if m and _ask_unit(q)==U(m.group(2)) and re.search(r'1\s*週間では何',q) and _n_amts(t)==2:
        c=U(m.group(2));r=b.bind('rate',f'{c}/日',_f(m.group(1)),m.group(0),integer=False);w=b.known('week','日',7,'1週間は7日')
        b.skip('1','1週間の1 (期間の単位)')
        b.rel('total',c,f'{r} * {w}',q,integer=_whole(c));return b.spec('total','daily')
    return None


def _rect(t,stm,q):
    if stm:return None
    b=_B(t)
    m=re.search(rf'(?:たて|縦)\s*{NUM}\s*(cm|m|km|mm)、\s*(?:よこ|横)\s*{NUM}\s*(cm|m|km|mm)の長方形の[^、。\d]{{1,6}}?の面積は何\s*(cm|m|km|mm)(?:²|2|\^2)',q)
    if not m or not (m.group(2)==m.group(4)==m.group(5)):return None
    u=m.group(2);a=b.bind('length',u,_f(m.group(1)),m.group(0),integer=False);c=b.bind('width',u,_f(m.group(3)),m.group(0),integer=False)
    if re.search(r'(cm|m|km|mm)2',q):b.skip('2','平方の2 (面積の単位)')
    b.rel('area',f'{u}^2',f'{a} * {c}',q,integer=False);return b.spec('area','rect')


FORMS=(_rect,_per_one,_per_item,_zutsu,_measure_cmp,_cmp_inverse,_cmp_total,_diff_slots,_age_then,_finisher,_rest,_part,_times,_share,
       _buy_count,_two_numbers,_clock,_convert,_from_to,_round_trip,_boxes,_daily)
