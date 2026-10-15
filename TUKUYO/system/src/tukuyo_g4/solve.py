"""generation 4: solves a reading exactly (rational arithmetic). Only a unique answer is an answer.

solve(spec) -> {'ok':True,'answer':Fraction,'values':{name:Fraction},'steps':[...]} | {'ok':False,'reason':...}
  propagation  an equation with one unknown left, linear in it, gives that unknown
  elimination  the equations linear in the unknowns that are left are reduced together (Gauss-Jordan); an unknown
               whose row has no free unknown is determined
Both repeat until nothing changes. A function (floor, mod, ...) is evaluated once its arguments are known and is
never inverted. Every declared quantity must end up determined and every equation must then hold exactly
(UNDERDETERMINED / INCONSISTENT otherwise); integer quantities must be whole, and nothing may be negative unless
the quantity is declared signed.
"""
from __future__ import annotations
import math
from fractions import Fraction
from .fpl import load,FPLError,fmt

class _NL(Exception):pass
class _Fail(Exception):pass

def _apply(fn,v):
    if fn=='floor':return Fraction(math.floor(v[0]))
    if fn=='ceil':return Fraction(math.ceil(v[0]))
    if fn=='abs':return abs(v[0])
    if fn=='min':return min(v)
    if fn=='max':return max(v)
    if any(x.denominator!=1 for x in v):raise _Fail('INTEGER_FUNCTION_OF_A_FRACTION')
    a,b=int(v[0]),int(v[1])
    if fn=='gcd':return Fraction(math.gcd(a,b))
    if fn=='lcm':return Fraction(abs(a*b)//math.gcd(a,b) if a and b else 0)
    if fn=='mod':
        if b==0:raise _Fail('DIVISION_BY_ZERO')
        return Fraction(a%b)
    raise _Fail('FUNCTION')

def _lin(a,known):
    """linear form ({name: coefficient}, constant) of an expression, given the known values; _NL if not linear"""
    k=a[0]
    if k=='n':return {},a[1]
    if k=='v':return ({},known[a[1]]) if a[1] in known else ({a[1]:Fraction(1)},Fraction(0))
    if k=='neg':c,d=_lin(a[1],known);return {x:-v for x,v in c.items()},-d
    if k in ('+','-'):
        c1,d1=_lin(a[1],known);c2,d2=_lin(a[2],known);sg=1 if k=='+' else -1;c=dict(c1)
        for x,v in c2.items():
            c[x]=c.get(x,0)+sg*v
            if c[x]==0:del c[x]
        return c,d1+sg*d2
    if k=='*':
        c1,d1=_lin(a[1],known);c2,d2=_lin(a[2],known)
        if c1 and c2:raise _NL()
        c,d,f=(c2,d2,d1) if not c1 else (c1,d1,d2)
        return ({x:v*f for x,v in c.items() if v*f!=0},d*f)
    if k=='/':
        c2,d2=_lin(a[2],known)
        if c2:raise _NL()
        if d2==0:raise _Fail('DIVISION_BY_ZERO')
        c1,d1=_lin(a[1],known);return {x:v/d2 for x,v in c1.items()},d1/d2
    if k=='f':
        vals=[]
        for x in a[2]:
            c,d=_lin(x,known)
            if c:raise _NL()
            vals.append(d)
        return {},_apply(a[1],vals)
    raise _Fail('EXPRESSION')

def _eliminate(rows):
    """rows of ({name: coef}, const) meaning sum(coef*name)+const=0 -> {name: value} for the determined unknowns"""
    cols=sorted({x for c,_ in rows for x in c});m=[[c.get(x,Fraction(0)) for x in cols]+[-d] for c,d in rows]
    piv=[];r=0
    for j in range(len(cols)):
        p=next((i for i in range(r,len(m)) if m[i][j]!=0),None)
        if p is None:continue
        m[r],m[p]=m[p],m[r];pv=m[r][j];m[r]=[x/pv for x in m[r]]
        for i in range(len(m)):
            if i!=r and m[i][j]!=0:f=m[i][j];m[i]=[a-f*b for a,b in zip(m[i],m[r])]
        piv.append(j);r+=1
    for row in m[r:]:
        if row[-1]!=0:raise _Fail('INCONSISTENT')
    out={}
    for i,j in enumerate(piv):
        if all(m[i][k]==0 for k in range(len(cols)) if k!=j):out[cols[j]]=m[i][-1]
    return out

def solve(spec):
    try:qs,facts=load(spec)
    except FPLError as e:return {'ok':False,'reason':'FPL:'+str(e)}
    known={};steps=[]
    try:
        while True:
            rows=[];moved=False
            for f in facts:
                try:c1,d1=_lin(f['lhs'],known);c2,d2=_lin(f['rhs'],known)
                except _NL:continue
                c=dict(c1)
                for x,v in c2.items():
                    c[x]=c.get(x,0)-v
                    if c[x]==0:del c[x]
                d=d1-d2
                if not c:
                    if d!=0:raise _Fail(f'INCONSISTENT:fact {f["i"]}')
                    continue
                if len(c)==1:
                    (x,a),=c.items();known[x]=-d/a;steps.append({'fact':f['i'],'solve':x,'value':fmt(known[x])});moved=True;break
                rows.append((c,d,f['i']))
            if moved:continue
            if rows:
                got=_eliminate([(c,d) for c,d,_ in rows])
                if got:
                    known.update(got);steps.append({'facts':[i for *_,i in rows],'solve':sorted(got),'values':{k:fmt(v) for k,v in sorted(got.items())}});continue
            break
        missing=sorted(set(qs)-set(known))
        if missing:return {'ok':False,'reason':'UNDERDETERMINED:'+','.join(missing),'values':{k:fmt(v) for k,v in known.items()},'steps':steps}
        for f in facts:
            c1,d1=_lin(f['lhs'],known);c2,d2=_lin(f['rhs'],known)
            if c1 or c2 or d1!=d2:return {'ok':False,'reason':f'INCONSISTENT:fact {f["i"]}'}
        for n,q in qs.items():
            v=known[n]
            if q['integer'] and v.denominator!=1:return {'ok':False,'reason':'NOT_WHOLE:'+n,'values':{k:fmt(x) for k,x in known.items()}}
            if v<0 and not q['signed']:return {'ok':False,'reason':'NEGATIVE:'+n,'values':{k:fmt(x) for k,x in known.items()}}
    except _Fail as e:return {'ok':False,'reason':str(e)}
    return {'ok':True,'answer':known[spec['ask']],'values':known,'steps':steps}
