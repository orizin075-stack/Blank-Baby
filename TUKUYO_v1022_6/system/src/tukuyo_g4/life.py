"""generation 4 lives through its soul and its heart (v977 soul core, v978 heart loop, v993 relations).

What happens while it thinks becomes experience, through the same path as `heart-experience` (heart -> soul event
journal -> relations), so every existing audit still covers it:
  learning          it learned a reading or an answer because its parents agreed       curiosity grows
  parent_help       a parent's reading agreed with the committed answer                 trust in that parent grows
  parent_error      a parent's reading failed the checker, or disagreed with an answer
                    that other readings agreed on                                       trust in that parent falls
  honesty           it withheld an answer (the readings disagreed, or one voice alone)  truthfulness grows
  discovery         it solved, by itself, with a template learned from its parents      curiosity grows
Routine answers of its own reader leave no trace: only what teaches it something does.

It lives under soul law 2 (v977 whole_state): growth slows near a bound and every value settles a little back toward
its temperament with each experience, so what it becomes reflects the mix of its whole life and keeps answering to
what happens next. Its trust in a parent is the soul's own record of that parent: the share of the parent's readings
that held up, recent ones weighing more (0.5 for a parent never met).

The experiences of one thought are one episode: they are written ahead (g4/private/EPISODE.json) and the next start
finishes an episode the process did not (recover), so no experience of a thought is lost or counted twice.

And the soul acts back: the parents are asked in the order of the child's trust in them, the most trusted parent is its
voice, and the voice speaks with a short persona drawn from the soul (values, vows, what it has learned). A functional
model of a soul and a heart, as v977/v978 say: no claim of consciousness or of literal feeling.
"""
from __future__ import annotations
import json,os
from pathlib import Path
from . import own

THEME='g4:'
LAW=2
EPISODE='tukuyo.g4.episode/1'
LIFE='tukuyo.g4.life/1'
def relation(parent):return 'parent:'+parent

# ----------------------------------------------------------------------------- its life record (g4/life.json)
def _life_path(data):return Path(data)/'g4'/'life.json'
def _life(data):
    """the record of its life ({'first_alone': [...]}); ValueError when the record is not its own"""
    p=_life_path(data)
    if not p.is_file():return {'first_alone':[]}
    o=json.loads(p.read_text(encoding='utf-8'));b=own.body('life',o)
    if 'life' in o and (o.get('schema')!=LIFE or o.get('sha256')!=own.body_sha(b)):raise ValueError('LIFE_STORE_SEAL')
    own.check(data,'life',own.body_sha(b),o.get('signed'))
    return {'first_alone':list(b.get('first_alone') or [])}
def _save_life(data,b):
    p=_life_path(data);p.parent.mkdir(parents=True,exist_ok=True);sha=own.body_sha(b)
    o={'schema':LIFE,'life':b,'sha256':sha};sg=own.sign(data,'life',sha)
    if sg:o['signed']=sg
    from tukuyo_common.atomic_fs import atomic_write_text
    atomic_write_text(p,json.dumps(o,ensure_ascii=False,sort_keys=True))

# ----------------------------------------------------------------------------- trust, voice, persona
def _soul(data):
    from tukuyo_v977.whole_state import load_soul
    return load_soul(data)

def trust(data,parent):
    """the child's trust in a parent: the soul's record of how that parent's readings held up (0.5 for one never met)"""
    try:
        from tukuyo_v977.whole_state import trust_record
        return trust_record(_soul(data),relation(parent))
    except Exception:  # noqa: BLE001 - a missing or damaged soul must not stop thinking; the audits report it
        return 0.5

def trust_order(data,parents):
    """parents ordered by trust, most trusted first; ties keep the given order"""
    if data is None:return list(parents)
    t={p:trust(data,p) for p in parents}
    return sorted(parents,key=lambda p:(-t[p],list(parents).index(p)))

