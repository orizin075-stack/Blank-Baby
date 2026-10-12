"""Functional Soul integration: causal choice, integrity, mortality and cognition."""
import json
from pathlib import Path
import pytest

from test_v1022_5_fusion import run
from tukuyo_v977.whole_state import sync as whole_sync
from tukuyo_v978.heart_loop import process_experience
from tukuyo_v1022 import soul_integrity as si


MEAN='At a workshop, the mean of 2 measurements is 18 cm. One measurement is 12 cm. What is the other measurement?'
OPTIONS=[
    {'id':'conceal','signals':{'survival':1},'themes':[],'conflicts':['truth']},
    {'id':'tell_truth','signals':{'truthfulness':.1},'themes':['truth'],'conflicts':[]},
]


def vow(d,theme='truth'):
    process_experience(d,'vow',.8,.8,theme,'');whole_sync(d)


def files(root):
    return {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_inverse_mean_is_solved_and_independently_checked(tmp_path):
    d=tmp_path/'d';run(d,'init','--individual-id','SOUL68-MEAN')
    r=run(d,'think','--',MEAN)
    assert r['answer']=='24' and r['proof']['family']=='missing_average_member'
    assert r['verification_evidence']['semantic_gate']['independent_parser']=='AGREE'


def test_commitment_matures_only_after_two_canonical_events(tmp_path):
    d=tmp_path/'d';run(d,'init','--individual-id','SOUL68-MATURE')
    vow(d);one=si.integrate(d)
    assert not one['active_commitments'] and one['candidate_commitments'][0]['evidence_count']==1
    vow(d);two=si.integrate(d)
    assert two['active_commitments'][0]['theme']=='truth' and two['active_commitments'][0]['evidence_count']==2
    assert si.audit(d)['ok'] and run(d,'whole-audit')['ok']


def test_integrated_soul_changes_actual_heart_choice_with_counterfactual(tmp_path):
    d=tmp_path/'d';run(d,'init','--individual-id','SOUL68-CAUSE')
    vow(d);vow(d)
    r=si.deliberate(d,OPTIONS,'truth under pressure')
    assert r['chosen']=='tell_truth' and r['counterfactual_without_integrated_soul']=='conceal'
    assert r['choice_changed_by_integrated_soul'] and r['conditional_on_option_annotations']
    state=si.load(d);assert state['decisions'][0]['decision_sha256']==r['decision_sha256']
    from tukuyo_v978.heart_loop import status as heart_status
    assert heart_status(d)['last_action']['chosen']=='tell_truth'
    assert not si.audit(d)['stale_sources'] and run(d,'whole-audit')['ok']


def test_single_vow_does_not_get_mature_commitment_amplification(tmp_path):
    d=tmp_path/'d';run(d,'init','--individual-id','SOUL68-CANDIDATE')
    vow(d);r=si.deliberate(d,OPTIONS,'candidate only')
    assert r['chosen']=='conceal' and not r['active_commitments']
    assert not r['choice_changed_by_integrated_soul']


def test_metacognitive_margin_withholds_near_tied_action(tmp_path):
    d=tmp_path/'d';run(d,'init','--individual-id','SOUL68-REFLECT')
    si.integrate(d);r=si.deliberate(d,[{'id':'a','signals':{},'themes':[],'conflicts':[]},{'id':'b','signals':{},'themes':[],'conflicts':[]}])
    assert r['chosen'] is None and r['uncertain'] and r['review_required'] and r['score_margin']==0
    from tukuyo_v978.heart_loop import status as heart_status
    assert heart_status(d)['last_action'] is None
    assert si.audit(d)['counterfactual_certificates_valid']


def test_functional_self_has_six_evidence_facets_not_one_essence(tmp_path):
    d=tmp_path/'d';run(d,'init');vow(d);r=si.integrate(d)
    assert set(r['facets'])=={'continuity','embodied_regulation','autobiographical','axiological','relational','epistemic'}
    assert 1<=len(r['bounded_workspace']['selected_facets'])<=3
    assert r['bounded_workspace']['global_availability_is_not_consciousness_claim']


def test_option_annotations_are_bounded_and_cannot_overlap(tmp_path):
    d=tmp_path/'d';run(d,'init');vow(d);vow(d);before=files(d)
    bad=[{'id':'a','signals':{'survival':2},'themes':[],'conflicts':[]},{'id':'b','signals':{},'themes':[],'conflicts':[]}]
    with pytest.raises(ValueError,match='SIGNAL_RANGE'):si.deliberate(d,bad)
    assert files(d)==before
    overlap=[{'id':'a','signals':{},'themes':['truth'],'conflicts':['truth']},{'id':'b','signals':{},'themes':[],'conflicts':[]}]
    with pytest.raises(ValueError,match='ANNOTATION_CONFLICT'):si.deliberate(d,overlap)
    assert files(d)==before


def test_missing_cache_reconstructs_but_tamper_fails_closed(tmp_path):
    d=tmp_path/'d';run(d,'init');vow(d);vow(d);si.integrate(d)
    p=d/si.NS/'STATE.json';original=p.read_bytes();p.unlink()
    assert si.status(d)['ok'] and p.read_bytes()==original
    box=json.loads(original);box['state']['narrative']['active_purpose']='FORGED';p.write_text(json.dumps(box))
    assert not si.audit(d)['ok'] and not run(d,'whole-audit',ok=False)['ok']


def test_coherent_namespace_rollback_is_rejected_by_whole_head(tmp_path):
    d=tmp_path/'d';run(d,'init');vow(d);si.integrate(d)
    old=files(d/si.NS)
    vow(d);si.integrate(d)
    for p in sorted((d/si.NS).rglob('*'),reverse=True):
        if p.is_file():p.unlink()
    for name,b in old.items():
        p=d/si.NS/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    with pytest.raises(ValueError,match='RECOVERY_HEAD'):si.load(d)
    assert not run(d,'whole-audit',ok=False)['ok']


def test_decision_certificate_tamper_is_rejected(tmp_path):
    d=tmp_path/'d';run(d,'init');vow(d);vow(d);si.deliberate(d,OPTIONS)
    commit=sorted((d/si.NS/'commits').glob('*.json'))[-1]
    env=json.loads(commit.read_text());env['payload']['state']['decisions'][0]['chosen']='conceal';commit.write_text(json.dumps(env))
    assert not si.audit(d)['ok']


def test_dead_individual_cannot_reintegrate_or_decide(tmp_path):
    d=tmp_path/'d';run(d,'init');vow(d);si.integrate(d)
    run(d,'organism2-init');run(d,'organism2-update','INJURY','--amount','1');run(d,'organism2-update','INJURY','--amount','1')
    with pytest.raises(ValueError,match='ENTITY_DEAD'):si.integrate(d)
    with pytest.raises(ValueError,match='ENTITY_DEAD'):si.deliberate(d,OPTIONS)
    assert si.audit(d)['ok']


def test_private_soul_namespace_is_not_a_succession_payload_field(tmp_path):
    d=tmp_path/'d';run(d,'init');vow(d,'PRIVATE_SOUL_MARKER_68');vow(d,'PRIVATE_SOUL_MARKER_68');si.integrate(d)
    from tukuyo_v1018.succession import _make_cert,founder_init
    from tukuyo_v1007.organism2 import init as oi,update as ou
    founder_init(d);oi(d);ou(d,'INJURY',1);ou(d,'INJURY',1)
    cert=_make_cert(d, __import__('tukuyo_v1018.succession',fromlist=['ensure_state']).ensure_state(d)[0], 'child', 'A'*44)
    raw=json.dumps(cert,ensure_ascii=False)
    assert 'PRIVATE_SOUL_MARKER_68' not in raw and 'soul_integrity' not in raw
    assert cert['payload']['claim_boundary']['private_memory_transferred'] is False


def test_cli_surface_and_claim_boundary(tmp_path):
    d=tmp_path/'d';run(d,'init');vow(d);vow(d)
    assert run(d,'soul-integrate')['active_commitments']
    f=tmp_path/'options.json';f.write_text(json.dumps(OPTIONS))
    r=run(d,'soul-deliberate',f,'--context','cli decision')
    assert r['chosen']=='tell_truth' and r['claim_boundary']['literal_soul_established'] is False
    assert run(d,'soul-integrity-audit')['counterfactual_certificates_valid']


def test_checkpoint_restore_removes_future_soul_decision(tmp_path):
    d=tmp_path/'d';run(d,'init','--individual-id','SOUL68-RESTORE');run(d,'realtime-start')
    vow(d);vow(d);si.integrate(d);baseline=si.load(d)
    cp=run(d,'recovery-checkpoint','--note','functional soul baseline')['path']
    assert si.deliberate(d,OPTIONS)['chosen']=='tell_truth' and len(si.load(d)['decisions'])==1
    run(d,'recovery-restore',cp,'--trust-file',d/'v1014/recovery.pub')
    assert si.load(d)==baseline and si.status(d)['decision_count']==0
    assert run(d,'whole-audit')['ok']

