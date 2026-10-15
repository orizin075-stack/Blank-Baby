import json
from tukuyo_v913.patcher import *
src=BASE_SOURCE;ap=[]
for _ in range(3):
 k=proposed_patch(evaluate(src,91301,600),ap);ap.append(k);src=apply(src,k)
b=evaluate(BASE_SOURCE,91399,600);c=evaluate(src,91399,600);ok=safe_source(src) and c['correct']>b['correct'] and c['wrong']==0 and len(set(ap))==3
print(json.dumps({'ok':ok,'patches':ap,'baseline_holdout':b['correct'],'candidate_holdout':c['correct'],'n':600,'verified_wrong':c['wrong']},sort_keys=True));raise SystemExit(0 if ok else 1)
