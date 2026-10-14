"""generation 4: TUKUYO's own reader of Japanese story problems (v1022.8.0). No LLM.

read(text) -> {'spec': FPL reading} | {'spec': None, 'reason': ...}

It reads the everyday forms of a primary school, each by a small pattern over the sentences, and writes them in the
formal problem language (fpl.py), so the checker (check.py) verifies every reading on its own: every number of the
text bound by a fact whose span holds it or declared unused, units that agree, one answer forced.

  remaining   a holding, then things taken away or added (食べました、もらいました、とんでいき、もどってき、...)
  combine     two or more amounts of one kind, asked together (全部で、あわせて)
  compare     one amount given and another N more or fewer than it (より…多い/少ない/年上/年下/高い), or two given
              and asked how many more (何…多いですか)
  groups      N in each of M (ずつ入っています、N本入りの…M箱、1列にN本ずつM列)
  share       N shared among M (M人で分けると、1人何…) or put in groups of K (Kこずつ…何ふくろ、何人に配れますか)
  price       1つP円のものをN買う; several things; paying with a bill and the change (おつり)
  rate        speed (時速), so much each day for D days, a proportion (100kmで6L…300kmでは)
  convert     2mは何cm, 1時間40分は何分, 1週間は7日…5週間は
  part        a fraction or a share of a whole (そのうち半分、3分の1、2/5、25%引き、3倍)
  rest        the rest of a whole (N人のうちK人が…、…でない人は; 男の子/女の子)
  inverse     the start or the change not given but the result (何こか持っていました…のこりが9こ…はじめに)
  geometry    the area of a rectangle, the perimeter of a square

It reads only what it can account for. An amount said without a number (いくつか、何こか、たくさん) is not guessed:
a problem that needs it is not read (an inverse problem asks for it, which is another thing).
"""
from __future__ import annotations
import re
from fractions import Fraction
from . import numbers as N
from .fpl import SCHEMA,fmt

READER='tukuyo.g4.reader_ja/1'
# the counters it reads, and one way to write each (the unit of the reading)
_C={'個':'個','こ':'個','コ':'個','枚':'枚','まい':'枚','本':'本','ほん':'本','ぼん':'本','ぽん':'本','人':'人','にん':'人','冊':'冊','さつ':'冊',
    '匹':'匹','ひき':'匹','びき':'匹','ぴき':'匹','頭':'頭','とう':'頭','羽':'羽','わ':'羽','台':'台','だい':'台','箱':'箱','はこ':'箱',
    '袋':'袋','ふくろ':'袋','パック':'パック','切れ':'切れ','きれ':'切れ','円':'円','才':'才','歳':'才','ページ':'ページ','点':'点','回':'回',
    '列':'列','れつ':'列','段':'段','だん':'段','階':'階','かい':'階','部屋':'部屋','へや':'部屋','脚':'脚','きゃく':'脚','席':'席','せき':'席',
    '鉢':'鉢','はち':'鉢','組':'組','くみ':'組','足':'足','そく':'足','杯':'杯','はい':'杯','粒':'粒','つぶ':'粒','往復':'往復','問':'問',
    'kg':'kg','km':'km','cm':'cm','mm':'mm','mL':'mL','ml':'mL','dL':'dL','dl':'dL','g':'g','m':'m','L':'L','t':'t','トン':'t','度':'度',
    '日間':'日','日':'日','週間':'週','週':'週','か月':'か月','ヶ月':'か月','カ月':'か月','時間':'時間','分間':'分','分':'分','秒':'秒','年':'年'}
CNT='|'.join(sorted(map(re.escape,_C),key=len,reverse=True))
# a number and its counter ('3分の1' is a fraction, not 3 minutes; 'g' and 'm' and 't' only as units, not in words)
AMT=re.compile(rf'(?<![\d./])(\d+(?:\.\d+)?)\s*({CNT})(?!の\d)(?![A-Za-z])(?!目)')   # '1回目' is an ordinal
QWORD=re.compile(r'何|いくつ|いくら')
UNKNOWN=re.compile(r'いくつか|いくらか|何(?:' + CNT + r')か|何人か|何こか|何個か|何枚か|何本か|何冊か|たくさん|いくらかの|少し|すこし')
# an event the story does not say happened: not done (食べていません、歩きません、買わなかった、食べずに), only planned or
# wished (予定、つもり、明日、もし…、食べたい、来たい), or only heard or seen to be likely (と言いました、たそうです、ようです);
# or what should or almost happened (食べたはずです、もう少しで…ところでした); 少ない and 足りません are not denials, the もし of
# アルバイトもしています is not a supposition, and 冷たい is not a wish
NOT_DONE=re.compile(r'(?<!少)(?<!すく)(?<!足り)(?<!たり)(?:ませんでした|ません|なかった|なくて|ないで|ずに|ない(?=[。、]|です|$|人|もの|ので|から|けれど|が|と))|'
                    r'予定|つもり|明日|あした|来週|来月|来年|これから|(?:^|、)\s*もし|(?:[きぎしちにびみりいえけげせてねべめれ]|(?![冷重平眠煙])[一-龯])たい(?=[。、]|です|$|と|の)|'
                    r'かもしれ|らしい|だろう|そうです|そうだ(?!ん)|ようです|ようだ|みたいです|と言(?:い|っ|わ)|と聞|はず|べき|ところでした|ところだった|もう少しで|あやうく')
# the same asked of an event in the question (3こ食べなかったら、のこりは); a negated kind asked for (読んでいないページは) is read
QNOT=re.compile(r'(?:^|、)\s*もし|予定|つもり|明日|あした|来週|なかったら|なければ|ないなら|ずに|かもしれ|と言(?:い|っ|わ)|(?<!足り)ません(?:でした)?か|たい(?:です|の)?か')
# an amount not said exactly (3こぐらい、60Lくらいの、約20人、10こ以上、5〜6本、45こあまり、12こ近く、30人前後、15本より多く);
# どのくらい is a question, and より of a comparison (兄より6本少なく) has no amount before it. Remainders
# (5こあまりました) are not read by these forms either
HEDGED=re.compile(r'(?<!どの)(?<!どれ)(?:ぐらい|くらい)|\d\s*(?:' + CNT + r')\s*(?:あまり|余り|近く|前後|強(?![いくめ])|弱(?![いくめ])|超|より(?:多|少))|(?<!先)ほど|程度|ほとんど|約\s*\d|およそ|だいたい|大体|ほぼ|以上|以下|未満|少なくとも|最大|最低|せいぜい|たぶん|多分|'
                  r'[〜~～]|または|もしくは|不明|かどうか')
# what no route answers, the v1022 core included (api.solve): an amount said only roughly with its number (80円あまりの、
# 3本近く、30人前後、15本より多く), which the core's own list (ぐらい、約、以上 …) does not have, and a question about a wish
# (何こ買いたいですか). A remainder (5こあまりました、あまり、…、あまりは何こ) is another use of the word
ROUGH=re.compile(r'\d\s*(?:' + CNT + r')\s*(?:(?:あまり|余り)(?![ま、。]|$)|近く|前後|強(?![いくめ])|弱(?![いくめ])|超|より(?:多|少))|たい(?:です|の)?か[。？?]?$')
# a wish or a plan in the story and a question about what was done (6週間ちょ金したいです。全部で何円ちょ金しましたか): the
# act did not happen, so what was done is not told. 買いたいです。代金は何円ですか asks the price of the wish, and is read by
# the core
WISHED=re.compile(r'(?:[きぎしちにびみりいえけげせてねべめれ]|(?![冷重平眠煙])[一-龯])たい(?:です|と思)|予定|つもり')
ASKS_DONE=re.compile(r'(?:ました|でした|た)か[。？?]?$')
# round 10 (found on the round's held-out set after its one measurement): きました is 来ました only after て/で or a particle
# (とんできました, 3人が きました); '5km歩きました' (walked) is no increase. It read 12 + 5 for 'ゴールまであと何km'.
# What there is now, after an amount added to what was there before, when nothing says what was there before, has no
# answer (the v1022 core answered 4 to 'ふでばこにえんぴつを4本足しました。ふでばこのえんぴつは何本になりましたか。'; the English
# 'N more' with no start). api.solve asks this before every route
ADDED_TO=r'(?:足し|たし|加え|くわえ|増え|ふえ|もらい|もらっ|貰い)'
NOW_Q=re.compile(r'に\s*なり(?:ました|ます)か|今|いま')
def start_not_given(text):
    sents=_sents(_norm(text))
    if len(sents)<2 or not NOW_Q.search(sents[-1]):return False
    stm=sents[:-1];a=[(s,x) for s in stm for x in _amts(s,0)]
    if len(a)!=1 or any(re.search(STATE,s) or re.search(r'はじめ|最初|もともと|もとは',s) for s in stm):return False
    s,x=a[0];return bool(re.search(ADDED_TO,s[x.e:x.e+16]))
