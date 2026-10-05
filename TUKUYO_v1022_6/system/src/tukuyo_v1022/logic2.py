"""claude-patch2: bounded logic with COMPLETE model checking.

Premises are parsed into propositional atoms (conditionals, negation, universals grounded over the
named individuals, disjunctions) or into a strict order (comparisons). The verdict is then computed
by enumerating every truth assignment, so within the parsed formalisation it is sound AND complete:
"yes" / "no" / "undetermined" / "contradiction". proofs.check recomputes it independently.

What can still go wrong is the PARSE (Japanese/English -> atoms). Guards: hedged or causal language
is refused, every sentence must parse, inflected predicates that collapse to the same stem in an
incompatible way are refused, and atoms not connected to anything are reported as `orphans` so that
callers never present "undetermined" as an answer when a premise may have been misread.
"""
from __future__ import annotations
import itertools,re,unicodedata

MAX_ATOMS=16
GUARD=re.compile(r'ことが多|ことも多|場合が多|ことが少な|相関|原因|かもしれ|だろう|らしい|多分|たぶん|おそらく|恐らく|可能性|ほとんど|たいてい|大抵|一部|いくつか|ことがある|場合がある|場合もある|時々|ときどき|しばしば|でしょう|と思う|と言|と聞|夢|想像|嘘|うそ|だけ|のみ|しか|以外|例えば|たとえば|もしかし|'
                 r'\bprobabl|\bmaybe\b|\bmight\b|\bmay\b|\bsome\b|\bmost\b|\busually\b|\boften\b|\bsometimes\b|\bonly\b|\bunless\b|\bexcept\b|\bsaid\b|\bheard\b|\bdream|\bperhaps\b|\blikely\b',re.I)
WH=re.compile(r'何|誰|だれ|どこ|いつ|なぜ|どうして|どの|いくつ|いくら|\bwhat\b|\bwhere\b|\bwhen\b|\bwhy\b|\bhow\b',re.I)
TOPIC={'今日','今','いま','現在','外','今朝','今夜','今晩','本日','ここ','きょう','today','now',
       '明日','あした','あす','昨日','きのう','今週','来週','先週','週末','放課後'}          # claude-patch6: time topics
TIME_HEAD=re.compile(r'^(?:もし)?(?:明日|あした|あす|昨日|きのう|今日|きょう|今朝|今夜|今晩|週末|放課後)(?:に|は|も)?[、,]?')
OCCUR=r'(?:降って(?:いる|います)|降った|降りました|降る|降ります|吹いて(?:いる|います)|吹いた|吹く|起きて(?:いる|います)|起きた|起こって(?:いる|います)|起こった|発生して(?:いる|います)|発生した|来て(?:いる|います)|来た|続いて(?:いる|います)|続いた)'
NEG=re.compile(r'(?:ではない|じゃない|ではありません|じゃありません|ではなかった|じゃなかった|でない|ていない|ていません|ていなかった|てない|なかった|ません|ませんでした|ない|ず)$')
NOT_NEG=('少ない','危ない','切ない','はかない','せわしない','幼い')
COP=re.compile(r'(?:でしょうか|ですか|でした|だった|である|です|だ|か|の)$')
ROWS={}
for row,chars in {'a':'あいうえお','k':'かきくけこ','g':'がぎぐげご','s':'さしすせそ','z':'ざじずぜぞ','t':'たちつてと','d':'だぢづでど','n':'なにぬねの',
                  'h':'はひふへほ','b':'ばびぶべぼ','p':'ぱぴぷぺぽ','m':'まみむめも','y':'やゆよ','r':'らりるれろ','w':'わを'}.items():
    for ch in chars:ROWS[ch]={row}
ROWS.update({'っ':{'r','t','a','w'},'ん':{'m','n','b'},'い':{'a','k','g'},'う':{'a','w'}})
EBA={'え':'う','け':'く','げ':'ぐ','せ':'す','て':'つ','ね':'ぬ','べ':'ぶ','め':'む','れ':'る'}
JA=re.compile(r'[぀-ヿ一-鿿]')

class Refuse(Exception):pass

def _sentences(s):
    parts=[p.strip() for p in re.findall(r'[^。．!！?？.]+(?:[。．!！?？]|\.(?!\d)|$)',s) if p.strip(' 。．.')]
    return parts

