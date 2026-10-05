"""claude-patch6: more problem families (Japanese + simple English), same rules as wordprob.py.

  average        3回の点数は72点、84点、90点。平均は何点？ / the average of 14 cm, 20 cm and 23 cm
  shapes         長方形・正方形・三角形の面積、長方形・正方形のまわりの長さ (rectangle / square area, perimeter)
  lcm / gcd      12と18の最小公倍数、24と36の最大公約数 (least common multiple, greatest common divisor)
  sequence       3, 7, 11, 15 の次の数 (four or more terms, constant difference or constant ratio)
  part of        72個の3分の1、40人の60%、800円の25%
  division       あまり (remainder), 全員が…何台いりますか (rounding up), いくつできますか (rounding down)
  inverse group  8人に3個ずつ配ると5個あまりました。はじめに何個？ (and …4個足りません)
  each x groups  子どもが8人います。1人に3本ずつ配ると何本いりますか / 6 rows with 9 chairs in each row
  per period     毎日3ページずつ…2週間で何ページ / 1日に20分ずつ…7日で何分
  complement     36人のうち、めがねをかけている人は9人。かけていない人は？
  difference     赤いビー玉が25個、青いビー玉が17個。ちがいは何個？
  times          父の年齢は子どもの年齢の4倍で、子どもは9歳。父は何歳？
  prices         300円の本と500円のノートの合計 / 1000円札で…のおつり / 300円持っています…残りは / pens cost 3 dollars each
  durations      1時間20分の映画を2本続けて見ると全部で何分 / a train travels 240 km in 3 hours
Fail closed: every number of the question must be read by the family, hedged or negated amounts
refuse, results are exact (a count that would not be whole refuses) and never negative.
solve() returns None, {'refused': reason} or {'answer','proof'}; proofs.check replays the proof.
"""
from __future__ import annotations
import math,re,unicodedata
from fractions import Fraction
from functools import reduce
from .wordprob import _norm

NUM=r'(\d+(?:\.\d+)?)'
COUNTER=r'個|人|本|枚|冊|台|匹|羽|頭|円|点|回|cm|m|km|g|kg|L|mL|dL|ページ|分|秒|時間|日|歳|脚|着|足|杯|袋|箱|束|つ|組|班|列|チーム|グループ|皿|かご|たば|束'
HEDGE=re.compile(r'予定|つもり|かもしれ|らしい|だろう|と言|と聞|もし(?!も)|ぐらい|くらい|ほど|程度|(?<!公)約(?!数)|およそ|だいたい|大体|ほぼ|以上|以下|未満|少なくとも|最大(?!公)|最低|せいぜい|[〜~～]|'
                 r'または|もしくは|不明|かどうか|(?:何(?:個|人|本|枚|冊|匹|羽|台|円|頭|つ|点|回)|いくつ|いくら)か(?![？?。]|$)|たくさん|少し|数(?:個|人|本|枚|冊)|'
                 r'\bsome\b|\bseveral\b|\babout\b|\bapproximately\b|\bmaybe\b|\bmight\b|\baround\b',re.I)

def _fmt(v):
    v=Fraction(v);return str(v.numerator) if v.denominator==1 else format(float(v),'.12g')
def _nums(t):return list(re.finditer(r'\d+(?:\.\d+)?',t))
class _No(Exception):pass
def _need(c):
    if not c:raise _No()
def _all_read(t,used):
    """every number of the question is one of the numbers the family read (by position)"""
    spans=[(m.start(),m.end()) for m in _nums(t)]
    return sorted(spans)==sorted(set(used))
def _out(family,label,expr,value,unit,given,query,whole=True):
    value=Fraction(value)
    if value<0:return {'refused':'MATHPROB_NEGATIVE'}
    if (whole or unit=='円') and value.denominator!=1:return {'refused':'MATHPROB_NOT_WHOLE'}
    d=value.denominator
    while d%2==0:d//=2
    while d%5==0:d//=5
    if d!=1:return {'refused':'MATHPROB_NOT_A_TERMINATING_DECIMAL'}
    proof={'kind':'mathprob','family':family,'label':label,'expression':expr,'given':[_fmt(g) for g in given],'unit':unit,'answer':_fmt(value),'source_query':str(query)}
    return {'answer':_fmt(value),'proof':proof}
COUNTABLE=('個','人','本','枚','冊','台','匹','羽','頭','脚','着','足','杯','袋','箱','束','つ','組','班','列','チーム','グループ','皿','かご','たば','回','ページ')

# ------------------------------------------------------------------ Japanese families
def _ja_average(t,q,query):
    if '平均' not in q:return None
    head=t[:len(t)-len(q)] if t.endswith(q) else t
    vals=list(re.finditer(NUM+r'\s*('+COUNTER+r'|度)(?!\d)',head))
    cnt=re.search(NUM+r'\s*(回|人|日間|日|週|か月|チーム|試合|教科|本|冊|個|匹|頭)(?:の|で|間で|間の|に)',head)
    used=[m.span(1) for m in vals]
    if cnt and cnt.span(1) in used:used.remove(cnt.span(1));vals=[m for m in vals if m.span(1)!=cnt.span(1)]
    per=re.search(r'1\s*(?:日|人|回|試合|か月|週)\s*(?:あたり|の)?\s*平均',t)
    if per:used.append((per.start(),per.start()+1))
    extra=[Fraction(1)] if per else []
    _need(len(vals)>=2 and len({m[2] for m in vals})==1)
    if cnt:
        _need(Fraction(cnt[1])==len(vals));used.append(cnt.span(1))
    _need(_all_read(t,used))
    u=vals[0][2];asked=re.search(r'何\s*('+COUNTER+r'|度)',q)
    if asked:_need(asked[1]==u)
    s=sum(Fraction(m[1]) for m in vals);n=len(vals)
    return _out('average','合計÷個数','('+'+'.join(m[1] for m in vals)+f')/{n}',s/n,u,[Fraction(m[1]) for m in vals]+([Fraction(cnt[1])] if cnt else [])+extra,query,whole=False)

