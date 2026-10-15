"""v1022.7.8: one individual, one history - a canon kept outside the data directory (the review round, 2026-10-13).

A copy of an individual's data directory has the same id and the same key. Before this module both copies could live
on, each passing every audit; a backup put back lived on as if nothing had happened; and a copy taken before the
individual died kept living (evidence_gen4/REVIEW_2026-10-13.md §3). Nothing inside a data directory can tell, as a copy
carries everything in it.

An owner who keeps a canon outside the data directory (TUKUYO_CANON: a directory, best on another disk or machine) has
each command that may change the individual end with one signed line in it (a chain: each line names the line before),
and the data directory keeps the line it wrote last (canon/private/CURSOR.json). The copy that holds the last line of the canon
is the individual; it may change. Any other copy is refused before it changes anything:

  BEHIND     its last line is an earlier line of the canon and it has not changed since: a copy left behind, or a
             backup put back (a restore)
  BRANCH     it changed after its last line without the canon: it lived on as a copy of its own. A command run with the
             canon leaves a mark in the data directory while it runs (canon/private/PENDING.json): a copy that stopped in the
             middle of a command is not a branch; one that changed with no canon and no mark is
  UNTRACKED  it never wrote a line of this canon (copied before the canon was kept, or its cursor was taken away)
  DEAD       the canon recorded the individual's death: no copy of it lives on

The owner decides which copy is the individual (identity-canon-adopt --yes): the canon records a restore or a chosen
branch, and every other copy is refused from then on. A dead individual is not taken back (a successor is a new
individual, v1018). Looking (status, audits) is never refused. When two copies run at once, the one that writes its line
second is told at once (CANON_BRANCH) and refused from then on.

The canon is as safe as the place it is kept: on the same disk it is put back with the disk, and whoever can write it
can take the turn. It does not prove which copy is the 'real' one in any deeper sense; it records which copy the owner's
commands kept living, and which the owner chose.
"""
from __future__ import annotations
import hashlib,json,os,time,uuid
from pathlib import Path

SCHEMA='tukuyo.v1022.canon/1';CURSOR_SCHEMA='tukuyo.v1022.canon_cursor/1';ENV='TUKUYO_CANON'
KINDS=('genesis','turn','death','restore','branch')
# commands that only look; everything else may change the individual
_LOOK={'status','system-status','verify-origins','eval','diagnose','recovery-status','recovery-audit','recovery-checkpoint','recovery-restore',
       'succession-pubkey-export','succession-export','evolution-export','archive-list','archive-show','init',
       'identity-canon-status','identity-canon-audit','identity-canon-adopt'}

def looks_only(cmd):return cmd in _LOOK or cmd.endswith(('-status','-audit','-gate-summary'))

def _identity(data):
    from tukuyo_v977.whole_state import _live_identity
    try:return _live_identity(data)['individual_id']
    except (ValueError,OSError,KeyError):return None

def canon_file(data):
    """the canon of the live individual in data, or None when none is kept (TUKUYO_CANON unset) or data is no live
    individual. ValueError when the canon would be inside the data directory (it would be put back with it)"""
    d=os.environ.get(ENV,'').strip()
    if not d:return None
    ident=_identity(data)
    if ident is None:return None
    d=Path(d).resolve();root=Path(data).resolve()
    if d==root or root in d.parents:raise ValueError('CANON_INSIDE_DATA')
    return d/(hashlib.sha256(ident.encode()).hexdigest()[:24]+'.canon.jsonl')

# in a 'private' directory: a recovery checkpoint does not hold them, and the restore frontier does not watch them (as the
# individual's keys, they stay with the data directory across a restore; the roadmap round found the frontier refusing an
# individual whose cursor had been written after a restore)
def cursor_path(data):return Path(data)/'canon'/'private'/'CURSOR.json'
def pending_path(data):return Path(data)/'canon'/'private'/'PENDING.json'
def _old_cursor_path(data):return Path(data)/'canon'/'CURSOR.json'      # v1022.7.8+gen4-r8

def _sha(o):
    from tukuyo_v977.whole_state import sha_obj
    return sha_obj(o)

