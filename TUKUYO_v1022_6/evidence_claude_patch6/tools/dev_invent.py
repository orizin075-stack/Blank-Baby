"""dev worlds only (key 'devkey'): research agent with law invention on vs off, same worlds, per tier"""
import collections,json,sys,time
sys.path.insert(0,sys.argv[1])
from tukuyo_v1023r.worlds import DeviceWorld
from tukuyo_v1023r.ecology import run_episode,REGIMES
seeds=range(int(sys.argv[2]),int(sys.argv[3]));pols=sys.argv[4].split(',') if len(sys.argv)>4 else ['research']
agg=collections.defaultdict(collections.Counter);wrong=[];diff=collections.Counter();t=time.time();slow=[]
for reg,econ in REGIMES.items():
    for s in seeds:
        for tier in (1,2,3,4,5):
            for noise in (0.0,0.05,0.1):
                for pol in pols:
                    out={}
                    for inv in (False,True):
                        t1=time.time();r=run_episode(DeviceWorld('devkey',s,tier,noise),pol,econ=econ,seed=s,invent=inv);dt=time.time()-t1
                        if dt>1.0:slow.append((reg,s,tier,noise,pol,inv,round(dt,2)))
                        c=agg[(pol,tier,inv)];c['n']+=1;c['alive']+=r['alive'];c['energy']+=r['final_energy'];c['claimed']+=r['law_claimed'];c['correct']+=r['law_correct']
                        c['wrong']+=r['wrong_law_claimed'];c['table']+=r['unexplained'];c['invented']+=r.get('invented_claim',False);c['exp']+=r['actions']['probe']+r['actions']['trial']
                        if r['wrong_law_claimed']:wrong.append({'reg':reg,'seed':s,'tier':tier,'noise':noise,'pol':pol,'invent':inv,'claim':r['claim']['law'],'events':r['events'][-12:]})
                        out[inv]=(r['alive'],r['final_energy'],r['law_claimed'],r['law_correct'],r['status'],r['method'])
                    diff[(pol,tier,out[False]==out[True])]+=1
print('seconds',round(time.time()-t,1))
for (pol,tier,inv),c in sorted(agg.items()):
    n=c['n'];print(f"{pol:16s} tier{tier} invent={int(inv)} n={n} alive={c['alive']} energy={c['energy']/n:7.1f} claimed={c['claimed']} correct={c['correct']} wrong={c['wrong']} table={c['table']} invented={c['invented']} exp={c['exp']/n:5.1f}")
print('identical outcome on/off:',{f'{p}|t{t}':(diff[(p,t,True)],diff[(p,t,False)]) for p in pols for t in (1,2,3,4,5)})
print('WRONG',json.dumps(wrong,ensure_ascii=False,indent=0))
print('slow',slow[:20])
