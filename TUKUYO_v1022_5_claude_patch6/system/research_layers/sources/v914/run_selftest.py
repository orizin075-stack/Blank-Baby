import json,tempfile,pathlib,subprocess,sys
from tukuyo_v914.patcher import evaluate,BASE_SOURCE
from tukuyo_v914.security import inspect_source
with tempfile.TemporaryDirectory() as d:
 d=pathlib.Path(d); pub=evaluate(BASE_SOURCE,91401,700); sp=d/'summary.json';sp.write_text(json.dumps(pub)); cp=d/'candidate.py'
 a=subprocess.run([sys.executable,'tools/propose_candidate.py',str(sp),str(cp)],capture_output=True,text=True)
 h=subprocess.run([sys.executable,'tools/hidden_evaluator.py',str(cp)],capture_output=True,text=True)
 hr=json.loads(h.stdout);mal=inspect_source(pathlib.Path('evidence/MALICIOUS_SOURCE.py').read_text())
 ok=a.returncode==0 and h.returncode==0 and hr['correct']>evaluate(BASE_SOURCE,91499,700)['correct'] and not mal['ok']
 print(json.dumps({'ok':ok,'hidden_correct':hr.get('correct'),'n':700,'malicious_blocked':not mal['ok'],'processes_separate':True},sort_keys=True));raise SystemExit(0 if ok else 1)