def wished_then_asked_done(text):
    sents=_sents(_norm(text))
    return len(sents)>=2 and any(WISHED.search(x) for x in sents[:-1]) and bool(ASKS_DONE.search(sents[-1]))
SENT=re.compile(r'[^。？?！!]+[。？?！!]?')
MINUS=r'(?:食べ|たべ|使い|使っ|つかい|つかっ|あげ|上げ(?!て?い?ます?。?$)|売り|売れ|うり|うれ|なくし|無くし|落とし|おとし|とんでいき|とんで行|飛んでいき|飛んで行|' \
      r'飛んでいっ|とんでいっ|にげ|逃げ|降り|おり|われ|割れ|こわれ|壊れ|ぬき|抜き|出し|だし|配り|くばり|わたし|渡し|すて|捨て|へり|減り|へっ|減っ|' \
      r'取り出し|とりだし|返し|かえし|貸し|かし|散り|ちり|帰り|かえり|引い|ひい|ちぎっ|おろし|下ろし|切り取っ|あげ)'
PLUS=r'(?:もらい|もらっ|貰い|買い|買っ|かい|かっ|拾い|拾っ|ひろい|ひろっ|ふえ|増え|もどってき|戻ってき|来|(?<=[てでがにもはへ、 ])き(?=て|ました)|乗り|のり|入り|はいり|' \
     r'足し|たし|のび|伸び|上がり|あがり|つみ|摘み|作り|作っ|つくり|つくっ|焼き|焼い|やき|やい|生まれ|うまれ|咲き|さき|集め|あつめ|見つけ|みつけ|' \
     r'借り|かり|加え|くわえ|入れ|いれ|育ち|そだち|植え|うえ|とれ|取れ|当たっ|ため|貯め)'
STATE=r'(?:あります|ありました|あった|います|いました|持っています|持っていました|もっています|もっていました|とまっています|とまっていました|' \
      r'入っています|入っていました|はいっています|はいっていました|乗っています|乗っていました|のっています|のっていました|さいています|' \
      r'さいていました|咲いています|残っています|のこっています|います|でした|です|かっています|飼っています|あり)'


MEASURES={'kg','g','t','km','m','cm','mm','L','mL','dL','時間','分','秒','日','週','か月','年','度'}
def _whole(u):
    """is a quantity in this unit counted one by one (people, cards, yen), so a share of it must be whole?"""
    return u.split('/')[0] not in MEASURES


class _B:
    """a reading under way: quantities, facts, numbers left out with a reason"""
    def __init__(s,text):s.text=text;s.q={};s.f=[];s.unused=[]
    def qty(s,name,unit,integer=True,signed=False):
        if name not in s.q:s.q[name]={'name':name,'unit':unit,'integer':integer,'signed':signed,'about':''}
        return name
    def bind(s,name,unit,value,span,integer=True):
        s.qty(name,unit,integer);s.f.append({'eq':f'{name} = {fmt(value)}','span':span});return name
    def rel(s,name,unit,expr,span,integer=True,signed=False):
        s.qty(name,unit,integer,signed);s.f.append({'eq':f'{name} = {expr}','span':span});return name
    def known(s,name,unit,value,said):
        s.qty(name,unit,True);s.f.append({'eq':f'{name} = {fmt(value)}','known':said});return name
    def skip(s,raw,why):s.unused.append({'raw':raw,'why':why})
    def spec(s,ask,form):
        bound={f['eq'].split('=')[1].strip() for f in s.f if 'span' in f}
        for m in re.finditer(r'(?<![\d.])(\d+)\s*月(?![間曜])',s.text):
            if m.group(1) not in bound and not any(u['raw']==m.group(1) for u in s.unused):s.skip(m.group(1),'日付の月 (量ではない)')
        for m in re.finditer(r'(?<![\d.])1\s*(?:'+CNT+r')(?:の[^\s、。]{1,6}?)?(?:分|あたり|当たり)?(?:は|に|が)?\s*(?:何|いくら)',s.text):
            if not any(u['raw']=='1' for u in s.unused):s.skip('1','「1…何」の1 (問いの単位)')
        t=s.text.translate(N._FW);ones=[n for n in N.find(t) if n.raw=='1' and not N.optional(n,t)]
        bases={m.start() for m in re.finditer(r'(?<![\d.])1(?=\s*(?:'+CNT+r')\s*(?:\d|は\s*\d|で\s*\d))',t)}
        binds_one=any(f['eq'].split('=')[1].strip()=='1' for f in s.f if 'span' in f)
        if ones and not any(u['raw']=='1' for u in s.unused) and all(n.start in bases for n in ones if not binds_one):
            if any(n.start in bases for n in ones):s.skip('1','1つあたりの量の1 (割合のもと)')
        return {'schema':SCHEMA,'lang':'ja','text':s.text,'quantities':list(s.q.values()),'facts':s.f,'ask':ask,
                'answer_unit':s.q[ask]['unit'],'unused':s.unused,'reader':f'{READER}:{form}'}


class _Amt:
    __slots__=('v','c','s','e','raw','sent','k')
    def __init__(s,m,sent,k):
        s.v=Fraction(m.group(1));s.c=_C[m.group(2)];s.s=m.start();s.e=m.end();s.raw=m.group(1);s.sent=sent;s.k=k
    def after(s,n=12):return s.sent[s.e:s.e+n]
    def before(s,n=12):return s.sent[max(0,s.s-n):s.s]


def _norm(text):
    return text.translate(N._FW).replace('ｍ','m').replace('ｋ','k').replace('ｃ','c').replace('Ｌ','L').replace('ｇ','g').strip()


def _sents(t):
    return [x.strip() for x in SENT.findall(t) if x.strip()]


def _amts(sent,k):
    out=[]
    for m in AMT.finditer(sent):
        # a unit letter inside a word is not a unit ('cm²' is fine, 'km' yes, 'g' after a letter no)
        if m.group(2) in ('g','m','t','L') and re.match(r'[A-Za-z]',sent[m.end():m.end()+1] or ' '):continue
        out.append(_Amt(m,sent,k))
    return out


def _question(sents):
    if not sents or not QWORD.search(sents[-1]):return None
    return sents[-1]


def _ask_unit(q):
    m=re.search(rf'何\s*({CNT})',q)
    if m:return _C[m.group(1)]
    if 'いくら' in q:return '円'
    m=re.search(r'時速何\s*(km|m)',q)
    if m:return m.group(1)
    return None


