import json,pathlib,sys,hashlib
ROOT=pathlib.Path(__file__).parents[1];sys.path.insert(0,str(ROOT));from tukuyo_v903.improver import candidate_sources;from tukuyo_v903.eval import score
rows=[]
for name,src in candidate_sources().items():
 vals=[score(src,s) for s in (90301,90302,90303,90304)]; rows.append({'name':name,'source_sha256':hashlib.sha256(src.encode()).hexdigest(),'correct':sum(x[0] for x in vals),'wrong':sum(x[1] for x in vals)})
best=max(rows,key=lambda x:(x['correct'],-x['wrong'])); out={'schema':'tukuyo.v903.summary.v1','candidates':rows,'promoted':best,'verified_wrong':best['wrong'],'scope':'PREDEFINED_SOURCE_TRANSFORM_LIBRARY'}; print(json.dumps(out,sort_keys=True))
