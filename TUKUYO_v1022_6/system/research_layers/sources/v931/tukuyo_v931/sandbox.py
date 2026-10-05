import subprocess,sys,json,tempfile,pathlib
from .search import safe_source
WORKER=pathlib.Path(__file__).resolve().parents[1]/'tools'/'candidate_worker.py'
def run_candidate(src,m,timeout_s=0.5):
    if not safe_source(src): return {'ok':False,'reason':'AST_REJECT'}
    with tempfile.NamedTemporaryFile('w',suffix='.py',delete=False) as f: f.write(src); p=f.name
    try:
        r=subprocess.run([sys.executable,str(WORKER),p,json.dumps(m)],capture_output=True,text=True,timeout=timeout_s)
        if r.returncode!=0:return {'ok':False,'reason':'PROCESS_FAIL'}
        return {'ok':True,**json.loads(r.stdout)}
    except subprocess.TimeoutExpired:return {'ok':False,'reason':'TIMEOUT'}
    finally:pathlib.Path(p).unlink(missing_ok=True)
