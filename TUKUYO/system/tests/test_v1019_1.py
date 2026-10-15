from pathlib import Path
import base64,copy,hashlib,json,os,shutil,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from test_v1019 import run,init,kill,pub
from tukuyo_v1019 import evolution as e
from tukuyo_v1018 import succession as s
from tukuyo_v977.whole_state import canon,sha_obj
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

def fingerprint(d):
 return {p.relative_to(d).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(d).rglob('*') if p.is_file()}

def fixture(td):
 p=td/'P';c=td/'C';init(p,'P');init(c,'C');run(p,'evolution-select','research','--seed','hardening');kill(p)
 pp=td/'p.pub';cp=td/'c.pub';pub(p,pp);pub(c,cp);pkg=td/'pc.json';run(p,'evolution-export','C','--out',pkg,'--child-public-key-file',cp)
 return p,c,pp,cp,pkg

def resign(pkg,parent):
 sk=Ed25519PrivateKey.from_private_bytes(base64.b64decode(s.key_path(parent).read_text()))
 cap=pkg['evolution_capsule'];pl=cap['payload'];sel=pl['selection_proof'];sel.pop('selection_sha256',None);sel['selection_sha256']=sha_obj(sel);pl['selection_sha256']=sel['selection_sha256']
 cap['signature']=base64.b64encode(sk.sign(canon(pl))).decode();cap.pop('capsule_sha256',None);cap['capsule_sha256']=sha_obj(cap);pkg.pop('package_sha256',None);pkg['package_sha256']=sha_obj(pkg)
 return pkg

def test_signed_invalid_evolution_payloads_rejected_without_state_change():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);p,c,pp,cp,pkg=fixture(td);original=json.loads(pkg.read_text())
  for kind in ('unbounded','fitness','negative_mutation','unknown_environment','wrong_generation','private_notes','boolean_fitness','nonwinner','baseline_origin'):
   q=copy.deepcopy(original);pl=q['evolution_capsule']['payload'];sel=pl['selection_proof']
   if kind=='unbounded':sel['selected_profile'].update(relationship=1.0,integrity=.2);sel['max_abs_mutation']=0
   elif kind=='fitness':sel.update(baseline_fitness=-1000,selected_fitness=5000,fitness_gain=6000)
   elif kind=='negative_mutation':sel['max_abs_mutation']=-5
   elif kind=='unknown_environment':sel['environment']='unknown'
   elif kind=='wrong_generation':pl['child_generation']=888
   elif kind=='private_notes':pl['private_notes']='SYNTHETIC_PRIVATE'
   elif kind=='boolean_fitness':sel['selected_fitness']=True
   elif kind=='nonwinner':sel['selected_candidate_id']='C999'
   elif kind=='baseline_origin':sel['baseline_profile'].update(curiosity=.6,relationship=.3)
   resign(q,p);bad=td/(kind+'.json');bad.write_bytes(canon(q));before=fingerprint(c)
   r,_=run(c,'evolution-import',bad,'--parent-trust-file',pp,ok=False)
   assert not r['ok'] and fingerprint(c)==before,(kind,r)
  run(c,'evolution-import',pkg,'--parent-trust-file',pp);assert run(c,'whole-audit')[0]['ok']

def test_rebind_and_invalid_select_preserve_all_state_bytes():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);p,c,pp,cp,pkg=fixture(td);run(c,'succession-founder-init');before=fingerprint(c)
  r,_=run(c,'evolution-import',pkg,'--parent-trust-file',pp,ok=False);assert 'IMPORT_REBIND' in r['error'];assert fingerprint(c)==before
  inner=td/'inner.json';inner.write_bytes(canon(json.loads(pkg.read_text())['base_successor_package']))
  r,_=run(c,'succession-import',inner,'--parent-trust-file',pp,ok=False);assert 'IMPORT_REBIND' in r['error'];assert fingerprint(c)==before
  d=td/'invalid';init(d,'invalid');before=fingerprint(d);run(d,'evolution-select','research','--population','2',ok=False);assert fingerprint(d)==before
  run(d,'evolution-status');assert fingerprint(d)==before;assert run(d,'whole-audit')[0]['ok']

def test_evolution_state_reconstructs_exactly_and_key_loss_fails_closed():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);p,c,pp,cp,pkg=fixture(td);run(c,'evolution-import',pkg,'--parent-trust-file',pp);expected=e.state_path(c).read_bytes();e.state_path(c).unlink()
  assert run(c,'evolution-audit')[0]['ok'];assert e.state_path(c).read_bytes()==expected;assert run(c,'whole-audit')[0]['ok']
  s.key_path(p).unlink();s.pub_path(p).unlink();r,_=run(p,'succession-status',ok=False);assert 'PRIVATE_KEY_MISSING' in r['error']

