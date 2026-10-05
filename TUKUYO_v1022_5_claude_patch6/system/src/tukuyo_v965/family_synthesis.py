from __future__ import annotations
import hashlib,json

def canon(o): return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha(o): return hashlib.sha256(canon(o)).hexdigest()

def _source(name,a,b):
    if name=='A': return a
    if name=='B': return b
    if name=='ABS_A': return abs(a)
    if name=='ABS_B': return abs(b)
    raise ValueError('SOURCE')

def _target(name,a,b,y):
    if name=='Y': return y
    if name=='Y_MINUS_A': return y-a
    if name=='Y_MINUS_B': return y-b
    if name=='Y_PLUS_A': return y+a
    if name=='Y_PLUS_B': return y+b
    raise ValueError('TARGET')

def _recombine(name,a,b,z):
    if name=='Y': return z
    if name=='Y_MINUS_A': return z+a
    if name=='Y_MINUS_B': return z+b
    if name=='Y_PLUS_A': return z-a
    if name=='Y_PLUS_B': return z-b
    raise ValueError('TARGET')

def _mapping(rows,src,tgt):
    m={}
    for r in rows:
        x=_source(src,r['a'],r['b']); z=_target(tgt,r['a'],r['b'],r['expected'])
        if type(x) is not int or type(z) is not int: return None
        if x in m and m[x]!=z: return None
        m[x]=z
    return m

def _infer_threshold_recurrence(m):
    xs=sorted(m)
    if len(xs)<12: return None
    vals=[m[x] for x in xs]
    # Integer monotone staircase with unit jumps only. Allows incomplete lower tail.
    if any(vals[i]>vals[i+1] for i in range(len(vals)-1)): return None
    if any(vals[i+1]-vals[i] not in (0,1) for i in range(len(vals)-1)): return None
    zmin,zmax=min(vals),max(vals)
    if zmax-zmin<4: return None
    # Earliest observed x for each level > zmin. These are candidate thresholds.
    th=[]
    for level in range(zmin+1,zmax+1):
        hits=[x for x in xs if m[x]>=level]
        if not hits: return None
        th.append((level,min(hits)))
    if len(th)<4: return None
    # We require contiguous integer x coverage around each observed boundary so the
    # threshold is evidence-backed rather than guessed between sparse samples.
    xset=set(xs)
    for _,t in th:
        if t-1 not in xset or t not in xset: return None
    ts=[t for _,t in th]
    ds=[ts[i+1]-ts[i] for i in range(len(ts)-1)]
    if len(ds)<3: return None
    second=[ds[i+1]-ds[i] for i in range(len(ds)-1)]
    if len(set(second))!=1: return None
    inc=second[0]
    if inc<0: return None
    # threshold for level k, using first observed level as anchor
    return {'base_level':th[0][0],'base_threshold':ts[0],'first_delta':ds[0],'delta_increment':inc,
            'observed_thresholds':th,'evidence_levels':[zmin,zmax]}

def _count(spec,x):
    # Extrapolate learned recurrence in both directions only down to output 0.
    level=spec['base_level']; t=spec['base_threshold']; d=spec['first_delta']; inc=spec['delta_increment']
    if level<1: raise ValueError('LEVEL_RANGE')
    # Build downward thresholds by reversing recurrence when evidence permits.
    thresholds=[]
    # derive t_k for k=1..base_level
    cur_t=t; cur_d=d
    back=[]
    for k in range(level,1,-1):
        prev_d=cur_d-inc
        prev_t=cur_t-prev_d
        back.append((k-1,prev_t)); cur_t,cur_d=prev_t,prev_d
    thresholds.extend(reversed(back)); thresholds.append((level,t))
    # forward until safely beyond x; hard finite cap blocks runaway candidates.
    cur_level=level; cur_t=t; cur_d=d
    crossed=False
    for _ in range(10000):
        if cur_t>x and cur_level>level:
            crossed=True; break
        nxt_t=cur_t+cur_d; cur_d=cur_d+inc; cur_level+=1; cur_t=nxt_t
        thresholds.append((cur_level,cur_t))
        if cur_t>x and cur_level>level+1:
            crossed=True; break
    if not crossed and thresholds and thresholds[-1][1] <= x:
        raise ValueError('FAMILY_EXTRAPOLATION_LIMIT')
    return sum(1 for k,t0 in thresholds if t0<=x)

def evaluate(proposal,a,b):
    if proposal.get('schema')!='tukuyo.v965.family_proposal/1': raise ValueError('SCHEMA')
    body={k:v for k,v in proposal.items() if k!='candidate_sha256'}
    if proposal.get('candidate_sha256')!=sha(body): raise ValueError('CANDIDATE_HASH')
    x=_source(proposal['source_transform'],int(a),int(b))
    z=_count(proposal['family_parameters'],x)
    return _recombine(proposal['residual_form'],int(a),int(b),z)

def propose(rows,ceiling_evidence):
    if ceiling_evidence.get('status')!='META_GRAMMAR_CEILING_DETECTED': raise ValueError('CEILING_EVIDENCE_REQUIRED')
    if len(rows)<30: raise ValueError('DATA_INSUFFICIENT')
    candidates=[]
    for src in ('A','B','ABS_A','ABS_B'):
      for tgt in ('Y','Y_MINUS_A','Y_MINUS_B','Y_PLUS_A','Y_PLUS_B'):
        m=_mapping(rows,src,tgt)
        if not m: continue
        spec=_infer_threshold_recurrence(m)
        if not spec: continue
        p={'schema':'tukuyo.v965.family_proposal/1','source_transform':src,'residual_form':tgt,
           'invented_family':{'kind':'THRESHOLD_RECURRENCE_COUNT','input_type':'int','output_type':'nonnegative_int',
                              'semantics':'count learned recurrence-generated thresholds <= transformed input',
                              'undefined_conditions':[],
                              'counterexample_conditions':['threshold-1/threshold boundary','far extrapolation','negative raw input when ABS is not selected']},
           'family_parameters':spec,'training_rows_sha256':sha(rows),'ceiling_evidence_sha256':sha(ceiling_evidence),
           'claim_scope':'BOUNDED_RESIDUAL_DERIVED_FAMILY_SYNTHESIS'}
        p['candidate_sha256']=sha(p)
        wrong=sum(evaluate(p,r['a'],r['b'])!=r['expected'] for r in rows)
        candidates.append((wrong,len(json.dumps(p['family_parameters'],sort_keys=True)),src,tgt,p))
    if not candidates: raise ValueError('NO_FAMILY_PROPOSAL')
    candidates.sort(key=lambda x:x[:4]); best=candidates[0]
    if best[0]!=0: raise ValueError('NO_ZERO_TRAINING_FAMILY')
    out=best[4]; out['candidate_count']=len(candidates); out['selection_rule']='training_wrong,family_parameter_size,source,residual'; out['candidate_sha256']=sha({k:v for k,v in out.items() if k!='candidate_sha256'})
    return out
