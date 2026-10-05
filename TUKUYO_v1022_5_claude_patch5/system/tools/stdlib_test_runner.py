#!/usr/bin/env python3
from __future__ import annotations
import argparse,importlib.util,inspect,json,os,sys,tempfile,traceback,unittest
from pathlib import Path

def load_module(path:Path,root:Path):
    sys.path.insert(0,str(root/'src'));sys.path.insert(0,str(root))
    name='tukuyo_selftest_'+path.stem+'_'+str(abs(hash(str(path))))
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:raise RuntimeError('MODULE_LOAD_SPEC')
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod

def run_file(path:Path):
    root=path.resolve().parents[1];mod=load_module(path.resolve(),root)
    suite=unittest.defaultTestLoader.loadTestsFromModule(mod)
    result=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(suite)
    passed_ut=result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped)
    failed=[]
    for test,txt in result.failures+result.errors:failed.append({'test':str(test),'traceback':txt})
    fn_pass=0;fn_fail=0
    for name,obj in sorted(vars(mod).items()):
        if not name.startswith('test_') or not inspect.isfunction(obj):continue
        params=list(inspect.signature(obj).parameters)
        try:
            if not params:obj()
            elif params==['tmp_path']:
                with tempfile.TemporaryDirectory(prefix='tukuyo-selftest-') as td:obj(Path(td))
            else:continue
            fn_pass+=1
        except Exception:
            fn_fail+=1;failed.append({'test':path.name+'::'+name,'traceback':traceback.format_exc()})
    total=result.testsRun+fn_pass+fn_fail
    return {'ok':not failed,'file':path.name,'total':total,'passed':passed_ut+fn_pass,'failed':len(failed),'skipped':len(result.skipped),'failures':failed}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('test_file',type=Path);a=ap.parse_args();r=run_file(a.test_file);print(json.dumps(r,ensure_ascii=False,sort_keys=True));return 0 if r['ok'] else 1
if __name__=='__main__':raise SystemExit(main())
