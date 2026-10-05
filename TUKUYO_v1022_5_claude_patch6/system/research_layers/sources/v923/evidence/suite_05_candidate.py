def choose(m):
    a=m['a']; b=m['b']; c=m['c']
    hi=a
    if b>hi: hi=b
    d=a-b
    if d<0: d=-d
    if c > 0.532000: return 'audit'
    if c >= 0.508000: return 'abstain'
    if hi < 0.228000: return 'hold'
    if hi <= 0.252000: return 'abstain'
    if d < 0.048000: return 'hold'
    if d <= 0.072000: return 'abstain'
    if a>=b: return 'probe'
    return 'propose'
