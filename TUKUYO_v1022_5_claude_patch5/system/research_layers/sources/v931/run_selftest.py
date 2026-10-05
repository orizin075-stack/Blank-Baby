import subprocess,sys,json,pathlib
r1=subprocess.run([sys.executable,'-m','pytest','-q','tests/test_repair.py'],capture_output=True,text=True)
r2=subprocess.run([sys.executable,'tools/test_timeout_kill.py'],capture_output=True,text=True)
out={'ok':r1.returncode==0 and r2.returncode==0,'pytest':r1.stdout.strip(),'timeout':r2.stdout.strip()};print(json.dumps(out,sort_keys=True));raise SystemExit(0 if out['ok'] else 1)