KINDS=[set('りんご みかん バナナ いちご ぶどう メロン なし もも かき すいか レモン オレンジ さくらんぼ'.split()),
       set('ねこ 犬 いぬ うさぎ 牛 うし 羊 ひつじ ぶた 馬 うま にわとり 鳥 とり すずめ アヒル ハト 魚 さかな'.split()),
       set('えんぴつ ペン ノート 消しゴム けしゴム 色紙 シール カード 本 ボール'.split()),
       set('あめ ガム クッキー ケーキ チョコレート せんべい ドーナツ プリン アイス マフィン パン おにぎり'.split()),
       set('男の子 女の子 男子 女子 大人 子ども'.split())]
def _another_thing(stm,q):
    """the question asks about a thing of the same kind as, but other than, the things the story tells of"""
    m=re.match(r'\s*(?:[^\s、。]*?の)?([^\s、。のは]+?)(?:は|が)',q)
    if not m:return False
    asked=m.group(1);s=''.join(stm)
    if asked in s:return False
    return any(asked in k and any(w in s for w in k if w!=asked) for k in KINDS)


def read(text):
    t=_norm(text);sents=_sents(t)
    if len(sents)<1:return {'spec':None,'reason':'JA:EMPTY'}
    q=_question(sents)
    if q is None:return {'spec':None,'reason':'JA:NO_QUESTION'}
    stm=sents[:-1]
    if _another_thing(stm,q):return {'spec':None,'reason':'JA:ASKS_ANOTHER_THING'}
    if any(NOT_DONE.search(s) for s in stm):return {'spec':None,'reason':'JA:EVENT_NOT_SAID_AS_DONE'}
    if any(HEDGED.search(s) for s in sents):return {'spec':None,'reason':'JA:AMOUNT_NOT_EXACT'}
    if QNOT.search(q):return {'spec':None,'reason':'JA:EVENT_NOT_SAID_AS_DONE'}
    from . import reader_ja_more
    from .api import evaluate
    failed=None
    for form in (_convert,_geometry,_inverse,_unknown_guard,_fraction,_rate,_price,_share,_groups,_compare,_rest,_combine,_remaining)+reader_ja_more.FORMS:
        try:r=form(t,stm,q)
        except (ValueError,KeyError,IndexError,ZeroDivisionError,TypeError,AttributeError,re.error):r=None
        if r=='STOP':return {'spec':None,'reason':'JA:AMOUNT_NOT_GIVEN'}
        if r is not None:
            r['text']=text
            # round 10: a reading the checker does not pass lets the next form try ('2人の本は合わせて': the 2 is the
            # number of people, which the comparing form left unbound)
            if evaluate(r,'own')['ok']:return {'spec':r}
            failed=failed or r
    return {'spec':failed} if failed else {'spec':None,'reason':'JA:NOT_READ'}


# ----------------------------------------------------------------------------- the forms
def _unknown_guard(t,stm,q):
    """an amount said without a number, which no form above asked for: not guessed"""
    if any(UNKNOWN.search(s) for s in stm):return 'STOP'
    return None


def _one(s,c=None):
    a=[x for x in _amts(s,0) if c is None or x.c==c]
    return a[0] if len(a)==1 else None


CONVERT={('m','cm'):(100,'1 m = 100 cm'),('km','m'):(1000,'1 km = 1000 m'),('cm','mm'):(10,'1 cm = 10 mm'),('m','mm'):(1000,'1 m = 1000 mm'),
         ('kg','g'):(1000,'1 kg = 1000 g'),('L','mL'):(1000,'1 L = 1000 mL'),('L','dL'):(10,'1 L = 10 dL'),('t','kg'):(1000,'1 t = 1000 kg'),
         ('時間','分'):(60,'1時間 = 60分'),('分','秒'):(60,'1分 = 60秒'),('週','日'):(7,'1週間 = 7日'),('年','か月'):(12,'1年 = 12か月')}


def _convert(t,stm,q):
    b=_B(t)
    if not stm:
        # 2mは何cmですか / 1時間40分は何分ですか
        m=re.fullmatch(rf'(\d+(?:\.\d+)?)\s*({CNT})(?:(\d+)\s*({CNT}))?は何\s*({CNT})(?:ですか|でしょうか)?[。？?]?',q)
        if not m:return None
        u1,u2=_C[m.group(2)],_C[m.group(5)]
        if m.group(3):
            u3=_C[m.group(4)]
            if u3!=u2 or (u1,u2) not in CONVERT:return None
            f,said=CONVERT[(u1,u2)]
            a=b.bind('big',u1,Fraction(m.group(1)),q);c=b.bind('small',u2,Fraction(m.group(3)),q);k=b.known('per',f'{u2}/{u1}',f,said)
            b.rel('total',u2,f'{a} * {k} + {c}',q);return b.spec('total','convert')
        if (u1,u2) not in CONVERT:return None
        f,said=CONVERT[(u1,u2)]
        a=b.bind('given',u1,Fraction(m.group(1)),q,integer=False);k=b.known('per',f'{u2}/{u1}',f,said)
        b.rel('total',u2,f'{a} * {k}',q,integer=False);return b.spec('total','convert')
    if len(stm)==1:
        # 映画は1時間40分でした。何分ですか / 1週間は7日です。5週間は何日ですか / 1年は365日です。2年は何日ですか
        m=re.search(rf'(\d+)\s*時間\s*(\d+)\s*分(?:間)?(?:でした|です|かかりました)',stm[0])
        if m and re.fullmatch(r'(?:それは)?何分(?:間)?(?:ですか|でしたか|かかりましたか)[。？?]?',q):
            a=b.bind('hours','時間',Fraction(m.group(1)),stm[0]);c=b.bind('minutes','分',Fraction(m.group(2)),stm[0]);k=b.known('per','分/時間',60,'1時間 = 60分')
            b.rel('total','分',f'{a} * {k} + {c}',q);return b.spec('total','convert')
        m=re.fullmatch(rf'1\s*({CNT})は(\d+)\s*({CNT})です[。]?',stm[0]);n=re.fullmatch(rf'(\d+)\s*({CNT})は何\s*({CNT})(?:ですか)?[。？?]?',q)
        if m and n and _C[m.group(1)]==_C[n.group(2)] and _C[m.group(3)]==_C[n.group(3)]:
            u1,u2=_C[m.group(1)],_C[m.group(3)]
            r=b.bind('per',f'{u2}/{u1}',Fraction(m.group(2)),stm[0]);c=b.bind('count',u1,Fraction(n.group(1)),q)
            b.rel('total',u2,f'{r} * {c}',q);return b.spec('total','convert')
    return None


def _geometry(t,stm,q):
    b=_B(t);s=''.join(stm)+q
    m=re.search(r'(?:たて|縦)\s*(\d+(?:\.\d+)?)\s*(cm|m|km|mm)[、,]\s*(?:よこ|横)\s*(\d+(?:\.\d+)?)\s*(cm|m|km|mm)の長方形の面積は何\s*(cm|m|km|mm)(?:²|2|\^2)',s)
    if m and m.group(2)==m.group(4)==m.group(5):
        u=m.group(2);sp=m.group(0)
        a=b.bind('length',u,Fraction(m.group(1)),sp,integer=False);c=b.bind('width',u,Fraction(m.group(3)),sp,integer=False)
        b.rel('area',f'{u}^2',f'{a} * {c}',sp,integer=False);b.skip('2','平方の2 (面積の単位)') if re.search(r'(cm|m|km|mm)2',s) else None
        return b.spec('area','geometry')
    m=re.search(r'1\s*辺が?\s*(\d+(?:\.\d+)?)\s*(cm|m|km|mm)の正方形の(?:まわり|周り|周)の長さは何\s*(cm|m|km|mm)',s)
    if m and m.group(2)==m.group(3):
        u=m.group(2);sp=m.group(0)
        a=b.bind('side',u,Fraction(m.group(1)),sp,integer=False);k=b.known('sides','1',4,'正方形の辺は4本')
        if re.search(r'(?<![\d.])1\s*辺',s):b.skip('1','1辺: 辺の数え方 (量ではない)')
        b.rel('perimeter',u,f'{k} * {a}',sp,integer=False);return b.spec('perimeter','geometry')
    return None


