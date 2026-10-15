"""v963 third-party reproduction contract/runner.
This module can produce and verify a fresh-process reproduction receipt, but it does not claim an actually independent third party ran it.
"""
from __future__ import annotations
import hashlib,json,subprocess,sys,tempfile
from pathlib import Path

def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()

def contract(runtime_zip_sha256):
    return {'schema':'tukuyo.v963.reproduction_contract/1','runtime_zip_sha256':runtime_zip_sha256,'required_checks':['release_verify','v959_v961_tests','v962_inheritance_tests'],'fresh_process_required':True,'third_party_reproduction_status':'PENDING'}

def run_fresh(root,trust_anchor):
    root=Path(root);env={'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(root/'src')}
    checks=[]
    cmds=[
      [sys.executable,'-B',str(root/'tools/verify_release.py'),str(root),'--trusted-pubkey-file',str(trust_anchor)],
      [sys.executable,'-B','-m','unittest','-v',str(root/'tests/test_v959_v961_route.py')],
      [sys.executable,'-B','-m','unittest','-v',str(root/'tests/test_v962_inheritance.py')],
    ]
    for c in cmds:
        r=subprocess.run(c,cwd=root,env={**__import__('os').environ,**env},capture_output=True,text=True,timeout=90)
        checks.append({'argv':c[1:],'returncode':r.returncode,'stdout_sha256':sha_bytes(r.stdout.encode()),'stderr_sha256':sha_bytes(r.stderr.encode())})
        if r.returncode!=0:return {'schema':'tukuyo.v963.reproduction_result/1','ok':False,'checks':checks,'independent_third_party':False}
    return {'schema':'tukuyo.v963.reproduction_result/1','ok':True,'checks':checks,'fresh_processes':True,'independent_third_party':False,'third_party_reproduction_status':'INTERNAL_ANALOG_PASS_EXTERNAL_PENDING'}
