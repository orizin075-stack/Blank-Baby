"""claude-patch2/3: answer from the individual's own knowledge store (knowledge-add), read-only.

Japanese facts 「XのYはZ（である|です|だ）」 and 「XはTにVした/された」 are read as (entity, attribute, value).
patch3:
  * the question tail must be a pure question word (patch2 accepted any trailing words, so
    「桐生ホールの最寄り駅はいつ開業した？」 was answered with the FIRST hop 「中央駅」 - fixed)
  * multi-hop chains: 「XのYのZは？」, 「XのYはいつVした？」 resolve hop by hop (max 3), every hop
    an exact entity match; English relative clauses "the city founded by Captain Rhee" resolve one hop
  * when the entity is known but the attribute is not, the result says what IS known
Entity names match exactly; attributes exactly or through a table of ordinary synonyms.
Different values for the same entity+attribute -> conflict -> abstain. Nothing is written.
proofs.check recomputes the whole answer from the question text and the cited records only.
"""
from __future__ import annotations
import json,re,unicodedata
from pathlib import Path

SYN=[{'人口','住民の数','住民数','住んでいる人の数','暮らしている人の数'},{'標高','高さ'},{'全長','長さ'},{'首都','首府'},
     {'創立者','創設者','設立者','創始者','創業者'},{'名物','名産','名産品','特産','特産品','名物料理','土産','おみやげ','お土産'},
     {'定休日','休業日','休みの日','休み','休館日'},{'開店時刻','開店時間','開店時間帯'},{'閉店時刻','閉店時間'},{'所在地','場所','住所'},
     {'通貨','お金'},{'公用語','言語','言葉'},{'色','カラー'},{'面積','広さ'},{'生徒数','生徒の数'},{'社員数','従業員数','社員の数','従業員の数'},
     {'誕生日','生まれた日'},{'出身地','生まれた場所','故郷','ふるさと','出身'},{'電話番号','電話'},{'重さ','重量','体重'},{'深さ','水深'},
     {'収容人数','定員','収容数','収容可能人数'},{'営業時間','開いている時間','営業時刻'},{'最寄り駅','最寄駅','近くの駅'},{'開館時間','開館時刻'},
     {'設計者','設計した人'},{'作者','著者'},{'幅','横幅'},{'築年','建築年'},
     {'登山口','登り口'}]
# claude-patch6: phrases that name an attribute by what it is (「政府が置かれた都市」 = 首都)
SYN[3]|={'政府が置かれた都市','政府のある都市','政府が置かれている都市'}
HEAD_WORDS={'トップ','代表','代表者','リーダー','責任者','長','トップの人'}
EVENT_SYN=[{'設立','創立','創設','創業'},{'開業','開設','開館','オープン','開店'},{'完成','竣工','落成'},{'開通'},{'建設','建築'},{'発見'},{'発明'}]
VERBQ=[(r'何人(?:が|ぐらい|くらい)?(?:住ん|暮らし)',{'人口'}),(r'何人(?:まで)?(?:入れる|入る|入れます|入ります|収容)',{'収容人数'}),
       (r'どこに(?:ある|あります)',{'所在地','場所','住所'}),(r'何時(?:に|から)(?:開|営業|やって)',{'開店時刻','開店時間','営業時間','開館時間'}),
       (r'何時(?:に|まで)(?:閉ま|営業|やって)',{'閉店時刻','閉店時間','営業時間'}),(r'何曜日(?:が|は|に)?(?:休み|閉ま|お休み|休館)',{'定休日'}),
       (r'(?:を|が)?(?:建て|作っ|創立し|設立し|創設し|創業し)た(?:の)?は誰',{'創立者','創設者','設立者','創業者'}),
       (r'(?:を|が)?(?:設計し)た(?:の)?は誰',{'設計者'}),(r'(?:を|が)?(?:書い)た(?:の)?は誰',{'作者','著者'}),
       (r'(?:を|が)?(?:率い|まとめ)て(?:いる)?(?:の)?は誰',HEAD_WORDS),
       (r'どのくらいの高さ|高さはどのくらい|どれくらい高|どのくらい高',{'標高','高さ'}),(r'どのくらいの長さ|長さはどのくらい|どれくらい長|どのくらい長',{'全長','長さ'}),
       (r'どのくらいの広さ|どれくらい広|どのくらい広',{'面積','広さ'}),(r'どのくらい深|どれくらい深',{'深さ','水深'}),
       (r'(?:閉まって|休んで|お休みして|休館して|休みになって)(?:いる|います)?(?:の)?(?:は|が)何曜日',{'定休日'}),
       (r'何人(?:の)?(?:生徒|学生)が(?:通っ|在籍し|学んで|いる|います)',{'生徒数'}),(r'何色(?:を)?(?:して|です)',{'色'}),
       (r'どんな(?:お金|通貨)が使われ',{'通貨'}),(r'どこから(?:登り始め|登り|のぼり)',{'登山口'}),(r'何語が(?:話され|使われ)',{'公用語'})]
