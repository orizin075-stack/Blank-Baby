"""generation 4: one entry point. Readings come from learned templates, TUKUYO's own reader, the v1022 core (Japanese)
and, when it is configured, Claude; every FPL reading is solved exactly and checked by check.py; an answer is
committed only by agreement.

solve(text, llm='auto'|'off'|'on', data=None, learn=True) ->
  {'answer': str|None, 'value', 'unit', 'route', 'reason', 'readings': [...], 'learned': template id or None}
Readings
  learned     a template learned from an earlier agreeing reading, read with this text's numbers (needs data)
  own         TUKUYO's own reader (English)
  v1022       the v1022 core with its own proof and semantic gate (Japanese only; needs data)
  llm_story   Claude reading the text in story order        } only when Claude is configured; with a verified
  llm_goal    Claude reading the text from the question     } own reading only llm_story runs, as a cross-check
Commit rules (route)
  learned | own | v1022            a TUKUYO reading passed and no other reading disagrees
  <tukuyo route>+llm               a TUKUYO reading and a Claude reading passed and agree
  llm+llm                          no TUKUYO reading; Claude's two readings passed and agree
Everything else abstains: no reading passed, readings disagree (DISAGREE), or one Claude reading passed alone
(SINGLE_LLM_READING: the value is reported as withheld, never committed). When an answer was committed with a
Claude reading in agreement and data is given, the reading is kept as a template (learn.py).
"""
from __future__ import annotations
import re,time
from fractions import Fraction
from pathlib import Path
from . import llm as L
from .solve import solve as _solve
from .check import check as _check
from .fpl import fmt

JA=re.compile(r'[぀-ヿ㐀-鿿]')

def _own(text):
    try:from . import reader
    except ImportError:return None
    return reader.read(text)

def evaluate(spec,route):
    """solve + check one reading"""
    r=_solve(spec)
    if not r['ok']:return {'route':route,'ok':False,'reason':'SOLVE:'+r['reason'],'spec':spec}
    c=_check(spec,r['values'])
    if not c['ok']:return {'route':route,'ok':False,'reason':'CHECK:'+';'.join(c['failures'][:4]),'spec':spec,'value':fmt(r['answer'])}
    return {'route':route,'ok':True,'value':fmt(r['answer']),'answer':r['answer'],'unit':spec.get('answer_unit') or c['unit'],
            'spec':spec,'steps':r['steps'],'values':{k:fmt(v) for k,v in r['values'].items()}}

def _v1022(data,text):
    try:
        from tukuyo_v1022 import cognition
        r=cognition.solve(str(data),text)
    except Exception as e:  # noqa: BLE001 - the older core must never break the generation-4 entry point
        return {'route':'v1022','ok':False,'reason':'V1022:'+type(e).__name__}
    return v1022_reading(r)

def v1022_reading(r):
    """a result of the v1022 core (cognition.solve) as a reading"""
    if r.get('uncertain') or r.get('answer') is None:return {'route':'v1022','ok':False,'reason':'V1022:'+str(r.get('reason'))}
    try:v=Fraction(str(r['answer']).replace(',',''))
    except (ValueError,ZeroDivisionError):return {'route':'v1022','ok':False,'reason':'V1022:NOT_A_NUMBER'}
    return {'route':'v1022','ok':True,'value':fmt(v),'answer':v,'unit':None,'proof_kind':(r.get('proof') or {}).get('kind')}

