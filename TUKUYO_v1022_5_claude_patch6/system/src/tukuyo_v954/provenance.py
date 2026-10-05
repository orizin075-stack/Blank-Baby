from __future__ import annotations
import base64,hashlib,json,os
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey
ZERO='0'*64

def canon(o): return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def sha_obj(o): return hashlib.sha256(canon(o)).hexdigest()
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def pub(priv): return base64.b64encode(priv.public_key().public_bytes_raw()).decode()
def sign(priv,payload): return {'payload':payload,'public_key':pub(priv),'signature':base64.b64encode(priv.sign(canon(payload))).decode()}
def verify(env,expected_pub):
    if not isinstance(env,dict) or env.get('public_key')!=expected_pub:return False
    try: Ed25519PublicKey.from_public_bytes(base64.b64decode(expected_pub)).verify(base64.b64decode(env['signature']),canon(env['payload']));return True
    except Exception:return False

def _paths(state,surface):
    state=Path(state); sem=load(state/'semantic/semantic_state.json')['payload']; meta=sem['promotions'].get(surface)
    if not meta: raise ValueError('NO_NATIVE_PROMOTION')
    pfile=None;pobj=None
    for p in (state/'semantic/promotions').glob('*.json'):
        o=load(p)
        if sha_obj(o)==meta.get('promotion_sha256'):pfile=p;pobj=o;break
    if pobj is None:raise ValueError('PROMOTION_OBJECT_MISSING')
    lfile=None;lobj=None
    for p in (state/'learning_ledger').glob('*.json'):
        o=load(p);q=o.get('payload',{})
        if q.get('semantic_promotion_sha256')==meta.get('promotion_sha256') and q.get('surface')==surface:lfile=p;lobj=o;break
    if lobj is None:raise ValueError('LEARNING_OBJECT_MISSING')
    return meta,pfile,pobj,lfile,lobj

def persist_teach_bundle(data,surface,semantic_provenance):
    data=Path(data);state=data/'state';meta,pfile,pobj,lfile,lobj=_paths(state,surface)
    root=data/'capability_provenance';objs=root/'objects';reqs=root/'requests';objs.mkdir(parents=True,exist_ok=True);reqs.mkdir(parents=True,exist_ok=True)
    pieces={'proposal':semantic_provenance['proposal'],'holdout':semantic_provenance['holdout'],'commitment':semantic_provenance['commitment'],'verifier_receipt':semantic_provenance['receipt'],'promotion':pobj,'learning_entry':lobj}
    refs={}
    for k,o in pieces.items():
        h=sha_obj(o);(objs/(h+'.json')).write_bytes(canon(o)+b'\n');refs[k+'_sha256']=h
    ip=load(state/'integration_state.json')['payload']
    request={'schema':'tukuyo.v954.capability_provenance_request/1','individual_id':ip['individual_id'],'surface':surface,'operator':meta['operator'],'promotion_sha256':meta['promotion_sha256'],'learning_entry_sha256':sha_obj(lobj),'object_refs':refs}
    verify_request(data,request)
    h=sha_obj(request);(reqs/(h+'.json')).write_bytes(canon(request)+b'\n')
    return request

def _obj(data,h):
    if not isinstance(h,str) or len(h)!=64 or h==ZERO:raise ValueError('ZERO_OR_INVALID_OBJECT_HASH')
    p=Path(data)/'capability_provenance/objects'/(h+'.json')
    if not p.is_file():raise ValueError('PROVENANCE_OBJECT_MISSING:'+h)
    o=load(p)
    if sha_obj(o)!=h:raise ValueError('PROVENANCE_OBJECT_HASH_MISMATCH')
    return o