# ---------------------------------------------------------------- atoms
def _tail_core(x):
    """claude-patch3: ichidan inflections attach straight to the stem (着る/着た/着ない): strip them before
    comparing consonant rows, so they are not mistaken for a different verb."""
    prev=None
    while x and x!=prev:
        prev=x;x=re.sub(r'(?:ていない|ていた|ています|ている|ました|ません|ます|なかった|ない|た|て|る|です|だ)$','',x)
    return x
class Atoms:
    def __init__(self):self.keys=[];self.surface={};self.tails={};self.subjects=set();self.classes={}
    def add(self,key,surface,tail=''):
        if key not in self.keys:
            self.keys.append(key)
            if len(self.keys)>MAX_ATOMS:raise Refuse('TOO_MANY_ATOMS')
        self.surface.setdefault(key,surface)
        if tail is not None:
            t=self.tails.setdefault(key,set());t.add(tail)
            cores=[_tail_core(x) for x in t]
            # claude-patch4: 走れる/書ける/見られる are ability or voice, not the event 走る/書く/見る happening
            erow=[c for c in cores if re.search(r'(?:られ|させ|され)$|^[えけげせてねべめれ]$',c)]
            if erow and any(c not in erow for c in cores):raise Refuse('POTENTIAL_OR_VOICE_FORM')
            rows=[ROWS.get(c[:1],{'*'}) if c else {'*'} for c in cores]
            for a in rows:
                for b in rows:
                    if '*' not in a and '*' not in b and not (a&b):raise Refuse('STEM_COLLISION')
        return self.keys.index(key)

IROW={'し':'す','き':'く','ち':'つ','に':'ぬ','び':'ぶ','み':'む','り':'る','ぎ':'ぐ'}
def _ja_stem(p):
    p=re.sub(r'[\s、,]','',p);p=COP.sub('',p)
    m=re.match(r'^(.*?[^぀-ゟ])([぀-ゟ]*)$',p)
    if m:return (m[1],m[2])
    # claude-patch3: all-hiragana predicates: さす/さし, つける/つけ, する/し are one atom
    if p in ('する','し','して','した','します'):return ('する','')
    if len(p)>2 and p.endswith('る'):p=p[:-1]
    if len(p)>=2 and p[-1] in IROW:p=p[:-1]+IROW[p[-1]]
    return (p,'')

def _ja_polarity(c):
    c=COP.sub('',c.strip())
    if c.endswith(NOT_NEG):return c,True
    m=NEG.search(c)
    if m and len(c)>len(m.group()):return c[:m.start()],False
    return c,True

def _ja_atom(c,atoms,keep_subject=True):
    """clause -> (atom index, polarity). Subject topic is kept unless it is a time/place topic."""
    raw=c.strip();body,pol=_ja_polarity(raw)
    if not re.match(r'^[^はが]{1,15}?(?:は|が)',TIME_HEAD.sub('',body)) or TIME_HEAD.match(body):body=TIME_HEAD.sub('',body) or body
    m=re.match(r'^(.{1,15}?)(?:は|が)(.+)$',body) or re.match(r'^(.{1,10}?)を(.+)$',body)   # claude-patch3: 「傘をさす」 = topic 傘
    subj,pred=(m[1],m[2]) if m else ('',body)
    # Removing a negative ending leaves e.g. 降ら / 降っ.  Keep these
    # known event inflections on the same atom as 降る / 降っている.
    negative_occurrence={'降ら','降り','降っ','吹か','吹き','吹い','起き','起こら','起こっ','発生し','来','続か','続き','続い'}
    if subj and (re.fullmatch(OCCUR,pred) or not pol and pred in negative_occurrence):subj,pred='',subj
    elif not subj and re.search(OCCUR+'$',pred):
        mm=re.match(r'^(.+?)(?:が|は)?'+OCCUR+'$',pred)
        if mm:pred=mm[1]
    if subj in TOPIC:subj=''
    stem,tail=_ja_stem(pred)
    if not stem:raise Refuse('EMPTY_PREDICATE')
    key=(subj+'|' if subj else '|')+stem
    if subj:atoms.subjects.add(subj)
    return atoms.add(key,raw,tail),pol

