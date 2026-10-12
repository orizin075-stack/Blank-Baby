"""Separate, stdlib-only lexical input check for the finite quantity extension.

Never calls the producer, its tokenizer or calculator. It reconstructs each
input's roles, intermediate balances, target and exact expected value. The
shared graph field names are a certificate format, not a shared parser.
"""
from fractions import Fraction
import re
import unicodedata

NUM=re.compile(r'\d+(?:\.\d+)?')
COUNT=('個','枚','本','冊')
CONTAINER=('パック','ケース','箱','袋','束')
VOLUME={'mL':Fraction(1),'dL':Fraction(100),'L':Fraction(1000)}

def _f(v):
    v=Fraction(v)
    return str(v.numerator) if v.denominator==1 else str(v)

def _normal(s):
    s=unicodedata.normalize('NFKC',str(s))
    for a,b in (('ミリリットル','mL'),('デシリットル','dL'),('リットル','L'),('キロメートル','km'),('メートル','m')):s=s.replace(a,b)
    return re.sub(r'\s+','',s)

def _lex(s,units):
    items=[]
    for n in NUM.finditer(s):
        u=next((u for u in units if s[n.end():].startswith(u)),None)
        if u is None:return None
        items.append((n,u,n.end()+len(u)))
    return items

def _make(s,kind,value=None,unit=None,graph=None,why=None):
    nums=list(NUM.finditer(s))
    return {'schema':'tukuyo.v1022_7_5.independent_quantity/1','recognized':True,
            'kind':'QUANTITY_'+kind.upper(),'ok':why is None,'reason':why,
            'expected':_f(value) if value is not None else None,'target_unit':unit,'graph':graph,
            'numeric_token_count':len(nums),'covered_numeric_ids':list(range(len(nums))) if why is None else [],
            'uncovered_numeric_tokens':[] if why is None else [{'id':i,'text':m[0]} for i,m in enumerate(nums)],
            'parser_separate_from_producer':True,'complete_semantic_independence':False,
            'quantity_schema':'bounded_quantity_'+kind}

