import base64,json,secrets,sys,tempfile,unittest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_v956.blind_gap import *
def make_suite(name,fn,n=24):
 cases=[]
 for i in range(n):
  a=i-12;b=((i*7+5)%19)-9;cases.append({'a':a,'b':b,'expected':fn(a,b)})
 return {'schema':SU,'suite_id':name,'cases':cases}
def fixture(suite):
 td=Path(tempfile.mkdtemp());priv=Ed25519PrivateKey.generate();pub=base64.b64encode(priv.public_key().public_bytes_raw()).decode();trust=td/'pub';trust.write_text(pub);salt=secrets.token_hex(32);pre={'suite':suite,'salt':salt};pay={'schema':SC,'suite_id':suite['suite_id'],'case_count':len(suite['cases']),'commitment_sha256':h(canon(pre))};c={'payload':pay,'public_key':pub,'signature':base64.b64encode(priv.sign(canon(pay))).decode()};r={'schema':RS,'suite':suite,'salt':salt};return td,trust,c,r
class V956(unittest.TestCase):
 def test_01_committed_in_class_resolves(self):
  td,t,c,r=fixture(make_suite('inclass',lambda a,b:a+b));x=classify_committed(c,r,t);self.assertEqual('RESOLVED_IN_CLASS',x['classification']['state']);self.assertEqual('ADD',x['classification']['best_operator'])
 def test_02_committed_out_of_class_is_representation_gap(self):
  td,t,c,r=fixture(make_suite('floor3',lambda a,b:a//3+b));x=classify_committed(c,r,t);self.assertEqual('REPRESENTATION_INSUFFICIENT',x['classification']['state']);self.assertGreater(x['classification']['best_wrong'],0)
 def test_03_tampered_reveal_blocked(self):
  td,t,c,r=fixture(make_suite('tamper',lambda a,b:a+b));r['suite']['cases'][0]['expected']+=1
  with self.assertRaisesRegex(ValueError,'PREIMAGE'):classify_committed(c,r,t)
 def test_04_wrong_authority_blocked(self):
  td,t,c,r=fixture(make_suite('key',lambda a,b:a+b));bad=td/'bad';bad.write_text(base64.b64encode(Ed25519PrivateKey.generate().public_key().public_bytes_raw()).decode())
  with self.assertRaisesRegex(ValueError,'TRUST_ROOT'):classify_committed(c,r,bad)
 def test_05_low_support_stays_data_insufficient(self):
  td,t,c,r=fixture(make_suite('small',lambda a,b:a//3+b,6));x=classify_committed(c,r,t);self.assertEqual('DATA_INSUFFICIENT',x['classification']['state'])
 def test_06_deliberately_incomplete_budget_is_search_insufficient(self):
  td,t,c,r=fixture(make_suite('budget',lambda a,b:a//3+b));x=classify_committed(c,r,t,budget=2);self.assertEqual('SEARCH_INSUFFICIENT',x['classification']['state'])
 def test_07_commitment_cannot_be_reused_for_other_suite(self):
  td,t,c,r=fixture(make_suite('one',lambda a,b:a+b));other=make_suite('two',lambda a,b:a*b);r['suite']=other
  with self.assertRaises(ValueError):classify_committed(c,r,t)
if __name__=='__main__':unittest.main()
