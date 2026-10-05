from .rulelearner import *
import hashlib
def cegis(cfg,base_seed,rounds=4):
    train=label_rows(gen_rows(base_seed,32,'uniform'),cfg); history=[]; src=None
    for r in range(rounds):
      fitcfg,err=fit(train); src=source_for(fitcfg,.012)
      pool=label_rows(gen_rows(base_seed+100+r,240,'uniform'),cfg); ev=evaluate_source(src,pool)
      counter=[]
      for e in pool:
        p=run_source(src,e['m'])
        if p!='abstain' and p!=e['y']: counter.append(e)
      # also add abstained boundary examples so coverage can improve
      if len(counter)<24:
        for e in pool:
          if run_source(src,e['m'])=='abstain': counter.append(e)
          if len(counter)>=24: break
      train.extend(counter[:48])
      history.append({'round':r+1,'fit_cfg':fitcfg,'train_size':len(train),'pool':ev,'counterexamples_added':min(48,len(counter)),'source_sha256':hashlib.sha256(src.encode()).hexdigest()})
    return src,history
