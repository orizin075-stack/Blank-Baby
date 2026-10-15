import base64,json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from tukuyo_v912.receipt import verify,canon
k=Ed25519PrivateKey.generate();pub=base64.b64encode(k.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode()
p={'schema':'tukuyo.external_semantic_evaluation_receipt.v2','track_sha256':'92659b241c50d6075f795b040596d497a11e3ee172080f4a945af5247a61089f','rows':279,'baseline_impl_sha256':'a'*64,'candidate_impl_sha256':'b'*64,'baseline_correct':161,'candidate_correct':187,'baseline_wrong':0,'candidate_wrong':0,'result_rows_sha256':'c'*64,'evaluator_id':'SELFTEST_ONLY','self_authored':True}
o={'payload':p,'signature_b64':base64.b64encode(k.sign(canon(p))).decode()};r=verify(o,pub);ok=(not r['ok'] and r['reason']=='SELF_AUTHORED');print(json.dumps({'ok':ok,'mechanism_signature_tested':True,'external_evidence_created':False},sort_keys=True));raise SystemExit(0 if ok else 1)
