META=[]
for k in range(2,7): META.append(('mod',k)); META.append(('floordiv',k))
META += [('sign',0)] + [('gt',k) for k in range(-3,4)]
def run(p,x):
 op,k=p
 if op=='mod': return x%k
 if op=='floordiv': return x//k
 if op=='sign': return (x>0)-(x<0)
 if op=='gt': return int(x>k)
 raise KeyError(op)
def propose(obs):
 m=[p for p in META if all(run(p,x)==y for x,y in obs)]
 return {'status':'UNIQUE_PROPOSAL','program':m[0]} if len(m)==1 else {'status':'AMBIGUOUS' if m else 'NO_PROPOSAL','program':None,'match_count':len(m)}