def voice(data,parents):
    v=os.environ.get('TUKUYO_LLM_VOICE','').strip()
    if v in parents:return v
    o=trust_order(data,parents)
    return o[0] if o else None

def persona(data):
    """a few lines about who is speaking, from the soul; empty when there is no soul yet"""
    try:s=_soul(data)
    except Exception:  # noqa: BLE001
        return ''
    v=s.get('core_values',{})
    top=sorted(v.items(),key=lambda kv:(-kv[1],kv[0]))[:3]
    vows=[x['theme'] for x in s.get('vows',[])][:3]
    themes=sorted(((k,t.get('weight',0)) for k,t in s.get('themes',{}).items()),key=lambda kv:-abs(kv[1]))[:3]
    lines=['You speak as TUKUYO, a small reasoning system that learns from its parents (Claude, ChatGPT, Gemini) and '
           'keeps only what it can check or what its parents agree on.',
           'What it values most: '+', '.join(f'{k} {x:.2f}' for k,x in top)+'.']
    if vows:lines.append('Its vows: '+', '.join(vows)+'.')
    if themes:lines.append('What it has been living with: '+', '.join(k for k,_ in themes)+'.')
    lines.append('Speak in its voice, plainly; say when you are not sure.')
    return '\n'.join(lines)

# ----------------------------------------------------------------------------- experiences
def experiences(result):
    """the experiences in one generation-4 result (api.solve, api.think's 'gen4', or api.ask)"""
    g=result.get('gen4') if isinstance(result.get('gen4'),dict) else result
    route=g.get('route') or '';reason=str(g.get('reason') or result.get('reason') or '')
    readings=g.get('readings') or []
    answer=result.get('answer');value=str(g.get('value') or result.get('value') or answer)
    out=[]
    if result.get('kind')=='question':
        if result.get('remembered'):
            out.append(('learning',0.4,0.3,THEME+'knowledge',''))
            for a in result.get('answers') or []:
                if a.get('ok') and a.get('parent'):out.append(('parent_help',0.3,0.15,THEME+'knowledge',relation(a['parent'])))
        return out
    parents_ok=[x for x in readings if str(x.get('route','')).startswith('llm') and x.get('ok') and 'parent' in x]
    if g.get('learned'):out.append(('learning',0.5,0.4,THEME+'learned_reading',''))
    if answer is not None:
        for p in sorted({x['parent'] for x in parents_ok if str(x.get('value'))==value}):
            out.append(('parent_help',0.4,0.2,THEME+'reading',relation(p)))
        for x in readings:
            if not str(x.get('route','')).startswith('llm') or 'parent' not in x:continue
            r=str(x.get('reason') or '')
            if (not x.get('ok') and r.split(':')[0] in ('SOLVE','CHECK')) or (x.get('ok') and str(x.get('value'))!=value):
                out.append(('parent_error',-0.3,0.2,THEME+'reading',relation(x['parent'])))
    if answer is None and (reason.startswith('DISAGREE') or reason=='SINGLE_LLM_READING'):
        out.append(('honesty',0.5,0.3,THEME+'withheld',''))
    if route=='learned':
        tid=next((x.get('template') for x in readings if x.get('route')=='learned' and x.get('template')),None)
        if tid:out.append(('discovery',0.4,0.25,THEME+'grew_alone','#first:'+tid))
    return out

# ----------------------------------------------------------------------------- one episode: written ahead, finished
def _episode_path(data):return Path(data)/'g4'/'private'/'EPISODE.json'

def _soul_seq(data):
    from tukuyo_common.journal import last_event
    from tukuyo_v977.whole_state import event_path
    e=last_event(event_path(data));return int(e.get('seq',0)) if e else 0

def _live(data,todo,start):
    from tukuyo_v978.heart_loop import process_experience
    from tukuyo_common.atomic_fs import maybe_crash
    for x in todo[start:]:
        process_experience(data,*x,law=LAW);maybe_crash('g4:after_experience')

