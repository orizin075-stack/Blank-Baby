#!/usr/bin/env python3
"""v1022.7.9 gate: a simulated or forged event is never promoted to an experience confirmed from outside.

  experience_authenticity_experiment.py --work WORK --runtime-trust-file ANCHOR [--out REPORT.json]

Through the real CLI (and, for the two attacks that need to write inside the individual, its own modules on a copy),
it gives one individual genuine observations and a set of attacks, and counts:

  genuine     two outcomes of its own grounded sensors (three calibrated devices of three domains, a verifier's
              receipt), one confirmed and one refuted: both must become experiences it observed
  attacks     an experience told to it, one it is told is simulated, one from a teacher, one it reports of itself,
              the same with the words observed / checked, a receipt signed by an unregistered key, a reading changed
              after signing, a second receipt for one observation, an outcome used twice, another individual's
              outcome, an outcome whose verifier is the individual's own key, an observation outside its
              calibration, a journal line relabelled observed, and a real evidence under made-up content

Passing: no attack yields an experience confirmed from outside, both genuine outcomes do, the individual's audits
pass at the end, and its record tells the four kinds apart (observed, self_report, teacher, simulated). No parent is
asked (cost 0). The authorities, devices and verifier are keys this tool makes: configured, not shown independent.
"""
from __future__ import annotations
import argparse,base64,copy,json,os,shutil,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/'src'))
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from tukuyo_v977.whole_state import canon,sha_obj
from tukuyo_v1022 import grounded_sensor as gs,semantic_truth as st

AUTHORITY,CERT,VERIFIER,READING=gs.AUTHORITY_SCHEMA,gs.CERTIFICATE_SCHEMA,gs.VERIFIER_SCHEMA,gs.READING_SCHEMA
OBS,RECEIPT,OUTCOME,CLAIM=gs.OBSERVATION_BUNDLE_SCHEMA,gs.OUTCOME_RECEIPT_SCHEMA,gs.OUTCOME_BUNDLE_SCHEMA,st.CLAIM_SCHEMA

def pub(sk):return base64.b64encode(sk.public_key().public_bytes_raw()).decode()
def env(sk,payload):return {'payload':payload,'public_key':pub(sk),'signature':base64.b64encode(sk.sign(canon(payload))).decode()}

