def choose(m):
    a=m['a']; b=m['b']; c=m['c']
    hi=a
    if b>hi: hi=b
    d=a-b
    if d<0: d=-d
    if c > 0.492000: return 'audit'
    if c >= 0.468000: return 'abstain'
    if hi < 0.268000: return 'hold'
    if hi <= 0.292000: return 'abstain'
    if d < 0.008000: return 'hold'
    if d <= 0.032000: return 'abstain'
    if a>=b: return 'probe'
    return 'propose'
