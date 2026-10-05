"""Independent semantic checker for the v1022.1 bounded deliberation frames.

Intentionally does not import deliberation.py.  It reparses a supported surface
and recomputes the expected answer with Fraction arithmetic.
"""
from __future__ import annotations
import ast,re,unicodedata
from fractions import Fraction

N=r'(\d+(?:\.\d+)?)';U=r'(個|枚|本|冊|台|人)'
def nstr(v):
    v=Fraction(v);return str(v.numerator) if v.denominator==1 else format(float(v),'.12g')
def norm(s):return unicodedata.normalize('NFKC',str(s)).strip().replace('％','%').replace('：',':')
def out(kind,expected,answer):return {'recognized':True,'decidable':True,'supported':str(expected)==str(answer),'expected':str(expected),'kind':kind}
def no(reason='NO_DELIBERATION_FRAME'):return {'recognized':False,'decidable':False,'supported':False,'expected':None,'kind':None,'reason':reason}

def _lin(node):
    if isinstance(node,ast.Expression):return _lin(node.body)
    if isinstance(node,ast.Name) and node.id=='x':return Fraction(1),Fraction(0)
    if isinstance(node,ast.Constant) and type(node.value) in (int,float):return Fraction(0),Fraction(str(node.value))
    if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
        a,b=_lin(node.operand);return (-a,-b) if isinstance(node.op,ast.USub) else (a,b)
    if isinstance(node,ast.BinOp):
        a,b=_lin(node.left);c,d=_lin(node.right)
        if isinstance(node.op,ast.Add):return a+c,b+d
        if isinstance(node.op,ast.Sub):return a-c,b-d
        if isinstance(node.op,ast.Mult):
            if a and c:raise ValueError
            if a:return a*d,b*d
            if c:return c*b,d*b
            return Fraction(0),b*d
        if isinstance(node.op,ast.Div):
            if c or d==0:raise ValueError
            return a/d,b/d
    raise ValueError

def verify(query,answer):
    s=norm(query)
    if re.search(r'約|およそ|だいたい|大体|ぐらい|くらい|ほど|程度|前後|かもしれ|\d+\s*[〜~～]\s*\d+',s):return no('AMBIGUOUS')
    # equation
    q=re.sub(r'\s+','',s).lower().replace('×','*').replace('÷','/')
    q=re.sub(r'^(?:方程式)?','',q);q=re.sub(r'(?:を)?(?:解いて|解け|解きなさい|解いてください)[?？。]*$','',q)
    if re.fullmatch(r'[0-9x.+\-*/()=]+',q or '') and q.count('=')==1 and 'x' in q:
        try:
            l,r=q.split('=',1);a,b=_lin(ast.parse(l,mode='eval'));c,d=_lin(ast.parse(r,mode='eval'));coef=a-c;rhs=d-b
            if coef:return out('DELIBERATION_LINEAR',nstr(rhs/coef),answer)
        except Exception:pass
    # rate/time/distance
    legs=list(re.finditer(r'時速\s*'+N+r'\s*(?:km|キロ)(?:/h)?\s*で\s*'+N+r'\s*(時間|分)',s,re.I))
    if len(legs)>=2 and re.search(r'合計|全部|総距離|あわせて|合わせて',s) and re.search(r'何\s*(?:km|キロ)',s,re.I):
        total=Fraction(0)
        for m in legs:
            v=Fraction(m[1]);t=Fraction(m[2]);total+=v*t if m[3]=='時間' else v*t/Fraction(60)
        return out('DELIBERATION_MULTI_LEG',nstr(total),answer)
    m=re.search(r'時速\s*'+N+r'\s*(?:km|キロ)(?:/h)?\s*で\s*'+N+r'\s*(時間|分)',s,re.I)
    if m and re.search(r'何\s*(?:km|キロ)|距離',s,re.I):
        v=Fraction(m[1]);t=Fraction(m[2]);return out('DELIBERATION_RATE_DISTANCE',nstr(v*t if m[3]=='時間' else v*t/Fraction(60)),answer)
    m=re.search(N+r'\s*(?:km|キロ)\s*を\s*時速\s*'+N+r'\s*(?:km|キロ)(?:/h)?\s*で',s,re.I)
    if m and re.search(r'何\s*時間|何時間|時間は',s):return out('DELIBERATION_RATE_TIME',nstr(Fraction(m[1])/Fraction(m[2])),answer)
    m=re.search(N+r'\s*(?:km|キロ)\s*を\s*'+N+r'\s*時間\s*で',s,re.I)
    if m and re.search(r'時速\s*何|速度|時速は',s):return out('DELIBERATION_RATE_SPEED',nstr(Fraction(m[1])/Fraction(m[2])),answer)
    # unit price / change
    m=re.search(r'1\s*'+U+r'(?:あたり)?\s*'+N+r'\s*円[^。?？]*?'+N+r'\s*\1[^。?？]*?(?:買|購入)',s)
    if m:
        cost=Fraction(m[2])*Fraction(m[3]);pay=re.search(N+r'\s*円\s*(?:払|支払)',s)
        if pay and re.search(r'おつり|釣り|残り',s):return out('DELIBERATION_CHANGE',nstr(Fraction(pay[1])-cost),answer)
        if re.search(r'合計|全部|いくら|代金|金額',s):return out('DELIBERATION_UNIT_PRICE',nstr(cost),answer)
    m=re.search(N+r'\s*円[^。?？]*?'+N+r'\s*%\s*(値引き|割引|引き|増し|増加|値上げ)',s)
    if m and re.search(r'いくら|何円|価格|値段',s):
        base=Fraction(m[1]);pct=Fraction(m[2]);v=base*(Fraction(100)-pct if m[3] in ('値引き','割引','引き') else Fraction(100)+pct)/100
        return out('DELIBERATION_PERCENT_PRICE',nstr(v),answer)
    # ratio partition
    m=re.search(r'([^\s、。]{1,16})と([^\s、。]{1,16})の比(?:は|が)?\s*'+N+r'\s*[:対]\s*'+N,s)
    if m:
        total=re.search(r'(?:合計|全部で|あわせて|合わせて)\s*'+N+r'\s*(?:個|人|枚|本|冊|台)?',s)
        if total:
            num=None
            if re.search(re.escape(m[1])+r'(?:は|が)\s*(?:何|いくつ)',s):num=Fraction(m[3])
            elif re.search(re.escape(m[2])+r'(?:は|が)\s*(?:何|いくつ)',s):num=Fraction(m[4])
            if num is not None:return out('DELIBERATION_RATIO',nstr(Fraction(total[1])*num/(Fraction(m[3])+Fraction(m[4]))),answer)
    # average
    m=re.search(r'([0-9.,、\s]+)\s*(?:の)?平均',s)
    if m and re.search(r'何|いくつ|求め',s):
        xs=re.findall(r'\d+(?:\.\d+)?',m[1])
        if 2<=len(xs)<=32:return out('DELIBERATION_MEAN',nstr(sum((Fraction(x) for x in xs),Fraction(0))/len(xs)),answer)
    return no()
