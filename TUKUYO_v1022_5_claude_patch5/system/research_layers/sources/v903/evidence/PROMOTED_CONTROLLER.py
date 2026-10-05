def choose(metrics):
    if metrics['ambiguous_failure']>=metrics['representation_failure'] and metrics['ambiguous_failure']>0.20:return 'probe'
    if metrics['representation_failure']>0.20:return 'propose'
    return 'hold'