def _stock(s):
    if not s.startswith(tuple('1'+u for u in CONTAINER)) or '入り' not in s:return None
    if not (re.search(r'(?:個|枚|本|冊|箱|袋|パック|ケース|束)(?:を)?(?:仕入先へ)?返品(?:しました)?[。?]',s) or re.search(r'(売って|使って|食べて)\d',s)):return None
    fail=lambda why:_make(s,'stock',why=why)
    items=_lex(s,CONTAINER+COUNT)
    if items is None or len(items)<4:return fail('QUANTITY_LEXER_UNACCOUNTED')
    one,per,count=items[:3];box=one[1];unit=per[1]
    if one[0][0]!='1' or one[0].start()!=0 or box not in CONTAINER or unit not in COUNT or count[1]!=box:return fail('PACKAGE_HEADER')
    if s[one[2]:per[0].start()] not in ('','に','あたり') or s[per[2]:count[0].start()] not in ('入りが','入りを'):return fail('PACKAGE_HEADER')
    if '.' in per[0][0] or '.' in count[0][0]:return fail('NON_INTEGER_COUNT')
    pv,cv=int(per[0][0]),int(count[0][0])
    if pv<=0:return fail('PACKAGE_SIZE')
    q=re.search(r'残り(?:は)?何([^?。]+)',s)
    if not q:return fail('QUERY_TARGET')
    ending=s[q.end():]
    raw_target=q[1];target=raw_target.removesuffix('ですか')
    if target not in (unit,box) or ending.strip('?。'):return fail('QUERY_TARGET')
    init=s[count[2]:items[3][0].start()].strip('。,、')
    init=re.sub(r'(?:さらに|その後|次に)$','',init).rstrip('。,、')
    if init not in ('あります','買い','買いました'):return fail('INITIAL_DECLARATION')
    bought=init in ('買い','買いました');value=Fraction(pv*cv);events=[]
    negative=('売りました','売った','売って','使って','使いました','食べて','食べました','仕入先へ返品しました')
    positive=('仕入れました','仕入れた')
    for i,(n,u,end) in enumerate(items[3:]):
        last=i==len(items[3:])-1
        stop=q.start() if last else items[i+4][0].start()
        if n.start()>=q.start() or u not in (unit,box) or '.' in n[0]:return fail('EVENT_UNIT_OR_LOCATION')
        raw=s[end:stop].removeprefix('を').strip('。,、')
        # A connector belongs to the next edge, never to a hidden new actor.
        raw=re.sub(r'(?:さらに|その後|次に)$','',raw).rstrip('。,、')
        if raw in ('返品','返品しました'):
            if not bought:return fail('RETURN_DIRECTION_NOT_BOUND')
            sign=-1
        elif raw in negative:sign=-1
        elif raw in positive:sign=1
        else:return fail('EVENT_PREDICATE_NOT_COVERED')
        if last and raw in ('売って','使って','食べて'):return fail('UNFINISHED_EVENT')
        factor=pv if u==box else 1;value+=sign*int(n[0])*factor
        if value<0:return fail('OVERCONSUMPTION')
        events.append({'quantity':n[0],'unit':u,'factor':str(factor),'direction':sign,'role':'loss' if sign<0 else 'gain'})
    if len(events)>12:return fail('EVENT_LIMIT')
    if target==box:
        if any(x['unit']==unit for x in events):return fail('PARTIAL_CONTAINER_UNDERDETERMINED')
        value=cv+sum(int(x['quantity'])*x['direction'] for x in events)
    graph={'per':per[0][0],'count':count[0][0],'content_unit':unit,'container_unit':box,'target_unit':target,
           'initial_role':'purchased_stock' if bought else 'current_stock','events':events}
    return _make(s,'stock',value,target,graph)

def _transfer(s):
    if not s.startswith(('袋','箱')) or '移し' not in s:return None
    if not re.match(r'[袋箱][A-Z]に',s):return None
    fail=lambda why:_make(s,'transfer',why=why)
    items=_lex(s,COUNT)
    if items is None or len(items)<3:return fail('TRANSFER_QUANTITIES')
    x,y=items[:2];unit=x[1]
    first=re.fullmatch(r'(袋|箱)([A-Z])に([ぁ-んァ-ヶ一-龠]{1,12})が',s[:x[0].start()])
    second=re.fullmatch(r'、(袋|箱)([A-Z])に',s[x[2]:y[0].start()])
    if not first or not second or first[1]!=second[1] or first[2]==second[2] or y[1]!=unit:return fail('TRANSFER_DECLARATION')
    names=(first[2],second[2]);initial={names[0]:x[0][0],names[1]:y[0][0]}
    if any('.' in t[0][0] for t in items):return fail('NON_INTEGER_COUNT')
    values={k:int(v) for k,v in initial.items()};events=[]
    query=re.search(r'(?:袋|箱)?([A-Z])は何('+unit+r')(?:ですか)?[?。]*$',s)
    if not query or query[1] not in names:return fail('TRANSFER_TARGET')
    cursor=y[2]
    if not s[cursor:].startswith('あります'):return fail('TRANSFER_DECLARATION')
    cursor+=len('あります')
    for i,(n,u,end) in enumerate(items[2:]):
        prefix=s[cursor:n.start()].strip('。,、');prefix=re.sub(r'^(さらに|その後)','',prefix)
        edge=re.fullmatch(r'([A-Z])から([A-Z])へ',prefix)
        if not edge or edge[1] not in names or edge[2] not in names or edge[1]==edge[2] or u!=unit:return fail('TRANSFER_EDGE')
        predicate=re.match(r'(?:を)?移しました',s[end:])
        if not predicate:return fail('TRANSFER_EVENT_NOT_COMPLETED')
        cursor=end+predicate.end();amount=int(n[0]);values[edge[1]]-=amount;values[edge[2]]+=amount
        if min(values.values())<0:return fail('TRANSFER_OVERDRAW')
        events.append({'from':edge[1],'to':edge[2],'quantity':n[0]})
    if s[cursor:query.start()].strip('。,、') or len(events)>12:return fail('TRANSFER_UNACCOUNTED')
    graph={'holder_type':first[1],'entity':first[3],'unit':unit,'initial':initial,'transfers':events,'target':query[1]}
    return _make(s,'transfer',values[query[1]],unit,graph)

