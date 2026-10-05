CANDIDATES=[{'probe_budget':p,'proposal_budget':q} for p in range(1,5) for q in range(1,5)]
def utility(policy,episodes):
 s=0
 for e in episodes:
  if e=='ambiguous': s+=min(policy['probe_budget'],3)/3
  elif e=='outside': s+=min(policy['proposal_budget'],2)/2
  else:s+=1
 return s/len(episodes)
def propose(training): return max(CANDIDATES,key=lambda p:(utility(p,training)-0.03*(p['probe_budget']+p['proposal_budget']),-p['probe_budget'],-p['proposal_budget']))