EN_IRR={'won':'win','ate':'eat','went':'go','saw':'see','came':'come','ran':'run','made':'make','took':'take','gave':'give','got':'get','built':'build','found':'find',
        'wrote':'write','drew':'draw','began':'begin','flew':'fly','left':'leave','bought':'buy','sold':'sell','held':'hold','grew':'grow','knew':'know','met':'meet',
        'paid':'pay','said':'say','sent':'send','sat':'sit','slept':'sleep','spoke':'speak','stood':'stand','taught':'teach','told':'tell','thought':'think',
        'threw':'throw','wore':'wear','lost':'lose','fell':'fall','felt':'feel','kept':'keep','swam':'swim','sang':'sing','drank':'drink','drove':'drive','rode':'ride','broke':'break','chose':'choose','forgot':'forget','had':'have','did':'do'}
def _en_word(w):
    w=EN_IRR.get(w,w)
    if w.endswith('ied') and len(w)>4:w=w[:-3]+'y'
    elif w.endswith('ed') and len(w)>4:
        w=w[:-2]
        if len(w)>2 and w[-1]==w[-2] and w[-1] not in 'sl':w=w[:-1]
    if w.endswith('ies') and len(w)>4:w=w[:-3]+'y'
    elif w.endswith('s') and not w.endswith('ss') and len(w)>3:w=w[:-1]
    if w.endswith('e') and len(w)>3:w=w[:-1]
    return w
EN_DROP={'the','a','an','does','do','did','is','are','was','were','then','it','that','true'}
def _en_atom(c,atoms):
    c=c.lower().strip(' .?!');pol=True
    c=re.sub(r'\b(?:gets|get|got|becomes|become|became|feels|feel|felt)\s+(?=[a-z]+$)','is ',c)   # claude-patch6: change of state = the state
    mq=re.fullmatch(r'(can|could|will|would|may|must|should) (?:(?:a|an|the) )?(\w+) (.+)',c)
    if mq:c=f'{mq[2]} {mq[1]} {mq[3]}'                 # claude-patch4: "can a salmon fly" -> "salmon can fly"
    if re.search(r"\b(?:not|never)\b|n't\b",c):pol=False;c=re.sub(r"\b(?:not|never)\b|n't\b",' ',c)
    m=re.fullmatch(r'(?:is\s+)?(\w+)\s+(?:is|are|was)?\s*(?:a|an)?\s*(\w+)',c) if re.search(r'\bis\b|\bare\b',c) else None
    words=[w for w in re.findall(r"[a-z]+",c) if w not in EN_DROP]
    if not words:raise Refuse('EMPTY_PREDICATE')
    if m and len(words)==2:
        subj,pred=words[0],_en_word(words[1])
    elif words[0] in atoms.subjects and len(words)>1:
        subj,pred=words[0],' '.join(_en_word(w) for w in words[1:])
    else:
        subj,pred='',' '.join(_en_word(w) for w in words)
    if subj:atoms.subjects.add(subj)
    return atoms.add((subj+'|' if subj else '|')+pred,c,None),pol

# ---------------------------------------------------------------- model checking
def _models(n,clauses):
    for bits in itertools.product((False,True),repeat=n):
        if all(any(bits[i]==p for i,p in cl) for cl in clauses):yield bits

def verdict(n,clauses,query):
    """query: list of (atom,pol) conjunction. Returns yes/no/undetermined/contradiction."""
    seen_t=seen_f=False;any_model=False
    for bits in _models(n,clauses):
        any_model=True
        v=all(bits[i]==p for i,p in query)
        seen_t|=v;seen_f|=not v
        if seen_t and seen_f:return 'undetermined'
    if not any_model:return 'contradiction'
    return 'yes' if seen_t else 'no'

def order_verdict(nodes,edges,query):
    closure={(a,b) for a,b in edges}
    for _ in range(len(nodes)+1):
        closure|={(a,d) for a,b in closure for c,d in closure if b==c}
    if any(a==b for a,b in closure):return 'contradiction',None
    t=query['type']
    if t in ('yesno','which'):
        a,b=query['a'],query['b']
        if (a,b) in closure:return ('yes' if t=='yesno' else 'a'),a
        if (b,a) in closure:return ('no' if t=='yesno' else 'b'),b
        return 'undetermined',None
    if t=='max':
        tops=[x for x in nodes if all((x,y) in closure for y in nodes if y!=x)]
        return ('max',tops[0]) if len(tops)==1 else ('undetermined',None)
    if t=='min':
        lows=[x for x in nodes if all((y,x) in closure for y in nodes if y!=x)]
        return ('max',lows[0]) if len(lows)==1 else ('undetermined',None)
    if t=='which_low':
        a,b=query['a'],query['b']
        if (a,b) in closure:return 'b',b
        if (b,a) in closure:return 'a',a
        return 'undetermined',None
    raise ValueError('ORDER_QUERY')

