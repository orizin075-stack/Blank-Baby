from __future__ import annotations
import copy,json,os,sys
from pathlib import Path
from .util import canonical,sha256_bytes,sha256_file,atomic_write,norm
from .crypto import new_keypair,sign_obj,verify_obj

OPS={
 'ADD':lambda a,b:a+b,
 'SUB':lambda a,b:a-b,
 'MUL':lambda a,b:a*b,
}
BUILTINS={'+':'ADD','-':'SUB','*':'MUL'}
STATE='semantic_state.json'; HEAD='promotion_head.json'; LEDGER='promotions'; PA_SK='private/promotion.key'; PA_PK='promotion.pub'; V_SK='private/verifier.key'; V_PK='verifier.pub'; ZERO='0'*64
class SemanticError(RuntimeError): pass

def _load(p): return json.loads(Path(p).read_text())
def _signed(payload,sk,pk): return {'payload':payload,'public_key':pk,'signature':sign_obj(sk,payload)}
def _verify(env): return verify_obj(env['public_key'],env['payload'],env['signature'])
def _module_sha(): return sha256_file(__file__)
def _ledger_path(root,seq): return Path(root)/LEDGER/f'{seq:012d}.json'

def init(root):
    root=Path(root); root.mkdir(parents=True,exist_ok=True); (root/'private').mkdir(exist_ok=True); (root/LEDGER).mkdir(exist_ok=True)
    if (root/STATE).exists(): return load_state(root)
    psk,ppk=new_keypair(); vsk,vpk=new_keypair()
    atomic_write(root/PA_SK,psk.encode()); os.chmod(root/PA_SK,0o600); atomic_write(root/PA_PK,ppk.encode())
    atomic_write(root/V_SK,vsk.encode()); os.chmod(root/V_SK,0o600); atomic_write(root/V_PK,vpk.encode())
    payload={'schema':'tukuyo.semantic_state.v838.1','state_seq':0,'builtins':BUILTINS,'promotions':{},'promotion_head_sha256':ZERO,'promotion_authority_pub':ppk,'verifier_pub':vpk,'semantic_source_sha256':_module_sha()}
    env=_signed(payload,psk,ppk); atomic_write(root/STATE,canonical(env))
    head=_signed({'schema':'tukuyo.semantic_head.v838.1','state_seq':0,'state_sha256':sha256_bytes(canonical(env)),'promotion_head_sha256':ZERO},psk,ppk); atomic_write(root/HEAD,canonical(head))
    return env

def load_state(root):
    root=Path(root); env=_load(root/STATE)
    if not _verify(env): raise SemanticError('STATE_SIGNATURE_INVALID')
    p=env['payload']; head=_load(root/HEAD)
    if not _verify(head): raise SemanticError('HEAD_SIGNATURE_INVALID')
    hp=head['payload']
    if hp['state_seq']!=p['state_seq'] or hp['state_sha256']!=sha256_bytes(canonical(env)) or hp['promotion_head_sha256']!=p['promotion_head_sha256']: raise SemanticError('STATE_ROLLBACK_OR_HEAD_MISMATCH')
    if p['semantic_source_sha256']!=_module_sha(): raise SemanticError('SEMANTIC_IMPLEMENTATION_IDENTITY_MISMATCH')
    return env

def parse_query(query):
    q=norm(query); parts=q.split(' ')
    if len(parts)<3: raise SemanticError('QUERY_SHAPE_UNSUPPORTED')
    try: a=int(parts[0]); b=int(parts[-1])
    except ValueError: raise SemanticError('QUERY_OPERANDS_UNSUPPORTED')
    surface=norm(' '.join(parts[1:-1])); return a,surface,b

def resolve_operator(state_payload,surface):
    s=norm(surface)
    if s in BUILTINS: return BUILTINS[s]
    x=state_payload['promotions'].get(s)
    return x['operator'] if x else None

def evaluate(root,query):
    p=load_state(root)['payload']; a,s,b=parse_query(query); op=resolve_operator(p,s)
    if not op: return {'status':'OPEN','surface':s,'answer':None}
    return {'status':'RESOLVED','surface':s,'operator':op,'answer':OPS[op](a,b)}

def _case(c):
    if set(c)!={'a','b','expected'}: raise SemanticError('CASE_SCHEMA_INVALID')
    return {'a':int(c['a']),'b':int(c['b']),'expected':int(c['expected'])}
def normalize_cases(cases): return [_case(c) for c in cases]

def hypotheses(training):
    tr=normalize_cases(training); out=[]
    for op,f in OPS.items():
        if all(f(c['a'],c['b'])==c['expected'] for c in tr): out.append(op)
    return out

def discriminating_probe(candidates):
    cands=list(candidates)
    if len(cands)<2: return None
    for a in range(-4,6):
      for b in range(-4,6):
        vals={op:OPS[op](a,b) for op in cands}
        if len(set(vals.values()))==len(cands): return {'a':a,'b':b,'predictions':vals}
    return None

