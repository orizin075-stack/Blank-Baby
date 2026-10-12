"""Independent input audit for bounded quantity and occurrence schemas.

Only stdlib is used: this checker does not import the producer, its tokenizer,
proof parser, or calculator. Numbers are occurrence-indexed, not a set of values.
Unknown clauses, target changes and incomplete operations cannot be approved by
the covered schemas. Other schemas explicitly report an unaudited boundary.
"""
from fractions import Fraction
import re
import unicodedata

NUMBER = re.compile(r'\d+(?:\.\d+)?')
MEASURES = {'時間':Fraction(3600), '分':Fraction(60), '秒':Fraction(1),
            'km':Fraction(1000), 'm':Fraction(1), 'cm':Fraction(1,100)}
MODAL = re.compile(r'走れる|走れます|泳げる|泳げます|歩ける|歩けます|食べられる|食べたい|歩きたい|走りたい|泳ぎたい|予定|つもり|できる|できます|\bcan\b|\bwants? to\b',re.I)

def quantity_scope(query):
    """Withhold a quantity result when an event's scope is unresolved.

    Not exactly N is neither N consumed nor zero consumed. This guard runs
    before question-clause filtering and every numeric answer route. It does
    not claim to interpret unrestricted Japanese negation.
    """
    s=text(query)
    if not re.search(r'\d+\s*(?:個|枚|本|冊|台|人|箱|袋|パック|ケース|束|円|時間|分|秒|km|kg|mL|L)',s):return None
    # The duration suffix in "50分から" is not the uncertainty verb "分からない".
    scope_surface=re.sub(r'\d+(?:\.\d+)?\s*分から','',s)
    if re.search(r'わけ(?:では|じゃ|でも)|(?:とは|とも)限(?:ら|り)|ないとは|なくは|不明|不詳|未確認|未確定|不確か|分か(?:ら|りません)|わか(?:ら|りません)|断定でき|確かでは|確かじゃ',scope_surface):
        return _result(s,'QUANTITY_EVENT_SCOPE',reason='UNRESOLVED_EVENT_SCOPE')
    return None

def text(query):
    s=unicodedata.normalize('NFKC',str(query))
    for a,b in [('ミリリットル','mL'),('デシリットル','dL'),('リットル','L'),('キロメートル','km'),('メートル','m'),('パーセント','%')]:s=s.replace(a,b)
    # Separate implementation of integer numerals, only adjacent to units.
    def kanji(m):
        digits=dict(zip('〇零一二三四五六七八九',[0,0,1,2,3,4,5,6,7,8,9]))
        scales={'十':10,'百':100,'千':1000};n=section=total=0
        for c in m[0]:
            if c in digits:n=n*10+digits[c]
            elif c=='万':total+=(section+n or 1)*10000;section=n=0
            else:section+=(n or 1)*scales[c];n=0
        return str(total+section+n)
    return re.sub(r'[〇零一二三四五六七八九十百千万]+(?=\s*(?:個|枚|本|冊|台|箱|袋|人|円|時間|分|秒|km|m|%))',kanji,s)

def fmt(v):
    v=Fraction(v)
    return str(v.numerator) if v.denominator==1 else str(v)

def _result(s,kind,used=(),expected=None,reason=None,unit=None,operations=None):
    nums=list(NUMBER.finditer(s))
    covered=[i for i,m in enumerate(nums) if any(a<=m.start() and m.end()<=b for a,b in used)]
    missing=[{'id':i,'text':m[0],'span':list(m.span())} for i,m in enumerate(nums) if i not in covered]
    if missing and not reason:reason='UNCOVERED_NUMERIC_OR_OPERATION'
    return {'schema':'tukuyo.v1022_5_2.independent_input/1','recognized':True,'kind':kind,
            'ok':reason is None,'reason':reason,'expected':fmt(expected) if expected is not None else None,
            'target_unit':unit,'operation_count':operations,'numeric_token_count':len(nums),
            'covered_numeric_ids':covered,'uncovered_numeric_tokens':missing,
            'parser_separate_from_producer':True,'complete_semantic_independence':False}