# ---------------------------------------------------------------- parsing
def _cond_ja(c):
    m=re.match(r'^(?:もし)?(.+?)(ならば|なら|であれば|ければ|[えけげせてねべめれ]ば|たら|だら)[、,]?\s*(.+)$',c)
    if not m:
        # claude-patch3: 「雨が降ると傘をさす」 (dictionary-form verb + と) as a conditional
        m2=re.match(r'^(.+?[うくぐすつぬぶむる])と[、,]?\s*(.+)$',c)
        if m2 and re.search(r'[はがを]',m2[1]):return m2[1],m2[2]
        return None
    a,mk,b=m[1],m[2],m[3]
    if mk=='ければ':a+='ける' if 'を' in a else 'い'     # claude-patch4: 「窓を開ければ」 is the verb 開ける, not an adjective
    elif mk.endswith('ば') and mk[0] in EBA and mk not in ('ならば','であれば'):a+=EBA[mk[0]]
    elif mk=='たら':a+='た'
    elif mk=='だら':a+='だ'
    return a,b

def _parse(s):
    lang='ja' if JA.search(s) else 'en'
    sents=_sentences(s)
    if len(sents)>64:raise Refuse('LOGIC_SENTENCE_LIMIT')
    if len(sents)<2:return None
    q=sents[-1]
    if not re.search(r'[?？]$',q) and not (lang=='en' and re.match(r'(?:is|does|do|did|are|who|which|can)\b',q.lower())):return None
    body=sents[:-1]
    if any(re.search(r'[?？]$',x) for x in body):return None
    if GUARD.search(s):raise Refuse('HEDGED_OR_CAUSAL_LANGUAGE')
    q=q.rstrip('?？。. ')
    return lang,[x.rstrip('。．.!！ ') for x in body],q

ANT_JA=[('年上','年下'),('高い','低い'),('背が高い','背が低い'),('大きい','小さい'),('重い','軽い'),('速い','遅い'),('長い','短い'),('強い','弱い'),('多い','少ない'),
        ('遠い','近い'),('明るい','暗い'),('広い','狭い'),('古い','新しい'),('早い','遅い'),('暑い','寒い'),('深い','浅い'),('太い','細い'),('厚い','薄い'),('高価','安価'),('高い','安い')]
ANT_EN=[('old','young'),('tall','short'),('big','small'),('larg','small'),('heavi','light'),('fast','slow'),('long','short'),('strong','weak'),('high','low'),('rich','poor'),
        ('old','new'),('hot','cold'),('warm','cool'),('near','far'),('expensive','cheap'),('wid','narrow'),('deep','shallow'),('bright','dark'),('earli','lat'),('good','bad')]
def _antonym(x,y,lang):
    return (x,y) in (ANT_JA if lang=='ja' else ANT_EN) or (y,x) in (ANT_JA if lang=='ja' else ANT_EN)
def _qflip(qp,p,lang,query):
    """query asked with predicate qp about an order stored under p"""
    if qp==p:return query
    if not _antonym(qp,p,lang):return None
    t=query['type']
    if t=='max':return {'type':'min'}
    if t=='which':return {'type':'which_low','a':query['a'],'b':query['b']}
    if t=='yesno':return {'type':'yesno','a':query['b'],'b':query['a']}
    return None
