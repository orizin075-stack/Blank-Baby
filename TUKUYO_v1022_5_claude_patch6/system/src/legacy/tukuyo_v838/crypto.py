from __future__ import annotations
import base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from .util import canonical

def new_keypair():
    sk=Ed25519PrivateKey.generate(); sb=sk.private_bytes(serialization.Encoding.Raw,serialization.PrivateFormat.Raw,serialization.NoEncryption()); pb=sk.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    return base64.b64encode(sb).decode(),base64.b64encode(pb).decode()
def sign_obj(sk64,obj): return base64.b64encode(Ed25519PrivateKey.from_private_bytes(base64.b64decode(sk64)).sign(canonical(obj))).decode()
def verify_obj(pk64,obj,sig64):
    try: Ed25519PublicKey.from_public_bytes(base64.b64decode(pk64)).verify(base64.b64decode(sig64),canonical(obj)); return True
    except Exception: return False
