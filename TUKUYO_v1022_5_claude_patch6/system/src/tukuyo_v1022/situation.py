"""claude-patch6: a situation model for quantity stories (Japanese + simple English).

patch5 answered 「みかんが20個あります。8個食べました。はじめにあったのは何個？」 with 12 and
「りんごが12個あります。妹に5個あげました。妹は何個持っていますか？」 with 7: every producer computed
the remainder without reading what the question asks for. This module first builds a small
model of the story
  holders  people or places that hold something (わたし, 兄, バス, 公園, Mia, the tree ...)
  objects  what is held (りんご, ビー玉, 人, 円, stickers ...); 2L300mL is one amount
  events   completed changes in reading order: verb, amount, holder and, when it is stated,
           the other party (妹に あげた / 友だちから もらった / gave 6 to Leo)
and then reads the question as a query over the model (the role):
  remain    current amount of the main holding (残り, 今, になりました, now, left)
  total     sum over all stated holdings (二人合わせて, in all)
  initial   amount before any event (はじめに, 最初, もともと, at first)
  before    amount just before the first event of a verb (もらう前は)
  event     amount of the events of a verb, optionally with that other party (食べたのは, 妹にあげたのは)
  received  what another party received (妹は何枚もらいましたか)
  holding   current amount of another holder or object (弟は今何個, りんごは何個)
A value that the story does not determine (the other party's starting amount is never stated)
is refused, never guessed. The rest fails closed like wordprob.py: every number must be read,
hedged / negated / unknown amounts and verbs whose effect depends on the point of view (売る
借りる なくす 釣る sell lend lose ...) refuse, results are exact and never negative.

solve() returns None (not a story this module reads), {'refused': reason, 'role': role} or
{'answer', 'role', 'proof'}; proofs.check replays the proof by reading the question again.
The caller treats every role except remain/total as authoritative; for remain/total the older
producers keep precedence and this model is a second, separately built reading.
"""
from __future__ import annotations
import re,unicodedata
from fractions import Fraction
from .wordprob import _norm,_merge_compound,_conv,QTY,DIM,CNT

def _fmt(v):
    v=Fraction(v);return str(v.numerator) if v.denominator==1 else format(float(v),'.12g')

class Refuse(Exception):pass
def _refuse(reason):raise Refuse(reason)

# ----------------------------------------------------------------------------- the model
class Model:
    def __init__(s):
        s.hold={};s.initial={};s.order=[];s.events=[];s.main=None;s.given=[]
    def state(s,h,o,v):
        k=(h,o)
        if k in s.hold and s.initial.get(k) is not None:_refuse('SITUATION_DUPLICATE_STATE')
        s.hold[k]=Fraction(v);s.initial[k]=Fraction(v);s.order.append(k)
        if s.main is None:s.main=k
    def unknown(s,k):
        if k not in s.hold:s.hold[k]=None;s.initial[k]=None
    def apply(s,ev):
        k=(ev['holder'],ev['object']);q=ev['quantity'];o=ev.get('other');ko=(o,ev['object']) if o is not None else None
        if ev['kind'] in ('out','give'):
            s.hold[k]=None if s.hold.get(k) is None else s.hold[k]-q
            if ev['kind']=='give' and ko:s.unknown(ko);s.hold[ko]=None if s.hold[ko] is None else s.hold[ko]+q
        elif ev['kind'] in ('in','receive'):
            s.hold[k]=None if s.hold.get(k) is None else s.hold[k]+q
            if ev['kind']=='receive' and ko and ko in s.hold:s.hold[ko]=None if s.hold[ko] is None else s.hold[ko]-q
        if any(v is not None and v<0 for v in s.hold.values()):_refuse('SITUATION_OVERCONSUMPTION')
        s.events.append(ev)
    def chain(s,k,upto=None):
        """expression and value of holding k after the first `upto` events (None if its start is unknown)"""
        if s.initial.get(k) is None:return None,None
        v=s.initial[k];expr=_fmt(v)
        for e in s.events[:upto]:
            q=e['quantity'];mine=(e['holder'],e['object'])==k;to_me=e.get('other') is not None and (e['other'],e['object'])==k
            if mine and e['kind'] in ('out','give') or to_me and e['kind']=='receive':v-=q;expr+='-'+_fmt(q)
            elif mine and e['kind'] in ('in','receive') or to_me and e['kind']=='give':v+=q;expr+='+'+_fmt(q)
        return expr,v

def _answer(role,value,expr,model,target,query,unit,scale=None):
    if value is None:_refuse('SITUATION_TARGET_NOT_DETERMINED')
    if scale is not None:value=value*scale;expr=f'({expr})*{_fmt(scale)}'
    if value<0:_refuse('SITUATION_NEGATIVE')
    proof={'kind':'situation','role':role,'target':[str(x) for x in target],'unit':unit,'given':[_fmt(x) for x in model.given],
           'holdings':len(model.order),
           'initial':[[h,o,_fmt(v)] for (h,o),v in model.initial.items() if v is not None],
           'events':[{'verb':e['verb'],'effect':e['kind'],'quantity':_fmt(e['quantity']),'holder':e['holder'],'object':e['object'],
                      'other':e.get('other')} for e in model.events],
           'expression':expr,'answer':_fmt(value),'source_query':str(query)}
    return {'answer':_fmt(value),'role':role,'proof':proof,'holdings':max(len(model.order),len({k[1] for k in model.hold}))}