def _percent(s):
    if '%' not in s or not re.search(r'円',s):return None
    nums=list(NUMBER.finditer(s));money=[m for m in nums if s[m.end():].startswith('円')]
    rates=[m for m in nums if s[m.end():].startswith('%')]
    if not rates:return None
    used=[m.span() for m in money+rates]
    # A percent OF a base is a different target from a price AFTER a discount.
    direct=re.fullmatch(r'(\d+(?:\.\d+)?)円の(\d+(?:\.\d+)?)%(?:は)?[?。]*',s)
    if direct and len(money)==len(rates)==1:
        return _result(s,'PERCENT_OF',used,Fraction(direct[1])*Fraction(direct[2])/100,unit='円',operations=1)
    def fail(why):return _result(s,'PRICE_OPERATIONS',used,reason=why,operations=len(rates),unit='円')
    if len(money)!=1:return fail('AMBIGUOUS_PRICE_BASE')
    # Named products cannot silently share a price or a final operation.
    entities=set(re.findall(r'(?:商品|製品|品物)\s*([A-Za-z][A-Za-z0-9_]*)',s))
    if len(entities)>1:return fail('AMBIGUOUS_OPERATION_TARGET')
    prefix=s[:money[0].start()]
    if prefix.strip():return fail('UNCOVERED_PRICE_CLAUSE')
    between=s[money[0].end()+1:rates[0].start()]
    if not re.fullmatch(r'(?:の(?:商品|品|品物|製品)(?:[A-Za-z][A-Za-z0-9_]*)?)?(?:を|は|が)?',between):return fail('AMBIGUOUS_OPERATION_TARGET')
    value=Fraction(money[0][0]);units=[]
    for i,n in enumerate(rates):
        end=rates[i+1].start() if i+1<len(rates) else len(s)
        tail=s[n.end()+1:end]
        sign=None
        for word,direction in [('値上げ',1),('増加',1),('増し',1),('値引き',-1),('値引',-1),('割引',-1),('引き',-1)]:
            if tail.startswith(word):sign=direction;tail=tail[len(word):];break
        if sign is None:return fail('UNCOVERED_NUMERIC_OR_OPERATION')
        tail=re.sub(r'^(?:しました|した|して|し|する)','',tail)
        if i+1<len(rates):
            if not re.fullmatch(r'[、,。]?(?:さらに|次に|その後)',tail):return fail('UNCOVERED_NUMERIC_OR_OPERATION')
        elif not re.fullmatch(r'[。,.]*(?:最終(?:の)?)?(?:価格|値段|代金|金額)(?:は|が)?(?:(?:何円|いくら)(?:ですか|になる|になるか)?)?[?。]*',tail):
            return fail('UNCOVERED_PRICE_CLAUSE')
        pct=Fraction(n[0])
        if not 0<=pct<=100:return fail('PERCENTAGE_RANGE')
        value*=1+sign*pct/100;units.append(sign)
    return _result(s,'PRICE_OPERATIONS',used,value,unit='円',operations=len(units))