def _inverse(t,stm,q):
    b=_B(t);s=''.join(stm)
    # 何こか持っていました。6こあげたので、のこりが9こになりました。はじめに何こ
    if re.search(r'はじめ|最初|もともと|初め',q) and re.search(rf'何\s*(?:{CNT})か',s):
        m=re.search(rf'(\d+)\s*({CNT})\s*{MINUS}[^。]*?(?:のこり|残り)が?\s*(\d+)\s*({CNT})に?なり',s)
        if m and _C[m.group(2)]==_C[m.group(4)]==_ask_unit(q):
            u=_C[m.group(2)];sp=m.group(0)
            g=b.bind('gone',u,Fraction(m.group(1)),sp);r=b.bind('left',u,Fraction(m.group(3)),sp)
            b.rel('start',u,f'{g} + {r}',sp);return b.spec('start','inverse')
        m=re.search(rf'(\d+)\s*({CNT})\s*{PLUS}[^。]*?(\d+)\s*({CNT})に?なり',s)
        if m and _C[m.group(2)]==_C[m.group(4)]==_ask_unit(q):
            u=_C[m.group(2)];sp=m.group(0)
            g=b.bind('got',u,Fraction(m.group(1)),sp);r=b.bind('now',u,Fraction(m.group(3)),sp)
            b.rel('start',u,f'{r} - {g}',sp);return b.spec('start','inverse')
        return None
    # 7こ持っていました。何こかもらったので16こになりました。何こもらいましたか
    if re.search(rf'何\s*(?:{CNT})か\s*{PLUS}',s) and re.search(PLUS,q):
        a=_amts(s,0)
        m=re.search(rf'(\d+)\s*({CNT})に?なり',s)
        if len(a)==2 and m and a[0].c==a[1].c==_ask_unit(q) and a[1].raw==m.group(1):
            u=a[0].c;x=b.bind('before',u,a[0].v,stm[0]);y=b.bind('after',u,a[1].v,m.group(0))
            b.rel('got',u,f'{y} - {x}',m.group(0));return b.spec('got','inverse')
    if re.search(rf'何\s*(?:{CNT})か\s*{MINUS}',s) and re.search(MINUS,q):
        a=_amts(s,0)
        m=re.search(rf'(\d+)\s*({CNT})に?なり|(?:のこり|残り)が?\s*(\d+)\s*({CNT})',s)
        if len(a)==2 and m and a[0].c==a[1].c==_ask_unit(q):
            u=a[0].c;x=b.bind('before',u,a[0].v,stm[0]);y=b.bind('after',u,a[1].v,m.group(0))
            b.rel('gone',u,f'{x} - {y}',m.group(0));return b.spec('gone','inverse')
    # 3500円持っていました。ゲームを買ったら1200円残りました。ゲームはいくらでしたか
    if len(stm)==2 and 'いくら' in q:
        a=_amts(stm[0],0);c=_amts(stm[1],1)
        if len(a)==1 and len(c)==1 and a[0].c==c[0].c=='円' and re.search(r'持っていました|もっていました',stm[0]) and re.search(r'買っ(?:たら|て)[^。]*(?:残り|のこり)',stm[1]):
            x=b.bind('had','円',a[0].v,stm[0]);y=b.bind('left','円',c[0].v,stm[1]);b.rel('price','円',f'{x} - {y}',stm[1]);return b.spec('price','inverse')
    # 2つの数をたすと50になります。1つは18です。もう1つの数は
    m=re.fullmatch(r'2つの数を(?:たす|足す)と(\d+)になります。',stm[0]) if len(stm)==2 else None
    n=re.fullmatch(r'1つ(?:の数)?は(\d+)です。',stm[1]) if m else None
    if m and n and re.search(r'もう1つ',q):
        a=b.bind('sum','1',Fraction(m.group(1)),stm[0],integer=False);c=b.bind('one','1',Fraction(n.group(1)),stm[1],integer=False)
        b.rel('other','1',f'{a} - {c}',q,integer=False,signed=True);b.skip('2','2つの数の2 (数の個数)');return b.spec('other','inverse')
    return None


FRAC=re.compile(r'(半分|(\d+)分の(\d+)|(\d+)/(\d+))')
def _frac(m):
    if m.group(1)=='半分':return Fraction(1,2),None
    if m.group(2):return Fraction(int(m.group(3)),int(m.group(2))),m.group(0)
    return Fraction(int(m.group(4)),int(m.group(5))),m.group(0)


def _asks_the_part(after,q):
    """the question asks for the part the fraction names: what it is ('半分が男の子です' - 男の子は何人), what it is of
    ('3分の1の水が入っています' - 水は何L), or what was done with it ('2/5を使いました' - 使ったのは何円). Not, for example,
    a whole trip of which a half is one leg ('その半分の日数で済みます…何日間かかるでしょうか')"""
    clause=re.split(r'[、。]',after)[0];topic=_topic(q)
    m=re.match(r'\s*(?:が|は)\s*([^\s、。]+?)(?:です|でした|だ|$)',clause) or re.match(r'\s*の\s*([^\s、。]+?)(?:が|を|は|$)',clause)
    if m and topic and (m.group(1) in topic or topic in m.group(1) or m.group(1)[0]==topic[0] and len(m.group(1))<=2):return True
    v=re.match(r'\s*を\s*([^\s、。]{1,2})',clause)
    return bool(v and re.search(re.escape(v.group(1)[0])+r'[^。]*?(?:た|だ)のは',q))


def _fraction(t,stm,q):
    b=_B(t);s=''.join(stm)
    # N C のうち、半分 / K分のJ が X です。X は何 C  /  N L の…その3分の1の水が入っています  /  N円の2/5を使いました
    a=_amts(s,0);fm=list(FRAC.finditer(s));au=_ask_unit(q)
    if len(a)==1 and len(fm)==1 and not re.search(r'ずつ|より|倍',s) and a[0].c==au and re.search(r'のうち|その|の(?:半分|\d+分の\d+|\d+/\d+)',s) \
            and _asks_the_part(s[fm[0].end():],q):
        f,raw=_frac(fm[0]);sp=s
        w=b.bind('whole',au,a[0].v,sp,integer=False);b.qty('part',au,_whole(au))
        if raw:
            fq=b.bind('share','1',f,sp,integer=False);b.rel('part',au,f'{w} * {fq}',sp,integer=False)
        else:
            fq=b.bind('share','1',Fraction(1,2),sp,integer=False);b.rel('part',au,f'{w} * {fq}',sp,integer=False)   # 半分
        return b.spec('part','part')
    # N円のおもちゃがP%引き(になっています)。いくらで買えますか
    m=re.search(r'(\d+)\s*円の[^。]*?(\d+)\s*%\s*引き',s)
    if m and len(a)==1 and au=='円':
        sp=m.group(0);p=b.bind('price','円',Fraction(m.group(1)),sp,integer=False);r=b.bind('off','1',Fraction(m.group(2))/100,sp,integer=False)
        b.rel('pay','円',f'{p} * (1 - {r})',q,integer=False);return b.spec('pay','part')
    # 月曜日に48個集め、火曜日はその3倍集めました。火曜日は何個
    m=re.search(rf'(\d+)\s*({CNT})[^。]*?その\s*(\d+)\s*倍',s)
    if m and _C[m.group(2)]==au and len(a)==1:
        sp=m.group(0);x=b.bind('first',au,Fraction(m.group(1)),sp);k=b.bind('times','1',Fraction(m.group(3)),sp,integer=False)
        b.rel('second',au,f'{x} * {k}',sp,integer=False);return b.spec('second','part')
    # Xの…はYの2倍です。Yは7さつ持っています。Xは何さつ  /  Xは2400円持っていて、これはYの2倍です。Yは何円
    m=re.search(r'(\d+)\s*倍',s)
    if m and len(a)==1 and a[0].c==au and len(re.findall(r'\d+',s))==2:
        sp=s
        if re.search(r'これは[^。]*の\s*\d+\s*倍|の\s*\d+\s*倍です。[^。]*?(?:何|いくつ)',s) and re.search(r'持っていて、これは',s):
            x=b.bind('known',au,a[0].v,sp,integer=False);k=b.bind('times','1',Fraction(m.group(1)),sp,integer=False)
            b.rel('other',au,f'{x} / {k}',sp,integer=False);return b.spec('other','part')
        if re.search(r'の\s*\d+\s*倍です',stm[0]) and len(stm)==2:
            x=b.bind('known',au,a[0].v,stm[1],integer=False);k=b.bind('times','1',Fraction(m.group(1)),stm[0],integer=False)
            b.rel('other',au,f'{x} * {k}',stm[0],integer=False);return b.spec('other','part')
    return None


