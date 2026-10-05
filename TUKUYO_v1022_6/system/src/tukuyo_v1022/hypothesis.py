"""Finite hypothesis generation / comparison for v1022.2.

This is deliberately *not* open-ended induction.  It searches a small explicit
family of exact rational functions, checks every supplied example, deduplicates
extensionally equivalent candidates, and refuses to answer when more than one
surviving hypothesis predicts a different continuation.  A bounded
counterexample search is returned as evidence of ambiguity.
"""
from __future__ import annotations
import re,unicodedata
from fractions import Fraction
from . import proofs

N=r'[-+]?\d+(?:\.\d+)?'

def _norm(s):
    return unicodedata.normalize('NFKC',str(s)).strip().replace('−','-').replace('→','->')

def _num(x): return Fraction(str(x))
def _s(x): return proofs.number(Fraction(x))
def _eval(coeff,x):
    c0,c1,c2=coeff;x=Fraction(x);return c0+c1*x+c2*x*x

def _pairs(s):
    out=[]
    # x=1 のとき y=3 / x=1 -> y=3
    for m in re.finditer(rf'(?<![A-Za-z0-9_])x\s*=\s*({N})\s*(?:のとき|なら|->|,|、|;|；)?\s*y\s*=\s*({N})',s,re.I):
        out.append((_num(m[1]),_num(m[2])))
    # 入力1 -> 出力3 / 入力1なら3
    for m in re.finditer(rf'入力\s*({N})\s*(?:->|なら|のとき|で)\s*(?:出力\s*)?({N})',s):
        out.append((_num(m[1]),_num(m[2])))
    # preserve order, drop exact duplicates
    seen=set();uniq=[]
    for p in out:
        if p not in seen:seen.add(p);uniq.append(p)
    return uniq

def _target(s,pairs):
    spans=[]
    for m in re.finditer(rf'(?<![A-Za-z0-9_])x\s*=\s*({N})[^。?？]*?(?:y|出力)(?:\s*(?:は|=))?\s*(?:何|いくつ|\?)',s,re.I):spans.append((_num(m[1]),m.start()))
    for m in re.finditer(rf'入力\s*({N})[^。?？]*?(?:出力|答え)(?:\s*は)?\s*(?:何|いくつ|\?)',s):spans.append((_num(m[1]),m.start()))
    if not spans:return None
    # Prefer a target not already used as an example; otherwise the last query.
    xs={x for x,_ in pairs};fresh=[z for z in spans if z[0] not in xs]
    return (fresh or spans)[-1][0]

def _candidate_rows(pairs):
    if len(pairs)<2:return []
    rows=[]
    def add(kind,coeff,complexity):
        if all(_eval(coeff,x)==y for x,y in pairs):rows.append({'kind':kind,'coeff':coeff,'complexity':complexity})
    x0,y0=pairs[0]
    add('constant',(y0,Fraction(0),Fraction(0)),1)
    add('identity',(Fraction(0),Fraction(1),Fraction(0)),1)
    add('offset',(y0-x0,Fraction(1),Fraction(0)),2)
    if x0!=0:add('scale',(Fraction(0),y0/x0,Fraction(0)),2)
    # affine from the first two examples with distinct x
    pair2=next(((x,y) for x,y in pairs[1:] if x!=x0),None)
    if pair2:
        x1,y1=pair2;a=(y1-y0)/(x1-x0);b=y0-a*x0;add('affine',(b,a,Fraction(0)),3)
    add('square_offset',(y0-x0*x0,Fraction(0),Fraction(1)),3)
    if x0!=0:add('square_scale',(Fraction(0),Fraction(0),y0/(x0*x0)),3)
    # Deduplicate equivalent polynomials; retain simplest label for explanation.
    best={}
    for r in rows:
        k=tuple(r['coeff']);cur=best.get(k)
        if cur is None or (r['complexity'],r['kind'])<(cur['complexity'],cur['kind']):best[k]=r
    return sorted(best.values(),key=lambda r:(r['complexity'],r['kind'],tuple(map(str,r['coeff']))))

def _counterexample(rows,pairs):
    if len(rows)<2:return None
    used={x for x,_ in pairs}
    for n in list(range(-8,0))+list(range(0,9)):
        x=Fraction(n)
        if x in used:continue
        vals={_eval(r['coeff'],x) for r in rows}
        if len(vals)>1:
            return {'x':_s(x),'predictions':[{'kind':r['kind'],'y':_s(_eval(r['coeff'],x))} for r in rows]}
    return None

