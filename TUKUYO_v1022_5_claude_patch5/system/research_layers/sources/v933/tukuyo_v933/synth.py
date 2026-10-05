import itertools
FEATURES=('ambiguous_failure','representation_failure','consistency_failure');ACTIONS=('audit','probe','propose','hold')
def synthesize(base_choose,labeled_rows,bins=20):
 best=None
 for x,y in itertools.combinations(FEATURES,2):
  z=next(k for k in FEATURES if k not in (x,y));sums=sorted(m[x]+m[y] for m,t in labeled_rows);zs=sorted(m[z] for m,t in labeled_rows)
  t1s=sorted(set(sums[int((len(sums)-1)*q/bins)] for q in range(3,bins)));t2s=sorted(set(zs[int((len(zs)-1)*q/bins)] for q in range(3,bins)))
  for t1 in t1s:
   for t2 in t2s:
    for action in ACTIONS:
     c=0;over=0
     for m,t in labeled_rows:
      p=action if (m[x]+m[y]>t1 and m[z]>t2) else base_choose(m);c+=p==t;over+=p!=base_choose(m)
     key=(c,-over,x,y,z,t1,t2,action)
     if best is None or key>best:best=key
 return {'correct':best[0],'x':best[2],'y':best[3],'z':best[4],'t1':best[5],'t2':best[6],'action':best[7]}
def render(base_src,rule):
 lines=base_src.splitlines();line=f"    if m['{rule['x']}'] + m['{rule['y']}'] > {rule['t1']:.17g} and m['{rule['z']}'] > {rule['t2']:.17g}: return '{rule['action']}'";lines.insert(2,line);return '\n'.join(lines)+'\n'
