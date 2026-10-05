def choose(m):
    a=m['a']; b=m['b']; c=m['c']
    hi=a
    if b>hi: hi=b
    d=a-b
    if d<0: d=-d
    if c > 0.252000: return 'audit'
    if c >= 0.228000: return 'abstain'
    if hi < 0.348000: return 'hold'
    if hi <= 0.372000: return 'abstain'
    if d < 0.000000: return 'hold'
    if d <= 0.012000: return 'abstain'
    if a>=b: return 'probe'
    return 'propose'
