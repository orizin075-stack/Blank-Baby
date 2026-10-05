import base64,json,sys,unittest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tukuyo_v944.gap import shaobj
from tukuyo_v946.promotion import expected_evaluation
from tukuyo_v947.transfer import adapt_state,adapt_graph
from tukuyo_v948.goals import propose_goal,verify_authorization
from tukuyo_v949.cycle import prepare,finalize
from tukuyo_v950.improver import config0,benchmark,propose_next
from tukuyo_v953.multigen import evolve

def truth(a,b):return a*b+a-b
def rows(n=36,off=0):return [{'a':i-9,'b':((i*5+3+off)%13)-6,'expected':truth(i-9,((i*5+3+off)%13)-6)} for i in range(n)]
def pub(sk):return base64.b64encode(sk.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode()
def sign(sk,p):
 raw=json.dumps(p,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode();return {'payload':p,'public_key':pub(sk),'signature':base64.b64encode(sk.sign(raw)).decode()}
class LaterRoute(unittest.TestCase):
 def test_01_v948_self_authored_goal_is_scored_not_self_authorized(self):
  rs=[{'problem_id':'small','gap_state':'REPRESENTATION_INSUFFICIENT','best_wrong':3,'estimated_cost':20,'novelty':1},{'problem_id':'big','gap_state':'REPRESENTATION_INSUFFICIENT','best_wrong':20,'estimated_cost':30,'novelty':2}]
  g=propose_goal(rs);self.assertEqual(g['selected_problem_id'],'big');self.assertTrue(g['authorization_required'])
  sk=Ed25519PrivateKey.generate();env=sign(sk,{'schema':'tukuyo.v948.goal_authority/1','goal_sha256':g['goal_sha256'],'selected_problem_id':'big','decision':'AUTHORIZE'});self.assertTrue(verify_authorization(g,env,pub(sk))['ok'])
 def test_02_v948_wrong_goal_authority_binding_blocked(self):
  g=propose_goal([{'problem_id':'p','gap_state':'REPRESENTATION_INSUFFICIENT','best_wrong':5,'estimated_cost':2,'novelty':1}]);sk=Ed25519PrivateKey.generate();env=sign(sk,{'schema':'tukuyo.v948.goal_authority/1','goal_sha256':g['goal_sha256'],'selected_problem_id':'other','decision':'AUTHORIZE'})
  with self.assertRaises(ValueError):verify_authorization(g,env,pub(sk))
 def _cycle(self):
  prep=prepare({'hard':rows(36),'easy':[{'a':i,'b':1,'expected':i+1} for i in range(20)]});goal,obs,evk,prom=[Ed25519PrivateKey.generate() for _ in range(4)]
  ge=sign(goal,{'schema':'tukuyo.v948.goal_authority/1','goal_sha256':prep['goal']['goal_sha256'],'selected_problem_id':prep['goal']['selected_problem_id'],'decision':'AUTHORIZE'})
  q=prep['probe'];oe=sign(obs,{'schema':'tukuyo.v949.probe_observation/1','cycle_prepare_sha256':prep['cycle_prepare_sha256'],'a':q['a'],'b':q['b'],'observed':q['candidate_prediction']})
  hidden=[{'x':r['a'],'y':r['b'],'expected':r['expected']} for r in rows(30,7)];dom={'state':adapt_state([{'state':r['a'],'delta':r['b'],'next':r['expected']} for r in rows(28,11)]),'graph':adapt_graph([{'degree':r['a'],'signal':r['b'],'response':r['expected']} for r in rows(28,19)])}
  ep=expected_evaluation(prep['candidate'],hidden,dom);ee=sign(evk,ep);ae=sign(prom,{'schema':'tukuyo.v946.promotion_authority/1','candidate_sha256':prep['candidate']['candidate_sha256'],'evaluation_receipt_sha256':shaobj(ee),'hidden_rows_sha256':ep['hidden_rows_sha256'],'transfer_domain_hashes':{k:v['rows_sha256'] for k,v in ep['transfer_domains'].items()},'decision':'PROMOTE'})
  keys={'goal_authority':pub(goal),'observer':pub(obs),'evaluator':pub(evk),'promotion_authority':pub(prom)}
  return prep,ge,oe,hidden,dom,ee,ae,keys
 def test_03_v949_full_bounded_research_cycle(self):
  x=self._cycle();r=finalize(*x);self.assertTrue(r['promoted']);self.assertEqual(r['status'],'PROMOTED_BOUNDED');self.assertFalse(r['general_l5_claim'])
 def test_04_v949_probe_can_reject_hypothesis(self):
  prep,ge,oe,h,d,ee,ae,k=self._cycle();q=prep['probe'];badsk=Ed25519PrivateKey.generate();k['observer']=pub(badsk);oe=sign(badsk,{'schema':'tukuyo.v949.probe_observation/1','cycle_prepare_sha256':prep['cycle_prepare_sha256'],'a':q['a'],'b':q['b'],'observed':q['baseline_prediction']});r=finalize(prep,ge,oe,h,d,ee,ae,k);self.assertFalse(r['promoted'])
 def test_05_v950_actual_improver_strictly_reduces_effort(self):
  c=config0();p=propose_next(c);self.assertTrue(p['improved']);self.assertLess(p['after']['effort'],p['before']['effort'])
 def test_06_v951_v953_multigen_chain(self):
  r=evolve(3);self.assertEqual(r['generations_completed'],3);self.assertTrue(r['blind']['success']);self.assertFalse(r['general_l6']);
  self.assertTrue(all(x['after_effort']<x['before_effort'] for x in r['chain']))
if __name__=='__main__':unittest.main()