def _share(s):
    if not re.match(r'\d+人で',s) or '合計' not in s or '払' not in s:return None
    fail=lambda why:_make(s,'share',why=why)
    items=_lex(s,('人','円'))
    if items is None or len(items)!=3:return fail('SHARE_INPUT')
    people,total,target=items
    if people[0].start()!=0 or people[1]!='人' or total[1]!='円' or target[0][0]!='1' or target[1]!='人':return fail('SHARE_ROLES')
    before=s[people[2]:total[0].start()]
    if before not in ('で同じ額ずつ払って合計','で同じ金額ずつ払って合計','で均等に払って合計'):return fail('EQUAL_PAYMENT_NOT_ESTABLISHED')
    if s[total[2]:target[0].start()]!='でした。' or not re.fullmatch(r'(?:は)?何円(?:ですか)?[?。]*',s[target[2]:]):return fail('SHARE_QUERY')
    if '.' in people[0][0] or int(people[0][0])==0:return fail('ZERO_OR_NONINTEGER_PARTICIPANTS')
    graph={'participants':people[0][0],'total':total[0][0],'currency':'円','equal':True,'target_people':'1'}
    return _make(s,'share',Fraction(total[0][0])/int(people[0][0]),'円',graph)

def _unknown(s):
    if not s.startswith(('ある数の','ある整数の','ある正の数の')):return None
    fail=lambda why:_make(s,'unknown',why=why)
    nums=list(NUM.finditer(s))
    if len(nums)!=3:return fail('EQUATION_NUMBER_COVERAGE')
    a,b,c=nums
    subject=s[:a.start()];domain={'ある数の':'rational','ある整数の':'integer','ある正の数の':'positive_rational'}.get(subject)
    op=s[a.end():b.start()];middle=s[b.end():c.start()]
    if op=='倍に' and middle=='を足すと':sign=1
    elif op=='倍から' and middle=='を引くと':sign=-1
    else:return fail('EQUATION_OPERATION')
    if domain is None or s[c.end():].rstrip('?。')!='です。その数は':return fail('EQUATION_QUERY')
    av,bv,cv=Fraction(a[0]),Fraction(b[0]),Fraction(c[0])
    if av==0:return fail('UNKNOWN_NOT_UNIQUE')
    value=(cv-sign*bv)/av
    if domain=='integer' and value.denominator!=1 or domain=='positive_rational' and value<=0:return fail('UNKNOWN_DOMAIN')
    graph={'coefficient':a[0],'offset':b[0],'offset_sign':sign,'total':c[0],'domain':domain,'target':'unknown'}
    return _make(s,'unknown',value,None,graph)

