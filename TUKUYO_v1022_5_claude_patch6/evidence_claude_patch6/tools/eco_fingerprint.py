"""Fingerprint of research-agent behaviour on development worlds (devkey, seeds 1000-1013): every episode's
full result, hashed. An exact refactor must reproduce it bit for bit."""
import hashlib,json,sys,time
sys.path.insert(0,sys.argv[1])
from tukuyo_v1023r.worlds import DeviceWorld
from tukuyo_v1023r.ecology import run_episode,REGIMES
t=time.time();rows=[]
for reg,econ in REGIMES.items():
    for s in range(1000,1000+int(sys.argv[2]) if len(sys.argv)>2 else 1014):
        for tier in (1,2,3,4):
            for noise in (0.0,0.05,0.1):
                for pol in ('research','random_research','doing'):
                    r=run_episode(DeviceWorld('devkey',s,tier,noise),pol,econ=econ,seed=s)
                    rows.append({k:r.get(k) for k in ('policy','alive','final_energy','actions','law_claimed','law_correct','status','method','events')})
print(json.dumps({'episodes':len(rows),'sha256':hashlib.sha256(json.dumps(rows,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'seconds':round(time.time()-t,1)}))