def solve(text,llm='auto',data=None,learn=True,v1022=None):
    """v1022: a reading of the v1022 core made by the caller (think); it then replaces the core's own call"""
    readings=[];tukuyo_ok=False
    store=None
    if data is not None:
        from .learn import Store,instantiate
        store=Store(Path(data)/'g4')
        try:t=store.find(text)
        except ValueError:t=None;readings.append({'route':'learned','ok':False,'reason':'LEARNED_STORE_SEAL'})
        if t:
            spec=instantiate(t,text)
            if spec:readings.append(evaluate(spec,'learned'));tukuyo_ok|=readings[-1]['ok']
    if v1022 is not None:readings.append(v1022);tukuyo_ok|=v1022['ok']
    if JA.search(text):
        if data is not None and v1022 is None:readings.append(_v1022(data,text));tukuyo_ok|=readings[-1]['ok']
    else:
        own=_own(text)
        if own is not None:
            readings.append(evaluate(own['spec'],'own') if own.get('spec') else {'route':'own','ok':False,'reason':own.get('reason','OWN_UNREAD')})
            tukuyo_ok|=readings[-1]['ok']
    use_llm=llm=='on' or (llm=='auto' and L.available())
    if use_llm:
        views=('story',) if tukuyo_ok else ('story','goal')
        for v in views:
            r=L.read(text,v)
            readings.append(evaluate(r['spec'],'llm_'+v) if r['ok'] else {'route':'llm_'+v,'ok':False,'reason':'LLM:'+str(r.get('reason'))})
            if r.get('reply'):readings[-1]['llm']={k:r['reply'].get(k) for k in ('model','request_id','usage','replayed')}
    good=[r for r in readings if r['ok']]
    out={'answer':None,'value':None,'unit':None,'route':None,'learned':None,
         'readings':[{k:v for k,v in r.items() if k not in ('answer',)} for r in readings]}
    if not good:return {**out,'reason':'NO_VERIFIED_READING' if readings else 'NOT_READ'}
    vals={r['answer'] for r in good}
    if len(vals)>1:return {**out,'reason':'DISAGREE:'+','.join(sorted(fmt(v) for v in vals))}
    mine=[r['route'] for r in good if not r['route'].startswith('llm')]
    llms=[r for r in good if r['route'].startswith('llm')]
    if mine:route='+'.join(dict.fromkeys(mine))+('+llm' if llms else '')
    elif len(llms)>=2:route='llm+llm'
    else:return {**out,'reason':'SINGLE_LLM_READING','withheld':good[0]['value']}
    g=next((r for r in good if r.get('spec')),good[0])
    res={**out,'answer':g['value'],'value':g['value'],'unit':g.get('unit'),'route':route,'reason':None}
    if learn and store is not None and llms and not any(r['route']=='learned' for r in good):
        prov={'route':route,'models':sorted({str((r.get('llm') or {}).get('model')) for r in llms}),
              'request_ids':[(r.get('llm') or {}).get('request_id') for r in llms],'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
        try:res['learned']=store.add(llms[0]['spec'],prov)
        except ValueError:res['learned']=None
    return res

# ----------------------------------------------------------------------------- think
def v1022_story(base):
    """is this answer of the v1022 core a story reading (its proof names a story schema: combine, change_sequence, ...)?
    Expressions ('12*(5+4)') and the formula families (mathprob: average, area, gcd/lcm ...) are not"""
    return bool((base.get('proof') or {}).get('schema'))

def _explain(g):
    sp=g.get('spec') or {}
    facts='、'.join(f"{f['eq']}（{f['span']}）" if f.get('span') else f"{f['eq']}（{f.get('known')}）" for f in sp.get('facts',[]))
    return f"第4世代の読み（{g['route']}）：{facts}。答え：{sp.get('ask')} = {g['value']}" if sp else None

def think(data,text,base,llm='auto',learn=True):
    """`think` with generation 4. base is the v1022 core's result for the same text (cognition.solve).
      * no number in the text, or an answer that is not a number (logic, memory): base, unchanged
      * Japanese: the v1022 reading is one reading among the others (Claude's, when it is configured)
      * English: generation 4 reads the problem. The v1022 core's English story readings (v1022_story) were right 20
        times and wrong 9 times on third-party problems (ASDiv dev), so they neither answer nor block an answer: such
        an answer is reported as withheld. Its expressions and formula families count as a reading
    The result keeps the v1022 shape (answer, uncertain, reason, proof, explanation) and adds 'gen4'."""
    from . import numbers as N
    if not N.find(text):return base
    a=base.get('answer')
    if a is not None and not base.get('uncertain'):
        try:Fraction(str(a).replace(',',''))
        except (ValueError,ZeroDivisionError):return base
    v=v1022_reading(base)
    ja=bool(JA.search(text))
    use=v if (ja or not v['ok'] or not v1022_story(base)) else None
    if not ja and v['ok'] and use is None:ignored={'route':'v1022','value':v['value'],'proof_kind':v.get('proof_kind'),'story':True,'used':False}
    else:ignored=None
    r=solve(text,llm=llm,data=data,learn=learn,v1022=use if v['ok'] or ja else None)
    info={'route':r['route'],'reason':r['reason'],'learned':r.get('learned'),
          'readings':[{k:x.get(k) for k in ('route','ok','value','reason','proof_kind','llm') if x.get(k) is not None} for x in r['readings']]+([ignored] if ignored else [])}
    if r['answer'] is None:
        out={'ok':True,'answer':None,'confidence':0.,'uncertain':True,'recognized':base.get('recognized',True),'proof':None,'gen4':info,
             'reason':r['reason'] if r['reason'] not in ('NO_VERIFIED_READING','NOT_READ') or not ignored else 'V1022_STORY_READING_UNCONFIRMED'}
        if ignored:out['withheld_answer']=ignored['value'];out['explanation']=f"v1022 の読みは {ignored['value']} でしたが、英語の物語の読みは第4世代の読みで確かめられないので、答えを確定しません。"
        elif r.get('withheld'):out['withheld_answer']=r['withheld']
        elif base.get('answer') is None:return {**base,'gen4':info}
        return out
    if v['ok'] and use is not None and v['answer']==Fraction(r['value']):return {**base,'gen4':info}
    g=next((x for x in r['readings'] if x.get('ok') and x.get('spec')),None)
    return {'ok':True,'answer':r['answer'],'confidence':.9,'uncertain':False,'recognized':True,'reason':None,'unit':r.get('unit'),
            'proof':{'kind':'g4_reading','spec':g['spec'],'values':g['values']} if g else None,
            'verification_evidence':{'mode':'G4_EXACT_SOLVE_AND_SEPARATE_CHECK','route':r['route']},
            'explanation':_explain(g) if g else None,'gen4':info}

def ask(text,llm='auto',data=None,learn=True):
    """any question: a problem with numbers goes through solve(); anything else is answered by Claude when it is
    configured, marked unverified (TUKUYO does not check knowledge or conversation, it only labels it)"""
    from . import numbers as N
    r=solve(text,llm=llm,data=data,learn=learn)
    if r['answer'] is not None or N.find(text):return {**r,'kind':'problem','verified':r['answer'] is not None}
    use_llm=llm=='on' or (llm=='auto' and L.available())
    if not use_llm:return {**r,'kind':'question','verified':False,'reason':'NOT_A_PROBLEM_AND_NO_LLM'}
    a=L.answer(text)
    if not a['ok']:return {**r,'kind':'question','verified':False,'reason':'LLM:'+str(a.get('reason'))}
    return {'answer':a['answer'],'route':'llm_voice','kind':'question','verified':False,'source':'claude','model':a.get('model'),
            'request_id':a.get('request_id'),'reason':None,'readings':r['readings']}