def test_death_blocks_experience_selection_and_conversation():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);p,c,pp,cp,pkg=fixture(td);before=fingerprint(p)
  for args in [('evolution-select','resource'),('soul-experience','learning','.9','1'),('heart-experience','learning','.9','1'),('conversation-ingest','new knowledge')]:
   r,_=run(p,*args,ok=False);assert 'ENTITY_DEAD' in r.get('error',''),r;assert fingerprint(p)==before
  from tukuyo_v978.heart_loop import process_experience
  try:process_experience(p,'learning',.9,1)
  except ValueError as ex:assert 'ENTITY_DEAD' in str(ex)
  else:raise AssertionError('dead API accepted')

def crash(d,point,*args):
 anchor=os.environ['TUKUYO_TEST_RUNTIME_ANCHOR']
 r=subprocess.run([sys.executable,'-B',str(ROOT/'run_tukuyo.py'),'--runtime-trust-file',anchor,'--data',str(d),*map(str,args)],cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','TUKUYO_CRASH_POINT':point},capture_output=True,text=True,timeout=180)
 assert r.returncode==-9,(point,r.returncode,r.stdout,r.stderr)

def test_real_sigkill_selection_import_and_export_recover():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);p,c,pp,cp,pkg=fixture(td);live=td/'live';init(live,'live')
  points=('lineage:before_prepare','lineage:after_prepare','lineage:apply:0','lineage:apply:3','lineage:after_apply')
  for op in ('select','import','export','succession'):
   for j,point in enumerate(points):
    d=td/(op+str(j));shutil.copytree(live if op=='select' else p if op=='export' else c,d)
    if op=='select':args=('evolution-select','social','--seed','crash')
    elif op=='import':args=('evolution-import',pkg,'--parent-trust-file',pp)
    elif op=='export':args=('evolution-export','C','--out',td/(op+str(j)+'.json'),'--child-public-key-file',cp)
    else:
     inner=td/'inner.json';inner.write_bytes(canon(json.loads(pkg.read_text())['base_successor_package']));args=('succession-import',inner,'--parent-trust-file',pp)
    crash(d,point,*args);assert run(d,'whole-audit')[0]['ok'];assert run(d,'evolution-audit')[0]['ok']
    if point=='lineage:before_prepare':run(d,*args)
    elif op in ('import','succession'):
     r,_=run(d,*args,ok=False);assert 'PACKAGE_REPLAY' in r['error']
    assert run(d,'whole-audit')[0]['ok']

def test_signed_certificate_mortality_profile_and_keys_rejected():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);p,c,pp,cp,pkg=fixture(td);sk=Ed25519PrivateKey.from_private_bytes(base64.b64decode(s.key_path(p).read_text()))
  original=json.loads(pkg.read_text())['base_successor_package']
  for kind in ('alive','profile','memo'):
   q=copy.deepcopy(original);cert=q['lineage_certificates'][-1];pl=cert['payload']
   if kind=='alive':pl['mortality_commitment']['lifecycle']='ALIVE'
   elif kind=='profile':pl['inherited_value_profile']['curiosity']=99
   else:pl['memo']='unauthorized extension'
   cert['signature']=base64.b64encode(sk.sign(canon(pl))).decode();cert.pop('certificate_sha256');cert['certificate_sha256']=sha_obj(cert);q.pop('package_sha256');q['package_sha256']=sha_obj(q)
   f=td/(kind+'.json');f.write_bytes(canon(q));before=fingerprint(c);run(c,'succession-import',f,'--parent-trust-file',pp,ok=False);assert fingerprint(c)==before

def test_independent_container_consumption_and_overconsumption():
 from tukuyo_v1012.core_reasoning import reason
 from tukuyo_v1014_1.semantic_verifier import verify_bounded_semantics
 cases=[('6個入りの箱を4箱。3箱使った。残りの箱は何箱？','1'),('1箱に8個入りが4箱あります。3箱使いました。残りの箱は何箱？','1'),('1箱に8個入りが4箱あります。3箱と2個使いました。残りは何個？','6'),('1箱に8個入りが4箱あります。5箱使いました。残りは何個？',None),('6個入りの箱が4箱あり、3箱使った。残りは何箱？','1'),('8個入りの箱を4箱。2個使ってから1箱使った。残りは何個？','22'),('8枚入りの袋を4袋。3袋と2枚使った。残りは何枚？','6'),('1箱に8個入りが4箱あります。1箱開けて3個食べました。残りは何個？','29')]
 for q,expected in cases:
  r=reason(q);v=verify_bounded_semantics(q,expected if expected else '-8')
  if expected is None:assert not r['ok'] and not v['supported'],(q,r,v)
  else:assert r['answer']==expected and v['supported'],(q,r,v)