def _sum_events(role,hits,model,target,query,unit,scale=None):
    if not hits:_refuse('SITUATION_EVENT_NOT_IN_STORY')
    return _answer(role,sum(e['quantity'] for e in hits),'+'.join(_fmt(e['quantity']) for e in hits),model,target,query,unit,scale)

# ----------------------------------------------------------------------------- Japanese
# A verb is read at the start of the predicate that follows an amount. Order matters: the
# point-of-view dependent verbs refuse first, then passives (取られた = taken from the holder),
# then "...てきた" (came back / came in), then the plain lexicon.
AMBIG_JA=(r'売っ|売り|売る|販売|返品|仕入|貸し|貸す|借り(?!られ)|かりまし|かりて|かりた|返し|返す|かえし|預け|あずけ|交換|両替|譲|寄付|出荷|入荷|'
          r'なくし|無くし|失くし|紛失|落とし|おとし|盗ん|釣|つっ(?=た|て)|つり|補充|処分|配達|送っ|送り|おくっ|移し|うつし|動かし|運ん|はこん|もっていっ|持っていっ|持ってき|もってき|しまい|片付')
VERBS_JA=[
    (r'借りられ|かりられ|持っていかれ|もっていかれ|食べられ|たべられ|取られ|とられ|盗まれ','out','passive'),
    (r'返ってき|返って来|かえってき|もどってき|戻ってき|戻って来|乗ってき|乗って来|のってき|飛んでき|飛んで来|とんでき|入ってき|入って来|はいってき|やってき|やって来|集まってき','in','arrive'),
    (r'食べ|たべ|飲ん|飲み|のん(?=で|だ)|のみ(?=まし)|使っ|使い|使う|つかっ|つかい|使用し|消費し|捨て|すて(?=まし|て|た)|割れ|われ(?=まし|て|た)|割っ|こわれ|壊れ|こわし|壊し|枯れ|散っ|切り取|切りとっ|切りとり|切り落と|切っ|切り(?=まし)|減っ|減り|へっ(?=て|た)|溶け','out','consume'),
    (r'あげ|渡し|わたし(?=まし|て|た)|配っ|配り|くばっ|くばり|贈っ|贈り|プレゼントし','give','give'),
    (r'降り|おり(?=まし|て|た)|帰っ|帰り|かえっ(?=て|た)|かえり(?=まし)|出て行|出ていっ|出ていき|でていっ|でていき|出かけ|でかけ|飛んでいっ|飛んでいき|飛んで行|とんでいっ|とんでいき|飛び去|飛び立|去っ|去り|逃げ|にげ|いなくなっ|いなくなり|取り出|とりだ|抜い|抜き|売れ|うれ(?=まし|て|た)','out','leave'),
    (r'払っ|払い|はらっ|はらい|支払','out','pay'),
    (r'もらい|もらっ|もらう|貰い|貰っ|受け取|うけと|届い|とどい','receive','receive'),
    (r'買っ|買い|買う|拾っ|拾い|ひろっ|ひろい|見つけ|みつけ|集め|あつめ|作っ|作り|つくっ|つくり|焼い|摘ん|生まれ|うまれ|咲い|咲き|増え|ふえ|増やし|ふやし|入れ|いれ(?=まし|て|た)|足し|加え|くわえ|加わ|くわわ|追加し|貯金し|貯め|ため(?=まし|て|た)|戻っ|戻り|もどっ|もどり|乗り|のり(?=まし|て|た)|乗っ(?=た)|来ま|来た|来て|きまし|入り|はいり|入っ(?=た)|はいっ(?=た)|集まっ|あつまっ','in','gain'),
    (r'読ん|読み|よん(?=で|だ)|よみ(?=まし)|解い|書い|見ま|見た|みまし|数え|かぞえ|開け|確認し|練習し','none','activity'),
]
STATE_JA=(r'(?:あります|ある|あり|ありました|あった|あって|います|いる|いて|いました|いた|持って(?:い|お)|もって(?:い|お)|乗って(?:い|お)|のって(?:い|お)|'
          r'入って(?:い|お)|はいって(?:い|お)|咲いて(?:い)|さいて(?:い)|残って(?:い)|のこって(?:い)|飼って(?:い)|並んで(?:い)|泳いで(?:い)|座って(?:い)|すわって(?:い)|'
          r'集まって(?:い)|貯まって(?:い)|たまって(?:い)|置いて(?:あ)|しまって(?:あ)|生えて(?:い))')
HEDGE_JA=re.compile(r'予定|つもり|かもしれ|らしい|そうです|だろう|と言|と聞|明日|来週|夢|想像|もし|なら(?!ん|べ)|ぐらい|くらい|ほど|程度|約|およそ|だいたい|大体|ほぼ|以上|以下|未満|少なくとも|最大|最低|高々|せいぜい|'
                    r'[〜~～]|または|もしくは|不明|かどうか|(?:何(?:個|人|本|枚|冊|匹|羽|台|円|頭|つ|杯|回|足)|いくつ|いくら)か(?![？?。]|$)|たくさん|少し|すこし|数(?:個|人|本|枚|冊|匹|羽)')
NEG_JA=re.compile(r'ません|なかった|(?<!少)ない(?!よう)|なくて|ずに|ないで')
OTHER_JA=re.compile(r'ずつ|倍|割|%|パーセント|平均|分の|あまり|余り|時速|分速|秒速|速さ|\d+\s*円の|面積|まわり|周り|より|ちがい|違い|差|以外|ある数|比|回目|番目|'
                    r'\d+\s*(?:時|日|月|年)(?!間)|何時|何日|何曜|ごと|毎|ダース')
