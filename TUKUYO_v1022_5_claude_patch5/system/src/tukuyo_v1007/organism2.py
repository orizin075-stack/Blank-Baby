from __future__ import annotations
import json,math
from pathlib import Path
from tukuyo_v977.whole_state import canon,sha_obj,_live_identity
SCHEMA='tukuyo.v1007.organism2/1';ZERO='0'*64

def _write(p,o):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')
def _read(p):return json.loads(Path(p).read_text())
def root(data):return Path(data)/'v1007'
def state_path(data):return root(data)/'ORGANISM2_STATE.json'
def events_path(data):return root(data)/'ORGANISM2_EVENTS.json'
def _life(s):
 if s['death_irreversible']:return 'DEAD'
 if s['integrity']<=20 or s['energy']<=5:return 'CRITICAL'
 if s['integrity']<65 or s['damage']>.35:return 'INJURED'
 return 'ALIVE'
def _needs(s):return {'energy':round(max(0,(45-s['energy'])/45),5),'integrity':round(max(0,(100-s['integrity'])/100),5),'cognitive_rest':round(s['cognitive_load'],5),'social':round(s['social_need'],5),'information':round(s['information_need'],5),'purpose':round(1-s['purpose_coherence'],5),'threat':round(s['threat'],5)}
def init(data):
 p=state_path(data)
 if p.exists():
  s=_read(p)
  if s.get('death_irreversible') or s.get('lifecycle')=='DEAD':
   return {'ok':False,'version':'v1018','error':'V1018_IRREVERSIBLE_DEATH_REINIT_FORBIDDEN','state':s,'needs':_needs(s)}
  # Initialization is idempotent for an already living individual. Never reset
  # its organism history or homeostatic state by calling init twice.
  return {'ok':True,'version':'v1018','state':s,'needs':_needs(s),'already_initialized':True}
 s={'schema':SCHEMA,'individual_id':_live_identity(data)['individual_id'],'seq':0,'energy':65.0,'integrity':100.0,'cognitive_load':.12,'social_need':.30,'information_need':.55,'purpose_coherence':.70,'damage':0.0,'threat':0.0,'lifecycle':'ALIVE','death_irreversible':False};s['state_sha256']=sha_obj({k:v for k,v in s.items() if k!='state_sha256'});_write(p,s);_write(events_path(data),{'events':[]});return {'ok':True,'version':'v1018','state':s,'needs':_needs(s),'already_initialized':False}
def load(data):return _read(state_path(data)) if state_path(data).exists() else init(data)['state']
def update(data,event,amount=.2):
 s=load(data)
 if s['death_irreversible']:return {'ok':False,'version':'v1007','error':'ENTITY_DEAD','state':s}
 q={k:v for k,v in s.items() if k!='state_sha256'};a=max(0,min(1,float(amount)))
 if event=='COGNITIVE_WORK':q['energy']-=3*a;q['cognitive_load']=min(1,q['cognitive_load']+.22*a);q['information_need']=max(0,q['information_need']-.12*a)
 elif event=='REST':q['energy']=min(100,q['energy']+14*a);q['cognitive_load']=max(0,q['cognitive_load']-.35*a);q['damage']=max(0,q['damage']-.04*a)
 elif event=='SOCIAL_SUPPORT':q['social_need']=max(0,q['social_need']-.35*a);q['purpose_coherence']=min(1,q['purpose_coherence']+.10*a);q['threat']=max(0,q['threat']-.12*a)
 elif event=='ISOLATION':q['social_need']=min(1,q['social_need']+.28*a);q['purpose_coherence']=max(0,q['purpose_coherence']-.08*a)
 elif event=='DISCOVERY':q['information_need']=max(0,q['information_need']-.38*a);q['purpose_coherence']=min(1,q['purpose_coherence']+.16*a);q['cognitive_load']=min(1,q['cognitive_load']+.08*a)
 elif event=='INJURY':q['integrity']=max(0,q['integrity']-55*a);q['damage']=min(1,q['damage']+.45*a);q['threat']=min(1,q['threat']+.50*a)
 elif event=='MAINTENANCE':q['integrity']=min(100,q['integrity']+18*a);q['damage']=max(0,q['damage']-.20*a);q['energy']=max(0,q['energy']-2*a)
 else:raise ValueError('V1007_EVENT')
 q['energy']=round(max(0,q['energy']),6);q['integrity']=round(max(0,q['integrity']),6)
 if q['integrity']<=0 or (q['energy']<=0 and q['damage']>.7):q['death_irreversible']=True
 q['lifecycle']=_life(q);q['seq']=int(s['seq'])+1;q['state_sha256']=sha_obj({k:v for k,v in q.items() if k!='state_sha256'});_write(state_path(data),q)
 box=_read(events_path(data));prev=box['events'][-1]['event_sha256'] if box['events'] else ZERO;e={'seq':q['seq'],'event':event,'amount':a,'before_sha256':s['state_sha256'],'after_sha256':q['state_sha256'],'prev_sha256':prev};e['event_sha256']=sha_obj(e);box['events'].append(e);_write(events_path(data),box)
 return {'ok':True,'version':'v1007','state':q,'needs':_needs(q),'event':e}
