import hashlib,json,pathlib
def validate():
 r=pathlib.Path(__file__).resolve().parents[1];b=(r/'evidence/INHERITED_WALLCLOCK30_START.json').read_bytes();s=json.loads((r/'evidence/WALLCLOCK30_SNAPSHOT.json').read_text());o=json.loads(b)
 return {'start_hash_match':hashlib.sha256(b).hexdigest()==s['original_start_sha256'],'start_time_match':o['started_at_unix']==s['original_started_at_unix'],'forks_match':len(o['forks'])==s['forks'],'completed':s['completed'],'elapsed_seconds':s['elapsed_seconds'],'required_seconds':s['required_seconds'],'external_time_anchor':s['external_time_anchor']}
