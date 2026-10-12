"""Experience must be bound to acted episodes, authors and exact context."""
import copy
import json
import pytest
from test_v1022_5_fusion import run
from test_v1022_7_evidence_bound_soul import setup, envelope, file_bytes
from tukuyo_v977.whole_state import sha_obj
from tukuyo_v1022 import evidence_bound_soul as es, reflective_soul as rs
from tukuyo_v1022 import soul_experience_learning as learning

OPTIONS = [
    {'id':'fast_gain','signals':{'survival':.15},'themes':[],'conflicts':[]},
    {'id':'patient_gain','signals':{},'themes':[],'conflicts':[]}]
EFFECTS = {
    'fast_gain':{'self_wellbeing':.6,'others_wellbeing':.8,'future_self':.8,'truth_consistency':.8,'bodily_cost':0,'uncertainty':0},
    'patient_gain':{'self_wellbeing':.55,'others_wellbeing':.55,'future_self':.55,'truth_consistency':.55,'bodily_cost':0,'uncertainty':0}}
CONTEXT = 'repeatable-local-work'

def decide(data, witnesses, n, context=CONTEXT, options=None):
    options=copy.deepcopy(options or OPTIONS)
    assessments=[envelope(key, {'schema':es.ASSESSMENT_SCHEMA,'assessment_id':f'a-{n}-{i}',
        'observer_id':observer,'options_sha256':sha_obj(options),'context_sha256':sha_obj(context),
        'measurement_kind':'bounded_evaluator','evidence_sha256':sha_obj({'assessment':n,'source':i}),
        'effects_by_option':copy.deepcopy(EFFECTS)}) for i,(observer,key) in enumerate(witnesses)]
    return es.deliberate(data,{'schema':es.BUNDLE_SCHEMA,'context':context,'options':options,'assessments':assessments})

def outcome(witness, decision, n, i, **changes):
    observer,key=witness
    p={'schema':es.ATTESTATION_SCHEMA,'attestation_id':f'o-{n}-{i}','observer_id':observer,
        'decision_sha256':decision['decision_sha256'],'chosen':decision['chosen'],'measurement_kind':'bounded_evaluator',
        'evidence_sha256':sha_obj({'episode':n,'source':i}),'source_kind':'direct_observation',
        'self_wellbeing':-1,'others_wellbeing':-1,'future_self':-1,'truth_consistency':-1,'bodily_cost':.8,
        'surprise':0,'confidence':.9,'note':'synthetic fixture, external truth not established'}
    p.update(changes);return envelope(key,p)

def train(data,witnesses,count=2):
    decisions=[]
    for n in range(count):
        d=decide(data,witnesses,n);assert d['chosen']=='fast_gain'
        for i,w in enumerate(witnesses):es.attest(data,outcome(w,d,n,i))
        decisions.append(d)
    return decisions

def test_signed_repeated_failure_changes_actual_choice_without_rewriting_history(tmp_path):
    d=tmp_path/'d';_,w=setup(d);train(d,w)
    original=copy.deepcopy(es.load(d)['decisions'])
    r=decide(d,w,2)
    assert r['chosen']=='patient_gain'
    assert r['experience_learning']['options']['fast_gain']['eligible_episode_count']==2
    assert r['experience_learning']['options']['fast_gain']['cases'][0]['mean_absolute_prediction_error']>1
    assert es.load(d)['decisions'][:2]==original
    from tukuyo_v978.heart_loop import status
    assert status(d)['last_action']['chosen']=='patient_gain'
    assert es.audit(d)['ok'] and run(d,'whole-audit')['ok']

def test_one_replicated_episode_does_not_generalize(tmp_path):
    d=tmp_path/'d';_,w=setup(d);train(d,w,1)
    r=decide(d,w,1)
    assert r['chosen']=='fast_gain'
    assert r['experience_learning']['options']['fast_gain']['status']=='WAIT_FOR_REPLICATION'

