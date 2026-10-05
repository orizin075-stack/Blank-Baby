"""Bounded dependency-graph meta reasoning for v1022.3.

The engine accepts a small equation-style problem language embedded in Japanese
or ASCII text.  A target may have more than one candidate definition.  Rather
than committing to the first one, the engine enumerates bounded derivations,
records failed strategies, compares all successful answers, and commits only
when every successful derivation agrees.

This is intentionally finite and fail-closed: it is not a general theorem
prover, unrestricted program evaluator, or arbitrary natural-language solver.
"""
from __future__ import annotations
import ast,itertools,re,unicodedata
from fractions import Fraction
from . import proofs

MAX_DEFINITIONS=64
MAX_DEPTH=16
MAX_DERIVATIONS=32
MAX_EXPR=240
MAX_SEARCH_WORK=4096

class SearchLimit(ValueError):pass

_ID=r'[^\W\d]\w*'

def _norm(s):
    s=unicodedata.normalize('NFKC',str(s)).strip()
    return s.replace('×','*').replace('÷','/').replace('−','-').replace('：',':')

def _fstr(v):return proofs.number(Fraction(v))

def _split(s):
    return [x.strip() for x in re.split(r'[。；;\n]+',s) if x.strip()]

def _goal(parts):
    ident_re=re.compile(rf'^{_ID}$',re.I)
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

def _expr_names(expr):
    if len(expr)>MAX_EXPR:raise ValueError('META_EXPRESSION_LIMIT')
    tree=ast.parse(expr,mode='eval');names=set();ops=0
    def walk(n,depth=0):
        nonlocal ops
        if depth>20:raise ValueError('META_EXPRESSION_DEPTH')
        if isinstance(n,ast.Expression):return walk(n.body,depth+1)
        if isinstance(n,ast.Constant) and type(n.value) in (int,float):
            if abs(Fraction(str(n.value)))>10**12:raise ValueError('META_NUMBER_LIMIT')
            return
        if isinstance(n,ast.Name):names.add(n.id);return
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.UAdd,ast.USub)):
            ops+=1;return walk(n.operand,depth+1)
        if isinstance(n,ast.BinOp) and isinstance(n.op,(ast.Add,ast.Sub,ast.Mult,ast.Div,ast.Pow)):
            ops+=1;walk(n.left,depth+1);walk(n.right,depth+1);return
        raise ValueError('META_UNSUPPORTED_AST')
    walk(tree)
    return tree,names,ops

def _eval(tree,env):
    def rec(n,depth=0):
        if depth>20:raise ValueError('META_EXPRESSION_DEPTH')
        if isinstance(n,ast.Expression):return rec(n.body,depth+1)
        if isinstance(n,ast.Constant) and type(n.value) in (int,float):return Fraction(str(n.value))
        if isinstance(n,ast.Name):
            if n.id not in env:raise KeyError(n.id)
            return Fraction(env[n.id])
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.UAdd,ast.USub)):
            v=rec(n.operand,depth+1);return -v if isinstance(n.op,ast.USub) else v
        if isinstance(n,ast.BinOp):
            a=rec(n.left,depth+1);b=rec(n.right,depth+1)
            if isinstance(n.op,ast.Add):v=a+b
            elif isinstance(n.op,ast.Sub):v=a-b
            elif isinstance(n.op,ast.Mult):v=a*b
            elif isinstance(n.op,ast.Div):
                if b==0:raise ZeroDivisionError
                v=a/b
            elif isinstance(n.op,ast.Pow):
                if b.denominator!=1 or abs(b)>6:raise ValueError('META_POWER_LIMIT')
                v=a**int(b)
            else:raise ValueError('META_UNSUPPORTED_OP')
            if max(v.numerator.bit_length(),v.denominator.bit_length())>160:raise ValueError('META_RESULT_LIMIT')
            return v
        raise ValueError('META_UNSUPPORTED_AST')
    return rec(tree)

def parse(query):
    s=_norm(query)
    if len(s)>5000:return None
    parts=_split(s);target=_goal(parts)
    if not target:return None
    defs={};order=0
    for p in parts:
        # skip the goal sentence
        if _goal([p]):continue
        m=re.fullmatch(rf'({_ID})\s*=\s*(.+)',p)
        if not m:continue
        name,expr=m.group(1),m.group(2).strip()
        try:tree,names,ops=_expr_names(expr)
        except (SyntaxError,ValueError):
            return {'recognized':True,'error':'META_PARSE_REJECTED','target':target,'bad_statement':p}
        order+=1
        defs.setdefault(name,[]).append({'id':f'{name}#{len(defs.get(name,[]))+1}','name':name,'expr':expr,'tree':tree,'deps':sorted(names),'ops':ops,'order':order})
        if sum(map(len,defs.values()))>MAX_DEFINITIONS:
            return {'recognized':True,'error':'META_DEFINITION_LIMIT','target':target}
    # Do not claim ordinary natural-language questions that contain no
    # equation assignments at all (e.g. inventory '残りは何個?').
    if not defs:return None
    if target not in defs:
        return {'recognized':True,'error':'META_TARGET_UNDEFINED','target':target,'definitions':defs}
    return {'recognized':True,'target':target,'definitions':defs,'program':s}

