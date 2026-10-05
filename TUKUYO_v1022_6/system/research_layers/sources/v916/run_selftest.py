import json
from tukuyo_v916.multigen import run
from tukuyo_v916.patcher import evaluate,BASE_SOURCE
r,s=run();f=evaluate(s,91999,1200);b=evaluate(BASE_SOURCE,91999,1200);ok=len(r)==3 and all(x['accepted'] for x in r) and len({x['promoted_sha256'] for x in r})==3 and f['correct']>b['correct'] and f['wrong']==0;print(json.dumps({'ok':ok,'promotions':sum(x['accepted'] for x in r),'final_fresh_correct':f['correct'],'base_fresh_correct':b['correct'],'fresh_n':1200,'verified_wrong':f['wrong']},sort_keys=True));raise SystemExit(0 if ok else 1)