TAIL=r'(?:何(?:色|曜日|人|時|年|月|日|歳|個|本|メートル|キロメートル|キロ|グラム|円|階|番)?|なに|なん|誰|だれ|どこ|いつ|いくつ|いくら|どれ|どなた|どんな(?:もの|物|人|ところ)?|どのくらい|どれくらい)?(?:です|でしょう)?'
EN_STOP={'what','which','who','whom','whose','where','when','why','how','is','are','was','were','the','a','an','of','in','on','at','to','into','does','do','did','it','its','and','or','for','by','from','with','that','this','there','has','have','had'}
EN_IRR={'won':'win','ate':'eat','went':'go','saw':'see','came':'come','ran':'run','made':'make','took':'take','gave':'give','got':'get','built':'build','found':'find',
        'wrote':'write','written':'write','drew':'draw','drawn':'draw','began':'begin','begun':'begin','rose':'rise','risen':'rise','flew':'fly','led':'lead','taught':'teach',
        'founded':'found','bought':'buy','sold':'sell','held':'hold','grew':'grow','grown':'grow','knew':'know','known':'know','became':'become','discovered':'discover'}
EN_SYN={'created':'invent','create':'invent','creator':'invent','inventor':'invent','invented':'invent','empty':'flow','empties':'flow','birth':'born','length':'long','height':'tall',
        'start':'rise','begin':'rise','source':'rise','founder':'found','discoverer':'discover','builder':'build','architect':'design','designer':'design','designed':'design',
        'finished':'complete','completed':'complete','completion':'complete','opened':'open','opening':'open','inhabitants':'population','people':'population'}

def _n(s):return unicodedata.normalize('NFKC',str(s)).strip()
def _records(data):
    p=Path(data)/'v1001'/'knowledge.jsonl'
    if not p.exists():return []
    out=[]
    for line in p.read_text(encoding='utf-8').splitlines():
        if line.strip():
            try:r=json.loads(line);out.append({'id':r.get('id'),'text':_n(r.get('text',''))})
            except Exception:pass
    return out

def _triples(rec):
    t=rec['text'].rstrip('。. ')
    m=re.fullmatch(r'(.{1,20}?)の(.{1,12}?)は(.{1,30}?)(?:である|です|だ)',t)
    if m:return [(m[1],m[2],m[3])]
    m=re.fullmatch(r'(.{1,20}?)は(\d{1,4}年(?:\d{1,2}月)?(?:\d{1,2}日)?|.{1,8}?(?:年|月|日|時))に(.{1,8}?)(?:された|した|れた|た|しました|されました)',t)
    if m:return [(m[1],m[3],m[2])]
    return []

def _syn(a):
    if a in HEAD_WORDS:return set(HEAD_WORDS)|{'__HEAD__'}
    s={a}
    for g in SYN+EVENT_SYN:
        if a in g:s|=g
    return s
def _attr_ok(fact_attr,attrs):
    if fact_attr in attrs:return True
    return '__HEAD__' in attrs and re.fullmatch(r'.{1,3}長|代表|代表者',fact_attr) is not None and fact_attr not in ('全長','身長','部長代理')

def _lookup(facts,ent,attrs):
    hits=[(r,tr) for r,tr in facts if tr[0]==ent and _attr_ok(tr[1],attrs)]
    if not hits:return None
    values={tr[2] for _,tr in hits}
    if len(values)!=1:return {'conflict':True,'entity':ent,'values':sorted(values)}
    return {'value':hits[0][1][2],'attribute':hits[0][1][1],'records':[r for r,_ in hits]}

def _resolve(facts,np,depth=0):
    """noun phrase -> (entity, records used). 「XのYのZ」: X must be a known entity, each 「のY」 a hop."""
    np=np.strip()
    if any(tr[0]==np for _,tr in facts):return np,[]
    if depth>=3 or 'の' not in np:return None
    for i in [k for k,ch in enumerate(np) if ch=='の'][::-1]:
        head,attr=np[:i],np[i+1:]
        if not head or not attr:continue
        h=_resolve(facts,head,depth+1)
        if not h:continue
        hop=_lookup(facts,h[0],_syn(attr))
        if hop and not hop.get('conflict'):return hop['value'],h[1]+hop['records']
        return None
    return None