def verify_request(data,request):
    state=Path(data)/'state';meta,pfile,pobj,lfile,lobj=_paths(state,request['surface'])
    if request.get('schema')!='tukuyo.v954.capability_provenance_request/1':raise ValueError('REQUEST_SCHEMA')
    ip=load(state/'integration_state.json')['payload']
    if request.get('individual_id')!=ip['individual_id']:raise ValueError('REQUEST_WRONG_INDIVIDUAL')
    if request.get('operator')!=meta['operator'] or request.get('promotion_sha256')!=meta['promotion_sha256']:raise ValueError('REQUEST_CAPABILITY_BINDING')
    refs=request.get('object_refs',{})
    required={'proposal_sha256','holdout_sha256','commitment_sha256','verifier_receipt_sha256','promotion_sha256','learning_entry_sha256'}
    if set(refs)!=required:raise ValueError('REQUEST_OBJECT_SET')
    proposal=_obj(data,refs['proposal_sha256']);holdout=_obj(data,refs['holdout_sha256']);commit=_obj(data,refs['commitment_sha256']);receipt=_obj(data,refs['verifier_receipt_sha256']);promotion=_obj(data,refs['promotion_sha256']);learning=_obj(data,refs['learning_entry_sha256'])
    if sha_obj(promotion)!=meta['promotion_sha256'] or sha_obj(learning)!=request['learning_entry_sha256']:raise ValueError('LIVE_OBJECT_BINDING')
    pp=promotion.get('payload',{});lp=learning.get('payload',{});rp=receipt.get('payload',{});cp=commit.get('payload',{})
    if pp.get('surface')!=request['surface'] or pp.get('operator')!=request['operator']:raise ValueError('PROMOTION_FIELDS')
    if lp.get('surface')!=request['surface'] or lp.get('operator')!=request['operator'] or lp.get('individual_id')!=request['individual_id'] or lp.get('semantic_promotion_sha256')!=request['promotion_sha256']:raise ValueError('LEARNING_FIELDS')
    if pp.get('proposal_sha256')!=refs['proposal_sha256'] or pp.get('verifier_receipt_sha256')!=refs['verifier_receipt_sha256']:raise ValueError('PROMOTION_PROOF_BINDING')
    if proposal.get('surface')!=request['surface'] or proposal.get('unique_operator')!=request['operator']:raise ValueError('PROPOSAL_FIELDS')
    if proposal.get('holdout_commitment_sha256')!=refs['commitment_sha256']:raise ValueError('PROPOSAL_COMMITMENT')
    if rp.get('proposal_sha256')!=refs['proposal_sha256'] or rp.get('holdout_commitment_sha256')!=refs['commitment_sha256'] or rp.get('holdout_sha256')!=refs['holdout_sha256']:raise ValueError('RECEIPT_BINDING')
    if cp.get('holdout_sha256')!=refs['holdout_sha256'] or cp.get('surface')!=request['surface']:raise ValueError('COMMITMENT_BINDING')
    OPS={'ADD':lambda a,b:a+b,'SUB':lambda a,b:a-b,'MUL':lambda a,b:a*b}
    op=request['operator']
    if op not in OPS:raise ValueError('UNKNOWN_OPERATOR')
    rows=[]
    for c in holdout:
        actual=OPS[op](c['a'],c['b']);rows.append({'a':c['a'],'b':c['b'],'expected':c['expected'],'actual':actual,'correct':actual==c['expected']})
    wrong=sum(not x['correct'] for x in rows)
    if wrong or rp.get('wrong')!=0 or rp.get('correct')!=len(rows) or rp.get('results_sha256')!=sha_obj(rows):raise ValueError('RECEIPT_RECOMPUTE_FAILED')
    if any(v==ZERO for v in refs.values()):raise ValueError('ZERO_HASH_FORBIDDEN')
    return {'ok':True,'request_sha256':sha_obj(request),'surface':request['surface'],'operator':request['operator']}

def install_seal(data,trust_dir,request_file,receipt_file):
    data=Path(data);trust=Path(trust_dir);req=load(request_file);verify_request(data,req);rec=load(receipt_file);pk=(trust/'capability_authority.pub').read_text().strip()
    if not verify(rec,pk):raise ValueError('CAPABILITY_AUTHORITY_SIGNATURE_INVALID')
    expected={'schema':'tukuyo.v954.capability_authority_receipt/1','request_sha256':sha_obj(req),'individual_id':req['individual_id'],'surface':req['surface'],'operator':req['operator'],'promotion_sha256':req['promotion_sha256']}
    if rec['payload']!=expected:raise ValueError('CAPABILITY_AUTHORITY_BINDING')
    root=data/'capability_provenance/seals';root.mkdir(parents=True,exist_ok=True);name=hashlib.sha256(req['surface'].encode()).hexdigest()+'.json';out={'request':req,'receipt':rec};(root/name).write_bytes(canon(out)+b'\n');return {'ok':True,'surface':req['surface'],'seal_sha256':sha_obj(out)}

def gate_state_answer(state,query,result,trust_dir):
    if result.get('status')!='RESOLVED':return result
    surface=result.get('surface')
    if surface in ('+','-','*'):return result
    if not trust_dir:return {'status':'OPEN','surface':surface,'answer':None,'reason':'EXTERNAL_CAPABILITY_SEAL_REQUIRED'}
    data=Path(state).parent;name=hashlib.sha256(surface.encode()).hexdigest()+'.json';p=data/'capability_provenance/seals'/name
    if not p.is_file():return {'status':'OPEN','surface':surface,'answer':None,'reason':'EXTERNAL_CAPABILITY_SEAL_REQUIRED'}
    x=load(p);req=x['request'];rec=x['receipt'];verify_request(data,req);pk=(Path(trust_dir)/'capability_authority.pub').read_text().strip()
    if not verify(rec,pk):raise ValueError('CAPABILITY_AUTHORITY_SIGNATURE_INVALID')
    expected={'schema':'tukuyo.v954.capability_authority_receipt/1','request_sha256':sha_obj(req),'individual_id':req['individual_id'],'surface':req['surface'],'operator':req['operator'],'promotion_sha256':req['promotion_sha256']}
    if rec['payload']!=expected:raise ValueError('CAPABILITY_AUTHORITY_BINDING')
    if result.get('surface')!=req.get('surface'):raise ValueError('SEAL_SURFACE_MISMATCH')
    if result.get('operator')!=req['operator']:raise ValueError('RUNTIME_OPERATOR_NOT_SEALED')
    return dict(result,authority='EXTERNALLY_SEALED_V954_PROVENANCE')
