# Synthetic evaluation-only oracle. Proposer/synthesizer modules do not import this file.
def truth(m):
 a=m['ambiguous_failure'];b=m['representation_failure'];c=m['consistency_failure']
 if c>0.22 or (a+b>0.70 and c>0.15):return 'audit'
 if b>a and b>0.20:return 'propose'
 if a>0.20:return 'probe'
 return 'hold'
