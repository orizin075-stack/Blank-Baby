from .patcher import *
def run():
 src=BASE_SOURCE; applied=[]; rows=[]
 for g in range(3):
  train_seed=91610+g*100;hold_seed=91660+g*100
  train=evaluate(src,train_seed,800); k=proposed_patch(train,applied); cand=apply(src,k)
  parent_hold=evaluate(src,hold_seed,800); cand_hold=evaluate(cand,hold_seed,800)
  accept=(cand_hold['wrong']==0 and cand_hold['correct']>parent_hold['correct'])
  new=cand if accept else src
  rows.append({'generation':g+1,'patch':k,'accepted':accept,'train_correct':train['correct'],'parent_holdout_correct':parent_hold['correct'],'candidate_holdout_correct':cand_hold['correct'],'parent_sha256':source_sha(src),'candidate_sha256':source_sha(cand),'promoted_sha256':source_sha(new),'verified_wrong':cand_hold['wrong'],'holdout_seed':hold_seed})
  if accept: src=new;applied.append(k)
 return rows,src
