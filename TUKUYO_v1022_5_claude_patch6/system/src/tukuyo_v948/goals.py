"""v948 self-authored bounded research-goal proposals with external authorization."""
from __future__ import annotations
import hashlib,json
from tukuyo_v946.promotion import check
from tukuyo_v944.gap import shaobj

def propose_goal(problem_reports):
 if not isinstance(problem_reports,list) or not problem_reports:raise ValueError('NO_PROBLEMS')
 eligible=[]
 for r in problem_reports:
  if set(r)!={'problem_id','gap_state','best_wrong','estimated_cost','novelty'}:raise ValueError('PROBLEM_SCHEMA')
  if r['gap_state']!='REPRESENTATION_INSUFFICIENT':continue
  if any(type(r[k]) is not int or r[k]<0 for k in ('best_wrong','estimated_cost','novelty')):raise ValueError('PROBLEM_VALUE')
  score=r['best_wrong']*100+r['novelty']*10-r['estimated_cost']
  eligible.append((score,r['problem_id'],r))
 if not eligible:raise ValueError('NO_RESEARCH_WORTHY_GAP')
 eligible.sort(key=lambda x:(-x[0],x[1]));score,pid,r=eligible[0]
 body={'schema':'tukuyo.v948.goal_proposal/1','selected_problem_id':pid,'score':score,'problem_report_sha256':shaobj(r),
       'objective':'reduce verified residual without self-certifying promotion','authorization_required':True}
 body['goal_sha256']=shaobj({k:v for k,v in body.items() if k!='goal_sha256'})
 return body

def verify_authorization(goal,env,authority_pub):
 p=check(env,authority_pub)
 required={'schema':'tukuyo.v948.goal_authority/1','goal_sha256':goal['goal_sha256'],'selected_problem_id':goal['selected_problem_id'],'decision':'AUTHORIZE'}
 if p!=required:raise ValueError('GOAL_AUTHORITY_BINDING')
 return {'ok':True,'goal_sha256':goal['goal_sha256'],'authority_receipt_sha256':shaobj(env)}
