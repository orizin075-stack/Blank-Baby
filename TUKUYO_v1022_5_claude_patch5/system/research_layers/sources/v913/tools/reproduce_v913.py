import json,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tukuyo_v913.patcher import *
b=BASE_SOURCE;s=evaluate(b,91301,600);ap=[];src=b
for _ in range(3):
 k=proposed_patch(evaluate(src,91301,600),ap);ap.append(k);src=apply(src,k)
out={'patches':ap,'baseline':s,'candidate_train':evaluate(src,91301,600),'candidate_holdout':evaluate(src,91399,600),'baseline_sha256':source_sha(b),'candidate_sha256':source_sha(src),'safe_source':safe_source(src)}
print(json.dumps(out,sort_keys=True))
