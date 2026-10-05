"""Independent bounded verifier for v1022.2 hypothesis induction.

It intentionally does not import tukuyo_v1022.hypothesis.
"""
from __future__ import annotations
import re,unicodedata
from fractions import Fraction

N=r'[-+]?\d+(?:\.\d+)?'
def norm(s):return unicodedata.normalize('NFKC',str(s)).strip().replace('−','-').replace('→','->')
def ns(v):
    v=Fraction(v);return str(v.numerator) if v.denominator==1 else format(float(v),'.12g')
def ev(c,x):c0,c1,c2=c;x=Fraction(x);return c0+c1*x+c2*x*x

def pairs(s):
    z=[]
    for m in re.finditer(rf'(?<![A-Za-z0-9_])x\s*=\s*({N})\s*(?:のとき|なら|->|,|、|;|；)?\s*y\s*=\s*({N})',s,re.I):z.append((Fraction(m[1]),Fraction(m[2])))
    for m in re.finditer(rf'入力\s*({N})\s*(?:->|なら|のとき|で)\s*(?:出力\s*)?({N})',s):z.append((Fraction(m[1]),Fraction(m[2])))
    out=[]
    for p in z:
        if p not in out:out.append(p)
    return out

def target(s,ps):
    zs=[]
    for m in re.finditer(rf'(?<![A-Za-z0-9_])x\s*=\s*({N})[^。?？]*?(?:y|出力)(?:\s*(?:は|=))?\s*(?:何|いくつ|\?)',s,re.I):zs.append(Fraction(m[1]))
    for m in re.finditer(rf'入力\s*({N})[^。?？]*?(?:出力|答え)(?:\s*は)?\s*(?:何|いくつ|\?)',s):zs.append(Fraction(m[1]))
    if not zs:return None
    xs={x for x,_ in ps};fresh=[x for x in zs if x not in xs];return (fresh or zs)[-1]

def candidates(ps):
    if len(ps)<2:return []
    x0,y0=ps[0];raw=[]
    def a(c):
        if all(ev(c,x)==y for x,y in ps):raw.append(c)
    a((y0,Fraction(0),Fraction(0)));a((Fraction(0),Fraction(1),Fraction(0)));a((y0-x0,Fraction(1),Fraction(0)))
    if x0:a((Fraction(0),y0/x0,Fraction(0)))
    p=next(((x,y) for x,y in ps[1:] if x!=x0),None)
    if p:
        x1,y1=p;k=(y1-y0)/(x1-x0);a((y0-k*x0,k,Fraction(0)))
    a((y0-x0*x0,Fraction(0),Fraction(1)))
    if x0:a((Fraction(0),Fraction(0),y0/(x0*x0)))
    return list(dict.fromkeys(raw))

def verify(query,answer):
    s=norm(query);ps=pairs(s);tx=target(s,ps)
    if len(ps)<2 or tx is None:return {'recognized':False,'decidable':False,'supported':False,'reason':'NO_HYPOTHESIS_FRAME'}
    if len({x for x,_ in ps})!=len(ps):return {'recognized':True,'decidable':False,'supported':False,'reason':'CONTRADICTORY_OR_DUPLICATE_X'}
    cs=candidates(ps)
    if len(cs)!=1:return {'recognized':True,'decidable':False,'supported':False,'reason':'MODEL_NOT_UNIQUE','candidate_count':len(cs)}
    expected=ns(ev(cs[0],tx))
    return {'recognized':True,'decidable':True,'supported':str(answer)==expected,'expected':expected,'candidate_count':1}
