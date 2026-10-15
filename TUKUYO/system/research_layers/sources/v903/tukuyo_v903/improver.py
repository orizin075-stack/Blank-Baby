CANDIDATES={
'base':"def choose(metrics):\n    return 'hold'\n",
'ambiguity':"def choose(metrics):\n    return 'probe' if metrics['ambiguous_failure']>0.20 else 'hold'\n",
'representation':"def choose(metrics):\n    return 'propose' if metrics['representation_failure']>0.20 else 'hold'\n",
'joint':"def choose(metrics):\n    if metrics['ambiguous_failure']>=metrics['representation_failure'] and metrics['ambiguous_failure']>0.20:return 'probe'\n    if metrics['representation_failure']>0.20:return 'propose'\n    return 'hold'\n"}
def candidate_sources(): return dict(CANDIDATES)