def _derive(var,defs,stack=(),depth=0,memo=None,budget=None):
    memo={} if memo is None else memo
    budget=[0] if budget is None else budget
    budget[0]+=1
    if budget[0]>MAX_SEARCH_WORK:raise SearchLimit('WORK_LIMIT')
    key=(var,stack)
    if key in memo:return memo[key]
    if depth>MAX_DEPTH:raise SearchLimit('DEPTH_LIMIT')
    if var in stack:return [],[{'variable':var,'reason':'CYCLE','path':list(stack)+( [var] if False else [])}]
    if var not in defs:return [],[{'variable':var,'reason':'MISSING_DEPENDENCY','path':list(stack)}]
    successes=[];failures=[]
    for d in defs[var]:
        dep_results=[];def_failed=False;local_fail=[]
        for dep in d['deps']:
            ss,ff=_derive(dep,defs,stack+(var,),depth+1,memo,budget)
            if not ss:
                def_failed=True;local_fail.extend(ff or [{'variable':dep,'reason':'UNRESOLVED'}]);continue
            dep_results.append((dep,ss))
        if def_failed:
            failures.append({'definition':d['id'],'expr':d['expr'],'reason':'DEPENDENCY_FAILURE','details':local_fail[:8]});continue
        combos=[()] if not dep_results else itertools.product(*[[(name,x) for x in rows] for name,rows in dep_results])
        count=0
        for combo in combos:
            count+=1
            budget[0]+=1
            if budget[0]>MAX_SEARCH_WORK:raise SearchLimit('WORK_LIMIT')
            env={};steps=[];cost=d['ops']
            used=[]
            for dep,res in combo:
                env[dep]=Fraction(res['value']);steps.extend(res['steps']);cost+=res['cost'];used.append(res['strategy_id'])
            # de-duplicate dependency steps while preserving order
            uniq=[];seen=set()
            for st in steps:
                k=(st['variable'],st['definition'])
                if k not in seen:seen.add(k);uniq.append(st)
            try:value=_eval(d['tree'],env)
            except (ValueError,KeyError,ZeroDivisionError,OverflowError) as e:
                failures.append({'definition':d['id'],'expr':d['expr'],'reason':type(e).__name__});continue
            step={'variable':var,'definition':d['id'],'expression':d['expr'],'dependencies':d['deps'],'value':_fstr(value)}
            strategy=d['id']+('['+','.join(used)+']' if used else '')
            if len(successes)>=MAX_DERIVATIONS:raise SearchLimit('DERIVATION_LIMIT')
            successes.append({'value':value,'steps':uniq+[step],'cost':cost,'strategy_id':strategy,'root_definition':d['id']})
    # Deduplicate exact same strategy trace/value.
    out=[];seen=set()
    for r in successes:
        sig=(r['value'],tuple((x['variable'],x['definition']) for x in r['steps']))
        if sig not in seen:seen.add(sig);out.append(r)
    memo[key]=(out[:MAX_DERIVATIONS],failures[:MAX_DERIVATIONS]);return memo[key]

def _missing_requests(failures):
    out=[]
    def rec(x):
        if isinstance(x,dict):
            if x.get('reason')=='MISSING_DEPENDENCY' and isinstance(x.get('variable'),str):out.append(x['variable'])
            for v in x.values():rec(v)
        elif isinstance(x,list):
            for v in x:rec(v)
    rec(failures)
    return sorted(set(out))

def abstract_schema(result):
    """Extract a reusable bounded derivation skeleton from a successful run.

    Constant leaf assignments become inputs; derived equations retain their
    symbolic expressions.  No values, identities, or private runtime state are
    copied.  The schema is therefore a procedure template, not episodic memory.
    """
    if not isinstance(result,dict) or result.get('answer') is None:
        raise ValueError('META_SUCCESSFUL_RESULT_REQUIRED')
    proof=result.get('proof') or {};steps=proof.get('steps')
    if proof.get('kind')!='meta_derivation' or not isinstance(steps,list):raise ValueError('META_PROOF_REQUIRED')
    inputs=[];derived=[]
    for st in steps:
        if st.get('dependencies'):
            derived.append({'variable':st['variable'],'expression':st['expression'],'dependencies':list(st['dependencies'])})
        else:
            inputs.append(st['variable'])
    return {'schema':'tukuyo.v1022_3.meta_strategy/1','target':proof['target'],'inputs':sorted(set(inputs)),
            'derived':derived,'claim_boundary':{'same_symbol_roles_required':True,'semantic_role_inference':False}}

