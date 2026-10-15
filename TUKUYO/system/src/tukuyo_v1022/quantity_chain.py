"""Finite quantity producer: ordered operations and explicit conserved stocks.

This adds syntax and role binding, rather than a question/answer table. Contextual
inventory verbs still require the individual's existing learned event rules.
The independent input checker never imports this module.
"""
import re
from fractions import Fraction

N=r'\d+(?:\.\d+)?'
C='個|枚|本|冊'
B='箱|袋|パック|ケース|束'
VOL={'L':Fraction(1000),'dL':Fraction(100),'mL':Fraction(1)}
SCHEMAS={'bounded_quantity_stock','bounded_quantity_transfer','bounded_quantity_share',
         'bounded_quantity_unknown','bounded_quantity_liquid','bounded_quantity_average_rate'}

def _fmt(v):
    v=Fraction(v)
    return str(v.numerator) if v.denominator==1 else str(v)

def _yes(expr,value,kind,unit,graph,skills=()):
    return {'expression':expr,'value':Fraction(value),'schema':'bounded_quantity_'+kind,
            'unit':unit,'semantic_graph':graph,'trace':graph,
            'required_learning':[{'templates':list(keys),'direction':sign} for keys,sign in skills]}

def _no(why):return {'refused':'QUANTITY_CHAIN_'+why}

def stock(s):
    h=re.match(r'1('+B+r')(?:に|あたり)?(\d+)('+C+r')入り(?:が|を)(\d+)\1(あります|買いました|買い)',s)
    if not h:return None
    tail=s[h.end():]
    # Old single-event grammar retains its own learning/polarity behaviour.
    if not (re.search(r'(?:'+C+'|'+B+r')(?:を)?(?:仕入先へ)?返品(?:しました)?[。?]',tail) or re.search(r'(?:売って|使って|食べて)\d',tail)):return None
    q=re.search(r'残り(?:は)?何('+C+'|'+B+r')(?:ですか)?[?。]*$',tail)
    if not q:return _no('TARGET_UNSUPPORTED')
    body=tail[:q.start()].strip('。,、');per,count=int(h[2]),int(h[4])
    if per<=0:return _no('PACKAGE_SIZE')
    unit,box=h[3],h[1];target=q[1]
    if target not in (unit,box):return _no('TARGET_UNIT')
    purchase=h[5].startswith('買');pos=0;value=per*count;events=[];terms=[f'{h[2]}*{h[4]}'];skills=[]
    verbs={'売りました':(-1,('<Q>売りました','<Q>売った')),'売った':(-1,('<Q>売った','<Q>売りました')),
           '売って':(-1,('<Q>売った','<Q>売りました')),
           '仕入れました':(1,('<Q>買った',)),'仕入れた':(1,('<Q>買った',)),
           '返品しました':(-1,('<Q>仕入先へ返品しました','<Q>仕入先へ返品した')),
           '返品':(-1,('<Q>仕入先へ返品しました','<Q>仕入先へ返品した')),
           '仕入先へ返品しました':(-1,('<Q>仕入先へ返品しました','<Q>仕入先へ返品した')),
           '使って':(-1,()),'使いました':(-1,()),'食べて':(-1,()),'食べました':(-1,())}
    pattern=re.compile(r'(?:さらに|その後|次に)?(\d+)('+unit+'|'+box+r')(?:を)?('+'|'.join(sorted(verbs,key=len,reverse=True))+r')')
    while pos<len(body):
        m=pattern.match(body,pos)
        if not m:return _no('UNACCOUNTED_STOCK_OPERATION')
        verb=m[3]
        if verb in ('返品','返品しました') and not purchase:return _no('RETURN_DIRECTION_NOT_BOUND')
        direction,keys=verbs[verb];factor=per if m[2]==box else 1;amount=int(m[1])
        value+=direction*amount*factor
        if value<0:return _no('OVERCONSUMPTION')
        events.append({'quantity':m[1],'unit':m[2],'factor':str(factor),'direction':direction,
                       'role':'loss' if direction<0 else 'gain'})
        terms.append(('+' if direction>0 else '-')+m[1]+'*'+str(factor))
        if keys:skills.append((keys,direction))
        pos=m.end()
        while pos<len(body) and body[pos] in '。,、':pos+=1
        if pos==len(body) and verb in ('売って','使って','食べて'):return _no('UNFINISHED_EVENT')
        if len(events)>12:return _no('EVENT_LIMIT')
    if not events:return _no('EVENT_MISSING')
    if target==box:
        if any(e['unit']==unit for e in events):return _no('PARTIAL_CONTAINER_UNDERDETERMINED')
        value=count+sum(int(e['quantity'])*e['direction'] for e in events)
        expr=h[4]+''.join(('+' if e['direction']>0 else '-')+e['quantity'] for e in events)
    else:expr=''.join(terms)
    graph={'per':h[2],'count':h[4],'content_unit':unit,'container_unit':box,'target_unit':target,
           'initial_role':'purchased_stock' if purchase else 'current_stock','events':events}
    return _yes(expr,value,'stock',target,graph,skills)

