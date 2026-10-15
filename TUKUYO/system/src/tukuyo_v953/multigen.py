"""v951-v953 bounded three-generation improver chain."""
from __future__ import annotations
from tukuyo_v950.improver import config0,propose_next,benchmark

def evolve(generations=3):
 if generations<1 or generations>3:raise ValueError('GENERATION_BOUND')
 cfg=config0();chain=[]
 for g in range(1,generations+1):
  p=propose_next(cfg)
  if not p.get('improved'):break
  chain.append({'generation':g,'edit':p['edit'],'before_effort':p['before']['effort'],'after_effort':p['after']['effort'],'before_generated':p['before']['generated'],'after_generated':p['after']['generated']})
  cfg=p['next_config']
 # blind inputs differ from optimizer inputs; same frozen benchmark tasks, no retraining here
 blind=tuple((i-9,((i*5+1)%17)-8) for i in range(22));b=benchmark(cfg,blind)
 return {'schema':'tukuyo.v953.multigen_improver/1','generations_completed':len(chain),'chain':chain,'final_config':{k:list(v) if isinstance(v,tuple) else v for k,v in cfg.items()},'blind':b,
         'scope':'FINITE_POLICY_SPACE_BOUNDED_META_IMPROVEMENT','code_self_rewrite':False,'general_l6':False}