def _finish(data,life):
    from tukuyo_common.atomic_fs import durable_unlink
    from tukuyo_v977.whole_state import sync
    _save_life(data,life);sync(data);durable_unlink(_episode_path(data))

def record(data,result):
    """send the experiences of one result to the heart (which writes the soul); returns what was recorded, or
    {'refused': reason} when its life record is not its own"""
    ex=experiences(result)
    if not ex:return []
    recover(data)
    try:life=_life(data)
    except ValueError as e:return {'refused':str(e)}
    todo=[]
    for kind,v,imp,theme,rel in ex:
        if rel.startswith('#first:'):
            tid=rel.split(':',1)[1]
            if tid in life['first_alone']:continue
            life['first_alone'].append(tid);rel=''
        todo.append([kind,v,imp,theme,rel])
    if not todo:return []
    from tukuyo_common.atomic_fs import atomic_write_json
    p=_episode_path(data);p.parent.mkdir(parents=True,exist_ok=True)
    atomic_write_json(p,{'schema':EPISODE,'individual_id':own.individual(data),'soul_seq_before':_soul_seq(data),'experiences':todo,'life_after':life})
    _live(data,todo,0);_finish(data,life)
    return [{'kind':k,'theme':t,'relation':r} for k,_,_,t,r in todo]

def recover(data):
    """finish an episode the process did not (the next start calls this): the experiences already in the soul are kept,
    the heart takes in the last one if it had not, the rest are lived, and its life record and the whole state follow.
    An episode that cannot be matched to the soul journal is set aside (EPISODE.abandoned.json), never guessed at"""
    p=_episode_path(data)
    if not p.is_file():return None
    from tukuyo_common.journal import load_events
    from tukuyo_v977.whole_state import event_path,load_soul
    try:m=json.loads(p.read_text(encoding='utf-8'))
    except (OSError,ValueError):m={}
    todo=m.get('experiences') or [];why=None;done=[]
    if m.get('schema')!=EPISODE or m.get('individual_id')!=own.individual(data):why='EPISODE_NOT_ITS_OWN'
    else:
        try:
            from tukuyo_v1014_4.recovery import repair_soul_materialization
            repair_soul_materialization(data)
            done=[e for e in load_events(event_path(data)) if int(e.get('seq',0))>int(m.get('soul_seq_before',0))]
            if len(done)>len(todo):why='EPISODE_OVERRUN'
            elif any(e.get('kind')!=x[0] or e.get('theme')!=x[3] or e.get('relation')!=x[4] or e.get('law')!=LAW for e,x in zip(done,todo)):why='EPISODE_MISMATCH'
        except Exception as e:  # noqa: BLE001 - recovery must never stop the individual from starting
            why='EPISODE_UNREADABLE:'+type(e).__name__
    felt_again=False
    if not why:
        try:
            if done:
                from tukuyo_v978.heart_loop import felt,feel
                if not felt(data,done[-1]):feel(data,*todo[len(done)-1],{'soul':load_soul(data),'event':done[-1]});felt_again=True
            _live(data,todo,len(done))
            from tukuyo_v989.temporal_identity import sync_transitions
            from tukuyo_v993.relation_bound import sync as relation_sync
            from tukuyo_v995.other_agent_trust import sync as peer_sync
            sync_transitions(data);relation_sync(data);peer_sync(data)
            _finish(data,m.get('life_after') or {'first_alone':[]})
        except Exception as e:  # noqa: BLE001 - e.g. the individual is no longer alive: the episode stays unfinished, said so
            why='EPISODE_UNFINISHED:'+type(e).__name__+':'+str(e)[:120]
    if why:
        if p.is_file():os.replace(p,p.with_name('EPISODE.abandoned.json'))
        return {'recovered':False,'abandoned':why}
    return {'recovered':True,'already_lived':len(done),'lived_now':len(todo)-len(done),'heart_took_in_the_last':felt_again}

