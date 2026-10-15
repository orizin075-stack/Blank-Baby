import json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py'
def run(data,*args,ok=True):
 p=subprocess.run([sys.executable,'-B',str(CLI),'--data',str(data),*map(str,args)],cwd=ROOT,text=True,capture_output=True)
 if ok and p.returncode!=0:raise AssertionError(p.stdout+p.stderr)
 return json.loads(p.stdout)

def test_surface_memory_loss_preserves_deep_tendency():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'data';run(d,'init','--individual-id','SOUL-CONT')
  run(d,'heart-experience','betrayal','-1','1','--theme','unknown_lab','--relation','peer')
  opts=Path(td)/'opts.json';opts.write_text(json.dumps([
   {'id':'approach','signals':{'relationship':1.0},'themes':['unknown_lab']},
   {'id':'avoid','signals':{'integrity':0.30}}
  ]),encoding='utf-8')
  out=run(d,'soul-continuity-assay',opts)
  assert out['ok'];assert out['checks']['surface_memory_removed'];assert out['checks']['soul_core_preserved'];assert out['checks']['choice_tendency_preserved'];assert out['checks']['discriminating_against_unexperienced_control'];assert out['before_choice']!=out['unexperienced_control_choice']
  # independent CLI process still sees the deep core after the assay
  assert run(d,'soul-deep-audit')['ok'];assert run(d,'whole-audit')['ok']
