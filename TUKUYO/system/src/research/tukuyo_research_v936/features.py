"""A deliberately finite, human-designed grammar; no oracle-specific expressions."""
import itertools, math
BASE = ('a', 'b', 'c')
DERIVED = tuple(f'{op}:{x}:{y}' for op in ('sum', 'diff', 'prod') for x,y in itertools.combinations(BASE, 2))
ALL_FEATURES = BASE + DERIVED

def values(m, features=ALL_FEATURES):
    a, b, c = (float(m[k]) for k in BASE)
    if any(not math.isfinite(x) or x<0 or x>1 for x in (a,b,c)):
        raise ValueError('metrics must be finite and inside [0,1]')
    d = {'a':a,'b':b,'c':c}
    for op,x,y in (f.split(':') for f in features if ':' in f):
        if op == 'sum': d[f'{op}:{x}:{y}'] = d[x]+d[y]
        elif op == 'diff': d[f'{op}:{x}:{y}'] = d[x]-d[y]
        elif op == 'prod': d[f'{op}:{x}:{y}'] = d[x]*d[y]
        else: raise ValueError(op)
    return d