SCOPE_JA=re.compile(r'別の|他の|ほかの|よその|他人|友人の在庫|隣の|隣店')
QWORD_JA=re.compile(r'何|いくつ|いくら|どれだけ|どのくらい|どれくらい')
SELF=('わたし','私','ぼく','僕','おれ','自分','あなた')
TIME_WORDS=('今日','きょう','昨日','きのう','朝','夕方','夜','午前','午後','今','いま','さっき','あとで','はじめ','最初','初め','現在')
PKG=re.compile(r'1\s*(箱|袋|パック|ケース|束|皿|かご)\s*(?:に|あたり|には)?\s*(\d+)\s*(個|枚|本|冊|台|人|粒|匹)\s*入り(?:の([^、。\d]{1,10}?))?\s*(?:が|を|の)?\s*(\d+)\s*\1')
LABEL=re.compile(r'\d+年\d+組|\d+年生|第\d+|\d+号(?:車|室|館)?|\d+番(?:目|線)?')

def _name(x):
    x=re.sub(r'^(?:その|この|あの|それから|そして|また|さらに|次に|まず|すると|今度は)','',x or '')
    x=re.sub(r'(?:さん|くん|ちゃん|君|様)$','',x)
    return x or None

def _match_verb(p):
    if re.match(AMBIG_JA,p):return 'AMBIG',None,None
    for pat,kind,cls in VERBS_JA:
        m=re.match(pat,p)
        if m:return kind,cls,m.group()
    return None,None,None

def _strip_pred(p):
    p=re.sub(r'^だけ','',p)
    p=re.sub(r'^(?:の[^、。\d]{1,10}?)?(?:を|が|は|に)?','',p)
    return re.sub(r'^(?:さらに|また|あとから|後から|その後|そのあと|それから|新しく|あたらしく|次に|みんなで|全部|ぜんぶ|すぐに)?[、]?','',p)

STATIVE_Q=r'(?:あり|い|持ってい|もってい|乗ってい|のってい|入ってい|はいってい|残ってい|のこってい|咲いてい|飼ってい|にな|になり|あっ|でし)'
def _ask_verb(q):
    """「何枚もらいましたか」 -> もらい; existence / result verbs (ありましたか, になりましたか) are not events"""
    m=re.search(r'何\s*(?:'+CNT+r')?(?:を|も(?!ら))?([^、。\d？?何]{1,10}?)(?:まし|た|だ)(?:た)?か',q)
    if not m or re.fullmatch(STATIVE_Q,m[1]):return None
    return m

def _ja_role(q):
    """role of a Japanese question, read from the question alone"""
    if re.search(r'はじめ|初め|最初|もともと|もとは|元は|元々',q):return 'initial'
    if re.search(r'[^、。\d]{1,6}?前(?:は|に|には)',q):return 'before'
    if re.search(r'(?:た|だ)(?:の|数|分)(?:は|が)',q) and not re.search(r'(?:てい|って|でい)(?:た|る)の',q):return 'event'
    if _ask_verb(q):return 'event'
    if _ja_subject(q):return 'holding'
    if re.search(r'二人|ふたり|2人|三人|みんな|全員|合わせて|あわせて|合計',q):return 'total'
    return 'remain'

def _ja_subject(q):
    q=re.sub(r'^(?:では|それでは|じゃあ|さて)[、]?','',q)
    q=re.sub(r'^(?:はじめに|初めに|最初に|もともと|もとは|今|いま|現在)[、]?','',q)
    m=re.match(r'^([^、。\d何]{1,10}?)(?:には|は|が)(?!じめ)',q)
    x=_name(m[1]) if m else None
    if x and re.search(r'(?:た|だ|る|う)の$|前$',x):return None          # 「あげたのは」「もらう前は」 are not subjects
    if x in TIME_WORDS or x in SELF or x in ('残り','全部','ぜんぶ','みんな','合計','全体','のこり','二人','ふたり'):return None
    return x

def _lemma(verb):
    """a question verb matches an event by stem: the leading kanji (読ん/読み -> 読) or the first two kana;
    the lexicon kind is compared as well, so 飛んできた (in) and 飛んでいった (out) stay apart"""
    m=re.match(r'[一-鿿]+',verb or '')
    return m.group() if m else (verb or '')[:2]

def _ja_mentions(sents):
    """amount mentions with the text before and after each one, per sentence"""
    out=[]
    for si,s in enumerate(sents):
        spans=[];items=[]
        for m in PKG.finditer(s):
            items.append({'value':Fraction(int(m[2])*int(m[5])),'unit':m[3],'span':m.span(),'obj':_name(m[4]),'package':True,'factors':[int(m[2]),int(m[5])]});spans.append(m.span())
        for m in LABEL.finditer(s):spans.append(m.span())
        for q in _merge_compound(list(QTY.finditer(s))):
            if any(a<=q.start()<b for a,b in spans):continue
            items.append({'value':Fraction(q[1]),'unit':q[2],'span':q.span(),'obj':None,'package':False})
        items.sort(key=lambda x:x['span'][0])
        for n in re.finditer(r'\d+(?:\.\d+)?',s):
            if not any(a<=n.start() and n.end()<=b for a,b in spans+[x['span'] for x in items]):_refuse('SITUATION_NUMBER_NOT_READ')
        prev=0
        for i,it in enumerate(items):
            a,b=it['span'];nxt=items[i+1]['span'][0] if i+1<len(items) else len(s)
            gap=s[b:nxt]
            if i+1<len(items):
                m=re.match(r'[^、]*?(?:、|と(?=[^、。\d]{1,10}(?:が|を|は))|や)',gap)
                post=m.group() if m else gap
            else:post=gap
            it.update({'si':si,'pre':s[prev:a],'post':post,'sent':s});prev=b+len(post)
            out.append(it)
    return out

