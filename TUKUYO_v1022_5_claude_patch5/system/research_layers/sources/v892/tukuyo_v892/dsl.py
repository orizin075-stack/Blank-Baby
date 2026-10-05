from functools import lru_cache
INT_PRIMS={'inc':lambda x:x+1,'dec':lambda x:x-1,'neg':lambda x:-x,'abs':lambda x:abs(x),'double':lambda x:2*x,'clip0':lambda x:max(x,0),'square':lambda x:x*x}
SEQ_PRIMS={'sum':lambda s:sum(s),'max':lambda s:max(s),'min':lambda s:min(s),'count_pos':lambda s:sum(x>0 for x in s),'count_zero':lambda s:sum(x==0 for x in s),'first':lambda s:s[0],'last':lambda s:s[-1],'length':lambda s:len(s)}
SCALAR_BASIS=list(range(-8,9)); SEQ_BASIS=[(-3,-1,2),(0,0,1),(4,-2,1,0),(-1,-1,-1),(2,3,4),(5,),(-5,5),(1,0,-1,2,-2)]
def run(p,x):
 k,a,b=p
 if k=='scalar2': return INT_PRIMS[a](INT_PRIMS[b](x))
 if k=='seq2': return INT_PRIMS[a](SEQ_PRIMS[b](x))
 if k=='scalar1': return INT_PRIMS[a](x)
 if k=='seq1': return SEQ_PRIMS[a](x)
 raise KeyError(k)
def base_programs(d): return [('scalar1',n,'') for n in INT_PRIMS] if d=='scalar' else [('seq1',n,'') for n in SEQ_PRIMS]
@lru_cache(maxsize=None)
def composed_programs(d):
 raw=[('scalar2',a,b) for a in INT_PRIMS for b in INT_PRIMS] if d=='scalar' else [('seq2',a,b) for a in INT_PRIMS for b in SEQ_PRIMS]; basis=SCALAR_BASIS if d=='scalar' else SEQ_BASIS
 bs={tuple(run(p,x) for x in basis) for p in base_programs(d)}; seen={}
 for p in raw:
  sig=tuple(run(p,x) for x in basis)
  if sig not in bs and sig not in seen: seen[sig]=p
 return list(seen.values())
def matches(d,obs): return [p for p in composed_programs(d) if all(run(p,x)==y for x,y in obs)]
def resolve(d,obs):
 m=matches(d,obs); return m[0] if len(m)==1 else None
def valid(p,target,hold): return all(run(p,x)==run(target,x) for x in hold)