def _rate(s):
    rate=re.search(r'時速|分速|秒速',s)
    if not rate:return None
    nums=list(NUMBER.finditer(s));used=[]
    fail=lambda reason:_result(s,'RATE_DURATION',used,reason=reason)
    # A quantity lexer followed by a state machine, rather than a partial
    # "rate ... duration" regex. Every measured occurrence has a role.
    quantities=[]
    for n in nums:
        suffix=s[n.end():]
        unit=next((u for u in ('時間','km','cm','分','秒','m') if suffix.startswith(u)),None)
        if unit is None:return fail('UNCOVERED_NUMERIC_OR_OPERATION')
        quantities.append((n,unit));used.append(n.span())
    speeds=list(re.finditer(r'時速|分速|秒速',s))
    question=re.search(r'何(km|cm|m|時間|分|秒)',s)
    if not question:return fail('RATE_SCHEMA_NOT_COVERED')
    if len(re.findall(r'何(?:km|cm|m|時間|分|秒)',s))!=1:return fail('MULTIPLE_QUERY_TARGETS')
    if MODAL.search(s) or re.search(r'ません|なかった|ていない',s):return fail('EVENT_NOT_ESTABLISHED')
    if re.search(r'休憩|休ん|停車|停止|待機|待っ|眠|寝|睡眠|調理|料理|食事',s):
        return fail('DURATION_NOT_BOUND_TO_MOVEMENT')
    if re.match(r'(?:は|が)?何',s[rate.end():]):
        times=[x for x in quantities if x[1] in ('時間','分','秒')]
        dists=[x for x in quantities if x[1] in ('km','cm','m')]
        if len(times)!=1 or len(dists)!=1 or len(quantities)!=2:return fail('RATE_SCHEMA_NOT_COVERED')
        a,u=times[0];b,v=dists[0];per={'時速':'時間','分速':'分','秒速':'秒'}[rate[0]]
        if not Fraction(a[0]):return fail('ZERO_DURATION')
        value=Fraction(b[0])*MEASURES[v]*MEASURES[per]/(Fraction(a[0])*MEASURES[u]*MEASURES[question[1]])
        return _result(s,'RATE_DURATION',used,value,unit=question[1],operations=2)
    if len(speeds)>1:
        if question[1] not in ('km','m','cm'):return fail('RATE_UNIT_MISMATCH')
        value=Fraction(0);taken=[]
        for i,r in enumerate(speeds):
            end=speeds[i+1].start() if i+1<len(speeds) else len(s)
            leg=[x for x in quantities if r.end()<=x[0].start()<end]
            if len(leg)!=2 or leg[0][0].start()!=r.end() or leg[0][1] not in ('km','m') or leg[1][1] not in ('時間','分','秒'):
                return fail('RATE_SCHEMA_NOT_COVERED')
            a,u=leg[0];b,v=leg[1];per={'時速':'時間','分速':'分','秒速':'秒'}[r[0]]
            value+=Fraction(a[0])*MEASURES[u]*Fraction(b[0])*MEASURES[v]/MEASURES[per]/MEASURES[question[1]]
            taken.extend(x[0].span() for x in leg)
        return _result(s,'RATE_DURATION',taken,value,unit=question[1],operations=len(speeds))
    candidates=[(n,u) for n,u in quantities if n.start()==rate.end()]
    if len(candidates)!=1 or candidates[0][1] not in ('km','m'):return fail('RATE_UNIT_MISMATCH')
    n,du=candidates[0];per={'時速':'時間','分速':'分','秒速':'秒'}[rate[0]]
    others=[x for x in quantities if x[0] is not n]
    times=[x for x in others if x[1] in ('時間','分','秒')]
    distances=[x for x in others if x[1] in ('km','cm','m')]
    target=question[1]
    if times and not distances and target in ('km','m','cm'):
        if len({u for _,u in times})!=len(times):return fail('AMBIGUOUS_DURATION')
        last,lu=times[-1];predicate=s[last.end()+len(lu):]
        # Duration is not automatically motion: a rest/stop/sleep/cooking
        # predicate cannot be fed to distance=speed*time. Bare mathematical
        # quantities and the bounded movement vocabulary are separate cases.
        if not re.match(r'(?:で)?(?:歩|進|走|移動)|[。、,]*(?:何(?:km|m|cm)|距離|合計|どれだけ進|どのくらい進|どれくらい進)',predicate):
            return fail('DURATION_NOT_BOUND_TO_MOVEMENT')
        # Components must be adjacent, so two different journeys are not added.
        for (a,u),(b,_) in zip(times,times[1:]):
            if s[a.end()+len(u):b.start()] not in ('','と'):return fail('AMBIGUOUS_DURATION')
        total=sum(Fraction(a[0])*MEASURES[u] for a,u in times)
        value=Fraction(n[0])*MEASURES[du]*total/MEASURES[per]/MEASURES[target]
    elif len(distances)==1 and not times and target in ('時間','分','秒') and Fraction(n[0]):
        a,u=distances[0];value=Fraction(a[0])*MEASURES[u]*MEASURES[per]/(Fraction(n[0])*MEASURES[du]*MEASURES[target])
    else:return fail('RATE_SCHEMA_NOT_COVERED')
    return _result(s,'RATE_DURATION',used,value,unit=target,operations=len(others))