def content(data):
    """what the individual is now: its whole state (without its own sequence) and the hashes of everything the whole
    state binds"""
    from tukuyo_v977.whole_state import _read,state_path,_component_hashes
    try:q=dict(_read(state_path(data))['payload'])
    except (OSError,ValueError,KeyError):q={}
    q.pop('seq',None);q.pop('previous_unified_state_sha256',None)
    return _sha({'whole':q,'components':_component_hashes(data)})

def _lines(f,verify_with=None,ident=None):
    """the lines of the canon, each (envelope, its hash); ValueError CANON_NOT_ITS_OWN when one is not signed by this
    individual's key, CANON_CHAIN when the chain is broken. verify_with: the public key ('last' checks the last line only)"""
    if not f.is_file():return []
    out=[];prev='0'*64
    raw=[x for x in f.read_text(encoding='utf-8').splitlines() if x.strip()]
    from tukuyo_v977.whole_state import _verify
    for i,x in enumerate(raw,1):
        try:env=json.loads(x);q=env['payload']
        except (ValueError,KeyError,TypeError):raise ValueError('CANON_MALFORMED') from None
        h=_sha(env)
        full=verify_with is not None and (verify_with[1]=='all' or i==len(raw))
        if full:
            if not _verify(env,verify_with[0]) or q.get('schema')!=SCHEMA or q.get('individual_id')!=ident:raise ValueError('CANON_NOT_ITS_OWN')
        if verify_with is not None and verify_with[1]=='all' and (q.get('n')!=i or q.get('previous_line_sha256')!=prev or q.get('kind') not in KINDS):
            raise ValueError('CANON_CHAIN')
        out.append((env,h));prev=h
    return out

def _pub(data):
    from tukuyo_v977.whole_state import _key_paths
    return _key_paths(data)[1].read_text().strip()

def cursor(data):
    p=cursor_path(data)
    if not p.is_file():p=_old_cursor_path(data)
    if not p.is_file():return None
    try:c=json.loads(p.read_text(encoding='utf-8'))
    except (OSError,ValueError):return None
    return c if isinstance(c,dict) and c.get('schema')==CURSOR_SCHEMA else None

def _dead(data):
    p=Path(data)/'v1007'/'ORGANISM2_STATE.json'
    if not p.is_file():return False
    try:s=json.loads(p.read_text(encoding='utf-8'))
    except (OSError,ValueError):return False
    return bool(s.get('death_irreversible') or s.get('lifecycle')=='DEAD')

def status(data,verify='last'):
    """{'kept': False} when no canon is kept; else the state of this copy: IN_SYNC (it holds the last line), NEW (no line
    yet), BEHIND, BRANCH, UNTRACKED, DEAD (a copy of an individual that died), DEAD_SELF (the individual that died)"""
    f=canon_file(data)
    if f is None:return {'kept':False}
    ident=_identity(data);ls=_lines(f,(_pub(data),verify),ident);c=cursor(data);now=content(data)
    out={'kept':True,'canon_file':str(f),'lines':len(ls),'cursor':c and {k:c.get(k) for k in ('n','line_sha256')}}
    if not ls:return {**out,'state':'NEW'}
    head,hh=ls[-1];out['head']={'n':head['payload']['n'],'kind':head['payload']['kind'],'utc':head['payload'].get('utc'),'line_sha256':hh}
    mine=c is not None and c.get('individual_id')==ident and c.get('line_sha256')==hh
    if any(e['payload']['kind']=='death' for e,_ in ls):return {**out,'state':'DEAD_SELF' if mine else 'DEAD'}
    # an earlier line whose individual is what this copy is now: a copy left behind there, or put back to it (a restore)
    def earlier(upto):
        for e,_ in reversed(ls[:upto]):
            if e['payload'].get('content_sha256')==now:return e
        return None
    if mine:
        changed=now!=head['payload'].get('content_sha256');pend=_pending_mark(data)
        if changed and not (pend and pend.get('head_line_sha256')==hh):
            back=earlier(len(ls)-1)
            if back is not None:
                return {**out,'state':'BEHIND','why':'it is what the individual was at an earlier line (put back)','its_last_line':back['payload']['n'],
                        'lines_after_it':head['payload']['n']-back['payload']['n']}
            return {**out,'state':'BRANCH','why':'it changed after its last line, with no command of the canon running'}
        return {**out,'state':'IN_SYNC','changed_since_last_line':changed}
    if c is None or c.get('individual_id')!=ident:return {**out,'state':'UNTRACKED'}
    k=next((i for i,(e,h) in enumerate(ls) if h==c.get('line_sha256')),None)
    if k is None:return {**out,'state':'UNTRACKED','why':'its last line is not in this canon'}
    at=ls[k][0];back=at if now==at['payload'].get('content_sha256') else earlier(k)
    if back is None:return {**out,'state':'BRANCH','its_last_line':at['payload']['n'],'lines_after_it':head['payload']['n']-at['payload']['n']}
    return {**out,'state':'BEHIND','its_last_line':back['payload']['n'],'lines_after_it':head['payload']['n']-back['payload']['n']}

