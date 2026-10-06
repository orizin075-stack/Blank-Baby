"""generation 4: the checker. Written apart from fpl.py and solve.py: it parses every fact again with its own
shunting-yard parser and decides on its own whether a reading and its answer may be committed.

check(spec, values) -> {'ok', 'failures', 'answer', 'unit', 'covered', 'unused'}
  equations  every fact holds exactly at the given values
  unique     the Jacobian of the facts at the values has full column rank: one value for every quantity (for the
             linear facts of word problems this is global uniqueness); floor ceil gcd lcm are locally constant
  sanity     integer quantities are whole; nothing is negative unless the quantity is declared signed
  units      both sides of every fact, both operands of every + and -, and the arguments of min max mod gcd lcm
             have the same unit (a bare number takes the unit it is combined with)
  grounding  every span occurs in the text; a binding's number is a number of the text inside its span; known
             constants are from KNOWN and say what they are; relations use no numbers but 0 1 100; every number
             of the text is bound, optional (the value 1, ordinals) or declared unused with a reason
"""
from __future__ import annotations
import re
from fractions import Fraction
from . import numbers as N
from .fpl import KNOWN,RELATION_LITERALS,parse_unit,unit_str,fmt,SCHEMA

ARITY={'floor':1,'ceil':1,'abs':1,'min':2,'max':2,'gcd':2,'lcm':2,'mod':2}
PREC={'+':1,'-':1,'*':2,'/':2,'u-':3}

def _rpn(s):
    """shunting-yard: infix string -> list of RPN items"""
    out=[];ops=[];prev='op';argc=[]
    for m in re.finditer(r'\d+(?:\.\d+)?|[A-Za-z_]\w*|[-+*/(),]|\S',s):
        t=m.group()
        if t[0].isdigit():out.append(('num',Fraction(t)));prev='val'
        elif t[0].isalpha() or t[0]=='_':
            nxt=s[m.end():].lstrip()[:1]
            if nxt=='(':
                if t not in ARITY:raise ValueError('FUNCTION:'+t)
                ops.append(('fn',t))
            else:out.append(('var',t));prev='val'
        elif t=='(':
            ops.append(('(',None))
            if len(ops)>1 and ops[-2][0]=='fn':argc.append(1)
            prev='op'
        elif t==',':
            while ops and ops[-1][0]!='(':out.append(ops.pop())
            if not argc:raise ValueError('COMMA')
            argc[-1]+=1;prev='op'
        elif t==')':
            while ops and ops[-1][0]!='(':out.append(ops.pop())
            if not ops:raise ValueError('PAREN')
            ops.pop()
            if ops and ops[-1][0]=='fn':
                f=ops.pop()[1];n=argc.pop()
                if n!=ARITY[f]:raise ValueError('ARITY:'+f)
                out.append(('call',f,n))
            prev='val'
        elif t in '+-*/':
            op='u-' if t=='-' and prev=='op' else ('u+' if t=='+' and prev=='op' else t)
            if op=='u+':continue
            while ops and ops[-1][0]=='op' and (PREC[ops[-1][1]]>PREC[op] or PREC[ops[-1][1]]==PREC[op] and op!='u-'):out.append(ops.pop())
            ops.append(('op',op));prev='op'
        else:raise ValueError('CHARACTER:'+t)
    while ops:
        o=ops.pop()
        if o[0]=='(':raise ValueError('PAREN')
        out.append(o)
    return out

def _tree(s):
    st=[]
    for it in _rpn(s):
        if it[0] in ('num','var'):st.append(it)
        elif it[0]=='call':
            n=it[2];args=st[-n:];del st[-n:];st.append(('call',it[1],args))
        elif it[1]=='u-':st.append(('neg',st.pop()))
        else:b=st.pop();a=st.pop();st.append(('bin',it[1],a,b))
    if len(st)!=1:raise ValueError('EXPRESSION')
    return st[0]

