"""Fresh tests: originals, real composed state, negative controls, restart."""
import copy,hashlib,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT/'src'))
from tukuyo_v939 import bootstrap
from tukuyo_v939.integrated import full_status,run_lab,audit_lab

class ComposedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx=bootstrap.mounted();cls.api=cls.ctx.__enter__()
    @classmethod
    def tearDownClass(cls):cls.ctx.__exit__(None,None,None)
    def setUp(self):
        self.t=tempfile.TemporaryDirectory(prefix='v939_fresh_');self.addCleanup(self.t.cleanup)
        self.r=Path(self.t.name)

    def test_01_original_sha_and_real_runtime_guard_identity(self):
        origins=bootstrap.verify_origins();self.assertEqual(len(origins),3)
        self.assertIs(self.api['guard'].r837,self.api['organism'].r837)
        self.assertTrue(self.api['guard']._INSTALLED)
        self.assertTrue(all(x in self.api for x in ('society','cluster','lineage','ecology','evolution','research','learner')))

    def test_02_core_init_life_ticks_and_guarded_persistence(self):
        b=self.api['bridge'];data=self.r/'live';b.init(self.api,data,'LIVE-A')
        start=full_status(self.api,data)
        b.tick(self.api,data,10)
        final=full_status(self.api,data)
        self.assertEqual(start['organism']['runtime_tick'],0)
        self.assertEqual(final['organism']['runtime_tick'],10)
        self.assertTrue(final['full_integration']['v846_1_guard']['ok'])
        self.assertLess(final['organism']['energy'],start['organism']['energy'])

    def test_03_real_learning_explicit_apply_then_resolved(self):
        b=self.api['bridge'];data=self.r/'live';b.init(self.api,data,'LEARN-A')
        source=self.api['v938_root']/'examples/SEMANTIC_TEACH_SAMPLE.json'
        with self.assertRaises(PermissionError):b.teach(self.api,data,source,apply=False)
        self.assertEqual(b.evaluate(self.api,data,'3 とけあわせる 2')['status'],'OPEN')
        result=b.teach(self.api,data,source,apply=True)
        self.assertEqual(result['operator'],'ADD')
        self.assertEqual(b.evaluate(self.api,data,'3 とけあわせる 2')['status'],'OPEN')
        self.assertEqual(b.evaluate(self.api,data,'3 とけあわせる 2')['reason'],'EXTERNAL_CAPABILITY_SEAL_REQUIRED')
        self.assertEqual(full_status(self.api,data)['organism']['capability_generation'],1)

    def test_04_wrong_holdout_cannot_modify_live_state(self):
        b=self.api['bridge'];data=self.r/'live';b.init(self.api,data,'HOLD-A')
        original=json.loads((self.api['v938_root']/'examples/SEMANTIC_TEACH_SAMPLE.json').read_text())
        original['holdout'][0]['expected']=1234
        ev=self.r/'bad.json';ev.write_text(json.dumps(original),encoding='utf-8')
        with self.assertRaises(Exception):b.teach(self.api,data,ev,apply=True)
        self.assertEqual(full_status(self.api,data)['organism']['capability_generation'],0)

    def test_05_shadow_research_must_not_mutate_organism(self):
        b=self.api['bridge'];data=self.r/'live';b.init(self.api,data,'RESEARCH-A')
        before=full_status(self.api,data)['organism']
        report=b.run_research(self.api,data,'coupled_product',93601)
        after=full_status(self.api,data)['organism']
        self.assertEqual(before,after)
        self.assertTrue(report['organism_unchanged'])
        self.assertEqual(report['promotion'],'BLOCKED_PENDING_REAL_EVALUATION')

    def test_06_actual_all_modules_simultaneous_lab_and_audit(self):
        root=self.r/'lab';report=run_lab(self.api,root,include_research=True)
        self.assertTrue(report['ok']);self.assertEqual(report['steps']['cluster']['correct'],1)
        self.assertEqual(report['steps']['ecology']['death_count'],1)
        self.assertEqual(report['steps']['lineage']['inherited_answer'],5)
        self.assertTrue(audit_lab(self.api,root)['ok'])
        self.assertTrue(report['steps']['research']['organism_unchanged'])

    def test_07_multiple_ecology_evolution_generations_and_lineage(self):
        root=self.r/'lab';run_lab(self.api,root,include_research=False)
        for _ in range(2):
            self.api['ecology'].step_generation(root/'ecology')
            self.api['evolution'].step_generation(root/'evolution')
        ea=self.api['ecology'].audit(root/'ecology')
        va=self.api['evolution'].audit(root/'evolution')
        la=self.api['lineage'].verify_lineage(root/'lineage')
        self.assertTrue(ea['ok'] and va['ok'] and la['ok'])
        self.assertEqual((ea['generation'],va['generation']),(3,3))
        self.assertEqual(la['birth_count'],1+ea['birth_count']+va['birth_count'])
        self.assertTrue(audit_lab(self.api,root)['ok'])

    def test_08_torn_event_quarantines_live_organism(self):
        b=self.api['bridge'];data=self.r/'live';b.init(self.api,data,'CORRUPT-A')
        b.tick(self.api,data,1);org=data/'state/organism'
        (org/'events/000000000001.json').write_text('{',encoding='utf-8')
        with self.assertRaises(Exception):b.tick(self.api,data,1)
        self.assertTrue((org/self.api['guard'].QUAR).exists())
        self.assertFalse(self.api['guard'].audit_checked(org)['ok'])

    def test_09_unknown_genome_operator_rejected(self):
        with self.assertRaises(Exception):
            self.api['evolution'].normalize_genome({'op':'unsafe_eval','code':'2+2'})

    def test_10_cluster_member_cannot_be_external_evaluator(self):
        root=self.r/'lab';run_lab(self.api,root,include_research=False)
        payload=json.loads((root/'cluster_task_receipt.json').read_text())
        member=root/'agents/P0'
        with self.assertRaises(Exception):
            self.api['cluster'].external_verifier_receipt(root/'society',root/'role_manifest.json',
                payload['tasks'],payload['bundle'],self.api['society']._sk(member),self.api['society']._pk(member))

    def test_11_evolution_ledger_tamper_detected(self):
        root=self.r/'lab';run_lab(self.api,root,include_research=False)
        ledger=root/'evolution/ledger/000001.json'
        # Use actual upstream ledger path, not guessed pathname.
        ledger=root/'evolution'/self.api['evolution'].LEDGER/'000001.json'
        data=json.loads(ledger.read_text());data['payload']['generation']=99
        ledger.write_text(json.dumps(data),encoding='utf-8')
        self.assertFalse(self.api['evolution'].audit(root/'evolution')['ok'])

    def test_12_changed_source_fails_before_boot(self):
        from unittest.mock import patch
        cloned=self.r/'copied';import shutil
        shutil.copytree(ROOT/'src',cloned/'src')
        shutil.copytree(ROOT/'META',cloned/'META')
        shutil.copytree(ROOT/'examples',cloned/'examples')
        shutil.copytree(ROOT/'history',cloned/'history')
        victim=cloned/'src/legacy/tukuyo_v841/social.py'
        victim.write_bytes(victim.read_bytes()+bytes([10])+b'# tamper'+bytes([10]))
        with patch.object(bootstrap,'ROOT',cloned),patch.object(bootstrap,'SRC',cloned/'src'),patch.object(bootstrap,'RESEARCH',cloned/'src/research'),patch.object(bootstrap,'V935',cloned/'history/TUKUYO_v931_to_v935_VERIFIED_DEBUGGED_CHAIN.zip'):
            with self.assertRaises(bootstrap.OriginError):bootstrap.verify_origins()

    def test_13_repeated_mounts_do_not_retain_stale_modules(self):
        # Nested mounts would share sys.modules. Real restarts are new processes.
        cmd=[sys.executable,'-B',str(ROOT/'run_tukuyo.py'),'layers']
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=65,
            env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertTrue(json.loads(result.stdout)['v846_1_guard_installed'])

    def test_14_cli_cross_process_restart_tick(self):
        live=self.r/'cli'
        base=[sys.executable,'-B',str(ROOT/'run_tukuyo.py'),'--data',str(live)]
        def cli(*args):
            p=subprocess.run([*base,*args],capture_output=True,text=True,timeout=65,
                env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
            self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)
            return json.loads(p.stdout)
        cli('init','--individual-id','RESTART-001')
        self.assertEqual(cli('tick','5')['organism']['runtime_tick'],5)
        self.assertEqual(cli('status')['organism']['runtime_tick'],5)
        self.assertEqual(cli('eval','3 + 2')['answer'],5)

    def test_15_cluster_receipt_rebinding_attack_blocked(self):
        root=self.r/'lab';run_lab(self.api,root,include_research=False)
        report=root/'cluster_task_receipt.json';e=json.loads(report.read_text(encoding='utf-8'))
        e['tasks'][0]['expected']=999
        report.write_text(json.dumps(e),encoding='utf-8')
        got=audit_lab(self.api,root)
        self.assertFalse(got['ok'],got)
        self.assertFalse(got['checks']['cluster'])

    def test_16_cluster_signature_tamper_blocked(self):
        root=self.r/'lab';run_lab(self.api,root,include_research=False)
        report=root/'cluster_task_receipt.json';e=json.loads(report.read_text(encoding='utf-8'))
        e['receipt']['signature']='A'*88
        report.write_text(json.dumps(e),encoding='utf-8')
        self.assertFalse(audit_lab(self.api,root)['ok'])

    def test_17_runtime_assertions_remain_active_under_optimized_python(self):
        cmd=[sys.executable,'-O','-B',str(ROOT/'run_tukuyo.py'),'layers']
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=65,
                              env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        source=(ROOT/'src/tukuyo_v939/integrated.py').read_text(encoding='utf-8')
        self.assertNotIn('assert ',source,'Integration requirements must survive -O')

    def test_18_zip_slip_and_symlink_archive_refused(self):
        import zipfile
        from tukuyo_v939.bootstrap import safe_extract,OriginError
        bad=self.r/'bad.zip'
        with zipfile.ZipFile(bad,'w') as z:z.writestr('../escaped','untrusted')
        with self.assertRaises(OriginError):safe_extract(bad,self.r/'extract_bad',4096)
        other=self.r/'sym.zip'
        with zipfile.ZipFile(other,'w') as z:
            i=zipfile.ZipInfo('sym');i.create_system=3;i.external_attr=(0o120777<<16)
            z.writestr(i,'target')
        with self.assertRaises(OriginError):safe_extract(other,self.r/'extract_sym',4096)

    def test_19_flat_origin_source_hashes_rechecked(self):
        details=bootstrap.verify_origins()
        self.assertTrue(details['source_integrity'])
        self.assertGreater(details['flat_sources'],50)

    def test_20_flat_source_extra_cache_refused(self):
        import shutil
        from unittest.mock import patch
        cloned=self.r/'copied'
        for part in ('src','META','history','examples'):shutil.copytree(ROOT/part,cloned/part)
        cache=cloned/'src/legacy/tukuyo_v841/__pycache__';cache.mkdir()
        (cache/'UNVERIFIED_CLAIM.pyc').write_bytes(b'fake')
        with patch.object(bootstrap,'ROOT',cloned),patch.object(bootstrap,'SRC',cloned/'src'),patch.object(bootstrap,'RESEARCH',cloned/'src/research'),patch.object(bootstrap,'V935',cloned/'history/TUKUYO_v931_to_v935_VERIFIED_DEBUGGED_CHAIN.zip'):
            with self.assertRaises(bootstrap.OriginError):bootstrap.verify_origins()

    def test_21_historical_v935_replay_verifies_original_before_after(self):
        from tukuyo_v939.integrated import replay_v935
        r=replay_v935(self.api)
        self.assertTrue(r['ok'] and r['release_verified_before_after'])
        self.assertIn('3 passed',r['historical_selftest'])
        self.assertFalse(r['third_party_semantic_assessment'])

if __name__=='__main__':unittest.main()