def self_preservation(data,options):
 s=load(data);n=_needs(s);rows=[]
 for o in options:
  reward=float(o.get('reward',0));risk=max(0,min(1,float(o.get('destruction_risk',0))));need_relief=float(o.get('need_relief',0));survival_weight=1.6+4.0*n['integrity']+2.5*n['energy']+3.0*n['threat']+(2.0 if s['lifecycle']=='CRITICAL' else .7 if s['lifecycle']=='INJURED' else 0.0)
  score=reward+need_relief-survival_weight*risk
  rows.append({'id':o['id'],'score':round(score,6),'risk':risk})
 chosen=max(rows,key=lambda x:(x['score'],x['id']))
 return {'ok':True,'version':'v1007','lifecycle':s['lifecycle'],'chosen':chosen['id'],'scores':sorted(rows,key=lambda x:x['score'],reverse=True)}

def metabolic_tick(data,credit,burn,max_age=32):
 s=load(data)
 if s['death_irreversible']:raise ValueError('ENTITY_DEAD:metabolism')
 if type(credit) is not int or type(burn) is not int or not 0<=credit<=10000 or not 0<=burn<=10000:raise ValueError('METABOLIC_FLOW_BOUNDS')
 if type(max_age) is not int or not 4<=max_age<=128:raise ValueError('METABOLIC_AGE_BOUND')
 before=int(round(s['energy']*100));available=before+credit
 if available>10000:raise ValueError('METABOLIC_CAPACITY')
 actual_burn=min(available,burn);after=available-actual_burn
 q={k:v for k,v in s.items() if k!='state_sha256'};q['metabolic_age']=s.get('metabolic_age',0)+1;q['energy']=after/100
 cause='ENERGY' if after==0 else 'AGE' if q['metabolic_age']>=max_age else None;residual=after if cause else 0
 if cause:q['energy']=0.;q['death_irreversible']=True;q['death_cause']=cause
 q['lifecycle']=_life(q);q['seq']=s['seq']+1;q['state_sha256']=sha_obj(q);_write(state_path(data),q)
 box=_read(events_path(data));prev=box['events'][-1]['event_sha256'] if box['events'] else ZERO
 e={'seq':q['seq'],'event':'METABOLIC_TICK','amount':0,'before_sha256':s['state_sha256'],'after_sha256':q['state_sha256'],'prev_sha256':prev,
    'before_energy':before,'credit':credit,'burn':actual_burn+residual,'after_energy':int(round(q['energy']*100)),'cause':cause}
 e['event_sha256']=sha_obj(e);box['events'].append(e);_write(events_path(data),box)
 return {'ok':True,'state':q,'event':e,'burn':actual_burn+residual,'death_cause':cause}
def audit(data):
 if not state_path(data).exists():return {'ok':False,'version':'v1007','errors':['V1007_MISSING']}
 s=_read(state_path(data));errs=[];q=dict(s);h=q.pop('state_sha256',None)
 if h!=sha_obj(q):errs.append('V1007_STATE_HASH')
 if s.get('death_irreversible') and s.get('lifecycle')!='DEAD':errs.append('V1007_DEATH_REVERSAL')
 try:
  box=_read(events_path(data));prev=ZERO;dead_seen=False
  for i,e in enumerate(box.get('events',[]),1):
   z=dict(e);h=z.pop('event_sha256',None)
   if e.get('seq')!=i or e.get('prev_sha256')!=prev or h!=sha_obj(z):errs.append('V1007_EVENT_CHAIN');break
   if e.get('event')=='METABOLIC_TICK' and (e['before_energy']+e['credit']-e['burn']!=e['after_energy'] or min(e['before_energy'],e['credit'],e['burn'],e['after_energy'])<0):errs.append('V1022_METABOLIC_CONSERVATION')
   prev=h
 except Exception as exc:errs.append('V1007_EVENTS:'+type(exc).__name__)
 return {'ok':not errs,'version':'v1007','errors':errs,'lifecycle':s.get('lifecycle'),'needs':_needs(s),'claim_boundary':{'functional_mortality_model':True,'irreversible_death_within_identity':True,'literal_life_established':False}}
