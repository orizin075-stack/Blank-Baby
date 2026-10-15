"""Independent checker for v1022.3 equation-graph answers.

This module intentionally does not import meta_reasoning.py.  It independently
parses the restricted equation language and computes the set of reachable target
values by bounded recursive substitution.  A proposed answer is supported only
when at least one derivation exists and all successful derivations agree.
"""
from __future__ import annotations
import ast,itertools,re,unicodedata
from fractions import Fraction
ID=r'[^\W\d]\w*'
class VerificationLimit(ValueError):pass

def _norm(s):return unicodedata.normalize('NFKC',str(s)).strip().replace('×','*').replace('÷','/').replace('−','-')
def _parts(s):return [x.strip() for x in re.split(r'[。；;\n]+',s) if x.strip()]
def _goal(parts):
    ident_re=re.compile(rf'^{ID}$',re.I)
    for p in reversed(parts):
        q=p.strip()
        m=re.fullmatch(r'(.+?)\s*は\s*(?:何|いくつ|求めて|求める|求めよ|\?+)[?？]*',q,re.I)
        if m and ident_re.fullmatch(m.group(1).strip()):return m.group(1).strip()
        m=re.fullmatch(r'(.+?)\s*(?:を)?\s*(?:求めて|求める|求めよ)[?？]*',q,re.I)
        if m and ident_re.fullmatch(m.group(1).strip()):return m.group(1).strip()
        m=re.fullmatch(r'(.+?)\s*[?？]+',q,re.I)
        if m and ident_re.fullmatch(m.group(1).strip()):return m.group(1).strip()
        m=re.fullmatch(r'(?:求める|求めよ|goal)\s*[:=]\s*(.+?)[?？]*',q,re.I)
        if m and ident_re.fullmatch(m.group(1).strip()):return m.group(1).strip()
    return None

def _compile(e):
    if len(e)>240:raise ValueError
    t=ast.parse(e,mode='eval');names=set()
    def chk(n,d=0):
        if d>20:raise ValueError
        if isinstance(n,ast.Expression):return chk(n.body,d+1)
        if isinstance(n,ast.Constant) and type(n.value) in (int,float):
            if abs(Fraction(str(n.value)))>10**12:raise ValueError
            return
        if isinstance(n,ast.Name):names.add(n.id);return
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.UAdd,ast.USub)):return chk(n.operand,d+1)
        if isinstance(n,ast.BinOp) and isinstance(n.op,(ast.Add,ast.Sub,ast.Mult,ast.Div,ast.Pow)):chk(n.left,d+1);chk(n.right,d+1);return
        raise ValueError
    chk(t);return t,sorted(names)
def _ev(t,env):
    def bounded(v):
        if max(v.numerator.bit_length(),v.denominator.bit_length())>160:raise ValueError
        return v
    def r(n):
        if isinstance(n,ast.Expression):return r(n.body)
        if isinstance(n,ast.Constant):return Fraction(str(n.value))
        if isinstance(n,ast.Name):return env[n.id]
        if isinstance(n,ast.UnaryOp):
            v=r(n.operand);return -v if isinstance(n.op,ast.USub) else v
        a=r(n.left);b=r(n.right)
        if isinstance(n.op,ast.Add):return bounded(a+b)
        if isinstance(n.op,ast.Sub):return bounded(a-b)
        if isinstance(n.op,ast.Mult):return bounded(a*b)
        if isinstance(n.op,ast.Div):return bounded(a/b)
        if isinstance(n.op,ast.Pow):
            if b.denominator!=1 or abs(b)>6:raise ValueError
            return bounded(a**int(b))
        raise ValueError
    return r(t)
def _vals(v,defs,stack=(),depth=0,budget=None,memo=None):
    budget=[0] if budget is None else budget;memo={} if memo is None else memo
    budget[0]+=1
    if budget[0]>4096 or depth>16:raise VerificationLimit
    if v in stack or v not in defs:return set()
    key=(v,stack)
    if key in memo:return memo[key]
    out=set()
    for t,deps in defs[v]:
        rows=[];bad=False
        for d in deps:
            z=_vals(d,defs,stack+(v,),depth+1,budget,memo)
            if not z:bad=True;break
            rows.append((d,sorted(z)))
        if bad:continue
        combos=[()] if not rows else itertools.product(*[[(n,x) for x in vs] for n,vs in rows])
        for c in combos:
            budget[0]+=1
            if budget[0]>4096:raise VerificationLimit
            try:out.add(_ev(t,{n:x for n,x in c}))
            except (ValueError,KeyError,ZeroDivisionError,OverflowError):pass
            if len(out)>32:raise VerificationLimit
    memo[key]=out
    return out
def _fmt(v):return str(v.numerator) if v.denominator==1 else format(float(v),'.12g')
def verify(query,answer):
    try:
        s=_norm(query)
        if len(s)>5000:raise VerificationLimit
        parts=_parts(s);goal=_goal(parts)
        if not goal:return {'recognized':False,'decidable':False,'supported':False,'reason':'NO_META_FRAME'}
        defs={}
        for p in parts:
            if _goal([p]):continue
            m=re.fullmatch(rf'({ID})\s*=\s*(.+)',p)
            if not m:continue
            t,names=_compile(m.group(2));defs.setdefault(m.group(1),[]).append((t,names))
            if sum(map(len,defs.values()))>64:raise VerificationLimit
        if goal not in defs:return {'recognized':True,'decidable':False,'supported':False,'reason':'TARGET_UNDEFINED'}
        vals=_vals(goal,defs)
        if len(vals)!=1:return {'recognized':True,'decidable':False,'supported':False,'reason':'NONUNIQUE_OR_UNREACHABLE','values':sorted(_fmt(v) for v in vals)}
        exp=_fmt(next(iter(vals)))
        return {'recognized':True,'decidable':True,'supported':str(answer)==exp,'expected':exp,'strategy_values':[exp]}
    except VerificationLimit:
        return {'recognized':True,'decidable':False,'supported':False,'reason':'VERIFY_SEARCH_INCOMPLETE'}
    except (SyntaxError,ValueError,TypeError,ZeroDivisionError,OverflowError):
        return {'recognized':True,'decidable':False,'supported':False,'reason':'VERIFY_REJECTED'}
