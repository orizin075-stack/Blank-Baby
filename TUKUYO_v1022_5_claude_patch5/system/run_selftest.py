from pathlib import Path
import importlib.util,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parent
ENV={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT/'src')}
force_stdlib=os.environ.get('TUKUYO_SELFTEST_FORCE_STDLIB')=='1'
if not force_stdlib and importlib.util.find_spec('pytest') is not None:
    p=subprocess.run([sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider','tests'],cwd=ROOT,env=ENV)
    raise SystemExit(p.returncode)
# Dependency-free fallback: each file is isolated in a fresh process and both unittest.TestCase
# tests and top-level zero-argument test_* functions are executed.
runner=ROOT/'tools'/'stdlib_test_runner.py';summary={'runner':'stdlib_fallback','files':[],'total':0,'passed':0,'failed':0,'ok':True}
for f in sorted((ROOT/'tests').glob('test*.py')):
    p=subprocess.run([sys.executable,'-B',str(runner),str(f)],cwd=ROOT,env=ENV,text=True,capture_output=True)
    try:r=json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:r={'ok':False,'file':f.name,'total':0,'passed':0,'failed':1,'failures':[{'test':'RUNNER','traceback':p.stdout+p.stderr}]}
    summary['files'].append({k:r.get(k) for k in ('file','total','passed','failed','skipped','ok')});summary['total']+=int(r.get('total',0));summary['passed']+=int(r.get('passed',0));summary['failed']+=int(r.get('failed',0));summary['ok']=summary['ok'] and bool(r.get('ok')) and p.returncode==0
    if not r.get('ok'):
        print(json.dumps(r,ensure_ascii=False,indent=2),file=sys.stderr)
print(json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2))
raise SystemExit(0 if summary['ok'] else 1)
