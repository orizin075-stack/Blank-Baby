#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,shutil,stat,tempfile,zipfile
from pathlib import Path,PurePosixPath
from verify_release import verify

def verify_zip(path,key,limit=128*1024*1024):
    bad=[];seen=set();total=0
    try:
        with zipfile.ZipFile(path) as z:
            names=z.namelist();roots=set()
            for info in z.infolist():
                n=info.filename;p=PurePosixPath(n)
                if n in seen:bad.append('ZIP_DUPLICATE:'+n)
                seen.add(n)
                if p.is_absolute() or not p.parts or '..' in p.parts or '\\' in n or ':' in p.parts[0]:bad.append('ZIP_BAD_PATH:'+n);continue
                roots.add(p.parts[0])
                if stat.S_ISLNK(info.external_attr>>16):bad.append('ZIP_SYMLINK:'+n)
                total+=info.file_size
                if total>limit:bad.append('ZIP_EXPANSION_LIMIT')
            if len(roots)!=1:bad.append('ZIP_ROOT_COUNT:'+str(len(roots)))
            if bad:return {'ok':False,'bad':sorted(set(bad)),'zip_entries':len(names)}
            root=next(iter(roots))
            # every member must belong to the sole root; roots check plus path parser enforces this.
            with tempfile.TemporaryDirectory() as td:
                base=Path(td)
                for info in z.infolist():
                    p=PurePosixPath(info.filename);target=base.joinpath(*p.parts)
                    if info.is_dir():target.mkdir(parents=True,exist_ok=True)
                    else:
                        target.parent.mkdir(parents=True,exist_ok=True)
                        with z.open(info) as src,target.open('xb') as dst:shutil.copyfileobj(src,dst)
                r=verify(base/root,key);r['zip_entries']=len(names);r['zip_root']=root;return r
    except Exception as e:return {'ok':False,'bad':['ZIP_MALFORMED:'+type(e).__name__]}
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('archive');a.add_argument('--trusted-pubkey-file',required=True);x=a.parse_args();key=Path(x.trusted_pubkey_file).read_text().strip();r=verify_zip(x.archive,key);print(json.dumps(r,sort_keys=True));raise SystemExit(0 if r['ok'] else 1)
