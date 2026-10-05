import subprocess,sys,json,pathlib,os
r=pathlib.Path(__file__).resolve().parent;env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1';q=subprocess.run([sys.executable,'-m','pytest','-q','-p','no:cacheprovider',str(r/'tests')],capture_output=True,text=True,env=env);print(json.dumps({'ok':q.returncode==0,'pytest':q.stdout}));raise SystemExit(q.returncode)
