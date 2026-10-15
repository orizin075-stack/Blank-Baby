"""Origin classes must affect actual learning, not only report labels."""
import copy,json
import base64
from pathlib import Path
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from test_v1022_7_evidence_bound_soul import setup,envelope,public,file_bytes
from test_v1022_7_7_experiential_soul import decide,outcome
from test_v1022_5_fusion import run
from tukuyo_v1022 import experience_provenance as pv,evidence_bound_soul as es
from tukuyo_v977 import whole_state as W

def fixture(root,scope='simulation',origin='simulation',count=3,same_domain=False):
    authorities,witnesses=setup(root);pv.integrate(root,scope,'world-one');sources=[]
    for i in range(count):
        key=Ed25519PrivateKey.generate();authority,issuer=authorities[0 if same_domain else i]
        kind='sensor_reading' if origin=='external_observation' else 'bounded_evaluator'
        p={'schema':pv.SOURCE,'source_id':f'source-{i}','authority_id':authority['authority_id'],'source_class':origin,'environment_id':'world-one','measurement_kind':kind,'producer_public_key':public(key)}
        pv.add_source(root,envelope(issuer,p));sources.append((p,key))
    return authorities,witnesses,sources

def pair(root,witness,source,decision,n,i,raw=None):
    s,key=source;state=pv.load(root)
    values={'self_wellbeing':-1,'others_wellbeing':-1,'future_self':-1,'truth_consistency':-1,'bodily_cost':.8}
    p={'schema':pv.REPORT,'report_id':f'report-{n}-{s["source_id"]}','source_id':s['source_id'],'source_class':s['source_class'],
       'environment_id':'world-one','measurement_kind':s['measurement_kind'],'individual_id':state['identity']['individual_id'],
       'policy_sha256':state['policy_sha256'],'decision_sha256':decision['decision_sha256'],'chosen':decision['chosen'],
       'raw_evidence':raw if raw is not None else {'episode':n,'source':s['source_id'],'outcome':'failure'},'outcomes':values}
    report=envelope(key,p)
    a=outcome(witness,decision,n,i,measurement_kind=s['measurement_kind'],evidence_sha256=pv.observer_evidence(report,witness[0]),source_kind='self_report' if s['source_class']=='self_report' else 'external_report' if s['source_class']=='teacher' else 'direct_observation')
    return a,report

def train(root,witnesses,sources,same_source=False):
    choices=[]
    for n in range(2):
        d=decide(root,witnesses,n);choices.append(d['chosen'])
        for i,w in enumerate(witnesses):
            a,r=pair(root,w,sources[0 if same_source else i],d,n,i);pv.attest(root,a,r)
    d=decide(root,witnesses,2);choices.append(d['chosen']);return choices,d

@pytest.mark.parametrize('scope,origin',[('simulation','simulation'),('teacher','teacher'),('external_channel','external_observation')])
def test_matching_origin_changes_actual_choice_after_two_episodes(tmp_path,scope,origin):
    root=tmp_path/'d';_,w,s=fixture(root,scope,origin);choices,d=train(root,w,s)
    assert choices==['fast_gain','fast_gain','patient_gain']
    assert d['experience_learning']['schema']==pv.LEARNING and d['experience_learning']['options']['fast_gain']['eligible_episode_count']==2
    assert d['experience_learning']['experience_scope']==scope and not pv.status(root)['physical_truth_verified']
    assert es.audit(root)['ok'] and pv.audit(root)['ok'] and W.audit(root)['ok']

@pytest.mark.parametrize('scope,origin',[('external_channel','simulation'),('external_channel','teacher'),('external_channel','self_report'),('simulation','external_observation'),('teacher','simulation')])
def test_wrong_origin_never_becomes_experience_for_another_scope(tmp_path,scope,origin):
    root=tmp_path/'d';_,w,s=fixture(root,scope,origin);choices,d=train(root,w,s)
    assert choices==['fast_gain']*3 and d['experience_learning']['options']['fast_gain']['eligible_episode_count']==0
    assert pv.audit(root)['ok'] and W.audit(root)['ok']

def test_three_observers_forwarding_one_teacher_do_not_count_as_three_origins(tmp_path):
    root=tmp_path/'d';_,w,s=fixture(root,'teacher','teacher',count=1);choices,d=train(root,w,s,True)
    assert choices==['fast_gain']*3 and d['experience_learning']['options']['fast_gain']['eligible_episode_count']==0
    assert pv.status(root)['bindings']==6 and pv.status(root)['sources']==1

def test_three_producer_keys_in_one_configured_source_domain_are_not_three_domains(tmp_path):
    root=tmp_path/'d';_,w,s=fixture(root,same_domain=True);choices,d=train(root,w,s)
    assert choices==['fast_gain']*3 and d['experience_learning']['options']['fast_gain']['eligible_episode_count']==0

