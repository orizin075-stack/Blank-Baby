"""Independent lexical input reader and algebraic certificate checker.

Only standard-library modules are used: no producer parser, AST, elimination,
learning state or answer generator. This proves a goal over the bounded stated
linear premises, not correctness of arbitrary natural language interpretation.
"""
import re, unicodedata
from fractions import Fraction

class Invalid(ValueError):pass

def _q(s):
    if not isinstance(s,(str,int,Fraction)) or isinstance(s,bool) or len(str(s))>100:raise Invalid('VERIFY_NUMBER')
    v=Fraction(s)
    if max(v.numerator.bit_length(),v.denominator.bit_length())>160:raise Invalid('VERIFY_NUMBER_LIMIT')
    return v

def _sum(a,b,sign=1):
    out=dict(a[1])
    for k,v in b[1].items():
        out[k]=_q(out.get(k,Fraction(0))+sign*v)
        if out[k]==0:del out[k]
    return _q(a[0]+sign*b[0]),out

def _times(a,b):return _q(a[0]*b),{k:_q(v*b) for k,v in a[1].items() if v*b}

def _expr(raw):
    """Recursive-descent lexical reader, independent of Python AST semantics."""
    if len(raw)>240:raise Invalid('VERIFY_EXPRESSION_LIMIT')
    token_re=re.compile(r'\s*(?:(\d+(?:\.\d+)?)|([^\W\d]\w{0,31})|([()+*/-]))')
    tokens=[];offset=0;symbols=set()
    while offset<len(raw):
        if raw[offset:].isspace():break
        match=token_re.match(raw,offset)
        if not match:raise Invalid('VERIFY_UNCOVERED_TOKEN')
        typ='num' if match[1] else 'id' if match[2] else 'op';value=next(x for x in match.groups() if x is not None)
        tokens.append((typ,value));offset=match.end()
        if len(tokens)>96:raise Invalid('VERIFY_TOKEN_LIMIT')
    pos=0
    def factor(depth=0):
        nonlocal pos
        if depth>20 or pos>=len(tokens):raise Invalid('VERIFY_FACTOR')
        typ,val=tokens[pos];pos+=1
        if val in ('+','-'):
            out=factor(depth+1);return _times(out,-1) if val=='-' else out
        if val=='(':
            out=expression(depth+1)
            if pos>=len(tokens) or tokens[pos][1]!=')':raise Invalid('VERIFY_PARENS')
            pos+=1;return out
        if typ=='num':
            v=_q(val)
            if abs(v)>10**12:raise Invalid('VERIFY_LITERAL_LIMIT')
            return v,{}
        if typ=='id':symbols.add(val);return Fraction(0),{val:Fraction(1)}
        raise Invalid('VERIFY_FACTOR')
    def term(depth=0):
        nonlocal pos
        out=factor(depth+1)
        while pos<len(tokens) and tokens[pos][1] in ('*','/'):
            op=tokens[pos][1];pos+=1;rhs=factor(depth+1)
            if op=='*':
                if out[1] and rhs[1]:raise Invalid('VERIFY_NONLINEAR')
                out=_times(out,rhs[0]) if not rhs[1] else _times(rhs,out[0])
            else:
                if rhs[1] or rhs[0]==0:raise Invalid('VERIFY_DIVISION')
                out=_times(out,1/rhs[0])
        return out
    def expression(depth=0):
        nonlocal pos
        out=term(depth+1)
        while pos<len(tokens) and tokens[pos][1] in ('+','-'):
            op=tokens[pos][1];pos+=1;out=_sum(out,term(depth+1),1 if op=='+' else -1)
        return out
    out=expression()
    if pos!=len(tokens):raise Invalid('VERIFY_TRAILING_EXPRESSION')
    return out,symbols

