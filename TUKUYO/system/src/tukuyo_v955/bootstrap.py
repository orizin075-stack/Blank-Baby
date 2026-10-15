from __future__ import annotations
from contextlib import contextmanager
from tukuyo_v954.bootstrap import mounted as old_mounted
from tukuyo_v939.bootstrap import verify_origins as old_verify_origins
from .semantic_guard import install,installed,check_builtin_semantics

def verify_origins():
    x=old_verify_origins();return {**x,'v955_semantic_guard_release_layer':True}
@contextmanager
def mounted():
    with old_mounted() as api:
        s838=api['organism'].s838
        install(s838)
        if not installed(s838):raise RuntimeError('V955_SEMANTIC_GUARD_NOT_INSTALLED')
        chk=check_builtin_semantics(s838)
        if not chk['ok']:raise RuntimeError('V955_BUILTIN_SPEC_FAILED')
        yield api