def transfer(s):
    if not re.match(r'(?:袋|箱)[A-Z]に',s) or '移し' not in s:return None
    h=re.match(r'(袋|箱)([A-Z])に([ぁ-んァ-ヶ一-龠]{1,12})が(\d+)('+C+r')、\1([A-Z])に(\d+)\5あります。',s)
    if not h:return _no('TRANSFER_INITIAL_UNSUPPORTED')
    a,b=h[2],h[6]
    if a==b:return _no('DUPLICATE_HOLDER')
    q=re.search(r'(?:袋|箱)?([A-Z])は何('+C+r')(?:ですか)?[?。]*$',s[h.end():])
    if not q or q[1] not in (a,b) or q[2]!=h[5]:return _no('TRANSFER_TARGET')
    body=s[h.end():h.end()+q.start()].strip('。,、');values={a:int(h[4]),b:int(h[7])};initial={a:h[4],b:h[7]}
    steps=[];terms=[initial[q[1]]];pos=0
    pattern=re.compile(r'(?:さらに|その後)?([A-Z])から([A-Z])へ(\d+)'+h[5]+r'(?:を)?移しました')
    while pos<len(body):
        m=pattern.match(body,pos)
        if not m or m[1] not in values or m[2] not in values or m[1]==m[2]:return _no('TRANSFER_EDGE')
        amount=int(m[3]);values[m[1]]-=amount;values[m[2]]+=amount
        if min(values.values())<0:return _no('TRANSFER_OVERDRAW')
        steps.append({'from':m[1],'to':m[2],'quantity':m[3]})
        terms.append(('+' if m[2]==q[1] else '-')+m[3]);pos=m.end()
        while pos<len(body) and body[pos] in '。,、':pos+=1
        if len(steps)>12:return _no('EVENT_LIMIT')
    if not steps:return _no('EVENT_MISSING')
    graph={'holder_type':h[1],'entity':h[3],'unit':h[5],'initial':initial,'transfers':steps,'target':q[1]}
    return _yes(''.join(terms),values[q[1]],'transfer',h[5],graph)

def sharing(s):
    if not re.match(r'\d+人で',s) or '合計' not in s or '払' not in s:return None
    m=re.fullmatch(r'(\d+)人で(同じ額ずつ|同じ金額ずつ|均等に)払って合計('+N+r')円でした。1人(?:は)?何円(?:ですか)?[?。]*',s)
    if not m:return _no('EQUAL_PAYMENT_NOT_ESTABLISHED')
    if int(m[1])<=0:return _no('ZERO_PARTICIPANTS')
    graph={'participants':m[1],'total':m[3],'currency':'円','equal':True,'target_people':'1'}
    return _yes(m[3]+'/'+m[1],Fraction(m[3])/int(m[1]),'share','円',graph)

