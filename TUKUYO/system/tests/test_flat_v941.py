"""v941-specific integration, provenance and registry controls."""
import json,hashlib,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from tukuyo_v939 import bootstrap

class FlatSourceTests(unittest.TestCase):
 def test_source_direct_import_and_one_guard_instance(self):
  with bootstrap.mounted() as api:
   base=(ROOT/'src/legacy').resolve()
   for k in ('organism','social','society','cluster','lineage','ecology','evolution','guard'):
    self.assertTrue(Path(api[k].__file__).resolve().is_relative_to(base),k)
   self.assertIs(api['guard'].r837,api['organism'].r837)
   self.assertEqual(api['research'].__file__,str(ROOT/'src/research/tools/reproduce.py'))

 def test_research_layer_registry_45_original_shas_and_archive_crc(self):
  index=json.loads((ROOT/'RESEARCH_LAYER_INDEX.json').read_text())
  self.assertEqual(index['release_count'],45)
  self.assertEqual(set(x['version'] for x in index['records']),{'v'+str(i) for i in range(891,936)})
  for row in index['records']:
   p=ROOT/row['archive']
   self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),row['sha256'])
   with zipfile.ZipFile(p) as z:self.assertIsNone(z.testzip())
   self.assertGreater(row['files_extracted'],2)

 def test_registry_rejects_unknown_version(self):
  p=subprocess.run([sys.executable,'-B',str(ROOT/'run_tukuyo.py'),'archive-show','v999'],capture_output=True,text=True,timeout=25)
  self.assertNotEqual(p.returncode,0)
  self.assertEqual(json.loads(p.stdout)['error'],'UNKNOWN_VERSION')

 def test_research_archive_listing_is_not_live_promotion(self):
  p=subprocess.run([sys.executable,'-B',str(ROOT/'run_tukuyo.py'),'archive-list'],capture_output=True,text=True,timeout=25)
  self.assertEqual(p.returncode,0,p.stderr)
  x=json.loads(p.stdout)
  self.assertEqual(x['release_count'],45)
  self.assertEqual(x['execution_mode'],'ARCHIVAL_ISOLATED')
  status=json.loads((ROOT/'STATUS.json').read_text())
  self.assertFalse(status['general_l6_established'])
  self.assertFalse(status['historical_signature_rotation_proven'])

 def test_legacy_source_files_do_not_require_runtime_zip_extraction(self):
  self.assertFalse(list((ROOT/'src/legacy').rglob('*.zip')))
  self.assertFalse(list((ROOT/'src/research').rglob('*.zip')))
  p=ROOT/'META/PROVENANCE_SOURCE.json'
  d=json.loads(p.read_text())
  self.assertGreaterEqual(len(d['ancestor_layers']),10)
  self.assertTrue(bootstrap.verify_origins()['source_integrity'])

 def test_restart_retains_learned_semantic_capability(self):
  with tempfile.TemporaryDirectory(prefix='v941_restart_') as tmp:
   base=[sys.executable,'-B',str(ROOT/'run_tukuyo.py'),'--data',str(Path(tmp)/'live')]
   def cmd(*a):
    proc=subprocess.run([*base,*a],capture_output=True,text=True,timeout=30)
    self.assertEqual(proc.returncode,0,proc.stdout+'\n'+proc.stderr)
    return json.loads(proc.stdout)
   cmd('init','--individual-id','V941-PERSISTENCE-CONTROL')
   self.assertEqual(cmd('eval','3 とけあわせる 2')['status'],'OPEN')
   result=cmd('teach',str(ROOT/'examples/SEMANTIC_TEACH_SAMPLE.json'),'--apply')
   self.assertEqual(result['operator'],'ADD')
   self.assertEqual(cmd('eval','3 とけあわせる 2')['status'],'OPEN')
   self.assertEqual(cmd('status')['organism']['capability_generation'],1)

if __name__=='__main__':unittest.main()
