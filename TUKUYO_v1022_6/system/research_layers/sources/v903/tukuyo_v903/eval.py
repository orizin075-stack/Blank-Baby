import random,types
def score(src,seed,n=160):
 ns={}; exec(src,ns); choose=ns['choose']; rng=random.Random(seed); correct=0; wrong=0
 for _ in range(n):
  a=rng.random()*.5; b=rng.random()*.5
  truth='probe' if a>=b and a>.20 else ('propose' if b>.20 else 'hold')
  p=choose({'ambiguous_failure':a,'representation_failure':b})
  correct+=p==truth; wrong+=p not in ('probe','propose','hold')
 return correct,wrong
