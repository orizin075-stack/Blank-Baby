from __future__ import annotations
import base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from .util import canonical

def new_keypair():
    sk=Ed25519PrivateKey.generate()
    sk_b=sk.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    pk_b=sk.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return base64.b64encode(sk_b).decode(), base64.b64encode(pk_b).decode()

def pub_from_private(sk64):
    sk=Ed25519PrivateKey.from_private_bytes(base64.b64decode(sk64))
    return base64.b64encode(sk.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()

def sign_obj(sk64,obj):
    sk=Ed25519PrivateKey.from_private_bytes(base64.b64decode(sk64))
    return base64.b64encode(sk.sign(canonical(obj))).decode()

def verify_obj(pk64,obj,sig64):
    try:
        Ed25519PublicKey.from_public_bytes(base64.b64decode(pk64)).verify(base64.b64decode(sig64),canonical(obj)); return True
    except Exception: return False