def _pending_mark(data):
    try:c=json.loads(pending_path(data).read_text(encoding='utf-8'))
    except (OSError,ValueError):return None
    return c if isinstance(c,dict) else None

def guard(data,cmd):
    """before a command: a copy that is not the individual (or of one that died) may only look. The individual leaves a
    mark that a command of the canon is running (removed when its line is written)"""
    if canon_file(data) is None:return
    s=status(data)
    if s['state'] in ('IN_SYNC','NEW'):
        from tukuyo_common.atomic_fs import atomic_write_bytes
        from tukuyo_v977.whole_state import canon as _canon
        atomic_write_bytes(pending_path(data),_canon({'cmd':cmd,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                                                      'head_line_sha256':(s.get('head') or {}).get('line_sha256')})+b'\n')
        return
    if looks_only(cmd):return
    raise ValueError('CANON_'+s['state'])

def _clear(data):
    try:pending_path(data).unlink()
    except FileNotFoundError:pass

class _Lock:
    def __init__(s,f):s.p=Path(str(f)+'.lock')
    def __enter__(s):
        s.p.parent.mkdir(parents=True,exist_ok=True);s.h=s.p.open('a+b')
        if os.name=='nt':
            import msvcrt;s.h.seek(0);msvcrt.locking(s.h.fileno(),msvcrt.LK_LOCK,1)
        else:
            import fcntl;fcntl.flock(s.h,fcntl.LOCK_EX)
        return s
    def __exit__(s,*a):
        try:
            if os.name=='nt':
                import msvcrt;s.h.seek(0);msvcrt.locking(s.h.fileno(),msvcrt.LK_UNLCK,1)
            else:
                import fcntl;fcntl.flock(s.h,fcntl.LOCK_UN)
        finally:s.h.close()

def _append(data,f,ls,kind,**extra):
    from tukuyo_v977.whole_state import _sign,_read,state_path,canon as _canon
    from tukuyo_common.atomic_fs import atomic_write_bytes
    ident=_identity(data);prev=ls[-1][1] if ls else '0'*64;n=len(ls)+1
    try:st=_read(state_path(data));seq=st['payload'].get('seq');ssha=_sha(st)
    except (OSError,ValueError,KeyError):seq=ssha=None
    q={'schema':SCHEMA,'individual_id':ident,'n':n,'kind':kind,'content_sha256':content(data),'state_seq':seq,'state_sha256':ssha,
       'previous_line_sha256':prev,'nonce':uuid.uuid4().hex,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**extra}
    env=_sign(data,q);b=json.dumps(env,ensure_ascii=False,sort_keys=True)
    with f.open('a',encoding='utf-8') as h:
        h.write(b+'\n');h.flush();os.fsync(h.fileno())
    h2=_sha(env)
    atomic_write_bytes(cursor_path(data),_canon({'schema':CURSOR_SCHEMA,'individual_id':ident,'n':n,'line_sha256':h2})+b'\n')
    try:_old_cursor_path(data).unlink()
    except FileNotFoundError:pass
    return {'n':n,'kind':kind,'line_sha256':h2}