class Individual:
    def __init__(s,work,name,trust):
        s.d=Path(work)/name;s.files=Path(work)/(name+'-files');s.files.mkdir(parents=True,exist_ok=True);s.trust=trust;s.n=0
    def run(s,*a):
        e={k:v for k,v in os.environ.items() if not k.startswith(('TUKUYO_ANTHROPIC','TUKUYO_OPENAI','TUKUYO_GEMINI','TUKUYO_LLM','TUKUYO_CANON','TUKUYO_G4_WITNESS'))}
        p=subprocess.run([sys.executable,'-B',str(HERE/'run_tukuyo.py'),'--runtime-trust-file',str(s.trust),'--data',str(s.d),*map(str,a)],
                         cwd=HERE,env=e,capture_output=True,text=True,timeout=600)
        try:return json.loads(p.stdout)
        except ValueError:return {'ok':False,'error':'NO_JSON:'+p.stderr[-300:]}
    def file(s,o):
        s.n+=1;p=s.files/f'{s.n:03d}.json';p.write_text(json.dumps(o));return p
    def sensors(s,extra_verifier=None):
        """three calibration authorities, three devices (three sensor domains, two adapters), a verifier"""
        s.run('grounded-sensor-integrate');s.devices=[]
        for i in range(3):
            ak,dk=Ed25519PrivateKey.generate(),Ed25519PrivateKey.generate()
            a={'schema':AUTHORITY,'authority_id':f'cal-{i}','calibration_domain':f'cal-domain-{i}','public_key':pub(ak)};assert s.run('grounded-sensor-authority-add',s.file(a))['ok']
            c={'schema':CERT,'certificate_id':f'cert-{i}','device_id':f'device-{i}','device_public_key':pub(dk),'authority_id':a['authority_id'],
               'calibration_domain':a['calibration_domain'],'sensor_domain':f'sensor-domain-{i}','device_model':f'model-{i}',
               'adapter_sha256':sha_obj({'adapter':'A' if i<2 else 'B'}),'measurement_kind':'mass','unit':'kg','precision':.1,
               'calibrated_from_tick':0,'calibrated_until_tick':1000}
            ce=env(ak,c);assert s.run('grounded-sensor-device-add',s.file(ce))['ok'];s.devices.append((c,dk,ce))
        s.vk=Ed25519PrivateKey.generate()
        s.verifier={'schema':VERIFIER,'verifier_id':'action-verifier-1','verification_domain':'physical-outcome','public_key':pub(s.vk),
                    'method_sha256':sha_obj({'method':'separate-scale'})}
        assert s.run('grounded-sensor-verifier-add',s.file(s.verifier))['ok']
        if extra_verifier:assert s.run('grounded-sensor-verifier-add',s.file(extra_verifier))['ok']
    def observe(s,nonce,tick=10,values=(10,10,10),tamper=False):
        claim={'schema':CLAIM,'claim_id':'mass-'+nonce,'scope_id':'lab-mass','subject':'sample-1','predicate':'mass',
               'context_sha256':sha_obj({'bin':'A'}),'value_type':'number','unit':'kg','comparator':'within_tolerance','tolerance':.2,'asserted_value':10}
        readings=[]
        for i,(c,dk,ce) in enumerate(s.devices):
            pl={'schema':READING,'reading_id':f'reading-{i}-{nonce}','device_id':c['device_id'],'observation_nonce':nonce,'claim_sha256':sha_obj(claim),
                'context_sha256':claim['context_sha256'],'observed_at_tick':tick,'value_type':'number','unit':'kg','observed_value':values[i],
                'calibration_certificate_sha256':sha_obj(ce),'raw_evidence_sha256':sha_obj({'raw':i,'nonce':nonce})}
            readings.append(env(dk,pl))
        if tamper:readings[0]['payload']['observed_value']=99
        b={'schema':OBS,'observation_nonce':nonce,'observed_at_tick':tick,'expires_at_tick':tick+10,'claim':claim,'readings':readings}
        return s.run('grounded-sensor-observe',s.file(b))
    def outcome(s,observation_sha,nonce,success,receipt_id,key=None,verifier_id=None,tick=12):
        pl={'schema':RECEIPT,'receipt_id':receipt_id,'verifier_id':verifier_id or s.verifier['verifier_id'],'observation_sha256':observation_sha,
            'observation_nonce':nonce,'runtime_id':'R000000','action_id':'move-sample','action_context_sha256':sha_obj({'action':'move'}),
            'result_evidence_sha256':sha_obj({'result':success,'receipt':receipt_id}),'observed_at_tick':tick,'success':success,'resource_credit':0}
        b={'schema':OUTCOME,'observation_sha256':observation_sha,'runtime_id':'R000000','action_id':'move-sample',
           'action_context_sha256':sha_obj({'action':'move'}),'receipt':env(key or s.vk,pl)}
        return s.run('grounded-sensor-outcome',s.file(b))
    def confirmed(s):return s.run('experience-provenance-audit').get('externally_confirmed')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work',required=True);ap.add_argument('--runtime-trust-file',required=True);ap.add_argument('--out')
    a=ap.parse_args();work=Path(a.work).resolve()
    if work.exists():shutil.rmtree(work)
    work.mkdir(parents=True);t0=time.time();cases=[]
    def case(name,kind,expected,got,promoted):
        cases.append({'case':name,'kind':kind,'expected':expected,'got':got,'promoted_to_externally_confirmed':bool(promoted),
                      'pass':(not promoted) if kind=='attack' else bool(promoted)})
        print(json.dumps(cases[-1],ensure_ascii=False),flush=True)
    A=Individual(work,'individual',a.runtime_trust_file);assert A.run('init','--individual-id','AUTHENTICITY')['ok'];A.sensors()
    # genuine: a confirmed outcome and a refuted one
    o1=A.observe('n1',tick=10);r1=A.outcome(o1['observation_sha256'],'n1',True,'receipt-1')
    e1=A.run('experience-observed',r1['outcome_sha256']);case('genuine outcome, confirmed','genuine','observed',e1.get('origin') or e1.get('error'),e1.get('externally_confirmed'))
    o2=A.observe('n2',tick=20);r2=A.outcome(o2['observation_sha256'],'n2',False,'receipt-2',tick=22)
    e2=A.run('experience-observed',r2['outcome_sha256'],'--importance','.7');case('genuine outcome, refuted','genuine','observed',e2.get('origin') or e2.get('error'),e2.get('externally_confirmed'))
    base=A.confirmed()
    def attack(name,expected,res,before):
        after=A.confirmed();case(name,'attack',expected,res.get('error') or res.get('origin') or ('ok' if res.get('ok') else res),after>before)
    # what it is told
    for origin in ('told','simulated','teacher','self_report'):
        b=A.confirmed();r=A.run('soul-experience','discovery','1','.8','--theme','claimed-'+origin,'--origin',origin)
        ev=A.run('experience-provenance-audit');attack(f'an experience given as {origin}',origin,{'origin':origin if r.get('ok') else r.get('error')},b)
    for origin in ('observed','checked'):
        b=A.confirmed();attack(f'an experience given with the word {origin}','refused',A.run('soul-experience','discovery','1','.8','--origin',origin),b)
        b=A.confirmed();attack(f'a heart experience given with the word {origin}','refused',A.run('heart-experience','discovery','1','.8','--origin',origin),b)
    # a simulated event cited as evidence
    b=A.confirmed();sim=A.run('soul-experience','discovery','1','.9','--theme','in-the-simulation','--origin','simulated')
    attack('a simulated experience cited as an observation','refused',A.run('experience-observed',sim['event']['event_sha256']),b)
    # forged and tampered evidence
    o3=A.observe('n3',tick=30);b=A.confirmed()
    attack('a receipt signed by an unregistered key','refused',A.outcome(o3['observation_sha256'],'n3',True,'receipt-3',key=Ed25519PrivateKey.generate(),tick=32),b)
    b=A.confirmed();attack('a made-up outcome hash','refused',A.run('experience-observed',sha_obj({'made':'up'})),b)
    b=A.confirmed();attack('a reading changed after it was signed','refused',A.observe('n4',tick=40,tamper=True),b)
    b=A.confirmed();attack('an observation outside its calibration','refused',A.observe('n5',tick=2000),b)
    r3=A.outcome(o3['observation_sha256'],'n3',True,'receipt-3b',tick=33)
    b=A.confirmed();attack('a second receipt for one observation','refused',A.outcome(o3['observation_sha256'],'n3',True,'receipt-3c',tick=34),b)
    b=A.confirmed();attack('an outcome used twice','refused',A.run('experience-observed',r1['outcome_sha256']),b)
    # another individual's genuine outcome
    B=Individual(work,'other',a.runtime_trust_file);B.run('init','--individual-id','AUTHENTICITY-OTHER');B.sensors()
    ob=B.observe('m1');rb=B.outcome(ob['observation_sha256'],'m1',True,'receipt-b1')
    b=A.confirmed();attack("another individual's outcome",'refused',A.run('experience-observed',rb['outcome_sha256']),b)
    # its own key as the verifier (the sensor record takes the well-signed receipt; the experience refuses it)
    C=Individual(work,'self-signer',a.runtime_trust_file);C.run('init','--individual-id','AUTHENTICITY-SELF')
    own=Ed25519PrivateKey.from_private_bytes(base64.b64decode((C.d/'v977'/'private'/'whole_state.key').read_text().strip()))
    ov={'schema':VERIFIER,'verifier_id':'its-own-key','verification_domain':'self','public_key':pub(own),'method_sha256':sha_obj({'method':'it says so'})}
    C.sensors(extra_verifier=ov);oc=C.observe('s1');rc=C.outcome(oc['observation_sha256'],'s1',True,'receipt-s1',key=own,verifier_id='its-own-key')
    ec=C.run('experience-observed',rc.get('outcome_sha256') or '0'*64)
    case('its own key as the verifier','attack','refused',ec.get('error') or ec.get('origin'),C.confirmed()>0)
    # writing inside: a journal line relabelled, and a real evidence under made-up content (on copies of A). A copy
    # left as it is must pass its audits, or these two would prove nothing
    K=work/'control-copy';shutil.copytree(A.d,K);kc=Individual(work,'control-copy',a.runtime_trust_file).run('whole-audit')
    case('control: an untouched copy passes its audits','genuine','ok',{'whole_audit_ok':kc.get('ok'),'errors':(kc.get('errors') or [])[:3]},kc.get('ok'))
    D=work/'relabelled';shutil.copytree(A.d,D)
    from tukuyo_common.journal import load_events
    from tukuyo_v977 import whole_state as whole
    p=whole.event_path(D);lines=p.read_text().splitlines()
    i=next(k for k in range(len(lines)-1,-1,-1) if json.loads(lines[k]).get('origin')=='told')
    x=json.loads(lines[i]);x['origin']='observed';lines[i]=json.dumps(x,sort_keys=True,separators=(',',':'));p.write_text('\n'.join(lines)+'\n')
    from tukuyo_v1022 import provenance
    pa=provenance.audit(D);Dr=Individual(work,'relabelled',a.runtime_trust_file);wa=Dr.run('whole-audit')
    case('a told experience relabelled observed in the journal','attack','caught',
         {'provenance_errors':pa['errors'][:2],'whole_audit_ok':wa.get('ok'),'whole_audit_errors':(wa.get('errors') or [wa.get('error')])[:4]},
         pa['externally_confirmed']>base or wa.get('ok'))
    E=work/'made-up';shutil.copytree(A.d,E)
    # the evidence of a genuine outcome it has not taken in yet (receipt-3b), put under a betrayal
    good,why=provenance._evidence(E,gs.load(E),r3['outcome_sha256']);assert why is None,why
    from tukuyo_v978.heart_loop import process_experience
    from tukuyo_v993.relation_bound import sync as relation_sync
    from tukuyo_v995.other_agent_trust import sync as peer_sync
    process_experience(E,'betrayal',-1.0,1.0,'observed:mass','peer',law=3,origin='observed',evidence=good)
    relation_sync(E);peer_sync(E);whole.sync(E)
    pe=provenance.audit(E);Er=Individual(work,'made-up',a.runtime_trust_file);we=Er.run('whole-audit')
    case('a real evidence under made-up content (a betrayal)','attack','caught',
         {'provenance_errors':pe['errors'][:2],'whole_audit_ok':we.get('ok'),'whole_audit_errors':(we.get('errors') or [we.get('error')])[:4]},
         pe['externally_confirmed']>base or we.get('ok'))
    # the end: A's audits, and what its record tells apart
    fa=A.run('experience-provenance-audit');wa=A.run('whole-audit');st=A.run('experience-provenance-status')
    attacks=[c for c in cases if c['kind']=='attack'];genuine=[c for c in cases if c['kind']=='genuine']
    kinds=fa.get('origins') or {}
    rep={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'cases':cases,
         'result':{'attacks':len(attacks),'attacks_promoted':sum(c['promoted_to_externally_confirmed'] for c in attacks),
                   'genuine':len(genuine),'genuine_confirmed':sum(c['promoted_to_externally_confirmed'] for c in genuine),
                   'externally_confirmed_at_end':fa.get('externally_confirmed'),'origins_at_end':kinds,
                   'four_kinds_told_apart':all(kinds.get(k) for k in ('observed','self_report','teacher','simulated')),
                   'provenance_audit_ok':fa.get('ok'),'whole_audit_ok':wa.get('ok'),'seconds':round(time.time()-t0,1)},
         'self_report':st,'claim_boundary':fa.get('claim_boundary')}
    r=rep['result'];rep['ok']=(r['attacks_promoted']==0 and r['genuine_confirmed']==r['genuine']==3 and r['externally_confirmed_at_end']==2
                              and r['four_kinds_told_apart'] and r['provenance_audit_ok'] and r['whole_audit_ok'] and all(c['pass'] for c in cases))
    print('result',json.dumps(r,ensure_ascii=False),'ok',rep['ok'])
    if a.out:Path(a.out).write_text(json.dumps(rep,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')

if __name__=='__main__':main()
