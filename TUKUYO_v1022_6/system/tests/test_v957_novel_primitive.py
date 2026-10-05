import base64,secrets,sys,tempfile,unittest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_v956.blind_gap import *
from tukuyo_v957.novel_primitive import propose,eval_proposal
def suite(name,fn,n=36):
 return {'schema':SU,'suite_id':name,'cases':[{'a':i-18,'b':((i*11+7)%29)-14,'expected':fn(i-18,((i*11+7)%29)-14)} for i in range(n)]}
def fix(s):
 td=Path(tempfile.mkdtemp());k=Ed25519PrivateKey.generate();pub=base64.b64encode(k.public_key().public_bytes_raw()).decode();t=td/'pub';t.write_text(pub);salt=secrets.token_hex(32);pre={'suite':s,'salt':salt};pay={'schema':SC,'suite_id':s['suite_id'],'case_count':len(s['cases']),'commitment_sha256':h(canon(pre))};c={'payload':pay,'public_key':pub,'signature':base64.b64encode(k.sign(canon(pay))).decode()};r={'schema':RS,'suite':s,'salt':salt};g=classify_committed(c,r,t);return s,g
def make_proposal(s,g):return propose(s['cases'],g)
class V957(unittest.TestCase):
 def test_01_floor_divisor_is_generated_from_meta_grammar(self):
  s,g=fix(suite('fd3',lambda a,b:a//3+b));p=make_proposal(s,g);self.assertEqual(0,p['training_wrong']);self.assertEqual('FLOORDIV_CONST',p['primitive']['kind']);self.assertEqual(3,p['primitive']['parameter']);self.assertTrue(all(eval_proposal(p,r['a'],r['b'])==r['expected'] for r in s['cases']))
 def test_02_modulus_is_generated(self):
  s,g=fix(suite('mod5',lambda a,b:a%5-b));p=make_proposal(s,g);self.assertEqual(0,p['training_wrong']);self.assertEqual('MOD_CONST',p['primitive']['kind']);self.assertEqual(5,p['primitive']['parameter'])
 def test_03_existing_v945_dsl_prevents_false_novelty(self):
  s,g=fix(suite('old-dsl',lambda a,b:a*b+a-b));self.assertEqual('REPRESENTATION_INSUFFICIENT',g['classification']['state'])
  with self.assertRaisesRegex(ValueError,'EXISTING_V945_DSL_ALREADY_SUFFICIENT'):make_proposal(s,g)
 def test_04_schema_contains_semantics_type_and_counterexample_conditions(self):
  s,g=fix(suite('meta',lambda a,b:a//4+b));p=make_proposal(s,g);q=p['primitive'];self.assertIn('semantics',q);self.assertIn('input_type',q);self.assertIn('output_type',q);self.assertTrue(q['counterexample_conditions'])
 def test_05_candidate_hash_tamper_blocked(self):
  s,g=fix(suite('hash',lambda a,b:a//2+b));p=make_proposal(s,g);p['primitive']['parameter']=7
  with self.assertRaisesRegex(ValueError,'CANDIDATE_HASH'):eval_proposal(p,2,3)
 def test_06_non_gap_input_rejected(self):
  s,g=fix(suite('add',lambda a,b:a+b));self.assertEqual('RESOLVED_IN_CLASS',g['classification']['state'])
  with self.assertRaisesRegex(ValueError,'REPRESENTATION_GAP_REQUIRED'):make_proposal(s,g)
if __name__=='__main__':unittest.main()
