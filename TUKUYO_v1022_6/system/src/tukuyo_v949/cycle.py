"""v949 bounded autonomous research-cycle orchestration.

TUKUYO proposes the goal and experiment; external actors authorize the goal,
provide the probe observation, evaluate hidden/transfer data, and authorize promotion.
"""
from __future__ import annotations
from tukuyo_v944.gap import search_evidence,classify,OPS,shaobj
from tukuyo_v945.primitive import propose,eval_proposal
from tukuyo_v946.promotion import check,verify_and_promote
from tukuyo_v948.goals import propose_goal,verify_authorization

def _best_known(rows):
 scores=[]
 for n,f in OPS.items():scores.append((sum(f(r['a'],r['b'])!=r['expected'] for r in rows),n))
 return min(scores)[1]
def _probe(candidate,baseline):
 for a in range(-7,8):
  for b in range(-7,8):
   c=eval_proposal(candidate,a,b);k=OPS[baseline](a,b)
   if c!=k:return {'a':a,'b':b,'candidate_prediction':c,'baseline_prediction':k}
 raise ValueError('NO_DISCRIMINATING_PROBE')
def prepare(problem_tracks):
 reports=[];cache={}
 for pid,rows in sorted(problem_tracks.items()):
  ev=search_evidence(rows);g=classify(rows,ev);cache[pid]=(rows,ev,g)
  reports.append({'problem_id':pid,'gap_state':g['state'],'best_wrong':g.get('best_wrong',0),'estimated_cost':len(rows),'novelty':1 if g['state']=='REPRESENTATION_INSUFFICIENT' else 0})
 goal=propose_goal(reports);rows,ev,g=cache[goal['selected_problem_id']];candidate=propose(rows,ev);baseline=_best_known(rows);probe=_probe(candidate,baseline)
 return {'schema':'tukuyo.v949.prepared_cycle/1','goal':goal,'goal_reports':reports,'training_rows_sha256':shaobj(rows),'candidate':candidate,'baseline_operator':baseline,'probe':probe,
         'cycle_prepare_sha256':shaobj({'goal':goal,'training_rows_sha256':shaobj(rows),'candidate_sha256':candidate['candidate_sha256'],'baseline_operator':baseline,'probe':probe})}
def finalize(prepared,goal_auth_env,observer_env,hidden_rows,transfer_domains,evaluator_env,promotion_env,keys):
 ga=verify_authorization(prepared['goal'],goal_auth_env,keys['goal_authority'])
 op=check(observer_env,keys['observer']);q=prepared['probe']
 required={'schema':'tukuyo.v949.probe_observation/1','cycle_prepare_sha256':prepared['cycle_prepare_sha256'],'a':q['a'],'b':q['b'],'observed':op.get('observed')}
 if op!=required:raise ValueError('PROBE_OBSERVATION_BINDING')
 if op['observed']!=q['candidate_prediction']:return {'schema':'tukuyo.v949.cycle_result/1','status':'HYPOTHESIS_REJECTED_BY_PROBE','promoted':False}
 promoted=verify_and_promote(prepared['candidate'],hidden_rows,transfer_domains,evaluator_env,promotion_env,keys['evaluator'],keys['promotion_authority'])
 return {'schema':'tukuyo.v949.cycle_result/1','status':'PROMOTED_BOUNDED','promoted':True,'goal_sha256':prepared['goal']['goal_sha256'],'goal_authority_receipt_sha256':ga['authority_receipt_sha256'],
         'probe_observation_sha256':shaobj(observer_env),'candidate_sha256':prepared['candidate']['candidate_sha256'],'promotion':promoted,'general_l5_claim':False}