def _colour_counts(s):
    """A separate token stream: declaration, count/attribute/entity nodes, query.
    Excluded quantities must be accounted for as disjoint attributes, never lost.
    """
    s=s.lower().strip();words=re.findall(r'\d+(?:\.\d+)?|[a-z]+|[^\w\s]',s)
    colours={'red','blue','green','yellow','black','white','orange','purple','brown'}
    if not any(x in colours for x in words) or 'many' not in words:return None
    used=[x.span() for x in NUMBER.finditer(s)];nodes=[]
    fail=lambda why:_result(s,'ATTRIBUTE_SUBSET',used,reason=why)
    if words[:2]!=['there','are']:return fail('SUBSET_DECLARATION_UNSUPPORTED')
    i=2
    while i<len(words):
        if i+2>=len(words) or not words[i].isdigit() or words[i+1] not in colours or not words[i+2].isalpha():return fail('SUBSET_DECLARATION_UNSUPPORTED')
        nodes.append({'quantity':words[i],'attribute':words[i+1],'entity':words[i+2]});i+=3
        if i>=len(words):return fail('QUERY_ROLE_MISSING')
        if words[i]=='.':i+=1;break
        if words[i] not in ('and',','):return fail('UNRESOLVED_SUBSET_RELATION')
        i+=1
        if i<len(words) and words[i]=='and':i+=1
    if words[i:i+2]!=['how','many']:return fail('QUERY_ROLE_MISSING')
    i+=2;attribute=words[i] if i<len(words) and words[i] in colours else None
    if attribute:i+=1
    if i>=len(words):return fail('QUERY_ROLE_MISSING')
    entity=words[i];i+=1
    if words[i:] not in (['in','total','?'],['are','there','?']):return fail('UNCOVERED_SUBSET_CLAUSE')
    if not 1<=len(nodes)<=8 or len({x['attribute'] for x in nodes})!=len(nodes):return fail('SUBSET_OVERLAP_NOT_RESOLVED')
    if any(x['entity']!=entity for x in nodes) or attribute and attribute not in {x['attribute'] for x in nodes}:return fail('QUERY_ENTITY_MISMATCH')
    for x in nodes:x['role']='selected' if attribute is None or attribute==x['attribute'] else 'disjoint_other_attribute'
    value=sum(Fraction(x['quantity']) for x in nodes if x['role']=='selected')
    return {**_result(s,'ATTRIBUTE_SUBSET',used,value,unit=entity,operations=0),'graph':{'target':{'entity':entity,'attribute':attribute},'quantities':nodes}}

