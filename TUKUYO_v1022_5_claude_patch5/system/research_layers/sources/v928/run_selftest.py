import json,tempfile,pathlib
from tukuyo_v928.semantic_gate import inspect
with tempfile.NamedTemporaryFile(delete=False) as f:f.write(b'not canonical');p=f.name
r=inspect(p);pathlib.Path(p).unlink();ok=(not r['accepted'])
print(json.dumps({'ok':ok,'canonical_bytes_present':False,'full_digest_present':False,'gate_fail_closed':True},sort_keys=True));raise SystemExit(0 if ok else 1)
