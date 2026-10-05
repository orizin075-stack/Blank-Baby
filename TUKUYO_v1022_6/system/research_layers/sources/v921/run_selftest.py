import json
from tukuyo_v921.correctness import *
b=evaluate(BASE_SOURCE,91399,600);f=evaluate(FINAL_SOURCE,91399,600)
old_wrong_metric=0
ok=(b['verified_wrong']==600-b['correct'] and b['verified_wrong']>0 and old_wrong_metric==0 and f['verified_wrong']==0 and f['correct']==600)
print(json.dumps({'ok':ok,'baseline':b,'final':f,'old_metric_would_have_reported':old_wrong_metric,'bug_detected':b['verified_wrong']>old_wrong_metric},sort_keys=True));raise SystemExit(0 if ok else 1)
