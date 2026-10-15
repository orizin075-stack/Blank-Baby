import json,tempfile,pathlib
from tukuyo_v911.admit import admit,TRACKS
with tempfile.TemporaryDirectory() as d:
 p=pathlib.Path(d)/'fake.json';p.write_text('[]')
 a=admit(p,'H3_DEDUP');b=admit(p,'UNKNOWN')
 ok=(not a['ok'] and a['reason']=='SHA_MISMATCH' and not b['ok'] and b['reason']=='UNKNOWN_TRACK' and len(TRACKS)==2)
 print(json.dumps({'ok':ok,'tests':3,'canonical_assets_embedded':False},sort_keys=True));raise SystemExit(0 if ok else 1)