def _water(s):
    """Quantity lexer + temporal balance. One water/milk stock, no density."""
    nums=list(NUMBER.finditer(s))
    units={'mL':Fraction(1),'dL':Fraction(100),'L':Fraction(1000)}
    if not any(any(s[n.end():].startswith(u) for u in units) for n in nums):return None
    taken=[];quantities=[];graph=[]
    fail=lambda why:_result(s,'LIQUID_VOLUME',taken,reason=why)
    for n in nums:
        u=next((u for u in units if s[n.end():].startswith(u)),None)
        if u is None:return fail('UNCOVERED_NUMERIC_OR_OPERATION')
        taken.append(n.span());quantities.append((n,u,n.end()+len(u)))
    query_start=s.rfind('残り');query=s[query_start:] if query_start>=0 else ''
    target=re.fullmatch(r'残り(?:の(水|牛乳))?(?:は|が)?何(mL|dL|L)(?:ですか|ありますか|になる|になりますか)?[?。]*',query)
    if not target:return fail('VOLUME_QUERY_UNSUPPORTED')
    if not quantities or len(quantities)>12:return fail('VOLUME_INITIAL_STATE_UNSUPPORTED')
    prefix=s[:quantities[0][0].start()];substances={'水':'water','牛乳':'milk'}
    name=next((n for n in substances if prefix in (n+'が',n+'は')),None)
    if prefix and name is None:return fail('VOLUME_SUBSTANCE_UNSUPPORTED')
    subject=substances[name] if name else 'water'
    current=Fraction(0)
    for i,(n,u,end) in enumerate(quantities):
        stop=quantities[i+1][0].start() if i+1<len(quantities) else query_start
        predicate=s[end:stop];predicate=re.sub(r'[。,.、]+$','',predicate)
        predicate=re.sub(r'(?:さらに|その後|次に)$','',predicate).rstrip('。,.、')
        if i==0:
            declared=next((n for n in substances if predicate.startswith('の'+n)),None)
            if declared:
                if name and declared!=name:return fail('VOLUME_SUBSTANCE_MISMATCH')
                subject=substances[declared];predicate=predicate[len(declared)+1:]
            if predicate not in ('があります','がありました','はあります','あります','ありました','ある','あり','がある','あって'):return fail('VOLUME_INITIAL_STATE_UNSUPPORTED')
            direction=1;role='initial'
        else:
            predicate=predicate.removeprefix('を')
            if predicate in ('飲みました','飲んだ','使いました','使った','使い'):direction=-1;role='loss'
            elif predicate in ('加えました','加えた'):direction=1;role='gain'
            else:return fail('VOLUME_OPERATION_UNSUPPORTED')
        amount=Fraction(n[0])*units[u];current+=direction*amount
        if current<0:return fail('OVERCONSUMPTION')
        graph.append({'quantity':n[0],'unit':u,'role':role,'millilitres':fmt(amount)})
    if target[1] and substances[target[1]]!=subject:return fail('VOLUME_SUBSTANCE_MISMATCH')
    return {**_result(s,'LIQUID_VOLUME',taken,current/units[target[2]],unit=target[2],operations=len(graph)-1),
            'graph':{'target_unit':target[2],'substance':subject,'quantities':graph}}

