import base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from .util import canonical
def keygen():
 sk=Ed25519PrivateKey.generate();pk=sk.public_key()
 return (base64.b64encode(sk.private_bytes(serialization.Encoding.Raw,serialization.PrivateFormat.Raw,serialization.NoEncryption())).decode(),base64.b64encode(pk.public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode())
def pub(sk):
 s=Ed25519PrivateKey.from_private_bytes(base64.b64decode(sk));return base64.b64encode(s.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode()
def sign(sk,obj):return base64.b64encode(Ed25519PrivateKey.from_private_bytes(base64.b64decode(sk)).sign(canonical(obj))).decode()
def verify(pk,obj,sig):
 try:Ed25519PublicKey.from_public_bytes(base64.b64decode(pk)).verify(base64.b64decode(sig),canonical(obj));return True
 except Exception:return False
