"""generation 4: learning readings from verified examples.

A reading that was committed by agreement (two Claude readings, or Claude and TUKUYO's own reader, or a reading a
person gave with g4-teach) is kept as a template: the text with every number replaced by a slot, and the reading
with each bound number replaced by the slot of the text number it binds. A later problem whose text is the same
apart from its numbers is read from the template alone, without Claude; the new reading is solved and checked like
any other, so a template can never commit an answer that the checker refuses.

  skeleton(text)          -> (key, ...)               the text with numbers as #0 #1 ...
  template(spec)          -> template | None          from a checked reading
  instantiate(t, text)    -> spec | None              the template read with the numbers of a new text
  Store(dir)              learned templates of one individual (learned.json with a sha256 seal); add, find, contest, audit

A template two parents taught can still be wrong in a way the checker cannot see. When two different parents later
read the same wording to another answer (api.solve asks the other parents when the one asked disagrees with a template),
the template is contested: it is kept, with who contested it, but it no longer reads a problem. Two parents who agree
later may teach that wording again; the contested reading is kept in the new template's history ('replaced').
"""
from __future__ import annotations
import copy,hashlib,json,os,re,time
from fractions import Fraction
from pathlib import Path
from . import numbers as N,own
from .fpl import fmt,load as load_fpl

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
    """the index of the text number inside one occurrence of span that has this value; None when there is none, or when
    two numbers of the span have this value (the template could not tell them apart: '2 grape and 2 banana popsicles')"""
    core=''.join(span.split())
    if not core:return None
    pat=r'\s*'.join(re.escape(c) for c in core)
    for m in re.finditer(pat,t):
        ks=[k for k,n in enumerate(nums) if m.start()<=n.start and n.end<=m.end() and (n.value==value or (n.kind=='percent' and n.value/100==value))]
        if len(ks)==1:return ks[0]
        if ks:return None
    return None

def template(spec):
    """a template from a checked reading, or None when a binding cannot be tied to one text number"""
    key,t,nums,names=skeleton(spec['text'])
    tpl=copy.deepcopy(spec);tpl.pop('text',None)
    facts=[];bound=set()
    _,parsed=load_fpl(spec)
    for f,p in zip(spec['facts'],parsed):
        eq=f['eq'];g=dict(f)
        if p['role']=='binding' and f.get('span') and not f.get('known'):
            v=p['value'];k=_slot_of(t,nums,f['span'],v)
            if k is None:return None
            n=nums[k];bound.add(k)
            g['eq']=f'{p["name"]} = #{k}';g['scale']='percent' if (n.kind=='percent' and n.value/100==v and n.value!=v) else None
        if f.get('span'):g['span']=_span_template(t,nums,f['span'])
        if g.get('span') is None and f.get('span'):return None
        facts.append(g)
    tpl['facts']=facts
    un=[]
    for u in spec.get('unused') or []:
        ks=[k for k,n in enumerate(nums) if n.raw==str(u.get('raw','')).strip()]
        if len(ks)!=1:return None          # none, or two numbers written alike: the template could not tell which
        un.append({'slot':ks[0],'why':u.get('why','')})
    tpl['unused']=un
    return {'key':key,'names':len(names),'numbers':len(nums),'reading':tpl,
            'numeric_roles':[_numeric_role(n) for n in nums],
            'unused_guards':[{'slot':k,'value':str(n.value)} for k,n in enumerate(nums) if k not in bound]}

def _numeric_role(n):return n.kind if n.kind in ('percent','ordinal') else 'amount'

