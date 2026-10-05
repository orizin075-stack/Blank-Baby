from __future__ import annotations
from pathlib import Path

def audit(data):
 d=Path(data);checks={};errors=[]
 def run(name,exists,fn):
  if not exists:checks[name]={'present':False,'ok':None};return
  try:r=fn();ok=bool(r.get('ok'));checks[name]={'present':True,'ok':ok,'errors':r.get('errors',[])}
  except Exception as e:ok=False;checks[name]={'present':True,'ok':False,'errors':[type(e).__name__+':'+str(e)]}
  if not ok:errors.append(name)
 from tukuyo_v978.heart_loop import audit as a978
 from tukuyo_v979.deep_core import audit as a979
 from tukuyo_v982.continuity_ledger import audit as a982
 from tukuyo_v983.homeostasis import audit as a983
 from tukuyo_v989.temporal_identity import audit as a989
 from tukuyo_v993.relation_bound import audit as a993
 from tukuyo_v995.other_agent_trust import audit as a995
 from tukuyo_v996.conversational_grounding import audit as a996
 from tukuyo_v998.semantic_inference import audit as a998
 from tukuyo_v977.whole_state import audit as whole
 run('heart',(d/'v978/HEART_STATE.json').exists(),lambda:a978(d))
 run('deep_soul',(d/'v979/DEEP_SOUL_CORE.json').exists(),lambda:a979(d))
 run('continuity_ledger',(d/'v982/HEAD.json').exists(),lambda:a982(d))
 run('homeostasis',(d/'v983/HOMEOSTASIS_STATE.json').exists(),lambda:a983(d))
 run('temporal_identity',(d/'v989/TEMPORAL_IDENTITY.json').exists(),lambda:a989(d))
 run('relation',(d/'v993/RELATION_BOUND_STATE.json').exists(),lambda:a993(d))
 run('peer',(d/'v995/OTHER_AGENT_MODELS.json').exists(),lambda:a995(d))
 run('conversation',(d/'v996/CONVERSATION_GROUNDING_EVENTS.jsonl').exists(),lambda:a996(d))
 run('semantic_inference',(d/'v998/SEMANTIC_INFERENCE_EVENTS.jsonl').exists(),lambda:a998(d))
 run('whole',(d/'v977/UNIFIED_STATE.json').exists(),lambda:whole(d))
 return {'ok':not errors,'version':'v1012.1','errors':errors,'checks':checks,
  'claim_boundary':{'legacy_capability_reintegrated_into_audit_surface':True,'external_anchor_authenticity_requires_external_key':True,'general_l5':False,'literal_life_established':False,'literal_soul_established':False}}
