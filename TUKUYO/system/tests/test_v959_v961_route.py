import base64,tempfile,unittest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from tukuyo_v959.agenda import *
from tukuyo_v960.campaign import run_campaign
from tukuyo_v961.evolution import *

def sign(priv,payload):
 pub=base64.b64encode(priv.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode()
 return {'payload':payload,'public_key':pub,'signature':base64.b64encode(priv.sign(canon(payload))).decode()}
def pubfile(td,priv,name):
 p=td/name;p.write_text(base64.b64encode(priv.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode());return p

class Route(unittest.TestCase):
 def test_01_v959_selects_research_goal(self):
  cs=[
   {'challenge_id':'low','gap_state':'SEARCH_INSUFFICIENT','information_gain':2,'capability_gain':1,'uncertainty':1,'estimated_cost':5,'safety_risk':0},
   {'challenge_id':'high','gap_state':'REPRESENTATION_INSUFFICIENT','information_gain':8,'capability_gain':7,'uncertainty':4,'estimated_cost':9,'safety_risk':0},
   {'challenge_id':'risky','gap_state':'HYPOTHESIS_AMBIGUOUS','information_gain':10,'capability_gain':9,'uncertainty':5,'estimated_cost':3,'safety_risk':10}]
  a=propose_agenda(cs);self.assertEqual(a['selected_challenge_id'],'high');self.assertGreater(a['ranking'][0]['score'],a['ranking'][1]['score'])
 def test_02_authority_cannot_rewrite_goal(self):
  a=propose_agenda([{'challenge_id':'a','gap_state':'REPRESENTATION_INSUFFICIENT','information_gain':5,'capability_gain':5,'uncertainty':2,'estimated_cost':4,'safety_risk':0},{'challenge_id':'b','gap_state':'SEARCH_INSUFFICIENT','information_gain':1,'capability_gain':1,'uncertainty':1,'estimated_cost':2,'safety_risk':0}])
  with tempfile.TemporaryDirectory() as x:
   td=Path(x);k=Ed25519PrivateKey.generate();pf=pubfile(td,k,'g.pub');p={'schema':'tukuyo.v959.goal_authority/1','agenda_sha256':a['agenda_sha256'],'selected_challenge_id':a['selected_challenge_id'],'decision':'AUTHORIZE','budget_ceiling':10,'safety_decision':'ALLOW_BOUNDED'}
   self.assertTrue(verify_authorization(a,sign(k,p),pf)['ok']);p['replacement_objective']='other'
   with self.assertRaises(ValueError):verify_authorization(a,sign(k,p),pf)
 def test_03_v960_can_lose_then_switch(self):
  with tempfile.TemporaryDirectory() as x:
   td=Path(x);k=Ed25519PrivateKey.generate();pf=pubfile(td,k,'o.pub');q={'a':3,'b':4};obs=[]
   for i in (1,2):obs.append(sign(k,{'schema':'tukuyo.v960.probe_observation/1','challenge_id':'c1','cycle':i,'a':3,'b':4,'observed':12}))
   hs=[{'hypothesis_id':'ADD','predict':lambda a,b:a+b},{'hypothesis_id':'MUL','predict':lambda a,b:a*b}]
   r=run_campaign('c1',hs,q,obs,pf);self.assertEqual(r['cycles_used'],2);self.assertEqual(r['trace'][0]['status'],'REJECTED_BY_EXTERNAL_PROBE');self.assertEqual(r['selected_hypothesis_id'],'MUL')
 def test_04_v960_all_fail_is_not_promoted(self):
  with tempfile.TemporaryDirectory() as x:
   td=Path(x);k=Ed25519PrivateKey.generate();pf=pubfile(td,k,'o.pub');obs=[sign(k,{'schema':'tukuyo.v960.probe_observation/1','challenge_id':'c','cycle':i,'a':2,'b':5,'observed':999}) for i in (1,2)]
   hs=[{'hypothesis_id':'A','predict':lambda a,b:a+b},{'hypothesis_id':'M','predict':lambda a,b:a*b}]
   r=run_campaign('c',hs,{'a':2,'b':5},obs,pf);self.assertEqual(r['status'],'NO_SUPPORTED_HYPOTHESIS')
 def test_05_v961_policy_improves_without_family_regression(self):
  r=compare();self.assertEqual(r['decision'],'PROMOTE_BOUNDED_META_POLICY');self.assertEqual(r['family_regressions'],[]);self.assertLess(r['candidate']['aggregate_family_effort'],r['parent']['aggregate_family_effort'])
 def test_06_v961_overspecialized_policy_rejected(self):
  bad={'policy_id':'BAD','family_config':{'polynomial':'MUL_FIRST','piecewise':'MUL_FIRST','absolute':'MUL_FIRST'}}
  r=compare(candidate=bad);self.assertEqual(r['decision'],'REJECT');self.assertTrue(r['family_regressions'])
if __name__=='__main__':unittest.main()
