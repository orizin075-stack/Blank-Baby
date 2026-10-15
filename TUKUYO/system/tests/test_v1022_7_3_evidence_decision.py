"""Adversarial regressions; successful transfers require actual runtime evidence."""
import copy, json, os, subprocess, sys
from pathlib import Path
import pytest
from test_v1022_5_fusion import ROOT, run
from test_v1022_7_evidence_bound_soul import envelope, file_bytes
from test_v1022_7_2_grounded_sensor import setup, observation, outcome_bundle, typed_claim
from tukuyo_v1022 import grounded_sensor as gs, sensor_action as sa, sensor_decision as sd, metabolism as m
from tukuyo_v977.whole_state import sha_obj
from tukuyo_v1007 import organism2


def decide(data, obs, predecessor=None):
    return sa.decide(data, {'schema': sa.DECISION_SCHEMA, 'observation_sha256': obs['observation_sha256'], 'predecessor_sha256': predecessor})


def measured_bundle(data, devices, verifier, key, credit=700, result_values=(10,10,10), initial=None):
    initial = initial or gs.load(data)['observations'][0]
    decision = decide(data, initial)
    intent = sa.precommit(data, {'schema': sa.INTENT_SCHEMA, 'intent_id': 'intent-1',
        'decision_sha256': decision['decision_sha256'], 'runtime_id': 'R000000', 'action_id': 'move-sample',
        'action_context_sha256': sha_obj({'action':'move'}), 'expected_result': typed_claim(),
        'maximum_credit': 700, 'started_at_tick': 10, 'deadline_tick': 20})
    result = gs.observe(data, observation(devices, values=result_values, nonce='result-1', tick=12))
    row = next(r for r in gs.load(data)['observations'] if r['observation_sha256']==initial['observation_sha256'])
    bundle = outcome_bundle(data, verifier, key, success=True, credit=credit, tick=12)
    p = bundle['receipt']['payload']; p.update(schema=sa.RECEIPT_SCHEMA, intent_sha256=intent['intent_sha256'],
        result_observation_sha256=result['observation_sha256'], result_evidence_sha256=result['observation_sha256'])
    bundle['receipt'] = envelope(key,p)
    return bundle


@pytest.mark.parametrize('values,remaining,expected', [
    ((10,10,10),2,'ACT'), ((10,10,40),2,'ACQUIRE'), ((40,40,10),2,'ACQUIRE'),
    ((40,40,40),2,'ABSTAIN'), ((10,10,40),0,'ABSTAIN'), ((10.15,10.15,10.15),2,'ACQUIRE')])
def test_interval_decision_does_not_confuse_median_with_evidence(values,remaining,expected):
    obs={'claim':typed_claim(),'reading_envelopes':[{'payload':{'device_id':str(i),'observed_value':x}} for i,x in enumerate(values)]}
    sensors={str(i):{'precision':.1} for i in range(3)}
    result=sd.assess(obs,sensors,remaining)
    assert result['decision']==expected and not result['statistical_coverage_guaranteed']


def test_fresh_observation_resolves_conflict_and_links_reconsideration(tmp_path):
    d=tmp_path/'data';devices,_,_=setup(d)
    obs=gs.observe(d,observation(devices,values=(10,10,40)));first=decide(d,obs)
    assert first['assessment']['decision']=='ACQUIRE'
    later=gs.observe(d,observation(devices,nonce='reobserve',tick=11));second=decide(d,later,first['decision_sha256'])
    assert second['assessment']['decision']=='ACT' and second['assessment']['remaining_acquisitions']==1
    assert gs.audit(d)['ok'] and run(d,'whole-audit')['ok']


def test_acquisition_exhaustion_and_duplicate_decision_are_recorded(tmp_path):
    d=tmp_path/'data';devices,_,_=setup(d);parent=None
    for i in range(3):
        obs=gs.observe(d,observation(devices,values=(10,10,40),nonce=f'b-{i}',tick=10+i))
        result=decide(d,obs,parent);parent=result['decision_sha256']
    assert result['assessment']['decision']=='ABSTAIN'
    before=file_bytes(d)
    with pytest.raises(ValueError):decide(d,obs,parent)
    assert file_bytes(d)==before


def test_authority_added_after_device_cannot_reuse_its_key(tmp_path):
    d=tmp_path/'data';devices,_,_=setup(d);before=file_bytes(d)
    with pytest.raises(ValueError,match='CROSS_ROLE_KEY_REUSE'):
        gs.add_authority(d,{'schema':gs.AUTHORITY_SCHEMA,'authority_id':'role','calibration_domain':'new','public_key':devices[0][0]['device_public_key']})
    assert file_bytes(d)==before


