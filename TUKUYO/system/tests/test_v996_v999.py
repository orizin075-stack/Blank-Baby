import json,subprocess,sys,tempfile,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py'

def run(data,*args,ok=True):
    p=subprocess.run([sys.executable,'-B',str(CLI),'--data',str(data),*map(str,args)],cwd=ROOT,text=True,capture_output=True,timeout=240,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    if ok and p.returncode!=0:raise AssertionError(p.stdout+p.stderr)
    try:r=json.loads(p.stdout)
    except Exception:raise AssertionError(p.stdout+p.stderr)
    if ok and not r.get('ok',True):raise AssertionError(r)
    return r

def test_v996_chat_text_reaches_heart_and_derives_social_valence_without_numeric_input():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V996-CHAT')
        before=run(d,'heart-status')['meaning_count']
        r=run(d,'conversation-ingest','peerXに裏切られた','--relation','peerX')
        after=run(d,'heart-status')['meaning_count']
        assert after==before+1
        assert r['appraisal']['derived_valence']<0 and r['appraisal']['relation']=='peerX'
        assert run(d,'peer-status','--peer','peerX')['peer']['negative_evidence']>0

def test_v997_peer_scope_auto_applies_relation_history_without_engages_relation_flag():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V997-AUTO')
        for _ in range(8):run(d,'conversation-ingest','peerXに裏切られた','--relation','peerX')
        opts=Path(td)/'opts.json';opts.write_text(json.dumps([
          {'id':'accept','signals':{'relationship':1.0,'trust':1.0},'themes':['collaboration']},
          {'id':'decline','signals':{'integrity':0.45},'themes':['caution']}
        ]),encoding='utf-8')
        x=run(d,'peer-choose','peerX',opts);y=run(d,'peer-choose','peerY',opts)
        assert x['chosen']=='decline' and y['chosen']=='accept'
        assert all(row['relation_exposure']==1.0 for row in x['scores'])
        assert all(row['auto_relation_exposure'] for row in x['scores'])

def test_v998_negation_scope_and_unlisted_epistemic_successes():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V998-SEM')
        neg=run(d,'semantic-infer','裏切られなかった')['analysis']
        assert not neg['features']['betrayal'] and any(x['label']=='NEGATED_PROPOSITION' for x in neg['meaning_profile'])
        for text in ('新しい定理を証明した','ひらめいた','謎が解けた'):
            a=run(d,'semantic-infer',text)['analysis'];assert a['primary_meaning']=='EPISTEMIC_GAIN'

def test_v999_policy_is_state_dependent_and_beats_constant_and_hand_rule_baselines():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'data';run(d,'init','--individual-id','V999-POLICY')
        r=run(d,'adaptive-policy-assay')
        assert r['wins']['always_forward']==6 and r['wins']['always_shield']==6 and r['wins']['hand_rule']==6
        assert set(r['distinct_holdout_actions'])=={'GATHER','SHIELD'}
        assert r['selected_policy']['action_diversity']>=2
        assert run(d,'adaptive-policy-audit')['ok']

def test_v999_distribution_defaults_keep_private_data_outside_signed_tree_and_install_pytest():
    req=(ROOT/'requirements.txt').read_text(encoding='utf-8');sh=(ROOT/'START_TUKUYO.sh').read_text(encoding='utf-8')
    assert 'pytest>=' in req
    assert '.tukuyo/v999_data' in sh and 'TUKUYO_v941_DATA' not in sh
