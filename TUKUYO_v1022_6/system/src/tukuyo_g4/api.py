"""generation 4: one entry point. Readings come from TUKUYO's own reader and, when it is configured, from Claude;
every reading is solved exactly and checked by check.py; the answer is committed only by agreement.

solve(text, llm='auto'|'off'|'on') ->
  {'answer': str|None, 'value': 'p/q', 'unit', 'route', 'reason', 'readings': [...]}
Commit rules (route):
  own         TUKUYO's own reading passed the checker and no other reading disagrees
  own+llm     the own reading and a Claude reading passed and agree
  llm+llm     the own reader cannot read the text; Claude's two readings (story and goal) passed and agree
Everything else abstains: no reading passed, readings disagree (DISAGREE), or a single Claude reading passed alone
(SINGLE_LLM_READING: the value is reported as withheld, never committed).
"""
from __future__ import annotations
from fractions import Fraction
from . import llm as L
from .solve import solve as _solve
from .check import check as _check
from .fpl import fmt

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

def solve(text,llm='auto'):
    readings=[]
    own=_own(text)
    if own is not None:
        readings.append(evaluate(own['spec'],'own') if own.get('spec') else {'route':'own','ok':False,'reason':own.get('reason','OWN_UNREAD')})
        own_ok=readings[-1]['ok']
    else:own_ok=False
    use_llm=llm=='on' or (llm=='auto' and L.available())
    if use_llm:
        views=('story',) if own_ok else ('story','goal')
        for v in views:
            r=L.read(text,v)
            readings.append(evaluate(r['spec'],'llm_'+v) if r['ok'] else {'route':'llm_'+v,'ok':False,'reason':'LLM:'+str(r.get('reason'))})
    good=[r for r in readings if r['ok']]
    out={'answer':None,'value':None,'unit':None,'route':None,'readings':[{k:v for k,v in r.items() if k!='answer'} for r in readings]}
    if not good:
        return {**out,'reason':'NO_VERIFIED_READING' if readings else 'NOT_READ'}
    vals={r['answer'] for r in good}
    if len(vals)>1:return {**out,'reason':'DISAGREE:'+','.join(sorted(fmt(v) for v in vals))}
    routes={r['route'] for r in good}
    if 'own' in routes:route='own+llm' if len(routes)>1 else 'own'
    elif len(routes)>=2:route='llm+llm'
    else:return {**out,'reason':'SINGLE_LLM_READING','withheld':good[0]['value']}
    g=good[0]
    return {**out,'answer':g['value'],'value':g['value'],'unit':g['unit'],'route':route,'reason':None}
