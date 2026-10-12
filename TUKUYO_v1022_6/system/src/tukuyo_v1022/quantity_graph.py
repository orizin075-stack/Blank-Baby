"""Producer for two finite quantity schemas. Verification is in a separate module.

Explicit disjoint colour counts and one water/milk inventory only. No learned
inventory verb is added here; teaching and cultural inheritance remain causal.
"""
from fractions import Fraction
import re

NUM=r'\d+(?:\.\d+)?'
COLOURS='red|blue|green|yellow|black|white|orange|purple|brown'
VOLUME={'L':Fraction(1000),'dL':Fraction(100),'mL':Fraction(1)}

def subset(t):
    s=t.lower().strip()
    if not re.search(r'how many (?:'+COLOURS+r')\s',s) and not re.search(r'\d+ (?:'+COLOURS+r') ',s):return None
    if not s.startswith('there are '):return {'refused':'SUBSET_DECLARATION_UNSUPPORTED'}
    m=re.fullmatch(r'there are (.+?)\.\s*how many (?:('+COLOURS+r') )?([a-z]+) (?:in total|are there)\?',s)
    if not m:return {'refused':'SUBSET_DECLARATION_UNSUPPORTED'}
    members=[]
    for piece in re.split(r'\s+and\s+|,\s*(?:and\s+)?',m[1]):
        a=re.fullmatch(r'(\d+) ('+COLOURS+r') ([a-z]+)',piece.strip())
        if not a:return {'refused':'SUBSET_DECLARATION_UNSUPPORTED'}
        members.append({'quantity':a[1],'attribute':a[2],'entity':a[3]})
    if not 1<=len(members)<=8 or len({x['attribute'] for x in members})!=len(members):return {'refused':'SUBSET_OVERLAP_NOT_RESOLVED'}
    if any(x['entity']!=m[3] for x in members) or m[2] and not any(x['attribute']==m[2] for x in members):return {'refused':'QUERY_ENTITY_MISMATCH'}
    graph={'target':{'entity':m[3],'attribute':m[2]},'quantities':[{**x,'role':'selected' if m[2] is None or x['attribute']==m[2] else 'disjoint_other_attribute'} for x in members]}
    selected=[x['quantity'] for x in graph['quantities'] if x['role']=='selected']
    return {'expression':'+'.join(selected),'value':sum(Fraction(x) for x in selected),'schema':'attribute_subset','unit':m[3],'trace':graph['quantities'],'semantic_graph':graph}

def volume(t):
    if not re.search(NUM+r'(?:mL|dL|L)',t):return None
    s=re.sub(r'\s+','',t)
    q=re.search(r'残り(?:の(水|牛乳))?(?:は|が)?何(mL|dL|L)(?:ですか|ありますか|になる|になりますか)?[?。]*$',s)
    if not q:return {'refused':'VOLUME_QUERY_UNSUPPORTED'}
    body=s[:q.start()].rstrip('。');matches=list(re.finditer('('+NUM+r')(mL|dL|L)',body))
    if not matches or len(matches)>12:return {'refused':'VOLUME_INVENTORY_UNSUPPORTED'}
    prefix=body[:matches[0].start()];subject={'':'water','水が':'water','水は':'water','牛乳が':'milk','牛乳は':'milk'}.get(prefix)
    if subject is None:return {'refused':'VOLUME_SUBSTANCE_UNSUPPORTED'}
    if q[1] and {'水':'water','牛乳':'milk'}[q[1]]!=subject:return {'refused':'VOLUME_SUBSTANCE_MISMATCH'}
    if len(re.findall(NUM,s))!=len(matches):return {'refused':'WORD_PROBLEM_NUMBER_COVERAGE'}
    total=Fraction(0);expression=[];nodes=[]
    for i,x in enumerate(matches):
        stop=matches[i+1].start() if i+1<len(matches) else len(body)
        tail=body[x.end():stop]
        tail=re.sub(r'[。,.、]*(?:さらに|次に|その後)?$','',tail)
        if i==0:
            noun=re.match(r'の(水|牛乳)',tail)
            if noun:
                declared={'水':'water','牛乳':'milk'}[noun[1]]
                if prefix and declared!=subject:return {'refused':'VOLUME_SUBSTANCE_MISMATCH'}
                subject=declared
                if q[1] and {'水':'water','牛乳':'milk'}[q[1]]!=subject:return {'refused':'VOLUME_SUBSTANCE_MISMATCH'}
            if not re.fullmatch(r'(?:の(?:水|牛乳))?(?:が|は)?(?:あります|ありました|ある|あり|あって)',tail):return {'refused':'VOLUME_INITIAL_STATE_UNSUPPORTED'}
            sign=1;role='initial'
        else:
            a=re.fullmatch(r'(?:を)?(飲みました|飲んだ|使いました|使った|使い|加えました|加えた)',tail)
            if not a:return {'refused':'VOLUME_OPERATION_UNSUPPORTED'}
            sign=1 if a[1].startswith('加え') else -1;role='gain' if sign>0 else 'loss'
        base=Fraction(x[1])*VOLUME[x[2]];total+=sign*base
        if total<0:return {'refused':'OVERCONSUMPTION'}
        term='('+x[1]+'*'+str(VOLUME[x[2]])+')'
        expression.append(('+' if sign>0 and i else '-' if sign<0 else '')+term)
        nodes.append({'quantity':x[1],'unit':x[2],'role':role,'millilitres':str(base)})
    graph={'target_unit':q[2],'substance':subject,'quantities':nodes}
    return {'expression':'('+''.join(expression)+')/'+str(VOLUME[q[2]]),'value':total/VOLUME[q[2]],'schema':'single_liquid_volume_sequence','unit':q[2],'trace':nodes,'semantic_graph':graph}

def solve(t):
    return volume(t) or subset(t)
