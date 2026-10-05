from .dsl import *
def classify(d,obs):
 base=[p for p in base_programs(d) if all(run(p,x)==y for x,y in obs)]
 if base:return {'label':'BASE_REPRESENTABLE','matches':base}
 comp=[p for p in composed_programs(d) if all(run(p,x)==y for x,y in obs)]
 if comp:return {'label':'SEARCH_INSUFFICIENT_FOR_BASE_ONLY_SEARCH','matches':comp}
 return {'label':'REPRESENTATION_INSUFFICIENT_WITHIN_DEPTH2_DSL','matches':[]}