AREA_U={'cm':'cm','m':'m','km':'km','mm':'mm'}
def _ja_shape(t,q,query):
    area=bool(re.search(r'面積',q));peri=bool(re.search(r'まわり|周り|周の長さ|周囲',q))
    if not (area or peri) or area and peri:return None
    shape=re.search(r'長方形|正方形|三角形',t)
    _need(shape)
    if shape.group()=='長方形':
        a=re.search(r'(?:たて|縦)(?:の長さ)?(?:が|は)?\s*'+NUM+r'\s*(cm|m|km|mm)',t);b=re.search(r'(?:よこ|横)(?:の長さ)?(?:が|は)?\s*'+NUM+r'\s*(cm|m|km|mm)',t)
        _need(a and b and a[2]==b[2] and _all_read(t,[a.span(1),b.span(1)]))
        x,y,u=Fraction(a[1]),Fraction(b[1]),a[2]
        if area:return _out('area','たて×よこ',f'{a[1]}*{b[1]}',x*y,u+'2',[x,y],query,whole=False)
        return _out('perimeter','（たて＋よこ）×2',f'({a[1]}+{b[1]})*2',(x+y)*2,u,[x,y],query,whole=False)
    if shape.group()=='正方形':
        a=re.search(r'(?:1\s*辺|一辺)(?:の長さ)?(?:が|は)?\s*'+NUM+r'\s*(cm|m|km|mm)',t)
        _need(a);one=re.search(r'1\s*辺',t)
        _need(_all_read(t,[a.span(1)]+([(one.start(),one.start()+1)] if one else [])))
        x,u=Fraction(a[1]),a[2];g=[x]+([Fraction(1)] if one else [])
        if area:return _out('area','1辺×1辺',f'{a[1]}*{a[1]}',x*x,u+'2',g,query,whole=False)
        return _out('perimeter','1辺×4',f'{a[1]}*4',x*4,u,g,query,whole=False)
    _need(area)
    a=re.search(r'底辺(?:が|は)?\s*'+NUM+r'\s*(cm|m|km|mm)',t);b=re.search(r'高さ(?:が|は)?\s*'+NUM+r'\s*(cm|m|km|mm)',t)
    _need(a and b and a[2]==b[2] and _all_read(t,[a.span(1),b.span(1)]))
    x,y=Fraction(a[1]),Fraction(b[1])
    return _out('area','底辺×高さ÷2',f'{a[1]}*{b[1]}/2',x*y/2,a[2]+'2',[x,y],query,whole=False)

