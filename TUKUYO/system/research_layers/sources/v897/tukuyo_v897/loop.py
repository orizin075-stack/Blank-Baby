ACTIVE={'direct','compose','probe','gap','propose'}
def route(case):
 if case['kind']=='direct': return 'direct'
 if case['kind']=='compose': return 'compose'
 if case['kind']=='ambiguous': return 'probe'
 if case['kind']=='outside': return 'propose'
 return 'gap'
def old_route(case): return 'direct' if case['kind']=='direct' else ('compose' if case['kind']=='compose' else 'abstain')
def success(action,case): return action==route(case)