def test_legacy_signed_but_unclassified_outcomes_are_not_adopted_by_strict_learning(tmp_path):
    root=tmp_path/'d';_,w,_=fixture(root)
    for n in range(2):
        d=decide(root,w,n)
        for i,v in enumerate(w):es.attest(root,outcome(v,d,n,i))
    result=decide(root,w,2);assert result['chosen']=='fast_gain'
    assert result['experience_learning']['options']['fast_gain']['eligible_episode_count']==0 and pv.status(root)['bindings']==0

@pytest.mark.parametrize('attack',['origin','raw','outcome','signature','observer_digest','policy'])
def test_forged_or_misbound_packet_refused_without_mutation(tmp_path,attack):
    root=tmp_path/'d';_,w,s=fixture(root);d=decide(root,w,0);a,r=pair(root,w[0],s[0],d,0,0)
    if attack=='origin':r['payload']['source_class']='external_observation';r=envelope(s[0][1],r['payload'])
    if attack=='raw':r['payload']['raw_evidence']['outcome']='success'
    if attack=='outcome':r['payload']['outcomes']['future_self']=1;r=envelope(s[0][1],r['payload'])
    if attack=='signature':r=envelope(Ed25519PrivateKey.generate(),r['payload'])
    if attack=='observer_digest':a['payload']['evidence_sha256']='1'*64;a=envelope(w[0][1],a['payload'])
    if attack=='policy':r['payload']['policy_sha256']='2'*64;r=envelope(s[0][1],r['payload'])
    before=file_bytes(root)
    with pytest.raises(ValueError,match='PROVENANCE'):pv.attest(root,a,r)
    assert file_bytes(root)==before

def test_same_raw_report_cannot_be_replayed_for_a_new_acted_episode(tmp_path):
    root=tmp_path/'d';_,w,s=fixture(root);raw={'one_measurement':'unchanged'}
    d=decide(root,w,0);a,r=pair(root,w[0],s[0],d,0,0,raw);pv.attest(root,a,r)
    next_d=decide(root,w,1);a,r=pair(root,w[0],s[0],next_d,1,0,raw);before=file_bytes(root)
    with pytest.raises(ValueError,match='RAW_EVIDENCE_REPLAY'):pv.attest(root,a,r)
    assert file_bytes(root)==before

def test_policy_source_registry_and_trust_registry_are_sealed(tmp_path):
    root=tmp_path/'d';authorities,w,s=fixture(root);decide(root,w,0);before=file_bytes(root)
    with pytest.raises(ValueError,match='POLICY_IMMUTABLE'):pv.integrate(root,'external_channel','world-one')
    with pytest.raises(ValueError,match='SOURCES_SEALED'):pv.add_source(root,envelope(authorities[0][1],s[0][0]))
    with pytest.raises(ValueError,match='TRUST_REGISTRY_SEALED'):es.add_authority(root,authorities[0][0])
    assert file_bytes(root)==before

def test_source_certificate_cannot_change_environment_or_reuse_an_observer_key(tmp_path):
    root=tmp_path/'d';a,w,s=fixture(root);p=copy.deepcopy(s[0][0]);p['source_id']='other';p['producer_public_key']=public(Ed25519PrivateKey.generate());p['environment_id']='different';before=file_bytes(root)
    with pytest.raises(ValueError,match='ENVIRONMENT'):pv.add_source(root,envelope(a[0][1],p))
    p['environment_id']='world-one';p['producer_public_key']=public(w[0][1])
    with pytest.raises(ValueError,match='ROLE_COLLISION'):pv.add_source(root,envelope(a[0][1],p))
    assert file_bytes(root)==before

def test_cache_loss_recovers_and_coherent_provenance_rollback_is_refused(tmp_path):
    root=tmp_path/'d';_,w,s=fixture(root);choices,d=train(root,w,s);path=root/pv.NS/'STATE.json';data=path.read_bytes();path.unlink();assert pv.audit(root)['ok'] and path.read_bytes()==data
    old=copy.deepcopy(pv.load(root));before_names={p.name for p in (root/pv.NS/'commits').glob('*.json')}
    a,r=pair(root,w[0],s[0],d,3,0);pv.attest(root,a,r)
    for f in (root/pv.NS/'commits').glob('*.json'):
        if f.name not in before_names:f.unlink()
    path.write_bytes(data);before=file_bytes(root)
    with pytest.raises(ValueError,match='RECOVERY_HEAD'):decide(root,w,4)
    assert file_bytes(root)==before

