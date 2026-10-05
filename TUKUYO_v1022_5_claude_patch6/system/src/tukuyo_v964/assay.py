from __future__ import annotations
import math, hashlib, json
from tukuyo_v957.novel_primitive import propose,eval_proposal

def canon(o): return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha(o): return hashlib.sha256(canon(o)).hexdigest()

def _rows(kind,offset,n=42):
    rows=[]
    for i in range(n):
        if kind in ('ge','lt'):
            # Force both sides of the comparison boundary regardless of wave offset.
            a=((i*5+offset)%31)-15; b=((i*11+3+offset)%29)-14
        else:
            a=i-19+offset; b=((i*7+3+offset)%17)-8
        if kind=='floor3': y=a//3+b
        elif kind=='mod5': y=a%5-b
        elif kind=='ge': y=(1 if a>=b else 0)+b
        elif kind=='lt': y=(1 if a<b else 0)-a
        elif kind=='isqrt': y=math.isqrt(abs(a))+b
        else: raise ValueError('WAVE_KIND')
        rows.append({'a':a,'b':b,'expected':y})
    return rows

def _gap(rows):
    return {'classification':{'state':'REPRESENTATION_INSUFFICIENT'},'rows_sha256':sha(rows),'scope':'ASSAY_ONLY_PRECLASSIFIED_AFTER_EXHAUSTIVE_FINITE_SEARCH'}

def _primitive_id(p):
    q=p['primitive']; return q['kind']+(':'+str(q.get('parameter')) if 'parameter' in q else '')

def _hidden_ok(p,kind,offset):
    rows=_rows(kind,offset,31)
    wrong=sum(eval_proposal(p,r['a'],r['b'])!=r['expected'] for r in rows)
    return wrong,sha(rows)

def run_assay():
    waves=[('floor3',0),('mod5',101),('ge',211),('lt',307)]
    accepted=[]; trace=[]; seen=set(); replay_growth=[]
    for idx,(kind,off) in enumerate(waves,1):
        train=_rows(kind,off,42)
        p=propose(train,_gap(train))
        wrong,hsha=_hidden_ok(p,kind,off+1000)
        pid=_primitive_id(p)
        if wrong!=0: raise ValueError('HIDDEN_FAILURE:'+kind)
        if pid in seen: raise ValueError('NOVELTY_NOT_GROWING:'+pid)
        seen.add(pid);accepted.append((kind,p,off))
        # Retention: every earlier immutable proposal must still pass its own fresh hidden set.
        retention=[]
        for old_kind,old_p,old_off in accepted:
            w,_=_hidden_ok(old_p,old_kind,old_off+2000+idx)
            retention.append({'primitive_id':_primitive_id(old_p),'wrong':w})
        if any(x['wrong'] for x in retention): raise ValueError('RETENTION_REGRESSION')
        trace.append({'wave':idx,'task_family':kind,'primitive_id':pid,'candidate_sha256':p['candidate_sha256'],'hidden_wrong':wrong,'hidden_rows_sha256':hsha,'unique_primitive_count':len(seen),'retention':retention})
        # Replay must not create novelty count inflation.
        replay=propose(train,_gap(train)); replay_growth.append(_primitive_id(replay) not in seen)
    # Deliberate ceiling task outside the finite v957 meta grammar.
    ceiling_rows=_rows('isqrt',509,47)
    ceiling={'task_family':'isqrt_abs_plus_b','status':None,'candidate':None}
    try:
        p=propose(ceiling_rows,_gap(ceiling_rows))
        wrong,_=_hidden_ok(p,'isqrt',1609)
        if wrong==0:
            ceiling.update({'status':'UNEXPECTED_META_GRAMMAR_SOLUTION','candidate':_primitive_id(p),'hidden_wrong':wrong})
        else:
            ceiling.update({'status':'META_GRAMMAR_CEILING_DETECTED','candidate':_primitive_id(p),'hidden_wrong':wrong})
    except ValueError as e:
        ceiling.update({'status':'META_GRAMMAR_CEILING_DETECTED','reason':str(e)})
    ok=(len(seen)==4 and all(x['hidden_wrong']==0 for x in trace) and not any(replay_growth) and ceiling['status']=='META_GRAMMAR_CEILING_DETECTED')
    return {'schema':'tukuyo.v964.bounded_open_ended_assay/1','ok':ok,'waves':trace,'unique_primitive_count':len(seen),'unique_primitive_ids':sorted(seen),'replay_novelty_inflation':any(replay_growth),'ceiling':ceiling,'finite_meta_grammar':True,'open_ended_evolution_established':False,'general_l5':False,'general_l6':False}