def _rate(t,stm,q):
    b=_B(t);s=''.join(stm);whole=s+q;au=_ask_unit(q)
    # 時速40kmで3時間走ると、何km
    m=re.search(r'時速\s*(\d+(?:\.\d+)?)\s*(km|m)で\s*(\d+(?:\.\d+)?)\s*時間',whole)
    if m and au==m.group(2) and len(_amts(whole,0))==2:
        sp=m.group(0);v=b.bind('speed',f'{au}/時間',Fraction(m.group(1)),sp,integer=False);h=b.bind('hours','時間',Fraction(m.group(3)),sp,integer=False)
        b.rel('distance',au,f'{v} * {h}',sp,integer=False);return b.spec('distance','rate')
    # 150kmを3時間で走りました。時速何km
    m=re.search(r'(\d+(?:\.\d+)?)\s*(km|m)を\s*(\d+(?:\.\d+)?)\s*時間で',s)
    if m and re.search(rf'時速何\s*{m.group(2)}',q) and len(_amts(s,0))==2:
        sp=m.group(0);d=b.bind('distance',m.group(2),Fraction(m.group(1)),sp,integer=False);h=b.bind('hours','時間',Fraction(m.group(3)),sp,integer=False)
        b.rel('speed',f'{m.group(2)}/時間',f'{d} / {h}',q,integer=False);return b.spec('speed','rate')
    # 100km走るのにガソリンを6L使う…300km走るには何L
    m=re.search(r'(\d+(?:\.\d+)?)\s*(km|m)\s*(?:走る|進む)のに[^。]*?(\d+(?:\.\d+)?)\s*(L|mL|dL)',s);n=re.search(r'(\d+(?:\.\d+)?)\s*(km|m)\s*(?:走る|進む)には',q)
    if m and n and m.group(2)==n.group(2) and au==m.group(4):
        d1=b.bind('d1',m.group(2),Fraction(m.group(1)),m.group(0),integer=False);f1=b.bind('f1',au,Fraction(m.group(3)),m.group(0),integer=False)
        d2=b.bind('d2',m.group(2),Fraction(n.group(1)),q,integer=False);b.rel('f2',au,f'{f1} * {d2} / {d1}',q,integer=False);return b.spec('f2','rate')
    # 毎朝3kmずつ5日間 / 毎週500円ずつ6週間 / 1時間に2cmずつ…6時間では / 12cmの草が、1週間に3cmずつ4週間のびました
    m=re.search(rf'(?:毎朝|毎日|毎晩|毎週|毎月|毎年|1\s*({CNT})に)\s*(\d+(?:\.\d+)?)\s*({CNT})ずつ',s)
    if m and _C[m.group(3)]==au:
        word=re.match(r'毎(朝|日|晩|週|月|年)',m.group(0))
        per=_C[m.group(1)] if m.group(1) else {'朝':'日','日':'日','晩':'日','週':'週','月':'か月','年':'年'}[word.group(1)]
        rest=whole[:m.start()]+' '*(m.end()-m.start())+whole[m.end():]
        dur=[x for x in _amts(rest,0) if x.c==per]
        start=[x for x in _amts(rest,0) if x.c==au]
        if len(dur)!=1:return None
        sp_r=m.group(0);r=b.bind('per',f'{au}/{per}',Fraction(m.group(2)),sp_r,integer=False)
        dsp=_span_of(whole,dur[0]);d=b.bind('periods',per,dur[0].v,dsp,integer=False)
        if not start:
            if not re.search(r'全部で|何|あわせて|合わせて',q):return None
            b.rel('total',au,f'{r} * {d}',sp_r,integer=False);return b.spec('total','rate')
        if len(start)==1 and re.search(r'今|いま|何',q) and re.search(rf'{PLUS}|のび|伸び',s):
            # round 10 (found on the round's held-out set after its one measurement): the start is an amount said as there
            # (ありました) or the one that grew (12cmの草が…のびました), never one eaten, sold or given ('うさぎが9本食べました'
            # was read as the start of 11本ずつ7列: 86 for 68)
            ss=next((x for x in stm if _span_of(whole,start[0]) in x),'')
            if re.search(MINUS,ss) or not re.search(STATE+r'|のび|伸び',ss):return None
            st=b.bind('start',au,start[0].v,_span_of(whole,start[0]),integer=False)
            b.rel('total',au,f'{st} + {r} * {d}',sp_r,integer=False);return b.spec('total','rate')
        return None
    # 公園まで2km歩き、同じ道を歩いて帰りました。全部で何km
    m=re.search(r'(\d+(?:\.\d+)?)\s*(km|m)\s*(?:歩き|走り|進み|行き|歩いて|走って)、?\s*同じ道を[^。]*?(?:帰り|帰っ|もどり|戻り|もどっ|戻っ)',s)
    if m and au==m.group(2) and len(_amts(s,0))==1 and re.search(r'全部で|あわせて|合わせて|往復',q):
        d=b.bind('one_way',au,Fraction(m.group(1)),m.group(0),integer=False);k=b.known('ways','1',2,'行きと帰りで2回')
        b.rel('total',au,f'{k} * {d}',q,integer=False);return b.spec('total','rate')
    # さくらさんは11才です。6年後には何才
    m=re.search(r'(\d+)\s*(?:才|歳)です',s);n=re.search(r'(\d+)\s*年(後|ご|前|まえ)(?:に|には|は)?\s*何\s*(?:才|歳)',q)
    if m and n and len(_amts(s,0))==1:
        a0=b.bind('age','才',Fraction(m.group(1)),m.group(0));y=b.bind('years','才',Fraction(n.group(1)),n.group(0))
        b.rel('then','才',f"{a0} {'+' if n.group(2) in ('後','ご') else '-'} {y}",q);return b.spec('then','rate')
    # 時給1200円で7時間働きました
    m=re.search(r'時給\s*(\d+)\s*円で\s*(\d+(?:\.\d+)?)\s*時間',s)
    if m and au=='円' and len(_amts(s,0))==2:
        sp=m.group(0);p=b.bind('wage','円/時間',Fraction(m.group(1)),sp,integer=False);h=b.bind('hours','時間',Fraction(m.group(2)),sp,integer=False)
        b.rel('pay','円',f'{p} * {h}',sp,integer=False);return b.spec('pay','rate')
    return None


def _span_of(whole,a):
    """the clause around an amount (between punctuation)"""
    s=whole.rfind('、',0,a.s);s=max(s,whole.rfind('。',0,a.s))+1
    e=min([x for x in (whole.find('、',a.e),whole.find('。',a.e)) if x>=0] or [len(whole)])
    return whole[s:e]