def read(query):
    raw=unicodedata.normalize('NFKC',str(query)).strip().translate(str.maketrans({'×':'*','÷':'/','−':'-'}))
    marker=re.match(r'(制約|連立方程式|constraints)\s*:\s*',raw,re.I)
    first=re.split('[。；;\n]',raw,1)[0]
    prefix=re.split('の(?:合計|平均)は',first,1)
    natural=len(prefix)==2 and 'と' in prefix[0]
    if not marker and not natural:return None
    if len(raw)>5000:raise Invalid('VERIFY_INPUT_LIMIT')
    if marker:raw=raw[marker.end():]
    # Consume a complete goal as the final clause, not the first ? occurrence.
    clauses=[x.strip() for x in re.split('[。；;\n]',raw) if x.strip()]
    if not 2<=len(clauses)<=33:raise Invalid('VERIFY_STATEMENT_LIMIT')
    goal=clauses.pop();g=re.fullmatch(r'(.*?)\s*は\s*(何|いくつ)([個人枚本冊台円])?\s*\?*',goal)
    if g:target,unit=g[1].strip(),g[3] or ''
    else:
        g=re.fullmatch(r'(goal|求める)\s*:\s*([^?]+)\?*',goal,re.I)
        if not g:raise Invalid('VERIFY_GOAL')
        target,unit=g[2].strip(),''
    target_term,variables=_expr(target);eqs=[];units=set()
    # This reader accepts names by lexical checking, rather than producer regex.
    def name(x):
        _,ns=_expr(x)
        if len(ns)!=1 or x not in ns:raise Invalid('VERIFY_RELATION_NAME')
        return x
    def literal(x):
        if not re.fullmatch(r'[+-]?\d+(?:\.\d+)?',x):raise Invalid('VERIFY_RELATION_NUMBER')
        return x
    for statement in clauses:
        lhs=rhs=None;found_unit=''
        if marker:
            sides=statement.split('=')
            if len(sides)!=2:raise Invalid('VERIFY_STATEMENT')
            lhs,rhs=(v.strip() for v in sides)
        else:
            for delimiter,average in (('の合計は',False),('の平均は',True)):
                if delimiter in statement:
                    labels,tail=statement.split(delimiter,1);members=labels.split('と')
                    if not 2<=len(members)<=4:raise Invalid('VERIFY_SUM_ARITY')
                    members=[name(x) for x in members]
                    t=re.fullmatch(r'([+-]?\d+(?:\.\d+)?)([個人枚本冊台円])(?:です|だ)?',tail)
                    if not t:raise Invalid('VERIFY_SUM_VALUE')
                    lhs='+'.join(members);rhs=literal(t[1])+('*'+str(len(members)) if average else '');found_unit=t[2];break
            if lhs is None:
                m=re.fullmatch(r'(.+?)は(.+?)の([+-]?\d+(?:\.\d+)?)倍(?:です|だ)?',statement)
                if m:lhs=name(m[1]);rhs='('+name(m[2])+')*('+literal(m[3])+')'
            if lhs is None:
                m=re.fullmatch(r'(.+?)は(.+?)より([+-]?\d+(?:\.\d+)?)([個人枚本冊台円])(多い|少ない|高い|安い)(?:です|だ)?',statement)
                if m:lhs=name(m[1]);rhs='('+name(m[2])+')'+('+' if m[5] in ('多い','高い') else '-')+'('+literal(m[3])+')';found_unit=m[4]
            if lhs is None:
                m=re.fullmatch(r'(.+?)は([+-]?\d+(?:\.\d+)?)([個人枚本冊台円])(?:です|だ)?',statement)
                if m:lhs=name(m[1]);rhs=literal(m[2]);found_unit=m[3]
            if lhs is None:raise Invalid('VERIFY_UNCOVERED_STATEMENT')
        if found_unit:units.add(found_unit)
        left,n1=_expr(lhs);right,n2=_expr(rhs);variables|=n1|n2;v=_sum(left,right,-1)
        eqs.append({'id':f'E{len(eqs)+1}','source':statement,'coefficients':{k:str(x) for k,x in sorted(v[1].items())},'rhs':str(-v[0])})
    if len(variables)>16:raise Invalid('VERIFY_VARIABLE_LIMIT')
    if marker and unit or not marker and (len(units)!=1 or unit not in units):raise Invalid('VERIFY_UNITS')
    return {'schema':'tukuyo.v1022_6.linear_constraints/1','source_query':str(query),'variables':sorted(variables),'equations':eqs,
            'target':{'expression':target,'coefficients':{k:str(x) for k,x in sorted(target_term[1].items())},'constant':str(target_term[0])},
            'unit':unit,'domain':'nonnegative_integer_counts' if unit and unit!='円' else 'rational',
            'coverage':{'all_statements_consumed':True,'statement_count':len(clauses)+1,'equation_count':len(eqs)}}

