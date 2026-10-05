def choose(m):
    a=m['ambiguous_failure']; b=m['representation_failure']; c=m['consistency_failure']
    if c > 0.22: return 'audit'
    if b > a and b > 0.20: return 'propose'
    if a > 0.20: return 'probe'
    return 'hold'
