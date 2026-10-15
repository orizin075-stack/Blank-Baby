import json
from tukuyo_v919.wallclock import status
r=status();ok=(r['forks']==2 and not r['completed'] and r['external_time_anchor']=='PENDING');print(json.dumps({'ok':ok,**r},sort_keys=True));raise SystemExit(0 if ok else 1)