def _price(t,stm,q):
    b=_B(t);s=''.join(stm);whole=s+q;au=_ask_unit(q)
    if au!='円' and not re.search(r'代金|いくら|おつり|何円',q):return None
    items=[]   # (unit price, count, span)
    # 1本80円のえんぴつを3本 / 1こ250円のケーキを4こ / 1kg300円のりんごを2kg / 1袋2kgの... (not a price)
    for m in re.finditer(rf'1\s*({CNT})\s*(\d+)\s*円の[^。、を]*?を\s*(\d+(?:\.\d+)?)\s*({CNT})',whole):
        if _C[m.group(1)]!=_C[m.group(4)]:return None
        items.append((Fraction(m.group(2)),Fraction(m.group(3)),m.group(0),_C[m.group(1)],'1'))
    # ペンは1本120円、ノートは1さつ150円です。ペン2本とノート1さつを買うと
    if not items:
        prices={}
        for m in re.finditer(rf'([^\s、。は]+)は\s*1\s*({CNT})\s*(\d+)\s*円',s):prices[m.group(1)]=(Fraction(m.group(3)),_C[m.group(2)],m.group(0))
        if len(prices)>=2:
            for name,(p,c,sp) in prices.items():
                m=re.search(rf'{re.escape(name)}\s*(\d+)\s*({CNT})',q)
                if not m or _C[m.group(2)]!=c:return None
                items.append((p,Fraction(m.group(1)),sp,c,'1',m.group(0)))
    # 1500円のぼうしと1200円のマフラーを買って
    flat=[]
    if not items:
        for m in re.finditer(r'(?<![\d1])(\d+)\s*円の([^\s、。を]+?)(?:と|を)',whole):
            if re.search(r'1\s*$',whole[max(0,m.start()-3):m.start()]):continue
            flat.append((Fraction(m.group(1)),m.group(0)))
    pay=re.search(r'(\d+)\s*円\s*(?:さつ|札|玉|硬貨)?\s*で\s*(?:はら|払)',whole)
    if not items and not flat:return None
    if flat and not pay:return None
    nums_used=len(items)*2+len(flat)+(1 if pay else 0)+sum(1 for it in items if len(it)>5)*0
    total_nums=[n for n in N.find(t.translate(N._FW))]
    k=0;terms=[]
    for it in items:
        k+=1;p=b.bind(f'price{k}',f'円/{it[3]}',it[0],it[2],integer=False);c=b.bind(f'count{k}',it[3],it[1],it[5] if len(it)>5 else it[2],integer=False)
        terms.append(f'{p} * {c}')
        if '1' in [x.raw for x in N.find(it[2])] and not N.optional(next(x for x in N.find(it[2]) if x.raw=='1'),it[2]):b.skip('1',f'1{it[3]}あたりの値段の1')
    for v,sp in flat:
        k+=1;terms.append(b.bind(f'price{k}','円',v,sp,integer=False))
    if pay:
        if not re.search(r'おつり|お釣り',q):return None
        pd=b.bind('paid','円',Fraction(pay.group(1)),pay.group(0),integer=False)
        b.rel('change','円',f'{pd} - ({" + ".join(terms)})',q,integer=False);return b.spec('change','price')
    if flat:return None
    b.rel('cost','円',' + '.join(terms),q,integer=False);return b.spec('cost','price')


def _share(t,stm,q):
    b=_B(t);s=''.join(stm);whole=s+q;au=_ask_unit(q)
    # N C の I を M 人で(同じ数ずつ|等しく)分け…1人(分は)?何 C
    m=re.search(rf'(\d+)\s*({CNT})の?[^。]*?を\s*(\d+)\s*人で(?:同じ数ずつ|等しく|同じ数に|同じように|同じだけ|均等に)\s*分け',whole)   # 分けました alone may not be equal
    if m and re.search(r'1\s*人(?:分|あたり|当たり)?(?:は|に|が)?\s*何|1\s*人(?:分|あたり)?\s*何',q) and _C[m.group(2)]==au:
        sp=m.group(0);n=b.bind('total',au,Fraction(m.group(1)),sp,integer=False);p=b.bind('people','人',Fraction(m.group(3)),sp,integer=False)
        b.rel('each',f'{au}/人',f'{n} / {p}',q,integer=_whole(au));return b.spec('each','share')
    # クッキーが18まいあります。3まいのお皿に同じ数ずつのせると、1まいのお皿に何まい
    m=re.search(rf'(\d+)\s*({CNT})の\s*([^\s、。0-9]+?)に\s*(?:同じ数ずつ|等しく|同じ数に)\s*(?:のせ|乗せ|入れ|いれ|分け|わけ|配|くば|置|お)',whole)
    if m and au and re.search(rf'1\s*(?:{CNT})\s*の\s*{re.escape(m.group(3))}に?\s*(?:は)?\s*何',q):
        rest=whole[:m.start()]+' '*(m.end()-m.start())+whole[m.end():]
        tot=[x for x in _amts(rest,0) if x.c==au and not (x.v==1 and x.s>len(s))]
        if len(tot)==1:
            gu=m.group(3)
            n=b.bind('total',au,tot[0].v,_span_of(whole,tot[0]),integer=False);g=b.bind('groups','皿' if 'さら' in gu or '皿' in gu else gu,Fraction(m.group(1)),m.group(0),integer=False)
            b.rel('each',f"{au}/{'皿' if 'さら' in gu or '皿' in gu else gu}",f'{n} / {g}',q,integer=_whole(au));return b.spec('each','share')
    # N C を K C ずつ G に入れ…G は何 G | いくつ  /  I が N C あります。K C ずつ G に入れると、何 G
    m=re.search(rf'(\d+)\s*({CNT})\s*ずつ\s*([^\s、。]*?)(?:に|へ)\s*(?:入れ|いれ|分け|わけ|つめ|詰め|配る|くばる|配り|くばり|配ると|分ける)',whole)
    if m:
        k_c=_C[m.group(2)]
        rest=whole[:m.start()]+' '*(m.end()-m.start())+whole[m.end():]
        tot=[x for x in _amts(rest,0) if x.c==k_c]
        g=re.search(rf'何\s*({CNT})|いくつ',q)
        if len(tot)==1 and g and len(_amts(whole,0))==2 and not re.search(r'あまり|余り',q):
            gu=_C[g.group(1)] if g.group(1) else (m.group(3) or '組')
            if g.group(1) is None and not m.group(3):return None
            n=b.bind('total',k_c,tot[0].v,_span_of(whole,tot[0]),integer=False);k=b.bind('size',f'{k_c}/{gu}',Fraction(m.group(1)),m.group(0),integer=False)
            b.rel('groups',gu,f'{n} / {k}',q,integer=True);return b.spec('groups','share')
    m=re.search(rf'1\s*人に\s*(\d+)\s*({CNT})ずつ\s*(?:配る|くばる|分ける|あげる)と',whole)
    if m and re.search(r'何人',q):
        c=_C[m.group(2)];rest=whole.replace(m.group(0),' '*len(m.group(0)))
        tot=[x for x in _amts(rest,0) if x.c==c]
        if len(tot)==1 and len(_amts(whole,0))==2:
            n=b.bind('total',c,tot[0].v,_span_of(whole,tot[0]),integer=False);k=b.bind('each',f'{c}/人',Fraction(m.group(1)),m.group(0),integer=False)
            b.rel('people','人',f'{n} / {k}',q,integer=True);return b.spec('people','share')
    # 1まい800円のチケットを買います。5600円では何まい買えますか
    m=re.search(rf'1\s*({CNT})\s*(\d+)\s*円の[^。]*?。?',s);n=re.search(r'(\d+)\s*円で(?:は)?\s*何\s*('+CNT+')',q)
    if m and n and _C[n.group(2)]==_C[m.group(1)] and len(_amts(whole,0))==3:
        c=_C[m.group(1)];p=b.bind('price',f'円/{c}',Fraction(m.group(2)),m.group(0),integer=False);w=b.bind('money','円',Fraction(n.group(1)),q,integer=False)
        b.rel('count',c,f'{w} / {p}',q);return b.spec('count','share')
    # 毎月1500円ずつ貯め…9000円貯めるには何か月 / 1日に20ページずつ読むと、140ページの本を読み終えるのに何日
    m=re.search(rf'(?:毎朝|毎日|毎晩|毎週|毎月|毎年|1\s*({CNT})に)\s*(\d+(?:\.\d+)?)\s*({CNT})ずつ',whole)
    g=re.search(rf'何\s*({CNT})',q)
    if m and g:
        word=re.match(r'毎(朝|日|晩|週|月|年)',m.group(0))
        per=_C[m.group(1)] if m.group(1) else {'朝':'日','日':'日','晩':'日','週':'週','月':'か月','年':'年'}[word.group(1)]
        c=_C[m.group(3)]
        if _C[g.group(1)]==per:
            rest=whole[:m.start()]+' '*(m.end()-m.start())+whole[m.end():]
            tot=[x for x in _amts(rest,0) if x.c==c]
            if len(tot)==1 and len(_amts(whole,0))==(3 if m.group(1) else 2):
                r=b.bind('rate',f'{c}/{per}',Fraction(m.group(2)),m.group(0),integer=False);n=b.bind('total',c,tot[0].v,_span_of(whole,tot[0]),integer=False)
                b.rel('periods',per,f'{n} / {r}',q,integer=True);return b.spec('periods','share')   # 7.5 days to finish is 8, not read
    # N C で P 円です。1 C 何円  /  N本入りのジュースがP円です。1本あたり何円
    m=re.search(rf'(\d+)\s*({CNT})(?:で|入りの[^。]*?が)\s*(\d+)\s*円です',s)
    if m and re.search(rf'1\s*({CNT})(?:あたり|当たり)?\s*(?:は)?\s*何円|1\s*({CNT})\s*(?:あたり|当たり)?\s*いくら',q):
        c=_C[m.group(2)];n=b.bind('count',c,Fraction(m.group(1)),m.group(0),integer=False);p=b.bind('price','円',Fraction(m.group(3)),m.group(0),integer=False)
        b.rel('each',f'円/{c}',f'{p} / {n}',q,integer=True);return b.spec('each','share')
    return None


