"""Goal-directed exact linear constraint reasoning (finite, no eval or LLM).

Explicit 制約: problems treat equalities as simultaneous premises, unlike the
older meta engine's alternative definitions. Every input clause must parse.
An answer can be unique even when individual variables remain undetermined.
Certificates contain a feasible witness and a linear combination forcing the
goal. A separately implemented lexical parser checks those certificates.
"""
from __future__ import annotations
import ast, re, unicodedata
from fractions import Fraction as F

SCHEMA='tukuyo.v1022_6.linear_constraints/1'
MAX_VARIABLES=16
MAX_EQUATIONS=32
MAX_EXPR=240
MAX_BITS=160
IDENT=r'[^\W\d]\w{0,31}'
NUM=r'[+-]?\d+(?:\.\d+)?'
UNIT=r'個|人|枚|本|冊|台|円'

class Reject(ValueError):pass

def _bounded(v):
    v=F(v)
    if max(v.numerator.bit_length(),v.denominator.bit_length())>MAX_BITS:
        raise Reject('CONSTRAINT_ARITHMETIC_LIMIT')
    return v

def _plus(a,b,factor=F(1)):
    c=_bounded(a[0]+factor*b[0]);d=dict(a[1])
    for k,v in b[1].items():
        d[k]=_bounded(d.get(k,F(0))+factor*v)
        if not d[k]:del d[k]
    return c,d

def _scale(a,factor):return _bounded(a[0]*factor),{k:_bounded(v*factor) for k,v in a[1].items() if v*factor}

def _affine(text):
    if not isinstance(text,str) or len(text)>MAX_EXPR:raise Reject('CONSTRAINT_EXPRESSION_LIMIT')
    try:tree=ast.parse(text.strip(),mode='eval')
    except (ValueError,SyntaxError):raise Reject('CONSTRAINT_EXPRESSION_REJECTED')
    names=set();work=[0]
    def walk(n,depth=0):
        work[0]+=1
        if depth>20 or work[0]>96:raise Reject('CONSTRAINT_EXPRESSION_LIMIT')
        if isinstance(n,ast.Expression):return walk(n.body,depth+1)
        if isinstance(n,ast.Constant) and type(n.value) in (int,float):
            token=ast.get_source_segment(text.strip(),n)
            if not token or not re.fullmatch(r'\d+(?:\.\d+)?',token):raise Reject('CONSTRAINT_NUMBER_FORMAT')
            v=_bounded(F(token))
            if abs(v)>10**12:raise Reject('CONSTRAINT_NUMBER_LIMIT')
            return v,{}
        if isinstance(n,ast.Name) and re.fullmatch(IDENT,n.id):
            names.add(n.id);return F(0),{n.id:F(1)}
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.USub,ast.UAdd)):
            a=walk(n.operand,depth+1);return _scale(a,-1) if isinstance(n.op,ast.USub) else a
        if isinstance(n,ast.BinOp):
            a=walk(n.left,depth+1);b=walk(n.right,depth+1)
            if isinstance(n.op,ast.Add):return _plus(a,b)
            if isinstance(n.op,ast.Sub):return _plus(a,b,-1)
            if isinstance(n.op,ast.Mult):
                if a[1] and b[1]:raise Reject('CONSTRAINT_NONLINEAR')
                return _scale(a,b[0]) if not b[1] else _scale(b,a[0])
            if isinstance(n.op,ast.Div) and not b[1] and b[0]:return _scale(a,F(1)/b[0])
        raise Reject('CONSTRAINT_OPERATOR_REJECTED')
    out=walk(tree)
    return out,names

def _goal(clause):
    m=re.fullmatch(r'(.+?)\s*は\s*(?:何|いくつ)(個|人|枚|本|冊|台|円)?\s*[?？]*',clause)
    if m:return m[1].strip(),m[2] or ''
    m=re.fullmatch(r'(?:goal|求める)\s*[:：]\s*(.+?)[?？]*',clause,re.I)
    if m:return m[1].strip(),''
    return None

