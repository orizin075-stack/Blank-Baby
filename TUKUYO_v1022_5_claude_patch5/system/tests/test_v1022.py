import copy,json,os,shutil,tempfile
from pathlib import Path
import pytest
from test_v1019 import run
from test_v1019_1 import fingerprint,crash
from tukuyo_v1022 import cognition as c,proofs,metabolism as m

def fresh(d):run(d,'init','--individual-id','V1022-TEST','--blank-learning')
def teach(d,path,examples):
    path.write_text(json.dumps({'teacher':'test-teacher','examples':examples},ensure_ascii=False));return run(d,'dialogue-learn',path)[0]
def sale(per,count,qty):return {'question':f'1箱に{per}個入りが{count}箱あります。{qty}個売った。残りは何個？','expected_answer':str(per*count-qty)}
def test_learning_requires_two_numeric_examples_and_survives_restart():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);d=td/'d';fresh(d);e=sale(7,4,3);e['event_labels']=[{'surface':'3個売った','direction':-1,'occurred':True,'scope':'current_inventory'}]
  teach(d,td/'lesson.json',[e]);assert run(d,'think',sale(13,7,5)['question'])[0]['uncertain']
  teach(d,td/'lesson.json',[sale(9,3,2)]);r=run(d,'think',sale(13,7,5)['question'])[0];assert r['answer']=='86' and proofs.check(r['proof'],'86')
  cached=(d/'v1022/STATE.json').read_bytes();(d/'v1022/STATE.json').unlink();assert run(d,'learning-audit')[0]['ok'];assert (d/'v1022/STATE.json').read_bytes()==cached
  teach(d,td/'lesson.json',[{**sale(11,5,4),'expected_answer':'59'}]);assert run(d,'think',sale(13,7,5)['question'])[0]['uncertain'];assert run(d,'whole-audit')[0]['ok']
def test_ambiguous_scope_range_and_mixed_event_clauses_abstain():
 with tempfile.TemporaryDirectory() as t:
  d=Path(t)/'d';fresh(d)
  for clause in ['3〜5個食べました','3個食べたかどうか不明','3個食べないとは言えない','3個食べたと報告されました','1箱開けて3個食べました','3個借りて返しました']:
   q='1箱に8個入りが4箱あります。'+clause+'。残りは何個？';r=run(d,'verified-query',q)[0];assert r['uncertain'],(q,r)
  for clause,n in [('3個食べていません','32'),('3個食べたが足りないです','29'),('明日3個食べます','32'),('別の人が別の在庫から3個食べました','32')]:
   assert run(d,'think','1箱に8個入りが4箱あります。'+clause+'。残りは何個？')[0]['answer']==n
def test_minimum_cost_route_role_and_independent_replay():
 task={'initial':{'place':'A'},'goal':{'place':'C'},'actions':[{'id':'direct','pre':{'place':'A'},'set':{'place':'C'},'cost':9},{'id':'one','pre':{'place':'A'},'set':{'place':'B'},'cost':2},{'id':'two','pre':{'place':'B'},'set':{'place':'C'},'cost':3}]}
 p=proofs.plan(task);assert p['route']==['one','two'] and p['cost']==5
 assert proofs.check_plan(task,p);bad=copy.deepcopy(p);bad['cost']=4;assert not proofs.check_plan(task,bad)
 with tempfile.TemporaryDirectory() as t:
  d=Path(t)/'d';fresh(d);r=c.solve(d,'費用を比べて最安の行動列を答えて',task);assert json.loads(r['answer'])==['one','two']
 for expr in ['__import__("os")','2**100000','1/0']:
  with pytest.raises((ValueError,ZeroDivisionError)):proofs.calculate(expr)
def test_path_bound_keeps_costlier_short_prefix_reachable():
 task={'initial':{'n':0,'done':False},'goal':{'done':True},'actions':[{'id':'increment','delta':{'n':1},'cost':1},{'id':'jump','set':{'n':24},'cost':60},{'id':'finish','pre':{'n':24},'set':{'done':True},'cost':1}]}
 p=proofs.plan(task);assert p['route']==['jump','finish'] and p['cost']==61
def test_memory_context_longest_name_and_conflicts():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);d=td/'d';fresh(d);q='記録：本田律は岡山、律は秋田。質問：本田律の現在の居住地は？'
  teach(d,td/'lesson.json',[{'question':q,'expected_answer':'岡山','facts':[{'entity':'本田律','relation':'現在の居住地','value':'岡山'},{'entity':'律','relation':'現在の居住地','value':'秋田'}]}]);assert run(d,'think',q)[0]['answer']=='岡山'
  teach(d,td/'lesson.json',[{'question':q,'expected_answer':'東京','facts':[{'entity':'本田律','relation':'現在の居住地','value':'東京'}]}]);assert run(d,'think',q)[0]['uncertain']
def test_false_quoted_label_cannot_poison_positive_consumption():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);d=td/'d';fresh(d)
  for n in [3,5]:
   teach(d,td/'lesson.json',[{'question':f'1箱に8個入りが4箱あります。「{n}個食べました」は事実ではない。残りは何個？','expected_answer':'32','event_labels':[{'surface':f'{n}個食べました','direction':-1,'occurred':False,'scope':'current_inventory'}]}])
  assert run(d,'think','1箱に8個入りが4箱あります。9個食べました。残りは何個？')[0]['answer']=='23'