def _groups(t,stm,q):
    b=_B(t);s=''.join(stm);whole=s+q;au=_ask_unit(q)
    if au is None:return None
    pats=[
     # 1ふくろにあめが6こずつ入っています。4ふくろでは / 1れつに8本ずつ6れつ / 1つの階に4部屋ずつ(9かい) / 1台に9人ずつ乗れるバンが7台
     rf'1\s*(?:つの)?\s*(?P<g>{CNT}|[^\s、。0-9]{{1,4}}?)に[^。、0-9]*?(?P<n>\d+)\s*(?P<c>{CNT})ずつ',
     # ガムが5まいずつ入ったパックが3パック / 6こずつ入ったふくろ
     rf'(?P<n>\d+)\s*(?P<c>{CNT})ずつ入った',
     # 10本入りのマーカーを3箱 / 6本入りの
     rf'(?P<n>\d+)\s*(?P<c>{CNT})入りの',
     # 1袋2kgの米を5袋 / 1箱5kgの荷物が8箱 / 1段に30冊ずつ
     rf'1\s*(?P<g>{CNT})\s*(?P<n>\d+(?:\.\d+)?)\s*(?P<c>kg|g|L|mL|m|cm|km)の',
     # 500mLの水が入ったペットボトルが3本
     rf'(?P<n>\d+(?:\.\d+)?)\s*(?P<c>{CNT})の[^。、0-9]*?(?:が入った|の入った)',
     # ケーキ1こに小麦粉を200g使います。ケーキ5こでは
     rf'1\s*(?P<g>{CNT})に[^。、0-9]*?(?P<n>\d+(?:\.\d+)?)\s*(?P<c>kg|g|L|mL|dL|cm|m|km|分)\s*(?:使|つか|かか|いり|いる|必要)']
    for pat in pats:
        m=re.search(pat,whole)
        if not m:continue
        c=_C[m.group('c')] if m.group('c') in _C else m.group('c')
        if c!=au:continue
        rest=whole[:m.start()]+' '*(m.end()-m.start())+whole[m.end():]
        others=[x for x in _amts(rest,0) if x.c!=c or True]
        gu=_C.get(m.groupdict().get('g') or '',None)
        cnt=[x for x in others if (gu is None or x.c==gu) and x.c!=c and not (x.v==1 and N.optional(next((n for n in N.find(rest) if n.start==x.s),N.find(x.raw)[0]),rest))]
        minus=[x for x in others if x.c==c]
        if gu is None and len(cnt)==1:gu=cnt[0].c
        if len(cnt)!=1 or gu is None:continue
        sp=m.group(0)
        n=b.bind('each',f'{c}/{gu}',Fraction(m.group('n')),sp,integer=False)
        g=b.bind('groups',gu,cnt[0].v,_span_of(whole,cnt[0]),integer=False)
        if not minus:
            b.rel('total',c,f'{n} * {g}',sp,integer=False);return b.spec('total','groups')
        if len(minus)==1 and re.search(MINUS,whole[minus[0].s:minus[0].s+40]) and re.search(r'のこり|残り',q):
            x=b.bind('gone',c,minus[0].v,_span_of(whole,minus[0]),integer=False)
            b.rel('left',c,f'{n} * {g} - {x}',q,integer=False);return b.spec('left','groups')
        return None
    return None


