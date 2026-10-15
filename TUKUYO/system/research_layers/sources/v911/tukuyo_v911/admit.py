import hashlib,json,pathlib
TRACKS={'H3_CORRECTED':{'sha256':'37fa9e81f4ee8eb41e27075c1f404791c99b7c3c021972a565ba2b7ce27ac95e','rows':300},'H3_DEDUP':{'sha256':'92659b241c50d6075f795b040596d497a11e3ee172080f4a945af5247a61089f','rows':279}}
def sha256(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def admit(path,track):
 if track not in TRACKS:return {'ok':False,'reason':'UNKNOWN_TRACK'}
 p=pathlib.Path(path)
 if not p.is_file(): return {'ok':False,'reason':'MISSING_FILE'}
 got=sha256(p); spec=TRACKS[track]
 if got!=spec['sha256']: return {'ok':False,'reason':'SHA_MISMATCH','sha256':got}
 try: rows=json.loads(p.read_text(encoding='utf-8'))
 except Exception:return {'ok':False,'reason':'JSON_PARSE'}
 if not isinstance(rows,list) or len(rows)!=spec['rows']: return {'ok':False,'reason':'ROW_COUNT'}
 return {'ok':True,'track':track,'sha256':got,'rows':len(rows)}