def _liquid(s):
    ns=list(NUM.finditer(s))
    if not ns or ns[0].start()!=0:return None
    if not any(s[ns[0].end():].startswith(u+'の'+name+'から') for u in VOLUME for name in ('水','牛乳')):return None
    fail=lambda why:_make(s,'liquid',why=why)
    items=_lex(s,tuple(VOLUME))
    if items is None or not 2<=len(items)<=9:return fail('LIQUID_NUMBER_COVERAGE')
    first=items[0];noun=s[first[2]:items[1][0].start()]
    if noun not in ('の水から','の牛乳から'):return fail('LIQUID_SUBSTANCE')
    query=re.search(r'残り(?:は)?何(mL|dL|L)(?:ですか)?[?。]*$',s)
    if not query:return fail('LIQUID_TARGET')
    # A shared past predicate binds all quantities joined by と to one loss.
    last=items[-1];predicate=s[last[2]:query.start()]
    if predicate not in ('を使いました。','を飲みました。'):return fail('LIQUID_EVENT_NOT_COMPLETED')
    nodes=[];value=Fraction(0)
    for i,(n,u,end) in enumerate(items):
        amount=Fraction(n[0])*VOLUME[u];role='initial' if i==0 else 'loss'
        if 0<i<len(items)-1 and s[end:items[i+1][0].start()]!='と':return fail('LIQUID_GROUP_UNACCOUNTED')
        value+=amount if i==0 else -amount
        if value<0:return fail('OVERCONSUMPTION')
        nodes.append({'quantity':n[0],'unit':u,'role':role,'millilitres':_f(amount)})
    graph={'target_unit':query[1],'substance':'water' if noun=='の水から' else 'milk','quantities':nodes,'group_operation':'loss'}
    return _make(s,'liquid',value/VOLUME[query[1]],query[1],graph)

def _average(s):
    if not re.search(r'平均の速さは(?:時速|分速|秒速)何',s):return None
    fail=lambda why:_make(s,'average_rate',why=why)
    items=_lex(s,('時間','km','分','秒','m'))
    if items is None or len(items)!=2:return fail('RATE_NUMBER_COVERAGE')
    distance,duration=items;time={'時間':Fraction(3600),'分':Fraction(60),'秒':Fraction(1)};length={'km':Fraction(1000),'m':Fraction(1)}
    if distance[0].start()!=0 or distance[1] not in length or duration[1] not in time or s[distance[2]:duration[0].start()]!='を':return fail('RATE_QUANTITY_ROLES')
    suffix=s[duration[2]:];parts=suffix.split('。')
    if len(parts)!=2 or parts[0] not in ('で歩きました','で走りました','で進みました'):return fail('RATE_MOVEMENT_NOT_COMPLETED')
    q=re.fullmatch(r'平均の速さは(時速|分速|秒速)何(km|m)(?:ですか)?[?]*',parts[1])
    if not q:return fail('RATE_QUERY')
    if Fraction(duration[0][0])<=0:return fail('ZERO_DURATION')
    per={'時速':'時間','分速':'分','秒速':'秒'}[q[1]]
    value=Fraction(distance[0][0])*length[distance[1]]*time[per]/(Fraction(duration[0][0])*time[duration[1]]*length[q[2]])
    graph={'distance':distance[0][0],'distance_unit':distance[1],'duration':duration[0][0],'duration_unit':duration[1],
           'target_length_unit':q[2],'target_time_unit':per,'event':'completed_movement'}
    return _make(s,'average_rate',value,q[2],graph)

def inspect(query,answer=None,proof=None):
    s=_normal(query)
    if len(s)>800:return None
    result=None
    for check in (_stock,_transfer,_share,_unknown,_liquid,_average):
        result=check(s)
        if result is not None:break
    if result is None:return None
    if result['ok'] and answer is not None:
        try:agree=Fraction(str(answer))==Fraction(result['expected'])
        except (ValueError,ZeroDivisionError):agree=False
        if not agree:result.update(ok=False,reason='INDEPENDENT_QUANTITY_DISAGREEMENT')
    if result['ok'] and proof and str(proof.get('schema','')).startswith('bounded_quantity_'):
        if (proof.get('source_query')!=str(query) or proof.get('schema')!=result['quantity_schema'] or
                proof.get('unit')!=result['target_unit'] or proof.get('semantic_graph')!=result['graph']):
            result.update(ok=False,reason='QUANTITY_CERTIFICATE_SOURCE_OR_GRAPH')
    return result