ADVERB_JA=r'(?:さらに|すぐに|次に|最後に|最初に|はじめに|初めに|一緒に|いっしょに|新たに|あらたに|ほかに|他に|全部で|みんなで|また|そして|それから|その後|そのあと|あとから|後から|今度は|続けて|つづけて)'
def _ja_holder_object(it,kind):
    pre=it['pre'];other=None
    pre2=re.sub(r'^[^、。\d]{1,8}?は(?!じめ)','',pre)
    pre2=re.sub(r'(?:^|(?<=[、]))'+ADVERB_JA+r'[、]?','',pre2)
    loc=re.match(r'^(?:[^、。\d]{0,6}?、)?([^、。\d]{1,8}?)(?:の中|の上)?(?:には|に|では|の中には)(?=.)',pre2) if kind=='state' else None
    obj=re.search(r'([^、。\dにで]{1,10}?)(?:が|を|は)$',pre2)
    if kind!='state':
        g=re.search(r'([^、。\d]{1,8}?)(?:に|へ)(?:[^、。\d]{1,10}?を)?$',pre2);f=re.search(r'([^、。\d]{1,8}?)から(?:[^、。\d]{1,10}?を)?$',pre2)
        if g:other=('to',_name(g[1]))
        elif f:other=('from',_name(f[1]))
    o=_name(it.get('obj') or (obj[1] if obj else None))
    if o in ('そのうち','うち'):o=None
    h=_name(loc[1]) if loc else None
    if h and o and h==o:h=None
    return h,o,other

def _ja_build(body,query):
    model=Model();ments=_ja_mentions(body)
    if not ments:return None
    units={m['unit'] for m in ments}
    if len(units)>1 and (not all(u in DIM for u in units) or len({DIM[u][0] for u in units})>1):return None
    unit=min(units,key=lambda u:Fraction(DIM[u][1])) if all(u in DIM for u in units) else units.pop()
    pending=[]
    for it in ments:
        model.given+=it.get('factors') or [it['value']]
        s=it['sent'];topic=None
        tm=re.match(r'^([^、。\d]{1,8}?)は(?!じめ)',it['pre']) or re.match(r'^([^、。\d]{1,8}?)は(?!じめ)',s)
        if tm and not tm[1].endswith(('に','で')) and _name(tm[1]) not in TIME_WORDS:topic=_name(tm[1])
        p=_strip_pred(it['post']);val=_conv(it['value'],it['unit'],unit) if it['unit']!=unit else it['value']
        if re.fullmatch(r'[、と]?|や',p) and not it['package']:
            pending.append((it,topic,val));continue
        if re.match(STATE_JA,p) or it['package'] and re.match(r'(?:が|を|は)?(?:'+STATE_JA+'|$)',p):
            for jt,jtopic,jval in pending+[(it,topic,val)]:
                h,o,_=_ja_holder_object(jt,'state')
                holder=h or (jtopic if jtopic not in SELF else None) or 'わたし'
                obj='円' if unit=='円' else (o or unit)
                model.state(_name(holder),obj,jval)
            pending=[];continue
        kind,cls,verb=_match_verb(p)
        if kind=='AMBIG':_refuse('SITUATION_AMBIGUOUS_VERB')
        if kind is None or model.main is None:return None
        for jt,jtopic,jval in pending+[(it,topic,val)]:
            h,o,other=_ja_holder_object(jt,'event')
            if jtopic and jtopic not in SELF and not any(k[0]==jtopic for k in model.hold):
                if len(model.order)==1 and jtopic!=model.main[1]:jtopic=None      # 「Aさんは5個食べました」 acting on the only holding
                elif jtopic==model.main[1]:jtopic=None
                else:_refuse('SITUATION_UNKNOWN_ACTOR')
            holder=jtopic if jtopic and jtopic not in SELF else model.main[0]
            if unit=='円':obj='円'
            elif o:
                if (holder,o) not in model.hold:model.unknown((holder,o))
                obj=o
            else:
                objs={k[1] for k in model.hold if k[0]==holder and model.initial.get(k) is not None}
                if len(objs)!=1:_refuse('SITUATION_AMBIGUOUS_OBJECT')
                obj=next(iter(objs))
            k_=kind;cp=None
            if other:
                d,nm=other
                if d=='to' and kind=='in' and re.match(r'入れ|いれ',verb):k_='give';cp=nm
                elif d=='to' and kind=='give':cp=nm
                elif d=='from' and kind in ('receive','in'):k_='receive';cp=nm
            if unit=='円' and cls=='gain' and re.match(r'買',verb):k_='out'
            if cls=='pay' and unit!='円':_refuse('SITUATION_PAY_WITHOUT_MONEY')
            if cp is not None and cp==holder:_refuse('SITUATION_SELF_TRANSFER')
            model.apply({'holder':holder,'object':obj,'kind':k_,'quantity':jval,'other':cp,'verb':verb,'cls':cls,'lex':kind})
        pending=[]
    if pending or model.main is None:return None
    return model,unit

