import json,os,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));CLI=ROOT/'run_tukuyo.py'
from tukuyo_v1012.core_reasoning import reason
from tukuyo_v1012.memory_compaction import compact,audit as compact_audit
from tukuyo_v1002.cognition import _state_context

def run(d,*a,ok=True):
 env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
 cmd=[sys.executable,'-B',str(CLI),'--data',str(d),*map(str,a)]
 p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,env=env,timeout=240)
 try:r=json.loads(p.stdout)
 except Exception:raise AssertionError((p.returncode,p.stdout,p.stderr))
 if ok and (p.returncode!=0 or not r.get('ok',False)):raise AssertionError((p.returncode,r,p.stderr))
 if not ok and p.returncode==0 and r.get('ok',True):raise AssertionError(('expected failure',r))
 return r

def test_v1012_1_negation_and_invalid_logic_abstain():
 r=reason('もし晴れなら地面が乾く。今日は晴れだ。どうなる？');assert r['ok'] and '地面が乾く' in r['answer']
 assert not reason('雨なら地面が濡れる。雨は降っていない。どうなる？')['ok']
 assert not reason('AならB。Bである。Aと言える？')['ok']
 assert not reason('AならB。Aではない。Bと言える？')['ok']
 assert not reason('AならB。Aである。Aではない。どうなる？')['ok']

def test_v1012_1_quantity_soundness_and_abstention():
 assert reason('3個と4個と5個を全部足すといくつ？')['answer']=='12'
 assert reason('80円の商品を3個。合計はいくら？')['answer']=='240'
 assert reason('6個入り×4箱の総数は？')['answer']=='24'
 assert not reason('2リットルから500ミリリットル使った。残りは？')['ok']
 assert not reason('3kgと2mを合計すると？')['ok']
 assert not reason('5個ずつ3人に配る。全部で？')['ok']

def test_v1012_1_verified_query_recomputes_core_reasoning():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10121-VER')
  r=run(d,'verified-query','6個入り×4箱の総数は？')
  assert r['answer']=='24' and not r['uncertain'] and r['confidence']>=.78
  x=run(d,'verified-query','2リットルから500ミリリットル使った。残りは？')
  assert x['uncertain'] and x['confidence']<.7

def test_v1012_1_unrelated_conversation_keeps_social_and_whole_audits_green():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10121-CHAT')
  run(d,'conversation-ingest','田中さんが助けてくれた')
  run(d,'conversation-ingest','本を読んだ')
  assert run(d,'relation-audit')['ok'] and run(d,'peer-audit')['ok'] and run(d,'whole-audit')['ok']

def test_v1012_1_conversation_and_semantic_tamper_reach_whole_audit():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10121-TAMP');run(d,'conversation-ingest','Alice helped me')
  assert run(d,'whole-audit')['ok']
  p=d/'v996/CONVERSATION_GROUNDING_EVENTS.jsonl';lines=p.read_text().splitlines();q=json.loads(lines[0]);q['text']='TAMPERED';lines[0]=json.dumps(q,ensure_ascii=False);p.write_text('\n'.join(lines)+'\n')
  w=run(d,'whole-audit',ok=False);assert any('CONVERSATION_GROUNDING_AUDIT' in x or 'COMPONENT_DRIFT:conversation_events_v996' in x for x in w['errors'])
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10121-SEMT');run(d,'conversation-ingest','研究で証拠を発見した')
  p=d/'v998/SEMANTIC_INFERENCE_EVENTS.jsonl';lines=p.read_text().splitlines();q=json.loads(lines[0]);q['analysis']['primary_meaning']='TAMPERED';lines[0]=json.dumps(q,ensure_ascii=False);p.write_text('\n'.join(lines)+'\n')
  w=run(d,'whole-audit',ok=False);assert any('SEMANTIC_INFERENCE_AUDIT' in x or 'COMPONENT_DRIFT:semantic_inference_events_v998' in x for x in w['errors'])

def test_v1012_1_checkpoint_uses_real_journals_heart_and_empty_to_created_is_append_safe():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10121-COMP')
  c=compact(d,retain=16);assert c['ok'] and compact_audit(d)['ok']
  run(d,'knowledge-add','最初の知識は42')
  run(d,'conversation-ingest','Bob helped me')
  assert compact_audit(d)['ok']  # all were empty prefixes at checkpoint, normal creation is append-safe
  c=compact(d,retain=16);src=c['checkpoint']['sources']
  assert src['knowledge']['count']>=1 and src['conversation']['count']>=1 and src['semantic']['count']>=1 and src['heart']['count']>=1
  assert _state_context(d).get('working_memory',{}).get('schema')=='tukuyo.v1012_1.working_memory/1'
  # checkpoint now commits the existing conversation bytes; mutate the committed prefix.
  p=d/'v996/CONVERSATION_GROUNDING_EVENTS.jsonl';raw=p.read_bytes();p.write_bytes(raw.replace(b'Bob',b'Eve',1))
  assert not compact_audit(d)['ok']

def test_v1012_1_legacy_layers_are_reintegrated_into_whole_audit_surface():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10121-LEGACY')
  run(d,'conversation-ingest','peerAに助けてもらった','--relation','peerA')
  run(d,'soul-consolidate');run(d,'continuity-checkpoint','--note','legacy reintegration');run(d,'homeostasis-assess')
  run(d,'whole-sync')
  r=run(d,'legacy-integration-audit')
  assert r['ok']
  for k in ('heart','deep_soul','continuity_ledger','homeostasis','temporal_identity','relation','peer','conversation','semantic_inference','whole'):
   assert r['checks'][k]['present'] and r['checks'][k]['ok']
