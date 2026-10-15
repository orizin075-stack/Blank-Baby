from __future__ import annotations
import itertools,json,random
from pathlib import Path
from tukuyo_v977.whole_state import canon,sha_obj,_live_identity
SCHEMA='tukuyo.v1006.autonomous_research/1'
# Oracle is isolated from the learner: learner receives only query(x,y)->z.
OPS={'ADD':lambda x,y:x+y,'SUB':lambda x,y:x-y,'MUL':lambda x,y:x*y,'MAX':max,'MIN':min}
def _write(p,o):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')
def _domain(seed):
 r=random.Random(seed);op=r.choice(sorted(OPS));a=r.choice([-2,-1,1,2]);b=r.choice([-2,-1,0,1,2]);return {'op':op,'a':a,'b':b}
def _oracle(secret,x,y):return OPS[secret['op']](x,y)*secret['a']+secret['b']
def _candidates():return [{'op':o,'a':a,'b':b} for o,a,b in itertools.product(sorted(OPS),[-2,-1,1,2],[-2,-1,0,1,2])]
def _predict(c,x,y):return OPS[c['op']](x,y)*c['a']+c['b']
def discover(seed,budget=8):
 sec=_domain(seed);cands=_candidates();obs=[];pool=[(x,y) for x in range(-4,5) for y in range(-4,5) if not(x==0 and y==0)]
 for _ in range(min(budget,len(pool))):
  # choose probe maximizing disagreement among surviving hypotheses
  probe=max(pool,key=lambda p:len({_predict(c,*p) for c in cands}));pool.remove(probe);z=_oracle(sec,*probe);obs.append({'x':probe[0],'y':probe[1],'z':z});cands=[c for c in cands if _predict(c,*probe)==z]
  if len(cands)<=1:break
 chosen=cands[0] if len(cands)==1 else None;holds=[]
 for x,y in [(5,3),(-5,2),(4,-3),(-4,-2),(6,1),(-6,-1)]:holds.append(chosen is not None and _predict(chosen,x,y)==_oracle(sec,x,y))
 return {'seed':seed,'observations':obs,'remaining_hypotheses':len(cands),'discovered':chosen,'holdout_correct':sum(holds),'holdout_total':len(holds),'pass':bool(chosen) and all(holds)}
def assay(data,seeds=(100601,100602,100603,100604,100605,100606)):
 rows=[discover(int(s)) for s in seeds];out={'schema':SCHEMA,'individual_id':_live_identity(data)['individual_id'],'domains':rows,'passed':sum(r['pass'] for r in rows),'total':len(rows),'pass':all(r['pass'] for r in rows),'claim_boundary':{'bounded_symbolic_unknown_rule_research':True,'learner_has_no_direct_secret_access':True,'cross_domain_general_intelligence':False}};out['result_sha256']=sha_obj(out);_write(Path(data)/'v1006'/'RESEARCH_ASSAY.json',out);return {'ok':out['pass'],'version':'v1006',**out}
def audit(data):
 p=Path(data)/'v1006'/'RESEARCH_ASSAY.json'
 if not p.exists():return {'ok':False,'version':'v1006','errors':['V1006_MISSING']}
 x=json.loads(p.read_text());q=dict(x);h=q.pop('result_sha256',None);errs=[]
 if h!=sha_obj(q):errs.append('V1006_HASH')
 if x.get('passed')!=x.get('total'):errs.append('V1006_HOLDOUT')
 return {'ok':not errs,'version':'v1006','errors':errs,'passed':x.get('passed'),'total':x.get('total')}
