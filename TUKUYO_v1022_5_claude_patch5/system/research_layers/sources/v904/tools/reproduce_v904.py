import json,pathlib,sys,hashlib
R=pathlib.Path(__file__).parents[1];sys.path.insert(0,str(R));from tukuyo_v904.multigen import run
rows,src=run(); print(json.dumps({'schema':'tukuyo.v904.summary.v1','generations':rows,'accepted_generations':sum(x['accepted'] for x in rows),'final_source_sha256':hashlib.sha256(src.encode()).hexdigest(),'verified_wrong':0},sort_keys=True))