def unknown(s):
    if not s.startswith(('ある数の','ある整数の','ある正の数の')):return None
    m=re.fullmatch(r'(ある数|ある整数|ある正の数)の('+N+r')倍(?:に|から)('+N+r')を(足す|引く)と('+N+r')です。その数は[?。]*',s)
    if not m:return _no('UNKNOWN_EQUATION_UNSUPPORTED')
    if ('倍に' in s)!=(m[4]=='足す'):return _no('EQUATION_CONNECTOR')
    coefficient,offset,total=Fraction(m[2]),Fraction(m[3]),Fraction(m[5])
    if coefficient==0:return _no('UNKNOWN_NOT_UNIQUE')
    sign=1 if m[4]=='足す' else -1;value=(total-sign*offset)/coefficient
    domain={'ある数':'rational','ある整数':'integer','ある正の数':'positive_rational'}[m[1]]
    if domain=='integer' and value.denominator!=1 or domain=='positive_rational' and value<=0:return _no('UNKNOWN_DOMAIN')
    graph={'coefficient':m[2],'offset':m[3],'offset_sign':sign,'total':m[5],'domain':domain,'target':'unknown'}
    return _yes('('+m[5]+('-' if sign>0 else '+')+m[3]+')/'+m[2],value,'unknown',None,graph)

def liquid(s):
    if not re.match(N+r'(?:L|dL|mL)の(?:水|牛乳)から',s):return None
    m=re.fullmatch(r'('+N+r')(mL|dL|L)の(水|牛乳)から(.+)を(使いました|飲みました)。残り(?:は)?何(mL|dL|L)(?:ですか)?[?。]*',s)
    if not m:return _no('LIQUID_GROUP_SCOPE')
    pieces=m[4].split('と')
    if not 1<=len(pieces)<=8:return _no('EVENT_LIMIT')
    used=[];nodes=[{'quantity':m[1],'unit':m[2],'role':'initial','millilitres':_fmt(Fraction(m[1])*VOL[m[2]])}]
    total=Fraction(m[1])*VOL[m[2]];terms=[f'({m[1]}*{VOL[m[2]]})']
    for piece in pieces:
        a=re.fullmatch('('+N+r')(mL|dL|L)',piece)
        if not a:return _no('LIQUID_GROUP_UNACCOUNTED')
        amount=Fraction(a[1])*VOL[a[2]];total-=amount
        if total<0:return _no('OVERCONSUMPTION')
        used.append(a);terms.append(f'-({a[1]}*{VOL[a[2]]})')
        nodes.append({'quantity':a[1],'unit':a[2],'role':'loss','millilitres':_fmt(amount)})
    graph={'target_unit':m[6],'substance':{'水':'water','牛乳':'milk'}[m[3]],'quantities':nodes,'group_operation':'loss'}
    return _yes('('+''.join(terms)+')/'+str(VOL[m[6]]),total/VOL[m[6]],'liquid',m[6],graph)

def average_rate(s):
    if not re.search(r'平均の速さは(?:時速|分速|秒速)何',s):return None
    m=re.fullmatch('('+N+r')(km|m)を('+N+r')(時間|分|秒)で(歩きました|走りました|進みました)。平均の速さは(時速|分速|秒速)何(km|m)(?:ですか)?[?。]*',s)
    if not m:return _no('AVERAGE_EVENT_UNACCOUNTED')
    t={'時間':Fraction(3600),'分':Fraction(60),'秒':Fraction(1)};d={'km':Fraction(1000),'m':Fraction(1)}
    if Fraction(m[3])<=0:return _no('ZERO_DURATION')
    per={'時速':'時間','分速':'分','秒速':'秒'}[m[6]];factor=d[m[2]]*t[per]/t[m[4]]/d[m[7]]
    graph={'distance':m[1],'distance_unit':m[2],'duration':m[3],'duration_unit':m[4],
           'target_length_unit':m[7],'target_time_unit':per,'event':'completed_movement'}
    return _yes('('+m[1]+'/'+m[3]+')*('+_fmt(factor)+')',Fraction(m[1])/Fraction(m[3])*factor,'average_rate',m[7],graph)

def solve(t):
    s=re.sub(r'\s+','',t)
    if len(s)>800:return None
    for reader in (stock,transfer,sharing,unknown,liquid,average_rate):
        r=reader(s)
        if r:return r
    return None