def alias(pub):
    alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    assert pub[-1]=='='
    value=pub[:-2]+alphabet[alphabet.index(pub[-2])+1]+'='
    assert value!=pub and base64.b64decode(value,validate=True)==base64.b64decode(pub,validate=True)
    return value

@pytest.mark.parametrize('role',['observer','whole','producer'])
def test_alternate_base64_spelling_cannot_bypass_key_roles_or_duplicate_source_gate(tmp_path,role):
    root=tmp_path/'d';a,w,s=fixture(root);p=copy.deepcopy(s[0][0]);p['source_id']='alias-source'
    pub=public(w[0][1]) if role=='observer' else W._key_paths(root)[1].read_text().strip() if role=='whole' else s[0][0]['producer_public_key']
    p['producer_public_key']=alias(pub);before=file_bytes(root)
    with pytest.raises(ValueError,match='ROLE_COLLISION|DUPLICATE_PRODUCER'):pv.add_source(root,envelope(a[0][1],p))
    assert file_bytes(root)==before

def test_pre_policy_acted_decision_cannot_be_relabelled_as_new_verified_origin(tmp_path):
    root=tmp_path/'d';authorities,w=setup(root);old=decide(root,w,0);pv.integrate(root,'simulation','world-one')
    k=Ed25519PrivateKey.generate();p={'schema':pv.SOURCE,'source_id':'source-0','authority_id':authorities[0][0]['authority_id'],'source_class':'simulation','environment_id':'world-one','measurement_kind':'bounded_evaluator','producer_public_key':public(k)}
    pv.add_source(root,envelope(authorities[0][1],p));a,r=pair(root,w[0],(p,k),old,0,0);before=file_bytes(root)
    with pytest.raises(ValueError,match='HISTORICAL'):pv.attest(root,a,r)
    assert file_bytes(root)==before

def test_independent_verifier_replays_origin_filters_and_choices(tmp_path):
    root=tmp_path/'d';_,w,s=fixture(root);train(root,w,s)
    import sys
    from test_v1022_5_fusion import ROOT
    sys.path.insert(0,str(ROOT/'tools'))
    import v1022_7_9_experience_verifier as raw
    r=raw.verify(root);assert r['ok'],r
    assert r['strict_decisions_replayed']==3 and r['producer_reports_bound']==6 and not r['physical_truth_verified']
    cache=json.loads((root/pv.NS/'STATE.json').read_text());cache['state']['bindings'][0]['report']['payload']['raw_evidence']['outcome']='forged'
    (root/pv.NS/'STATE.json').write_text(json.dumps(cache))
    assert not raw.verify(root)['ok']

def test_private_origin_reports_are_not_inherited_and_dead_cannot_attest(tmp_path):
    root=tmp_path/'d';_,w,s=fixture(root);_,d=train(root,w,s)
    from tukuyo_v1018.succession import founder_init,ensure_state,_make_cert
    from tukuyo_v1007.organism2 import init,update
    founder_init(root);init(root);update(root,'INJURY',1);update(root,'INJURY',1)
    cert=_make_cert(root,ensure_state(root)[0],'child','A'*44);raw=json.dumps(cert)
    assert pv.NS not in raw and 'provenance_snapshot' not in raw and 'producer_reports' not in raw
    before=file_bytes(root);a,r=pair(root,w[0],s[0],d,3,0)
    with pytest.raises(ValueError,match='ENTITY_DEAD'):pv.attest(root,a,r)
    assert file_bytes(root)==before

def test_restore_removes_future_origin_bindings_and_decisions(tmp_path):
    root=tmp_path/'d';_,w,s=fixture(root);d=decide(root,w,0);run(root,'realtime-start');run(root,'realtime-tick')
    cp=run(root,'recovery-checkpoint');before=copy.deepcopy(pv.load(root))
    for i,v in enumerate(w):a,r=pair(root,v,s[i],d,0,i);pv.attest(root,a,r)
    decide(root,w,1)
    run(root,'recovery-restore',cp['path'],'--trust-file',root/'v1014/recovery.pub')
    assert pv.load(root)==before and pv.audit(root)['ok'] and run(root,'whole-audit')['ok']

def test_prepared_origin_transaction_crash_redoes_and_binds_once(tmp_path):
    from test_v1019_1 import crash
    root=tmp_path/'d';_,w,s=fixture(root);d=decide(root,w,0);a,r=pair(root,w[0],s[0],d,0,0)
    af=tmp_path/'attestation.json';rf=tmp_path/'report.json';af.write_text(json.dumps(a));rf.write_text(json.dumps(r))
    crash(root,'lineage:after_prepare','soul-provenance-attest',af,rf)
    assert run(root,'soul-provenance-audit')['ok'] and pv.status(root)['bindings']==1
    assert len(es.load(root)['attestations'])==1 and run(root,'whole-audit')['ok']
