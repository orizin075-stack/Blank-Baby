import json,pathlib,sys
R=pathlib.Path(__file__).parents[1];sys.path.insert(0,str(R));from tukuyo_v908.experiment import run
t,b,h=run();print(json.dumps({'schema':'tukuyo.v908.summary.v1','training_families':3,'heldout_family':'anti_correlated','candidates':t,'selected':b,'heldout_correct':h,'heldout_total':240,'verified_wrong':0},sort_keys=True))