def _ja_query(model,unit,q,query,ctx=None):
    ctx=ctx if ctx is not None else {}
    am=re.search(r'何\s*('+CNT+r')',q)
    if am:
        au=am[1]
        if au!=unit and not (au in DIM and unit in DIM and DIM[au][0]==DIM[unit][0]):_refuse('SITUATION_UNIT_MISMATCH')
    elif re.search(r'いくら',q):
        au='円'
        if unit!='円':_refuse('SITUATION_UNIT_MISMATCH')
    elif re.search(r'いくつ',q):au=unit
    else:return None
    scale=None if au==unit else _conv(Fraction(1),unit,au)
    role=_ja_role(q);subj=_ja_subject(q)
    def done(r,v,expr,target):return _answer(r,v,expr,model,target,query,au,scale)
    def verb_hits(text):
        k,cls,vb=_match_verb(text)
        if k in (None,'AMBIG'):return []
        return [e for e in model.events if _lemma(e['verb'])==_lemma(vb) and e['lex']==k]
    # the holding the question is about
    target=model.main;ctx['role']=role
    if subj:
        hs=[k for k in model.hold if k[0]==subj];os_=[k for k in model.hold if k[1]==subj and k[0]==model.main[0]]
        if subj in (model.main[0],model.main[1]):target=model.main
        elif hs and not os_:
            same=[k for k in hs if k[1]==model.main[1]]
            if same:target=same[0]
            elif len(hs)==1:target=hs[0]
            else:_refuse('SITUATION_AMBIGUOUS_TARGET')
        elif os_ and not hs:target=os_[0]
        elif role!='event':_refuse('SITUATION_UNKNOWN_TARGET')
    if role=='holding' and target==model.main:role='remain';ctx['role']=role
    if role=='initial':
        v=model.initial.get(target);return done('initial',v,_fmt(v) if v is not None else '',target)
    if role=='before':
        bm=re.search(r'([^、。\d]{1,6}?)前(?:は|に|には)',q)
        k,cls,vb=_match_verb(bm[1])
        if k is None or k=='AMBIG':_refuse('SITUATION_UNKNOWN_BEFORE_EVENT')
        for i,e in enumerate(model.events):
            if _lemma(e['verb'])==_lemma(vb) and e['lex']==k:
                expr,v=model.chain(target,i)
                return done('before',v,expr or '',target)
        _refuse('SITUATION_EVENT_NOT_IN_STORY')
    if role=='event':
        nom=re.search(r'(?:([^、。\d]{1,8}?)(?:に|へ|から))?([^、。\d何]{1,8}?)(?:た|だ)(?:の|数|分)(?:は|が)',q)
        if nom:
            hits=verb_hits(nom[2]);other=_name(nom[1]) if nom[1] else None
            if other is not None:hits=[e for e in hits if e.get('other')==other]
            return _sum_events('event',hits,model,[nom[2],other or ''],query,au,scale)
        ask=_ask_verb(q)
        k,cls,vb=_match_verb(ask[1])
        if k in (None,'AMBIG'):_refuse('SITUATION_UNKNOWN_QUESTION_VERB')
        if subj and subj not in (model.main[0],model.main[1]):
            if k=='receive':
                hits=[e for e in model.events if e['kind']=='give' and e.get('other')==subj]+[e for e in model.events if e['kind']=='receive' and e['holder']==subj]
                return _sum_events('received',hits,model,[subj,'receive'],query,au,scale)
            hits=[e for e in verb_hits(ask[1]) if e['holder']==subj]
        else:hits=verb_hits(ask[1])
        return _sum_events('event',hits,model,[ask[1],''],query,au,scale)
    present=re.search(r'残り|残って|残った|のこり|のこって|今|いま|現在|になりました|になった|になります|になる|になって|ありますか|いますか|持っていますか|もっていますか|乗っていますか|入っていますか|残りますか|ですか|でしょうか|か$|全部で|ぜんぶで|合わせて|あわせて|合計',q) or \
        re.search(r'(?:何\s*(?:'+CNT+r')|いくつ|いくら)\s*(?:ですか)?[？?]?$',q)
    past_only=re.search(r'(?:あり|い|持ってい|乗ってい|入ってい)ましたか',q) and not re.search(r'残|今|いま|現在|なりました',q)
    if role=='total' and len(model.order)>1 and not subj:
        parts=[model.chain(k) for k in model.order]
        if any(v is None for _,v in parts):_refuse('SITUATION_TARGET_NOT_DETERMINED')
        return done('total',sum(v for _,v in parts),'+'.join('('+e+')' for e,_ in parts),['*','*'])
    if past_only or not present:ctx['role']='time_unclear';_refuse('SITUATION_TIME_OF_QUESTION_UNCLEAR')
    if not subj and len(model.order)>1:_refuse('SITUATION_AMBIGUOUS_TARGET')
    if any(e['cls']=='activity' for e in model.events if (e['holder'],e['object'])==target):_refuse('SITUATION_ACTIVITY_EFFECT_UNKNOWN')
    expr,v=model.chain(target)
    return done('remain' if target==model.main else 'holding',v,expr or '',target)

