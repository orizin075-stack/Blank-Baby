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

And the soul acts back: the parents are asked in the order of the child's trust in them (the v993 relation model of
'parent:<name>'), the most trusted parent is its voice, and the voice speaks with a short persona drawn from the soul
(values, vows, what it has learned). A functional model of a soul and a heart, as v977/v978 say: no claim of
consciousness or of literal feeling.
"""
from __future__ import annotations
import json,os
from pathlib import Path

THEME='g4:'
def relation(parent):return 'parent:'+parent

def _life_path(data):return Path(data)/'g4'/'life.json'
def _life(data):
    p=_life_path(data)
    try:return json.loads(p.read_text(encoding='utf-8'))
    except (OSError,ValueError):return {'first_alone':[]}
def _save_life(data,o):
    p=_life_path(data);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,sort_keys=True),encoding='utf-8')

def trust(data,parent):
    """the child's trust in a parent: the v993 relation model of parent:<name> (0.5 for a parent never met)"""
    try:
        from tukuyo_v993.relation_bound import model
        return float(model(data,relation(parent)).get('trust',0.5))
    except Exception:  # noqa: BLE001 - a missing or damaged relation cache must not stop thinking; the audits report it
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
    try:
        from tukuyo_v977.whole_state import load_soul
        s=load_soul(data)
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

def record(data,result):
    """send the experiences of one result to the heart (which writes the soul); returns what was recorded"""
    ex=experiences(result);done=[]
    if not ex:return done
    from tukuyo_v978.heart_loop import process_experience
    life=_life(data)
    for kind,v,imp,theme,rel in ex:
        if rel.startswith('#first:'):
            tid=rel.split(':',1)[1]
            if tid in life['first_alone']:continue
            life['first_alone'].append(tid);rel=''
        process_experience(data,kind,v,imp,theme,rel);done.append({'kind':kind,'theme':theme,'relation':rel})
    _save_life(data,life)
    from tukuyo_v977.whole_state import sync
    sync(data)
    return done

def self_report(data,parents=('claude','chatgpt','gemini')):
    """how the child has grown: what it learned, from whom, how far it trusts each parent, and its soul and heart"""
    from tukuyo_v977.whole_state import load_soul
    from tukuyo_v978.heart_loop import load as load_heart
    from .learn import Store
    from . import memory
    s=load_soul(data);h=load_heart(data);st=Store(Path(data)/'g4').load()['templates']
    by=dict()
    for t in st.values():
        for p in (t.get('provenance') or {}).get('parents') or []:by[p]=by.get(p,0)+1
    mine=[m for m in h.get('episodic_meanings',[]) if str(m.get('theme','')).startswith(THEME)]
    return {'templates_learned':len(st),'templates_by_parent':by,'remembered_answers':memory.count(data),
            'solved_alone_first_times':len(_life(data)['first_alone']),
            'trust_in_parents':{p:round(trust(data,p),4) for p in parents},
            'soul':{'core_values':s.get('core_values'),'vows':s.get('vows'),'g4_themes':{k:v for k,v in s.get('themes',{}).items() if k.startswith(THEME)}},
            'heart':{'emotion':h.get('emotion'),'active_goal':(h.get('active_goal') or {}).get('goal')},
            'recent_g4_experiences':[{k:m.get(k) for k in ('kind','theme','relation','meaning')} for m in mine[-8:]],
            'claim_boundary':{'functional_soul_and_heart':True,'consciousness_established':False}}