def solve(query):
    s=_norm(query)
    if len(s)>2000:return None
    if re.search(r'約|およそ|だいたい|大体|たぶん|かもしれ|[〜~～]',s):
        if re.search(r'(?<![A-Za-z0-9_])x\s*=|入力',s,re.I):return {'recognized':True,'answer':None,'reason':'HYPOTHESIS_AMBIGUOUS_INPUT','confidence':0.0,'proof':None}
        return None
    pairs=_pairs(s);target=_target(s,pairs)
    if len(pairs)<2 or target is None:return None
    if len(pairs)>16:return {'recognized':True,'answer':None,'reason':'HYPOTHESIS_EXAMPLE_LIMIT','confidence':0.0,'proof':None}
    if len({x for x,_ in pairs})!=len(pairs):
        byx={}
        for x,y in pairs:
            if x in byx and byx[x]!=y:return {'recognized':True,'answer':None,'reason':'HYPOTHESIS_CONTRADICTORY_EXAMPLES','confidence':0.0,'proof':None}
            byx[x]=y
    rows=_candidate_rows(pairs)
    if not rows:return {'recognized':True,'answer':None,'reason':'HYPOTHESIS_NO_SUPPORTED_MODEL','confidence':0.0,'proof':None,'candidates':[],'examples':[[_s(x),_s(y)] for x,y in pairs],'target_x':_s(target)}
    preds={_eval(r['coeff'],target) for r in rows}
    cx=_counterexample(rows,pairs)
    serial=[{'kind':r['kind'],'coefficients':[_s(v) for v in r['coeff']], 'prediction':_s(_eval(r['coeff'],target))} for r in rows]
    if len(rows)!=1 or len(preds)!=1:
        return {'recognized':True,'answer':None,'reason':'HYPOTHESIS_UNDERDETERMINED','confidence':0.0,'proof':None,'candidates':serial,'counterexample':cx,'examples':[[_s(x),_s(y)] for x,y in pairs],'target_x':_s(target)}
    r=rows[0];ans=_s(_eval(r['coeff'],target))
    proof={'kind':'hypothesis','examples':[[ _s(x),_s(y)] for x,y in pairs],
           'model':{'family':r['kind'],'coefficients':[_s(v) for v in r['coeff']]},
           'target_x':_s(target),'answer':ans,'candidate_count':1,'counterexample':None}
    return {'recognized':True,'answer':ans,'confidence':.91,'proof':proof,'candidates':serial,'counterexample':None,
            'reasoning_evidence':{'generated_candidates':len(rows),'finite_hypothesis_class':True,'counterexample_search':True},'examples':[[_s(x),_s(y)] for x,y in pairs],'target_x':_s(target)}


def refine(previous, observed_x, observed_y):
    """Refine a finite hypothesis set with one discriminating observation.

    This is counterexample-driven rather than a blind overwrite: the previous
    candidates are recorded, the new observation is appended, inconsistent
    hypotheses are eliminated, and an answer is emitted only when exactly one
    polynomial remains in the supported finite family.
    """
    if not isinstance(previous,dict) or not previous.get('recognized'):
        raise ValueError('HYPOTHESIS_PREVIOUS_REQUIRED')
    ex=previous.get('examples')
    tx=previous.get('target_x')
    if not isinstance(ex,list) or tx is None:
        raise ValueError('HYPOTHESIS_REFINEMENT_CONTEXT_MISSING')
    pairs=[(_num(x),_num(y)) for x,y in ex]
    ox,oy=_num(observed_x),_num(observed_y)
    for x,y in pairs:
        if x==ox and y!=oy:
            return {'recognized':True,'answer':None,'reason':'HYPOTHESIS_CONTRADICTORY_OBSERVATION','confidence':0.0,
                    'proof':None,'examples':ex,'target_x':str(tx),'eliminated':previous.get('candidates',[]),'candidates':[]}
    if all(x!=ox for x,_ in pairs):pairs.append((ox,oy))
    old={(c.get('kind'),tuple(c.get('coefficients',[]))) for c in previous.get('candidates',[])}
    rows=_candidate_rows(pairs)
    serial=[{'kind':r['kind'],'coefficients':[_s(v) for v in r['coeff']],
             'prediction':_s(_eval(r['coeff'],_num(tx)))} for r in rows]
    new={(c['kind'],tuple(c['coefficients'])) for c in serial}
    eliminated=[c for c in previous.get('candidates',[]) if (c.get('kind'),tuple(c.get('coefficients',[]))) not in new]
    base={'recognized':True,'examples':[[_s(x),_s(y)] for x,y in pairs],'target_x':str(tx),
          'candidates':serial,'eliminated':eliminated,'counterexample':_counterexample(rows,pairs)}
    if len(rows)!=1:
        return {**base,'answer':None,'reason':'HYPOTHESIS_UNDERDETERMINED' if rows else 'HYPOTHESIS_NO_SUPPORTED_MODEL',
                'confidence':0.0,'proof':None}
    r=rows[0];target=_num(tx);ans=_s(_eval(r['coeff'],target))
    proof={'kind':'hypothesis','examples':base['examples'],'model':{'family':r['kind'],'coefficients':[_s(v) for v in r['coeff']]},
           'target_x':str(tx),'answer':ans,'candidate_count':1,'counterexample':None}
    return {**base,'answer':ans,'reason':'COUNTEREXAMPLE_REFINED','confidence':.93,'proof':proof,
            'reasoning_evidence':{'counterexample_driven_refinement':True,'eliminated_count':len(eliminated),'survivor_count':1}}
