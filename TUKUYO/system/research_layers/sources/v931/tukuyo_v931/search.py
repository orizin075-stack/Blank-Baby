import ast, hashlib, random
BASE_SOURCE = """def choose(m):
    a=m['ambiguous_failure']; b=m['representation_failure']; c=m['consistency_failure']
    if a > 0.30: return 'probe'
    if b > 0.30: return 'propose'
    return 'hold'
"""
ACTIONS={'probe','propose','hold','audit'}
MUTATIONS=('add_audit','lower_threshold','repr_priority','decoy_overaudit','decoy_raise_threshold','decoy_swap')
def source_sha(s): return hashlib.sha256(s.encode()).hexdigest()
def safe_source(src):
    try:t=ast.parse(src)
    except SyntaxError:return False
    banned=(ast.Import,ast.ImportFrom,ast.With,ast.Try,ast.Global,ast.Nonlocal,ast.ClassDef,ast.Lambda,ast.Attribute,ast.While,ast.For,ast.AsyncFor,ast.AsyncFunctionDef)
    if any(isinstance(n,banned) for n in ast.walk(t)):return False
    if sum(isinstance(n,(ast.FunctionDef,)) for n in ast.walk(t)) != 1:return False
    if any(isinstance(n,ast.Call) for n in ast.walk(t)):return False
    return True

def _src(flags):
    # Canonical regeneration. Mutations alter flags; grammar cannot express oracle interaction rule.
    audit_t = '0.10' if 'decoy_overaudit' in flags else '0.22'
    thr = '0.38' if 'decoy_raise_threshold' in flags else ('0.20' if 'lower_threshold' in flags else '0.30')
    lines=["def choose(m):","    a=m['ambiguous_failure']; b=m['representation_failure']; c=m['consistency_failure']"]
    if 'add_audit' in flags or 'decoy_overaudit' in flags: lines += [f"    if c > {audit_t}: return 'audit'"]
    if 'repr_priority' in flags: lines += [f"    if b > a and b > {thr}: return 'propose'",f"    if a > {thr}: return 'probe'"]
    else: lines += [f"    if a > {thr}: return 'probe'",f"    if b > {thr}: return 'propose'"]
    if 'decoy_swap' in flags:
        lines=[x.replace("return 'probe'","return '__TMP__'").replace("return 'propose'","return 'probe'").replace("return '__TMP__'","return 'propose'") for x in lines]
    lines += ["    return 'hold'"]
    return '\n'.join(lines)+'\n'

def apply(src, mutation, applied):
    flags=set(applied); flags.add(mutation); return _src(flags)

def run(src,m):
    if not safe_source(src): raise ValueError('unsafe')
    ns={'__builtins__':{}}; exec(compile(src,'<candidate>','exec'),ns); return ns['choose'](m)

def rows(seed,n):
    r=random.Random(seed)
    return [{'ambiguous_failure':r.random()*.48,'representation_failure':r.random()*.48,'consistency_failure':r.random()*.35} for _ in range(n)]

def score(src,seed,n,truth_fn):
    correct=wrong=invalid=0; fails=[]
    for i,m in enumerate(rows(seed,n)):
        try:p=run(src,m)
        except Exception:p='__INVALID__'
        t=truth_fn(m)
        if p==t: correct+=1
        else:
            wrong+=1
            if p not in ACTIONS: invalid+=1
            fails.append({'i':i,'pred':p,'truth':t})
    return {'correct':correct,'verified_wrong':wrong,'invalid_output':invalid,'n':n,'failures':fails}

def choose_mutation(src,applied,seed,n,truth_fn,mode='evidence'):
    avail=[m for m in MUTATIONS if m not in applied]
    scored=[]
    for m in avail:
        cand=apply(src,m,applied); r=score(cand,seed,n,truth_fn); scored.append((r['correct'],-r['verified_wrong'],m,cand,r))
    scored.sort(reverse=True)
    if mode=='evidence': return scored[0]
    if mode=='reverse': return scored[-1]
    if mode=='constant':
        fixed=('decoy_swap','decoy_raise_threshold','decoy_overaudit','repr_priority','lower_threshold','add_audit')
        m=next(x for x in fixed if x in avail); cand=apply(src,m,applied); r=score(cand,seed,n,truth_fn); return (r['correct'],-r['verified_wrong'],m,cand,r)
    raise ValueError(mode)
