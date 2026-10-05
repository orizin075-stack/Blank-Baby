def choose(m):
    a=m['a']; b=m['b']; c=m['c']
    hi=a
    if b>hi: hi=b
    d=a-b
    if d<0: d=-d
    if c > 0.492000: return 'audit'
    if c >= 0.468000: return 'abstain'
    if hi < 0.308000: return 'hold'
    if hi <= 0.332000: return 'abstain'
    if d < 0.088000: return 'hold'
    if d <= 0.112000: return 'abstain'
    if a>=b: return 'probe'
    return 'propose'
