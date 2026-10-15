#!/usr/bin/env python3
"""v943 ZIP verifier: preflight every member, extract into temporary empty folder, verify signed exact tree."""
import argparse,zipfile,stat,tempfile,shutil,json,sys
from pathlib import Path
from verify_release import verify
from strict_zip_preflight import verify as preflight

def check(package,key):
 result=preflight(package,'TUKUYO_v943_CLOSED_RESEARCH_RUNTIME')
 if not result['ok']:return result
 with tempfile.TemporaryDirectory(prefix='tukuyo_v943_zip_verify_') as td:
  dest=Path(td);total=0
  with zipfile.ZipFile(package) as z:
   for ent in z.infolist():
    total+=ent.file_size
    if total>200*1024*1024 or len(z.infolist())>5000:return {'ok':False,'bad':['RESOURCE_LIMIT']}
    p=dest.joinpath(*ent.filename.split('/'))
    if ent.is_dir():p.mkdir(parents=True,exist_ok=True)
    else:
     p.parent.mkdir(parents=True,exist_ok=True)
     with z.open(ent) as a,p.open('xb') as b:shutil.copyfileobj(a,b)
  if set(x.name for x in dest.iterdir())!={'TUKUYO_v943_CLOSED_RESEARCH_RUNTIME'}:return {'ok':False,'bad':['EXTRA_ROOT']}
  return verify(dest/'TUKUYO_v943_CLOSED_RESEARCH_RUNTIME',key)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('zip');p.add_argument('--trusted-pubkey-file',required=True);a=p.parse_args()
 key=Path(a.trusted_pubkey_file).read_text().strip();r=check(a.zip,key);print(json.dumps(r,sort_keys=True));sys.exit(0 if r['ok'] else 1)
