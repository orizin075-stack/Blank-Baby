"""generation 4: an individual of a version from before stores were signed (2026-10-06 to 10-09) takes its stores back.

Its unsigned stores - what it learned (g4/learned.json), what its parents agreed on (g4/remembered.json) and the record of
its life (g4/life.json) - are refused, because its whole state never recorded them: a store put into an individual from
outside reads the same way (own.py, runtime_store.py). Every command stops on the learned store until it is moved away,
and with it what the individual learned. The owner, who knows where the stores came from, looks at what they hold
(g4-adopt-legacy) and signs them as the individual's own (g4-adopt-legacy --yes). Only these three kinds, only unsigned
and only when the whole state did not record that very file; a sealed body that does not match its seal is refused.
"""
from __future__ import annotations
import json
from pathlib import Path
from . import own

LEARNED='tukuyo.g4.learned/1';REMEMBERED='tukuyo.g4.remembered/1'

def _legacy(data,kind):
    """the body of an unsigned store of this kind that is refused now, or None (no store, signed, or read already)"""
    p=Path(data)/own.KINDS[kind]
    if not p.is_file():return None
    try:o=json.loads(p.read_text(encoding='utf-8'))
    except (OSError,ValueError):raise ValueError(kind.upper()+'_NOT_JSON') from None
    if not isinstance(o,dict) or o.get('signed') is not None:return None
    if kind=='learned':
        if (Path(data)/'g4'/'commits').exists():return None
        if o.get('schema')!=LEARNED or o.get('sha256')!=own.body_sha(o.get('templates',{})):raise ValueError('LEARNED_STORE_SEAL')
        body=o['templates']
    elif kind=='remembered':
        if o.get('schema')!=REMEMBERED or o.get('seal')!=own.body_sha(o.get('entries',{})):raise ValueError('REMEMBERED_STORE_SEAL')
        body=o['entries']
    else:
        b=own.body('life',o)
        if 'life' in o and o.get('sha256')!=own.body_sha(b):raise ValueError('LIFE_STORE_SEAL')
        if not isinstance(b.get('first_alone',[]),list):raise ValueError('LIFE_STORE_SEAL')
        body={'first_alone':list(b.get('first_alone') or [])}
    rec=own._recorded(data,kind)
    if rec is not own.NOT_RECORDED and rec==own._file_sha(p):return None        # recorded as it is: it is read already
    return body

def look(data):
    """what each unsigned store holds; nothing is changed"""
    out={}
    for kind in ('learned','remembered','life'):
        b=_legacy(data,kind)
        if b is None:continue
        if kind=='learned':out[kind]={'templates':len(b),'examples':[t.get('example') for t in list(b.values())[:5]]}
        elif kind=='remembered':out[kind]={'answers':len(b),'items':[{k:e.get(k) for k in ('question','answer','parents')} for e in list(b.values())[:10]]}
        else:out[kind]={'first_alone':len(b['first_alone'])}
    return out

def adopt(data):
    """sign the unsigned stores as this individual's own: the owner asked for it (g4-adopt-legacy --yes)"""
    if own.individual(data) is None:raise ValueError('NOT_A_LIVE_INDIVIDUAL')
    done={}
    b=_legacy(data,'remembered')
    if b is not None:
        from .memory import Memory
        Memory(data)._save({'schema':REMEMBERED,'entries':b});done['remembered']=len(b)
    b=_legacy(data,'life')
    if b is not None:
        from .life import _save_life
        _save_life(data,b);done['life']=len(b['first_alone'])
    b=_legacy(data,'learned')
    if b is not None:
        # the first signed commit of what it learned (runtime_store.py); the unsigned file is moved out of the way first,
        # as the commit's own checks would refuse it, and put back if the commit fails
        from . import runtime_store
        p=Path(data)/own.KINDS['learned'];keep=p.read_bytes();p.unlink()
        try:runtime_store.save(data,{'schema':LEARNED,'templates':b,'sha256':own.body_sha(b)})
        except BaseException:
            p.write_bytes(keep);raise
        done['learned']=len(b)
    return done
