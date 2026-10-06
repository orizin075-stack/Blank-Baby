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
    if r.get('uncertain') or r.get('answer') is None:return {'route':'v1022','ok':False,'reason':'V1022:'+str(r.get('reason'))}
    try:v=Fraction(str(r['answer']).replace(',',''))
    except (ValueError,ZeroDivisionError):return {'route':'v1022','ok':False,'reason':'V1022:NOT_A_NUMBER'}
    return {'route':'v1022','ok':True,'value':fmt(v),'answer':v,'unit':None,'proof_kind':(r.get('proof') or {}).get('kind')}

def solve(text,llm='auto',data=None,learn=True):
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
    if JA.search(text):
        if data is not None:readings.append(_v1022(data,text));tukuyo_ok|=readings[-1]['ok']
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
