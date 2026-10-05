import json,os,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py'
sys.path.insert(0,str(ROOT/'src'))

def run(d,*a,ok=True):
 env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
 p=subprocess.run([sys.executable,'-B',str(CLI),'--data',str(d),*map(str,a)],cwd=ROOT,text=True,capture_output=True,env=env,timeout=240)
 try:r=json.loads(p.stdout)
 except Exception:raise AssertionError((p.returncode,p.stdout,p.stderr))
 if ok and (p.returncode!=0 or not r.get('ok',False)):raise AssertionError((p.returncode,r,p.stderr))
 if not ok and p.returncode==0 and r.get('ok',True):raise AssertionError(('expected failure',r))
 return r

def test_v1014_1_recovery_signer_survives_first_restore_and_recheckpoint():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';pin=Path(td)/'recovery.pin'
  run(d,'init','--individual-id','V10141-KEY');run(d,'realtime-start','--target-seconds','60');run(d,'realtime-tick')
  cp1=run(d,'recovery-checkpoint','--note','first');cpp1=Path(cp1['path'])
  pub=(d/'v1014/recovery.pub').read_text().strip();pin.write_text(pub)
  assert run(d,'recovery-audit',cpp1,'--trust-file',pin)['ok']
  rr=run(d,'recovery-restore',cpp1,'--trust-file',pin);assert rr['restored']
  assert (d/'v1014/recovery.pub').read_text().strip()==pub
  cp2=run(d,'recovery-checkpoint','--note','after restore');cpp2=Path(cp2['path'])
  assert (d/'v1014/recovery.pub').read_text().strip()==pub
  assert run(d,'recovery-audit',cpp2,'--trust-file',pin)['ok']

def test_v1014_1_missing_public_key_is_derived_not_rotated():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10141-DERIVE');run(d,'realtime-start','--target-seconds','60')
  run(d,'recovery-checkpoint');pub=(d/'v1014/recovery.pub').read_text().strip();(d/'v1014/recovery.pub').unlink()
  run(d,'recovery-checkpoint');assert (d/'v1014/recovery.pub').read_text().strip()==pub

def test_v1014_1_verified_semantics_and_query_roles():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10141-SEM')
  good={
   '3個持っていて2個もらった。合計は？':'5',
   '3個と2個と4個の総数は？':'9',
   '1箱6個、4箱。総数は？':'24',
   '1箱6個、4箱。箱は何箱？':'4',
   '1箱6個、4箱買い3個食べた。残りは？':'21',
   '20円の商品を3個。商品は何個？':'3',
   'りんご3個・みかん2個。りんごの総数は？':'3',
  }
  for q,exp in good.items():
   r=run(d,'verified-query',q);assert r['answer']==exp and not r['uncertain'] and r['confidence']>=.70,(q,r)
   assert r['verification_evidence'].get('independent') is True
  for q in ('3kgと2mの合計は？','最大3個と最大2個。正確な合計は？','雨なら濡れる。雨ではない。どうなる？'):
   r=run(d,'verified-query',q);assert r['uncertain'] and r['confidence']<.70,(q,r)

def test_v1014_1_verified_query_keeps_whole_state_green():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';run(d,'init','--individual-id','V10141-SYNC');assert run(d,'whole-audit')['ok']
  r=run(d,'verified-query','3たす4は？');assert r['answer']=='7' and not r['uncertain']
  assert run(d,'whole-audit')['ok']
  assert run(d,'realtime-start','--target-seconds','60')['ok']

def test_v1014_1_index_uses_bounded_candidate_surface():
 from tukuyo_v1001.knowledge import _connect,_index_record,_path,search_diagnostics
 with tempfile.TemporaryDirectory() as td:
  d=Path(td)/'d';p=_path(d);p.parent.mkdir(parents=True,exist_ok=True);db=_connect(d)
  rows=[]
  for i in range(3000):
   rec={'id':f'id{i:05d}','source':'test','text':f'国{i:05d}の首都は都市{i:05d}。','metadata':{}}
   rows.append(rec);_index_record(db,rec)
  p.write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rows),encoding='utf-8')
  db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('source_size',?)",(str(p.stat().st_size),));db.commit();db.close()
  r=search_diagnostics(d,'国02999の首都は？',5)
  assert r['results'] and '都市02999' in r['results'][0]['text']
  assert r['candidate_count']<=256,r
  assert r['candidate_strategy']=='SELECTIVE_UNION'
