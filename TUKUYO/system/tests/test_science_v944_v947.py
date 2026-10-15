import base64,json,sys,unittest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tukuyo_v944.gap import search_evidence,classify,shaobj
from tukuyo_v945.primitive import propose,eval_proposal
from tukuyo_v946.promotion import expected_evaluation,verify_and_promote
from tukuyo_v947.transfer import adapt_state,adapt_graph,discover

def truth(a,b):return a*b+a-b
def rows(n=36,off=0):
 return [{'a':i-9,'b':((i*5+3+off)%13)-6,'expected':truth(i-9,((i*5+3+off)%13)-6)} for i in range(n)]
def sign(sk,p):
 pub=base64.b64encode(sk.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode()
 raw=json.dumps(p,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
 return {'payload':p,'public_key':pub,'signature':base64.b64encode(sk.sign(raw)).decode()}
def pub(sk):return base64.b64encode(sk.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode()

class ScienceRoute(unittest.TestCase):
 def test_01_v944_representation_gap_requires_complete_evidence(self):
  r=rows();e=search_evidence(r);g=classify(r,e);self.assertEqual(g['state'],'REPRESENTATION_INSUFFICIENT');self.assertGreater(g['best_wrong'],0)
  e2=json.loads(json.dumps(e));e2['runs']=e2['runs'][:-1];self.assertEqual(classify(r,e2)['state'],'SEARCH_INSUFFICIENT')
 def test_02_v944_tampered_search_evidence_rejected(self):
  r=rows();e=search_evidence(r);e['runs'][0]['best_wrong']=0
  with self.assertRaisesRegex(ValueError,'SEARCH_EVIDENCE_NOT_RECOMPUTABLE'):classify(r,e)
 def test_03_v944_data_insufficient_not_mislabeled(self):
  r=rows(5);self.assertEqual(classify(r,search_evidence(r))['state'],'DATA_INSUFFICIENT')
 def test_04_v944_resolved_in_known_class(self):
  r=[{'a':i,'b':i%4-2,'expected':i+(i%4-2)} for i in range(20)]
  self.assertEqual(classify(r,search_evidence(r))['state'],'RESOLVED_IN_CLASS')
 def test_05_v945_generates_unseen_composed_primitive(self):
  p=discover(rows())['proposal'];self.assertIsNotNone(p);self.assertEqual(p['training_wrong'],0);self.assertGreater(p['baseline_wrong'],0)
  self.assertNotIn(p['expression'],('(a+b)','(a*b)','(a-b)','max(a,b)','min(a,b)'))
  self.assertTrue(all(eval_proposal(p,r['a'],r['b'])==r['expected'] for r in rows()))
 def test_06_v945_candidate_hash_tamper_blocked(self):
  p=discover(rows())['proposal'];p['expression']='forged'
  with self.assertRaisesRegex(ValueError,'CANDIDATE_HASH'):eval_proposal(p,2,3)
 def _promotion_fixture(self):
  p=discover(rows())['proposal'];hidden=[{'x':r['a'],'y':r['b'],'expected':r['expected']} for r in rows(30,7)]
  state=[{'state':r['a'],'delta':r['b'],'next':r['expected']} for r in rows(28,11)]
  graph=[{'degree':r['a'],'signal':r['b'],'response':r['expected']} for r in rows(28,19)]
  domains={'state':adapt_state(state),'graph':adapt_graph(graph)};evk,auk=Ed25519PrivateKey.generate(),Ed25519PrivateKey.generate();ep=expected_evaluation(p,hidden,domains);ee=sign(evk,ep)
  auth={'schema':'tukuyo.v946.promotion_authority/1','candidate_sha256':p['candidate_sha256'],'evaluation_receipt_sha256':shaobj(ee),'hidden_rows_sha256':ep['hidden_rows_sha256'],'transfer_domain_hashes':{k:v['rows_sha256'] for k,v in ep['transfer_domains'].items()},'decision':'PROMOTE'};ae=sign(auk,auth)
  return p,hidden,domains,evk,auk,ee,ae
 def test_07_v946_external_hidden_and_transfer_promotion(self):
  p,h,d,evk,auk,ee,ae=self._promotion_fixture();res=verify_and_promote(p,h,d,ee,ae,pub(evk),pub(auk));self.assertEqual(res['scope'],'EXTERNALLY_VERIFIED_BOUNDED_PRIMITIVE')
 def test_08_v946_wrong_key_and_tamper_blocked(self):
  p,h,d,evk,auk,ee,ae=self._promotion_fixture();bad=Ed25519PrivateKey.generate()
  with self.assertRaises(ValueError):verify_and_promote(p,h,d,ee,ae,pub(bad),pub(auk))
  h[0]['expected']+=1
  with self.assertRaises(ValueError):verify_and_promote(p,h,d,ee,ae,pub(evk),pub(auk))
 def test_09_v947_candidate_is_unchanged_across_domains(self):
  p=discover(rows())['proposal'];h=p['candidate_sha256']
  for a,b in [(-3,4),(0,7),(8,-2)]:self.assertEqual(eval_proposal(p,a,b),truth(a,b))
  self.assertEqual(p['candidate_sha256'],h)

if __name__=='__main__':unittest.main()
