import base64,json,sys,tempfile,pathlib,hashlib,shutil
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tukuyo_research_v937.challenge import sign_evaluation,verify,dataset
from tukuyo_research_v936.evaluator import rows

def setup_case(tmp):
    key=Ed25519PrivateKey.generate()
    pub=key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    priv=key.private_bytes(serialization.Encoding.Raw,serialization.PrivateFormat.Raw,serialization.NoEncryption())
    (tmp/'key').write_bytes(priv)
    cases=[{'case_id':f'c{i}','input':m,'truth':truth} for i,(m,truth) in enumerate(rows('coupled_product',27001,140,'edges'))]
    data=tmp/'external.jsonl'
    data.write_text(''.join(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n' for x in cases))
    out=tmp/'results'
    sign_evaluation(ROOT,'coupled_product',data,tmp/'key',out,'INTERNAL_TEST_NOT_EXTERNAL')
    return data,out,base64.b64encode(pub).decode()

def check(data,out,pub):
    return verify(ROOT,'coupled_product',data,out/'RESULT_ROWS.json',out/'EVALUATION_RECEIPT.json',pub)

def test_sign_verify_and_incorrect_key():
    with tempfile.TemporaryDirectory() as s:
        tmp=pathlib.Path(s);d,o,p=setup_case(tmp);assert check(d,o,p)['ok']
        fake=Ed25519PrivateKey.generate().public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
        assert not check(d,o,base64.b64encode(fake).decode())['ok']

def test_tampered_dataset_and_row():
    with tempfile.TemporaryDirectory() as s:
        tmp=pathlib.Path(s);d,o,p=setup_case(tmp)
        lines=d.read_text().splitlines();row=json.loads(lines[0]);row['truth']='hold' if row['truth']!='hold' else 'audit';lines[0]=json.dumps(row)
        d.write_text('\n'.join(lines)+'\n');assert not check(d,o,p)['ok']
        # Restore via fresh setup, then forge a row while preserving signature.
        d,o,p=setup_case(tmp);rp=o/'RESULT_ROWS.json';rr=json.loads(rp.read_text());rr[0]['correct']=not rr[0]['correct'];rp.write_text(json.dumps(rr)+'\n')
        assert check(d,o,p)['reason']=='RESULT_ROWS_MISMATCH'

def test_candidate_mutation_rejected():
    with tempfile.TemporaryDirectory() as s:
        tmp=pathlib.Path(s);d,o,p=setup_case(tmp)
        clean=tmp/'candidate_copy'
        for rel in ('challenge/CHALLENGE_CONTRACT.json','evidence/coupled_product_model.json','evidence/coupled_product_source.py'):
            target=clean/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,target)
        candidate=clean/'evidence/coupled_product_source.py'
        candidate.write_bytes(candidate.read_bytes()+b'\n# forged\n')
        result=verify(clean,'coupled_product',d,o/'RESULT_ROWS.json',o/'EVALUATION_RECEIPT.json',p)
        assert result['reason'].startswith('EVALUATION_RECOMPUTE')

def test_bad_inputs_duplicate_keys_and_self_authority():
    with tempfile.TemporaryDirectory() as s:
        tmp=pathlib.Path(s);d,o,p=setup_case(tmp)
        d.write_text('{"case_id":"1","case_id":"2","input":{"a":0.1,"b":0.2,"c":0.2},"truth":"audit"}\n')
        try:dataset(d)
        except ValueError:pass
        else:raise AssertionError('duplicate key accepted')
        # The independent public key is supplied through caller, never from the untrusted receipt.
        assert not check(d,o,p)['ok']

def test_contract_and_parent_sha_are_pinned():
    c=json.loads((ROOT/'challenge/CHALLENGE_CONTRACT.json').read_text())
    assert len(c['parent_v936_zip_sha256'])==64
    assert c['third_party_receipt_status']=='PENDING'
    s=json.loads((ROOT/'STATUS.json').read_text())
    assert s['general_l6_established'] is False and s['active_policy_promotion']=='BLOCKED_NONREGRESSION'
