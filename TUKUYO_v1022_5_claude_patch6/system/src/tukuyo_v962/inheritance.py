"""v962 research-knowledge inheritance.
Only externally promoted public research primitives may cross an individual boundary.
Private autobiography, event history, local keys, and resource state are excluded by schema.
"""
from __future__ import annotations
import base64,hashlib,json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from tukuyo_v958.promotion import registry_path,verify_proposal,evaluate_registry
from tukuyo_v959.agenda import canon,sha_obj
from tukuyo_v957.novel_primitive import eval_proposal

PROHIBITED=('private','secret','key','autobiography','event_history','resource_state','memory')
def _check_public(o,path='root'):
    if isinstance(o,dict):
        for k,v in o.items():
            lk=str(k).lower()
            if any(x in lk for x in PROHIBITED): raise ValueError('PRIVATE_FIELD:'+path+'.'+str(k))
            _check_public(v,path+'.'+str(k))
    elif isinstance(o,list):
        for i,v in enumerate(o):_check_public(v,path+f'[{i}]')

def prepare(parent_data,candidate_sha256,parent_individual_id,child_individual_id):
    if not parent_individual_id or not child_individual_id or parent_individual_id==child_individual_id: raise ValueError('INDIVIDUAL_IDS')
    s=json.loads(registry_path(parent_data).read_text())
    xs=[e for e in s.get('entries',[]) if e.get('candidate_sha256')==candidate_sha256 and e.get('status')=='ACTIVE_BOUNDED_RESEARCH']
    if len(xs)!=1: raise ValueError('ACTIVE_CAPABILITY_REQUIRED')
    e=xs[0]; p=e['proposal'];verify_proposal(p)
    public={'proposal':p,'candidate_sha256':p['candidate_sha256'],'proposal_sha256':e['proposal_sha256'],'promotion_scope':e['promotion_scope'],'domains':e['domains']}
    _check_public(public)
    b={'schema':'tukuyo.v962.public_knowledge_bundle/1','parent_individual_id':parent_individual_id,'child_individual_id':child_individual_id,'public_capability':public,'inheritance_policy':'PUBLIC_VERIFIED_CAPABILITY_ONLY'}
    b['bundle_sha256']=sha_obj({k:v for k,v in b.items() if k!='bundle_sha256'})
    return b

def _verify(env,pubfile):
    if set(env)!={'payload','public_key','signature'}:raise ValueError('SIGNED_ENVELOPE_SCHEMA')
    want=Path(pubfile).read_text().strip()
    if env['public_key']!=want:raise ValueError('TRUST_ROOT_MISMATCH')
    Ed25519PublicKey.from_public_bytes(base64.b64decode(want)).verify(base64.b64decode(env['signature']),canon(env['payload']))
    return env['payload']

def import_bundle(child_data,bundle,receipt,authority_pubfile,expected_child_id):
    _check_public(bundle)
    if bundle.get('schema')!='tukuyo.v962.public_knowledge_bundle/1':raise ValueError('BUNDLE_SCHEMA')
    calc=sha_obj({k:v for k,v in bundle.items() if k!='bundle_sha256'})
    if calc!=bundle.get('bundle_sha256'):raise ValueError('BUNDLE_HASH')
    if bundle.get('child_individual_id')!=expected_child_id:raise ValueError('WRONG_CHILD')
    live=Path(child_data)/'state'/'integration_state.json'
    if not live.is_file(): raise ValueError('LIVE_CHILD_REQUIRED')
    live_id=json.loads(live.read_text(encoding='utf-8')).get('payload',{}).get('individual_id')
    if live_id!=expected_child_id: raise ValueError('WRONG_LIVE_CHILD')
    p=_verify(receipt,authority_pubfile)
    req={'schema':'tukuyo.v962.inheritance_authority/1','bundle_sha256':bundle['bundle_sha256'],'parent_individual_id':bundle['parent_individual_id'],'child_individual_id':expected_child_id,'decision':'ALLOW_PUBLIC_INHERITANCE'}
    if p!=req:raise ValueError('INHERITANCE_AUTHORITY_BINDING')
    out=Path(child_data)/'inherited_research_v962'/'PUBLIC_CAPABILITIES.json';out.parent.mkdir(parents=True,exist_ok=True)
    state={'schema':'tukuyo.v962.child_public_capabilities/1','entries':[]}
    if out.exists():state=json.loads(out.read_text())
    if any(x['public_capability']['candidate_sha256']==bundle['public_capability']['candidate_sha256'] for x in state['entries']):raise ValueError('DUPLICATE_INHERITANCE')
    state['entries'].append({'bundle_sha256':bundle['bundle_sha256'],'public_capability':bundle['public_capability'],'authority_receipt_sha256':sha_obj(receipt),'source_parent':bundle['parent_individual_id']})
    out.write_bytes(canon(state)+b'\n');return state['entries'][-1]

def evaluate_child(child_data,candidate_sha256,a,b):
    p=Path(child_data)/'inherited_research_v962'/'PUBLIC_CAPABILITIES.json';s=json.loads(p.read_text())
    xs=[x for x in s['entries'] if x['public_capability']['candidate_sha256']==candidate_sha256]
    if len(xs)!=1:raise ValueError('INHERITED_CAPABILITY_NOT_FOUND')
    cap=xs[0]['public_capability'];proposal=cap['proposal'];verify_proposal(proposal)
    return {'status':'RESOLVED_INHERITED_PUBLIC','answer':eval_proposal(proposal,int(a),int(b)),'candidate_sha256':candidate_sha256}
