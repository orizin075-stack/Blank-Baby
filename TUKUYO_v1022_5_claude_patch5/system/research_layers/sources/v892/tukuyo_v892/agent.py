from .dsl import *
def version_space(d,obs): return [p for p in composed_programs(d) if all(run(p,x)==y for x,y in obs)]
def choose_probe(d,obs,pool):
 vs=version_space(d,obs); used={repr(x) for x,_ in obs}; best=None
 for x in pool:
  if repr(x) in used: continue
  groups={}
  for p in vs: groups[run(p,x)]=groups.get(run(p,x),0)+1
  if len(groups)<=1: continue
  n=len(vs); collision=sum(v*v for v in groups.values())/(n*n); key=(1-collision,len(groups),-max(groups.values()),repr(x))
  if best is None or key>best[0]: best=(key,x)
 return None if best is None else best[1]
def resolve_vs(d,obs):
 vs=version_space(d,obs); return vs[0] if len(vs)==1 else None
