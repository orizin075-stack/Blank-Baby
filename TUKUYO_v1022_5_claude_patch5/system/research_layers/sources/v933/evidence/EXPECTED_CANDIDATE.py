def choose(m):
    a=m['ambiguous_failure']; b=m['representation_failure']; c=m['consistency_failure']
    if m['ambiguous_failure'] + m['representation_failure'] > 0.69410705921405991 and m['consistency_failure'] > 0.15560496428426754: return 'audit'
    if c > 0.22: return 'audit'
    if b > a and b > 0.20: return 'propose'
    if a > 0.20: return 'probe'
    return 'hold'
