"""v959 bounded self-authored research agenda with external budget/safety authorization."""
from __future__ import annotations
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

def canon(o): return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha_obj(o): return hashlib.sha256(canon(o)).hexdigest()

def _verify(env,pubfile):
    if not isinstance(env,dict) or set(env)!={'payload','public_key','signature'}: raise ValueError('SIGNED_ENVELOPE_SCHEMA')
    want=Path(pubfile).read_text().strip()
    if env['public_key']!=want: raise ValueError('TRUST_ROOT_MISMATCH')
    Ed25519PublicKey.from_public_bytes(base64.b64decode(want)).verify(base64.b64decode(env['signature']),canon(env['payload']))
    return env['payload']

def propose_agenda(challenges):
    if not isinstance(challenges,list) or len(challenges)<2: raise ValueError('MULTIPLE_CHALLENGES_REQUIRED')
    rows=[]; seen=set()
    for c in challenges:
        req={'challenge_id','gap_state','information_gain','capability_gain','uncertainty','estimated_cost','safety_risk'}
        if set(c)!=req: raise ValueError('CHALLENGE_SCHEMA')
        if c['challenge_id'] in seen: raise ValueError('DUPLICATE_CHALLENGE')
        seen.add(c['challenge_id'])
        if c['gap_state'] not in {'REPRESENTATION_INSUFFICIENT','HYPOTHESIS_AMBIGUOUS','SEARCH_INSUFFICIENT'}: raise ValueError('GAP_STATE')
        for k in ('information_gain','capability_gain','uncertainty','estimated_cost','safety_risk'):
            if type(c[k]) is not int or c[k]<0: raise ValueError('CHALLENGE_VALUE')
        # Safety risk and cost are penalties. The model authors the ranking; authority only authorizes.
        score=5*c['information_gain']+4*c['capability_gain']+2*c['uncertainty']-c['estimated_cost']-8*c['safety_risk']
        rows.append({'challenge_id':c['challenge_id'],'score':score,'challenge_sha256':sha_obj(c),'estimated_cost':c['estimated_cost'],'safety_risk':c['safety_risk']})
    rows.sort(key=lambda x:(-x['score'],x['challenge_id']))
    selected=rows[0]
    proposal={'schema':'tukuyo.v959.research_agenda/1','ranking':rows,'selected_challenge_id':selected['challenge_id'],'selected_challenge_sha256':selected['challenge_sha256'],
              'requested_budget':selected['estimated_cost'],'authority_may_rewrite_content':False,'general_l5_claim':False}
    proposal['agenda_sha256']=sha_obj({k:v for k,v in proposal.items() if k!='agenda_sha256'})
    return proposal

def verify_authorization(agenda,env,pubfile):
    p=_verify(env,pubfile)
    if p.get('schema')!='tukuyo.v959.goal_authority/1': raise ValueError('AUTH_SCHEMA')
    if p.get('agenda_sha256')!=agenda['agenda_sha256'] or p.get('selected_challenge_id')!=agenda['selected_challenge_id']: raise ValueError('AUTH_BINDING')
    if p.get('decision')!='AUTHORIZE': raise ValueError('NOT_AUTHORIZED')
    if type(p.get('budget_ceiling')) is not int or p['budget_ceiling']<agenda['requested_budget']: raise ValueError('BUDGET_INSUFFICIENT')
    if p.get('safety_decision')!='ALLOW_BOUNDED': raise ValueError('SAFETY_NOT_ALLOWED')
    # Authority must not replace objective/content.
    if 'replacement_challenge_id' in p or 'replacement_objective' in p: raise ValueError('AUTHORITY_CONTENT_REWRITE')
    return {'ok':True,'agenda_sha256':agenda['agenda_sha256'],'authorized_budget':p['budget_ceiling'],'authority_receipt_sha256':sha_obj(env)}