def holdout_commitment(root,surface,holdout):
    root=Path(root); ho=normalize_cases(holdout); s=norm(surface)
    pairs={(c['a'],c['b']) for c in ho}
    if len(pairs)!=len(ho): raise SemanticError('HOLDOUT_DUPLICATE_CASE')
    payload={'schema':'tukuyo.semantic_holdout_commitment.v838.1','surface':s,'holdout_sha256':sha256_bytes(canonical(ho)),'holdout_count':len(ho),'semantic_source_sha256':_module_sha()}
    sk=(root/V_SK).read_text().strip(); pk=(root/V_PK).read_text().strip(); return _signed(payload,sk,pk)

def make_proposal(surface,training,commitment):
    s=norm(surface); tr=normalize_cases(training); hs=hypotheses(tr)
    if not _verify(commitment): raise SemanticError('HOLDOUT_COMMITMENT_SIGNATURE_INVALID')
    cp=commitment['payload']
    if cp.get('surface')!=s or cp.get('semantic_source_sha256')!=_module_sha(): raise SemanticError('HOLDOUT_COMMITMENT_BINDING_MISMATCH')
    return {'schema':'tukuyo.semantic_proposal.v838.1','surface':s,'training':tr,'training_sha256':sha256_bytes(canonical(tr)),'holdout_commitment_sha256':sha256_bytes(canonical(commitment)),'candidates':hs,'unique_operator':hs[0] if len(hs)==1 else None,'discriminating_probe':discriminating_probe(hs),'semantic_source_sha256':_module_sha()}

def verifier_receipt(root,proposal,holdout,commitment):
    root=Path(root); ho=normalize_cases(holdout)
    if proposal.get('semantic_source_sha256')!=_module_sha(): raise SemanticError('PROPOSAL_IMPLEMENTATION_MISMATCH')
    if not _verify(commitment): raise SemanticError('HOLDOUT_COMMITMENT_SIGNATURE_INVALID')
    cp=commitment['payload']
    if commitment['public_key']!=(root/V_PK).read_text().strip(): raise SemanticError('HOLDOUT_COMMITMENT_KEY_MISMATCH')
    if proposal.get('holdout_commitment_sha256')!=sha256_bytes(canonical(commitment)): raise SemanticError('PROPOSAL_COMMITMENT_BINDING_MISMATCH')
    if cp.get('surface')!=proposal['surface'] or cp.get('holdout_sha256')!=sha256_bytes(canonical(ho)) or cp.get('holdout_count')!=len(ho): raise SemanticError('HOLDOUT_COMMITMENT_MISMATCH')
    tr=proposal['training']; train_pairs={(c['a'],c['b']) for c in tr}; hold_pairs={(c['a'],c['b']) for c in ho}
    if len(hold_pairs)!=len(ho): raise SemanticError('HOLDOUT_DUPLICATE_CASE')
    if train_pairs & hold_pairs: raise SemanticError('TRAIN_HOLDOUT_OVERLAP')
    op=proposal.get('unique_operator')
    if not op or op not in OPS: raise SemanticError('NO_UNIQUE_HYPOTHESIS')
    results=[{'a':c['a'],'b':c['b'],'expected':c['expected'],'actual':OPS[op](c['a'],c['b']),'correct':OPS[op](c['a'],c['b'])==c['expected']} for c in ho]
    payload={'schema':'tukuyo.semantic_verifier_receipt.v838.1','proposal_sha256':sha256_bytes(canonical(proposal)),'holdout_commitment_sha256':sha256_bytes(canonical(commitment)),'surface':proposal['surface'],'operator':op,'holdout_sha256':sha256_bytes(canonical(ho)),'holdout_count':len(ho),'correct':sum(x['correct'] for x in results),'wrong':sum(not x['correct'] for x in results),'results_sha256':sha256_bytes(canonical(results)),'semantic_source_sha256':_module_sha()}
    sk=(root/V_SK).read_text().strip(); pk=(root/V_PK).read_text().strip(); return _signed(payload,sk,pk)

def _regression(state_payload,new_surface,new_op):
    probes=[(-3,2),(0,5),(2,3),(7,-2)]
    # Built-ins must stay exact.
    for surf,op in BUILTINS.items():
      for a,b in probes:
        if OPS[op](a,b)!=OPS[BUILTINS[surf]](a,b): return False
    # Existing promotions must not be rewritten by a new promotion.
    if new_surface in state_payload['promotions'] and state_payload['promotions'][new_surface]['operator']!=new_op: return False
    return True

