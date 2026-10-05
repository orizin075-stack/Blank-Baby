import random,hashlib
SRC=["def choose(m):\n return 'hold'\n","def choose(m):\n return 'probe' if m['ambiguous_failure']>.2 else ('propose' if m['representation_failure']>.2 else 'hold')\n","def choose(m):\n a=m['ambiguous_failure'];b=m['representation_failure']\n if a>=b and a>.2:return 'probe'\n if b>.2:return 'propose'\n return 'hold'\n"]
def evals(src,seed,n=300):
 ns={};exec(src,ns);f=ns['choose'];r=random.Random(seed);c=0
 for _ in range(n):
  a=r.random()*.5;b=r.random()*.5;t='probe' if a>=b and a>.2 else ('propose' if b>.2 else 'hold');c+=f({'ambiguous_failure':a,'representation_failure':b})==t
 return c
def run():
 parent=SRC[0];rows=[];calls=0
 for g in range(3):
  candidates=SRC[:min(3,g+2)];seed=90910+g;scores=[]
  for c in candidates:scores.append((evals(c,seed),c));calls+=1
  bc,chosen=max(scores,key=lambda x:x[0]);bp=evals(parent,seed);calls+=1;accept=bc>=bp;new=chosen if accept else parent
  rows.append({'generation':g,'seed':seed,'parent_correct':bp,'best_candidate_correct':bc,'accepted':accept,'parent_sha256':hashlib.sha256(parent.encode()).hexdigest(),'chosen_sha256':hashlib.sha256(new.encode()).hexdigest(),'candidate_count':len(candidates)});parent=new
 return rows,parent,calls
