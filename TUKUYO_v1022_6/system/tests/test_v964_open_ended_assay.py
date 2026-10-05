import unittest
from tukuyo_v964.assay import run_assay
class V964(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.r=run_assay()
 def test_01_assay_pass(self): self.assertTrue(self.r['ok'])
 def test_02_novelty_monotonic(self): self.assertEqual([w['unique_primitive_count'] for w in self.r['waves']],[1,2,3,4])
 def test_03_hidden_zero(self): self.assertTrue(all(w['hidden_wrong']==0 for w in self.r['waves']))
 def test_04_retention(self): self.assertTrue(all(all(x['wrong']==0 for x in w['retention']) for w in self.r['waves']))
 def test_05_no_replay_inflation(self): self.assertFalse(self.r['replay_novelty_inflation'])
 def test_06_ceiling_detected(self): self.assertEqual(self.r['ceiling']['status'],'META_GRAMMAR_CEILING_DETECTED')
 def test_07_claim_boundary(self): self.assertFalse(self.r['open_ended_evolution_established']);self.assertTrue(self.r['finite_meta_grammar']);self.assertFalse(self.r['general_l6'])
if __name__=='__main__': unittest.main()
