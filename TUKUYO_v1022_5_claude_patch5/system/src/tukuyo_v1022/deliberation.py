"""Bounded multi-step deliberation for v1022.1.

This module extends the local core without an LLM.  It recognizes a deliberately
small set of quantitative problem frames, translates each frame to exact rational
steps, and returns a proof object that is independently replayed by proofs.check.
Ambiguous language is rejected rather than guessed.
"""
from __future__ import annotations
import ast,re,unicodedata
from fractions import Fraction
from . import proofs

_NUM=r'(\d+(?:\.\d+)?)'
_UNIT=r'(個|枚|本|冊|台|人)'

def _norm(s):
    s=unicodedata.normalize('NFKC',str(s)).strip()
    return s.replace('％','%').replace('：',':')

def _value(expr):
    return proofs.number(proofs.calculate(expr))

def _proof(frame,steps,answer,givens=None,constraints=None):
    return {'kind':'deliberation','frame':frame,'givens':givens or {},'steps':steps,
            'constraints':constraints or [],'answer':str(answer)}

def _step(label,expr):
    return {'label':label,'expression':expr,'value':_value(expr)}

def _out(frame,steps,givens=None,constraints=None,confidence=.94):
    answer=steps[-1]['value']
    return {'recognized':True,'answer':answer,'confidence':confidence,
            'proof':_proof(frame,steps,answer,givens,constraints)}

def _reject(reason):
    return {'recognized':True,'answer':None,'confidence':0.0,'reason':reason,'proof':None}

def _ambiguous(s):
    return bool(re.search(r'約|およそ|だいたい|大体|ぐらい|くらい|ほど|程度|前後|たぶん|かもしれ|少なくとも|以上|以下|未満|最大|最低|\d+\s*[〜~～]\s*\d+',s))

def _linear_form(node):
    """Return (a,b) for a*x+b using exact rational constants."""
    if isinstance(node,ast.Expression):return _linear_form(node.body)
    if isinstance(node,ast.Name) and node.id=='x':return Fraction(1),Fraction(0)
    if isinstance(node,ast.Constant) and type(node.value) in (int,float):return Fraction(0),Fraction(str(node.value))
    if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
        a,b=_linear_form(node.operand);return (-a,-b) if isinstance(node.op,ast.USub) else (a,b)
    if isinstance(node,ast.BinOp):
        a1,b1=_linear_form(node.left);a2,b2=_linear_form(node.right)
        if isinstance(node.op,ast.Add):return a1+a2,b1+b2
        if isinstance(node.op,ast.Sub):return a1-a2,b1-b2
        if isinstance(node.op,ast.Mult):
            if a1 and a2:raise ValueError('NONLINEAR')
            if a1:return a1*b2,b1*b2
            if a2:return a2*b1,b2*b1
            return Fraction(0),b1*b2
        if isinstance(node.op,ast.Div):
            if a2 or b2==0:raise ValueError('NONLINEAR_OR_ZERO_DIV')
            return a1/b2,b1/b2
    raise ValueError('UNSUPPORTED_LINEAR_AST')

def _linear_equation(s):
    q=re.sub(r'\s+','',s).lower().replace('×','*').replace('÷','/')
    q=re.sub(r'^(?:方程式)?','',q)
    q=re.sub(r'(?:を)?(?:解いて|解け|解きなさい|解いてください)[?？。]*$','',q)
    if not re.fullmatch(r'[0-9x.+\-*/()=]+',q) or q.count('=')!=1 or 'x' not in q:return None
    left,right=q.split('=',1)
    if max(len(left),len(right))>100:return _reject('EQUATION_LIMIT')
    try:
        a1,b1=_linear_form(ast.parse(left,mode='eval'));a2,b2=_linear_form(ast.parse(right,mode='eval'))
        a=a1-a2;b=b2-b1
        if a==0:return _reject('EQUATION_UNDERDETERMINED_OR_INCONSISTENT')
        x=b/a
        if max(x.numerator.bit_length(),x.denominator.bit_length())>120:return _reject('EQUATION_RESULT_LIMIT')
        xs=proofs.number(x)
        steps=[{'label':'collect_linear_terms','expression':f'({proofs.number(b)})/({proofs.number(a)})','value':xs}]
        return _out('linear_equation',steps,{'equation':q,'left':[proofs.number(a1),proofs.number(b1)],'right':[proofs.number(a2),proofs.number(b2)]},confidence=.97)
    except (SyntaxError,ValueError,ZeroDivisionError,OverflowError):return _reject('EQUATION_UNSUPPORTED')