def promote(root,proposal,holdout,commitment,receipt):
    root=Path(root); env=load_state(root); p=copy.deepcopy(env['payload']); ho=normalize_cases(holdout)
    if proposal.get('semantic_source_sha256')!=_module_sha(): raise SemanticError('PROPOSAL_IMPLEMENTATION_MISMATCH')
    if not _verify(commitment): raise SemanticError('HOLDOUT_COMMITMENT_SIGNATURE_INVALID')
    cp=commitment['payload']; expected_pk=(root/V_PK).read_text().strip()
    if commitment['public_key']!=expected_pk: raise SemanticError('HOLDOUT_COMMITMENT_KEY_MISMATCH')
    if proposal.get('holdout_commitment_sha256')!=sha256_bytes(canonical(commitment)): raise SemanticError('PROPOSAL_COMMITMENT_BINDING_MISMATCH')
    if cp.get('surface')!=proposal['surface'] or cp.get('holdout_sha256')!=sha256_bytes(canonical(ho)) or cp.get('holdout_count')!=len(ho): raise SemanticError('HOLDOUT_COMMITMENT_MISMATCH')
    if not _verify(receipt): raise SemanticError('VERIFIER_SIGNATURE_INVALID')
    rp=receipt['payload']
    if receipt['public_key']!=expected_pk: raise SemanticError('VERIFIER_KEY_MISMATCH')
    if rp['proposal_sha256']!=sha256_bytes(canonical(proposal)) or rp.get('holdout_commitment_sha256')!=sha256_bytes(canonical(commitment)): raise SemanticError('VERIFIER_PROPOSAL_BINDING_MISMATCH')
    if rp['semantic_source_sha256']!=_module_sha(): raise SemanticError('VERIFIER_IMPLEMENTATION_MISMATCH')
    op_for_recompute=proposal.get('unique_operator')
    if op_for_recompute not in OPS: raise SemanticError('NO_UNIQUE_HYPOTHESIS')
    recomputed=[{'a':c['a'],'b':c['b'],'expected':c['expected'],'actual':OPS[op_for_recompute](c['a'],c['b']),'correct':OPS[op_for_recompute](c['a'],c['b'])==c['expected']} for c in ho]
    rc=sum(x['correct'] for x in recomputed); rw=sum(not x['correct'] for x in recomputed); rsha=sha256_bytes(canonical(recomputed))
    if rp.get('holdout_sha256')!=sha256_bytes(canonical(ho)) or rp.get('holdout_count')!=len(ho) or rp.get('correct')!=rc or rp.get('wrong')!=rw or rp.get('results_sha256')!=rsha: raise SemanticError('VERIFIER_SUMMARY_DISAGREES_WITH_RAW_HOLDOUT')
    if rw!=0 or rc!=len(ho) or len(ho)<3: raise SemanticError('HOLDOUT_NOT_FULLY_VERIFIED')
    hs=proposal['candidates']; op=proposal.get('unique_operator'); surf=proposal['surface']
    if len(hs)!=1 or op not in OPS: raise SemanticError('NO_UNIQUE_HYPOTHESIS')
    if surf in BUILTINS: raise SemanticError('BUILTIN_SURFACE_IMMUTABLE')
    if not _regression(p,surf,op): raise SemanticError('REGRESSION_OR_REWRITE')
    prev=p['promotion_head_sha256']; seq=p['state_seq']+1
    entry_payload={'schema':'tukuyo.semantic_promotion.v838.1','seq':seq,'surface':surf,'operator':op,'proposal_sha256':sha256_bytes(canonical(proposal)),'verifier_receipt_sha256':sha256_bytes(canonical(receipt)),'previous_promotion_sha256':prev,'semantic_source_sha256':_module_sha()}
    psk=(root/PA_SK).read_text().strip(); ppk=(root/PA_PK).read_text().strip(); entry=_signed(entry_payload,psk,ppk); ehash=sha256_bytes(canonical(entry))
    p['state_seq']=seq; p['promotions'][surf]={'operator':op,'promotion_sha256':ehash,'verifier_receipt_sha256':entry_payload['verifier_receipt_sha256']}; p['promotion_head_sha256']=ehash
    new_env=_signed(p,psk,ppk); head=_signed({'schema':'tukuyo.semantic_head.v838.1','state_seq':seq,'state_sha256':sha256_bytes(canonical(new_env)),'promotion_head_sha256':ehash},psk,ppk)
    atomic_write(_ledger_path(root,seq),canonical(entry)); atomic_write(root/STATE,canonical(new_env)); atomic_write(root/HEAD,canonical(head)); return new_env

def audit(root):
    root=Path(root); errors=[]
    try: st=load_state(root)
    except Exception as e: return {'ok':False,'errors':[str(e)]}
    p=st['payload']; prev=ZERO
    for seq in range(1,p['state_seq']+1):
        lp=_ledger_path(root,seq)
        if not lp.exists(): errors.append(f'MISSING_PROMOTION:{seq}'); break
        e=_load(lp)
        if not _verify(e): errors.append(f'PROMOTION_SIGNATURE:{seq}'); break
        q=e['payload']
        if q['seq']!=seq or q['previous_promotion_sha256']!=prev: errors.append(f'PROMOTION_CHAIN:{seq}'); break
        if q['semantic_source_sha256']!=_module_sha(): errors.append(f'PROMOTION_IMPLEMENTATION:{seq}'); break
        prev=sha256_bytes(canonical(e))
    if prev!=p['promotion_head_sha256']: errors.append('PROMOTION_HEAD_MISMATCH')
    for surf,meta in p['promotions'].items():
        if meta['operator'] not in OPS: errors.append('UNKNOWN_OPERATOR:'+surf)
    return {'ok':not errors,'errors':errors,'state_seq':p['state_seq'],'promotions':p['promotions'],'promotion_head_sha256':p['promotion_head_sha256']}
