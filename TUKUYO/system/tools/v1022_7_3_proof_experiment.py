#!/usr/bin/env python3
"""Fresh CLI experiment with synthetic signed measurements and actual runtimes."""
import argparse, base64, hashlib, json, os, subprocess, sys
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def main():
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--trust',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    release=Path(__file__).resolve().parents[1];data=Path(a.data).resolve();sys.path.insert(0,str(release/'src'))
    from tukuyo_v1022 import grounded_sensor as gs, sensor_action as sa, metabolism as m
    from tukuyo_v977 import whole_state as w
    from tukuyo_v1007 import organism2
    results={};inputs=data.parent/(data.name+'_public_inputs');inputs.mkdir(exist_ok=True)
    def public(k):return base64.b64encode(k.public_key().public_bytes_raw()).decode()
    def signed(k,v):return {'payload':v,'public_key':public(k),'signature':base64.b64encode(k.sign(w.canon(v))).decode()}
    def run(*args):
        proc=subprocess.run([sys.executable,'-B',str(release/'run_tukuyo.py'),'--runtime-trust-file',a.trust,'--data',str(data),*map(str,args)],
            env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=240)
        body=json.loads(proc.stdout)
        if proc.returncode or not body.get('ok'):raise RuntimeError(str(body)+proc.stderr)
        return body
    count=0
    def json_command(command,value):
        nonlocal count
        count+=1;path=inputs/f'{count:03d}-{command}.json';path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
        return run(command,path)
    def fingerprint():return {str(x.relative_to(data)):hashlib.sha256(x.read_bytes()).hexdigest() for x in data.rglob('*') if x.is_file()}
    run('init','--individual-id','V1022-7-3-FRESH-PROOF');run('grounded-sensor-integrate')
    devices=[]
    for i in range(3):
        ck,dk=Ed25519PrivateKey.generate(),Ed25519PrivateKey.generate()
        auth={'schema':gs.AUTHORITY_SCHEMA,'authority_id':f'cal-{i}','calibration_domain':f'cal-{i}','public_key':public(ck)}
        json_command('grounded-sensor-authority-add',auth)
        cert={'schema':gs.CERTIFICATE_SCHEMA,'certificate_id':f'cert-{i}','device_id':f'sensor-{i}','device_public_key':public(dk),
            'authority_id':f'cal-{i}','calibration_domain':f'cal-{i}','sensor_domain':f'sensor-domain-{i}','device_model':f'model-{i}',
            'adapter_sha256':w.sha_obj({'adapter':i%2}),'measurement_kind':'mass','unit':'kg','precision':.1,
            'calibrated_from_tick':0,'calibrated_until_tick':1000}
        env=signed(ck,cert);json_command('grounded-sensor-device-add',env);devices.append((cert,dk,env))
    key=Ed25519PrivateKey.generate();verifier={'schema':gs.VERIFIER_SCHEMA,'verifier_id':'outcome-meter','verification_domain':'separate-role',
        'public_key':public(key),'method_sha256':w.sha_obj({'method':'result-measurement-v3'})}
    json_command('grounded-sensor-verifier-add',verifier)
    context=w.sha_obj({'sample':'A','quantity':'mass'})
    claim={'schema':gs.truth.CLAIM_SCHEMA,'claim_id':'mass-A','scope_id':'proof','subject':'sample-A','predicate':'mass','context_sha256':context,
        'value_type':'number','unit':'kg','comparator':'within_tolerance','tolerance':.2,'asserted_value':10}
    def observe(nonce,tick,values):
        readings=[]
        for i,((device,k,cert),value) in enumerate(zip(devices,values)):
            readings.append(signed(k,{'schema':gs.READING_SCHEMA,'reading_id':f'{nonce}-{i}','device_id':device['device_id'],
                'observation_nonce':nonce,'claim_sha256':w.sha_obj(claim),'context_sha256':context,'observed_at_tick':tick,'value_type':'number',
                'unit':'kg','observed_value':value,'calibration_certificate_sha256':w.sha_obj(cert),
                'raw_evidence_sha256':w.sha_obj({'nonce':nonce,'device':i,'value':value})}))
        return json_command('grounded-sensor-observe',{'schema':gs.OBSERVATION_BUNDLE_SCHEMA,'observation_nonce':nonce,
            'observed_at_tick':tick,'expires_at_tick':tick+10,'claim':claim,'readings':readings})
    def decide(obs,parent=None):return json_command('grounded-sensor-decide',{'schema':sa.DECISION_SCHEMA,'observation_sha256':obs['observation_sha256'],'predecessor_sha256':parent})
    first=observe('conflict',10,[10,10,40]);decision1=decide(first)
    second=observe('additional',11,[10,10,10]);decision2=decide(second,decision1['decision_sha256'])
    results['reconsideration']={'initial':decision1,'after_additional_measurement':decision2}
    run('metabolism-init','--families','2','--reservoir','80000','--regeneration','1800','--max-age','4')
    before=fingerprint()
    try:m.grounded_reward(data,'R000000',700,w.sha_obj({'arbitrary':True}));rejected=False
    except ValueError:rejected=True
    results['direct_reward_rejected']=rejected;results['direct_rejection_bytes_unchanged']=before==fingerprint()
    intent=json_command('grounded-sensor-precommit',{'schema':sa.INTENT_SCHEMA,'intent_id':'move-1','decision_sha256':decision2['decision_sha256'],
        'runtime_id':'R000000','action_id':'move-sample','action_context_sha256':w.sha_obj({'action':'move-sample'}),
        'expected_result':claim,'maximum_credit':700,'started_at_tick':11,'deadline_tick':20})
    result=observe('result',12,[10,10,10]);before=m.status(data);age=organism2.load(m.child(data,'R000000')).get('metabolic_age',0)
    initial=gs.load(data)['observations'][1]
    payload={'schema':sa.RECEIPT_SCHEMA,'receipt_id':'paid-result','verifier_id':verifier['verifier_id'],
        'observation_sha256':second['observation_sha256'],'observation_nonce':initial['observation_nonce'],'runtime_id':'R000000',
        'action_id':intent['action_id'],'action_context_sha256':intent['action_context_sha256'],'result_evidence_sha256':result['observation_sha256'],
        'observed_at_tick':12,'success':True,'resource_credit':700,'intent_sha256':intent['intent_sha256'],'result_observation_sha256':result['observation_sha256']}
    bundle={'schema':gs.OUTCOME_BUNDLE_SCHEMA,'observation_sha256':second['observation_sha256'],'runtime_id':'R000000',
        'action_id':intent['action_id'],'action_context_sha256':intent['action_context_sha256'],'receipt':signed(key,payload)}
    reward=json_command('grounded-sensor-outcome',bundle);after=m.status(data)
    results['transfer']={'before':before,'after':after,'receipt_result':reward,'age_before':age,'age_after':organism2.load(m.child(data,'R000000')).get('metabolic_age',0)}
    before_bytes=fingerprint()
    try:gs.apply_outcome(data,bundle);replay=False
    except ValueError:replay=True
    results['replay_rejected']=replay;results['replay_rejection_bytes_unchanged']=before_bytes==fingerprint()
    results['lineage']=run('metabolism-step','--ticks','8')
    run('realtime-start');checkpoint=run('recovery-checkpoint','--note','V1022.7.3 measured action baseline')['path']
    baseline=m.status(data);baseline_sensor=gs.load(data);restores=[]
    for i in range(3):
        run('metabolism-step','--ticks','2');observe(f'future-{i}',20+i,[10,10,40])
        run('recovery-restore',checkpoint,'--trust-file',data/'v1014/recovery.pub')
        independent=subprocess.run([sys.executable,'-B',str(release/'tools/v1022_7_2_grounded_verifier.py'),'--data',str(data)],capture_output=True,text=True,timeout=120)
        check=json.loads(independent.stdout)
        restores.append({'cycle':i+1,'metabolism_exact':m.status(data)==baseline,'sensor_state_exact':gs.load(data)==baseline_sensor,
            'independent':check,'whole':run('whole-audit'),'metabolism':run('metabolism-audit')})
    results['repeated_process_restore']=restores
    results['audits']={'sensor':run('grounded-sensor-audit'),'metabolism':run('metabolism-audit'),'whole':run('whole-audit')}
    results['boundary']={'synthetic_measurements_only':True,'physical_actuator_used':False,'external_truth_verified':False,
        'consciousness_established':False,'literal_soul_established':False,'24h_run_completed':False,'statistical_coverage_guaranteed':False}
    results['manifest_sha256']=hashlib.sha256((release/'META/RELEASE_MANIFEST.json').read_bytes()).hexdigest()
    results['ok']=all([decision1['assessment']['decision']=='ACQUIRE',decision2['assessment']['decision']=='ACT',rejected,
        results['direct_rejection_bytes_unchanged'],reward['metabolism_result']['paid']==700,after['reservoir']==before['reservoir']-700,
        after['living_energy']==before['living_energy']+700,results['transfer']['age_before']==results['transfer']['age_after'],
        replay,results['replay_rejection_bytes_unchanged'],results['lineage']['max_generation']==2,results['lineage']['wrong']==0,
        all(r['metabolism_exact'] and r['sensor_state_exact'] and r['independent']['ok'] and r['whole']['ok'] and r['metabolism']['ok'] for r in restores),
        all(r['ok'] for r in results['audits'].values())])
    Path(a.out).write_text(json.dumps(results,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'ok':results['ok'],'manifest_sha256':results['manifest_sha256'],'out':a.out}));raise SystemExit(0 if results['ok'] else 1)


if __name__=='__main__':main()
