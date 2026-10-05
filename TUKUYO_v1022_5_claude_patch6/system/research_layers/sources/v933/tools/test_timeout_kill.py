import subprocess,sys,tempfile,pathlib,json
src="def choose(m):\n    while True:\n        pass\n"
with tempfile.NamedTemporaryFile('w',suffix='.py',delete=False) as f:f.write(src);p=f.name
try:
 try:subprocess.run([sys.executable,str(pathlib.Path(__file__).with_name('candidate_worker.py')),p,'{}'],timeout=.25,capture_output=True,text=True);o={'ok':False,'reason':'NOT_KILLED'}
 except subprocess.TimeoutExpired:o={'ok':True,'reason':'TIMEOUT_KILLED'}
finally:pathlib.Path(p).unlink(missing_ok=True)
print(json.dumps(o));raise SystemExit(0 if o['ok'] else 1)