def _ja(t,query):
    t=re.sub(r'\s+','',t)
    if len(t)>300 or not QTY.search(t):return None
    sents=[x for x in re.findall(r'[^。？?！!]+[。？?！!]?',t) if x.strip('。？?！!')]
    qi=[i for i,x in enumerate(sents) if QWORD_JA.search(x)]
    if len(qi)!=1 or qi[0]!=len(sents)-1 or len(sents)<2:return None
    q=sents[-1];body=sents[:-1]
    # 「二人合わせて」 is normalized to 2人合わせて: a total marker in the question, not an amount
    # another person's or another place's stock (「別の人が別の在庫から」) is not this model's case
    if OTHER_JA.search(LABEL.sub('#',t)) or SCOPE_JA.search(t) or re.search(r'\d',re.sub(r'[2-9]人(?:合わせて|あわせて|で|の合計|とも)','',q)) or '入り' in t and not PKG.search(t):return None
    ctx={'role':_ja_role(q)}
    try:
        if NEG_JA.search(q) and not NEG_JA.search(''.join(body)):return None
        if HEDGE_JA.search(''.join(body)) or HEDGE_JA.search(re.sub(r'たら|と(?=[何いど])','',q)) or NEG_JA.search(t):
            _refuse('SITUATION_HEDGED_OR_NEGATED')
        b=_ja_build(body,query)
        if not b:return None
        ctx['holdings']=max(len(b[0].order),len({k[1] for k in b[0].hold}))
        return _ja_query(*b,q,query,ctx)
    except Refuse as e:return {'refused':str(e),'role':ctx['role'],'holdings':ctx.get('holdings',1)}

# ----------------------------------------------------------------------------- English
AMBIG_EN=r'sold|sells|sell|lent|lends|lend|borrowed|borrows|borrow|lost|loses|lose|returned|returns|return|donated|donates|traded|trades|shipped|ships|caught|catches|moved|moves|sent|sends|took|takes'
GIVE_EN=r'gave|gives|give|handed|hands'
VERBS_EN=[(r'ate|eats|eat|used|uses|use|spent|spends|spend|drank|drinks|drink|broke|breaks|threw away|throws away|cut off|cuts off|paid|pays|popped|pops|gave away|gives away','out','consume'),
          (r'got|gets|get|received|receives|receive','receive','receive'),
          (r'bought|buys|buy|found|finds|find|picked|picks|collected|collects|won|wins|win|made|makes|make|baked|bakes|bake|grew|grows|earned|earns|added|adds','in','gain'),
          (r'read|reads|wrote|writes|saw|sees|counted|counts|solved|solves','none','activity')]
LEAVE_EN=r'flew away|fly away|flies away|left|leave|leaves|went home|go home|goes home|got off|get off|gets off|ran away|run away|runs away|swam away|walked away|went away'
ARRIVE_EN=r'came back|came|come|comes|arrived|arrive|arrives|joined|join|joins|got on|get on|gets on|flew in|landed|land|lands'
PRON=('he','she','they')
STOP_EN={'there','then','how','the','a','an','on','in','at','after','later','next','today','yesterday','his','her','their','first','finally','now','he','she','they',
         'it','what','if','each','every','some','one','two','mom','dad','monday','tuesday','wednesday','thursday','friday','saturday','sunday'}

def _en_role(q):
    low=q.lower()
    if re.search(r'\bat first\b|\bin the beginning\b|\bto (?:begin|start) with\b|\boriginally\b|\bat the start\b',low):return 'initial'
    if re.search(r'\b(?:did|does|do)\s+\w+\s+(?:'+GIVE_EN+'|'+'|'.join(p for p,_,_ in VERBS_EN)+r')\b',low) or re.search(r'\bhow many\s+(?:(?!are\b|is\b|were\b|was\b)\w+\s+)?(?:'+LEAVE_EN+'|'+ARRIVE_EN+r')\b',low):return 'event'
    m=re.match(r'how (?:many|much)(?:\s+\w+)?\s+(?:does|did|do)\s+([a-z]+)\s',low)
    if m and m[1] not in PRON:return 'holding'
    return 'remain'

def _en(text):
    s=re.sub(r'\$\s*(\d)',r'\1 dollars ',unicodedata.normalize('NFKC',str(text)).strip()).replace(',','')
    if len(s)>400:return None
    sents=[x.strip() for x in re.split(r'(?<=[.?!])\s+',s) if x.strip()]
    if len(sents)<2:return None
    q=sents[-1]
    if not re.match(r'(?i)how (?:many|much|long|tall)\b',q) or any(re.search(r'(?i)\bhow (?:many|much)\b',x) for x in sents[:-1]) or re.search(r'\d',q):return None
    low=s.lower();role=_en_role(q);ctx={}
    m=re.match(r'(?i)how (?:many|much)(?:\s+\w+)?\s+(?:does|did|do)\s+([A-Za-z]+)',q)
    if role=='holding' and m and sents[0].split()[0].lower()==m[1].lower():role='remain'
    if re.search(r"\b(?:not|never|no)\b|n't\b",low):return None
    if re.search(r'\b(?:each|every|per|times|twice|half|percent|average|more than|fewer than|less than|older|younger|taller than|shorter than|as many|rows?|bags? of|boxes? of)\b|%',low):return None
    try:
        if re.search(r'\b(?:some|several|a few|many of|about|around|approximately|maybe|might|will|plans?|if|probably)\b',low):_refuse('SITUATION_HEDGED_OR_UNKNOWN_AMOUNT')
        if re.search(r'\b(?:'+AMBIG_EN+r')\b',low):_refuse('SITUATION_AMBIGUOUS_VERB')
        b=_en_build(sents)
        if not b:return None
        ctx['holdings']=max(len(b[0].order),len({k[1] for k in b[0].hold}))
        return _en_query(*b,q,text)
    except Refuse as e:return {'refused':str(e),'role':role,'holdings':ctx.get('holdings',1)}

