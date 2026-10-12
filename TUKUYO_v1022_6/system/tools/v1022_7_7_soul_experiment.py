#!/usr/bin/env python3
"""Fresh baseline/new comparison. All witnesses and outcomes are fixtures."""
import argparse, base64, copy, hashlib, json, os, subprocess, sys
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--release',type=Path);ap.add_argument('--data',type=Path,required=True)
    ap.add_argument('--trust',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();root=(a.release or Path(__file__).resolve().parents[1]).resolve();data=a.data.resolve()
    sys.path.insert(0,str(root/'src'))
    from tukuyo_v1022 import evidence_bound_soul as es, reflective_soul as rs
    from tukuyo_v977.whole_state import canon,sha_obj
    def pub(k):return base64.b64encode(k.public_key().public_bytes_raw()).decode()
    def envelope(k,p):return {'payload':p,'public_key':pub(k),'signature':base64.b64encode(k.sign(canon(p))).decode()}
    def cli(d,*args,expect_ok=True):
        p=subprocess.run([sys.executable,'-B',str(root/'run_tukuyo.py'),'--runtime-trust-file',str(a.trust),'--data',str(d),*map(str,args)],
                         capture_output=True,text=True,timeout=240,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        r=json.loads(p.stdout)
        if expect_ok:assert p.returncode==0 and r.get('ok'),(args,r,p.stderr)
        return r
    cli(data,'init','--individual-id','SOUL-EXPERIENCE-CAMPAIGN');es.integrate(data);witnesses=[]
    for i in range(3):
        ak,k=Ed25519PrivateKey.generate(),Ed25519PrivateKey.generate()
        es.add_authority(data,{'schema':es.AUTHORITY_SCHEMA,'authority_id':f'authority-{i}','trust_domain':f'domain-{i}','public_key':pub(ak)})
        es.add_witness(data,envelope(ak,{'schema':es.WITNESS_SCHEMA,'certificate_id':f'cert-{i}', 'observer_id':f'observer-{i}',
                       'observer_public_key':pub(k),'authority_id':f'authority-{i}','trust_domain':f'domain-{i}'}))
        witnesses.append((f'observer-{i}',k))
    options=[{'id':'fast_gain','signals':{'survival':.15},'themes':[],'conflicts':[]},
             {'id':'patient_gain','signals':{},'themes':[],'conflicts':[]}]
    effects={'fast_gain':{'self_wellbeing':.6,'others_wellbeing':.8,'future_self':.8,'truth_consistency':.8,'bodily_cost':0,'uncertainty':0},
             'patient_gain':{'self_wellbeing':.55,'others_wellbeing':.55,'future_self':.55,'truth_consistency':.55,'bodily_cost':0,'uncertainty':0}}
    count=0
    def decide(context='repeatable-local-work'):
        nonlocal count
        count+=1
        assessments=[envelope(k,{'schema':es.ASSESSMENT_SCHEMA,'assessment_id':f'a-{count}-{i}','observer_id':obs,
            'options_sha256':sha_obj(options),'context_sha256':sha_obj(context),'measurement_kind':'bounded_evaluator',
            'evidence_sha256':sha_obj({'assessment':count,'source':i}),'effects_by_option':copy.deepcopy(effects)}) for i,(obs,k) in enumerate(witnesses)]
        return es.deliberate(data,{'schema':es.BUNDLE_SCHEMA,'context':context,'options':options,'assessments':assessments})
    def attest(decision,n):
        out=[]
        for i,(obs,k) in enumerate(witnesses):
            p={'schema':es.ATTESTATION_SCHEMA,'attestation_id':f'o-{n}-{i}','observer_id':obs,'decision_sha256':decision['decision_sha256'],
                'chosen':decision['chosen'],'measurement_kind':'bounded_evaluator','evidence_sha256':sha_obj({'episode':n,'source':i}),
                'source_kind':'direct_observation','self_wellbeing':-1,'others_wellbeing':-1,'future_self':-1,'truth_consistency':-1,
                'bodily_cost':.8,'surprise':0,'confidence':.9,'note':'synthetic signed outcome, physical truth not established'}
            out.append(es.attest(data,envelope(k,p)))
        return out
    results={};first=decide();results['before_experience']=first;results['episode1']=attest(first,1)
    second=decide();results['after_one_episode']=second;results['episode2']=attest(second,2)
    old_decisions=copy.deepcopy(es.load(data)['decisions']);third=decide();results['after_two_episodes']=third
    results['prior_decisions_unchanged']=es.load(data)['decisions'][:2]==old_decisions
    results['unrelated_context']=decide('unrelated-local-work')
    pre=copy.deepcopy(rs.load(data)['profile']['perspective_weights'])
    for i in range(3):
        rs.reflect(data,third['reflective_decision_sha256'],{'evidence_id':f'unsigned-{i}','observer_id':f'invented-{i}',
            'source_kind':'direct_observation','self_wellbeing':1,'others_wellbeing':1,'future_self':1,'truth_consistency':1,
            'bodily_cost':0,'surprise':1,'confidence':1,'note':'caller invented this observer'})
    results['unsigned_profile_before']=pre;results['unsigned_profile_after']=rs.load(data)['profile']['perspective_weights']
    results['after_unsigned_reports']=decide()
    results['audits']={'evidence':es.audit(data),'reflective':rs.audit(data),'whole':cli(data,'whole-audit')}
    # Ordinary CLI commitment control and signed temporal continuity.
    c=data.parent/(data.name+'-commitment');cli(c,'init','--individual-id','SOUL-COMMITMENT-CONTROL')
    opts=[{'id':'conceal','signals':{'survival':1},'themes':[],'conflicts':['truth']},
          {'id':'tell_truth','signals':{'truthfulness':.1},'themes':['truth'],'conflicts':[]}]
    f=c.parent/(c.name+'-options.json');f.write_text(json.dumps(opts))
    cli(c,'soul-experience','vow','.8','.8','--theme','truth');one=cli(c,'soul-deliberate',f)
    cli(c,'soul-experience','vow','.8','.8','--theme','truth');two=cli(c,'soul-deliberate',f)
    results['commitment']={'one_vow':one,'two_vows':two,'temporal':cli(c,'soul-identity-audit'),
                           'heart':cli(c,'heart-audit',expect_ok=False),'whole':cli(c,'whole-audit',expect_ok=False)}
    results['manifest_sha256']=hashlib.sha256((root/'META/RELEASE_MANIFEST.json').read_bytes()).hexdigest()
    results['boundary']={'synthetic_outcomes_only':True,'independent_real_world_witnesses':False,'live_ai_teachers':False,
                         'literal_soul_established':False,'consciousness_established':False}
    a.out.write_text(json.dumps(results,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'out':str(a.out),'choices':[first['chosen'],second['chosen'],third['chosen']],
          'unrelated':results['unrelated_context']['chosen'],'unsigned_weights_changed':pre!=results['unsigned_profile_after'],
          'audits':{k:v['ok'] for k,v in results['audits'].items()},'one_vow':one['chosen'],'two_vows':two['chosen']}))

if __name__=='__main__':main()