def _order(lang,body,q):
    edges=[];preds=set();nodes=[];raw=[]
    def node(x):
        x=x.strip()
        if not x or len(x)>15 or re.search(r'[はがをにのと、 ]',x) and lang=='ja':raise Refuse('ORDER_NODE')
        if x not in nodes:nodes.append(x)
        if len(nodes)>32:raise Refuse('ORDER_NODE_LIMIT')
        return x
    for c in body:
        if lang=='ja':m=re.fullmatch(r'(.+?)は(.+?)より(?:も)?(.+?)(?:です|だ|である)?',c)
        else:
            m=re.fullmatch(r'(\w+) (?:is|are) (?:more (\w+)|(\w+?)(?:er|r)) than (\w+)',c.lower())
            if m:m=(None,m[1],m[4],m[2] or m[3])
        if not m:return None
        a,b,p=(m[1],m[2],m[3])
        if lang=='ja':p=COP.sub('',p)
        raw.append((node(a),node(b),p))
    # claude-patch3: antonyms are the same order read backwards (年下 = reversed 年上, younger = reversed older)
    p=raw[0][2]
    for a,b,pp in raw:
        if pp==p:edges.append((a,b))
        elif _antonym(pp,p,lang):edges.append((b,a))
        else:raise Refuse('ORDER_MIXED_PREDICATES')
    preds={p}
    if order_verdict(nodes,edges,{'type':'max'})[0]=='contradiction':return nodes,edges,p,{'type':'max'}
    if lang=='ja':
        m=re.fullmatch(r'(.+?)と(.+?)(?:では|は|で)?(?:どちら|どっち)が(?:より)?(.+?)(?:ですか|でしょうか|か)?',q)
        if m and _qflip(COP.sub('',m[3]),p,lang,{'type':'which','a':m[1],'b':m[2]}):return nodes,edges,COP.sub('',m[3]),_qflip(COP.sub('',m[3]),p,lang,{'type':'which','a':node(m[1]),'b':node(m[2])})
        m=re.fullmatch(r'(?:一番|いちばん|最も|もっとも)(.+?)(?:のは|なのは|人は|ものは|は)?(?:誰|だれ|どれ|何|なに|どこ)?(?:ですか|か)?',q)
        if m and _qflip(COP.sub('',m[1]),p,lang,{'type':'max'}):return nodes,edges,COP.sub('',m[1]),_qflip(COP.sub('',m[1]),p,lang,{'type':'max'})
        m=re.fullmatch(r'(.+?)は(.+?)より(?:も)?(.+?)(?:ですか|でしょうか|か)?',q)
        if m and _qflip(COP.sub('',m[3]),p,lang,{'type':'yesno','a':m[1],'b':m[2]}):return nodes,edges,COP.sub('',m[3]),_qflip(COP.sub('',m[3]),p,lang,{'type':'yesno','a':node(m[1]),'b':node(m[2])})
    else:
        ql=q.lower()
        m=re.fullmatch(r'who is (?:the )?(?:most (\w+)|(\w+?)(?:est|st))',ql)
        if m and _qflip(m[1] or m[2],p,lang,{'type':'max'}):return nodes,edges,m[1] or m[2],_qflip(m[1] or m[2],p,lang,{'type':'max'})
        m=re.fullmatch(r'is (\w+) (?:more (\w+)|(\w+?)(?:er|r)) than (\w+)',ql)
        if m and _qflip(m[2] or m[3],p,lang,{'type':'yesno','a':m[1],'b':m[4]}):return nodes,edges,m[2] or m[3],_qflip(m[2] or m[3],p,lang,{'type':'yesno','a':node(m[1]),'b':node(m[4])})
        m=re.fullmatch(r'(?:which|who) is (?:more (\w+)|(\w+?)(?:er|r)),? (\w+) or (\w+)',ql)
        if m and _qflip(m[1] or m[2],p,lang,{'type':'which','a':m[3],'b':m[4]}):return nodes,edges,m[1] or m[2],_qflip(m[1] or m[2],p,lang,{'type':'which','a':node(m[3]),'b':node(m[4])})
    raise Refuse('ORDER_QUERY_UNSUPPORTED')

