import random,hashlib
SOURCES=[
"def choose(m):\n return 'hold'\n",
"def choose(m):\n return 'probe' if m['ambiguous_failure']>.2 else ('propose' if m['representation_failure']>.2 else 'hold')\n",
"def choose(m):\n a=m['ambiguous_failure'];b=m['representation_failure']\n if a>=b and a>.2:return 'probe'\n if b>.2:return 'propose'\n return 'hold'\n",
]
def eval_src(src,seed,n=220):
 ns={};exec(src,ns);f=ns['choose'];rng=random.Random(seed);c=0
 for _ in range(n):
  a=rng.random()*.5;b=rng.random()*.5;truth='probe' if a>=b and a>.2 else ('propose' if b>.2 else 'hold');c+=f({'ambiguous_failure':a,'representation_failure':b})==truth
 return c
def run():
 rows=[]; parent=SOURCES[0]
 for g in range(3):
  cand=SOURCES[min(g+1,2)]; seed=90400+g
  bp=eval_src(parent,seed);bc=eval_src(cand,seed); accept=bc>=bp; chosen=cand if accept else parent
  rows.append({'generation':g,'parent_sha256':hashlib.sha256(parent.encode()).hexdigest(),'candidate_sha256':hashlib.sha256(cand.encode()).hexdigest(),'parent_correct':bp,'candidate_correct':bc,'accepted':accept,'chosen_sha256':hashlib.sha256(chosen.encode()).hexdigest()});parent=chosen
 return rows,parent