CMP_MORE=r'(?:多く|多い|おおく|おおい|年上|高く|高い|たかく|たかい|長く|長い|重く|重い|おそく|遅く|大きく|大きい)'
CMP_LESS=r'(?:少なく|少ない|すくなく|すくない|年下|低く|低い|ひくく|ひくい|短く|短い|軽く|軽い|はやく|早く|小さく|小さい)'
def _compare(t,stm,q):
    b=_B(t);s=''.join(stm);au=_ask_unit(q)
    if au is None and not re.search(r'何才|何歳|何点|何cm|何m',q):return None
    # X は Y より N C 多く/少なく … ; Y の amount given; ask X (or both together)
    for i,st in enumerate(stm):
        m=re.search(rf'(?P<x>[^\s、。]+?)(?:は|が|の[^\s、。]*?は)(?:[^。]*?[をがに])?(?P<y>[^\s、。をがに]+?)より\s*(?P<n>\d+(?:\.\d+)?)\s*(?P<c>{CNT})\s*(?P<d>{CMP_MORE}|{CMP_LESS})',st)
        if not m:continue
        x,y=_who(m.group('x')),_who(m.group('y'));c=_C[m.group('c')];sign='+' if re.fullmatch(CMP_MORE,m.group('d')) else '-'
        # Y's amount, in another sentence or before in this one (…持っていて、Yより6枚多いです)
        given=None
        for j,o in enumerate(stm):
            if j==i:
                pre=st[:m.start('y')]
                a=_amts(pre,0)
                if len(a)==1 and re.search(r'持っていて|で、|あり、',pre):given=('x',a[0],pre)
                continue
            a=_amts(o,j)
            if len(a)==1 and _who(_topic(o))==y:given=('y',a[0],o)
            elif len(a)==1 and _who(_topic(o))==x:given=('x',a[0],o)
        if given is None:continue
        side,a,gsp=given
        conv=None
        if a.c!=c:
            if (a.c,c) in CONVERT:conv=CONVERT[(a.c,c)]
            else:return None
        d=b.bind('difference',c,Fraction(m.group('n')),st,integer=False)
        gv=b.bind('given',a.c,a.v,gsp,integer=False)
        if conv:gv=f"{gv} * {b.known('per',f'{c}/{a.c}',conv[0],conv[1])}"
        asks_x=_who(_topic(q)) in (x,'') if 'は' in q else True
        both=re.search(r'(?:2人|二人|ふたり|両方)[^。]*?(?:合わせて|あわせて|全部で)',q)
        if side=='y':
            b.rel('other',c,f'{gv} {sign} {d}',st,integer=False)
            if both:b.rel('together',c,f'{gv} + other',q,integer=False);return b.spec('together','compare')
            if re.search(re.escape(m.group('x')),q) or asks_x:return b.spec('other','compare')
            return None
        else:
            b.rel('other',c,f'{gv} {"-" if sign=="+" else "+"} {d}',st,integer=False)
            if re.search(re.escape(m.group('y')),q):return b.spec('other','compare')
            return None
    # A が N1、B が N2 … A は B より何 C 多い/少ない / 差は何
    m=re.search(rf'(?P<x>[^\s、。]+?)は(?P<y>[^\s、。]+?)より何\s*(?P<c>{CNT})\s*(?P<d>{CMP_MORE}|{CMP_LESS})',q)
    diff=re.search(r'差は|ちがいは|違いは',q)
    a=_amts(s,0)
    if (m or diff) and len(a)==2 and a[0].c==a[1].c and (au is None or a[0].c==au):
        c=a[0].c
        if m:
            names=[_who(x) for x in _holders(s,a)]
            if None in names:return None
            x,y=_who(m.group('x')),_who(m.group('y'))
            def same(u,v):return u==v or u.startswith(v) or v.startswith(u)
            if not (same(x,names[0]) and same(y,names[1])) and not (same(x,names[1]) and same(y,names[0])):return None
            first=0 if same(x,names[0]) and same(y,names[1]) else 1;hi,lo=(a[first],a[1-first])
            if re.fullmatch(CMP_LESS,m.group('d')):hi,lo=lo,hi
        else:
            hi,lo=(a[0],a[1]) if a[0].v>=a[1].v else (a[1],a[0])
        h=b.bind('high',c,hi.v,_span_of(s,hi),integer=False);l=b.bind('low',c,lo.v,_span_of(s,lo),integer=False)
        b.rel('difference',c,f'{h} - {l}',q,integer=False);return b.spec('difference','compare')
    return None


def _topic(s):
    """what a sentence is about: the words before its first は that has a word before it ('はるとさんは8才です')"""
    m=re.match(r'\s*(.+?)は',s or '')
    return m.group(1) if m else ''


def _who(w):
    w=re.sub(r'^(?:その|この)','',(w or '').strip())
    w=re.sub(r'(?:さん|くん|君|ちゃん)$','',w)
    return w


def _holders(s,amts):
    """the holder of each amount: the word before は/が before it in its clause"""
    out=[]
    for a in amts:
        st=s.rfind('、',0,a.s);st=max(st,s.rfind('。',0,a.s))+1
        m=re.match(r'\s*([^\s、。]+?)(?:は|が)',s[st:a.s])
        out.append(m.group(1) if m else None)
    return out


def _rest(t,stm,q):
    b=_B(t);s=''.join(stm);au=_ask_unit(q)
    a=_amts(s,0)
    if len(a)!=2 or au is None:return None
    # 劇場には200席あります。163人がすわっています。空いている席は何席 (one person in each seat)
    if a[0].c=='席' and a[1].c=='人' and re.search(r'すわっ|座っ',s) and re.search(r'(?:空いて|あいて)いる(?:席|せき)は何\s*(?:席|せき)',q):
        w=b.bind('seats','席',a[0].v,_span_of(s,a[0]));p=b.bind('taken','席',a[1].v,_span_of(s,a[1]))
        b.rel('free','席',f'{w} - {p}',q);return b.spec('free','rest')
    # N人のうち、K人が…。…でない/ない X は何人  /  子どもがN人来ました。そのうちK人が女の子です。男の子は何人
    pairs=(('男の子','女の子'),('男子','女子'),('大人','子ども'),('おとな','こども'))
    whole,part=a
    if not (whole.c==part.c==au):return None
    if re.search(r'のうち|そのうち|その中で|そのなか',s):
        neg=re.search(r'(?:ない|ていない|でない|ではない|じゃない)\s*[^\s、。]*?は\s*何',q)
        comp=False
        for x,y in pairs:
            if (y in s and x in q and x not in s.replace(y,'')) or (x in s and y in q and y not in s.replace(x,'')):comp=True
        if neg or comp:
            w=b.bind('whole',au,whole.v,_span_of(s,whole),integer=False);p=b.bind('part',au,part.v,_span_of(s,part),integer=False)
            b.rel('rest',au,f'{w} - {p}',q,integer=False);return b.spec('rest','rest')
    return None


def _combine(t,stm,q):
    b=_B(t);s=''.join(stm);au=_ask_unit(q)
    if au is None or not re.search(r'全部で|ぜんぶで|あわせて|合わせて|みんなで|両方で|全体で',q):return None
    if re.search(r'ずつ|より|のうち|倍|分の|%|引き|1\s*(?:'+CNT+r')\s*\d+\s*円',s):return None
    if re.search(MINUS,s) and not re.search(r'(?:つみ|摘み|読み|焼き|売れ)',s):return None
    a=_amts(s,0)
    if len(a)<2 or any(x.c!=au for x in a):return None
    names=[]
    for i,x in enumerate(a):names.append(b.bind(f'part{i+1}',au,x.v,_span_of(s,x),integer=False))
    b.rel('total',au,' + '.join(names),q,integer=False);return b.spec('total','combine')


def _remaining(t,stm,q):
    b=_B(t);au=_ask_unit(q)
    if au is None or not stm:return None
    if not re.search(r'のこり|残り|今|いま|何\s*(?:'+CNT+r')\s*(?:に)?なり|何\s*(?:'+CNT+r')\s*(?:ありますか|いますか|持っていますか|ですか)|おつり|食べていない|使っていない|気温',q):return None
    s=''.join(stm)
    if re.search(r'ずつ|より|のうち|倍|分の|%',s):return None
    a=_amts(s,0)
    if len(a)<2 or any(x.c!=au for x in a):return None
    first=a[0];head=s[:a[1].s]
    if re.search(MINUS+'|'+PLUS,s[first.e:first.e+12]) and not re.search(STATE,s[first.e:first.e+14]):return None
    terms=[b.bind('start',au,first.v,_span_of(s,first),integer=False)];expr=terms[0]
    for i,x in enumerate(a[1:],2):
        after=s[x.e:x.e+30];clause=_span_of(s,x)
        tail=after.split('、')[0].split('。')[0]
        nxt=a[i] if i<len(a) else None
        if not tail.strip() and after.startswith('、') and nxt is not None and s.find('。',x.e)>=nxt.s:
            # nothing but a comma before the next amount of this sentence: the two share the verb that follows it
            tail=s[nxt.e:nxt.e+30].split('、')[0].split('。')[0]
        mi=re.search(MINUS,tail);pl=re.search(PLUS,tail)
        # 180円のパンを買いました: money spent
        if au=='円' and re.match(r'\s*の',after) and re.search(r'買',tail):mi,pl=True,None
        if bool(mi)==bool(pl):
            if mi and pl and mi.start()!=pl.start():
                mi,pl=(mi,None) if mi.start()<pl.start() else (None,pl)
            else:return None
        name=b.bind(f'change{i}',au,x.v,clause,integer=False)
        expr=f'{expr} {"-" if mi else "+"} {name}'
    b.rel('now',au,expr,q,integer=False,signed=au=='度');return b.spec('now','remaining')