PRON_SKIP={'if','the','a','an','all','no','either','every','each','who','which','is','does','do','did','can','was','were','are','then','it','he','she','they','we','you','i','some','not','yes'}
def _props(lang,body,q):
    if lang=='en':                                   # claude-patch3: he/she -> the only named person
        names=[]
        for t in body+[q]:
            for w in re.findall(r'\b[A-Z][a-z]+\b',t):
                if w.lower() not in PRON_SKIP and w not in names:names.append(w)
        if any(re.search(r'\b(?:he|she|him|her)\b',t,re.I) for t in body+[q]):
            if len(names)!=1:raise Refuse('PRONOUN_AMBIGUOUS')
            body=[re.sub(r'\b(?:he|she|him|her)\b',names[0],t,flags=re.I) for t in body];q=re.sub(r'\b(?:he|she|him|her)\b',names[0],q,flags=re.I)
    atoms=Atoms();rules=[];facts=[];universals=[];disj=[];used=set()
    atom=(lambda c:_ja_atom(c,atoms)) if lang=='ja' else (lambda c:_en_atom(c,atoms))
    pending=[]
    for c in body:                                   # pass 1: individuals named in is-a facts (English)
        if lang=='en':
            m=re.fullmatch(r'(?:a |an |the )?(\w+) is (?:not )?(?:a|an) (\w+)',c.lower())
            if m:atoms.subjects.add(m[1])
    for c in body:
        if lang=='ja':
            m=re.fullmatch(r'(?:すべての|全ての|全部の|あらゆる)(.+?)は(.+)',c) or re.fullmatch(r'どの(.+?)も(.+)',c) or re.fullmatch(r'(.+?)は(?:みな|みんな|皆)(.+)',c)
            if m:universals.append((m[1],m[2]));continue
            cd=_cond_ja(c)
            if cd:rules.append(cd);continue
            m=re.fullmatch(r'(.+?)か(.+?)の?(?:どちらか|いずれか)(?:一方)?(を|が|に)(.+)',c)
            if m:disj.append((m[1]+m[3]+m[4],m[2]+m[3]+m[4]));continue
            m=re.fullmatch(r'(.+?)か(.+?)(?:の)?(?:どちらか|いずれか)(?:です|だ|である)?',c)
            if m:disj.append((m[1],m[2]));continue
        else:
            cl=c.lower()
            m=re.fullmatch(r'(?:all|every|each) (\w+) (?:are|is) (?:a |an )?(.+)',cl) or re.fullmatch(r'(?:all|every|each) (\w+) (.+)',cl)
            if m:universals.append((m[1],m[2]));continue
            m=re.fullmatch(r'if (.+?),? then (.+)',cl) or re.fullmatch(r'if (.+?), (.+)',cl)
            if m:rules.append((m[1],m[2]));continue
            m=re.fullmatch(r'either (\w+) or (\w+) (\w.*)',cl)
            if m:
                disj.append((f'{m[1]} {m[3]}',f'{m[2]} {m[3]}'));continue
            m=re.fullmatch(r'either (.+?) or (.+)',cl)
            if m:disj.append((m[1],m[2]));continue
            m=re.fullmatch(r'no (\w+?)s? (?:does |do |is |are )?(.+)',cl)
            if m:universals.append((m[1],'not '+m[2]));continue
        facts.append(c)
    # facts first so subjects are known before universals are grounded
    clauses=[]
    for c in facts:
        i,p=atom(c);clauses.append([(i,p)]);used.add(i)
    for a,b in rules:
        ia,pa=atom(a);ib,pb=atom(b);clauses.append([(ia,not pa),(ib,pb)])
    dclauses=[]
    for a,b in disj:
        ia,pa=atom(a);ib,pb=atom(b);dclauses.append(((ia,pa),(ib,pb)))
    for cls,pred in universals:
        if lang=='en':cls=_en_word(cls)
        for subj in sorted(atoms.subjects):
            if lang=='ja':ia,pa=atom(f'{subj}は{cls}');ib,pb=atom(f'{subj}は{pred}')
            else:
                ia,pa=atom(f'{subj} is a {cls}');ib,pb=atom(f'{subj} {pred}')
            clauses.append([(ia,not pa),(ib,pb)])
    # claude-patch6: generic rules (no subject in either clause) are grounded like universals, after the question
    generic=[(a,b) for a,b in rules if lang=='ja' and not re.search(r'[はが]',a) and not re.search(r'[はが]',b)]
    # question
    derive=False
    if lang=='ja':
        m=re.fullmatch(r'(?:(.+?)は)?(?:どうなる|どうなります|どうする|どうします)(?:か)?',q)
        if m:
            derive=True;subj=(m[1] or '').strip();subj='' if subj in TOPIC else subj
        else:
            if WH.search(q):raise Refuse('WH_QUESTION_UNSUPPORTED')
            qq=re.sub(r'(?:と言える|といえる|と言えますか|と言えるか|ですか|でしょうか|か|の)$','',q)
            qi,qp=atom(qq)
    else:
        if WH.search(q) or re.match(r'(?:who|which)\b',q.lower()):raise Refuse('WH_QUESTION_UNSUPPORTED')
        qi,qp=atom(q)
    for a,b in generic:
        ka,kb=atoms.keys[atom(a)[0]],atoms.keys[atom(b)[0]]
        if not (ka.startswith('|') and kb.startswith('|')):continue
        for subj in sorted(atoms.subjects):
            if subj+ka in atoms.keys or subj+kb in atoms.keys:
                ia,pa=atom(f'{subj}は{a}');ib,pb=atom(f'{subj}は{b}');clauses.append([(ia,not pa),(ib,pb)])
    n=len(atoms.keys)
    connected=set()
    for cl in clauses+[[x,y] for x,y in dclauses]:
        if len(cl)>1:connected|={i for i,_ in cl}
    if derive:
        cands=[i for i in range(n) if i in connected and (not subj or atoms.keys[i].startswith(subj+'|')) and i not in used]
        if not cands:raise Refuse('NO_DERIVE_CANDIDATE')
        query={'type':'derive','candidates':cands,'subject':subj}
    else:
        if qi not in connected and qi not in used:raise Refuse('QUERY_ATOM_UNRELATED')
        query={'type':'yesno','lit':[qi,qp]}
    orphans=sorted(i for i in used if i not in connected and (derive or i!=query['lit'][0]))
    return atoms,clauses,dclauses,query,orphans

