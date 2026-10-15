def op_mod(k,v): return v%k
def source_examples(k): return [(x,op_mod(k,x)) for x in range(-9,10)]
def infer_k(examples):
 m=[k for k in range(2,7) if all(op_mod(k,x)==y for x,y in examples)]; return m[0] if len(m)==1 else None
def apply(domain,k,x):
 if domain=='sequence_sum': return op_mod(k,sum(x))
 if domain=='event_count': return op_mod(k,sum(1 for e in x if e))
 if domain=='state_terminal': return op_mod(k,x[-1])
 raise KeyError(domain)