def parse(query):
    text=unicodedata.normalize('NFKC',str(query)).strip().replace('×','*').replace('÷','/').replace('−','-')
    explicit=bool(re.match(r'^(?:制約|連立方程式|constraints)\s*:',text,re.I))
    natural=bool(re.match(r'^[^。;；\n]{1,160}と[^。;；\n]{1,160}の(?:合計|平均)は',text))
    if not explicit and not natural:return None
    if len(text)>5000:raise Reject('CONSTRAINT_INPUT_LIMIT')
    if explicit:text=re.sub(r'^(?:制約|連立方程式|constraints)\s*:\s*','',text,count=1,flags=re.I)
    parts=[x.strip() for x in re.split(r'[。;；\n]',text) if x.strip()]
    if not 2<=len(parts)<=MAX_EQUATIONS+1:raise Reject('CONSTRAINT_STATEMENT_LIMIT')
    goal=_goal(parts[-1])
    if not goal:raise Reject('CONSTRAINT_GOAL_MISSING')
    target,query_unit=goal;units=set();equations=[];names=set()
    target_value,target_names=_affine(target);names|=target_names
    for clause in parts[:-1]:
        lhs=rhs=None;unit=''
        if explicit:
            if clause.count('=')!=1:raise Reject('CONSTRAINT_UNCOVERED_STATEMENT')
            lhs,rhs=[x.strip() for x in clause.split('=')]
        else:
            m=re.fullmatch(rf'({IDENT}(?:と{IDENT}){{1,3}})の(合計|平均)は({NUM})({UNIT})(?:です|だ)?',clause)
            if m:
                items=m[1].split('と');lhs='+'.join(items);rhs=m[3]+('*'+str(len(items)) if m[2]=='平均' else '');unit=m[4]
            if lhs is None:
                m=re.fullmatch(rf'({IDENT})は({IDENT})の({NUM})倍(?:です|だ)?',clause)
                if m:lhs=m[1];rhs=f'({m[2]})*({m[3]})'
            if lhs is None:
                m=re.fullmatch(rf'({IDENT})は({IDENT})より({NUM})({UNIT})(多い|少ない|高い|安い)(?:です|だ)?',clause)
                if m:
                    lhs=m[1];rhs=f'({m[2]})'+('+' if m[5] in ('多い','高い') else '-')+f'({m[3]})';unit=m[4]
            if lhs is None:
                m=re.fullmatch(rf'({IDENT})は({NUM})({UNIT})(?:です|だ)?',clause)
                if m:lhs=m[1];rhs=m[2];unit=m[3]
            if lhs is None:raise Reject('CONSTRAINT_UNCOVERED_STATEMENT')
        if unit:units.add(unit)
        a,an=_affine(lhs);b,bn=_affine(rhs);names|=an|bn
        v=_plus(a,b,-1)
        equations.append({'id':f'E{len(equations)+1}','source':clause,'coefficients':{k:str(x) for k,x in sorted(v[1].items())},'rhs':str(-v[0])})
    if len(names)>MAX_VARIABLES:raise Reject('CONSTRAINT_VARIABLE_LIMIT')
    if not explicit and (len(units)!=1 or query_unit not in units):raise Reject('CONSTRAINT_UNIT_MISMATCH')
    if explicit and query_unit:raise Reject('CONSTRAINT_UNDECLARED_UNIT')
    return {'schema':SCHEMA,'source_query':str(query),'variables':sorted(names),'equations':equations,
            'target':{'expression':target,'coefficients':{k:str(x) for k,x in sorted(target_value[1].items())},'constant':str(target_value[0])},
            'unit':query_unit,'domain':'nonnegative_integer_counts' if query_unit and query_unit!='円' else 'rational',
            'coverage':{'all_statements_consumed':True,'statement_count':len(parts),'equation_count':len(equations)}}

