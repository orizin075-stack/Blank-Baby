import json,subprocess,sys,tempfile,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py'

def run(data,*args,ok=True):
    p=subprocess.run([sys.executable,'-B',str(CLI),'--data',str(data),*map(str,args)],cwd=ROOT,text=True,capture_output=True,timeout=180,
                     env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    if ok and p.returncode!=0: raise AssertionError(p.stdout+p.stderr)
    try:r=json.loads(p.stdout)
    except Exception: raise AssertionError(p.stdout+p.stderr)
    if ok and not r.get('ok',True):raise AssertionError(r)
    return r

def options_file(td):
    p=Path(td)/'social_options.json'
    p.write_text(json.dumps([
      {'id':'accept','signals':{'relationship':0.8,'trust':0.8},'themes':['collaboration'],'engages_relation':True,'relation_exposure':1.0},
      {'id':'decline','signals':{'integrity':0.5},'themes':[],'engages_relation':False,'relation_exposure':0.0}
    ]),encoding='utf-8')
    return p

def test_v993_relation_identity_changes_choice_even_when_theme_changes_and_surface_memory_is_absent():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V993-REL');opts=options_file(td)
        assert run(d,'relation-choose','peerX',opts)['chosen']=='accept'
        for _ in range(8):run(d,'soul-experience','betrayal','-0.9','0.9','--theme','broken_promise','--relation','peerX')
        rx=run(d,'relation-choose','peerX',opts);ry=run(d,'relation-choose','peerY',opts)
        assert rx['chosen']=='decline' and ry['chosen']=='accept'
        assert rx['relation_model']['scar_load']>0 and rx['relation_model']['risk']>0
        run(d,'soul-consolidate');run(d,'soul-forget-surface')
        # The offer now carries a harmless collaboration tag; peer identity still carries the scar.
        rx2=run(d,'relation-choose','peerX',opts)
        assert rx2['chosen']=='decline' and rx2['relation_model']['scar_load']==rx['relation_model']['scar_load']
        assert run(d,'relation-audit')['ok']

def test_v994_japanese_and_english_epistemic_labels_share_a_composed_domain_not_a_five_word_kind_table():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V994-LANG')
        texts=['learning','study','research','発見','新しい証拠を観察して研究する']
        for t in texts:
            r=run(d,'semantic-interpret',t)
            assert r['analysis']['features']['epistemic']>0
            assert any(x['label']=='EPISTEMIC_CONTENT' for x in r['analysis']['meaning_profile'])
        neg=run(d,'semantic-interpret','証拠を発見できなかった')
        assert neg['analysis']['features']['failure_or_negation']==1.0
        assert any(x['label']=='NEGATED_OR_FAILED_OUTCOME' for x in neg['analysis']['meaning_profile'])

def test_v994_uses_soul_vocabulary_and_replays_recorded_semantics():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V994-SOUL')
        run(d,'soul-experience','vow','0.8','0.9','--theme','星界航路','--relation','peerA')
        r=run(d,'semantic-record','星界航路の誓いを守り、真実を検証する','--relation','peerA')
        assert '星界航路' in r['analysis']['matched_soul_vocabulary']
        assert r['analysis']['features']['commitment']>0 and r['analysis']['features']['truth']>0
        assert run(d,'semantic-audit')['ok']
        p=d/'v994'/'SEMANTIC_EVENTS.json';q=json.loads(p.read_text());q['events'][0]['analysis']['features']['truth']=99;p.write_text(json.dumps(q),encoding='utf-8')
        assert not run(d,'semantic-audit',ok=False)['ok']

def test_v995_peer_history_is_separated_by_identity_and_tag_switch_does_not_reset_it():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V995-PEER');opts=options_file(td)
        for _ in range(8):run(d,'soul-experience','betrayal','-0.9','0.9','--theme','broken_promise','--relation','peerX')
        x=run(d,'peer-choose','peerX',opts);y=run(d,'peer-choose','peerY',opts)
        assert x['chosen']=='decline' and y['chosen']=='accept'
        assert x['peer_model']['peer_id']=='peerX' and y['peer_model']['peer_id']=='peerY'
        assert x['peer_model']['negative_evidence']>0 and y['peer_model']['negative_evidence']==0
        # Decision options say collaboration; the old betrayal identity remains relevant.
        assert x['claim_boundary']['tag_change_does_not_reset_peer_history'] is True

def test_v995_positive_history_repairs_trust_gradually_without_erasing_scar_floor():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V995-REPAIR')
        for _ in range(4):run(d,'soul-experience','betrayal','-0.9','0.9','--theme','broken_promise','--relation','peerX')
        before=run(d,'peer-status','--peer','peerX')['peer']
        for _ in range(10):run(d,'soul-experience','support','0.8','0.8','--theme','collaboration','--relation','peerX')
        after=run(d,'peer-status','--peer','peerX')['peer']
        assert after['trust']>before['trust']
        assert after['unresolved_harm']>0
        assert after['positive_evidence']>0 and after['negative_evidence']>0
        assert run(d,'peer-audit')['ok']

def test_v995_tamper_is_detected_and_whole_audit_covers_new_layers():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V995-AUDIT')
        run(d,'soul-experience','support','0.8','0.8','--theme','友情','--relation','peerY')
        run(d,'semantic-record','peerYとの友情と協力を大切にする','--relation','peerY')
        run(d,'peer-sync');run(d,'whole-sync')
        assert run(d,'whole-audit')['ok']
        p=d/'v995'/'OTHER_AGENT_MODELS.json';q=json.loads(p.read_text());q['peers']['peerY']['trust']=0.0;p.write_text(json.dumps(q),encoding='utf-8')
        assert not run(d,'peer-audit',ok=False)['ok']
        assert not run(d,'whole-audit',ok=False)['ok']

def test_v995_unrelated_grounded_experience_does_not_stale_relation_models():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V995-NONREL')
        run(d,'soul-experience','support','0.8','0.8','--theme','友情','--relation','peerY')
        before=run(d,'peer-status','--peer','peerY')['peer']
        run(d,'env-init','--profile','TRAIN_A','--seed','99001');run(d,'grounded-init');run(d,'grounded-step','MOVE_FORWARD')
        after=run(d,'peer-status','--peer','peerY')['peer']
        assert before==after
        run(d,'whole-sync');assert run(d,'whole-audit')['ok']