def _en_build(sents):
    model=Model();seen=[];unit=None
    for x in sents[:-1]:
        clauses=[re.sub(r'(?i)^(?:and then|then|after that|later|next|and)\s+','',c.strip()) for c in re.split(r',?\s+(?:and then|then|and|but)\s+|,\s*',x.rstrip('.!')) if c and c.strip()]
        subj=None;used=0;last=None
        for c in clauses:
            words=c.split();first=words[0] if words else ''
            fl=first.lower()
            if fl in PRON:
                if len(seen)!=1:_refuse('SITUATION_PRONOUN_AMBIGUOUS')
                subj=seen[0]
            elif first[:1].isupper() and fl not in STOP_EN and not first.isdigit():
                subj=first
                if subj not in seen:seen.append(subj)
            for m in re.finditer(r'\b([A-Z][a-z]+)\b',c):
                if m[1].lower() not in STOP_EN and m[1] not in seen and m.start()>0:seen.append(m[1])
            low=c.lower();nums=list(re.finditer(r'\d+(?:\.\d+)?',low))
            if not nums:continue
            if len(nums)>1:_refuse('SITUATION_TWO_AMOUNTS_IN_CLAUSE')
            n=nums[0];val=Fraction(n.group());before=low[:n.start()].strip();after=low[n.end():].strip();model.given.append(val)
            nm=re.match(r'(?:more\s+)?([a-z]+)',after);noun=nm[1] if nm else None
            if noun in ('to','from','more','on','in','of','for','with','and'):noun=None
            u=noun if noun in ('cm','m','km','kg','g','meters','centimeters','dollars','dollar','cents','cent','yen') else 'items'
            used+=1
            # states: Mia had 20 pencils / There were 30 birds in a tree / A ribbon is 50 cm long
            st=re.search(r'\b(?:has|had|have|owns|owned)$',before) or re.match(r'there (?:are|were|is|was)$',before)
            ln=re.match(r'(?:the |a |an |her |his )?([a-z]+) is$',before) if re.match(r'(?:cm|m|km|meters|centimeters) (?:long|tall)',after) else None
            if st or ln:
                if ln:holder=ln[1];obj=u
                elif subj and not before.startswith('there'):holder=subj;obj=noun if u=='items' else u
                else:
                    pl=re.search(r'\b(?:in|on|at) (?:the |a |an |his |her )?([a-z]+)',after);holder=pl[1] if pl else 'there';obj=noun if u=='items' else u
                if obj is None:_refuse('SITUATION_OBJECT_MISSING')
                if unit is not None and (u!='items')!=(unit!='items'):_refuse('SITUATION_UNIT_MISMATCH')
                unit=unit or u;model.state(holder,obj,val);continue
            if model.main is None:return None
            verb=kind=cls=None;other=None
            lv=re.match(r'(?:more\s+)?(?:[a-z]+\s+)?('+LEAVE_EN+r')\b',after);av=re.match(r'(?:more\s+)?(?:[a-z]+\s+)?('+ARRIVE_EN+r')\b',after)
            gv=re.search(r'\b('+GIVE_EN+r')(?:\s+([a-z]+))?$',before)
            if lv and not before:verb,kind,cls=lv[1],'out','leave'
            elif av and not before:verb,kind,cls=av[1],'in','arrive'
            elif gv and not re.search(r'\baway$',before):
                verb,kind,cls='give','give','give'
                to=re.search(r'\bto\s+((?:her|his|their|a)\s+)?([a-z]+)',after)
                if gv[2] and gv[2] not in ('away',):other=gv[2].capitalize()
                elif to:other=(to[1] or '')+to[2] if to[1] else to[2].capitalize()
                else:kind='out'
            else:
                for pat,k,cl in VERBS_EN:
                    vm=re.search(r'\b('+pat+r')$',before)
                    if vm:verb,kind,cls=vm[1],k,cl;break
                if verb and kind=='receive':
                    fr=re.search(r'\bfrom\s+((?:her|his|their|a)\s+)?([a-z]+)',after)
                    if fr:other=(fr[1] or '')+fr[2] if fr[1] else fr[2].capitalize()
            if verb is None and last and re.match(r'(?:\w+\s+)?(?:to|from)\s+\w+$|$',after if not before else '#') and not before:
                verb,kind,cls=last['verb'],last['lex'],last['cls']           # 「gave 8 to Joe and 5 to Amy」: the verb is shared
                if kind=='give':
                    to=re.search(r'\bto\s+((?:her|his|their|a)\s+)?([a-z]+)',after);other=((to[1] or '')+to[2] if to[1] else to[2].capitalize()) if to else None
                    if other is None:kind='out'
            if verb is None:_refuse('SITUATION_UNKNOWN_EVENT')
            holder=subj if subj and any(k[0]==subj for k in model.hold) else None
            if holder is None:
                if subj and len(model.order)>1:_refuse('SITUATION_UNKNOWN_ACTOR')
                holder=model.main[0]
            objs={k[1] for k in model.hold if k[0]==holder and model.initial.get(k) is not None}
            if u!='items':obj=u
            elif noun and noun in objs:obj=noun
            elif noun and (noun.rstrip('s') in {o.rstrip('s') for o in objs}):obj=next(o for o in objs if o.rstrip('s')==noun.rstrip('s'))
            elif len(objs)==1:obj=next(iter(objs))
            else:_refuse('SITUATION_AMBIGUOUS_OBJECT')
            if (holder,obj) not in model.hold:_refuse('SITUATION_AMBIGUOUS_OBJECT')
            last={'verb':verb,'lex':'give' if cls=='give' else kind,'cls':cls}
            model.apply({'holder':holder,'object':obj,'kind':kind,'quantity':val,'other':other,'verb':verb,'cls':cls,'lex':last['lex']})
    if model.main is None:return None
    return model,seen