def _inventory_input(s):
    """Reconstruct package counts and event effects without learned state/proofs.

    Closed event ontology verifies familiar verbs only. It does not teach the
    producer these verbs. Unsupported predicates in this frame are withheld.
    """
    units=('パック','ケース','箱','袋','束','個','枚','本','冊','台','人')
    nums=list(NUMBER.finditer(s));items=[];used=[]
    for n in nums:
        u=next((u for u in units if s[n.end():].startswith(u)),None)
        if u:items.append((n,u,n.end()+len(u)))
    fail=lambda why:_result(s,'INVENTORY_EVENTS',used,reason=why)
    packaged=(len(items)>=3 and items[0][0].start()==0 and items[0][0][0]=='1' and items[0][1] in units[:5] and '入り' in s[:items[2][2]])
    if packaged:
        header=items[:3];one,per,count=header;box=one[1];unit=per[1]
        if per[1] in units[:5] or count[1]!=box:return fail('INVENTORY_HEADER_NOT_COVERED')
        middle=s[per[2]:count[0].start()];named=re.fullmatch(r'入りの([ぁ-んァ-ヶ一-龠]{1,12})が',middle)
        label=named[1] if named else None
        if s[one[2]:per[0].start()] not in ('に','あたり','には','') or middle not in ('入りが','入り','入りの','入りを') and not named:return fail('INVENTORY_HEADER_NOT_COVERED')
        per_value=per[0][0];count_value=count[0][0];tail_start=count[2];event_items=items[3:]
    else:
        if not items or items[0][1] in units[:5]:return None
        # Relative-time/comparison stories belong to another schema; their
        # nouns must not be mistaken for inventory owners.
        if re.search(r'昨日|一昨日|今日|より(?:少ない|多い)',s):return None
        count=items[0];prefix=s[:count[0].start()]
        name=re.fullmatch(r'([ぁ-んァ-ヶ一-龠A-Za-z]{1,20})(?:が|は)',prefix)
        if prefix and not name:return None
        if not re.match(r'(?:あります|ありました|ある|あった|持っています|持っている)',s[count[2]:]):return None
        label=name[1] if name else None;unit=count[1];box=None
        header=[count];per_value='1';count_value=count[0][0];tail_start=count[2];event_items=items[1:]
    used.extend(n.span() for n,_,_ in header)
    if any('.' in n[0] for n,_,_ in items) or re.search(r'[-−~〜～]|不明|かどうか|かもしれ|約|およそ|少なくとも|以上|以下|未満|夢|想像|と言|と報告|と聞|嘘|もし|なら|なくは|ないとは|予定では|つもりでは',s):return fail('AMBIGUOUS_INVENTORY_EVENT')
    rest=s[tail_start:];m=re.match(r'(?:あります|ありました|ある|あった|です|を買いました|を持っています|を用意しました|持っています|持っている)',rest)
    if m:rest=rest[m.end():]
    rest=rest.lstrip('。');offset=len(s)-len(rest);clauses=[]
    for c in re.finditer(r'[^。!?,、]+',rest):clauses.append((c[0],offset+c.start(),offset+c.end()))
    current=Fraction(per_value)*Fraction(count_value);events=[];target=None
    for clause,start,end in clauses:
        quantities=[x for x in event_items if start<=x[0].start()<end]
        if not quantities:
            if target is not None and clause not in ('足りないです','足りません'):return fail('MULTIPLE_QUERY_TARGETS')
            if label and clause.startswith(label+'は'):clause=clause[len(label)+1:]
            if clause.startswith('今の在庫の'):clause=clause[len('今の在庫の'):]
            question=re.fullmatch(r'(?:残り(?:の数)?|残数|合計|全部で|総数)?(?:は|が|全部で)?何('+unit+('|' + box if box else '')+r')(?:か|ですか|ありますか|入っていますか|入っているか|になった|になりましたか)?',clause)
            boxq=re.fullmatch(re.escape(box)+r'(?:の数|の個数)?(?:は|が)?(?:全部で|合わせて|合計)?(?:いくつ|何個)?',clause) if box else None
            generic=re.fullmatch(r'(?:残り|残数|全部で|総数|合計)(?:は)?(?:いくつ)?',clause)
            if question:target=question[1]
            elif boxq:target=box
            elif generic:target=unit
            elif clause in ('足りないです','足りません','在庫としてあります','今の在庫としてあります','あります','ある'):continue
            else:return fail('UNCOVERED_INVENTORY_CLAUSE')
            continue
        if target is not None or len(quantities)!=1:return fail('MIXED_EVENT_CLAUSE_UNSUPPORTED')
        n,u,qend=quantities[0];used.append(n.span())
        if u not in (unit,box):return fail('EVENT_UNIT_MISMATCH')
        before=s[start:n.start()];after=s[qend:end].removeprefix('を');annotation=None
        if after.endswith('が足りないです'):after=after[:-len('が足りないです')];annotation='shortage_comment'
        recipient=(re.fullmatch(r'[ぁ-んァ-ヶ一-龠A-Za-z]{1,16}に',before) and after in ('渡した','渡しました','あげた','あげました'))
        if before and not recipient and not re.fullmatch(r'(?:明日|来週|別の在庫の|別の在庫から|別の人が別の在庫から|今の在庫から|実際には)',before):return fail('EVENT_ACTOR_NOT_BOUND')
        if before in ('別の在庫の','別の在庫から','別の人が別の在庫から') or '別の在庫' in after:direction=0;role='other_inventory'
        elif re.fullmatch(r'(?:食べ|使わ|使い|売ら|売り|捨て|渡さ|渡し|返さ|返し|返品し|もらわ|借り入れ)(?:ていません|なかった|ません|ませんでした|ない)',after) or re.fullmatch(r'(?:食べる|使う|売る|捨てる|渡す)(?:予定|つもり)(?:です)?',after) or (before in ('明日','来週') and re.fullmatch(r'(?:食べる|使う|売る|食べます|使います|売ります)(?:予定です|つもりです)?',after)):direction=0;role='not_executed'
        else:
            # The complete predicate must be accounted for; substring matches
            # cannot hide a second operation or an uncertain report.
            loss={'売った','売りました','販売した','販売しました','出荷した','出荷しました','食べた','食べました','使った','使いました','捨てた','捨てました','渡した','渡しました','あげた','あげました','返却した','返却しました','仕入先へ返品した','仕入先へ返品しました','紛失した','紛失しました','落として失いました','盗まれた','盗まれました'}
            gain={'買った','買いました','もらった','もらいました','追加した','追加しました','補充した','補充しました','仕入れた','仕入れました','が客から返品されて戻った','が客から返品されて戻りました','返品されて戻りました','借りて今の在庫に加えました','借りて在庫に加えました','借り入れた'}
            zero={'開けた','開けました','数えた','数えました','確認した','確認しました'}
            if after in loss:direction=-1;role='loss'
            elif after in gain:direction=1;role='gain'
            elif after in zero:direction=0;role='observation'
            else:return fail('EVENT_PREDICATE_NOT_IN_INDEPENDENT_SCHEMAS')
        factor=Fraction(per_value) if u==box else Fraction(1)
        current+=direction*Fraction(n[0])*factor
        if current<0:return fail('OVERCONSUMPTION')
        event={'quantity':n[0],'unit':u,'factor':fmt(factor),'direction':direction,'role':role}
        if annotation:event['annotation']=annotation
        events.append(event)
    if target is None:return fail('QUERY_ROLE_MISSING')
    if target==box:
        if any(e['direction'] and e['unit']==unit for e in events):return fail('PARTIAL_CONTAINER_UNDERDETERMINED')
        current=Fraction(count_value)+sum(Fraction(e['quantity'])*e['direction'] for e in events)
    return {**_result(s,'INVENTORY_EVENTS',used,current,unit=target,operations=len(events)),
            'graph':{'per':per_value,'count':count_value,'content_unit':unit,'container_unit':box,'content_entity':label,'target_unit':target,'events':events}}

