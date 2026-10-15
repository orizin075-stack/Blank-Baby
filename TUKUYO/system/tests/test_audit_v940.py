"""Negative controls: a forged but previously accepted lab summary must fail."""
import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from tukuyo_v939.bootstrap import mounted
from tukuyo_v939.integrated import run_lab,audit_lab

class LabClaimControls(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.mount=mounted();cls.api=cls.mount.__enter__()
 @classmethod
 def tearDownClass(cls):cls.mount.__exit__(None,None,None)
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(prefix='v940_');self.addCleanup(self.t.cleanup)
  self.root=Path(self.t.name)/'lab'
  run_lab(self.api,self.root,include_research=False)
  self.assertTrue(audit_lab(self.api,self.root)['ok'])
 def mutate(self,fn):
  p=self.root/'LAB_REPORT.json';r=json.loads(p.read_text());fn(r);p.write_text(json.dumps(r));return audit_lab(self.api,self.root)
 def test_01_forged_organism_count(self):
  r=self.mutate(lambda x:x['steps']['organism'].__setitem__('members',900))
  self.assertFalse(r['ok']);self.assertFalse(r['checks']['report_consistency'])
 def test_02_fake_external_evaluation(self):
  r=self.mutate(lambda x:x.__setitem__('independent_evaluation',True))
  self.assertFalse(r['ok']);self.assertEqual(r['error'],'LAB_SCOPE_OR_SCHEMA_MISMATCH')
 def test_03_fake_evolution_generation(self):
  r=self.mutate(lambda x:x['steps']['evolution'].__setitem__('generation',999))
  self.assertFalse(r['ok']);self.assertFalse(r['checks']['report_consistency'])
 def test_04_fake_research_promotion(self):
  r=self.mutate(lambda x:x['steps'].__setitem__('research',{'promotion':'ACCEPTED','organism_unchanged':True}))
  self.assertFalse(r['ok']);self.assertFalse(r['checks']['report_consistency'])
 def test_05_symlink_report(self):
  p=self.root/'LAB_REPORT.json';raw=p.read_bytes();other=self.root/'copy.json';other.write_bytes(raw);p.unlink();p.symlink_to(other)
  r=audit_lab(self.api,self.root);self.assertFalse(r['ok'])
if __name__=='__main__':unittest.main()
