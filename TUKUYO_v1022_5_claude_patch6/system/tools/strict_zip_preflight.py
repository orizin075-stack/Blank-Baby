#!/usr/bin/env python3
"""Exact one-root ZIP *structure* preflight. Supplement, NOT old epoch signer proof.
Both packaged ZIP and v930/v890 historical ZIP can be checked without extraction.
"""
import argparse,json,re,stat,zipfile
from pathlib import PurePosixPath

def verify(path,expected_root=None):
 bad=[];roots=set();seen=set();files=0
 try:
  with zipfile.ZipFile(path) as z:
   for ent in z.infolist():
    name=ent.filename
    if name in seen:bad.append('DUPLICATE:'+name)
    seen.add(name)
    if not name or '\\' in name or '\x00' in name or name.startswith('/') or ':' in name or '//' in name or any(p in ('','.','..') for p in name.split('/')[:-1]) or '..' in name.split('/') or (name.endswith('/') and ent.file_size):
     bad.append('BAD_PATH:'+name);continue
    bits=name.rstrip('/').split('/');roots.add(bits[0]);mode=(ent.external_attr>>16)
    if len(bits)<2 and not (ent.is_dir() and name==bits[0]+'/'):bad.append('ROOT_EXTERNAL_MEMBER:'+name)
    if (mode and stat.S_IFMT(mode) not in (0,stat.S_IFREG,stat.S_IFDIR)) or stat.S_ISLNK(mode):bad.append('SPECIAL_OR_SYMLINK:'+name)
    if name.endswith('/'):
     if ent.file_size!=0:bad.append('INVALID_DIRECTORY:'+name)
    else:
     if mode and stat.S_IFMT(mode)==stat.S_IFDIR:bad.append('DIRECTORY_AS_FILE:'+name)
     files+=1
   if len(roots)!=1:bad.append('NOT_ONE_ROOT:'+repr(sorted(roots)))
   if expected_root and roots!={expected_root}:bad.append('ROOT_MISMATCH')
   if z.testzip() is not None:bad.append('CRC_ERROR')
 except (OSError,zipfile.BadZipFile,ValueError) as exc:bad.append(type(exc).__name__)
 return {'ok':not bad,'bad':sorted(set(bad)),'files':files,'roots':sorted(roots)}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('zip');p.add_argument('--root');a=p.parse_args();r=verify(a.zip,a.root);print(json.dumps(r,sort_keys=True));raise SystemExit(0 if r['ok'] else 1)