def note(data,cmd):
    """after a command: its line when it may have changed the individual (the first is 'genesis'; 'death' once it died;
    a command that only looks writes one only if the individual changed while it ran). ValueError CANON_<STATE> when
    another copy wrote a line since this one started (both ran at once)"""
    f=canon_file(data)
    if f is None:return None
    f.parent.mkdir(parents=True,exist_ok=True)
    with _Lock(f):
        ident=_identity(data);ls=_lines(f,(_pub(data),'last'),ident);c=cursor(data)
        if ls and any(e['payload']['kind']=='death' for e,_ in ls):_clear(data);return None
        mine=not ls or (c is not None and c.get('individual_id')==ident and c.get('line_sha256')==ls[-1][1])
        if mine and ls and content(data)!=ls[-1][0]['payload'].get('content_sha256'):
            pend=_pending_mark(data);mine=bool(pend and pend.get('head_line_sha256')==ls[-1][1])   # changed with no command of the canon: a branch
        if not mine:
            if looks_only(cmd):return None
            raise ValueError('CANON_'+status(data)['state'])
        if looks_only(cmd) and (not ls or content(data)==ls[-1][0]['payload'].get('content_sha256')):_clear(data);return None
        kind='genesis' if not ls else ('death' if _dead(data) else 'turn')
        r=_append(data,f,ls,kind,command=cmd);_clear(data);return r

def adopt(data,yes=False):
    """the owner says this copy is the individual (a backup put back, or one of two copies that both lived on): the canon
    records a restore or a chosen branch, and every other copy is refused from then on"""
    f=canon_file(data)
    if f is None:raise ValueError('CANON_NOT_KEPT')
    s=status(data)
    if s['state'] in ('IN_SYNC','NEW'):return {'ok':True,'adopted':None,'state':s['state'],'note':'this copy already holds the last line'}
    if s['state'] in ('DEAD','DEAD_SELF'):raise ValueError('CANON_DEAD_NOT_ADOPTED')
    kind='restore' if s['state']=='BEHIND' else 'branch'
    if not yes:return {'ok':True,'adopted':None,'would_record':kind,'state':s,'note':'with --yes this copy becomes the individual; every other copy is refused from then on'}
    with _Lock(f):
        ident=_identity(data);ls=_lines(f,(_pub(data),'last'),ident)
        r=_append(data,f,ls,kind,from_line=s.get('its_last_line'),was=s['state']);_clear(data)
    # the generation-4 witness, when one is kept, follows the owner's choice (a restored copy's stores are older)
    from tukuyo_g4.own import witness_reset
    w=witness_reset(data)
    return {'ok':True,'adopted':r,'was':s['state'],**({'g4_witness_reset':w} if w is not None else {})}

def outside_errors(data):
    """what the records kept outside the data directory say about this copy (for the whole-audit command): a copy that is
    not the individual (CANON_BEHIND, CANON_BRANCH, CANON_UNTRACKED, CANON_DEAD), and generation-4 stores older than the
    witness (G4_WITNESS_AHEAD). [] when none is kept"""
    errs=[]
    try:
        cs=status(data)
        if cs.get('kept') and cs['state'] not in ('IN_SYNC','NEW','DEAD_SELF'):errs.append('CANON_'+cs['state'])
    except ValueError as e:errs.append('CANON:'+str(e))
    if (Path(data)/'g4').exists():
        try:
            from tukuyo_g4.own import behind_witness
            errs.extend('G4_WITNESS_AHEAD:g4_'+k for k in behind_witness(data))
        except ValueError as e:errs.append('G4_WITNESS:'+str(e))
    return errs

def audit(data):
    """the whole chain: every line signed by this individual, numbered, each naming the one before; and this copy's place"""
    f=canon_file(data)
    if f is None:return {'ok':True,'kept':False}
    try:
        ls=_lines(f,(_pub(data),'all'),_identity(data));s=status(data)
    except ValueError as e:return {'ok':False,'kept':True,'errors':[str(e)]}
    kinds={}
    for e,_ in ls:kinds[e['payload']['kind']]=kinds.get(e['payload']['kind'],0)+1
    bad=s['state'] not in ('IN_SYNC','NEW','DEAD_SELF')
    return {'ok':not bad,'kept':True,'state':s['state'],'lines':len(ls),'kinds':kinds,'errors':['CANON_'+s['state']] if bad else [],'status':s}