def _cnf_readings(clauses,dclauses):
    incl=clauses+[[a,b] for a,b in dclauses]
    excl=incl+[[(a[0],not a[1]),(b[0],not b[1])] for a,b in dclauses] if dclauses else None
    return incl,excl

def eval_props(n,incl,excl,query):
    def one(cnf):
        if query['type']=='yesno':return verdict(n,cnf,[tuple(query['lit'])])
        hits=[i for i in query['candidates'] if verdict(n,cnf,[(i,True)])=='yes']
        if verdict(n,cnf,[])=='contradiction':return 'contradiction'
        return f'derive:{hits[0]}' if len(hits)==1 else 'undetermined'
    v=one(incl)
    if excl is not None and one(excl)!=v:return 'ambiguous'
    return v

def _en_statement(q):
    q=q.strip(' ?.')
    m=re.fullmatch(r'(is|are|was|were|can) (\w+) (.+)',q,re.I)
    if m:return f'{m[2].capitalize()} {m[1].lower()} {m[3]}.'
    m=re.fullmatch(r'(does|do|did) (\w+) (\w+)(.*)',q,re.I)
    if m:
        v=m[3]
        if m[1].lower()=='does':v=v+('es' if re.search(r'(?:s|sh|ch|x|o)$',v) else 's')
        elif m[1].lower()=='did':v='did '+v
        return f'{m[2].capitalize()} {v}{m[4]}.'
    return q+'.'

def _ja_surface(t):return re.sub(r'(?:ですか|でしょうか|か)$','',t)

