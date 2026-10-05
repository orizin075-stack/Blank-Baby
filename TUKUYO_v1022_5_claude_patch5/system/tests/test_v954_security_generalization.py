import json,os,subprocess,sys,tempfile,unittest,base64
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from tukuyo_v954 import provenance as pv
from tukuyo_v954.generalization import propose_generalizing,authority_evaluate
from tukuyo_v950.improver import config0
class V954(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.w=Path(self.t.name);self.data=self.w/'live';self.trust=self.w/'trust';self.trust.mkdir();self.k=Ed25519PrivateKey.generate();(self.trust/'capability_authority.pub').write_text(pv.pub(self.k))
  base=[sys.executable,'-B',str(ROOT/'run_tukuyo.py'),'--data',str(self.data)]
  def cli(*a,trust=False):
   c=base.copy();
   if trust:c += ['--cap-trust-dir',str(self.trust)]
   c+=list(a);r=subprocess.run(c,capture_output=True,text=True,timeout=50,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'});return r,json.loads(r.stdout)
  self.cli=cli;self.assertEqual(cli('init')[0].returncode,0);self.assertEqual(cli('teach',str(ROOT/'examples/SEMANTIC_TEACH_SAMPLE.json'),'--apply')[0].returncode,0)
 def tearDown(self):self.t.cleanup()
 def _seal(self):
  req=self.w/'req.json';r,x=self.cli('cap-request','とけあわせる','--out',str(req));self.assertEqual(r.returncode,0,r.stdout+r.stderr);q=pv.load(req);receipt=pv.sign(self.k,{'schema':'tukuyo.v954.capability_authority_receipt/1','request_sha256':pv.sha_obj(q),'individual_id':q['individual_id'],'surface':q['surface'],'operator':q['operator'],'promotion_sha256':q['promotion_sha256']});rf=self.w/'rec.json';rf.write_bytes(pv.canon(receipt)+b'\n');r,x=self.cli('cap-install',str(req),str(rf),trust=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
 def test_01_unsealed_legacy_capability_cannot_answer(self):
  r,x=self.cli('eval','6 とけあわせる 7');self.assertEqual('OPEN',x['status']);self.assertEqual('EXTERNAL_CAPABILITY_SEAL_REQUIRED',x['reason'])
 def test_02_external_seal_enables_answer(self):
  self._seal();r,x=self.cli('eval','6 とけあわせる 7',trust=True);self.assertEqual(42 if False else 13,x['answer']);self.assertEqual('EXTERNALLY_SEALED_V954_PROVENANCE',x['authority'])
 def test_03_zero_hash_forgery_blocked(self):
  req=next((self.data/'capability_provenance/requests').glob('*.json'));q=pv.load(req);q['object_refs']['proposal_sha256']='0'*64
  with self.assertRaises(ValueError):pv.verify_request(self.data,q)
 def test_04_missing_object_blocked(self):
  req=next((self.data/'capability_provenance/requests').glob('*.json'));q=pv.load(req);h=q['object_refs']['holdout_sha256'];p=self.data/'capability_provenance/objects'/(h+'.json');b=p.read_bytes();p.unlink()
  try:
   with self.assertRaises(ValueError):pv.verify_request(self.data,q)
  finally:p.write_bytes(b)
 def test_05_wrong_individual_blocked(self):
  q=pv.load(next((self.data/'capability_provenance/requests').glob('*.json')));q['individual_id']='FORGED'
  with self.assertRaises(ValueError):pv.verify_request(self.data,q)
 def test_06_mixed_unseen_rejects_minmax_deletion(self):
  p=config0();c=dict(p);c['binops']=tuple(o for o in p['binops'] if o not in ('MAX','MIN'));a=tuple((i-6,((i*7+2)%11)-5) for i in range(18));b=tuple((i-11,((i*11+5)%19)-9) for i in range(26));e=authority_evaluate(p,c,a,b);self.assertFalse(e['promote']);self.assertFalse(e['no_family_regression'])
 def test_07_generalization_gate_has_failure_and_success_branches(self):
  x=propose_generalizing();self.assertTrue(any(not c['evaluation']['promote'] for c in x['candidates']));self.assertTrue(any(c['evaluation']['promote'] for c in x['candidates']))
 def test_08_non_deletion_edits_are_real_promotion_candidates(self):
  x=propose_generalizing();self.assertTrue(x['promoted']);promoted={r['edit'] for r in x['candidates'] if r['evaluation']['promote']};self.assertTrue(promoted & {'priority_mul_add_sub','priority_piecewise_first','priority_small_constants','priority_small_constants'})
 def test_09_v954_status_preserved_and_top_status_advances(self):
  old=json.loads((ROOT/'STATUS_v954.json').read_text());self.assertEqual('v954',old['version']);self.assertFalse(old['general_l6_established'])
  cur=json.loads((ROOT/'STATUS.json').read_text());self.assertTrue(cur['version'].startswith('v'));self.assertGreaterEqual(int(cur['version'][1:]),955);self.assertFalse(cur['general_l6_established'])
 def test_10_optimized_python_still_enforces_codegen_checks(self):
  code="import sys;sys.path.insert(0,%r);from research.tukuyo_research_v936.codegen import verify_generated_source;verify_generated_source('import os\\ndef choose(m):\\n return 1\\n',{})" % str(ROOT/'src')
  r=subprocess.run([sys.executable,'-O','-B','-c',code],capture_output=True,text=True);self.assertNotEqual(r.returncode,0)
if __name__=='__main__':unittest.main()
