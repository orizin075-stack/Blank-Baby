from __future__ import annotations
import base64,hashlib,json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

SCHEMA_POLICY='tukuyo.v955.semantic_guard_migration_policy/1'
SCHEMA_RECEIPT='tukuyo.v955.semantic_guard_migration_receipt/1'
SCHEMA_STATE='tukuyo.v955.semantic_guard_state/1'
# Fixed spec is deliberately independent of legacy s838.OPS and BUILTINS.
SPEC={
 '+':{'operator':'ADD','cases':[[-8,3,-5],[-3,-4,-7],[0,0,0],[2,5,7],[9,-2,7]]},
 '-':{'operator':'SUB','cases':[[-8,3,-11],[-3,-4,1],[0,0,0],[2,5,-3],[9,-2,11]]},
 '*':{'operator':'MUL','cases':[[-8,3,-24],[-3,-4,12],[0,7,0],[2,5,10],[9,-2,-18]]},
}

def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def sha_obj(o):return hashlib.sha256(canon(o)).hexdigest()
def sha_file(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def builtin_spec_sha256():return sha_obj(SPEC)

def check_builtin_semantics(s838):
    errors=[]
    if set(s838.BUILTINS)!=set(SPEC):errors.append('BUILTIN_SURFACE_SET')
    for surf,spec in SPEC.items():
        op=s838.BUILTINS.get(surf)
        if op!=spec['operator']:errors.append('BUILTIN_MAPPING:'+surf);continue
        fn=s838.OPS.get(op)
        if not callable(fn):errors.append('BUILTIN_OPERATOR_MISSING:'+op);continue
        for a,b,expected in spec['cases']:
            try:actual=fn(a,b)
            except Exception:errors.append('BUILTIN_EXCEPTION:'+op);break
            if actual!=expected:
                errors.append('BUILTIN_SEMANTIC_MISMATCH:'+op+':'+str((a,b,actual,expected)));break
    return {'ok':not errors,'errors':errors,'spec_sha256':builtin_spec_sha256()}

def hardened_regression_factory(s838):
    def hardened(state_payload,new_surface,new_op):
        chk=check_builtin_semantics(s838)
        if not chk['ok']:return False
        if new_surface in SPEC:return False
        if new_op not in tuple(x['operator'] for x in SPEC.values()):return False
        promos=state_payload.get('promotions',{})
        if new_surface in promos and promos[new_surface].get('operator')!=new_op:return False
        # Every existing promoted operator must still denote one of the independently checked builtins.
        for meta in promos.values():
            if meta.get('operator') not in tuple(x['operator'] for x in SPEC.values()):return False
        return True
    return hardened

def install(s838):
    chk=check_builtin_semantics(s838)
    if not chk['ok']:raise RuntimeError('V955_BUILTIN_SPEC_FAILED:'+','.join(chk['errors']))
    s838._regression=hardened_regression_factory(s838)
    s838._V955_HARDENED_REGRESSION=True
    s838._V955_BUILTIN_SPEC_SHA256=chk['spec_sha256']
    return chk

def installed(s838):
    return bool(getattr(s838,'_V955_HARDENED_REGRESSION',False)) and getattr(s838,'_V955_BUILTIN_SPEC_SHA256',None)==builtin_spec_sha256()

def _root():return Path(__file__).resolve().parents[2]
def _policy_paths():
    r=_root();return r/'META/V955_SEMANTIC_MIGRATION_POLICY.json',r/'META/V955_SEMANTIC_MIGRATION_RECEIPT.json'

def verify_policy(trust_file):
    polp,recp=_policy_paths();pol=json.loads(polp.read_text());rec=json.loads(recp.read_text());key=Path(trust_file).read_text().strip()
    if pol.get('schema')!=SCHEMA_POLICY:raise ValueError('MIGRATION_POLICY_SCHEMA')
    if pol.get('builtin_spec_sha256')!=builtin_spec_sha256():raise ValueError('MIGRATION_BUILTIN_SPEC_BINDING')
    if pol.get('guard_source_sha256')!=sha_file(__file__):raise ValueError('MIGRATION_GUARD_SOURCE_BINDING')
    if rec.get('public_key')!=key:raise ValueError('MIGRATION_TRUST_ROOT_MISMATCH')
    pay=rec.get('payload',{})
    if pay.get('schema')!=SCHEMA_RECEIPT or pay.get('policy_sha256')!=sha_obj(pol):raise ValueError('MIGRATION_RECEIPT_BINDING')
    try:
        Ed25519PublicKey.from_public_bytes(base64.b64decode(key,validate=True)).verify(base64.b64decode(rec['signature'],validate=True),canon(pay))
    except (InvalidSignature,ValueError,TypeError) as e:raise ValueError('MIGRATION_SIGNATURE_INVALID') from e
    return {'policy':pol,'receipt':rec,'policy_sha256':sha_obj(pol),'receipt_sha256':sha_obj(rec)}

def _state_path(data):return Path(data)/'semantic_guard_v955/MIGRATION_STATE.json'
def migrate(data,api,trust_file):
    info=verify_policy(trust_file);s838=api['organism'].s838
    if not installed(s838):raise ValueError('V955_GUARD_NOT_INSTALLED')
    semroot=Path(data)/'state/semantic';ienv=api['organism'].load(Path(data)/'state');sem=s838.load_state(semroot)
    legacy=sem['payload'].get('semantic_source_sha256')
    if legacy!=info['policy'].get('legacy_semantic_source_sha256'):raise ValueError('LEGACY_SEMANTIC_SOURCE_NOT_AUTHORIZED')
    chk=check_builtin_semantics(s838)
    if not chk['ok']:raise ValueError('BUILTIN_SPEC_FAILED')
    ip=ienv['payload'];rec={
      'schema':SCHEMA_STATE,'individual_id':ip['individual_id'],'integration_seq_at_migration':ip['integration_seq'],
      'semantic_state_sha256_at_migration':sha_obj(sem),'legacy_semantic_source_sha256':legacy,
      'guard_source_sha256':sha_file(__file__),'builtin_spec_sha256':builtin_spec_sha256(),
      'policy_sha256':info['policy_sha256'],'policy_receipt_sha256':info['receipt_sha256'],
      'mode':'LEGACY_STATE_PRESERVED_HARDENED_RUNTIME_GUARD'
    }
    p=_state_path(data);p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():
        old=json.loads(p.read_text())
        if old!=rec:raise ValueError('MIGRATION_STATE_ALREADY_EXISTS_DIFFERENT')
    else:p.write_bytes(canon(rec)+b'\n')
    return {'ok':True,'migration':rec}

def audit_migration(data,api,trust_file):
    info=verify_policy(trust_file);s838=api['organism'].s838
    if not installed(s838):raise ValueError('V955_GUARD_NOT_INSTALLED')
    chk=check_builtin_semantics(s838)
    if not chk['ok']:raise ValueError('BUILTIN_SPEC_FAILED')
    p=_state_path(data)
    if not p.is_file():return {'ok':False,'status':'MIGRATION_NOT_INSTALLED','guard_installed':True,'builtin_spec_ok':True}
    rec=json.loads(p.read_text());ienv=api['organism'].load(Path(data)/'state');sem=s838.load_state(Path(data)/'state/semantic')
    if rec.get('schema')!=SCHEMA_STATE:raise ValueError('MIGRATION_STATE_SCHEMA')
    if rec.get('individual_id')!=ienv['payload']['individual_id']:raise ValueError('MIGRATION_WRONG_INDIVIDUAL')
    if int(ienv['payload']['integration_seq'])<int(rec.get('integration_seq_at_migration',-1)):raise ValueError('MIGRATION_INTEGRATION_ROLLBACK')
    if rec.get('legacy_semantic_source_sha256')!=info['policy']['legacy_semantic_source_sha256']:raise ValueError('MIGRATION_LEGACY_BINDING')
    if rec.get('guard_source_sha256')!=sha_file(__file__):raise ValueError('MIGRATION_GUARD_BINDING')
    if rec.get('builtin_spec_sha256')!=builtin_spec_sha256():raise ValueError('MIGRATION_SPEC_BINDING')
    if rec.get('policy_sha256')!=info['policy_sha256'] or rec.get('policy_receipt_sha256')!=info['receipt_sha256']:raise ValueError('MIGRATION_POLICY_BINDING')
    if sem['payload'].get('semantic_source_sha256')!=rec['legacy_semantic_source_sha256']:raise ValueError('SEMANTIC_SOURCE_DRIFT')
    return {'ok':True,'status':'MIGRATED','individual_id':rec['individual_id'],'guard_installed':True,'builtin_spec_ok':True,'migration_origin_semantic_state_sha256':rec['semantic_state_sha256_at_migration']}
