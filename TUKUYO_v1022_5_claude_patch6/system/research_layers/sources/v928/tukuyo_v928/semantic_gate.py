import hashlib,json,pathlib
EXPECT=json.loads(pathlib.Path(__file__).resolve().parents[1].joinpath('evidence/CANONICAL_SEMANTIC_EXPECTATIONS.json').read_text())
def inspect(path):
 p=pathlib.Path(path)
 if not p.is_file():return {'accepted':False,'reason':'MISSING'}
 h=hashlib.sha256(p.read_bytes()).hexdigest();m=[x for x in EXPECT['assets'] if x.get('sha256_full') and h==x['sha256_full']]
 return {'accepted':bool(m),'reason':'MATCH' if m else 'HASH_NOT_CANONICAL','sha256':h}