def solve_with_schema(query,schema):
    """Transfer an abstracted procedure to new numeric inputs with same roles."""
    if not isinstance(schema,dict) or schema.get('schema')!='tukuyo.v1022_3.meta_strategy/1':raise ValueError('META_SCHEMA')
    target=schema.get('target');inputs=schema.get('inputs');derived=schema.get('derived')
    if not isinstance(target,str) or not isinstance(inputs,list) or not isinstance(derived,list):raise ValueError('META_SCHEMA_FIELDS')
    q=_norm(query);parts=_split(q);g=_goal(parts)
    if g!=target:return {'recognized':True,'answer':None,'confidence':0.0,'reason':'META_SCHEMA_TARGET_MISMATCH','proof':None}
    base=parse(q)
    # parse() requires a target definition; for transfer, collect assignments manually.
    present=set()
    for x in parts:
        m=re.fullmatch(rf'({_ID})\s*=\s*(.+)',x)
        if m:present.add(m.group(1))
    missing=[x for x in inputs if x not in present]
    if missing:return {'recognized':True,'answer':None,'confidence':0.0,'reason':'META_SCHEMA_INPUT_MISSING','proof':None,'information_requests':missing}
    injected=[]
    for d in derived:
        if not isinstance(d,dict) or set(d)!={'variable','expression','dependencies'}:raise ValueError('META_SCHEMA_DERIVATION')
        var=str(d['variable']);expr=str(d['expression'])
        _expr_names(expr)
        if var not in present:
            injected.append(f'{var}={expr}');present.add(var)
    body=[x for x in parts if not _goal([x])]
    augmented='。'.join(body+injected+[f'{target}は何?'])
    r=solve(augmented)
    if isinstance(r,dict):
        r['transfer_evidence']={'schema_applied':True,'injected_definitions':injected,'source_schema':schema['schema']}
    return r

def solve(query):
    p=parse(query)
    if p is None:return None
    if p.get('error'):
        return {'recognized':True,'answer':None,'confidence':0.0,'reason':p['error'],'proof':None,
                'target':p.get('target'),'diagnostics':p.get('bad_statement')}
    try:ss,ff=_derive(p['target'],p['definitions'],memo={})
    except SearchLimit as e:
        return {'recognized':True,'answer':None,'confidence':0.0,'reason':'META_SEARCH_INCOMPLETE','proof':None,
                'target':p['target'],'program':p['program'],'search_complete':False,'limit_reason':str(e)}
    if not ss:
        return {'recognized':True,'answer':None,'confidence':0.0,'reason':'META_NO_SUCCESSFUL_STRATEGY','proof':None,
                'target':p['target'],'failed_strategies':ff,'successful_strategies':[],'program':p['program'],
                'information_requests':_missing_requests(ff)}
    values={r['value'] for r in ss}
    serial=[{'strategy_id':r['strategy_id'],'root_definition':r['root_definition'],'value':_fstr(r['value']),
             'cost':r['cost'],'steps':r['steps']} for r in sorted(ss,key=lambda z:(z['cost'],len(z['steps']),z['strategy_id']))]
    if len(values)!=1:
        return {'recognized':True,'answer':None,'confidence':0.0,'reason':'META_STRATEGY_CONFLICT','proof':None,
                'target':p['target'],'successful_strategies':serial,'failed_strategies':ff,
                'conflicting_values':sorted(_fstr(v) for v in values),'program':p['program'],
                'conflict_resolution':{'compare_root_definitions':sorted(set(x['root_definition'] for x in serial)),
                                       'commit_blocked_until_disambiguated':True}}
    best=min(ss,key=lambda z:(z['cost'],len(z['steps']),z['strategy_id']));ans=_fstr(best['value'])
    proof={'kind':'meta_derivation','target':p['target'],'steps':best['steps'],'answer':ans}
    return {'recognized':True,'answer':ans,'confidence':.95 if len(ss)>1 else .92,'reason':'META_STRATEGY_AGREEMENT' if len(ss)>1 else 'META_DERIVED',
            'proof':proof,'target':p['target'],'successful_strategies':serial,'failed_strategies':ff,'program':p['program'],
            'reasoning_evidence':{'problem_decomposition':True,'dependency_graph':True,'strategy_count':len(ss),
                'strategy_agreement':len(ss)>1,'failed_strategy_count':len(ff),'strategy_switch_available':bool(ff and ss)}}

def refine(previous,new_statement):
    """Add one bounded equation after a failed/ambiguous run and solve again."""
    if not isinstance(previous,dict) or not previous.get('recognized') or not previous.get('program'):
        raise ValueError('META_PREVIOUS_REQUIRED')
    stmt=_norm(new_statement).strip('。；; ')
    if not re.fullmatch(rf'{_ID}\s*=\s*.+',stmt):raise ValueError('META_REFINEMENT_STATEMENT')
    # Put the new evidence before the terminal goal sentence.
    prog=previous['program'];parts=_split(prog);g=None;body=[]
    for x in parts:
        if _goal([x]):g=x
        else:body.append(x)
    if not g:raise ValueError('META_REFINEMENT_GOAL_MISSING')
    nxt=solve('。'.join(body+[stmt,g]))
    if isinstance(nxt,dict):
        nxt['refinement_evidence']={'added_statement':stmt,'previous_reason':previous.get('reason'),
                                    'recovered':previous.get('answer') is None and nxt.get('answer') is not None}
    return nxt
