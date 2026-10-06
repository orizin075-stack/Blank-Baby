"""generation 4: the formal problem language (FPL), the form every reader writes a problem in.

  {'schema':'tukuyo.g4.fpl/1','lang':'ja','text':<the problem>,
   'quantities':[{'name':'laid','unit':'egg/day','integer':True,'about':'eggs laid per day'}, ...],
   'facts':[{'eq':'laid = 16','span':'1日に16個の卵を生みます'},          binding: a quantity = a number the span states
            {'eq':'min_per_hour = 60','known':'60 minutes in an hour'},   known constant (KNOWN values only)
            {'eq':'left = laid - eaten - baked','span':'残りを'}],        relation: names and the numbers 0 1 100 only
   'ask':'income',
   'unused':[{'raw':'2020','why':'the year is not an amount'}]}           numbers of the text a reading leaves out

The discipline makes a reading checkable: every number of the text is bound by a fact whose span contains it (or
is declared unused), every relation is written over named quantities, every quantity has a unit, and the units of
every equation agree. check.py verifies all of it independently of how the reading was made.

Expressions: numbers, names, + - * / ( ), floor ceil abs min max gcd lcm mod.
"""
from __future__ import annotations
import re
from fractions import Fraction

SCHEMA='tukuyo.g4.fpl/1'
FUNCS={'floor':1,'ceil':1,'abs':1,'min':2,'max':2,'gcd':2,'lcm':2,'mod':2}
KNOWN={Fraction(v) for v in (2,3,4,7,10,12,16,24,36,52,60,100,365,366,1000,1760,5280)}
RELATION_LITERALS={Fraction(0),Fraction(1),Fraction(100)}
NAME=re.compile(r'[A-Za-z_][A-Za-z0-9_]*\Z')
_TOK=re.compile(r'\s*(?:(\d+(?:\.\d+)?)|([A-Za-z_][A-Za-z0-9_]*)|(.))')

class FPLError(ValueError):pass

# ----------------------------------------------------------------------------- expressions
def tokens(s):
    out=[];pos=0;s=s.strip()
    while pos<len(s):
        m=_TOK.match(s,pos)
        if not m or m.end()==pos:break
        pos=m.end()
        if m.group(1):out.append(('n',Fraction(m.group(1))))
        elif m.group(2):out.append(('v',m.group(2)))
        elif m.group(3) in '+-*/(),=':out.append(('o',m.group(3)))
        elif m.group(3).strip():raise FPLError('BAD_CHARACTER:'+m.group(3))
    return out

class _P:
    def __init__(s,toks):s.t=toks;s.i=0
    def peek(s):return s.t[s.i] if s.i<len(s.t) else ('end',None)
    def take(s,kind=None,val=None):
        k,v=s.peek()
        if (kind and k!=kind) or (val is not None and v!=val):raise FPLError(f'EXPECTED_{val or kind}')
        s.i+=1;return v
    def expr(s):
        a=s.term()
        while s.peek() in (('o','+'),('o','-')):op=s.take();a=(op,a,s.term())
        return a
    def term(s):
        a=s.factor()
        while s.peek() in (('o','*'),('o','/')):op=s.take();a=(op,a,s.factor())
        return a
    def factor(s):
        k,v=s.peek()
        if (k,v)==('o','-'):s.take();return ('neg',s.factor())
        if (k,v)==('o','+'):s.take();return s.factor()
        if (k,v)==('o','('):s.take();a=s.expr();s.take('o',')');return a
        if k=='n':s.take();return ('n',v)
        if k=='v':
            s.take()
            if s.peek()==('o','('):
                if v not in FUNCS:raise FPLError('UNKNOWN_FUNCTION:'+v)
                s.take();args=[s.expr()]
                while s.peek()==('o',','):s.take();args.append(s.expr())
                s.take('o',')')
                if len(args)!=FUNCS[v]:raise FPLError('ARITY:'+v)
                return ('f',v,args)
            return ('v',v)
        raise FPLError('UNEXPECTED_TOKEN')

def parse_expr(s):
    p=_P(tokens(s));a=p.expr()
    if p.i!=len(p.t):raise FPLError('TRAILING_TOKENS')
    return a

def parse_eq(s):
    if s.count('=')!=1:raise FPLError('ONE_EQUALS_SIGN_REQUIRED')
    l,r=s.split('=');return parse_expr(l),parse_expr(r)

def names(a,out=None):
    out=set() if out is None else out
    if a[0]=='v':out.add(a[1])
    elif a[0]=='f':[names(x,out) for x in a[2]]
    elif a[0]!='n':[names(x,out) for x in a[1:]]
    return out

