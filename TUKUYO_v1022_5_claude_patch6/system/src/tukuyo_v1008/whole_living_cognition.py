from __future__ import annotations
import json
from pathlib import Path
from tukuyo_v977.whole_state import canon,sha_obj,_live_identity,load_soul
from tukuyo_v1005.verifier import solve
from tukuyo_v1006.research_agent import assay as research_assay
from tukuyo_v1007.organism2 import load as load_org,init as init_org,update as update_org,audit as org_audit
SCHEMA='tukuyo.v1008.whole_living_cognition/1'
def _write(p,o):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')
def cycle(data,query='What should I do next?'):
 if not (Path(data)/'v1007'/'ORGANISM2_STATE.json').exists():init_org(data)
 before=load_org(data)
 if before['lifecycle']=='DEAD':return {'ok':False,'version':'v1008','error':'ENTITY_DEAD'}
 # cognition consumes energy; research satisfies information need when high.
 update_org(data,'COGNITIVE_WORK',.5);mid=load_org(data);research=None
 if mid['information_need']>.35:
  research=research_assay(data);update_org(data,'DISCOVERY',.45 if research.get('ok') else .1)
 reasoning=solve(data,query,1);after=load_org(data)
 # homeostatic autonomous internal choice only; no external side effect.
 if after['energy']<28 or after['cognitive_load']>.72:update_org(data,'REST',.65);maintenance='REST'
 elif after['integrity']<75 or after['damage']>.25:update_org(data,'MAINTENANCE',.55);maintenance='MAINTENANCE'
 else:maintenance='NONE'
 final=load_org(data);out={'schema':SCHEMA,'individual_id':_live_identity(data)['individual_id'],'query':query,'reasoning':{'answer':reasoning['answer'],'confidence':reasoning['confidence'],'uncertain':reasoning['uncertain']},'research':None if research is None else {'passed':research['passed'],'total':research['total']},'organism_before':before,'organism_after':final,'autonomous_internal_maintenance':maintenance,'external_action_taken':False};out['result_sha256']=sha_obj(out);_write(Path(data)/'v1008'/'LAST_CYCLE.json',out);return {'ok':True,'version':'v1008',**out}
def audit(data):
 p=Path(data)/'v1008'/'LAST_CYCLE.json';errs=[]
 if not p.exists():return {'ok':False,'version':'v1008','errors':['V1008_MISSING']}
 x=json.loads(p.read_text());q=dict(x);h=q.pop('result_sha256',None)
 if h!=sha_obj(q):errs.append('V1008_HASH')
 oa=org_audit(data)
 if not oa.get('ok'):errs.append('V1008_ORGANISM')
 if x.get('external_action_taken') is not False:errs.append('V1008_EXTERNAL_ACTION')
 return {'ok':not errs,'version':'v1008','errors':errs,'lifecycle':oa.get('lifecycle'),'claim_boundary':{'integrated_cognition_research_homeostasis':True,'autonomous_internal_maintenance':True,'unattended_external_action':False,'consciousness_established':False,'literal_life_established':False}}

def successor_seed(data,successor_id):
 final=load_org(data)
 if final.get('lifecycle')!='DEAD' or not final.get('death_irreversible'):raise ValueError('SUCCESSOR_REQUIRES_IRREVERSIBLE_DEATH')
 if not successor_id or successor_id==final.get('individual_id'):raise ValueError('SUCCESSOR_DISTINCT_ID_REQUIRED')
 soul=load_soul(data)
 seed={'schema':'tukuyo.v1008.successor_seed/1','parent_individual_id':final['individual_id'],'successor_individual_id':successor_id,'same_identity':False,'parent_is_dead':True,'episodic_memory_inherited':False,'inherited_value_bias':{k:round(float(v)*0.35,6) for k,v in soul.get('core_values',{}).items()},'parent_organism_sha256':final['state_sha256'],'lineage_relation':'SUCCESSOR_NOT_RESURRECTION'}
 seed['seed_sha256']=sha_obj(seed);_write(Path(data)/'v1008'/'SUCCESSOR_SEED.json',seed);return {'ok':True,'version':'v1008','successor_seed':seed}
