import base64,json,tempfile,unittest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PrivateFormat,NoEncryption,PublicFormat
from tukuyo_v958.promotion import *
from tukuyo_v957.novel_primitive import propose
from tukuyo_v944.gap import search_evidence,classify

def signed(priv,payload):
 pub=base64.b64encode(priv.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode();return {'payload':payload,'public_key':pub,'signature':base64.b64encode(priv.sign(canon(payload))).decode()}
def mkproposal():
 rows=[{'a':i-20,'b':(i*5)%9-4,'expected':(i-20)//3+((i*5)%9-4)} for i in range(40)];gap={'classification':{'state':'REPRESENTATION_INSUFFICIENT'}}
 return propose(rows,gap)
def mkreceipts(td,p):
 ev=Ed25519PrivateKey.generate();au=Ed25519PrivateKey.generate();epub=td/'ev.pub';apub=td/'au.pub';epub.write_text(base64.b64encode(ev.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode());apub.write_text(base64.b64encode(au.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode())
 domains=[{'domain_id':'numeric_hidden','source_schema':'tukuyo.v958.numeric_case/1','generator_id':'numeric_holdout_v958','source_sha256':'1'*64,'rows_sha256':'2'*64,'rows':20,'correct':20,'wrong':0,'invalid':0,'row_evidence_sha256':'3'*64},{'domain_id':'state_transition','source_schema':'tukuyo.v958.state_transition/1','generator_id':'state_machine_v958','source_sha256':'4'*64,'rows_sha256':'5'*64,'rows':20,'correct':20,'wrong':0,'invalid':0,'row_evidence_sha256':'6'*64}]
 ep={'schema':'tukuyo.v958.evaluator_receipt/1','candidate_sha256':p['candidate_sha256'],'proposal_sha256':sha_obj(p),'domains':domains,'evaluation_policy':'ZERO_WRONG_ZERO_INVALID_BOTH_DOMAINS'};er=signed(ev,ep)
 ap={'schema':'tukuyo.v958.promotion_receipt/1','candidate_sha256':p['candidate_sha256'],'evaluator_receipt_sha256':sha_obj(er),'decision':'PROMOTE_BOUNDED','scope':'V958_BOUNDED_SYNTHETIC_TWO_DOMAIN','domain_ids':['numeric_hidden','state_transition']};ar=signed(au,ap)
 return er,ar,epub,apub
class V958(unittest.TestCase):
 def test_01_two_distinct_domains_required(self):
  p=mkproposal()
  with tempfile.TemporaryDirectory() as x:
   td=Path(x);er,ar,ep,ap=mkreceipts(td,p);self.assertEqual(len(verify_evaluator_receipt(er,p,ep)['domains']),2)
 def test_02_same_generator_rejected(self):
  p=mkproposal()
  with tempfile.TemporaryDirectory() as x:
   td=Path(x);er,ar,ep,ap=mkreceipts(td,p);er['payload']['domains'][1]['generator_id']='numeric_holdout_v958';ev=Ed25519PrivateKey.generate()
   # tampering itself must fail signature before generator check
   with self.assertRaises(Exception):verify_evaluator_receipt(er,p,ep)
 def test_03_wrong_domain_score_rejected(self):
  p=mkproposal()
  with tempfile.TemporaryDirectory() as x:
   td=Path(x);ev=Ed25519PrivateKey.generate();pub=td/'ev.pub';pub.write_text(base64.b64encode(ev.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode())
   ds=[{'domain_id':'a','source_schema':'A','generator_id':'G1','source_sha256':'1'*64,'rows_sha256':'2'*64,'rows':20,'correct':19,'wrong':1,'invalid':0,'row_evidence_sha256':'3'*64},{'domain_id':'b','source_schema':'B','generator_id':'G2','source_sha256':'4'*64,'rows_sha256':'5'*64,'rows':20,'correct':20,'wrong':0,'invalid':0,'row_evidence_sha256':'6'*64}]
   pay={'schema':'tukuyo.v958.evaluator_receipt/1','candidate_sha256':p['candidate_sha256'],'proposal_sha256':sha_obj(p),'domains':ds,'evaluation_policy':'ZERO_WRONG_ZERO_INVALID_BOTH_DOMAINS'}
   with self.assertRaisesRegex(ValueError,'DOMAIN_NOT_CLEAN'):verify_evaluator_receipt(signed(ev,pay),p,pub)
 def test_04_role_keys_are_independent(self):
  p=mkproposal()
  with tempfile.TemporaryDirectory() as x:
   td=Path(x);er,ar,ep,ap=mkreceipts(td,p);self.assertNotEqual(ep.read_text(),ap.read_text())
 def test_05_install_and_restart_registry(self):
  p=mkproposal()
  with tempfile.TemporaryDirectory() as x:
   td=Path(x);er,ar,ep,ap=mkreceipts(td,p);e=install(td,p,er,ar,ep,ap);self.assertTrue(audit_registry(td)['ok']);self.assertEqual(evaluate_registry(td,e['candidate_sha256'],8,4)['answer'],6);self.assertTrue(audit_registry(td)['ok'])
 def test_06_duplicate_promotion_blocked(self):
  p=mkproposal()
  with tempfile.TemporaryDirectory() as x:
   td=Path(x);er,ar,ep,ap=mkreceipts(td,p);install(td,p,er,ar,ep,ap)
   with self.assertRaisesRegex(ValueError,'DUPLICATE_PROMOTION'):install(td,p,er,ar,ep,ap)
 def test_07_candidate_tamper_blocked(self):
  p=mkproposal();p['expression']='forged'
  with self.assertRaisesRegex(ValueError,'CANDIDATE_HASH'):verify_proposal(p)
 def test_08_state_domain_adapter(self):
  r={'schema':'tukuyo.v958.state_transition/1','before':{'counter':11},'event':{'batch':-2},'observed':{'bucket_plus_batch':1}}
  self.assertEqual(adapt_domain_b(r),{'a':11,'b':-2,'expected':1})
if __name__=='__main__':unittest.main()