def _eliminate(graph):
    vs=graph['variables'];n=len(vs);eqs=graph['equations'];m=len(eqs)
    matrix=[[F(e['coefficients'].get(v,0)) for v in vs]+[F(e['rhs'])] for e in eqs]
    trace=[[F(int(i==j)) for j in range(m)] for i in range(m)]
    pivots=[];row=0
    for col in range(n):
        hit=next((i for i in range(row,m) if matrix[i][col]),None)
        if hit is None:continue
        matrix[row],matrix[hit]=matrix[hit],matrix[row];trace[row],trace[hit]=trace[hit],trace[row]
        f=matrix[row][col];matrix[row]=[_bounded(x/f) for x in matrix[row]];trace[row]=[_bounded(x/f) for x in trace[row]]
        for i in range(m):
            if i==row or not matrix[i][col]:continue
            f=matrix[i][col];matrix[i]=[_bounded(a-f*b) for a,b in zip(matrix[i],matrix[row])];trace[i]=[_bounded(a-f*b) for a,b in zip(trace[i],trace[row])]
        pivots.append(col);row+=1
        if row==m:break
    for i in range(m):
        if not any(matrix[i][:n]) and matrix[i][n]:
            return {'reason':'CONSTRAINT_INCONSISTENT','conflict_equations':[eqs[j]['id'] for j,x in enumerate(trace[i]) if x],
                    'contradiction_certificate':{'multipliers':[str(x) for x in trace[i]],'nonzero_constant':str(matrix[i][n])}}
    witness=[F(0)]*n
    for i,c in enumerate(pivots):witness[c]=matrix[i][n]
    target=graph['target'];coeff=[F(target['coefficients'].get(v,0)) for v in vs]
    remainder=list(coeff);multipliers=[F(0)]*m;value=F(target['constant'])
    for i,c in enumerate(pivots):
        f=remainder[c]
        if not f:continue
        remainder=[_bounded(a-f*b) for a,b in zip(remainder,matrix[i][:n])]
        multipliers=[_bounded(a+f*b) for a,b in zip(multipliers,trace[i])];value=_bounded(value+f*matrix[i][n])
    if any(remainder):
        free=next(i for i,x in enumerate(remainder) if x);direction=[F(0)]*n;direction[free]=F(1)
        for i,c in enumerate(pivots):direction[c]=-matrix[i][free]
        second=[_bounded(a+b) for a,b in zip(witness,direction)]
        return {'reason':'CONSTRAINT_UNDERDETERMINED','free_variables':[vs[i] for i in range(n) if i not in pivots],
                'information_requests':[f'{vs[free]}を含む独立した条件が必要です'],
                'counterexamples':[{'assignment':{v:str(x) for v,x in zip(vs,w)},'target_value':str(F(target['constant'])+sum(c*x for c,x in zip(coeff,w)))} for w in (witness,second)]}
    # Typed count/currency premises are not treated as unrestricted real values.
    # With free variables, a non-domain particular witness is conservatively
    # withheld rather than solving an unimplemented integer-feasibility problem.
    if graph['unit']:
        if any(x<0 or graph['domain']=='nonnegative_integer_counts' and x.denominator!=1 for x in witness):
            return {'reason':'CONSTRAINT_DOMAIN_UNPROVEN'}
        if value<0 or graph['domain']=='nonnegative_integer_counts' and value.denominator!=1:return {'reason':'CONSTRAINT_DOMAIN_UNPROVEN'}
    return {'reason':'CONSTRAINT_TARGET_FORCED','answer':str(value),'rank':len(pivots),'free_variables':[vs[i] for i in range(n) if i not in pivots],
            'certificate':{'witness':{v:str(x) for v,x in zip(vs,witness)},'multipliers':[str(x) for x in multipliers],'answer':str(value)}}

def solve(query):
    try:
        graph=parse(query)
        if graph is None:return None
        result=_eliminate(graph)
    except (Reject,ValueError,SyntaxError,ZeroDivisionError,OverflowError) as e:
        return {'recognized':True,'answer':None,'reason':str(e) or 'CONSTRAINT_REJECTED','source_query':str(query),'proof':None}
    result={'answer':None,**result,'recognized':True,'source_query':str(query),'graph':graph}
    if result.get('answer') is not None:
        result['proof']={'kind':'linear_constraints','source_query':str(query),'graph':graph,'certificate':result['certificate']}
        result['explanation']='条件を同時に満たす例を確認し、等式の組合せで '+graph['target']['expression']+' = '+result['answer']+(graph['unit'] or '')+' と導きました。'
    else:result['proof']=None
    return result

def refine(previous,new_conditions):
    """Retry the same goal after new explicit premises; never guess an input."""
    if not isinstance(previous,dict) or not isinstance(previous.get('source_query'),str):raise Reject('CONSTRAINT_REFINE_SOURCE_REQUIRED')
    graph=parse(previous['source_query'])
    if graph is None or graph['unit']:raise Reject('CONSTRAINT_REFINE_EXPLICIT_ONLY')
    old=[e['source'] for e in graph['equations']]
    q='制約: '+'。'.join(old+[str(new_conditions),graph['target']['expression']+'は何？'])
    result=solve(q)
    result['refinement_evidence']={'new_conditions':str(new_conditions),'previous_answer':previous.get('answer'),'recovered':previous.get('answer') is None and result.get('answer') is not None}
    return result
