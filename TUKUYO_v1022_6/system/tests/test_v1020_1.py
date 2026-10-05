from pathlib import Path
import base64,copy,json,shutil,tempfile
import pytest
from tukuyo_v1020 import ecology as eco
from tukuyo_v977 import whole_state as whole
from test_v1020 import proof,fixture
from test_v1019 import run
from test_v1019_1 import fingerprint


def test_signed_source_requires_exact_integer_trait_budget():
 for delta in (-1,1):
  p=dict(eco.e19.DEFAULT_VALUES);p['curiosity']=.5+delta/1000000
  q,_=proof(profile=p)
  with pytest.raises(ValueError,match='TRAIT_BUDGET'):eco._verify_source(q,q['public_key'])
 for delta in (-.12,0,.12):
  p=dict(eco.e19.DEFAULT_VALUES);p['curiosity']+=delta;p['integrity']-=delta
  accepted=eco._profile(p)
  assert sum(round(v*1000000) for v in accepted.values())==3150000
  for tick in range(100):
   accepted=eco._mutate(accepted,'exact-budget',tick,str(tick))
   assert sum(round(v*1000000) for v in accepted.values())==3150000


def test_coherent_journal_and_warm_cache_rollback_rejected_before_mutation():
 with tempfile.TemporaryDirectory() as td:
  td=Path(td);p,_,_=fixture(td);old=eco.state_path(p).read_bytes()
  run(p,'population-step','resource','--ticks','3')
  for c in (eco.root(p)/'commits').glob('*.json'):
   if int(c.stem)>1:c.unlink()
  eco.state_path(p).write_bytes(old);before=fingerprint(p)
  assert not eco.audit(p)['ok']
  for args in (('population-audit',),('population-status',),('population-step','resource'),('population-init',)):
   result,_=run(p,*args,ok=False)
   assert 'RECOVERY_HEAD' in result['error'] and fingerprint(p)==before


def test_missing_or_invalid_whole_anchor_never_authorizes_cache_or_prefix():
 with tempfile.TemporaryDirectory() as td:
  td=Path(td);p,_,_=fixture(td);old=eco.state_path(p).read_bytes()
  run(p,'population-step','resource','--ticks','3')
  for cache_missing in (False,True):
   for kind,code in (('missing','RECOVERY_WHOLE_MISSING'),('component','RECOVERY_HEAD_MISSING'),('signature','RECOVERY_WHOLE_SIGNATURE'),('schema','RECOVERY_WHOLE_SCHEMA')):
    d=td/(kind+str(cache_missing));shutil.copytree(p,d)
    for c in (eco.root(d)/'commits').glob('*.json'):
     if int(c.stem)>1:c.unlink()
    if cache_missing:eco.state_path(d).unlink()
    else:eco.state_path(d).write_bytes(old)
    wp=whole.state_path(d)
    if kind=='missing':wp.unlink()
    else:
     envelope=json.loads(wp.read_text())
     if kind=='signature':envelope['signature']=base64.b64encode(b'x'*64).decode()
     else:
      payload=copy.deepcopy(envelope['payload'])
      if kind=='component':payload['component_hashes'].pop('population_ecology_v1020')
      else:payload['schema']='wrong'
      envelope=whole._sign(d,payload)
     wp.write_bytes(whole.canon(envelope)+b'\n')
    before=fingerprint(d)
    with pytest.raises(ValueError,match=code):eco.ensure_state(d)
    assert fingerprint(d)==before
    result,_=run(d,'population-step','resource',ok=False)
    assert code in result['error'] and fingerprint(d)==before


def test_parent_directory_symlink_cannot_redirect_redo_or_staging():
 from tukuyo_v1019 import transaction as tx
 with tempfile.TemporaryDirectory() as td:
  td=Path(td);external=td/'external';external.mkdir();sentinel=external/'sentinel';sentinel.write_bytes(b'ORIGINAL')
  data=td/'bare';data.mkdir();(data/'linked').symlink_to(external,target_is_directory=True)
  b=b'MODIFIED';rec={'schema':'tukuyo.v1019.1.lineage_transaction/1','writes':[{'path':'linked/sentinel','bytes':base64.b64encode(b).decode(),'sha256':tx.hashlib.sha256(b).hexdigest(),'mode':0o600}],'outputs':[]};rec['sha256']=whole.sha_obj(rec)
  with pytest.raises(ValueError,match='LINEAGE_TXN_SYMLINK'):tx._apply(data,rec)
  assert sentinel.read_bytes()==b'ORIGINAL'
  p,_,_=fixture(td/'runtime');before=fingerprint(p)
  (p/'linked').symlink_to(external,target_is_directory=True)
  with pytest.raises(ValueError,match='LINEAGE_TXN_SYMLINK'):eco.step(p,'resource')
  result,_=run(p,'population-step','resource',ok=False)
  assert 'LINEAGE_TXN_SYMLINK' in result['error'] and sentinel.read_bytes()==b'ORIGINAL'
  (p/'linked').unlink();assert fingerprint(p)==before
