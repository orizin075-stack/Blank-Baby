import subprocess,sys,tempfile,pathlib,json
src="def choose(m):\n    while True:\n        pass\n"
with tempfile.NamedTemporaryFile('w',suffix='.py',delete=False) as f:f.write(src);p=f.name
try:
 try:
  subprocess.run([sys.executable,str(pathlib.Path(__file__).with_name('candidate_worker.py')),p,'{}'],timeout=.25,capture_output=True,text=True)
  out={'ok':False,'reason':'NOT_KILLED'}
 except subprocess.TimeoutExpired: out={'ok':True,'reason':'TIMEOUT_KILLED'}
finally:pathlib.Path(p).unlink(missing_ok=True)
print(json.dumps(out));raise SystemExit(0 if out['ok'] else 1)
