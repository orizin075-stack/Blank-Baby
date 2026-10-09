from pathlib import Path
import json,os,subprocess,sys,tempfile,time
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'run_tukuyo.py';WIT=ROOT/'tools/realtime_witness.py'
def run(d,*a,env=None,ok=True):
 e={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT/'src')};e.update(env or {})
 p=subprocess.run([sys.executable,'-B',str(RUN),'--data',str(d),*map(str,a)],cwd=ROOT,env=e,text=True,capture_output=True)
 if ok and p.returncode!=0:raise AssertionError(p.stdout+p.stderr)
 return json.loads(p.stdout) if p.stdout.strip().startswith('{') else {'rc':p.returncode,'out':p.stdout,'err':p.stderr}
def wit(*a):
 p=subprocess.run([sys.executable,'-B',str(WIT),*map(str,a)],cwd=ROOT,text=True,capture_output=True);assert p.returncode==0,p.stderr;return json.loads(p.stdout)
def test_soul_event_first_recovers_after_kill():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10144-SOUL')
  p=subprocess.run([sys.executable,'-B',str(RUN),'--data',str(d),'soul-experience','learning','0.8','0.9','--theme','atomic'],cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT/'src'),'TUKUYO_CRASH_POINT':'soul:after_event'})
  assert p.returncode!=0
  a=run(d,'whole-audit');assert a['ok'],a
  t=run(d,'soul-identity-audit');assert t['ok'],t
def test_conversation_crash_auto_rollback():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10144-CHAT');before=(d/'v977/SOUL_CORE.json').read_bytes()
  p=subprocess.Popen([sys.executable,'-B',str(RUN),'--data',str(d),'conversation-ingest','今日は新しい発見をした'],cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT/'src')})
  time.sleep(.02)
  if p.poll() is None:p.kill()
  p.wait()
  a=run(d,'whole-audit');assert a['ok'],a
  assert not (d/'v1014_4/private/CONVERSATION_TXN.json').exists()
def test_pack_variants():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10144-R')
  a=run(d,'verified-query','1袋に8枚入りが3袋。全部で何枚？');assert a['answer']=='24' and not a['uncertain'],a
  b=run(d,'verified-query','6個入りパックを5つ。全部で何個？');assert b['answer']=='30' and not b['uncertain'],b
def test_gap_is_not_continuity():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';w=Path(td)/'w';run(d,'init','--individual-id','V10144-GAP');run(d,'continuity-campaign-start','--target-seconds','1','--tick-seconds','1','--checkpoint-seconds','99')
  wit('keygen','--out-dir',w);srq=Path(td)/'sreq.json';srr=Path(td)/'srec.json';run(d,'realtime-witness-request','--out',srq);wit('sign',srq,'--private-key',w/'realtime_witness.key','--out',srr)
  time.sleep(5.5);run(d,'continuity-campaign-step','--note','late')
  erq=Path(td)/'ereq.json';err=Path(td)/'erec.json';run(d,'continuity-campaign-end-request','--out',erq);wit('sign',erq,'--private-key',w/'realtime_witness.key','--out',err)
  a=run(d,'continuity-campaign-audit','--start-witness',srr,'--end-witness',err,'--witness-trust-file',w/'realtime_witness.pub','--require-complete',ok=False);assert not a['ok'] and ('CAMPAIGN_TICK_GAP' in a['errors'] or 'CAMPAIGN_WITNESS_GAP' in a['errors']),a


def test_question_clause_is_not_premise():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10144-Q')
  a=run(d,'verified-query','すべての犬は動物です。タマは犬ですか？タマは動物ですか？')
  assert a.get('uncertain') and float(a.get('confidence',1)) <= 0.2,a
  b=run(d,'verified-query','雪なら道が白くなる。道が白くなっている。雪は降った？')
  assert b.get('uncertain') and float(b.get('confidence',1)) <= 0.2 and b.get('answer') != '道が白くなる',b


