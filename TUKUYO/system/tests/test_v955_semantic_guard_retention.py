from pathlib import Path
import json,subprocess,sys,tempfile,unittest,copy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_v955 import semantic_guard as sg
from tukuyo_v955.retention import demo,retention_gate
from tukuyo_v950.improver import config0
from tukuyo_v955.bootstrap import mounted
class TestV955(unittest.TestCase):
 def test_01_old_tautology_reproduced_and_hardened_blocks(self):
  with mounted() as api:
   s=api['organism'].s838
   original=s.OPS['ADD']
   try:
    s.OPS['ADD']=s.OPS['SUB']
    # Legacy D6 guard compares the mutated operator to itself, so it would pass.
    self.assertTrue(all(s.OPS[op](a,b)==s.OPS[s.BUILTINS[surf]](a,b) for surf,op in s.BUILTINS.items() for a,b in [(-3,2),(0,5),(2,3),(7,-2)]))
    self.assertFalse(s._regression({'promotions':{}},'newcap','ADD'))
    self.assertFalse(sg.check_builtin_semantics(s)['ok'])
   finally:s.OPS['ADD']=original;sg.install(s)
 def test_02_guard_is_installed_on_mount(self):
  with mounted() as api:
   s=api['organism'].s838;self.assertTrue(sg.installed(s));self.assertTrue(sg.check_builtin_semantics(s)['ok'])
 def test_03_signed_migration_and_restart(self):
  td=Path(tempfile.mkdtemp());data=td/'data';rec=json.loads((ROOT/'META/V955_SEMANTIC_MIGRATION_RECEIPT.json').read_text());trust=td/'migration.pub';trust.write_text(rec['public_key']+'\n')
  with mounted() as api:
   api['bridge'].init(api,data,'v955-test');r=sg.migrate(data,api,trust);self.assertTrue(r['ok']);self.assertTrue(sg.audit_migration(data,api,trust)['ok'])
  with mounted() as api:self.assertTrue(sg.audit_migration(data,api,trust)['ok'])
 def test_04_wrong_migration_key_blocked(self):
  td=Path(tempfile.mkdtemp());data=td/'data';bad=td/'bad.txt';bad.write_text('A'*44+'\n')
  with mounted() as api:
   api['bridge'].init(api,data,'v955-test2')
   with self.assertRaises(ValueError):sg.migrate(data,api,bad)
 def test_05_migration_wrong_individual_blocked(self):
  td=Path(tempfile.mkdtemp());data=td/'data';rec=json.loads((ROOT/'META/V955_SEMANTIC_MIGRATION_RECEIPT.json').read_text());trust=td/'migration.pub';trust.write_text(rec['public_key']+'\n')
  with mounted() as api:
   api['bridge'].init(api,data,'v955-test3');sg.migrate(data,api,trust);p=data/'semantic_guard_v955/MIGRATION_STATE.json';x=json.loads(p.read_text());x['individual_id']='evil';p.write_text(json.dumps(x))
   with self.assertRaises(ValueError):sg.audit_migration(data,api,trust)
 def test_06_retention_rejects_minmax_deletion(self):
  x=demo()['remove_minmax'];self.assertFalse(x['promote']);self.assertFalse(x['no_capability_regression']);self.assertTrue(any(z['family'] in ('max','min') for z in x['regressions']))
 def test_07_retention_can_accept_safe_redundancy_removal(self):
  x=demo()['remove_unary'];self.assertTrue(x['no_capability_regression']);self.assertTrue(x['candidate']['all_solved'])
 def test_08_guard_has_no_assert_dependency(self):
  src=(ROOT/'src/tukuyo_v955/semantic_guard.py').read_text();self.assertNotIn('assert ',src)
 def test_09_cli_guard_status(self):
  td=Path(tempfile.mkdtemp());data=td/'data';p=subprocess.run([sys.executable,'-B',str(ROOT/'run_tukuyo.py'),'--data',str(data),'init'],capture_output=True,text=True);self.assertEqual(0,p.returncode,p.stdout+p.stderr)
  p=subprocess.run([sys.executable,'-O','-B',str(ROOT/'run_tukuyo.py'),'--data',str(data),'semantic-guard-status'],capture_output=True,text=True);self.assertEqual(0,p.returncode,p.stdout+p.stderr);self.assertTrue(json.loads(p.stdout)['builtin_spec']['ok'])
if __name__=='__main__':unittest.main()
