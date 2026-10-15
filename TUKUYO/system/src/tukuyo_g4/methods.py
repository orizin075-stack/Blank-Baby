"""Bounded equivalence of learned methods, not a natural-language verifier.

Slot identity, goal, types and cited text must agree. Only polynomial equations
of degree <= 4 are normalized; everything else retains its exact representation.
New instances still go through the solver and the separate FPL checker.
"""
import json,re
from fractions import Fraction as F
from .fpl import parse_eq,parse_unit,FPLError

class Outside(ValueError):pass

def _bounded(p):
    p={m:c for m,c in p.items() if c}
    if len(p)>128 or any(len(m)>4 or max(c.numerator.bit_length(),c.denominator.bit_length())>160 for m,c in p.items()):
        raise Outside('METHOD_POLYNOMIAL_BOUND')
    return p

def _add(a,b,sign=1):
    out=dict(a)
    for m,c in b.items():out[m]=out.get(m,F(0))+sign*c
    return _bounded(out)

def _poly(ast,mapping,work):
    work[0]+=1
    if work[0]>256:raise Outside('METHOD_EXPRESSION_BOUND')
    k=ast[0]
    if k=='n':return _bounded({():ast[1]})
    if k=='v':return {(mapping.get(ast[1],('named',ast[1])),):F(1)}
    if k=='neg':return {m:-c for m,c in _poly(ast[1],mapping,work).items()}
    if k not in ('+','-','*','/'):raise Outside('METHOD_NONPOLYNOMIAL')
    a=_poly(ast[1],mapping,work);b=_poly(ast[2],mapping,work)
    if k in ('+','-'):return _add(a,b,1 if k=='+' else -1)
    if k=='/':
        if set(b)!={()} or b[()]==0:raise Outside('METHOD_VARIABLE_DIVISION')
        return _bounded({m:c/b[()] for m,c in a.items()})
    out={}
    if len(a)*len(b)>512:raise Outside('METHOD_PRODUCT_BOUND')
    for ma,ca in a.items():
        for mb,cb in b.items():
            m=tuple(sorted(ma+mb));out[m]=out.get(m,F(0))+ca*cb
    return _bounded(out)

def signature(tpl):
    """Stable signature; conservative exact fallback outside this finite scope."""
    try:
        r=tpl['reading'];mapping={};slots=[];qs={q['name']:q for q in r['quantities']}
        if len(qs)>32 or len(r['facts'])>64:raise Outside('METHOD_BOUND')
        for f in r['facts']:
            m=re.fullmatch(r'\s*([A-Za-z_]\w*)\s*=\s*#(\d+)\s*',f['eq'])
            if m:
                name=m[1];role=('slot',m[2],f.get('scale') or '')
                if name in mapping or name==r['ask']:raise Outside('METHOD_AMBIGUOUS_BINDING')
                mapping[name]=role;slots.append(role)
        if len(set(slots))!=len(slots):raise Outside('METHOD_SHARED_SLOT')
        mapping[r['ask']]=('goal',)
        types=[]
        for name,q in qs.items():
            role=mapping.get(name,('named',name))
            types.append((role,sorted(parse_unit(q.get('unit')).items()),bool(q.get('integer')),bool(q.get('signed'))))
        facts=[]
        for f in r['facts']:
            eq=re.sub(r'#(\d+)',lambda m:'slot_'+m[1],f['eq'])
            slotmap={**mapping,**{'slot_'+s[1]:('input',s[1],s[2]) for s in slots}}
            left,right=parse_eq(eq);p=_add(_poly(left,slotmap,[0]),_poly(right,slotmap,[0]),-1)
            items=sorted(p.items())
            if items:
                scale=items[0][1];items=[(m,str(c/scale)) for m,c in items]
            facts.append((items,' '.join((f.get('span') or '').split()).lower(),f.get('known') or ''))
        body={'scope':'polynomial_method_v1','key':tpl['key'],'numbers':tpl['numbers'],
              'types':sorted(types),'facts':sorted(facts),'unused':sorted(r.get('unused') or [],key=lambda u:u['slot']),
              'unused_guards':tpl.get('unused_guards',[]),'numeric_roles':tpl.get('numeric_roles'),
              'answer_unit':sorted(parse_unit(r.get('answer_unit')).items())}
        return json.dumps(body,ensure_ascii=False,sort_keys=True)
    except (Outside,FPLError,ValueError,TypeError,KeyError,RecursionError):
        return json.dumps({'scope':'exact','key':tpl.get('key'),'reading':tpl.get('reading'),
                           'unused_guards':tpl.get('unused_guards',[]),'numeric_roles':tpl.get('numeric_roles')},ensure_ascii=False,sort_keys=True)

def equivalent(a,b):return signature(a)==signature(b)
