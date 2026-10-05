import ast,random,hashlib
ACTIONS={'probe','propose','hold','audit'}
BASE_SOURCE="def choose(m):\n    a=m['ambiguous_failure']; b=m['representation_failure']\n    if a>0.30: return 'probe'\n    if b>0.30: return 'propose'\n    return 'hold'\n"
FINAL_SOURCE="def choose(m):\n    a=m['ambiguous_failure']; b=m['representation_failure']\n    c=m['consistency_failure']\n    if c>0.22: return 'audit'\n    if a>=b and a>0.20: return 'probe'\n    if b>0.20: return 'propose'\n    return 'hold'\n"
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
def run(src,m):
 ns={'__builtins__':{}};exec(compile(src,'<candidate>','exec'),ns);return ns['choose'](m)
def truth(m):
 a=m['ambiguous_failure'];b=m['representation_failure'];c=m['consistency_failure']
 if c>.22:return 'audit'
 if a>=b and a>.20:return 'probe'
 if b>.20:return 'propose'
 return 'hold'
def evaluate(src,seed,n):
 r=random.Random(seed); correct=wrong=invalid=0
 for _ in range(n):
  m={'ambiguous_failure':r.random()*.48,'representation_failure':r.random()*.48,'consistency_failure':r.random()*.35}
  try:p=run(src,m)
  except Exception:p='__INVALID__'
  y=truth(m)
  if p==y:correct+=1
  else:wrong+=1
  if p not in ACTIONS:invalid+=1
 return {'n':n,'correct':correct,'verified_wrong':wrong,'invalid_output':invalid,'coverage':1.0}