def verify(query,answer,proof):
    evidence={'recognized':True,'decidable':False,'supported':False,'independent':True,'mode':'SEPARATE_LEXICAL_INPUT_AND_DUAL_CERTIFICATE'}
    try:
        graph=read(query)
        if graph is None:return {**evidence,'recognized':False,'reason':'OUTSIDE_LINEAR_CONSTRAINT_SCOPE'}
        if not isinstance(proof,dict) or proof.get('kind')!='linear_constraints' or proof.get('source_query')!=str(query) or proof.get('graph')!=graph:raise Invalid('VERIFY_SOURCE_GRAPH_BINDING')
        cert=proof.get('certificate')
        if not isinstance(cert,dict) or set(cert)!={'witness','multipliers','answer'}:raise Invalid('VERIFY_CERTIFICATE_FIELDS')
        variables=graph['variables'];eqs=graph['equations'];target=graph['target'];w=cert['witness'];ms=cert['multipliers']
        if not isinstance(w,dict) or set(w)!=set(variables) or not isinstance(ms,list) or len(ms)!=len(eqs):raise Invalid('VERIFY_CERTIFICATE_SHAPE')
        w={k:_q(v) for k,v in w.items()};ms=[_q(x) for x in ms];claimed=_q(answer)
        if _q(cert['answer'])!=claimed:raise Invalid('VERIFY_ANSWER_BINDING')
        # Feasibility prevents ex falso: a contradictory premise set cannot
        # certify arbitrary answers via a row-space combination.
        for e in eqs:
            if sum(_q(c)*w[k] for k,c in e['coefficients'].items())!=_q(e['rhs']):raise Invalid('VERIFY_INFEASIBLE_WITNESS')
        # Dual equality: the goal is this combination of all stated equations.
        for v in variables:
            c=sum(f*_q(e['coefficients'].get(v,'0')) for f,e in zip(ms,eqs))
            if c!=_q(target['coefficients'].get(v,'0')):raise Invalid('VERIFY_TARGET_NOT_FORCED')
        expected=_q(target['constant'])+sum(f*_q(e['rhs']) for f,e in zip(ms,eqs))
        if expected!=claimed:raise Invalid('VERIFY_COMBINATION_VALUE')
        if graph['unit'] and (any(v<0 for v in w.values()) or claimed<0):raise Invalid('VERIFY_NEGATIVE_QUANTITY')
        if graph['domain']=='nonnegative_integer_counts' and (any(v.denominator!=1 for v in w.values()) or claimed.denominator!=1):raise Invalid('VERIFY_FRACTIONAL_COUNT')
        return {**evidence,'decidable':True,'supported':True,'expected':str(expected),'all_premises_checked':True,'target_uniqueness_certified':True,'unit':graph['unit'],'graph':graph}
    except (Invalid,ValueError,TypeError,KeyError,ZeroDivisionError,OverflowError) as e:
        return {**evidence,'reason':str(e) or 'VERIFY_REJECTED'}

def verify_nonunique(query,proof):
    """Two feasible assignments with distinct target values certify ambiguity."""
    evidence={'recognized':True,'supported':False,'independent':True,'mode':'SEPARATE_INPUT_AND_TWO_FEASIBLE_WITNESSES'}
    try:
        graph=read(query)
        if graph is None:return {**evidence,'recognized':False,'reason':'OUTSIDE_LINEAR_CONSTRAINT_SCOPE'}
        if not isinstance(proof,dict) or proof.get('kind')!='linear_nonunique' or proof.get('source_query')!=str(query) or proof.get('graph')!=graph:
            raise Invalid('VERIFY_SOURCE_GRAPH_BINDING')
        examples=proof.get('witnesses')
        if not isinstance(examples,list) or len(examples)!=2:raise Invalid('VERIFY_AMBIGUITY_WITNESSES')
        values=[]
        for example in examples:
            w=example['assignment']
            if not isinstance(w,dict) or set(w)!=set(graph['variables']):raise Invalid('VERIFY_CERTIFICATE_SHAPE')
            w={k:_q(v) for k,v in w.items()}
            for e in graph['equations']:
                if sum(_q(c)*w[k] for k,c in e['coefficients'].items())!=_q(e['rhs']):raise Invalid('VERIFY_INFEASIBLE_WITNESS')
            value=_q(graph['target']['constant'])+sum(_q(c)*w[k] for k,c in graph['target']['coefficients'].items())
            if _q(example['target_value'])!=value:raise Invalid('VERIFY_WITNESS_TARGET')
            if graph['unit'] and (any(v<0 for v in w.values()) or value<0):raise Invalid('VERIFY_NEGATIVE_QUANTITY')
            if graph['domain']=='nonnegative_integer_counts' and (any(v.denominator!=1 for v in w.values()) or value.denominator!=1):raise Invalid('VERIFY_FRACTIONAL_COUNT')
            values.append(str(value))
        if values[0]==values[1]:raise Invalid('VERIFY_TARGET_NOT_AMBIGUOUS')
        return {**evidence,'supported':True,'all_premises_checked':True,'target_not_unique_certified':True,'target_values':values}
    except (Invalid,ValueError,TypeError,KeyError,ZeroDivisionError,OverflowError) as e:
        return {**evidence,'reason':str(e) or 'VERIFY_REJECTED'}