def test_coherent_learner_rollback_cannot_be_resigned():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);d=td/'d';fresh(d);teach(d,td/'lesson.json',[sale(7,4,3)]);old=(d/'v1022/STATE.json').read_bytes();oldnames={p.name for p in (d/'v1022/commits').glob('*.json')};teach(d,td/'lesson.json',[sale(9,3,2)])
  for p in (d/'v1022/commits').glob('*.json'):
   if p.name not in oldnames:p.unlink()
  (d/'v1022/STATE.json').write_bytes(old);before=fingerprint(d);r=run(d,'whole-sync',ok=False)[0];assert 'V1022_RECOVERY_HEAD' in r['error'];assert fingerprint(d)==before
def test_nested_runtime_checkpoint_preserves_independent_keys():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);d=td/'d';fresh(d);run(d,'runtime-ecology-init','--families','2');run(d,'runtime-ecology-step','resource','--ticks','8')
  run(d,'realtime-start');run(d,'realtime-tick');cp=run(d,'recovery-checkpoint')[0];path=Path(cp['path']);keys={p.relative_to(d):p.read_bytes() for p in (d/'v1021/runtimes').rglob('succession.key')};assert len(keys)==4
  run(d,'runtime-ecology-step','resource','--ticks','1');r=run(d,'recovery-restore',path,'--trust-file',d/'v1014/recovery.pub','--dry-run')[0];assert r['ok']
  run(d,'recovery-restore',path,'--trust-file',d/'v1014/recovery.pub');assert run(d,'runtime-ecology-status')[0]['tick']==8
  assert all((d/p).read_bytes()==b for p,b in keys.items());assert run(d,'whole-audit')[0]['ok']
def test_actual_energy_death_is_irreversible_and_conserved():
 with tempfile.TemporaryDirectory() as t:
  d=Path(t)/'d';fresh(d);run(d,'metabolism-init','--families','2','--reservoir','0','--max-age','64','--no-actions');r=run(d,'metabolism-step','--ticks','24')[0]
  assert r['active_runtime_count']==0 and r['total_runtime_count']==2 and all(x['cause']=='ENERGY' for x in r['deaths']);assert r['burned']==r['initial_total'];assert run(d,'whole-audit')[0]['ok'];run(m.child(d,'R000000'),'organism2-init',ok=False)
def test_metabolic_sigkill_rollback_redo_and_child_drift():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);d=td/'d';fresh(d);run(d,'metabolism-init','--families','2','--reservoir','0','--max-age','64','--no-actions');run(d,'metabolism-step','--ticks','21');crash(d,'metabolism:after_death','metabolism-step','--ticks','1');assert run(d,'metabolism-audit')[0]['tick']==21
  crash(d,'lineage:after_prepare','metabolism-step','--ticks','1');r=run(d,'metabolism-audit')[0];assert r['tick']==22 and r['active_runtime_count']==0 and run(d,'whole-audit')[0]['ok']
  p=m.child(d,'R000000')/'v978/HEART_STATE.json';assert p.exists();p.write_text('{}');before=fingerprint(d);run(d,'metabolism-step',ok=False);assert fingerprint(d)==before
def test_real_successor_is_fresh_funded_and_inherits_only_public_skills():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);d=td/'d';fresh(d);teach(d,td/'lesson.json',[sale(7,4,3),sale(9,3,2),{'question':'公開しない記憶','facts':[{'entity':'PRIVATE_PERSON','relation':'秘密','value':'PRIVATE_FACT'}]}]);run(d,'metabolism-init','--families','2','--reservoir','40000','--regeneration','1800','--max-age','4');r=run(d,'metabolism-step','--ticks','4')[0]
  assert r['actual_successions']==2 and r['max_generation']==1 and r['active_runtime_count']==2;assert r['initial_total']+r['regenerated']==r['reservoir']+r['burned']+r['living_energy']
  for e in r['successions']:
   assert e['funded_seed_energy']==6500 and e['public_learning_commitment'];assert c.state(m.child(d,e['child']))['facts']==[]
  run(d,'metabolism-step','--ticks','1');assert run(d,'whole-audit')[0]['ok']
def test_signed_trained_seed_mints_separate_identities_without_biography():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);rows=[]
  for name in ['A','B']:
   d=td/name;run(d,'init','--individual-id',name);s=c.state(d);assert s['seed_provenance'] and s['rounds']==0 and not s['facts'];assert run(d,'think','1箱に13個入りが7箱あります。5個売った。残りは何個？')[0]['answer']=='86';assert run(d,'whole-audit')[0]['ok']
   rows.append((d/'v1018/succession.pub').read_text())
  assert len(set(rows))==2
def test_newborn_checkpoint_removes_later_optional_component_directories():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);d=td/'d';run(d,'init','--individual-id','CHECKPOINT-NEWBORN');run(d,'metabolism-init','--families','2','--reservoir','40000','--regeneration','1800','--max-age','4');run(d,'metabolism-step','--ticks','4');run(d,'realtime-start');run(d,'realtime-tick');cp=run(d,'recovery-checkpoint')[0]
  run(d,'metabolism-step','--ticks','1');run(d,'recovery-restore',cp['path'],'--trust-file',d/'v1014/recovery.pub');assert run(d,'metabolism-audit')[0]['tick']==4 and run(d,'whole-audit')[0]['ok'];run(d,'metabolism-step','--ticks','1');assert run(d,'whole-audit')[0]['ok']
