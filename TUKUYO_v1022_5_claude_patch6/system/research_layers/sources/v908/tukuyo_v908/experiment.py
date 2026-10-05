import random,hashlib
CANDS={
'hold':"def choose(m):\n return 'hold'\n",
'amb':"def choose(m):\n return 'probe' if m['ambiguous_failure']>.2 else 'hold'\n",
'joint':"def choose(m):\n a=m['ambiguous_failure'];b=m['representation_failure']\n if a>=b and a>.2:return 'probe'\n if b>.2:return 'propose'\n return 'hold'\n"}
def rows(family,seed,n=240):
 r=random.Random(seed);out=[]
 for _ in range(n):
  if family=='uniform':a,b=r.random()*.5,r.random()*.5
  elif family=='skew_ambiguity':a,b=r.betavariate(4,2)*.5,r.betavariate(2,5)*.5
  elif family=='skew_representation':a,b=r.betavariate(2,5)*.5,r.betavariate(4,2)*.5
  else:
   x=r.random();a=.5*abs(2*x-1);b=.5*(1-abs(2*x-1))
  truth='probe' if a>=b and a>.2 else ('propose' if b>.2 else 'hold');out.append(({'ambiguous_failure':a,'representation_failure':b},truth))
 return out
def score(src,data):
 ns={};exec(src,ns);f=ns['choose'];return sum(f(m)==t for m,t in data)
def run():
 train=['uniform','skew_ambiguity','skew_representation'];held='anti_correlated';table=[]
 for n,s in CANDS.items():table.append({'name':n,'source_sha256':hashlib.sha256(s.encode()).hexdigest(),'train_correct':sum(score(s,rows(f,90800+i)) for i,f in enumerate(train))})
 best=max(table,key=lambda x:x['train_correct']);hs=score(CANDS[best['name']],rows(held,90899));return table,best,hs
