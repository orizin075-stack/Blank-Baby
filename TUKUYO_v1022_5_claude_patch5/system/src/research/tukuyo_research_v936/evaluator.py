"""Synthetic local development oracles; NEVER a third-party or blind evaluator."""
import random

def truth(task,m):
    a,b,c=m['a'],m['b'],m['c']
    if task=='v935_reference':
        if c>.22 or (a+b>.70 and c>.15):return 'audit'
        if b>a and b>.20:return 'propose'
        if a>.20:return 'probe'
        return 'hold'
    if task=='coupled_product':
        if a*b>.082 and c<.12:return 'audit'
        if a+b>.58 and c>.24:return 'audit'
        if b>a+.09:return 'propose'
        if a>.32:return 'probe'
        return 'hold'
    if task=='difference_shift':
        if a-b>.15 and c>.14:return 'audit'
        if b+c>.53:return 'propose'
        if a+.4*b>.46:return 'probe'
        return 'hold'
    raise ValueError(task)

def rows(task, seed, n, distribution):
    r=random.Random(seed)
    for _ in range(n):
        if distribution=='uniform':a,b,c=r.random()*.48,r.random()*.48,r.random()*.35
        elif distribution=='edges':
            a,b,c=(.48*r.betavariate(.53,.53),.48*r.betavariate(.53,.53),.35*r.betavariate(.53,.53))
        elif distribution=='anti_corr':
            a=r.random()*.48;b=max(0.,min(.48,.48-a+r.gauss(0,.055)));c=r.random()*.35
        elif distribution=='boundary':
            a=r.random()*.48;b=max(0.,min(.48,.70-a+r.gauss(0,.025)));c=max(0.,min(.35,r.choice([.15,.22,.24]) + r.gauss(0,.02)))
        else:raise ValueError(distribution)
        m={'a':a,'b':b,'c':c}
        yield m, truth(task,m)
