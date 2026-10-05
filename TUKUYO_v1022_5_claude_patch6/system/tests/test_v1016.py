from pathlib import Path
import json,os,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'run_tukuyo.py'

def run(d,*args,ok=True):
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT/'src')}
    cmd=[sys.executable,'-B',str(RUN)]
    anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if anchor:cmd += ['--runtime-trust-file',anchor]
    cmd += ['--data',str(d),*map(str,args)]
    p=subprocess.run(cmd,cwd=ROOT,env=env,text=True,capture_output=True,timeout=240)
    try:r=json.loads(p.stdout) if p.stdout.strip() else {}
    except Exception:raise AssertionError(p.stdout+p.stderr)
    if ok and (p.returncode or not r.get('ok')):raise AssertionError((p.returncode,r,p.stderr))
    if not ok and p.returncode==0 and r.get('ok'):raise AssertionError(('expected fail',r))
    return r,p.returncode

def init(d,i):return run(d,'init','--individual-id',i)[0]

def test_v1016_init_and_empty_society_audit():
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)/'A';r=init(d,'V1016-A');assert r['version'] =='v1019'
        s,_=run(d,'society-status');assert s['version']=='v1016' and s['state']['peers']=={}
        a,_=run(d,'society-audit');assert a['ok'] and a['peer_count']==0

def test_v1016_signed_send_receive_ack_and_peer_history():
    with tempfile.TemporaryDirectory() as t:
        td=Path(t);a=td/'A';b=td/'B';init(a,'V1016-A');init(b,'V1016-B')
        pkt=td/'pkt.json';ack=td/'ack.json'
        run(a,'society-send','V1016-B','--message','公開協力メッセージ','--out',pkt)
        rb,_=run(b,'society-receive',pkt,'--ack-out',ack,'--valence','0.8','--importance','0.7','--theme','cooperation');assert rb['living']['causal_checks']['relation_bound_if_requested']
        ra,_=run(a,'society-ack',pkt,ack,'--valence','0.7','--importance','0.7','--theme','cooperation');assert ra['living']['causal_checks']['relation_bound_if_requested']
        sa,_=run(a,'society-status');sb,_=run(b,'society-status')
        assert 'V1016-B' in sa['state']['peers'] and 'V1016-A' in sb['state']['peers']
        assert sa['models']['V1016-B']['peer']['encounters']>=1 and sb['models']['V1016-A']['peer']['encounters']>=1
        assert run(a,'whole-audit')[0]['ok'] and run(b,'whole-audit')[0]['ok']

def test_v1016_three_agent_gate_private_boundary_replay_and_choice_divergence():
    with tempfile.TemporaryDirectory() as t:
        td=Path(t);a=td/'A';b=td/'B';c=td/'C'
        init(a,'V1016-A');init(b,'V1016-B');init(c,'V1016-C')
        r,_=run(a,'society-gate-assay',b,c)
        assert r['ok'];checks=r['checks']
        for k in ('three_distinct_identities','all_society_audits_pass','a_tracks_b_and_c_separately','peer_history_diverged','peer_specific_choice_diverged','private_note_not_leaked','packet_replay_blocked','signed_exchange_paths_completed'):
            assert checks[k],(k,checks)
        assert len(set(r['a_peer_choice'].values()))==2

def test_v1016_society_event_tamper_is_detected():
    with tempfile.TemporaryDirectory() as t:
        td=Path(t);a=td/'A';b=td/'B';init(a,'V1016-A');init(b,'V1016-B')
        pkt=td/'p.json';run(a,'society-send','V1016-B','--message','hello','--out',pkt)
        ev=a/'v1016/events/00000001.json';x=json.loads(ev.read_text());x['message_sha256']='0'*64;ev.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')
        r,_=run(a,'society-audit',ok=False);assert any('EVENT_CHAIN' in e or 'STATE' in e for e in r.get('errors',[])),r

def test_v1016_self_recipient_is_rejected():
    with tempfile.TemporaryDirectory() as t:
        td=Path(t);a=td/'A';init(a,'V1016-A');out=td/'self.json'
        r,_=run(a,'society-send','V1016-A','--message','self','--out',out,ok=False);assert 'SELF_RECIPIENT_FORBIDDEN' in r.get('error',''),r

def test_v1016_wrong_recipient_packet_is_rejected_without_social_state_mutation():
    with tempfile.TemporaryDirectory() as t:
        td=Path(t);a=td/'A';b=td/'B';c=td/'C';init(a,'V1016-A');init(b,'V1016-B');init(c,'V1016-C')
        pkt=td/'to-b.json';ack=td/'bad-ack.json';run(a,'society-send','V1016-B','--message','for B only','--out',pkt)
        r,_=run(c,'society-receive',pkt,'--ack-out',ack,ok=False);assert 'PACKET_WRONG_RECIPIENT' in r.get('error',''),r
        s,_=run(c,'society-status');assert s['state']['event_count']==0 and s['state']['peers']=={}
        assert run(c,'whole-audit')[0]['ok']

def test_v1016_same_peer_id_with_different_key_is_rejected():
    with tempfile.TemporaryDirectory() as t:
        td=Path(t);a=td/'A';b1=td/'B1';b2=td/'B2';init(a,'V1016-A');init(b1,'V1016-PEER');init(b2,'V1016-PEER')
        p1=td/'p1.json';a1=td/'a1.json';run(a,'society-send','V1016-PEER','--message','first peer','--out',p1);run(b1,'society-receive',p1,'--ack-out',a1);run(a,'society-ack',p1,a1)
        p2=td/'p2.json';bad=td/'bad.json';run(b2,'society-send','V1016-A','--message','impersonation','--out',p2)
        r,_=run(a,'society-receive',p2,'--ack-out',bad,ok=False);assert 'PEER_KEY_CONFLICT' in r.get('error',''),r
        assert run(a,'society-audit')[0]['ok'] and run(a,'whole-audit')[0]['ok']
