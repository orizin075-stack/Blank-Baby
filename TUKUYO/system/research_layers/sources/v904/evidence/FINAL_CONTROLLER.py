def choose(m):
 a=m['ambiguous_failure'];b=m['representation_failure']
 if a>=b and a>.2:return 'probe'
 if b>.2:return 'propose'
 return 'hold'