def literals(a,out=None):
    out=[] if out is None else out
    if a[0]=='n':out.append(a[1])
    elif a[0]=='f':[literals(x,out) for x in a[2]]
    elif a[0]!='v':[literals(x,out) for x in a[1:]]
    return out

def show(a):
    k=a[0]
    if k=='n':return fmt(a[1])
    if k=='v':return a[1]
    if k=='neg':return '-'+show(a[1])
    if k=='f':return a[1]+'('+', '.join(show(x) for x in a[2])+')'
    return '('+show(a[1])+f' {k} '+show(a[2])+')'

def fmt(v):
    v=Fraction(v)
    if v.denominator==1:return str(v.numerator)
    d=v.denominator
    while d%2==0:d//=2
    while d%5==0:d//=5
    if d==1:return format(v.numerator/v.denominator,'.12g') if len(str(v.denominator))<=12 else f'{v.numerator}/{v.denominator}'
    return f'{v.numerator}/{v.denominator}'

# ----------------------------------------------------------------------------- units
def parse_unit(u):
    """'dollar/egg', 'km/hour', 'm^2', '個', '%' -> {base: exponent}; '%' and '1' and '' are dimensionless"""
    u=(u or '').strip()
    out={}
    if u in ('','1','%','percent','パーセント','割'):return out
    parts=re.split(r'\s*([*/])\s*',u);sign=1
    for i,p in enumerate(parts):
        if p=='*':sign=1;continue
        if p=='/':sign=-1;continue
        m=re.fullmatch(r'(.+?)(?:\^(-?\d+))?',p.strip())
        if not m or not m.group(1).strip():raise FPLError('BAD_UNIT:'+u)
        base=unit_base(m.group(1));exp=int(m.group(2) or 1)*sign
        if base in ('1','%'):continue
        out[base]=out.get(base,0)+exp
        if out[base]==0:del out[base]
    return out

def unit_base(w):
    w=w.strip().lower()
    if re.fullmatch(r'[a-z]+',w) and len(w)>3:
        if re.search(r'(sses|xes|ches|shes)$',w):w=w[:-2]
        elif w.endswith('ies') and len(w)>4:w=w[:-3]+'y'
        elif w.endswith('s') and not w.endswith('ss'):w=w[:-1]
    return w

def unit_str(d):
    num=[k if v==1 else f'{k}^{v}' for k,v in sorted(d.items()) if v>0]
    den=[k if v==-1 else f'{k}^{-v}' for k,v in sorted(d.items()) if v<0]
    return ('*'.join(num) or '1')+('/'+'/'.join(den) if den else '')

# ----------------------------------------------------------------------------- the reading
def load(spec):
    """validates a reading; returns (quantities, facts) with parsed equations and each fact's role, or raises FPLError"""
    if not isinstance(spec,dict) or spec.get('schema')!=SCHEMA:raise FPLError('SCHEMA')
    if not isinstance(spec.get('text'),str) or not spec['text'].strip():raise FPLError('TEXT')
    qs={}
    for q in spec.get('quantities') or []:
        n=q.get('name') if isinstance(q,dict) else None
        if not isinstance(n,str) or not NAME.match(n) or n in FUNCS:raise FPLError('BAD_NAME:'+str(n))
        if n in qs:raise FPLError('DUPLICATE_NAME:'+n)
        qs[n]={'name':n,'unit':parse_unit(q.get('unit')),'unit_text':q.get('unit') or '','integer':bool(q.get('integer')),
               'signed':bool(q.get('signed')),'about':str(q.get('about') or '')}
    if not qs:raise FPLError('NO_QUANTITIES')
    if spec.get('ask') not in qs:raise FPLError('ASK_NOT_A_QUANTITY')
    facts=[]
    for i,f in enumerate(spec.get('facts') or []):
        if not isinstance(f,dict) or not isinstance(f.get('eq'),str):raise FPLError(f'FACT_{i}')
        l,r=parse_eq(f['eq'])
        unknown=(names(l)|names(r))-set(qs)
        if unknown:raise FPLError('UNDECLARED:'+','.join(sorted(unknown)))
        role='relation';value=None;qname=None
        for a,b in ((l,r),(r,l)):
            if a[0]=='v' and b[0]=='n':role='binding';qname=a[1];value=b[1]
            elif a[0]=='v' and b[0]=='/' and b[1][0]=='n' and b[2][0]=='n' and b[2][1]!=0:role='binding';qname=a[1];value=b[1][1]/b[2][1]
        if role=='binding' and f.get('known') is not None:role='known'
        facts.append({'i':i,'eq':f['eq'],'lhs':l,'rhs':r,'role':role,'name':qname,'value':value,'span':f.get('span'),'known':f.get('known')})
    if not facts:raise FPLError('NO_FACTS')
    return qs,facts