@pytest.mark.parametrize('change', ['context','signal','theme'])
def test_lesson_does_not_spill_to_unrelated_context_or_option(tmp_path,change):
    d=tmp_path/'d';_,w=setup(d);train(d,w)
    opts=copy.deepcopy(OPTIONS);context=CONTEXT
    if change=='context':context='different-local-work'
    if change=='signal':opts[0]['signals']['survival']=.16
    if change=='theme':opts[0]['themes']=['new-theme']
    r=decide(d,w,2,context,opts)
    assert r['chosen']=='fast_gain'
    assert r['experience_learning']['options']['fast_gain']['eligible_episode_count']==0

def test_invented_observers_cannot_calibrate_evidence_bound_choice(tmp_path):
    d=tmp_path/'d';_,w=setup(d);first=decide(d,w,0)
    profile=copy.deepcopy(first['profile_used'])
    for i in range(3):
        rs.reflect(d,first['reflective_decision_sha256'],{'evidence_id':f'fake-{i}','observer_id':f'invented-{i}',
            'source_kind':'direct_observation','self_wellbeing':-1,'others_wellbeing':-1,'future_self':-1,
            'truth_consistency':-1,'bodily_cost':1,'surprise':1,'confidence':1,'note':'unsigned caller claim'})
    assert rs.load(d)['profile']!=profile  # legacy scenario remains explicitly labelled
    second=decide(d,w,1)
    assert second['profile_used']==profile and second['chosen']==first['chosen']
    assert second['experience_learning']['options']['fast_gain']['eligible_episode_count']==0

@pytest.mark.parametrize('case',['one_witness_repeated','two_domains','low_confidence','self_report','disagreement'])
def test_insufficient_or_disputed_outcomes_never_become_lessons(tmp_path,case):
    d=tmp_path/'d';_,w=setup(d)
    for n in range(2):
        dec=decide(d,w,n)
        for i in range(3):
            witness=w[0] if case=='one_witness_repeated' else w[i%2] if case=='two_domains' else w[i]
            changes={}
            if case=='low_confidence' and i==2:changes['confidence']=.4
            if case=='self_report':changes['source_kind']='self_report'
            if case=='disagreement' and i==2:changes['future_self']=1
            es.attest(d,outcome(witness,dec,n,i,**changes))
    result=decide(d,w,2)
    z=result['experience_learning']['options']['fast_gain']
    assert result['chosen']=='fast_gain' and z['eligible_episode_count']==0
    assert len(z['excluded_cases'])==2

def test_old_certificates_are_readable_and_new_learning_is_append_only(tmp_path):
    d=tmp_path/'d';_,w=setup(d);decide(d,w,0)
    old=copy.deepcopy(es.load(d));old['decisions'][0].pop('experience_learning')
    old['decisions'][0]['decision_sha256']=es._hash_row(old['decisions'][0],'decision_sha256')
    old['decision_head_sha256']=old['decisions'][0]['decision_sha256']
    es.validate(old)

def test_learning_certificate_cannot_use_future_outcomes(tmp_path):
    d=tmp_path/'d';_,w=setup(d);train(d,w)
    state=es.load(d);first=copy.deepcopy(state['decisions'][0]['experience_learning'])
    first['attestation_frontier_count']=len(state['attestations'])
    with pytest.raises(ValueError,match='FUTURE_EPISODE'):learning.replay_prefix(state,0,first)

def test_signed_journal_tamper_cache_loss_and_coherent_rollback(tmp_path):
    d=tmp_path/'d';_,w=setup(d);train(d,w)
    old=file_bytes(d/es.NS);decide(d,w,2)
    cache=d/es.NS/'STATE.json';raw=cache.read_bytes();cache.unlink()
    assert es.load(d) and cache.read_bytes()==raw
    box=json.loads(raw);box['state']['decisions'][-1]['experience_learning']['applied_effects']['fast_gain']['future_self']=1
    cache.write_text(json.dumps(box));assert not es.audit(d)['ok'];cache.write_bytes(raw)
    for p in sorted((d/es.NS).rglob('*'),reverse=True):
        if p.is_file():p.unlink()
    for name,value in old.items():
        p=d/es.NS/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(value)
    before=file_bytes(d)
    with pytest.raises(ValueError,match='RECOVERY_HEAD'):es.load(d)
    assert file_bytes(d)==before

