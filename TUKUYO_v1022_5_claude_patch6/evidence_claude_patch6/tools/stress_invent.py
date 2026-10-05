"""soundness stress on dev worlds (key 'devkey', seeds 2000+): invention on, tiers 4-5, all learning policies; any wrong claim is printed"""
import collections,json,sys,time
sys.path.insert(0,sys.argv[1])
from tukuyo_v1023r.worlds import DeviceWorld
from tukuyo_v1023r.ecology import run_episode,REGIMES
t=time.time();agg=collections.Counter();wrong=[]
for reg,econ in REGIMES.items():
    for s in range(int(sys.argv[2]),int(sys.argv[3])):
        for tier in (4,5):
            for noise in (0.0,0.05,0.1):
                for pol in ('research','random_research','doing'):
                    r=run_episode(DeviceWorld('devkey',s,tier,noise),pol,econ=econ,seed=s)
                    agg[(pol,tier,'n')]+=1;agg[(pol,tier,'correct')]+=r['law_correct'];agg[(pol,tier,'wrong')]+=r['wrong_law_claimed']
                    agg[(pol,tier,'bound_violation')]+=r.get('claim_bound_held') is False
                    if r['wrong_law_claimed']:wrong.append({'reg':reg,'seed':s,'tier':tier,'noise':noise,'pol':pol,'claim':r['claim']['law'],'truth':DeviceWorld('devkey',s,tier,noise).reveal()['law']})
print('seconds',round(time.time()-t,1))
for k in sorted(agg):print(k,agg[k])
print('WRONG',json.dumps(wrong,ensure_ascii=False))
