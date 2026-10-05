"""Third-party supplied dataset evaluation and exact receipt verification.

Local signatures prove key possession, NOT third-party independence or data truth.
"""
import base64,hashlib,json,math,pathlib
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey
from tukuyo_research_v936.learner import ACTIONS
from tukuyo_research_v936.codegen import source
from tukuyo_research_v936.features import values

def canon(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def H(x):return hashlib.sha256(x).hexdigest()
def _unique_pairs(pairs):
    d={}
    for k,v in pairs:
        if k in d:raise ValueError('DUPLICATE_KEY:'+k)
        d[k]=v
    return d

def dataset(path):
    raw=pathlib.Path(path).read_bytes();items=[];seen=set()
    if len(raw)>20_000_000:raise ValueError('DATASET_TOO_LARGE')
    for i,line in enumerate(raw.splitlines()):
        if not line.strip():raise ValueError('EMPTY_LINE')
        try:row=json.loads(line,object_pairs_hook=_unique_pairs)
        except Exception as e:raise ValueError(f'JSON_FORMAT:{i}') from e
        if not isinstance(row,dict) or set(row)!={'case_id','input','truth'}:raise ValueError('ROW_SCHEMA')
        cid=row['case_id']
        if not isinstance(cid,str) or not 1<=len(cid)<=100 or cid in seen:raise ValueError('DUPLICATE_OR_BAD_CASE_ID')
        seen.add(cid)
        if row['truth'] not in ACTIONS:raise ValueError('TRUTH_SCHEMA')
        if not isinstance(row['input'],dict) or set(row['input'])!={'a','b','c'}:raise ValueError('INPUT_SCHEMA')
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) for v in row['input'].values()):raise ValueError('INPUT_TYPES')
        values(row['input'])
        items.append(row)
    if not 1<=len(items)<=50_000:raise ValueError('DATASET_COUNT')
    return raw,items

def frozen_candidate(root, task):
    root=pathlib.Path(root)
    contract=json.loads((root/'challenge/CHALLENGE_CONTRACT.json').read_text())
    spec=contract['candidates'][task]
    modelb=(root/'evidence'/f'{task}_model.json').read_bytes()
    srcb=(root/'evidence'/f'{task}_source.py').read_bytes()
    if H(modelb)!=spec['model_sha256'] or H(srcb)!=spec['source_sha256']:raise ValueError('CANDIDATE_CHANGED')
    tree=json.loads(modelb)
    if srcb.decode()!=source(tree):raise ValueError('SOURCE_MODEL_DISAGREEMENT')
    # Execute only source reproduced byte-for-byte from a constrained tree.
    ns={'__builtins__':{'float':float}}
    exec(compile(srcb,'<frozen-candidate>','exec'),ns)
    return spec,ns['choose']

def execute(root,task,dataset_path):
    raw,items=dataset(dataset_path)
    spec,fn=frozen_candidate(root,task)
    rows=[]
    for idx,item in enumerate(items):
        pred=fn(item['input'])
        valid=pred in ACTIONS
        rows.append({'case_index':idx,'case_sha256':H(canon(item)),
                     'prediction':pred,'correct':bool(valid and pred==item['truth']),'invalid':not valid})
    counts={'correct':sum(row['correct'] for row in rows),'wrong':sum(not row['correct'] for row in rows),
            'invalid_output':sum(row['invalid'] for row in rows)}
    return {'dataset_sha256':H(raw),'rows':rows,'counts':counts,'source_sha256':spec['source_sha256'],
            'model_sha256':spec['model_sha256'],'n':len(items)}

def sign_evaluation(root,task,dataset_path,secret_path,out_dir,declared_org):
    private=pathlib.Path(secret_path).read_bytes()
    if len(private)!=32:raise ValueError('PRIVATE_KEY_FORMAT')
    key=Ed25519PrivateKey.from_private_bytes(private)
    pub=key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    contract=json.loads((pathlib.Path(root)/'challenge/CHALLENGE_CONTRACT.json').read_text())
    if H(pub)==contract['release_key_sha256']:raise ValueError('RELEASE_KEY_CANNOT_EVALUATE')
    run=execute(root,task,dataset_path)
    p=pathlib.Path(out_dir);p.mkdir(parents=True,exist_ok=True)
    rowsb=canon(run['rows'])+b'\n';(p/'RESULT_ROWS.json').write_bytes(rowsb)
    payload={'schema':'tukuyo.external_challenge_receipt.v1','task':task,
        'candidate_source_sha256':run['source_sha256'],'candidate_model_sha256':run['model_sha256'],
        'dataset_sha256':run['dataset_sha256'],'result_rows_sha256':H(rowsb),
        'n':run['n'],**run['counts'],'evaluator_public_key_sha256':H(pub),'evaluator_declaration':str(declared_org)[:100]}
    receipt={'payload':payload,'signature_b64':base64.b64encode(key.sign(canon(payload))).decode()}
    (p/'EVALUATION_RECEIPT.json').write_bytes(canon(receipt)+b'\n')
    return payload

def verify(root,task,dataset_path,result_rows_path,receipt_path,trusted_evaluator_pub_b64):
    try:
        pub=base64.b64decode(trusted_evaluator_pub_b64,validate=True)
        if len(pub)!=32:return {'ok':False,'reason':'EVALUATOR_PUBLIC_KEY_FORMAT'}
        contract=json.loads((pathlib.Path(root)/'challenge/CHALLENGE_CONTRACT.json').read_text())
        if H(pub)==contract['release_key_sha256']:return {'ok':False,'reason':'SELF_AUTHORITY'}
        receipt=json.loads(pathlib.Path(receipt_path).read_bytes(),object_pairs_hook=_unique_pairs)
        payload=receipt['payload']
        Ed25519PublicKey.from_public_bytes(pub).verify(base64.b64decode(receipt['signature_b64'],validate=True),canon(payload))
    except Exception:return {'ok':False,'reason':'SIGNATURE_OR_FORMAT'}
    if H(pub)!=payload.get('evaluator_public_key_sha256'):return {'ok':False,'reason':'EVALUATOR_BINDING'}
    try:
        run=execute(root,task,dataset_path)
        actual_rows=json.loads(pathlib.Path(result_rows_path).read_bytes(),object_pairs_hook=_unique_pairs)
        if actual_rows!=run['rows']:return {'ok':False,'reason':'RESULT_ROWS_MISMATCH'}
        rowsb=pathlib.Path(result_rows_path).read_bytes()
    except Exception as e:return {'ok':False,'reason':'EVALUATION_RECOMPUTE:'+str(e)[:100]}
    expected={'schema':'tukuyo.external_challenge_receipt.v1','task':task,'candidate_source_sha256':run['source_sha256'],
              'candidate_model_sha256':run['model_sha256'],'dataset_sha256':run['dataset_sha256'],
              'result_rows_sha256':H(rowsb),'n':run['n'],**run['counts'],'evaluator_public_key_sha256':H(pub)}
    if any(payload.get(k)!=v for k,v in expected.items()):return {'ok':False,'reason':'PAYLOAD_MISMATCH'}
    return {'ok':True,'counts':run['counts'],'n':run['n'], 'warning':'PINNED_KEY_SIGNATURE_AND_RECOMPUTATION_ONLY; INDEPENDENCE_AND_LABEL_TRUTH_REQUIRE_EXTERNAL_ATTESTATION'}