def test_private_lessons_do_not_leak_to_successor_and_dead_cannot_learn(tmp_path):
    d=tmp_path/'d';_,w=setup(d);train(d,w);decide(d,w,2,context=CONTEXT)
    from tukuyo_v1018.succession import founder_init,ensure_state,_make_cert
    from tukuyo_v1007.organism2 import init,update
    founder_init(d);init(d);update(d,'INJURY',1);update(d,'INJURY',1)
    cert=_make_cert(d,ensure_state(d)[0],'child','A'*44)
    raw=json.dumps(cert);assert CONTEXT not in raw and 'experience_learning' not in raw
    before=file_bytes(d)
    with pytest.raises(ValueError,match='ENTITY_DEAD'):decide(d,w,3)
    assert file_bytes(d)==before

def test_restore_removes_future_lesson_and_replays_decision(tmp_path):
    d=tmp_path/'d';_,w=setup(d);train(d,w,1);run(d,'realtime-start')
    baseline=copy.deepcopy(es.load(d));cp=run(d,'recovery-checkpoint','--note','one episode')['path']
    dec=decide(d,w,1)
    for i,v in enumerate(w):es.attest(d,outcome(v,dec,1,i))
    assert decide(d,w,2)['chosen']=='patient_gain'
    run(d,'recovery-restore',cp,'--trust-file',d/'v1014/recovery.pub')
    assert es.load(d)==baseline
    assert decide(d,w,1)['chosen']=='fast_gain'
    assert run(d,'whole-audit')['ok']

def test_soul_cli_keeps_existing_heart_in_sync_without_double_event(tmp_path):
    d=tmp_path/'d';run(d,'init')
    run(d,'heart-experience','learning','.8','.8','--theme','initial')
    from tukuyo_v977.whole_state import load_soul
    from tukuyo_v978.heart_loop import load as heart_load
    before=load_soul(d)['update_seq']
    h=copy.deepcopy(heart_load(d))
    r=run(d,'soul-experience','vow','.8','.8','--theme','truth')
    assert r['event']['kind']=='vow' and r['soul']['update_seq']==before+1
    current=heart_load(d)
    for key in ('emotion','value_bias','active_goal','episodic_meanings'):
        assert current[key]==h[key]
    assert run(d,'heart-audit')['ok'] and run(d,'whole-audit')['ok']

def test_heart_reference_sync_refuses_unbound_fake_event_without_mutation(tmp_path):
    d=tmp_path/'d';run(d,'init');run(d,'heart-experience','learning','.8','.8')
    from tukuyo_v978.heart_loop import sync_soul_reference
    before=file_bytes(d)
    with pytest.raises(ValueError,match='REFERENCE_SOURCE'):sync_soul_reference(d,{'kind':'forged'})
    assert file_bytes(d)==before

def test_separate_verifier_replays_and_rejects_fake_learning_even_if_row_rehashed(tmp_path):
    import importlib.util
    from test_v1022_5_fusion import ROOT
    import sys
    sys.path.insert(0,str(ROOT/'tools'))
    import v1022_7_7_experience_verifier as raw
    d=tmp_path/'d';_,w=setup(d);train(d,w);decide(d,w,2)
    assert raw.verify(d)['ok']
    forged=copy.deepcopy(es.load(d));row=forged['decisions'][-1]
    row['experience_learning']['options']['fast_gain']['correction']['future_self']=.6
    row['decision_sha256']=es._hash_row(row,'decision_sha256')
    forged['decision_head_sha256']=row['decision_sha256']
    with pytest.raises(ValueError,match='EXPERIENCE_REPLAY'):raw.replay(forged,rs.load(d))
