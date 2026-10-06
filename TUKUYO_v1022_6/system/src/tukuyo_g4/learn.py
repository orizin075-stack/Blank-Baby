"""generation 4: learning readings from verified examples.

A reading that was committed by agreement (two Claude readings, or Claude and TUKUYO's own reader, or a reading a
person gave with g4-teach) is kept as a template: the text with every number replaced by a slot, and the reading
with each bound number replaced by the slot of the text number it binds. A later problem whose text is the same
apart from its numbers is read from the template alone, without Claude; the new reading is solved and checked like
any other, so a template can never commit an answer that the checker refuses.

  skeleton(text)          -> (key, ...)               the text with numbers as #0 #1 ...
  template(spec)          -> template | None          from a checked reading
  instantiate(t, text)    -> spec | None              the template read with the numbers of a new text
  Store(dir)              learned templates of one individual (learned.json with a sha256 seal); add, find, audit
"""
from __future__ import annotations
import copy,hashlib,json,os,re,time
from fractions import Fraction
from pathlib import Path
from . import numbers as N
from .fpl import fmt

SCHEMA='tukuyo.g4.learned/1'

def skeleton(text):
    """normalized text with the numbers as #0 #1 ... (spans keep the original words, so names are not abstracted)"""
    t=' '.join(text.split());nums=N.find(t)
    out=[];pos=0
    for k,n in enumerate(nums):
        out.append(t[pos:n.start]);out.append(f'#{k}');pos=n.end
    out.append(t[pos:])
    return ''.join(out).lower(),t,nums,{}

def _slot_of(t,nums,span,value):
    """the index of the text number inside one occurrence of span that has this value"""
    core=''.join(span.split())
    if not core:return None
    pat=r'\s*'.join(re.escape(c) for c in core)
    for m in re.finditer(pat,t):
        for k,n in enumerate(nums):
            if m.start()<=n.start and n.end<=m.end() and (n.value==value or (n.kind=='percent' and n.value/100==value)):return k
    return None

def template(spec):
    """a template from a checked reading, or None when a binding cannot be tied to one text number"""
    key,t,nums,names=skeleton(spec['text'])
    tpl=copy.deepcopy(spec);tpl.pop('text',None)
    facts=[]
    for f in spec['facts']:
        eq=f['eq'];g=dict(f)
        m=re.fullmatch(r'\s*([A-Za-z_]\w*)\s*=\s*([0-9./]+)\s*',eq)
        if m and f.get('span') and not f.get('known'):
            v=Fraction(m.group(2));k=_slot_of(t,nums,f['span'],v)
            if k is None:return None
            n=nums[k]
            g['eq']=f'{m.group(1)} = #{k}';g['scale']='percent' if (n.kind=='percent' and n.value/100==v and n.value!=v) else None
        if f.get('span'):g['span']=_span_template(t,nums,f['span'])
        if g.get('span') is None and f.get('span'):return None
        facts.append(g)
    tpl['facts']=facts
    un=[]
    for u in spec.get('unused') or []:
        ks=[k for k,n in enumerate(nums) if n.raw==str(u.get('raw','')).strip()]
        if not ks:return None
        un.append({'slot':ks[0],'why':u.get('why','')})
    tpl['unused']=un
    return {'key':key,'names':len(names),'numbers':len(nums),'reading':tpl}

def _span_template(t,nums,span):
    core=''.join(span.split())
    pat=r'\s*'.join(re.escape(c) for c in core)
    m=re.search(pat,t)
    if not m:return None
    out=[];pos=m.start()
    for k,n in enumerate(nums):
        if m.start()<=n.start and n.end<=m.end():out.append(t[pos:n.start]);out.append('{#%d}'%k);pos=n.end
    out.append(t[pos:m.end()])
    return ''.join(out)

def instantiate(tpl,text):
    key,t,nums,names=skeleton(text)
    if key!=tpl['key'] or len(nums)!=tpl['numbers']:return None
    spec=copy.deepcopy(tpl['reading']);spec['text']=text
    facts=[]
    for f in spec['facts']:
        g=dict(f)
        m=re.fullmatch(r'\s*([A-Za-z_]\w*)\s*=\s*#(\d+)\s*',g['eq'])
        if m:
            n=nums[int(m.group(2))];v=n.value/100 if g.get('scale')=='percent' else n.value
            g['eq']=f'{m.group(1)} = {fmt(v) if Fraction(v).denominator==1 else str(Fraction(v).numerator)+"/"+str(Fraction(v).denominator)}'
        if g.get('span'):g['span']=re.sub(r'\{#(\d+)\}',lambda x:nums[int(x.group(1))].raw,g['span'])
        g.pop('scale',None);facts.append(g)
    spec['facts']=facts
    spec['unused']=[{'raw':nums[u['slot']].raw,'why':u['why']} for u in tpl['reading'].get('unused') or []]
    return spec

class Store:
    """learned templates of one individual: <dir>/learned.json, sealed with the sha256 of its body"""
    def __init__(s,d):
        s.dir=Path(d);s.path=s.dir/'learned.json'
    def load(s):
        if not s.path.is_file():return {'schema':SCHEMA,'templates':{}}
        o=json.loads(s.path.read_text(encoding='utf-8'))
        body=json.dumps(o.get('templates',{}),ensure_ascii=False,sort_keys=True)
        if o.get('schema')!=SCHEMA or o.get('sha256')!=hashlib.sha256(body.encode()).hexdigest():raise ValueError('LEARNED_STORE_SEAL')
        return o
    def save(s,o):
        s.dir.mkdir(parents=True,exist_ok=True)
        body=json.dumps(o['templates'],ensure_ascii=False,sort_keys=True)
        o={'schema':SCHEMA,'templates':o['templates'],'sha256':hashlib.sha256(body.encode()).hexdigest()}
        tmp=s.path.with_suffix('.tmp');tmp.write_text(json.dumps(o,ensure_ascii=False,indent=1,sort_keys=True),encoding='utf-8');os.replace(tmp,s.path)
    def find(s,text):
        key=skeleton(text)[0];o=s.load()
        return o['templates'].get(hashlib.sha256(key.encode()).hexdigest()[:24])
    def add(s,spec,provenance):
        tpl=template(spec)
        if tpl is None:return None
        o=s.load();tid=hashlib.sha256(tpl['key'].encode()).hexdigest()[:24]
        old=o['templates'].get(tid)
        if old and json.dumps(old['reading'],sort_keys=True)!=json.dumps(tpl['reading'],sort_keys=True):
            old['conflicts']=old.get('conflicts',0)+1;s.save(o);return None
        if old:
            old['seen']=old.get('seen',1)+1;s.save(o);return tid
        o['templates'][tid]={**tpl,'example':spec['text'],'provenance':provenance,'seen':1,'learned_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
        s.save(o);return tid
    def audit(s):
        """every template must reproduce its own example: instantiate, solve, check"""
        from .solve import solve
        from .check import check
        o=s.load();bad=[]
        for tid,t in o['templates'].items():
            spec=instantiate(t,t['example'])
            r=solve(spec) if spec else {'ok':False}
            c=check(spec,r['values']) if r.get('ok') else {'ok':False}
            if not c.get('ok'):bad.append(tid)
        return {'ok':not bad,'templates':len(o['templates']),'bad':bad}
