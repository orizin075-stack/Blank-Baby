import os,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));CLI=ROOT/'run_tukuyo.py'
from tukuyo_v1012.core_reasoning import reason
from tukuyo_v1012.memory_compaction import compact,audit

def run(d,*a):
 env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'};anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR');cmd=[sys.executable,'-B',str(CLI)]
 if anchor:cmd += ['--runtime-trust-file',anchor]
 cmd += ['--data',str(d),*map(str,a)];p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,env=env,timeout=240);r=json.loads(p.stdout)
 assert p.returncode==0 and r.get('ok',False),(p.stdout,p.stderr);return r

def test_v1012_core_reasoning_bounded():
 assert reason('りんごを3個持っていて2個もらった。全部で何個？')['answer']=='5'
 assert reason('10個持っていて4個使った。残りはいくつ？')['answer']=='6'
 r=reason('AはBより大きい。BはCより大きい。AとCでは？');assert r['ok'] and 'A' in r['answer'] and 'C' in r['answer']

def test_v1012_memory_checkpoint_is_append_safe():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V1012-C')
  for i in range(20):run(d,'knowledge-add',f'記憶{i}は値{i}')
  c=compact(d,retain=8);assert c['ok'] and audit(d)['ok']
  run(d,'knowledge-add','追加記憶は42');assert audit(d)['ok']

def test_v1012_cognition_uses_core_reasoning():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V1012-R')
  r=run(d,'cognitive-query','りんごを3個持っていて2個もらった。全部で何個？');assert r['answer']=='5'
