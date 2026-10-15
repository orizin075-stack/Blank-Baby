"""Independent lexical reader plus null-space minimum-cost plan verification."""
from fractions import Fraction as F
from .constraints_verify import read,_expr,_q

def _determined(rows,target):
    # Reduced homogeneous equations describe allowable differences between two
    # worlds. A goal is forced iff it vanishes on every free-variable direction.
    a=[list(r) for r in rows];n=len(target);pivots=[];r=0
    for c in range(n):
        hit=next((i for i in range(r,len(a)) if a[i][c]),None)
        if hit is None:continue
        a[r],a[hit]=a[hit],a[r];factor=a[r][c];a[r]=[_q(x/factor) for x in a[r]]
        for i in range(len(a)):
            if i!=r:
                f=a[i][c];a[i]=[_q(x-f*y) for x,y in zip(a[i],a[r])]
        pivots.append(c);r+=1
        if r==len(a):break
    for free in range(n):
        if free in pivots:continue
        if target[free]-sum(target[c]*a[i][free] for i,c in enumerate(pivots)):return False
    return True

def check(proof):
    try:
        if not isinstance(proof,dict) or set(proof)!={'kind','source_query','task','selected','total_cost','search_complete','candidates_examined'} or proof['kind']!='observation_plan' or proof['search_complete'] is not True:return False
        g=read(proof['source_query'])
        if g is None or g['unit']:return False
        # Check consistency independently, including the augmented constant.
        variables=g['variables'];rows=[[F(e['coefficients'].get(v,0)) for v in variables] for e in g['equations']];aug=[r+[F(e['rhs'])] for r,e in zip(rows,g['equations'])]
        if _determined(aug,[F(0)]*len(variables)+[F(1)]):return False
        goal=[F(g['target']['coefficients'].get(v,0)) for v in variables];task=proof['task']
        if not isinstance(task,dict) or set(task)!={'budget','options'} or type(task['budget']) is not int or not 0<=task['budget']<=800:return False
        opts=task['options']
        if not isinstance(opts,list) or not 1<=len(opts)<=8 or proof['candidates_examined']!=2**len(opts):return False
        ids=[];vectors=[]
        for o in opts:
            if not isinstance(o,dict) or set(o)!={'id','expression','cost'} or not isinstance(o['id'],str) or not 1<=len(o['id'])<=64 or o['id'] in ids:return False
            if type(o['cost']) is not int or not 1<=o['cost']<=100 or not isinstance(o['expression'],str):return False
            affine,names=_expr(o['expression'])
            if not names<=set(variables):return False
            ids.append(o['id']);vectors.append([affine[1].get(v,F(0)) for v in variables])
        selected=proof['selected']
        if not isinstance(selected,list) or any(not isinstance(i,str) for i in selected) or selected!=sorted(set(selected)) or not set(selected)<=set(ids) or type(proof['total_cost']) is not int:return False
        chosen=[ids.index(i) for i in selected];cost=sum(opts[i]['cost'] for i in chosen)
        if cost!=proof['total_cost'] or cost>task['budget'] or not _determined(rows+[vectors[i] for i in chosen],goal):return False
        # All lower-cost (and canonical tie-breaking) alternatives are checked.
        incumbent=(cost,len(selected),selected)
        for mask in range(2**len(opts)):
            ix=[i for i in range(len(opts)) if mask>>i&1];c=sum(opts[i]['cost'] for i in ix);s=sorted(ids[i] for i in ix)
            if c<=task['budget'] and (c,len(s),s)<incumbent and _determined(rows+[vectors[i] for i in ix],goal):return False
        return True
    except (ValueError,TypeError,KeyError,ZeroDivisionError,OverflowError):return False
