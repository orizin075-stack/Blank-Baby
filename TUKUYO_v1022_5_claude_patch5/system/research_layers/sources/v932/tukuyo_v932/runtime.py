import random,hashlib
BASE_SOURCE="""def choose(m):
    a=m['ambiguous_failure']; b=m['representation_failure']; c=m['consistency_failure']
    if a > 0.30: return 'probe'
    if b > 0.30: return 'propose'
    return 'hold'
"""
MUTATIONS=('add_audit','lower_threshold','repr_priority','decoy_overaudit','decoy_raise_threshold','decoy_swap')
def _src(flags):
 audit_t='0.10' if 'decoy_overaudit' in flags else '0.22';thr='0.38' if 'decoy_raise_threshold' in flags else ('0.20' if 'lower_threshold' in flags else '0.30')
 lines=["def choose(m):","    a=m['ambiguous_failure']; b=m['representation_failure']; c=m['consistency_failure']"]
 if 'add_audit' in flags or 'decoy_overaudit' in flags:lines+=[f"    if c > {audit_t}: return 'audit'"]
 if 'repr_priority' in flags:lines += [f"    if b > a and b > {thr}: return 'propose'",f"    if a > {thr}: return 'probe'"]
 else:lines += [f"    if a > {thr}: return 'probe'",f"    if b > {thr}: return 'propose'"]
 if 'decoy_swap' in flags:lines=[x.replace("return 'probe'","return '__TMP__'").replace("return 'propose'","return 'probe'").replace("return '__TMP__'","return 'propose'") for x in lines]
 lines += ["    return 'hold'"];return '\n'.join(lines)+'\n'
def apply(src,mutation,applied):flags=set(applied);flags.add(mutation);return _src(flags)
def rows(seed,n):
 r=random.Random(seed);return [{'ambiguous_failure':r.random()*.48,'representation_failure':r.random()*.48,'consistency_failure':r.random()*.35} for _ in range(n)]
def compile_choose(src):ns={'__builtins__':{}};exec(compile(src,'<c>','exec'),ns);return ns['choose']
def eval_source(src,seed,n,truth_fn):
 f=compile_choose(src);correct=wrong=invalid=0
 for m in rows(seed,n):
  try:p=f(m)
  except Exception:p='__INVALID__'
  t=truth_fn(m);correct+=p==t;wrong+=p!=t;invalid+=p not in {'probe','propose','hold','audit'}
 return {'correct':correct,'verified_wrong':wrong,'invalid_output':invalid,'n':n}