def _en_query(model,names,q,query):
    low=q.lower().rstrip('?').strip()
    role=_en_role(q)
    def done(r,v,expr,target):return _answer(r,v,expr,model,target,query,'')
    lm=re.match(r'how (?:long|tall) is (?:the |her |his )?([a-z]+)(?: now)?$',low)
    if lm:
        ks=[k for k in model.hold if k[0]==lm[1]]
        if len(ks)!=1:_refuse('SITUATION_UNKNOWN_TARGET')
        expr,v=model.chain(ks[0]);return done('remain' if ks[0]==model.main else 'holding',v,expr or '',ks[0])
    pm=re.match(r'how (?:many|much)(?:\s+([a-z]+))?\s+(?:(?:does|did|do|are|were|is|was)\s+)?(.*)$',low)
    if not pm:return None
    noun,rest=pm[1],pm[2]
    subj=None;tail=rest
    w=re.match(r'([a-z]+)\s*(.*)$',rest)
    if w and (w[1].capitalize() in names or w[1] in PRON):
        if w[1]=='they':
            if len(model.order)<2 or not re.search(r'\bin all\b|\baltogether\b|\bin total\b|\btogether\b',low):_refuse('SITUATION_PRONOUN_AMBIGUOUS')
            parts=[model.chain(k) for k in model.order]
            if any(v is None for _,v in parts):_refuse('SITUATION_TARGET_NOT_DETERMINED')
            return done('total',sum(v for _,v in parts),'+'.join('('+e+')' for e,_ in parts),['*','*'])
        if w[1] in PRON:
            holders=sorted({h for h,_ in model.order if h in names})
            if len(holders)!=1:_refuse('SITUATION_PRONOUN_AMBIGUOUS')
            subj=holders[0]
        else:subj=w[1].capitalize()
        tail=w[2]
    if role=='event':
        cands=[(LEAVE_EN,'out','leave'),(ARRIVE_EN,'in','arrive'),(GIVE_EN,'give','give')]+VERBS_EN
        for pat,k,cl in cands:
            vm=re.search(r'\b('+pat+r')\b',tail)
            if not vm:continue
            hits=[e for e in model.events if e['cls']==cl and (cl in ('leave','arrive','give') or e['verb'][:3]==vm[1][:3])]
            if subj:hits=[e for e in hits if e['holder']==subj]
            to=re.search(r'\b(?:to|from)\s+((?:her|his|their|a)\s+)?([a-z]+)',tail)
            if to:hits=[e for e in hits if (e.get('other') or '').lower()==((to[1] or '')+to[2]).lower()]
            return _sum_events('event',hits,model,[vm[1],''],query,'')
        _refuse('SITUATION_UNKNOWN_QUESTION_VERB')
    if subj:
        ks=[k for k in model.hold if k[0]==subj]
        if noun:ks=[k for k in ks if k[1]==noun or k[1].rstrip('s')==noun.rstrip('s') or noun in ('money',) and k[1] in ('dollars','cents','yen')] or ks
        if not ks:_refuse('SITUATION_UNKNOWN_TARGET')
        if len(ks)!=1:_refuse('SITUATION_AMBIGUOUS_TARGET')
        target=ks[0];when=re.sub(r'^(?:have|has|had)\b','',tail)
        if not re.match(r'(?:have|has|had)\b',tail):_refuse('SITUATION_UNKNOWN_QUESTION_VERB')
    else:
        if not re.match(r'(?:there|left)\b',rest):_refuse('SITUATION_UNKNOWN_QUESTION_VERB')
        target=model.main;when=rest
    if role=='initial':
        v=model.initial.get(target);return done('initial',v,_fmt(v) if v is not None else '',target)
    if not re.search(r'\bnow\b|\bleft\b|\bremain|\bin all\b|\baltogether\b|\bin total\b|^\s*(?:there|left)?\s*$',when):_refuse('SITUATION_TIME_OF_QUESTION_UNCLEAR')
    if re.search(r'\bin all\b|\baltogether\b|\bin total\b',when) and len(model.order)>1 and not subj:
        parts=[model.chain(k) for k in model.order]
        if any(v is None for _,v in parts):_refuse('SITUATION_TARGET_NOT_DETERMINED')
        return done('total',sum(v for _,v in parts),'+'.join('('+e+')' for e,_ in parts),['*','*'])
    if not subj and len(model.order)>1:_refuse('SITUATION_AMBIGUOUS_TARGET')
    if any(e['cls']=='activity' for e in model.events if (e['holder'],e['object'])==target):_refuse('SITUATION_ACTIVITY_EFFECT_UNKNOWN')
    expr,v=model.chain(target)
    return done('remain' if target==model.main else 'holding',v,expr or '',target)

# ----------------------------------------------------------------------------- entry points
JA=re.compile(r'[぀-ヿ一-鿿]')
def solve(query):
    try:
        t=_norm(query)
        return _ja(t,query) if JA.search(t) else _en(query)
    except (ValueError,ZeroDivisionError,KeyError,IndexError,TypeError,AttributeError):
        return None

def check(proof,answer):
    """proofs.check hook: re-read the question and compare the whole derivation"""
    r=solve(proof.get('source_query',''))
    if not r or 'answer' not in r:return False
    p=r['proof']
    return all(p.get(k)==proof.get(k) for k in ('role','target','expression','answer','events','initial','unit')) and r['answer']==str(answer)