def _ev(t,v):
    k=t[0]
    if k=='num':return t[1]
    if k=='var':return v[t[1]]
    if k=='neg':return -_ev(t[1],v)
    if k=='bin':
        a,b=_ev(t[2],v),_ev(t[3],v);op=t[1]
        if op=='+':return a+b
        if op=='-':return a-b
        if op=='*':return a*b
        if b==0:raise ZeroDivisionError()
        return a/b
    a=[_ev(x,v) for x in t[2]];f=t[1]
    if f=='floor':return Fraction(a[0].numerator//a[0].denominator)
    if f=='ceil':return Fraction(-((-a[0].numerator)//a[0].denominator))
    if f=='abs':return abs(a[0])
    if f=='min':return min(a)
    if f=='max':return max(a)
    if any(x.denominator!=1 for x in a):raise ValueError('INTEGER_FUNCTION')
    x,y=int(a[0]),int(a[1])
    if f=='mod':return Fraction(x%y)
    g=x
    while y:g,y=y,g%y
    if f=='gcd':return Fraction(abs(g))
    return Fraction(abs(int(a[0])*int(a[1]))//abs(g)) if g else Fraction(0)

def _d(t,x,v):
    k=t[0]
    if k=='num':return Fraction(0)
    if k=='var':return Fraction(1 if t[1]==x else 0)
    if k=='neg':return -_d(t[1],x,v)
    if k=='bin':
        op=t[1];da,db=_d(t[2],x,v),_d(t[3],x,v)
        if op=='+':return da+db
        if op=='-':return da-db
        a,b=_ev(t[2],v),_ev(t[3],v)
        if op=='*':return da*b+a*db
        return (da*b-a*db)/(b*b)
    f=t[1]
    if f in ('floor','ceil','gcd','lcm'):return Fraction(0)
    if f=='abs':
        a=_ev(t[2][0],v);return _d(t[2][0],x,v)*(1 if a>0 else -1 if a<0 else 0)
    if f in ('min','max'):
        a,b=(_ev(y,v) for y in t[2]);pick=(a<=b)==(f=='min');return _d(t[2][0 if pick else 1],x,v)
    if f=='mod':                                   # a - b*floor(a/b)
        a,b=(_ev(y,v) for y in t[2]);return _d(t[2][0],x,v)-_d(t[2][1],x,v)*Fraction((a/b).numerator//(a/b).denominator)
    raise ValueError('DERIVATIVE')

def _rank(m):
    m=[r[:] for r in m];rank=0;cols=len(m[0]) if m else 0
    for c in range(cols):
        p=next((i for i in range(rank,len(m)) if m[i][c]!=0),None)
        if p is None:continue
        m[rank],m[p]=m[p],m[rank]
        for i in range(rank+1,len(m)):
            if m[i][c]!=0:
                f=m[i][c]/m[rank][c];m[i]=[a-f*b for a,b in zip(m[i],m[rank])]
        rank+=1
    return rank

def _unit(t,qs):
    """unit of an expression: a dict, or None for a bare number that takes the unit it is combined with"""
    k=t[0]
    if k=='num':return None
    if k=='var':return qs[t[1]]
    if k=='neg':return _unit(t[1],qs)
    if k=='bin':
        a,b=_unit(t[2],qs),_unit(t[3],qs);op=t[1]
        if op in '+-':return _same(a,b)
        a=a or {};b=b or {};out=dict(a)
        for u,e in b.items():
            out[u]=out.get(u,0)+(e if op=='*' else -e)
            if out[u]==0:del out[u]
        return out
    us=[_unit(x,qs) for x in t[2]]
    return us[0] if len(us)==1 else _same(*us)

class _UnitClash(Exception):pass
def _same(a,b):
    if a is None:return b
    if b is None:return a
    if a!=b:raise _UnitClash(unit_str(a)+' vs '+unit_str(b))
    return a

def _locate(text,span):
    core=re.sub(r'\s+','',(span or '').translate(N._FW))
    if not core:return []
    pat=r'\s*'.join(re.escape(ch) for ch in core)
    return [(m.start(),m.end()) for m in re.finditer(pat,text.translate(N._FW))]

def check(spec,values):
    fails=[];out={'ok':False,'failures':fails}
    if not isinstance(spec,dict) or spec.get('schema')!=SCHEMA:fails.append('SCHEMA');return out
    text=spec.get('text') or ''
    try:
        qmeta={q['name']:q for q in spec['quantities']}
        qs={n:parse_unit(q.get('unit')) for n,q in qmeta.items()}
        facts=[(f,_tree(f['eq'].split('=')[0]),_tree(f['eq'].split('=')[1])) for f in spec['facts'] if f['eq'].count('=')==1]
        if len(facts)!=len(spec['facts']):fails.append('EQUATION_FORM')
        v={n:Fraction(values[n]) for n in qmeta}
    except Exception as e:  # noqa: BLE001 - any malformed reading is a failure, never an exception
        fails.append('MALFORMED:'+type(e).__name__);return out
    names=list(qmeta)
    # equations, sanity
    for f,l,r in facts:
        try:
            if _ev(l,v)!=_ev(r,v):fails.append('EQUATION_FALSE:'+f['eq'])
        except Exception as e:fails.append('EQUATION_ERROR:'+f['eq']+':'+type(e).__name__)  # noqa: BLE001
    for n,q in qmeta.items():
        if q.get('integer') and v[n].denominator!=1:fails.append('NOT_WHOLE:'+n)
        if v[n]<0 and not q.get('signed'):fails.append('NEGATIVE:'+n)
    # uniqueness
    try:
        jac=[[_d(l,x,v)-_d(r,x,v) for x in names] for f,l,r in facts]
        rk=_rank(jac)
        if rk<len(names):fails.append(f'NOT_UNIQUE:rank {rk} of {len(names)}')
    except Exception as e:fails.append('JACOBIAN:'+type(e).__name__)  # noqa: BLE001
    # units
    for f,l,r in facts:
        try:_same(_unit(l,qs),_unit(r,qs))
        except _UnitClash as e:fails.append('UNITS:'+f['eq']+':'+str(e))
    # grounding
    nums=N.find(text);covered=set();unused=[]
    def lits(t,acc):
        if t[0]=='num':acc.append(t[1])
        elif t[0]=='neg':lits(t[1],acc)
        elif t[0]=='bin':lits(t[2],acc);lits(t[3],acc)
        elif t[0]=='call':[lits(a,acc) for a in t[2]]
        return acc
    for f,l,r in facts:
        bind=None
        for a,b in ((l,r),(r,l)):
            if a[0]=='var' and b[0]=='num':bind=(a[1],b[1])
            elif a[0]=='var' and b[0]=='bin' and b[1]=='/' and b[2][0]=='num' and b[3][0]=='num' and b[3][1]!=0:bind=(a[1],b[2][1]/b[3][1])
        if bind and f.get('known') is not None:
            if bind[1] not in KNOWN or not str(f.get('known')).strip():fails.append('KNOWN_CONSTANT:'+f['eq'])
            continue
        if bind:
            spots=_locate(text,f.get('span'))
            if not spots:fails.append('SPAN_NOT_IN_TEXT:'+f['eq']);continue
            hit=[i for i,n in enumerate(nums) if any(s<=n.start and n.end<=e for s,e in spots) and
                 (n.value==bind[1] or n.kind=='percent' and n.value/100==bind[1])]
            if not hit:fails.append('NUMBER_NOT_IN_SPAN:'+f['eq']);continue
            covered.update(hit)
        else:
            bad=[x for x in lits(l,[])+lits(r,[]) if x not in RELATION_LITERALS]
            if bad:fails.append('NUMBER_IN_RELATION:'+f['eq'])
            if not _locate(text,f.get('span')):fails.append('SPAN_NOT_IN_TEXT:'+f['eq'])
    declared=spec.get('unused') or []
    for u in declared:
        raw=str((u or {}).get('raw','')).strip()
        if not str((u or {}).get('why','')).strip():fails.append('UNUSED_WITHOUT_REASON:'+raw);continue
        m=[i for i,n in enumerate(nums) if n.raw==raw or (N.find(raw) and N.find(raw)[0].value==n.value and len(N.find(raw))==1)]
        if not m:fails.append('UNUSED_NOT_IN_TEXT:'+raw)
        unused.extend(m)
    for i,n in enumerate(nums):
        if i in covered or i in unused or N.optional(n):continue
        fails.append('NUMBER_NOT_ACCOUNTED:'+n.raw)
    ask=spec.get('ask')
    out.update({'ok':not fails,'answer':fmt(v[ask]) if ask in v else None,'unit':qmeta.get(ask,{}).get('unit',''),
                'covered':sorted(nums[i].raw for i in covered),'unused':sorted({nums[i].raw for i in unused})})
    return out