def inspect(query,answer=None,proof=None):
    s=text(query);compact=re.sub(r'\s+','',s);p=proof or {}
    if len(s)>4000 or len(list(NUMBER.finditer(s)))>128:
        return _result(s,'INPUT_LIMIT',reason='INPUT_LIMIT')
    scope=quantity_scope(query)
    if scope is not None:return scope
    # Potential/desire inflections must not become an occurrence via stem collapse.
    if MODAL.search(s) and (re.search(r'なら|もし|\bif\b',s,re.I) or re.search(r'時速|分速|秒速',s)):
        return _result(s,'EVENT_MODALITY',reason='EVENT_NOT_ESTABLISHED')
    result=_percent(compact) or _rate(compact) or _water(compact) or _inventory_input(compact) or _colour_counts(s)
    if result is not None:
        if result['ok'] and answer is not None:
            try:match=Fraction(str(answer))==Fraction(result['expected'])
            except (ValueError,ZeroDivisionError):match=False
            if not match:result.update(ok=False,reason='INDEPENDENT_INPUT_DISAGREEMENT')
        return result
    # English groups: check the requested object, not only the numbers.
    if not re.search(r'[\u3040-\u30ff\u4e00-\u9fff]',s):
        if re.search(r'[-−]\s*\d+\s+(?:boxes|bags|apples|cookies)',s,re.I):
            return _result(s,'SIGNED_COUNT',reason='NEGATIVE_COUNT_UNSUPPORTED')
        g=re.search(r'(\d+)\s+(\w+)\s+(?:with|of|that each have|each with)\s+(\d+)\s+(\w+)',s,re.I)
        q=re.search(r'how many\s+([\w ]+?)\s+(?:in total|are there)',s,re.I)
        if g and q:
            noun=q[1].strip().lower();container=g[2].lower();contents=g[4].lower()
            v=Fraction(g[1]) if noun==container else Fraction(g[1])*Fraction(g[3]) if noun==contents else None
            reason=None if v is not None else 'QUERY_ENTITY_MISMATCH'
            r=_result(s,'GROUP_TARGET',[g.span()],v,reason=reason,unit=noun)
            if answer is not None and r['ok'] and str(answer)!=r['expected']:r.update(ok=False,reason='INDEPENDENT_INPUT_DISAGREEMENT')
            return r
        if re.search(r'\b(shared|divided|split)\b',s,re.I) and not re.search(r'\bequally\b|\bequal\b',s,re.I):
            return _result(s,'SHARING',reason='EQUAL_SHARING_NOT_ESTABLISHED')
    # Word arithmetic must retain the requested unit; adjective-qualified
    # subsets cannot be silently combined with the whole population.
    if p.get('from_words') and p.get('schema')=='comparison' and not re.search(r'[\u3040-\u30ff\u4e00-\u9fff]',s):
        units=re.findall(r'\d+(?:\.\d+)?\s+(years?|cm|kg|dollars?)',s,re.I)
        if len(set(u.lower().rstrip('s') for u in units))>1:return _result(s,'COMPARISON_UNITS',reason='UNIT_DIMENSION_MISMATCH')
    if p.get('schema')=='combine' and re.search(r'how many\s+(?:red|blue|green)\s',s,re.I):
        return _result(s,'QUALIFIED_TARGET',reason='QUERY_SUBSET_NOT_BOUND')
    # Inventory proof is bounded by all clauses, but query-unit binding is
    # independently checked here. Full verb semantics still relies on learning.
    if p.get('kind')=='inventory':
        box=re.search(r'(箱|袋|パック|ケース|束)(?:の数|の個数)?(?:は|が)?(?:いくつ|何個|[?？])',compact)
        if box and re.search(r'入り',compact):
            groups=re.search(r'(\d+)'+re.escape(box[1])+r'(?:あります|ある|。|[?？])',compact)
            if groups and not p.get('events'):
                header=re.match(r'1'+re.escape(box[1])+r'に?(\d+)(?:個|枚|本|冊|台|人)入りが?',compact)
                if not header:return _result(compact,'INVENTORY_TARGET',reason='INVENTORY_HEADER_NOT_COVERED')
                r=_result(compact,'INVENTORY_TARGET',[header.span(),groups.span()],Fraction(groups[1]),unit=box[1],operations=0)
                if str(answer)!=r['expected']:r.update(ok=False,reason='QUERY_UNIT_MISMATCH')
                return r
    return {'schema':'tukuyo.v1022_5_2.independent_input/1','recognized':False,'ok':True,
            'reason':'OUTSIDE_INDEPENDENT_INPUT_SCHEMAS','parser_separate_from_producer':True,
            'complete_semantic_independence':False}