def _ja(q,recs):
    q=re.sub(r'[?？。\s]+$','',_n(q));q=re.sub(r'(?:ですか|でしょうか|か)$','',q)
    facts=[(r,tr) for r in recs for tr in _triples(r)]
    if not facts:return None
    tries=[]
    m=re.fullmatch(r'(.{1,40}?)の([^の]{1,12}?)(?:は|って|といえば|と言えば|といったら)'+TAIL,q)
    if m:tries.append((m[1],_syn(m[2]),'attribute'))
    m=re.fullmatch(r'(.{1,40}?)(?:は|が|を|で|に|には)(.+)',q)
    if m:
        for pat,attrs in VERBQ:
            if re.fullmatch(r'(?:.{0,3})(?:'+pat+r')(?:\S{0,8})',m[2]):tries.append((m[1],set().union(*(_syn(a) for a in attrs)),'verb_paraphrase'))
        mm=re.fullmatch(r'(?:いつ|何年に|何年何月に)(.{1,8}?)(?:された|した|れた|た|しました|されました)',m[2])
        if mm:tries.append((m[1],_syn(mm[1]),'event_time'))
    known_entity=None
    for np,attrs,how in tries:
        base=_resolve(facts,np)
        if not base:continue
        ent,chain=base;known_entity=ent
        hit=_lookup(facts,ent,attrs)
        if not hit:continue
        if hit.get('conflict'):return {'conflict':True,'entity':ent}
        recs_used=[]
        for r in chain+hit['records']:
            if r not in recs_used:recs_used.append(r)
        return {'answer':hit['value'],'entity':ent,'attribute':hit['attribute'],'value':hit['value'],'records':[{'id':r['id'],'text':r['text']} for r in recs_used],
                'match':how if not chain else how+'+multi_hop','hops':len(chain)+1}
    if known_entity:
        attrs=sorted({tr[1] for _,tr in facts if tr[0]==known_entity})
        return {'missing':True,'entity':known_entity,'known_attributes':attrs}
    return None

def _en_words(s):
    out=[]
    for w in re.findall(r"[a-z0-9]+",s.lower()):
        if w in EN_STOP:continue
        w=EN_SYN.get(w,EN_IRR.get(w,w))
        for suf in ('ing','ed','es','s'):
            if len(w)>4 and w.endswith(suf):w=w[:-len(suf)];break
        out.append(EN_SYN.get(w,w))
    return out

def _en_single(q,recs):
    q=re.sub(r'(?i)\b(?:in |on )?what (?:year|date|day|time|month)\b','when',q)   # claude-patch6
    q=re.sub(r'(?i)\bwhat (?:colou?r|kind of|type of)\b','what',q)
    qw=set(_en_words(q))
    if len(qw)<2:return None
    hits=[r for r in recs if qw<=set(_en_words(r['text'])) and len(set(_en_words(r['text']))-qw)>=1]
    if len(hits)!=1:return {'conflict':True} if len(hits)>1 else None
    return hits[0]

REL=r'\bthe ((?:\w+ ){0,2}?\w+) (founded|built|invented|discovered|designed|created|written|painted|opened|completed|named|owned|led) by ((?:[A-Z][\w.]*\s?){1,3})'
def _en(q,recs):
    q=q.strip(' ?.')
    m=re.search(REL,q)
    if m:
        noun,verb,agent=m[1].lower(),m[2],m[3].strip()
        cand=[]
        for r in recs:
            mm=re.search(re.escape(agent)+r' '+verb+r' (?:the )?(?:'+re.escape(noun)+r' (?:of |called |named )?)?([A-Z][\w-]*(?: [A-Z][\w-]*)?)',r['text'])
            if mm:cand.append((r,mm[1]))
        if len(cand)!=1:return None
        hop1,ent=cand[0]
        q2=q[:m.start()]+f'{noun} of {ent}'+q[m.end():]
        h=_en_single(q2,[r for r in recs if r is not hop1])
        if not h or isinstance(h,dict) and h.get('conflict'):return h if isinstance(h,dict) and h.get('conflict') else None
        return {'answer':h['text'],'entity':ent,'attribute':None,'value':h['text'],'records':[hop1,h],'match':'coverage+relative_clause','hops':2}
    h=_en_single(q,recs)
    if not h or h.get('conflict'):return h
    return {'answer':h['text'],'entity':None,'attribute':None,'value':h['text'],'records':[h],'match':'coverage','hops':1}

def _solve_records(q,recs):
    q=_n(q)
    if not re.search(r'[?？]|何|誰|どこ|いつ|いくつ|いくら|どれ|どんな|どの|\b(?:what|who|where|when|which|how)\b',q,re.I):return None
    return _ja(q,recs) if re.search(r'[぀-ヿ一-鿿]',q) else _en(q,recs)

def solve(data,query):
    recs=_records(data)
    if not recs:return None
    return _solve_records(query,recs)

def check(proof,answer):
    records=proof.get('records');q=proof.get('source_query')
    if not isinstance(records,list) or not 1<=len(records)<=64 or not isinstance(q,str) or len(q)>2000:return False
    if any(not isinstance(r,dict) or not isinstance(r.get('text'),str) or len(r['text'])>4096 for r in records):return False
    result=_solve_records(q,records)
    if not result or result.get('conflict') or result.get('missing') or str(result['answer'])!=str(answer):return False
    return all(result.get(k)==proof.get(k) for k in ('entity','attribute','value','match','records'))
