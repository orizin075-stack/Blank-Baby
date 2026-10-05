import subprocess,sys,json
p=subprocess.run([sys.executable,'tools/check_handoff.py'],capture_output=True,text=True);r=json.loads(p.stdout);ok=p.returncode==0 and r['ready_for_external_inputs'] and not r['external_run_completed'];print(json.dumps({'ok':ok,'external_run_completed':False},sort_keys=True));raise SystemExit(0 if ok else 1)
