"""v941 flat runtime mount: no ancestor ZIP extraction. Integrity checked at boot.
Historical ZIPs are preserved separately and never confused with source authority.
"""
from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
import sys,hashlib,json,importlib,zipfile,stat,shutil
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'src'
LEGACY=SRC/'legacy'
RESEARCH=SRC/'research'
V935=ROOT/'history/TUKUYO_v931_to_v935_VERIFIED_DEBUGGED_CHAIN.zip'
V935_SHA='fbc07133b6fb6061deec2e8faada83cded55951e06e9750feba796869f0fb930'
class OriginError(RuntimeError):pass
def hash_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
    return h.hexdigest()
def verify_origins():
    p=ROOT/'META/PROVENANCE_SOURCE.json'
    manifest=json.loads(p.read_text(encoding='utf-8'))
    checks=manifest['installed_source_sha256']
    for relative,expected in checks.items():
        f=ROOT/relative
        if not f.is_file() or f.is_symlink() or hash_file(f)!=expected:
            raise OriginError('FLAT_SOURCE_TAMPER:'+relative)
    expected=set(checks)|{'src/tukuyo_v938/bootstrap.py','src/tukuyo_v939/bootstrap.py'}
    actual=set()
    for p in (SRC/'legacy').rglob('*'):
        if p.is_file() or p.is_symlink():actual.add(p.relative_to(ROOT).as_posix())
    for p in RESEARCH.rglob('*'):
        if p.is_file() or p.is_symlink():actual.add(p.relative_to(ROOT).as_posix())
    for p in (SRC/'tukuyo_v938').rglob('*'):
        if p.is_file() or p.is_symlink():actual.add(p.relative_to(ROOT).as_posix())
    for p in (SRC/'tukuyo_v939').rglob('*'):
        if p.is_file() or p.is_symlink():actual.add(p.relative_to(ROOT).as_posix())
    actual.add('examples/SEMANTIC_TEACH_SAMPLE.json')
    if actual!=expected:raise OriginError('FLAT_SOURCE_FILE_SET:extra='+str(sorted(actual-expected))+':missing='+str(sorted(expected-actual)))
    if hash_file(V935)!=manifest['v935_chain_sha256']:
        raise OriginError('V935_REPLAY_CHAIN_TAMPER')
    return {'flat_sources':len(checks),'verified_history_chain':'v931-v935','source_integrity':True}
def safe_extract(src,dest,limit):
    dest=Path(dest);dest.mkdir(parents=True,exist_ok=False);total=0;seen=set()
    with zipfile.ZipFile(src) as z:
        for info in z.infolist():
            p=Path(info.filename)
            if p.is_absolute() or '..' in p.parts or not p.parts or '\\' in info.filename or ':' in p.parts[0] or info.filename in seen:
                raise OriginError('ZIP_PATH_OR_DUPLICATE')
            seen.add(info.filename)
            if stat.S_ISLNK(info.external_attr >> 16):raise OriginError('ZIP_SYMLINK')
            total+=info.file_size
            if total>limit:raise OriginError('ZIP_EXPANSION_LIMIT')
            target=dest.joinpath(*p.parts)
            if info.is_dir():target.mkdir(parents=True,exist_ok=True)
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                with z.open(info) as inp,target.open('xb') as out:shutil.copyfileobj(inp,out)
    return total
@contextmanager
def mounted():
    verify_origins()
    sys.path.insert(0,str(LEGACY))
    sys.path.insert(0,str(RESEARCH))
    sys.path.insert(0,str(SRC))
    try:
        from tukuyo_v841 import social
        from tukuyo_v840 import integration as organism
        from tukuyo_v846_1 import runtime_guard as guard
        from tukuyo_v842 import society
        from tukuyo_v843 import cluster
        from tukuyo_v844 import lineage
        from tukuyo_v845 import ecology
        from tukuyo_v846 import evolution
        from tukuyo_research_v936 import learner
        import importlib.util
        spec=importlib.util.spec_from_file_location('tukuyo_flat_v937_reproduce',RESEARCH/'tools/reproduce.py')
        research=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(research)
        from tukuyo_v938 import bridge
        if guard.r837 is not organism.r837:raise OriginError('RUNTIME_GUARD_DISCONNECTED')
        if not guard._INSTALLED:raise OriginError('RUNTIME_GUARD_NOT_INSTALLED')
        yield {'social':social,'organism':organism,'guard':guard,'society':society,
               'cluster':cluster,'lineage':lineage,'ecology':ecology,'evolution':evolution,
               'learner':learner,'research':research,'bridge':bridge,
               'v938_root':ROOT,'research_root':RESEARCH,'v846_root':LEGACY}
    finally:
        for val in (str(SRC),str(RESEARCH),str(LEGACY)):
            try:sys.path.remove(val)
            except ValueError:pass
