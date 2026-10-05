import os,json,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py'
def run(d,*a,ok=True):
 env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'};anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR');cmd=[sys.executable,'-B',str(CLI)]
 if anchor:cmd += ['--runtime-trust-file',anchor]
 cmd += ['--data',str(d),*map(str,a)];p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,env=env,timeout=240);r=json.loads(p.stdout)
 if ok and (p.returncode or not r.get('ok',False)):raise AssertionError(p.stdout+p.stderr)
 return r

def test_v1010_natural_language_math_and_calibrated_verify():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V1010-MATH')
  assert run(d,'cognitive-query','3たす4は？')['answer']=='7'
  v=run(d,'verified-query','12かける9は？');assert v['answer']=='108' and not v['uncertain'] and v['confidence']>=.95

def test_v1010_no_answer_retrieval():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V1010-NOANS');run(d,'knowledge-add','トルヴァ共和国の首都はセレン')
  r=run(d,'cognitive-query','日本の首都は？');assert '十分に対応する根拠' in r['answer'] and not r['retrieval_answerable']
  v=run(d,'verified-query','日本の首都は？');assert v['uncertain'] and v['confidence']<.5

def test_v1010_conversation_keeps_whole_audit_green():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V1010-CHAT');run(d,'conversation-ingest','Alice betrayed me');assert run(d,'whole-audit')['ok']

def test_v1010_relation_and_negation_repairs():
 from tukuyo_v996.conversational_grounding import infer_relation,appraise
 assert infer_relation('Alice betrayed me')=='Alice';assert infer_relation('I was helped by Bob')=='Bob';assert infer_relation('ついに謎が解けた')==''
 assert appraise('助けてもらえなかった')['derived_valence']<0;assert appraise('誰も傷つかなかった')['features']['harm']==0

def test_v1010_incremental_identity_mode():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V1010-ID');run(d,'conversation-ingest','研究で新しい証拠を発見した')
  s=json.loads((d/'v989/TEMPORAL_IDENTITY.json').read_text());assert s['checkpoint_mode']=='INCREMENTAL_APPEND_WITH_FULL_REPLAY_AUDIT';assert run(d,'soul-identity-audit')['ok']
