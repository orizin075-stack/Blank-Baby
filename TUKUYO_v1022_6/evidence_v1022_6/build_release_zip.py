#!/usr/bin/env python3
"""Build the TUKUYO v1022.6 release zip deterministically, then check it.

  build_release_zip.py PACKAGE_DIR OUT.zip --trusted-pubkey-file ANCHOR

The zip has one root folder (the package folder's name), entries in sorted order, a fixed timestamp and fixed
modes, and no caches, so the same tree gives the same zip on the same zlib. After writing it:
  * system/tools/strict_zip_preflight.py: one root, no unsafe paths, no links or special files, CRC ok
  * the system/ folder inside the zip verifies with system/tools/verify_release.py against ANCHOR
(system/tools/verify_release_zip.py expects the signed tree itself at the zip root, so it is not used here.)
"""
from __future__ import annotations
import argparse,hashlib,json,os,stat,sys,tempfile,zipfile
from pathlib import Path

STAMP=(2026,10,6,0,0,0)
SKIP_DIRS={'__pycache__','.pytest_cache','.git'}

def entries(pkg:Path):
    out=[]
    for dirpath,dirnames,filenames in os.walk(pkg):
        dirnames[:]=sorted(d for d in dirnames if d not in SKIP_DIRS)
        rel=Path(dirpath).relative_to(pkg.parent).as_posix()
        out.append((rel+'/',None))
        for f in sorted(filenames):
            p=Path(dirpath)/f
            if f.endswith(('.pyc','.pyo')):continue
            if p.is_symlink() or not p.is_file():raise SystemExit('refusing to pack a link or special file: '+str(p))
            out.append((rel+'/'+f,p))
    return sorted(out)

def build(pkg:Path,out:Path):
    with zipfile.ZipFile(out,'w') as z:
        for name,p in entries(pkg):
            zi=zipfile.ZipInfo(name,STAMP);zi.create_system=3
            if p is None:
                zi.external_attr=(stat.S_IFDIR|0o755)<<16;zi.compress_type=zipfile.ZIP_STORED;z.writestr(zi,b'')
            else:
                zi.external_attr=(stat.S_IFREG|0o644)<<16;zi.compress_type=zipfile.ZIP_DEFLATED
                z.writestr(zi,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)

def check(out:Path,root:str,anchor:Path,tools:Path):
    sys.path.insert(0,str(tools))
    from strict_zip_preflight import verify as preflight
    from verify_release import verify
    pre=preflight(str(out),root)
    rel={'ok':False,'bad':['NOT_CHECKED']}
    if pre['ok']:
        with tempfile.TemporaryDirectory(prefix='tukuyo_zip_check_') as td:
            with zipfile.ZipFile(out) as z:z.extractall(td)          # paths were checked by the preflight
            rel=verify(Path(td)/root/'system',anchor.read_text().strip())
    return pre,rel

def main():
    ap=argparse.ArgumentParser();ap.add_argument('package',type=Path);ap.add_argument('out',type=Path);ap.add_argument('--trusted-pubkey-file',type=Path,required=True)
    a=ap.parse_args();pkg=a.package.resolve()
    if not (pkg/'system/META/RELEASE_MANIFEST.json').is_file():raise SystemExit('not a package folder: '+str(pkg))
    build(pkg,a.out)
    pre,rel=check(a.out,pkg.name,a.trusted_pubkey_file,pkg/'system/tools')
    with zipfile.ZipFile(a.out) as z:n=len(z.infolist())
    res={'ok':pre['ok'] and rel['ok'],'zip':str(a.out),'sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'bytes':a.out.stat().st_size,
         'entries':n,'root':pkg.name,'preflight':pre,'release_verify':{k:rel.get(k) for k in ('ok','bad','verified_files')}}
    print(json.dumps(res,ensure_ascii=False,indent=1))
    raise SystemExit(0 if res['ok'] else 1)

if __name__=='__main__':main()