def _rate(s):
    if not re.search(r'時速|km|キロ',s,re.I):return None
    # multi-leg distance: 時速60kmで30分、その後時速40kmで1時間。合計何km?
    legs=list(re.finditer(r'時速\s*'+_NUM+r'\s*(?:km|キロ)(?:/h)?\s*で\s*'+_NUM+r'\s*(時間|分)',s,re.I))
    if len(legs)>=2 and re.search(r'合計|全部|総距離|あわせて|合わせて',s) and re.search(r'何\s*(?:km|キロ)',s,re.I):
        steps=[];terms=[]
        for i,m in enumerate(legs,1):
            v,t=float(m[1]),float(m[2]);expr=f'{m[1]}*{m[2]}' if m[3]=='時間' else f'{m[1]}*{m[2]}/60'
            st=_step(f'leg_{i}_distance',expr);steps.append(st);terms.append(f'({st["value"]})')
        steps.append(_step('total_distance','+'.join(terms)))
        return _out('multi_leg_distance',steps,{'legs':len(legs)},['distance=sum(speed*time)'])
    m=re.search(r'時速\s*'+_NUM+r'\s*(?:km|キロ)(?:/h)?\s*で\s*'+_NUM+r'\s*(時間|分)',s,re.I)
    if m and re.search(r'何\s*(?:km|キロ)|距離',s,re.I):
        expr=f'{m[1]}*{m[2]}' if m[3]=='時間' else f'{m[1]}*{m[2]}/60'
        return _out('rate_distance',[_step('distance',expr)],{'speed_kmh':m[1],'time':m[2],'time_unit':m[3]},['distance=speed*time'])
    m=re.search(_NUM+r'\s*(?:km|キロ)\s*を\s*時速\s*'+_NUM+r'\s*(?:km|キロ)(?:/h)?\s*で',s,re.I)
    if m and re.search(r'何\s*時間|何時間|時間は',s):
        return _out('rate_time',[_step('time_hours',f'{m[1]}/{m[2]}')],{'distance_km':m[1],'speed_kmh':m[2]},['time=distance/speed'])
    m=re.search(_NUM+r'\s*(?:km|キロ)\s*を\s*'+_NUM+r'\s*時間\s*で',s,re.I)
    if m and re.search(r'時速\s*何|速度|時速は',s):
        return _out('rate_speed',[_step('speed_kmh',f'{m[1]}/{m[2]}')],{'distance_km':m[1],'time_hours':m[2]},['speed=distance/time'])
    return None

def _money(s):
    if '円' not in s:return None
    # change after buying N units at P yen each
    m=re.search(r'1\s*'+_UNIT+r'(?:あたり)?\s*'+_NUM+r'\s*円[^。?？]*?'+_NUM+r'\s*\1[^。?？]*?(?:買|購入)',s)
    if m:
        unit,price,count=m[1],m[2],m[3]
        pay=re.search(_NUM+r'\s*円\s*(?:払|支払)',s)
        if pay and re.search(r'おつり|釣り|残り',s):
            cost=_step('purchase_cost',f'{price}*{count}');change=_step('change',f'{pay[1]}-({cost["value"]})')
            if Fraction(change['value'])<0:return _reject('INSUFFICIENT_PAYMENT')
            return _out('unit_price_change',[cost,change],{'unit':unit,'unit_price':price,'count':count,'payment':pay[1]},['cost=unit_price*count','change=payment-cost'])
        if re.search(r'合計|全部|いくら|代金|金額',s):
            return _out('unit_price_total',[_step('purchase_cost',f'{price}*{count}')],{'unit':unit,'unit_price':price,'count':count},['cost=unit_price*count'])
    # percentage price adjustment
    m=re.search(_NUM+r'\s*円[^。?？]*?'+_NUM+r'\s*%\s*(値引き|割引|引き|増し|増加|値上げ)',s)
    if m and re.search(r'いくら|何円|価格|値段',s):
        sign='-' if m[3] in ('値引き','割引','引き') else '+'
        expr=f'{m[1]}*(100{sign}{m[2]})/100'
        return _out('percentage_price',[_step('adjusted_price',expr)],{'base_yen':m[1],'percent':m[2],'direction':m[3]},['percentage_adjustment'])
    return None

def _ratio(s):
    m=re.search(r'([^\s、。]{1,16})と([^\s、。]{1,16})の比(?:は|が)?\s*'+_NUM+r'\s*[:対]\s*'+_NUM,s)
    if not m:return None
    a,b,ra,rb=m[1],m[2],m[3],m[4]
    total=re.search(r'(?:合計|全部で|あわせて|合わせて)\s*'+_NUM+r'\s*(?:個|人|枚|本|冊|台)?',s)
    if not total:return _reject('RATIO_TOTAL_MISSING')
    target=None
    if re.search(re.escape(a)+r'(?:は|が)\s*(?:何|いくつ)',s):target=a;num=ra
    elif re.search(re.escape(b)+r'(?:は|が)\s*(?:何|いくつ)',s):target=b;num=rb
    else:return _reject('RATIO_TARGET_MISSING')
    den=f'{ra}+{rb}';part=_step('one_ratio_scale',f'{total[1]}/({den})');ans=_step('target_amount',f'({part["value"]})*{num}')
    # counts should be integral; otherwise question is under-specified for discrete objects.
    if re.search(r'個|人|枚|本|冊|台',s) and Fraction(ans['value']).denominator!=1:return _reject('RATIO_NONINTEGRAL_COUNT')
    return _out('ratio_partition',[part,ans],{'left':a,'right':b,'ratio_left':ra,'ratio_right':rb,'total':total[1],'target':target},['part=total/(ratio sum)','target=part*ratio'])

def _average(s):
    m=re.search(r'([0-9.,、\s]+)\s*(?:の)?平均',s)
    if not m:return None
    nums=re.findall(r'\d+(?:\.\d+)?',m[1])
    if not 2<=len(nums)<=32 or not re.search(r'何|いくつ|求め',s):return None
    expr='('+ '+'.join(nums)+f')/{len(nums)}'
    return _out('arithmetic_mean',[_step('mean',expr)],{'values':nums},['mean=sum(values)/count'])

def solve(query):
    s=_norm(query)
    if len(s)>1000:return None
    if _ambiguous(s):
        # Only claim recognition if it otherwise looks like one of our quantitative frames.
        if re.search(r'時速|円|の比|平均|\bx\b',s,re.I):return _reject('DELIBERATION_AMBIGUOUS_QUANTITY')
        return None
    for f in (_linear_equation,_rate,_money,_ratio,_average):
        r=f(s)
        if r is not None:return r
    return None
