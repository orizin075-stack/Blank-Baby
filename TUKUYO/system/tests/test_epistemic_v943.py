import sys,tempfile,unittest,json,copy
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tukuyo_v943 import epistemic as ep
from tukuyo_v939.bootstrap import mounted

class EpistemicCycle(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='v943_test_');cls.work=Path(cls.tmp.name);cls.data=cls.work/'data';cls.trust=cls.work/'external_trust';cls.trust.mkdir()
  cls.keys={x:Ed25519PrivateKey.generate() for x in ('observer','evaluator','authority')}
  for x,k in cls.keys.items():(cls.trust/(x+'.pub')).write_text(ep.public(k))
  with mounted() as api:
   api['bridge'].init(api,cls.data,'TEST_INDIVIDUAL_943')
   sample=Path(__file__).resolve().parents[1]/'examples/SEMANTIC_TEACH_SAMPLE.json'
   api['bridge'].teach(api,cls.data,sample,True)
  ep.init(cls.data,cls.trust/'local.pub')
  cls.surface='とけあわせる'
  cls.initial=ep.audit(cls.data,cls.trust)
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_01_import(self):
  res=ep.import_native(self.data,self.trust,self.surface)
  self.assertEqual('LOCAL_VERIFIED_NOT_THIRD_PARTY',res['native_status'])
  self.assertEqual('ACTIVE',ep.status(self.data,self.trust)['surfaces'][self.surface]['status'])
 def test_01a_conflicting_original_training_must_not_be_overwritten(self):
  with self.assertRaisesRegex(ValueError,'CONFLICTS_WITH_NATIVE_TRAINING'):
   ep.challenge(self.data,self.trust,self.surface,{'a':2,'b':3,'expected':6})
 def test_02_challenge(self):
  type(self).req=ep.challenge(self.data,self.trust,self.surface,{'a':3,'b':4,'expected':12})
  self.assertEqual('CHALLENGED',self.req['status'])
  with mounted() as api:
   value=ep.gated_evaluate(self.data,self.trust,'3 とけあわせる 4',lambda:api['bridge'].evaluate(api,self.data,'3 とけあわせる 4'))
  self.assertEqual('OPEN',value['status'])
 def test_03_no_external(self):
  with self.assertRaises(ValueError):ep.expected_receipts(self.data,self.trust,self.surface)
 def test_04_wrong_observer_and_replay(self):
  q=self.req['query'];req=self.req
  payload={'schema':'tukuyo.v943.observation/1','challenge_sha256':req['challenge_sha256'],'query_sha256':req['query_sha256'],'a':q['a'],'b':q['b'],'observed':q['predictions']['MUL'],'individual_id':req['individual_id']}
  self.observation=ep.sign(self.keys['observer'],payload)
  p=self.work/'obs.json';p.write_bytes(ep.canon(self.observation))
  bad=self.work/'bad_obs.json';bad.write_bytes(ep.canon(ep.sign(self.keys['evaluator'],payload)))
  with self.assertRaises(ValueError):ep.observation(self.data,self.trust,self.surface,bad)
  ep.observation(self.data,self.trust,self.surface,p)
  with self.assertRaises(ValueError):ep.observation(self.data,self.trust,self.surface,p)
 def test_05_evaluation_separation(self):
  expected=ep.expected_receipts(self.data,self.trust,self.surface)
  self.assertEqual(1,len(expected));self.assertEqual('MUL',expected[0]['new_operator'])
  type(self).eval=ep.sign(self.keys['evaluator'],expected[0]);type(self).ev_file=self.work/'eval.json';self.ev_file.write_bytes(ep.canon(self.eval))
  bad=self.work/'eval_bad.json';bad.write_bytes(ep.canon(ep.sign(self.keys['observer'],expected[0])))
  ap={'schema':'tukuyo.v943.promotion_authority/1','challenge_sha256':expected[0]['challenge_sha256'],
      'observation_sha256':expected[0]['observation_sha256'],'evaluator_receipt_sha256':ep.objsha(self.eval),
      'new_operator':'MUL','individual_id':expected[0]['individual_id']}
  type(self).approval=ep.sign(self.keys['authority'],ap);type(self).ap_file=self.work/'approve.json';self.ap_file.write_bytes(ep.canon(self.approval))
  with self.assertRaises(ValueError):ep.revise(self.data,self.trust,self.surface,bad,self.ap_file)
 def test_06_revision(self):
  r=ep.revise(self.data,self.trust,self.surface,self.ev_file,self.ap_file);self.assertEqual('REVISED_BOUNDED',r['status'])
  with mounted() as api:
   before=api['bridge'].evaluate(api,self.data,'3 とけあわせる 4')
   after=ep.gated_evaluate(self.data,self.trust,'3 とけあわせる 4',lambda:before)
  self.assertEqual('OPEN',before['status']);self.assertEqual(12,after['answer']);self.assertEqual('REVISED_BOUNDED',ep.status(self.data,self.trust)['surfaces'][self.surface]['status'])
  beyond=ep.gated_evaluate(self.data,self.trust,'2 とけあわせる 3',lambda: {'status':'RESOLVED','answer':5})
  self.assertEqual('OPEN',beyond['status'])
 def test_07_restart(self):
  res=ep.audit(self.data,self.trust);self.assertEqual(4,res['events']);self.assertTrue(res['external_roles_verified'])
 def test_08_objects_tampering(self):
  root=ep.roots(self.data);target=next(root.joinpath('objects').glob('*.json'))
  original=target.read_bytes();target.write_bytes(b'{}\n')
  with self.assertRaises(ValueError):ep.audit(self.data,self.trust)
  target.write_bytes(original);ep.audit(self.data,self.trust)
 def test_09_event_deletion(self):
  root=ep.roots(self.data);p=root/'events/000000000002.json';other=p.with_suffix('.off');p.rename(other)
  with self.assertRaises(ValueError):ep.audit(self.data,self.trust)
  other.rename(p);ep.audit(self.data,self.trust)
 def test_10_key_swap(self):
  original=(self.trust/'authority.pub').read_bytes();(self.trust/'authority.pub').write_text(ep.public(Ed25519PrivateKey.generate()))
  with self.assertRaises(ValueError):ep.audit(self.data,self.trust)
  (self.trust/'authority.pub').write_bytes(original);ep.audit(self.data,self.trust)
 def test_11_native_binding(self):
  root=ep.roots(self.data);e=root/'events/000000000001.json';raw=e.read_bytes();v=json.loads(raw);v['payload']['body']['individual_id']='ANOTHER';e.write_bytes(ep.canon(v))
  with self.assertRaises(ValueError):ep.audit(self.data,self.trust)
  e.write_bytes(raw);ep.audit(self.data,self.trust)
 def test_12_no_second_promotion(self):
  with self.assertRaises(ValueError):ep.revise(self.data,self.trust,self.surface,self.ev_file,self.ap_file)

 def test_13_orphan_objects_fail_closed(self):
  d=ep.roots(self.data)/'objects';p=d/('f'*64+'.json');p.write_text('null')
  with self.assertRaisesRegex(ValueError,'OBJECT_SET_MISMATCH'):ep.audit(self.data,self.trust)
  p.unlink();ep.audit(self.data,self.trust)
 def test_14_zero_hash_event_forgery(self):
  p=ep.roots(self.data)/'events/000000000003.json';before=p.read_bytes();x=json.loads(before);x['payload']['prev_sha256']='0'*64;p.write_bytes(ep.canon(x))
  with self.assertRaises(ValueError):ep.audit(self.data,self.trust)
  p.write_bytes(before);ep.audit(self.data,self.trust)
 def test_15_same_authority_role_key_rejected(self):
  p=self.trust/'authority.pub';old=p.read_bytes();p.write_bytes((self.trust/'evaluator.pub').read_bytes())
  with self.assertRaisesRegex(ValueError,'TRUST_ROLES_NOT_INDEPENDENT'):ep.audit(self.data,self.trust)
  p.write_bytes(old);ep.audit(self.data,self.trust)
 def test_16_missing_epistemic_state_with_external_pin(self):
  import subprocess,os
  root=ep.roots(self.data);hidden=root.with_name('epistemic_removed_for_test');root.rename(hidden)
  try:
   runner=Path(__file__).resolve().parents[1]/'run_tukuyo.py'
   p=subprocess.run([sys.executable,'-B',str(runner),'--data',str(self.data),'--ep-trust-dir',str(self.trust),'eval','3 とけあわせる 4'],
                    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},text=True,capture_output=True)
   self.assertNotEqual(0,p.returncode);self.assertIn('EP_STATE_MISSING_WITH_EXTERNAL_PIN',p.stdout)
  finally:hidden.rename(root)
  ep.audit(self.data,self.trust)

if __name__=='__main__':unittest.main()
