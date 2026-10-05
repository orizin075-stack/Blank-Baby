import json,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tukuyo_v916.multigen import run
from tukuyo_v916.patcher import evaluate,BASE_SOURCE,source_sha
r,s=run();final=evaluate(s,91999,1200);base=evaluate(BASE_SOURCE,91999,1200);print(json.dumps({'generations':r,'final_sha256':source_sha(s),'final_fresh_correct':final['correct'],'base_fresh_correct':base['correct'],'fresh_n':1200,'verified_wrong':final['wrong']},sort_keys=True))
