"""v960 bounded long-horizon autonomous science campaign.
The agent may reject a failed hypothesis and try a distinct alternative, but observations remain external signed evidence.
"""
from __future__ import annotations
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from tukuyo_v959.agenda import canon,sha_obj

def _verify(env,pubfile):
    if set(env)!={'payload','public_key','signature'}: raise ValueError('SIGNED_ENVELOPE_SCHEMA')
    want=Path(pubfile).read_text().strip()
    if env['public_key']!=want: raise ValueError('TRUST_ROOT_MISMATCH')
    Ed25519PublicKey.from_public_bytes(base64.b64decode(want)).verify(base64.b64decode(env['signature']),canon(env['payload']))
    return env['payload']

def run_campaign(challenge_id,hypotheses,probe_plan,observation_envelopes,observer_pubfile,max_cycles=4):
    if not isinstance(hypotheses,list) or len(hypotheses)<2: raise ValueError('MULTIPLE_HYPOTHESES_REQUIRED')
    if len(hypotheses)>max_cycles: raise ValueError('CYCLE_BUDGET')
    if set(probe_plan)!={'a','b'}: raise ValueError('PROBE_SCHEMA')
    seen=set(); trace=[]
    for i,h in enumerate(hypotheses):
        if set(h)!={'hypothesis_id','predict'} or h['hypothesis_id'] in seen: raise ValueError('HYPOTHESIS_SCHEMA')
        seen.add(h['hypothesis_id'])
        if i>=len(observation_envelopes): raise ValueError('OBSERVATION_REQUIRED')
        remaining=hypotheses[i:]
        if len(remaining)>1:
            preds={int(r['predict'](probe_plan['a'],probe_plan['b'])) for r in remaining}
            if len(preds)<2: raise ValueError('NON_DISCRIMINATING_PROBE')
        p=_verify(observation_envelopes[i],observer_pubfile)
        req={'schema':'tukuyo.v960.probe_observation/1','challenge_id':challenge_id,'cycle':i+1,'a':probe_plan['a'],'b':probe_plan['b'],'observed':p.get('observed')}
        if p!=req: raise ValueError('OBSERVATION_BINDING')
        pred=int(h['predict'](probe_plan['a'],probe_plan['b']))
        status='SUPPORTED' if pred==p['observed'] else 'REJECTED_BY_EXTERNAL_PROBE'
        trace.append({'cycle':i+1,'hypothesis_id':h['hypothesis_id'],'prediction':pred,'observed':p['observed'],'status':status,'observation_sha256':sha_obj(observation_envelopes[i])})
        if status=='SUPPORTED':
            return {'schema':'tukuyo.v960.campaign_result/1','challenge_id':challenge_id,'status':'HYPOTHESIS_SUPPORTED_AFTER_REVISION','cycles_used':i+1,'trace':trace,'selected_hypothesis_id':h['hypothesis_id'],'human_midcycle_hint':False,'general_l5_claim':False}
    return {'schema':'tukuyo.v960.campaign_result/1','challenge_id':challenge_id,'status':'NO_SUPPORTED_HYPOTHESIS','cycles_used':len(trace),'trace':trace,'selected_hypothesis_id':None,'human_midcycle_hint':False,'general_l5_claim':False}