def test_independent_logic_verifier_confidence():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10144-LOGIC')
  a=run(d,'verified-query','すべての犬は動物です。タマは犬です。タマは動物ですか？')
  assert a['answer']=='タマは動物です。' and not a['uncertain'] and a['confidence']>=.9 and a['verification_evidence'].get('independent'),a
  b=run(d,'verified-query','雨なら地面が濡れる。雨が降っている。地面は濡れる？')
  assert not b['uncertain'] and b['confidence']>=.9 and b['verification_evidence'].get('kind')=='LOGIC_MP',b
  c=run(d,'verified-query','雪なら道が白くなる。道が白くなっている。雪は降った？')
  assert c['uncertain'] and c['confidence']<=.2,c

def test_checkpoint_failure_makes_campaign_audit_red():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10144-CPFAIL');run(d,'continuity-campaign-start','--target-seconds','30','--tick-seconds','5','--checkpoint-seconds','999')
  code='from pathlib import Path\nimport json\nimport tukuyo_v1014_4.long_run_campaign as c\nd=Path('+repr(str(d))+');c.create_checkpoint=lambda *a,**k: (_ for _ in ()).throw(ValueError("INJECTED_CHECKPOINT_FAILURE"));x=c.step(d,"forced-cp-fail",True,None);a=c.audit(d);print(json.dumps({"step":x,"audit":a}))'
  e={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT/'src')};pr=subprocess.run([sys.executable,'-B','-c',code],cwd=ROOT,env=e,text=True,capture_output=True);assert pr.returncode==0,pr.stderr;o=json.loads(pr.stdout)
  assert not o['audit']['ok'] and 'CAMPAIGN_CHECKPOINT_FAILURE' in o['audit']['errors'],o

def test_restart_observation_counts_real_process_change():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10144-RST');run(d,'continuity-campaign-start','--target-seconds','30','--tick-seconds','5','--checkpoint-seconds','999')
  code='from pathlib import Path\nimport json\nfrom tukuyo_v1014_4.long_run_campaign import step,_read,state_path\nd=Path('+repr(str(d))+');step(d,"a");step(d,"b");print(json.dumps(_read(state_path(d))))'
  e={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT/'src')};pr=subprocess.run([sys.executable,'-B','-c',code],cwd=ROOT,env=e,text=True,capture_output=True);assert pr.returncode==0,pr.stderr;st=json.loads(pr.stdout)
  assert st['restart_observations']<=1,st

def test_quantity_generalization_unseen_surfaces():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10144-UNSEENQ')
  cases=[
   ('1ケースに7本入りが4ケース。全部で何本？','28',False),
   ('9枚入りの束を3束。全部で何枚？','27',False),
   ('1袋に10枚入りが4袋。2枚使った。残りは？','38',False),
   ('1箱に6個入りが5箱。箱はいくつ？','5',False),
  ]
  for q,ans,unc in cases:
   x=run(d,'verified-query',q);assert x['answer']==ans and bool(x['uncertain'])==unc and x['confidence']>=.9,(q,x)
  x=run(d,'verified-query','最低3個と最低2個あります。正確な合計は？')
  assert x['uncertain'] and x['confidence']<=.2,x

def test_heart_takes_in_what_the_soul_took_in_before_a_kill():
 # a process killed between the soul and the heart: the next start lets the heart take the experience in
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10144-HEART');run(d,'heart-experience','discovery','0.8','0.6','--theme','first')
  p=subprocess.run([sys.executable,'-B',str(RUN),'--data',str(d),'heart-experience','learning','0.7','0.5','--theme','second'],cwd=ROOT,capture_output=True,
                   env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT/'src'),'TUKUYO_CRASH_POINT':'heart:after_soul'})
  assert p.returncode!=0 and (d/'v978/private/PENDING_FEELING.json').is_file()
  a=run(d,'whole-audit');assert a['ok'],a
  souls=[json.loads(x) for x in (d/'v977/SOUL_EVENTS.jsonl').read_text().splitlines()]
  hearts=[json.loads(x) for x in (d/'v978/HEART_EVENTS.jsonl').read_text().splitlines() if 'EXPERIENCE_LOOP' in x]
  assert [h['soul_event_sha256'] for h in hearts]==[e['event_sha256'] for e in souls] and hearts[-1]['theme']=='second'
  assert run(d,'heart-audit')['ok'] and not (d/'v978/private/PENDING_FEELING.json').exists()
