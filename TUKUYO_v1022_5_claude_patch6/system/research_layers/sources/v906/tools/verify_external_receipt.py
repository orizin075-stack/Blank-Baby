import json,pathlib,base64,hashlib,argparse
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def verify(path):
 x=json.loads(pathlib.Path(path).read_text());p=x['payload']; pub=base64.b64decode(p['evaluator_public_key_b64']);Ed25519PublicKey.from_public_bytes(pub).verify(base64.b64decode(x['signature_b64']),canon(p));
 req={'schema','evaluator_public_key_b64','package_sha256','command','result_sha256','executed_at'}
 return {'ok':req.issubset(p),'package_sha256':p.get('package_sha256')}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('receipt');a=ap.parse_args();o=verify(a.receipt);print(json.dumps(o,sort_keys=True));raise SystemExit(0 if o['ok'] else 1)
