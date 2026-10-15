"""Separate inventory of nonnumeric unknown quantities; bounded, not full NLU."""
import re
QUAL=re.compile(r'\b(?:(?:some|(?:an?\s+)?(?:unknown|unspecified|undetermined|unreported|uncertain|indefinite|unquantified))\s+(?:number|amount|quantity)\s+of|a\s+(?:small|certain)\s+number\s+of|a\s+(?:handful|bunch|lot|number)\s+of|some|several|(?:a\s+)?few|many)\s+([a-z]+(?:\s+[a-z]+){0,2})',re.I)
STOP=set('and but then she he they it has have had buys bought sells sold gives gave loses lost receives received now today tomorrow yesterday to from in on of with for before after'.split())
MOD=set('more additional red blue green yellow small big large old new ripe fresh'.split())
def sing(w):return {'children':'child','people':'person','money':'dollar','cash':'dollar'}.get(w,w[:-3]+'y' if w.endswith('ies') else w[:-2] if w.endswith(('boxes','buses')) else w[:-1] if w.endswith('s') and not w.endswith('ss') else w)
def inventory(text):
    out=[]
    for m in QUAL.finditer(text):
        # 'how many' asks; 'as many', 'twice as many', 'so many', 'too many' compare or judge an amount: none of them is
        # an amount the story does not give (fusion with gen4 r11: '3 times as many books as Lou' was held back)
        if re.search(r'\b(?:how|as|so|too)\s*$',text[max(0,m.start()-6):m.start()],re.I):continue
        ws=[]
        for w in m.group(1).lower().split():
            if w in STOP:break
            ws.append(w)
            if w.endswith('s') or w in ('money','cash'):break
        ws=[w for w in ws if w not in MOD]
        if not ws:continue
        nm=re.search(r'\b'+re.escape(ws[-1])+r'\b',text[m.start(1):m.end(1)],re.I);end=m.start(1)+nm.end()
        a=max(text.rfind('.',0,m.start()),text.rfind(';',0,m.start()))+1
        owner=re.match(r'\s*([A-Z][a-z]+)\s+(?:has|had|owns|owned|holds|held|started)',text[a:m.start()])
        if owner and owner.group(1).lower() in ('she','he','they','we','you','it'):owner=None
        out.append({'id':len(out),'start':m.start(),'end':end,'text':text[m.start():end],'noun':sing(ws[-1]),'owner':owner.group(1).lower() if owner else None,'state':bool(re.search(r'\b(?:has|have|had|owns|owned|holds|held|started|began)\b',text[a:m.start()],re.I)),'packing_destination':bool(re.search(r'\bpack(?:ed|s|ing)?\b',text[a:m.start()],re.I) and re.search(r'\b(?:in|into)\s*$',text[a:m.start()],re.I))})
    return out
ASKED_STOP=STOP|set('does did do will would can could should must is are was were there'.split())
def asked_noun(question):
    """the thing a 'how many'/'number of' question counts (its last word, singular), or nothing"""
    m=re.search(r'\b(?:how\s+many|number\s+of)\s+((?:[a-z]+\s*){1,4})',question,re.I)
    if not m:return []
    ws=[]
    for w in m.group(1).split():
        if w.lower() in ASKED_STOP or w[:1].isupper():break       # 'number of bookshelves Allie can use'
        ws.append(w.lower())
        if w.lower().endswith('s'):break
    ws=[w for w in ws if w not in MOD]
    return ws[-1:] if ws else []
def inspect(text,quantities,facts,ask):
    markers=inventory(text);qm={q['name']:q for q in quantities};connected={ask}
    while True:
        old=set(connected)
        for f in facts:
            names=set(re.findall(r'\b[A-Za-z_]\w*\b',f.get('eq','')))&set(qm)
            if names&connected:connected|=names
        if old==connected:break
    units={sing(x) for n in connected for x in re.findall('[a-z]+',str(qm.get(n,{}).get('unit','')).lower())}
    parts=re.split(r'[.!?]',text);question=parts[-2] if text.rstrip().endswith('?') else parts[-1]
    if not units:
        # a reading without a unit (a sequence, a greatest common divisor) still answers what the question counts:
        # 'how many cherries ... in the sixth bowl' counts cherries, and 'some bowls' is not one of them (fusion with
        # gen4 r11: such readings were held back for any vague amount at all)
        units={sing(w) for w in asked_noun(question)}
    generic=not units or bool(units&{'item','thing','object','unit'})
    owner=re.search(r'\b(?:does|did)\s+([A-Z][a-z]+)\b',question)
    event=bool(re.search(r'\b(?:buy|bought|sell|sold|gave|give|receive|received|add|added)\b',question,re.I)) and not re.search(r'\b(?:now|remain|left|have|has|own|total)\b',question,re.I)
    relevant=[]
    for m in markers:
        if not generic and m['noun'] not in units:continue
        if event and m['state']:continue
        if owner and m['owner'] and owner.group(1).lower()!=m['owner'] and not re.search(r'\b(?:give|gave|sell|sold|transfer|receive|received|shared|together|total)\b',text,re.I):continue
        relevant.append(m)
    used=set();missing=[]
    for m in relevant:
        found=None
        for q in quantities:
            if q['name'] not in connected or q['name'] in used or m['noun'] not in {sing(w) for w in re.findall('[a-z]+',str(q.get('unit','')).lower())}:continue
            src=q.get('unknown_source')
            if m['packing_destination'] and any(re.match(r'\s*'+re.escape(q['name'])+r'\s*=\s*floor\(',f.get('eq','')) for f in facts):found=q['name'];break
            if not isinstance(src,dict) or set(src)!={'start','text'}:continue
            start=src['start'];raw=src['text']
            if type(start) is not int or not isinstance(raw,str) or text[start:start+len(raw)]!=raw:continue
            if not start<=m['start']<m['end']<=start+len(raw):continue
            if any(re.fullmatch(r'\s*'+re.escape(q['name'])+r'\s*=\s*\d+(?:\.\d+)?\s*',f.get('eq','')) for f in facts):continue
            found=q['name'];break
        if found:used.add(found)
        else:missing.append(m)
    return {'schema':'tukuyo.g4.unknown_quantity_coverage/1','ok':not missing,'markers':markers,'relevant':relevant,'uncovered':missing,'complete_semantic_independence':False}
