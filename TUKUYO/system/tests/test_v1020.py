from pathlib import Path
import base64,copy,hashlib,json,os,shutil,subprocess,sys,tempfile
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from tukuyo_v1020 import ecology as eco
from tukuyo_v977.whole_state import canon,sha_obj
from tukuyo_v1018 import succession as s18
from test_v1019 import ROOT,run,init,pub,kill
from test_v1019_1 import fingerprint,crash


def proof(family='F0',profile=None):
 sk=Ed25519PrivateKey.generate();pk=base64.b64encode(sk.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode()
 pl={'individual_id':'I'+family,'family_lineage_id':family,'generation':0,'profile':profile or dict(eco.e19.DEFAULT_VALUES),'source_evolution_state_sha256':'a'*64}
 return {'schema':'tukuyo.v1020.source_attestation/1','public_key':pk,'payload':pl,'signature':base64.b64encode(sk.sign(canon(pl))).decode()},sk

def genesis(seed='s',regen=18000,coop=True):
 q,_=proof();cmd={'kind':'INIT','owner_id':'owner','config':{'capacity':240000,'regeneration':regen,'max_population':24,'max_age':18,'cooperation':coop},'seed_sha256':hashlib.sha256(seed.encode()).hexdigest(),'source':q,'source_trust':q['public_key'],'founders':3}
 st,_=eco._transition(None,cmd,'owner')
 for i in range(1,4):
  q,_=proof('F'+str(i));st,_=eco._transition(st,{'kind':'JOIN','source':q,'source_trust':q['public_key'],'founders':3},'owner')
 return st

def evolve(st,n=64,envs=('resource','research','social','volatile')):
 reports=[]
 for t in range(n):st,r=eco._transition(st,{'kind':'TICK','environment':envs[t%len(envs)]},'owner');reports.append(r)
 return st,reports

def test_finite_resource_conservation_population_and_mutation_across_seeds():
 for seed in range(16):
  st,reports=evolve(genesis(str(seed),regen=5000+seed*5000),n=64)
  for r in reports:
   c=r['conservation'];assert c['before']+r['regenerated']==c['after']+r['burned']+r['overflow']
   assert 0<=r['resource']<=240000 and r['population']<=24 and r['allocated']<=r['requested']
   for b in r['births']:
    assert b['generation']>=1 and b['max_abs_mutation']<=.12
    assert abs(sum(b['profile'].values())-3.15)<1e-6
  assert st['metrics']['introduced']+st['metrics']['births']-st['metrics']['deaths']==len(st['agents'])
  assert 240000+st['metrics']['regenerated']==st['resource']+sum(a['energy'] for a in st['agents'].values())+st['metrics']['burned']+st['metrics']['overflow']

def test_resource_shortage_causally_changes_reproductive_success_and_extinction():
 start=genesis('counterfactual',regen=0);rich=copy.deepcopy(start);rich['config']['regeneration']=240000
 scarce,sr=evolve(start,64,('resource',));abundant,ar=evolve(rich,64,('resource',))
 assert len(scarce['agents'])==0 and len(abundant['agents'])>0
 assert abundant['metrics']['births']>scarce['metrics']['births'] and any(d['reason']=='STARVATION' for r in sr for d in r['deaths'])
 assert scarce['metrics']['scarcity_ticks']>0 and abundant['metrics']['scarcity_ticks']==0

def test_cooperation_is_a_conserved_transfer_and_changes_peer_energy():
 start=genesis('sharing',regen=18000)
 # All cooperating peers can donate; create an asymmetric stock of energy.
 ids=list(start['agents']);start['agents'][ids[0]]['energy']-=8000;start['agents'][ids[1]]['energy']+=8000
 # Public source profiles remain fixed; cooperation probabilities already differ
 # deterministically per agent. Search seeds without altering the rules.
 observed=False
 for seed in range(16):
  a=copy.deepcopy(start);a['seed_sha256']=hashlib.sha256(str(seed).encode()).hexdigest();b=copy.deepcopy(a);b['config']['cooperation']=False
  on,onr=evolve(a,24);off,offr=evolve(b,24)
  assert off['metrics']['shared']==0 and off['metrics']['cross_family_shared']==0
  if on['metrics']['shared'] and on['metrics']['cross_family_shared']:
   assert onr!=offr;observed=True;break
 assert observed

def test_deterministic_replay_restart_chunks_and_environment_counterfactual():
 st=genesis('determinism',regen=50000);a,ar=evolve(copy.deepcopy(st),64)
 b,br=evolve(copy.deepcopy(st),32);b,cr=evolve(b,32)
 assert a==b and ar==br+cr
 c,_=evolve(copy.deepcopy(st),64,('volatile',));assert a!=c and c['metrics']['regenerated']<a['metrics']['regenerated']
 assert len({tuple(birth['profile'].values()) for report in ar for birth in report['births']})>1

def test_source_signatures_strict_profile_and_command_bounds():
 q,sk=proof()
 for change in ('profile','private','generation','signature'):
  z=copy.deepcopy(q)
  if change=='profile':z['payload']['profile']['survival']=True
  elif change=='private':z['payload']['private_memory']='secret'
  elif change=='generation':z['payload']['generation']=-1
  else:z['signature']=base64.b64encode(b'x'*64).decode()
  if change!='signature':z['signature']=base64.b64encode(sk.sign(canon(z['payload']))).decode()
  try:eco._verify_source(z,q['public_key'])
  except ValueError:pass
  else:raise AssertionError(change)
 for profile in ({**eco.e19.DEFAULT_VALUES,'curiosity':float('nan')},{**eco.e19.DEFAULT_VALUES,'relationship':.5},{**eco.e19.DEFAULT_VALUES,'curiosity':.50000001,'relationship':.39999999}):
  try:eco._profile(profile)
  except ValueError:pass
  else:raise AssertionError(profile)
 for n in (True,-1,65,1.2):
  try:eco._int(n,1,64)
  except ValueError:pass
  else:raise AssertionError(n)
 st=genesis();st,_=eco._transition(st,{'kind':'TICK','environment':'resource'},'owner');q,_=proof('late')
 try:eco._transition(st,{'kind':'JOIN','source':q,'source_trust':q['public_key'],'founders':1},'owner')
 except ValueError as ex:assert 'ADMISSION_CLOSED' in str(ex)
 else:raise AssertionError('late admission')

def test_allocation_never_creates_resources_and_no_order_bias():
 for seed in range(20):
  weights={f'A{i}':(seed*11+i*31)%97 for i in range(24)}
  for total in (0,1,11,101,sum(weights.values()),sum(weights.values())+100):
   a=eco._allocate(total,weights,str(seed),'allocation');b=eco._allocate(total,dict(reversed(list(weights.items()))),str(seed),'allocation')
   assert a==b and sum(a.values())==min(total,sum(weights.values())) and all(0<=a[k]<=weights[k] for k in a)


def fixture(td):
 p=td/'owner';q=td/'peer';init(p,'owner');init(q,'peer');run(q,'succession-founder-init');pin=td/'peer.pub';pub(q,pin)
 run(p,'population-init','--seed','integration','--regeneration','18000');return p,q,pin

def test_real_two_family_ecology_preserves_source_privacy_and_whole_audit():
 with tempfile.TemporaryDirectory() as td:
  td=Path(td);p,q,pin=fixture(td);secret='SYNTHETIC_PRIVATE_v1020'
  run(q,'heart-experience','learning','.9','1','--theme',secret);before=fingerprint(q)
  run(p,'population-join',q,'--source-trust-file',pin);assert fingerprint(q)==before
  assert secret not in eco.state_path(p).read_text() and secret not in ''.join(x.read_text() for x in (eco.root(p)/'commits').glob('*.json'))
  report,_=run(p,'population-step','resource','--ticks','32');assert len(report['summary']['families'])==2
  assert report['summary']['metrics']['births']>0 and report['summary']['metrics']['deaths']>0
  assert run(p,'population-audit')[0]['ok'] and run(p,'whole-audit')[0]['ok'] and run(q,'whole-audit')[0]['ok']
  assert fingerprint(q)==before

def test_invalid_join_init_and_step_preserve_runtime_bytes():
 with tempfile.TemporaryDirectory() as td:
  td=Path(td);p,q,pin=fixture(td);before=fingerprint(p);wrong=td/'wrong.pub';pub(p,wrong)
  for args in (('population-init',),('population-join',q,'--source-trust-file',wrong),('population-step','resource','--ticks','65'),('population-join',p,'--source-trust-file',wrong)):
   run(p,*args,ok=False);assert fingerprint(p)==before,args
  run(p,'population-step','resource');before=fingerprint(p);run(p,'population-join',q,'--source-trust-file',pin,ok=False);assert fingerprint(p)==before

def test_cache_exact_recovery_and_suffix_or_total_history_loss_fail_closed():
 with tempfile.TemporaryDirectory() as td:
  td=Path(td);p,q,pin=fixture(td);run(p,'population-step','research','--ticks','3');expected=eco.state_path(p).read_bytes();before=fingerprint(p)
  eco.state_path(p).unlink();run(p,'population-audit');assert eco.state_path(p).read_bytes()==expected and fingerprint(p)==before
  assert run(p,'whole-audit')[0]['ok']
  shutil.copytree(p,td/'suffix');d=td/'suffix';eco.state_path(d).unlink();sorted((eco.root(d)/'commits').glob('*.json'))[-1].unlink()
  r,_=run(d,'population-audit',ok=False);assert 'RECOVERY_HEAD' in r['error']
  shutil.copytree(p,td/'lost');d=td/'lost';shutil.rmtree(eco.root(d));r,_=run(d,'population-init',ok=False);assert 'JOURNAL_MISSING' in r['error']

def test_signed_semantically_invalid_commit_and_cache_tamper_rejected():
 with tempfile.TemporaryDirectory() as td:
  td=Path(td);p,q,pin=fixture(td);run(p,'population-step','resource');eco.state_path(p).unlink()
  path=sorted((eco.root(p)/'commits').glob('*.json'))[-1];rec=json.loads(path.read_text());rec['command']['environment']='unknown';rec.pop('commit_sha256');rec.pop('signature');sk,_=s18._ensure_key(p);rec['signature']=base64.b64encode(sk.sign(canon(rec))).decode();rec['commit_sha256']=sha_obj(rec);path.write_bytes(canon(rec)+b'\n')
  r,_=run(p,'population-audit',ok=False);assert 'ENVIRONMENT' in r['error']
  p,q,pin=fixture(td/'cache');cached=json.loads(eco.state_path(p).read_text());cached['state']['resource']+=1;eco.state_path(p).write_bytes(canon(cached)+b'\n')
  r,_=run(p,'population-audit',ok=False);assert 'COMMITTED_STATE_MISMATCH' in r['error']

def test_runtime_death_blocks_model_mutation_but_keeps_read_audit():
 with tempfile.TemporaryDirectory() as td:
  p,q,pin=fixture(Path(td));kill(p);before=fingerprint(p)
  r,_=run(p,'population-step','resource',ok=False);assert 'ENTITY_DEAD' in r['error'] and fingerprint(p)==before
  assert run(p,'population-audit')[0]['ok']

def test_real_sigkill_population_init_join_and_batch_step_recover():
 with tempfile.TemporaryDirectory() as td:
  td=Path(td);p,q,pin=fixture(td);base=td/'base';shutil.copytree(p,base)
  empty=td/'empty';init(empty,'fresh-owner')
  for operation in ('init','join','step'):
   for n,point in enumerate(('lineage:before_prepare','lineage:after_prepare','lineage:apply:0','lineage:apply:2','lineage:after_apply')):
    d=td/f'{operation}-{n}';shutil.copytree(empty if operation=='init' else base,d);before=fingerprint(d)
    args={'init':('population-init',),'join':('population-join',q,'--source-trust-file',pin),'step':('population-step','volatile','--ticks','3')}[operation]
    crash(d,point,*args)
    run(d,'whole-audit');assert run(d,'whole-audit')[0]['ok']
    if point=='lineage:before_prepare':assert fingerprint(d)==before
    else:
     result,_=run(d,'population-audit');assert result['ok']
     if operation=='step':assert result['summary']['tick']==3
     if operation=='join':assert len(result['summary']['families'])==2


def test_tick_horizon_cannot_be_exceeded_or_reset():
 st=genesis('horizon',regen=0);st,_=evolve(st,512)
 assert st['tick']==512 and not st['agents']
 try:eco._transition(st,{'kind':'TICK','environment':'resource'},'owner')
 except ValueError as ex:assert 'TICK_LIMIT' in str(ex)
 else:raise AssertionError('tick limit')


def test_silently_dropped_write_is_not_acknowledged_and_redo_recovers():
 from tukuyo_v1019 import transaction as tx
 with tempfile.TemporaryDirectory() as td:
  p,q,pin=fixture(Path(td));original=tx.atomic_write_bytes;target=eco.state_path(p).resolve();dropped=[]
  def drop_once(path,*args,**kwargs):
   if Path(path).resolve()==target:
    dropped.append(str(path));return Path(path)
   return original(path,*args,**kwargs)
  tx.atomic_write_bytes=drop_once
  try:
   try:eco.step(p,'research',3)
   except ValueError as ex:assert 'WRITE_VERIFY' in str(ex)
   else:raise AssertionError('dropped write acknowledged')
  finally:tx.atomic_write_bytes=original
  assert dropped and (p/tx.TAG/'PREPARED.json').is_file()
  assert tx.recover(p)['recovered']
  assert eco.audit(p)['ok'] and eco.status(p)['summary']['tick']==3
  assert run(p,'whole-audit')[0]['ok'] and not (p/tx.TAG).exists()


def test_missing_cache_reconstruction_retries_stale_materialization_only():
 with tempfile.TemporaryDirectory() as td:
  p,q,pin=fixture(Path(td));stale=eco.state_path(p).read_bytes()
  run(p,'population-step','resource','--ticks','16');run(p,'population-step','research','--ticks','16');run(p,'population-step','social','--ticks','16');run(p,'population-step','volatile','--ticks','16')
  expected=eco.state_path(p).read_bytes();before=fingerprint(p);eco.state_path(p).unlink();original=eco.atomic_write_bytes;writes=[]
  def stale_once(path,contents,*args,**kwargs):
   if Path(path)==eco.state_path(p):
    writes.append(str(path))
    if len(writes)==1:contents=stale
   return original(path,contents,*args,**kwargs)
  eco.atomic_write_bytes=stale_once
  try:result=eco.ensure_state(p)
  finally:eco.atomic_write_bytes=original
  assert len(writes)==2 and result['state']['tick']==64
  assert eco.state_path(p).read_bytes()==expected and fingerprint(p)==before
  assert run(p,'whole-audit')[0]['ok']
  # A preexisting bad cache is not eligible for this retry path.
  eco.state_path(p).write_bytes(stale)
  assert not eco.audit(p)['ok'] and eco.state_path(p).read_bytes()==stale
