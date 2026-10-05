import json
from tukuyo_v917.gate import decide,RELEASE_FP
# malformed receipt must fail closed
r=decide({'payload':{},'signature_b64':''},'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=','a'*64);ok=(not r['promote']);print(json.dumps({'ok':ok,'promotion_without_external_receipt':False},sort_keys=True));raise SystemExit(0 if ok else 1)
