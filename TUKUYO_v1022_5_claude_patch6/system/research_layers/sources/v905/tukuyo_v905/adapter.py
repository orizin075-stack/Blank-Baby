import json,hashlib,pathlib
REQUIRED={'id','prompt','expected','must_abstain'}
def load_track(path,expected_sha256=None):
 p=pathlib.Path(path)
 if not p.is_file(): return {'ok':False,'reason':'TRACK_MISSING'}
 raw=p.read_bytes(); h=hashlib.sha256(raw).hexdigest()
 if expected_sha256 and h!=expected_sha256:return {'ok':False,'reason':'TRACK_SHA_MISMATCH','sha256':h}
 try: rows=json.loads(raw)
 except Exception:return {'ok':False,'reason':'TRACK_PARSE_ERROR','sha256':h}
 if not isinstance(rows,list) or not rows:return {'ok':False,'reason':'TRACK_EMPTY_OR_INVALID','sha256':h}
 if any(not REQUIRED.issubset(x) for x in rows):return {'ok':False,'reason':'TRACK_SCHEMA_MISMATCH','sha256':h}
 if len({x['id'] for x in rows})!=len(rows):return {'ok':False,'reason':'DUPLICATE_ID','sha256':h}
 return {'ok':True,'rows':len(rows),'sha256':h}