def _solve(s):
    """Returns None when the text is not a logic problem this module covers; otherwise a dict with
    verdict, answer (None unless determinate), explanation and proof."""
    s=unicodedata.normalize('NFKC',str(s)).strip()
    try:
        parsed=_parse(s)
        if not parsed:return None
        lang,body,q=parsed
        if any(re.search(r'より|than',c,re.I) for c in body):
            r=_order(lang,body,q)
            if r is None:return None
            nodes,edges,p,query=r;v,who=order_verdict(nodes,edges,query)
            if v=='contradiction':ans=None;expl='前提の大小関係が循環していて矛盾しているため、どちらとも決められません。' if lang=='ja' else 'The comparisons form a cycle; the premises contradict each other, so it cannot be determined.'
            elif v=='undetermined':ans=None;expl='前提だけではどちらとも決められません。' if lang=='ja' else 'It cannot be determined from the premises.'
            elif query['type'] in ('max','min'):ans=(f'一番{p}{"のは" if p.endswith("い") else "なのは"}{who}です。' if lang=='ja' else f'{who.capitalize()}.')
            elif query['type'] in ('which','which_low'):ans=(f'{who}の方が{p}です。' if lang=='ja' else f'{who.capitalize()}.')
            else:ans=(('はい。' if v=='yes' else 'いいえ。')+f'{query["a"]}は{query["b"]}より{p}'+('です。' if v=='yes' else 'とは言えません。')) if lang=='ja' else ('Yes.' if v=='yes' else 'No.')
            if ans:expl=f'推移律で {" , ".join(a+">"+b for a,b in edges)} から導きました。' if lang=='ja' else 'Derived by transitivity.'
            proof={'kind':'order','nodes':nodes,'edges':[list(e) for e in edges],'predicate':p,'query':query,'verdict':v,'winner':who,'answer':ans,'lang':lang}
            return {'verdict':v,'answer':ans,'explanation':expl,'proof':proof,'orphans':[]}
        atoms,clauses,dclauses,query,orphans=_props(lang,body,q)
        incl,excl=_cnf_readings(clauses,dclauses);n=len(atoms.keys)
        v=eval_props(n,incl,excl,query)
        if v=='ambiguous':return {'verdict':'ambiguous','answer':None,'explanation':'「AかB」が両方の場合を含むかで答えが変わるため決められません。','proof':None,'orphans':orphans}
        sur=lambda i:atoms.surface[atoms.keys[i]]
        if v.startswith('derive:'):
            i=int(v.split(':')[1]);ans=(_ja_surface(sur(i))+'。') if lang=='ja' else sur(i).capitalize()+'.'
            expl='前提から導ける結論はこれだけです（全ての場合を調べました）。' if lang=='ja' else 'This is the only conclusion that holds in every case consistent with the premises.'
        elif v=='yes':ans=('はい。'+_ja_surface(q)+'。') if lang=='ja' else 'Yes. '+_en_statement(q);expl='前提を満たす全ての場合で成り立ちます。' if lang=='ja' else 'It holds in every case consistent with the premises.'
        elif v=='no':ans=('いいえ。「'+_ja_surface(q)+'」は成り立ちません。') if lang=='ja' else 'No.';expl='前提を満たす全ての場合で成り立ちません（対偶などから）。' if lang=='ja' else 'It is false in every case consistent with the premises.'
        elif v=='contradiction':ans=None;expl='前提どうしが矛盾しているので決められません。' if lang=='ja' else 'The premises contradict each other, so it cannot be determined.'
        else:ans=None;expl=('前提だけでは「'+_ja_surface(q)+'」かどうか決められません（成り立つ場合と成り立たない場合の両方があります）。') if lang=='ja' else 'It cannot be determined from the premises (there are cases both ways).'
        proof={'kind':'logic_models','atoms':list(atoms.keys),'clauses':[[list(x) for x in cl] for cl in incl],'excl_clauses':[[list(x) for x in cl] for cl in excl] if excl else None,
               'query':query,'verdict':v,'answer':ans,'lang':lang}
        return {'verdict':v,'answer':ans,'explanation':expl,'proof':proof,'orphans':orphans}
    except Refuse as e:
        return {'verdict':'refused','answer':None,'reason':str(e),'proof':None,'orphans':[]}

def solve(s):
    s=unicodedata.normalize('NFKC',str(s)).strip()
    if len(s)>2000:
        return {'verdict':'refused','answer':None,'reason':'LOGIC_QUERY_LIMIT','proof':None,'orphans':[]}
    result=_solve(s)
    if result and result.get('proof'):
        result['proof']={**result['proof'],'source_query':s}
    return result

def check(proof,answer):
    """Independent recomputation used by proofs.check."""
    source=proof.get('source_query')
    if not isinstance(source,str) or not source or len(source)>2000:return False
    reconstructed=solve(source)
    if not reconstructed or reconstructed.get('proof')!=proof or reconstructed.get('answer')!=answer:return False
    if proof['kind']=='order':
        v,who=order_verdict(proof['nodes'],[tuple(e) for e in proof['edges']],proof['query'])
        return v==proof['verdict'] and who==proof['winner'] and proof['answer']==answer and v not in ('undetermined','contradiction')
    n=len(proof['atoms'])
    if n>MAX_ATOMS:return False
    incl=[[tuple(x) for x in cl] for cl in proof['clauses']];excl=[[tuple(x) for x in cl] for cl in proof['excl_clauses']] if proof.get('excl_clauses') else None
    v=eval_props(n,incl,excl,proof['query'])
    if v!=proof['verdict'] or proof['answer']!=answer:return False
    if v=='yes':return answer.startswith(('はい','Yes'))
    if v=='no':return answer.startswith(('いいえ','No'))
    return v.startswith('derive:')
