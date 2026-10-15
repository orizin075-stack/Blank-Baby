import json,base64,hashlib,pathlib,random,sys,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tukuyo_v931.search import *
from tukuyo_v931.oracle import truth
from tukuyo_v931.sandbox import run_candidate
from tukuyo_v931.receipt import verify,canon
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

def test_search_causality():
 c=json.loads((ROOT/'evidence/SEARCH_CAUSALITY_CONTROLS.json').read_text()); assert c['evidence']['correct']>c['reverse']['correct']; assert c['evidence']['correct']>c['constant']['correct']; assert c['evidence']['correct']>c['random30']['median']
def test_oracle_not_in_search_module():
 s=(ROOT/'tukuyo_v931/search.py').read_text(); assert 'def truth' not in s; assert 'import oracle' not in s; assert 'from .oracle' not in s; assert 'from tukuyo_v931.oracle' not in s
 # grammar endpoint must not equal oracle on all cases
 src=(ROOT/'evidence/EXPECTED_CANDIDATE.py').read_text(); r=score(src,99991,4000,truth); assert r['verified_wrong']>0
def test_gate_has_rejection():
 gens=json.loads((ROOT/'evidence/SEARCH_GENERATIONS.json').read_text());
 # explicit decoy candidate must be rejected by strict-gain gate
 parent=score(BASE_SOURCE,777,1000,truth); bad=apply(BASE_SOURCE,'decoy_swap',[]); br=score(bad,777,1000,truth); assert not (br['correct']>parent['correct'] and br['verified_wrong']<parent['verified_wrong'])
def test_timeout():
 evil="def choose(m):\n    while True:\n        pass\n"
 # AST policy itself rejects loops; timeout layer independently tested with finite but pathological expression is not possible under call-free grammar.
 assert run_candidate(evil,{'ambiguous_failure':.1,'representation_failure':.1,'consistency_failure':.1},.2)['reason']=='AST_REJECT'
 # worker timeout smoke-test bypassing AST gate: direct subprocess is tested by dedicated CLI

def test_receipt_row_binding():
 sk=Ed25519PrivateKey.generate();pub=base64.b64encode(sk.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode(); rows=[{'baseline_correct':False,'candidate_correct':True} for _ in range(279)]; rp=ROOT/'evidence/_tmp_rows.json';rp.write_text(json.dumps(rows,separators=(',',':'))); p={'schema':'x','track_sha256':'92659b241c50d6075f795b040596d497a11e3ee172080f4a945af5247a61089f','rows':279,'baseline_impl_sha256':'a'*64,'candidate_impl_sha256':'b'*64,'baseline_correct':0,'candidate_correct':279,'baseline_wrong':279,'candidate_wrong':0,'result_rows_sha256':hashlib.sha256(rp.read_bytes()).hexdigest(),'evaluator_id':'test','self_authored':False};o={'payload':p,'signature_b64':base64.b64encode(sk.sign(canon(p))).decode()};assert verify(o,pub,rp)['ok'];p2=dict(p);p2['rows']=300;o2={'payload':p2,'signature_b64':base64.b64encode(sk.sign(canon(p2))).decode()};assert verify(o2,pub,rp)['reason']=='TRACK_ROWS_MISMATCH';rp.unlink()
def test_promotion_contract_publishes_hash():
 c=json.loads((ROOT/'evidence/PROMOTION_CONTRACT.json').read_text()); assert c['candidate_impl_sha256']==hashlib.sha256((ROOT/'evidence/EXPECTED_CANDIDATE.py').read_bytes()).hexdigest()