def _transfer_guards(tpl):
    """Legacy entries derive the same conservative guards from their own example."""
    roles=tpl.get('numeric_roles');guards=tpl.get('unused_guards')
    if (roles is None or guards is None) and tpl.get('example'):
        _,_,nums,_=skeleton(tpl['example'])
        bound={int(m[1]) for f in tpl['reading']['facts'] if (m:=re.search(r'=\s*#(\d+)\s*$',f['eq']))}
        if roles is None:roles=[_numeric_role(n) for n in nums]
        if guards is None:guards=[{'slot':k,'value':str(n.value)} for k,n in enumerate(nums) if k not in bound]
    return roles,guards or []

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
    roles,guards=_transfer_guards(tpl)
    if roles is not None and roles!=[_numeric_role(n) for n in nums]:return None
    if any(g['slot']>=len(nums) or str(nums[g['slot']].value)!=g['value'] for g in guards):return None
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
    """learned templates of one individual: <dir>/learned.json, sealed with the sha256 of its body. In a live individual
    the templates are a signed, recovery-tracked commit of its runtime (runtime_store.py: learned.json is then a cache
    that must match the signed head; a rolled-back or edited cache is refused). A store an earlier generation-4 version
    signed with the individual's key (own.py) is taken over by the first commit"""
    def __init__(s,d):
        s.dir=Path(d);s.path=s.dir/'learned.json';s.data=s.dir.parent if s.dir.name=='g4' else None
    def load(s):
        from . import runtime_store
        if runtime_store.is_live(s.dir.parent):return runtime_store.load(s.dir.parent)
        if not s.path.is_file():return {'schema':SCHEMA,'templates':{}}
        o=json.loads(s.path.read_text(encoding='utf-8'))
        body=json.dumps(o.get('templates',{}),ensure_ascii=False,sort_keys=True);sha=hashlib.sha256(body.encode()).hexdigest()
        if o.get('schema')!=SCHEMA or o.get('sha256')!=sha:raise ValueError('LEARNED_STORE_SEAL')
        if s.data is not None:own.check(s.data,'learned',sha,o.get('signed'))
        return o
    def save(s,o):
        s.dir.mkdir(parents=True,exist_ok=True)
        body=json.dumps(o['templates'],ensure_ascii=False,sort_keys=True)
        o={'schema':SCHEMA,'templates':o['templates'],'sha256':hashlib.sha256(body.encode()).hexdigest()}
        from . import runtime_store
        if runtime_store.is_live(s.dir.parent):
            runtime_store.save(s.dir.parent,o);return
        tmp=s.path.with_suffix('.tmp');tmp.write_text(json.dumps(o,ensure_ascii=False,indent=1,sort_keys=True),encoding='utf-8');os.replace(tmp,s.path)
    @staticmethod
    def key_of(text):return hashlib.sha256(skeleton(text)[0].encode()).hexdigest()[:24]
    def find(s,text):
        """the template of this wording; None when there is none, or when its parents taught it two different ways
        (conflicts: suspended). A contested template is returned and marked (api.solve does not read with it)"""
        t=s.load()['templates'].get(s.key_of(text))
        return None if t and t.get('conflicts',0) else t
    def add(s,spec,provenance):
        from .solve import solve
        from .check import check
        r=solve(spec)
        if not r.get('ok') or not check(spec,r['values']).get('ok'):raise ValueError('G4_UNVERIFIED_TEMPLATE')
        tpl=template(spec)
        if tpl is None:return None
        o=s.load();tid=hashlib.sha256(tpl['key'].encode()).hexdigest()[:24]
        old=o['templates'].get(tid);same=False
        if old:
            # the same method with other names or terms in another order is the same reading (methods.py)
            from .methods import equivalent
            comparable={**old};comparable['numeric_roles'],comparable['unused_guards']=_transfer_guards(old)
            same=equivalent(comparable,tpl)
        now=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
        if old and old.get('contested'):
            # a contested wording is taught again only with another reading; the contested one goes to the history
            if same:return None
            hist=list(old.get('replaced') or [])+[{k:old.get(k) for k in ('reading','example','provenance','learned_utc','contested_by')}]
            o['templates'][tid]={**tpl,'example':spec['text'],'provenance':provenance,'seen':1,'learned_utc':now,'replaced':hist}
            s.save(o);return tid
        if old and not same:
            old['conflicts']=old.get('conflicts',0)+1;s.save(o);return None
        if old:
            old['seen']=old.get('seen',1)+1;s.save(o);return tid
        o['templates'][tid]={**tpl,'example':spec['text'],'provenance':provenance,'seen':1,'learned_utc':now}
        s.save(o);return tid
    def contest(s,tid,by):
        """two different parents read this wording to another answer: the template no longer reads a problem"""
        o=s.load();t=o['templates'].get(tid)
        if t is None:return False
        t['contested']=True;t['contested_by']=list(t.get('contested_by') or [])+[{**by,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}]
        s.save(o);return True
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
        return {'ok':not bad,'templates':len(o['templates']),'bad':bad,'contested':sorted(k for k,t in o['templates'].items() if t.get('contested'))}
