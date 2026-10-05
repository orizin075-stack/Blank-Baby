from contextlib import contextmanager
from tukuyo_v955.bootstrap import mounted as old_mounted,verify_origins
@contextmanager
def mounted():
    with old_mounted() as api:yield api
