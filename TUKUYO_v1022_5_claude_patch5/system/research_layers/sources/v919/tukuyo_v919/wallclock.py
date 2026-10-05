import datetime,json,pathlib,time
P=pathlib.Path('evidence/WALLCLOCK30_START.json')
def status(now=None):
 s=json.loads(P.read_text()); now=int(time.time()) if now is None else int(now);elapsed=max(0,now-s['started_at_unix']);return {'elapsed_seconds':elapsed,'required_seconds':s['required_seconds'],'completed':elapsed>=s['required_seconds'],'external_time_anchor':s['external_time_anchor'],'forks':len(s['forks'])}