def _ja_lcm_gcd(t,q,query):
    m=re.search(r'最小公倍数|最大公約数',t)
    if not m:return None
    ns=_nums(t);_need(2<=len(ns)<=4 and all(x.group().isdigit() and int(x.group())>0 for x in ns))
    _need(re.fullmatch(r'\s*'+r'\s*(?:と|、|,)\s*'.join(r'\d+' for _ in ns)+r'\s*の\s*(?:最小公倍数|最大公約数)\s*(?:は|を)?\s*(?:いくつ|何|なん|求め)?\S{0,8}',t))
    v=[int(x.group()) for x in ns]
    if m.group()=='最小公倍数':return _out('lcm','最小公倍数',f'lcm({",".join(map(str,v))})',reduce(lambda a,b:a*b//math.gcd(a,b),v),'',v,query)
    return _out('gcd','最大公約数',f'gcd({",".join(map(str,v))})',reduce(math.gcd,v),'',v,query)

def _sequence(t,q,query):
    m=re.search(r'((?:\d+\s*[,、，]\s*){3,}\d+)\s*[,、，]?\s*(?:…|\.\.\.|・・・)?\s*(?:の|と続く数の|と並んでいます。?)?\s*(?:次の数|つぎの数|次は|つぎは|次に来る数|what comes next|next number)',t,re.I)
    if not m:
        m=re.search(r'((?:\d+\s*,\s*){3,}\d+)\s*,?\s*(?:\.\.\.|…)?\s*(?:what (?:is|comes) (?:the )?next|what number comes next)',t,re.I)
    if not m:return None
    v=[Fraction(x) for x in re.findall(r'\d+',m[1])];_need(_all_read(t,[x.span() for x in _nums(m[1])]) or len(_nums(t))==len(v))
    d={v[i+1]-v[i] for i in range(len(v)-1)}
    if len(d)==1:
        dd=d.pop();return _out('sequence','同じ数ずつ増える（減る）',f'{_fmt(v[-1])}+({_fmt(dd)})',v[-1]+dd,'',v,query)
    _need(all(x!=0 for x in v[:-1]))
    r={v[i+1]/v[i] for i in range(len(v)-1)}
    _need(len(r)==1)
    rr=r.pop();_need(rr.denominator==1)
    return _out('sequence','同じ数ずつかける',f'{_fmt(v[-1])}*{_fmt(rr)}',v[-1]*rr,'',v,query)

def _ja_part_of(t,q,query):
    m=re.search(NUM+r'\s*('+COUNTER+r')?\s*の\s*(?:[^、。\d]{1,8}?の\s*)?'+NUM+r'\s*分の\s*'+NUM+r'\s*(?:は|って)?\s*何\s*('+COUNTER+r')?',t)
    if m:
        _need(_all_read(t,[m.span(1),m.span(3),m.span(4)]) and (not m[2] or not m[5] or m[2]==m[5]))
        n,d,k=Fraction(m[1]),Fraction(m[3]),Fraction(m[4]);_need(d!=0)
        u=m[2] or m[5] or ''
        return _out('part_of','全体×分子÷分母',f'{m[1]}*{m[4]}/{m[3]}',n*k/d,u,[n,d,k],query,whole=u in COUNTABLE)
    m=re.search(NUM+r'\s*('+COUNTER+r')の(?:学級|クラス|学年|グループ|チーム|集まり)?(?:で|が|は)?[、,]?\s*(?:そのうち|その)\s*'+NUM+r'\s*(?:%|パーセント)\s*(?:が|は)\s*([^、。\d]{1,8}?)(?:です|でした|だ)',t)
    if m:
        a=re.search(re.escape(m[4])+r'\s*(?:は|が)\s*何\s*('+COUNTER+r')',q)
        _need(a and a[1]==m[2] and _all_read(t,[m.span(1),m.span(3)]))
        n,p=Fraction(m[1]),Fraction(m[3])
        return _out('part_of','全体×割合',f'{m[1]}*{m[3]}/100',n*p/100,m[2],[n,p],query,whole=m[2] in COUNTABLE)
    # 「45人のクラスで、そのうち3分の1が自転車で通学しています。自転車で通学しているのは何人？」
    m=re.search(NUM+r'\s*('+COUNTER+r')の(?:学級|クラス|学年|グループ|チーム|集まり|[^、。\d]{1,6}?)?(?:で|が|は)?[、,]?\s*(?:そのうち|その)\s*(?:'+NUM+r'\s*分の\s*'+NUM+r'|'+NUM+r'\s*(?:%|パーセント))\s*(?:が|は)\s*([^。\d]{2,20}?)[。]',t)
    if m:
        stem=re.sub(r'(?:ています|ていました|でいます|でいました|います|いました|です|でした|ます|ました)$','',m[6])
        _need(len(stem)>=2 and not re.search(r'ない|ません',q))
        a=re.search(re.escape(stem[:max(2,len(stem)-1)])+r'[^、。\d]{0,6}?(?:の|人|もの)?(?:は|が)\s*何\s*('+COUNTER+r')',q)
        _need(a and a[1]==m[2])
        n=Fraction(m[1])
        if m[3]:
            d,k=Fraction(m[3]),Fraction(m[4]);_need(d!=0 and _all_read(t,[m.span(1),m.span(3),m.span(4)]))
            return _out('part_of','全体×分子÷分母',f'{m[1]}*{m[4]}/{m[3]}',n*k/d,m[2],[n,d,k],query,whole=m[2] in COUNTABLE)
        p=Fraction(m[5]);_need(_all_read(t,[m.span(1),m.span(5)]))
        return _out('part_of','全体×割合',f'{m[1]}*{m[5]}/100',n*p/100,m[2],[n,p],query,whole=m[2] in COUNTABLE)
    return None

def _ja_division(t,q,query):
    m=re.search(NUM+r'\s*('+COUNTER+r')(?:の[^、。\d]{1,10}?)?\s*(?:を|が)\s*(?:1\s*(人|台|つ|個|箱|袋|脚|列|組|回|日)(?:の[^、。\d]{1,6}?)?)?\s*(?:に|で|あたり)?\s*'+NUM+r'\s*\2\s*ずつ',t)
    if not m:
        m2=re.search(NUM+r'\s*(人)(?:の[^、。\d]{1,10}?)?\s*(?:が|を)\s*1\s*(台|つ|脚|列|組|艘|そう)\s*(?:の[^、。\d]{1,6}?)?\s*(?:に|で)\s*'+NUM+r'\s*人\s*ずつ',t)
        if not m2:return None
        n,k=Fraction(m2[1]),Fraction(m2[4]);used=[m2.span(1),m2.span(4),(m2.start(2)-1,m2.start(2))] if t[m2.start(2)-1:m2.start(2)]=='1' else [m2.span(1),m2.span(4)]
        one=re.search(r'1\s*'+re.escape(m2[3]),t);used=[m2.span(1),m2.span(4)]+([(one.start(),one.start()+1)] if one else [])
        unit=m2[3]
    else:
        n,k=Fraction(m[1]),Fraction(m[4]);one=re.search(r'1\s*'+re.escape(m[3]),t) if m[3] else None
        used=[m.span(1),m.span(4)]+([(one.start(),one.start()+1)] if one else [])
        unit=m[3]
    _need(k>0 and n.denominator==1 and k.denominator==1 and _all_read(t,used))
    q_=int(n)//int(k);r=int(n)%int(k);g=[n,k]+([Fraction(1)] if len(used)>2 else [])
    if re.search(r'あまり|余り|のこり|残り',q) and re.search(r'何\s*(?:'+COUNTER+r')',q) and not re.search(r'何(?:人|台|つ|組|回|日)\s*(?:に|分|で|できて|配れて)',q):
        return _out('remainder','わり算のあまり',f'{_fmt(n)}%{_fmt(k)}',r,'',g,query)
    if re.search(r'全員|全部|みんな|すべて|残らず',t) and re.search(r'(?:何\s*(?:台|つ|脚|列|組|回|日|箱|袋|艘|そう)|いくつ)\s*(?:いり|要り|必要|あれば|用意)',q) or re.search(r'何\s*(?:台|脚|艘)\s*(?:いり|要り|必要)',q):
        v=-(-int(n)//int(k))
        return _out('ceil_division','わり算の答えを切り上げ（あまった分にも1つ要る）',f'ceil({_fmt(n)}/{_fmt(k)})',v,'',g,query)
    if re.search(r'(?:いくつ|何\s*(?:'+COUNTER+r'))\s*(?:に|へ|で)?\s*(?:でき|作れ|つくれ|配れ|分けられ|入れられ)',q) or re.search(r'グループ|たば|束|組|班|袋|箱|皿',q) and re.search(r'いくつ|何',q):
        _need(r==0 or re.search(r'でき|作れ|つくれ|配れ',q))
        return _out('floor_division','わり算（あまりは数えない）',f'{_fmt(n)}//{_fmt(k)}',q_,'',g,query)
    return None

def _ja_inverse_group(t,q,query):
    m0=re.search(r'([^、。\d]{1,8}?)(?:が|は)\s*'+NUM+r'\s*(人)\s*(?:います|いました)[。、]?',t)
    m=re.search(r'1\s*人\s*(?:に|あたり)\s*'+NUM+r'\s*(個|本|枚|冊|つ|匹|羽|台|円)\s*ずつ[^。]*?(?:配|分け|わけ|あげ)[^。]*?'+NUM+r'\s*\2\s*(あまり|余り|足りな|足りま|たりな|たりま)',t)
    if m0 and m:
        n,k,r=Fraction(m0[2]),Fraction(m[1]),Fraction(m[3]);sign=1 if m[4] in ('あまり','余り') else -1
        one=re.search(r'1\s*人\s*(?:に|あたり)',t);used=[m0.span(2),m.span(1),m.span(3),(one.start(),one.start()+1)];unit=m[2]
    else:
        m=re.search(r'(?<![\d.])([2-9]|\d{2,})\s*(人|つ|箱|袋|皿)(?:の[^、。\d]{1,8}?)?\s*(?:に|へ)\s*(?:[^、。\d]{0,10}?)?\s*'+NUM+r'\s*(個|本|枚|冊|つ|匹|羽|台|円)\s*ずつ[^。]*?(?:配|分け|わけ|入れ|のせ|あげ)[^。]*?'+NUM+r'\s*\4\s*(あまり|余り|足りな|足りま|たりな|たりま)',t)
        if not m:return None
        n,k,r=Fraction(m[1]),Fraction(m[3]),Fraction(m[5]);sign=1 if m[6] in ('あまり','余り') else -1
        used=[m.span(1),m.span(3),m.span(5)];unit=m[4]
    _need(re.search(r'はじめ|初め|最初|全部で|もともと|何\s*'+unit+r'\s*(?:あり|あった)',q) and _all_read(t,used))
    out=_out('inverse_grouping','1つ分×いくつ分'+('＋あまり' if sign>0 else '−足りない数'),f'{_fmt(n)}*{_fmt(k)}{"+" if sign>0 else "-"}{_fmt(r)}',n*k+sign*r,unit,[n,k,r]+([Fraction(1)] if m0 and m and m0[2] else []),query)
    if 'answer' in out:out['negation_ok']=sign<0          # 「足りませんでした」 is the shortfall, not an unconfirmed event
    return out

def _ja_each_groups(t,q,query):
    m=re.search(r'([^、。\d]{1,8}?)(?:が|は)\s*'+NUM+r'\s*(人|つ|箱|袋|皿|列|チーム|組|班|台)\s*(?:います|あります|いました|ありました|います)[。、]\s*(?:[^。\d]{0,10}?)1\s*\3\s*(?:に|あたり|につき)?\s*'+NUM+r'\s*(個|本|枚|冊|匹|羽|台|円|人|つ|まい)\s*ずつ[^。]*?(?:配る|配ると|くばると|あげると|入れると|のせると|わたすと|渡すと|並べると|すわると|乗ると|配ります)',t)
    if not m:return None
    a=re.search(r'何\s*('+COUNTER+r')',q)
    _need(a and a[1]==m[5] and re.search(r'全部で|ぜんぶで|いり|要り|必要|合わせて|あわせて|みんなで|何\s*'+m[5]+r'\s*(?:です|に)',q))
    one=re.search(r'1\s*'+re.escape(m[3]),t);_need(_all_read(t,[m.span(2),m.span(4),(one.start(),one.start()+1)]))
    n,k=Fraction(m[2]),Fraction(m[4])
    return _out('each_x_groups','1つ分×いくつ分',f'{m[4]}*{m[2]}',n*k,m[5],[n,k],query)

PERIOD_DAYS={'日':1,'週':7,'週間':7}
def _ja_per_period(t,q,query):
    m=re.search(r'(?:毎日|1\s*日\s*(?:に|あたり)?)\s*'+NUM+r'\s*(ページ|分|個|枚|本|回|問|円|km|m|冊|時間)\s*ずつ',t)
    if not m:return None
    d=re.search(NUM+r'\s*(日間?|週間?)\s*(?:で|続けると|では|の間に?|たつと)',t)
    _need(d)
    one=re.search(r'1\s*日',t);used=[m.span(1),d.span(1)]+([(one.start(),one.start()+1)] if one else [])
    _need(_all_read(t,used))
    a=re.search(r'何\s*('+re.escape(m[2])+r')|いくら',q);_need(a)
    days=Fraction(d[1])*PERIOD_DAYS[d[2].replace('間','') if d[2] not in ('週間',) else '週間']
    r=Fraction(m[1])
    return _out('per_period','1日分×日数',f'{m[1]}*{_fmt(days)}',r*days,m[2],[r,Fraction(d[1])],query)

def _ja_complement(t,q,query):
    m=re.search(NUM+r'\s*(人|匹|頭|羽|個|本|枚|台)\s*(?:い|あり)ます[。、]?\s*(?:そのうち|その中で|うち)?[、,]?\s*([^、。\d]{2,14}?)(?:人|もの|の)?(?:は|が)\s*'+NUM+r'\s*\2',t)
    if not m:return None
    base=re.sub(r'(?:て|で)(?:いる|います)$','',m[3]);_need(len(base)>=2)
    neg=re.search(re.escape(base[:max(2,len(base)-1)])+r'[^、。\d]{0,4}?(?:ていない|でいない|ない|ていません|でない|ではない)[^、。\d]{0,3}?(?:人|もの)?(?:は|が)\s*何\s*'+m[2],q)
    _need(neg and _all_read(t,[m.span(1),m.span(4)]))
    n,k=Fraction(m[1]),Fraction(m[4])
    out=_out('complement','全体−あてはまる数',f'{m[1]}-{m[4]}',n-k,m[2],[n,k],query)
    if 'answer' in out:out['negation_ok']=True
    return out

def _ja_difference(t,q,query):
    if not re.search(r'ちがい|違い|差',q):return None
    items=list(re.finditer(r'([^、。\d]{1,10}?)(?:が|は)\s*(?:[^、。\d]{1,8}?を)?\s*'+NUM+r'\s*('+COUNTER+r')',t))
    _need(len(items)==2 and items[0][3]==items[1][3] and _all_read(t,[x.span(2) for x in items]))
    a=re.search(r'何\s*('+COUNTER+r')',q);_need(not a or a[1]==items[0][3])
    x,y=Fraction(items[0][2]),Fraction(items[1][2])
    return _out('difference','大きい方−小さい方',f'{_fmt(max(x,y))}-{_fmt(min(x,y))}',abs(x-y),items[0][3],[x,y],query)

def _ja_times(t,q,query):
    m=re.search(r'([^、。\d]{1,10}?)(?:の年齢|の数|の長さ|の重さ)?(?:は|が)\s*([^、。\d]{1,10}?)(?:の年齢|の数|の長さ|の重さ)?の\s*'+NUM+r'\s*倍',t)
    if not m:return None
    a,b=m[1],m[2];base=re.search(re.escape(b)+r'(?:の年齢|の数|の長さ|の重さ)?(?:は|が)\s*'+NUM+r'\s*('+COUNTER+r')',t)
    _need(base and _all_read(t,[m.span(3),base.span(1)]))
    _need(re.search(re.escape(a)+r'(?:の年齢|の数|の長さ|の重さ)?(?:は|が)\s*(?:何|いくつ)',q))
    k,v=Fraction(m[3]),Fraction(base[1])
    return _out('times','もとの数×倍',f'{base[1]}*{m[3]}',v*k,base[2],[v,k],query,whole=base[2] in COUNTABLE)

def _ja_prices(t,q,query):
    if not re.search(r'いくら|何円|代金|合計|おつり|お釣り|残り|のこり',q):return None
    items=list(re.finditer(NUM+r'\s*円の\s*([^、。\d]{1,10}?)(?=と|を|、|,)',t))
    _need(items)
    units=[re.match(r'1\s*(?:個|本|冊|枚|つ)',t[max(0,x.start()-4):x.start()]) for x in items]
    _need(not any(units) and not re.search(r'1\s*(?:個|本|冊|枚|つ|袋|箱)\s*\d',t) and not re.search(r'\d+\s*(?:個|本|冊|枚|つ)(?:買|を)',t[items[0].end():]))
    total=sum(Fraction(x[1]) for x in items);used=[x.span(1) for x in items];expr='+'.join(x[1] for x in items)
    pay=re.search(NUM+r'\s*円(?:札|玉)?(?:を|で)?\s*(?:1\s*枚)?\s*(?:出し|出して|払|で(?=[、,])|持って)',t)
    if re.search(r'おつり|お釣り|残り|のこり',q):
        _need(pay and pay.span(1) not in used);used.append(pay.span(1))
        one=re.search(r'(?<=円玉を)\s*1\s*枚|(?<=円札を)\s*1\s*枚|(?<=円札)\s*1\s*枚',t)
        if one:used.append((one.start()+len(one.group())-len(one.group().lstrip()),one.start()+len(one.group())-len(one.group().lstrip())+1))
        _need(_all_read(t,used))
        return _out('price_change','出した（持っている）額−代金の合計',f'{pay[1]}-({expr})',Fraction(pay[1])-total,'円',[Fraction(pay[1])]+[Fraction(x[1]) for x in items],query)
    _need(not pay and len(items)>=2 and _all_read(t,used) and re.search(r'合計|全部で|ぜんぶで|あわせて|合わせて|代金|いくら',q))
    return _out('price_sum','値段の合計',expr,total,'円',[Fraction(x[1]) for x in items],query)

def _ja_budget(t,q,query):
    m=re.search(r'^(?:[^、。\d]{0,10}?(?:は|が))?\s*'+NUM+r'\s*円\s*(?:持っています|あります|持っていました|ありました)[。、]',t)
    if not m or not re.search(r'残り|のこり|おつり|いくら残',q):return None
    p=re.search(r'1\s*(個|本|冊|枚|つ)\s*'+NUM+r'\s*円の\s*([^、。\d]{1,10}?)を\s*'+NUM+r'\s*(?:\1|つ)\s*(?:買|購入)',t)
    _need(p);one=re.search(r'1\s*'+re.escape(p[1]),t)
    _need(_all_read(t,[m.span(1),p.span(2),p.span(4),(one.start(),one.start()+1)]))
    a,c,n=Fraction(m[1]),Fraction(p[2]),Fraction(p[4])
    return _out('budget','持っている額−単価×個数',f'{m[1]}-{p[2]}*{p[4]}',a-c*n,'円',[a,c,n],query)

def _ja_unit_price_pay(t,q,query):
    if not re.search(r'おつり|お釣り',q):return None
    pay=re.search(NUM+r'\s*円\s*(玉|札)\s*(?:を)?\s*'+NUM+r'\s*枚\s*(?:出し|出して|で|使っ|払)',t)
    if pay:paid=Fraction(pay[1])*Fraction(pay[3]);used=[pay.span(1),pay.span(3)];given=[Fraction(pay[1]),Fraction(pay[3])];pexpr=f'{pay[1]}*{pay[3]}'
    else:
        # one bill or coin (「1000円札を出しました」「1000円札で」)
        pay=re.search(NUM+r'\s*円\s*(?:札|玉)\s*(?:を\s*(?:出し|出して|払|渡し)|で)',t)
        if not pay:return None
        paid=Fraction(pay[1]);used=[pay.span(1)];given=[paid];pexpr=pay[1]
    items=list(re.finditer(r'1\s*(個|本|冊|枚|つ)\s*'+NUM+r'\s*円の\s*[^、。\d]{1,10}?を\s*'+NUM+r'\s*(?:\1|つ)',t))
    if not items and len(used)==1:return None          # one bill and plain prices: _ja_prices reads it
    _need(items)
    expr=[];total=Fraction(0)
    for it in items:
        used+=[(it.start(),it.start()+1),it.span(2),it.span(3)];expr.append(f'{it[2]}*{it[3]}');total+=Fraction(it[2])*Fraction(it[3]);given+=[Fraction(1),Fraction(it[2]),Fraction(it[3])]
    _need(_all_read(t,used))
    return _out('price_change','出した額−代金',f'{pexpr}-('+'+'.join(expr)+')',paid-total,'円',given,query)

def _ja_duration(t,q,query):
    m=re.search(r'(?:(\d+)\s*時間)?\s*(?:(\d+)\s*分)?の\s*([^、。\d]{1,10}?)を\s*(\d+)\s*(本|回|つ|試合)\s*(?:続けて|つづけて)?\s*(?:見る|みる|する|聞く|きく)と',t)
    if not m or not (m[1] or m[2]) or not re.search(r'全部で|ぜんぶで|合わせて|あわせて|合計',q):return None
    a=re.search(r'何\s*(分|時間)',q);_need(a and a[1]=='分')
    used=[x for x in (m.span(1) if m[1] else None,m.span(2) if m[2] else None,m.span(4)) if x]
    _need(_all_read(t,used))
    mins=Fraction(m[1] or 0)*60+Fraction(m[2] or 0);n=Fraction(m[4])
    return _out('duration_x_count','1つ分の時間×数',f'({_fmt(mins)})*{m[4]}',mins*n,'分',[Fraction(m[1] or 0),Fraction(m[2] or 0),n],query)

def _ja_ratio(t,q,query):
    """「ひもAは48cm、ひもBは16cmです。ひもAはひもBの何倍の長さですか？」 -> 48/16"""
    m=re.search(r'^([^、。\d]{1,10}?)(?:の[^、。\d]{1,6}?)?(?:は|が)\s*([^、。\d]{1,10}?)(?:の[^、。\d]{1,6}?)?の\s*何倍',q)
    if not m:return None
    def val(name):return re.search(r'(?:^|[、。])'+re.escape(name)+r'(?:の[^、。\d]{1,6}?)?(?:は|が)\s*'+NUM+r'\s*('+COUNTER+r')',t)
    a,b=val(m[1]),val(m[2])
    _need(a and b and a[2]==b[2] and m[1]!=m[2] and _all_read(t,[a.span(1),b.span(1)]))
    x,y=Fraction(a[1]),Fraction(b[1]);_need(y!=0)
    return _out('ratio','くらべる量÷もとにする量',f'{a[1]}/{b[1]}',x/y,'',[x,y],query,whole=False)

def _ja_per_one(t,q,query):
    """「3個で210円のみかんがあります。1個の値段はいくらですか？」 -> 210/3"""
    m=re.search(NUM+r'\s*(個|本|冊|枚|つ|袋|箱|束|皿)\s*で\s*'+NUM+r'\s*(円)',t)
    if not m:return None
    one=re.search(r'1\s*'+re.escape(m[2])+r'\s*(?:の|あたり|あたりの|分の)?\s*(?:値段|ねだん|代金|お金)?\s*(?:は|が)?\s*(?:いくら|何\s*円)',q)
    _need(one)
    o=len(t)-len(q)+one.start();_need(_all_read(t,[m.span(1),m.span(3),(o,o+1)]))
    n,v=Fraction(m[1]),Fraction(m[3]);_need(n!=0)
    return _out('per_one','全体の値段÷個数',f'{m[3]}/{m[1]}',v/n,'円',[n,v,Fraction(1)],query)

def _ja_rows_formed(t,q,query):
    """「1列に7人ずつ並ぶと、6列できました。全部で何人いますか？」 -> 7*6"""
    m=re.search(r'1\s*(列|組|班|チーム|グループ|袋|箱|皿|たば|束|台)\s*(?:に|あたり|で)?\s*'+NUM+r'\s*(人|個|本|枚|冊|匹|羽|頭)\s*ずつ[^。]*?(?:と|たら|ところ)[、,]?\s*'+NUM+r'\s*\1\s*(?:でき|になり|になっ|作れ|つくれ)',t)
    if not m:return None
    a=re.search(r'何\s*('+COUNTER+r')',q)
    _need(a and a[1]==m[3] and re.search(r'全部で|ぜんぶで|みんなで|合わせて|あわせて|全員で|いますか|ありますか',q))
    _need(_all_read(t,[(m.start(),m.start()+1),m.span(2),m.span(4)]))
    k,n=Fraction(m[2]),Fraction(m[4])
    return _out('each_x_groups','1つ分×いくつ分',f'{m[2]}*{m[4]}',k*n,m[3],[Fraction(1),k,n],query)

SPEED_T={'時速':'時間','分速':'分','秒速':'秒'}
def _ja_speed(t,q,query):
    """「2時間で90km走る車の時速は何kmですか？」 -> 90/2"""
    a=re.search(r'(時速|分速|秒速)\s*(?:は)?\s*何\s*(km|m)',q)
    if not a:return None
    m=re.search(NUM+r'\s*(時間|分|秒)\s*(?:で|に)\s*'+NUM+r'\s*(km|m)\s*(?:を)?\s*(?:走|進|歩|泳|飛|移動)',t)
    if m:tv,tu,dv,du,used=m[1],m[2],m[3],m[4],[m.span(1),m.span(3)]
    else:
        m=re.search(NUM+r'\s*(km|m)\s*(?:の道のり)?\s*を\s*'+NUM+r'\s*(時間|分|秒)\s*で\s*(?:走|進|歩|泳|飛|移動)',t)
        if not m:return None
        dv,du,tv,tu,used=m[1],m[2],m[3],m[4],[m.span(1),m.span(3)]
    _need(SPEED_T[a[1]]==tu and du==a[2] and _all_read(t,used) and not re.search(r'時速|分速|秒速',t[:len(t)-len(q)]))
    d,h=Fraction(dv),Fraction(tv);_need(h!=0)
    return _out('speed','道のり÷時間',f'{dv}/{tv}',d/h,du,[d,h],query,whole=False)

# ------------------------------------------------------------------ English families
def _en_average(s,query):
    if not re.search(r'\baverage\b|\bmean\b',s):return None
    vals=list(re.finditer(r'(\d+(?:\.\d+)?)\s*(cm|m|kg|g|points?|dollars?|km|years?|minutes?|pages?)?(?=\s*(?:,|and\b|\.|$))',s))
    cnt=re.search(r'\b(?:of|the)\s+(\d+)\s+([a-z]+)\s+(?:are|were|is)\b',s)
    used=[x.span(1) for x in vals]
    if cnt:
        _need(cnt.span(1) not in used or True);used=[u for u in used if u!=cnt.span(1)];vals=[v for v in vals if v.span(1)!=cnt.span(1)]
    _need(len(vals)>=2 and len({(v[2] or '').rstrip('s') for v in vals})==1)
    if cnt:_need(Fraction(cnt[1])==len(vals));used.append(cnt.span(1))
    _need(_all_read(s,used))
    tot=sum(Fraction(v[1]) for v in vals)
    return _out('average','sum / count','('+'+'.join(v[1] for v in vals)+f')/{len(vals)}',tot/len(vals),(vals[0][2] or ''),[Fraction(v[1]) for v in vals],query,whole=False)

def _en_shape(s,query):
    area=bool(re.search(r'\barea\b',s));peri=bool(re.search(r'\bperimeter\b',s))
    if not (area or peri) or area and peri:return None
    if re.search(r'\bsquare\b',s):
        a=re.search(r'(?:side|sides)\s+(?:of\s+|that are\s+|is\s+|are\s+)?(\d+(?:\.\d+)?)\s*(cm|m|km|mm|inches|feet)',s)
        _need(a and _all_read(s,[a.span(1)]))
        x=Fraction(a[1])
        return _out('area' if area else 'perimeter','side*side' if area else 'side*4',f'{a[1]}*{a[1]}' if area else f'{a[1]}*4',x*x if area else 4*x,a[2],[x],query,whole=False)
    if re.search(r'\brectangle\b',s):
        a=re.search(r'(\d+(?:\.\d+)?)\s*(cm|m|km|mm)\s+long',s) or re.search(r'length\s+(?:of\s+|is\s+)?(\d+(?:\.\d+)?)\s*(cm|m|km|mm)',s)
        b=re.search(r'(\d+(?:\.\d+)?)\s*(cm|m|km|mm)\s+wide',s) or re.search(r'width\s+(?:of\s+|is\s+)?(\d+(?:\.\d+)?)\s*(cm|m|km|mm)',s)
        _need(a and b and a[2]==b[2] and _all_read(s,[a.span(1),b.span(1)]))
        x,y=Fraction(a[1]),Fraction(b[1])
        return _out('area' if area else 'perimeter','length*width' if area else '(length+width)*2',f'{a[1]}*{b[1]}' if area else f'({a[1]}+{b[1]})*2',x*y if area else 2*(x+y),a[2],[x,y],query,whole=False)
    return None

def _en_lcm_gcd(s,query):
    m=re.search(r'(least|lowest|smallest) common multiple|(greatest|highest|largest) common (?:divisor|factor)',s)
    if not m:return None
    ns=_nums(s);_need(2<=len(ns)<=4 and all(x.group().isdigit() and int(x.group())>0 for x in ns))
    _need(re.fullmatch(r'\s*(?:what is |find )?the (?:least|lowest|smallest|greatest|highest|largest) common (?:multiple|divisor|factor) of '+r'(?:\s*,\s*|\s+and\s+)'.join(r'\d+' for _ in ns)+r'\s*\??\s*',s))
    v=[int(x.group()) for x in ns]
    if m[1]:return _out('lcm','least common multiple',f'lcm({",".join(map(str,v))})',reduce(lambda a,b:a*b//math.gcd(a,b),v),'',v,query)
    return _out('gcd','greatest common divisor',f'gcd({",".join(map(str,v))})',reduce(math.gcd,v),'',v,query)

def _en_groups(s,query):
    m=re.search(r'there are (\d+) (rows|bags|boxes|tables|shelves|plates|baskets|teams|groups) (?:of [a-z]+ )?with (\d+) ([a-z]+) (?:in|on) each\b',s) or \
      re.search(r'(\d+) (rows|bags|boxes|tables|shelves|plates|baskets|teams|groups) (?:of [a-z]+ )?with (\d+) ([a-z]+) (?:in|on) each\b',s)
    if m and re.search(r'how many '+re.escape(m[4])+r'\b',s):
        _need(_all_read(s,[m.span(1),m.span(3)]))
        return _out('each_x_groups','groups*each',f'{m[1]}*{m[3]}',Fraction(m[1])*Fraction(m[3]),m[4],[Fraction(m[1]),Fraction(m[3])],query)
    m=re.search(r'an? ([a-z]+) holds (\d+) ([a-z]+)\. how many \3 (?:are|fit|can fit|are there) in (\d+) \1(?:e?s)?\b',s)
    if m:
        _need(_all_read(s,[m.span(2),m.span(4)]))
        return _out('each_x_groups','per container*containers',f'{m[2]}*{m[4]}',Fraction(m[2])*Fraction(m[4]),m[3],[Fraction(m[2]),Fraction(m[4])],query)
    return None

def _en_prices(s,query):
    m=re.search(r'\b([a-z]+?)s? cost (\d+(?:\.\d+)?) (dollars?|cents?|yen) each\. how much (?:do|does|will|would) (\d+) \1s? cost\b',s)
    if m:
        _need(_all_read(s,[m.span(2),m.span(4)]))
        return _out('unit_price','price*count',f'{m[2]}*{m[4]}',Fraction(m[2])*Fraction(m[4]),m[3],[Fraction(m[2]),Fraction(m[4])],query,whole=False)
    m=re.search(r'\b(?:a|an|the) ([a-z]+) costs (\d+(?:\.\d+)?) (dollars?|cents?)\. it is (?:discounted|reduced|marked down) by (\d+(?:\.\d+)?) ?(?:percent|%)\. how much does it cost now\b',s)
    if m:
        _need(_all_read(s,[m.span(2),m.span(4)]))
        p,d=Fraction(m[2]),Fraction(m[4]);_need(0<=d<=100)
        return _out('discount','price*(100-percent)/100',f'{m[2]}*(100-{m[4]})/100',p*(100-d)/100,m[3],[p,d],query,whole=False)
    return None

def _en_budget(s,query):
    """you have 20 dollars. you buy 3 books for 5 dollars each. how much money is left?"""
    m=re.search(r'\b(?:you|i|[a-z]+) (?:have|has|had) (\d+(?:\.\d+)?) (dollars?|cents?|yen)\. (?:you|i|he|she|[a-z]+) (?:buys?|bought) (\d+) ([a-z]+) (?:for|at) (\d+(?:\.\d+)?) (dollars?|cents?|yen) each\. how much (?:money )?(?:is|was|will be) left\b',s)
    if not m:return None
    _need(m[2].rstrip('s')==m[6].rstrip('s') and _all_read(s,[m.span(1),m.span(3),m.span(5)]))
    a,n,c=Fraction(m[1]),Fraction(m[3]),Fraction(m[5])
    return _out('budget','money-count*price',f'{m[1]}-{m[3]}*{m[5]}',a-n*c,m[2],[a,n,c],query,whole=False)

def _en_teams(s,query):
    """there are 45 students. they form teams of 5. how many teams are there?"""
    m=re.search(r'there are (\d+) ([a-z]+)\. (?:they|the \2) (?:form|make|are put into|are divided into|split into|are split into) (teams|groups|rows|lines|pairs) of (\d+)(?: each)?\. how many \3 (?:are there|can they (?:form|make)|will there be|do they (?:form|make))\b',s)
    if not m:return None
    _need(_all_read(s,[m.span(1),m.span(4)]))
    n,k=Fraction(m[1]),Fraction(m[4]);_need(k!=0 and (n/k).denominator==1)
    return _out('equal_groups','total/size',f'{m[1]}/{m[4]}',n/k,m[3],[n,k],query)

def _en_compare(s,query):
    """tom has 18 cards. jim has 7 more cards than tom. how many cards does jim have? (and the other direction)"""
    m=re.search(r'\b([a-z]+) (?:has|have|had) (\d+(?:\.\d+)?) (more|fewer|less) (?:([a-z]+) )?than ([a-z]+)\b',s)
    if not m:return None
    own=[x for x in re.finditer(r'\b([a-z]+) (?:has|have|had) (\d+(?:\.\d+)?) ([a-z]+)\b',s) if x.start()!=m.start()]
    ask=re.search(r'how many ([a-z]+) (?:does|do|did) ([a-z]+) (?:have|has|had)\b',s)
    _need(len(own)==1 and ask and _all_read(s,[m.span(2),own[0].span(2)]))
    nouns={x.rstrip('s') for x in (m[4],own[0][3],ask[1]) if x}
    _need(len(nouns)==1)
    who,than,owner,asked=m[1],m[5],own[0][1],ask[2]
    _need(asked not in ('he','she','they','it') and who!=than)
    d,b=Fraction(m[2]),Fraction(own[0][2]);sign=1 if m[3]=='more' else -1
    if asked==who and owner==than:v=b+sign*d;expr=f'{own[0][2]}{"+" if sign>0 else "-"}{m[2]}'
    elif asked==than and owner==who:v=b-sign*d;expr=f'{own[0][2]}{"-" if sign>0 else "+"}{m[2]}'
    else:raise _No()
    return _out('compare','base +/- difference',expr,v,'',[b,d],query)

def _en_number(s,query):
    """i think of a number. if i add 9, i get 30. what is the number?"""
    if not re.search(r'\b(?:i|you|she|he|[a-z]+) (?:think|thinks|thought) of a number\b',s) or not re.search(r'what (?:is|was) (?:the|my|her|his) number\b',s):return None
    m=re.search(r'if (?:i|you|she|he|we) (add|subtract|take away|multiply it by|multiply by|divide it by|divide by) (\d+)(?:,| to it| from it)?,? (?:i|you|she|he|we) get (\d+)\b',s)
    _need(m and _all_read(s,[m.span(2),m.span(3)]))
    k,r=Fraction(m[2]),Fraction(m[3]);op=m[1]
    if op=='add':return _out('number_puzzle','result-added',f'{m[3]}-{m[2]}',r-k,'',[k,r],query)
    if op in ('subtract','take away'):return _out('number_puzzle','result+subtracted',f'{m[3]}+{m[2]}',r+k,'',[k,r],query)
    _need(k!=0)
    if op.startswith('multiply'):return _out('number_puzzle','result/multiplier',f'{m[3]}/{m[2]}',r/k,'',[k,r],query)
    return _out('number_puzzle','result*divisor',f'{m[3]}*{m[2]}',r*k,'',[k,r],query)

def _en_speed(s,query):
    m=re.search(r'travels (\d+(?:\.\d+)?) (km|miles|kilometers|meters) in (\d+(?:\.\d+)?) (hours?|minutes?)\. what is (?:its|the|her|his) (?:average )?speed',s)
    if not m:return None
    _need(_all_read(s,[m.span(1),m.span(3)]))
    d,h=Fraction(m[1]),Fraction(m[3]);_need(h!=0)
    return _out('speed','distance/time',f'{m[1]}/{m[3]}',d/h,f'{m[2]} per {m[4].rstrip("s")}',[d,h],query,whole=False)

# ------------------------------------------------------------------ entry
JA_FAMILIES=(_ja_lcm_gcd,_ja_average,_ja_shape,_ja_part_of,_ja_inverse_group,_ja_each_groups,_ja_rows_formed,_ja_division,_ja_per_period,_ja_complement,_ja_difference,
             _ja_ratio,_ja_times,_ja_speed,_ja_per_one,_ja_budget,_ja_unit_price_pay,_ja_prices,_ja_duration)
EN_FAMILIES=(_en_lcm_gcd,_en_average,_en_shape,_en_groups,_en_teams,_en_prices,_en_budget,_en_speed,_en_compare,_en_number)

def solve(query):
    try:
        t=re.sub(r'\s+','',_norm(query)).replace('㎠','cm2').replace('平方センチメートル','平方cm').replace('平方メートル','平方m')
        t=re.sub(r'(cm|mm|km|m)2(?![\d])',r'平方\1',t)
        if len(t)>300:return None
        if re.search(r'[぀-ヿ一-鿿]',t):
            sents=[x for x in re.findall(r'[^。？?！!]+[。？?！!]?',t) if x.strip('。？?！!')]
            if not sents or not re.search(r'何|いくつ|いくら|求め|次の数|つぎの数|次は|最小公倍数|最大公約数|平均|面積|まわり|おつり|お釣り|合計|代金',sents[-1]):return None
            q=sents[-1]
            if HEDGE.search(t):return None
            if re.search(r'ません|なかった|(?<!足り)ない(?!人|もの)',t) and not re.search(r'足りま|足りな|たりま|たりな|ていない人|でない人',t):return None
            try:r=_sequence(t,q,query)
            except _No:return {'refused':'MATHPROB_SEQUENCE_INCOMPLETE'}
            if r:return r
            for f in JA_FAMILIES:
                try:r=f(t,q,query)
                except _No:return {'refused':'MATHPROB_'+f.__name__.upper()[4:]+'_INCOMPLETE'}
                if r:return r
            return None
        s=unicodedata.normalize('NFKC',str(query)).strip().lower().replace(',',' ,').replace(' ,',',')
        s=re.sub(r'\$\s*(\d)',r'\1 dollars ',s);s=re.sub(r'\s+',' ',s).strip()
        if len(s)>400 or HEDGE.search(s) or re.search(r"\b(?:not|never)\b|n't\b",s):return None
        try:r=_sequence(s,s,query)
        except _No:return {'refused':'MATHPROB_SEQUENCE_INCOMPLETE'}
        if r:return r
        for f in EN_FAMILIES:
            try:r=f(s,query)
            except _No:return {'refused':'MATHPROB_'+f.__name__.upper()[4:]+'_INCOMPLETE'}
            if r:return r
        return None
    except (ValueError,ZeroDivisionError,OverflowError,IndexError,TypeError,AttributeError):
        return None

import ast as _ast
def evaluate(expr):
    """exact evaluation of a proof expression: + - * / // % and lcm(), gcd(), ceil() on rationals"""
    if not isinstance(expr,str) or len(expr)>240:raise ValueError('MATHPROB_EXPR')
    def rec(n,d=0):
        if d>24:raise ValueError('MATHPROB_EXPR_DEPTH')
        if isinstance(n,_ast.Expression):return rec(n.body,d+1)
        if isinstance(n,_ast.Constant) and type(n.value) in (int,float):return Fraction(str(n.value))
        if isinstance(n,_ast.UnaryOp) and isinstance(n.op,_ast.USub):return -rec(n.operand,d+1)
        if isinstance(n,_ast.BinOp):
            a,b=rec(n.left,d+1),rec(n.right,d+1)
            if isinstance(n.op,_ast.Add):return a+b
            if isinstance(n.op,_ast.Sub):return a-b
            if isinstance(n.op,_ast.Mult):return a*b
            if isinstance(n.op,_ast.Div):return a/b
            if isinstance(n.op,(_ast.FloorDiv,_ast.Mod)):
                if a.denominator!=1 or b.denominator!=1 or b==0:raise ValueError('MATHPROB_INTEGER_DIVISION')
                return Fraction(int(a)//int(b) if isinstance(n.op,_ast.FloorDiv) else int(a)%int(b))
        if isinstance(n,_ast.Call) and isinstance(n.func,_ast.Name) and n.func.id in ('lcm','gcd','ceil') and not n.keywords:
            args=[rec(x,d+1) for x in n.args]
            if n.func.id=='ceil' and len(args)==1:return Fraction(math.ceil(args[0]))
            if n.func.id in ('lcm','gcd') and 2<=len(args)<=4 and all(x.denominator==1 and x>0 for x in args):
                v=[int(x) for x in args];return Fraction(reduce(lambda a,b:a*b//math.gcd(a,b),v) if n.func.id=='lcm' else reduce(math.gcd,v))
        raise ValueError('MATHPROB_EXPR_NODE')
    return rec(_ast.parse(expr,mode='eval'))

def check(proof,answer):
    """proofs.check hook: re-read the question (family, expression, numbers and answer must all repeat), then
    evaluate the expression exactly and compare it with the answer"""
    r=solve(proof.get('source_query',''))
    if not r or 'answer' not in r:return False
    p=r['proof']
    if not all(p.get(k)==proof.get(k) for k in ('family','expression','given','unit','answer')) or r['answer']!=str(answer):return False
    try:return _fmt(evaluate(p['expression']))==str(answer)
    except (ValueError,SyntaxError,ZeroDivisionError,OverflowError):return False