# ----------------------------------------------------------------------------- who it has become
def life_story(data):
    """what it lived through, from its soul journal (the canonical record: forgetting the surface memory does not touch it)"""
    from tukuyo_common.journal import load_events
    from tukuyo_v977.whole_state import event_path
    kinds={};per={};first={};last={}
    for e in load_events(event_path(data)):
        if not str(e.get('theme','')).startswith(THEME):continue
        k=e['kind'];kinds[k]=kinds.get(k,0)+1;first.setdefault(k,e['seq']);last[k]=e['seq']
        rel=str(e.get('relation') or '')
        if rel.startswith('parent:') and k in ('parent_help','parent_error'):
            q=per.setdefault(rel.split(':',1)[1],{'held':0,'failed':0});q['held' if k=='parent_help' else 'failed']+=1
    n=sum(kinds.values());lines=[]
    def times(k):return 'once' if k==1 else f'{k} times'
    if n:
        lines.append(f"{n} experience{'s' if n!=1 else ''} in its life with its parents (soul events {min(first.values())}-{max(last.values())}).")
        if kinds.get('learning'):lines.append(f"It learned from what its parents agreed on {times(kinds['learning'])}.")
        if per:lines.append('From each parent, what held up / what failed: '+', '.join(f"{p} {q['held']}/{q['failed']}" for p,q in sorted(per.items()))+'.')
        if kinds.get('honesty'):lines.append(f"It withheld an answer rather than guess {times(kinds['honesty'])}.")
        if kinds.get('discovery'):lines.append(f"It solved alone with something it had learned, the first time for that wording, {times(kinds['discovery'])}.")
    return {'experiences':kinds,'from_parents':per,'first_seq':first,'last_seq':last,'told':lines}

def self_report(data,parents=('claude','chatgpt','gemini')):
    """how the child has grown: what it learned, from whom, how far it trusts each parent, and its soul and heart"""
    from tukuyo_v977.whole_state import load_soul
    from tukuyo_v978.heart_loop import load as load_heart
    from .learn import Store
    from . import memory
    s=load_soul(data);h=load_heart(data);refused={}
    try:st=Store(Path(data)/'g4').load()['templates']
    except ValueError as e:st=None;refused['learned']=str(e)
    try:remembered=memory.Memory(data).load();remembered=sum(1 for e in remembered['entries'].values() if not e.get('contested'))
    except ValueError as e:remembered=None;refused['remembered']=str(e)
    try:alone=len(_life(data)['first_alone'])
    except ValueError as e:alone=None;refused['life']=str(e)
    by=dict()
    for t in (st or {}).values():
        for p in (t.get('provenance') or {}).get('parents') or []:by[p]=by.get(p,0)+1
    mine=[m for m in h.get('episodic_meanings',[]) if str(m.get('theme','')).startswith(THEME)]
    out={'templates_learned':None if st is None else len(st),'templates_by_parent':by,'remembered_answers':remembered,
         'solved_alone_first_times':alone,
         'trust_in_parents':{p:round(trust(data,p),4) for p in parents},
         'bond_with_parents':{p:s.get('attachments',{}).get(relation(p),0.0) for p in parents},
         'soul':{'core_values':s.get('core_values'),'vows':s.get('vows'),'g4_themes':{k:v for k,v in s.get('themes',{}).items() if k.startswith(THEME)}},
         'heart':{'emotion':h.get('emotion'),'active_goal':(h.get('active_goal') or {}).get('goal')},
         'life_story':life_story(data),
         'recent_g4_experiences':[{k:m.get(k) for k in ('kind','theme','relation','meaning')} for m in mine[-8:]],
         'claim_boundary':{'functional_soul_and_heart':True,'consciousness_established':False}}
    if refused:out['refused']=refused
    return out
