ACTIONS=['increase_probe','increase_proposal','hold']
def bottleneck(metrics):
 if metrics['ambiguous_failure']>metrics['representation_failure']: return 'ambiguity'
 if metrics['representation_failure']>0:return 'representation'
 return 'none'
def propose(metrics,policy):
 b=bottleneck(metrics); p=dict(policy)
 if b=='ambiguity' and p['probe_budget']<4:p['probe_budget']+=1; a='increase_probe'
 elif b=='representation' and p['proposal_budget']<4:p['proposal_budget']+=1; a='increase_proposal'
 else:a='hold'
 return a,p
def score(policy,metrics): return 1-metrics['ambiguous_failure']*(1-policy['probe_budget']/4)-metrics['representation_failure']*(1-policy['proposal_budget']/4)-.02*(policy['probe_budget']+policy['proposal_budget'])
