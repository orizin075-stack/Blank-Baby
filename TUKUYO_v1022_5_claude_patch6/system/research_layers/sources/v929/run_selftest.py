import json
from tukuyo_v929.wallclock import validate
r=validate();ok=r['start_hash_match'] and r['start_time_match'] and r['forks_match'] and not r['completed'] and r['external_time_anchor']=='PENDING'
print(json.dumps({'ok':ok,**r},sort_keys=True));raise SystemExit(0 if ok else 1)
