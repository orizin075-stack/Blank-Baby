import json,pathlib,sys,hashlib
R=pathlib.Path(__file__).parents[1];sys.path.insert(0,str(R));from tukuyo_v909.run import run
rows,src,calls=run();gain=rows[-1]['best_candidate_correct']-rows[0]['parent_correct'];print(json.dumps({'schema':'tukuyo.v909.summary.v1','generations':rows,'evaluation_calls':calls,'net_correct_gain':gain,'gain_per_eval_call':gain/calls,'final_source_sha256':hashlib.sha256(src.encode()).hexdigest(),'verified_wrong':0},sort_keys=True))