def test_untyped_measurement_kind_cannot_support_another_predicate(tmp_path):
    d=tmp_path/'data';devices,_,_=setup(d);claim=typed_claim();claim['predicate']='not-mass';before=file_bytes(d)
    with pytest.raises(ValueError,match='READING_BINDING'):gs.observe(d,observation(devices,claim=claim))
    assert file_bytes(d)==before


def test_direct_reward_without_authorization_has_no_effect(tmp_path):
    d=tmp_path/'data';setup(d)
    run(d,'metabolism-init','--families','2','--max-age','64','--no-actions')
    before=file_bytes(d)
    with pytest.raises(ValueError,match='AUTHORIZATION_REQUIRED'):
        m.grounded_reward(d,'R000000',700,sha_obj({'arbitrary':True}))
    assert file_bytes(d)==before


@pytest.mark.parametrize('attack', ['wrong-result','over-credit','wrong-context','future-result-before-intent','runtime-changed'])
def test_signed_outcome_attacks_do_not_transfer_resource(tmp_path,attack):
    d=tmp_path/'data';devices,v,k=setup(d)
    run(d,'metabolism-init','--families','2','--max-age','64','--no-actions')
    gs.observe(d,observation(devices));bundle=measured_bundle(d,devices,v,k,result_values=(40,40,40) if attack=='wrong-result' else (10,10,10))
    p=bundle['receipt']['payload']
    if attack=='over-credit':p['resource_credit']=701
    if attack=='wrong-context':p['action_context_sha256']=bundle['action_context_sha256']=sha_obj({'wrong':True})
    if attack=='future-result-before-intent':p['result_observation_sha256']=p['result_evidence_sha256']=p['observation_sha256']
    if attack=='runtime-changed':m.step(d,1)
    bundle['receipt']=envelope(k,p);before=file_bytes(d)
    with pytest.raises(ValueError):gs.apply_outcome(d,bundle)
    assert file_bytes(d)==before


def test_credit_is_receipt_bound_and_does_not_advance_age(tmp_path):
    d=tmp_path/'data';devices,v,k=setup(d)
    run(d,'metabolism-init','--families','2','--max-age','4','--reservoir','50000','--no-actions')
    gs.observe(d,observation(devices));bundle=measured_bundle(d,devices,v,k)
    age=organism2.load(m.child(d,'R000000')).get('metabolic_age',0)
    result=gs.apply_outcome(d,bundle)
    assert result['metabolism_result']['paid']==700
    assert organism2.load(m.child(d,'R000000')).get('metabolic_age',0)==age
    before=file_bytes(d)
    with pytest.raises(ValueError):m.grounded_reward(d,'R000000',700,sha_obj(bundle['receipt']))
    assert file_bytes(d)==before
    assert m.audit(d)['ok'] and gs.audit(d)['ok'] and run(d,'whole-audit')['ok']


@pytest.mark.parametrize('point', ['sensor:after_outcome_stage','sensor:after_reward','lineage:after_prepare'])
def test_crash_between_authorization_and_transfer_is_atomic(tmp_path,point):
    d=tmp_path/'data';devices,v,k=setup(d)
    run(d,'metabolism-init','--families','2','--max-age','64','--reservoir','50000','--no-actions')
    gs.observe(d,observation(devices));bundle=measured_bundle(d,devices,v,k)
    path=tmp_path/'outcome.json';path.write_text(json.dumps(bundle));before=m.status(d)
    command=[sys.executable,'-B',str(ROOT/'run_tukuyo.py'),'--runtime-trust-file',os.environ['TUKUYO_TEST_RUNTIME_ANCHOR'],
             '--data',str(d),'grounded-sensor-outcome',str(path)]
    process=subprocess.run(command,env={**os.environ,'TUKUYO_CRASH_POINT':point,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=240)
    assert process.returncode in (-9,137), process.stdout+process.stderr
    assert run(d,'grounded-sensor-audit')['ok'] and run(d,'metabolism-audit')['ok'] and run(d,'whole-audit')['ok']
    after=m.status(d);committed=point=='lineage:after_prepare'
    assert after['reservoir']==before['reservoir']-(700 if committed else 0)
    assert after['living_energy']==before['living_energy']+(700 if committed else 0)
    assert gs.status(d)['outcome_count']==int(committed)


def test_independent_verifier_handles_refutation_without_ecology(tmp_path):
    d=tmp_path/'data';devices,v,k=setup(d);gs.observe(d,observation(devices))
    gs.apply_outcome(d,outcome_bundle(d,v,k))
    process=subprocess.run([sys.executable,'-B',str(ROOT/'tools/v1022_7_2_grounded_verifier.py'),'--data',str(d)],capture_output=True,text=True)
    assert process.returncode==0,process.stdout+process.stderr