def test_signed_commit_rejects_hash_only_forgery():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);p,c,pp,cp,pkg=fixture(td);f=sorted((e.root(p)/'commits').glob('*.json'))[-1];q=json.loads(f.read_text());q['state']['selection_seq']+=1;q['state']['state_sha256']=e._state_hash(q['state']);q.pop('commit_sha256');q['commit_sha256']=sha_obj(q);f.write_bytes(canon(q));e.state_path(p).unlink()
  r,_=run(p,'evolution-audit',ok=False);assert 'COMMIT_SIGNATURE' in r['error'],r

def test_sigkill_before_evolution_materialization_leaves_live_tree_unchanged():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);p,c,pp,cp,pkg=fixture(td);live=td/'live';init(live,'live')
  for kind,d,args in [('select',live,('evolution-select','social')),('import',c,('evolution-import',pkg,'--parent-trust-file',pp))]:
   source="import sys,os,signal;sys.path.insert(0,sys.argv[1]);import run_tukuyo;from tukuyo_v1019 import evolution as e\nold=e._save_state\ndef write(data,st):\n if st.get('selection') or st.get('imported_package_sha256'):os.kill(os.getpid(),signal.SIGKILL)\n return old(data,st)\ne._save_state=write\nraise SystemExit(run_tukuyo.main(sys.argv[2:]))\n"
   before=fingerprint(d);anchor=os.environ['TUKUYO_TEST_RUNTIME_ANCHOR'];r=subprocess.run([sys.executable,'-B','-c',source,str(ROOT),'--runtime-trust-file',anchor,'--data',str(d),*map(str,args)],cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=180)
   assert r.returncode==-9,(r.returncode,r.stdout,r.stderr);run(d,'evolution-audit');assert fingerprint(d)==before;run(d,*args);assert run(d,'whole-audit')[0]['ok']

def test_complete_signed_forgery_of_baseline_origin_rejected():
 with tempfile.TemporaryDirectory() as t:
  td=Path(t);p,c,pp,cp,pkg=fixture(td);q=json.loads(pkg.read_text());pl=q['evolution_capsule']['payload'];sel=pl['selection_proof'];base=dict(e.DEFAULT_VALUES);base.update(curiosity=.6,relationship=.3)
  cand=e._candidates(base,sel['environment'],sel['population'],sel['seed_sha256'],sel['family_lineage_id'],sel['generation']);w=max(cand,key=lambda x:(x['fitness'],x['candidate_id']))
  sel.update(baseline_profile=base,baseline_fitness=cand[0]['fitness'],selected_candidate_id=w['candidate_id'],selected_profile=w['profile'],selected_fitness=w['fitness'],fitness_gain=round(w['fitness']-cand[0]['fitness'],9),max_abs_mutation=w['max_abs_mutation'],candidate_commitment_sha256=sha_obj([{'id':x['candidate_id'],'profile_sha256':x['profile_sha256'],'fitness':x['fitness']} for x in cand]))
  sel.pop('selection_sha256');sel['selection_sha256']=sha_obj(sel)
  for k in ('selection_sha256','environment','baseline_fitness','selected_fitness','fitness_gain','max_abs_mutation','trait_budget'):pl[k]=sel[k]
  pl['selected_evolution_profile']=w['profile'];pl['runtime_inherited_value_profile']=e._runtime_child_profile(w['profile']);bp=q['base_successor_package'];cert=bp['lineage_certificates'][-1];cpayload=cert['payload'];cpayload['inherited_value_profile']=pl['runtime_inherited_value_profile'];cpayload['evolution_commitment']={'selection_sha256':sel['selection_sha256'],'baseline_profile':base,'selected_profile':w['profile']}
  sk=Ed25519PrivateKey.from_private_bytes(base64.b64decode(s.key_path(p).read_text()));cert['signature']=base64.b64encode(sk.sign(canon(cpayload))).decode();cert.pop('certificate_sha256');cert['certificate_sha256']=sha_obj(cert);bp.pop('package_sha256');bp['package_sha256']=sha_obj(bp);pl['base_successor_package_sha256']=bp['package_sha256'];resign(q,p);f=td/'forged-origin.json';f.write_bytes(canon(q));before=fingerprint(c)
  r,_=run(c,'evolution-import',f,'--parent-trust-file',pp,ok=False);assert 'BASELINE_PROVENANCE' in r['error'],r;assert fingerprint(c)==before
