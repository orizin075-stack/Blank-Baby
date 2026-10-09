"""generation 4: one entry point. Readings come from learned templates, TUKUYO's own reader, the v1022 core (Japanese)
and, when they are configured, the parents (Claude, ChatGPT, Gemini: llm.py); every FPL reading is solved exactly and
checked by check.py; an answer is committed only by agreement.

solve(text, llm='auto'|'off'|'on', data=None, learn=True) ->
  {'answer': str|None, 'value', 'unit', 'route', 'reason', 'readings': [...], 'learned': template id or None}
Readings
  learned     a template learned from an earlier agreeing reading, read with this text's numbers (needs data)
  own         TUKUYO's own reader (English)
  v1022       the v1022 core with its own proof and semantic gate (Japanese only; needs data)
  llm_story, llm_goal     Claude reading the text in story order / from the question
  llm_chatgpt_story       ChatGPT reading the text in story order
  llm_gemini_story        Gemini reading the text in story order
  Which parents read: with a verified TUKUYO reading, only the first parent, as a cross-check; otherwise every
  parent reads once (story order), and when only one parent is configured it reads twice (story and goal).
Commit rules (route)
  learned | own | v1022            a TUKUYO reading passed and no other reading disagrees
  <tukuyo route>+llm               a TUKUYO reading and a parent's reading passed and agree
  chatgpt+claude, claude+gemini …  no TUKUYO reading; readings of two or more different parents passed and agree
  llm+llm                          no TUKUYO reading; the only configured parent's two readings passed and agree
Everything else abstains: no reading passed, readings disagree (DISAGREE), or the readings that passed come from one
parent while others were asked (SINGLE_LLM_READING: the value is reported as withheld, never committed). When an
answer was committed with a parent's reading in agreement and data is given, the reading is kept as a template
(learn.py), with the parents and models that agreed.
"""
from __future__ import annotations
import os,re,time
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
    """solve + check one reading. A reading may come from outside, so a fault while solving or checking it is a failed
    reading with its reason, never an exception"""
    try:r=_solve(spec)
    except (ArithmeticError,ValueError,KeyError,IndexError,TypeError,AttributeError,RecursionError) as e:
        return {'route':route,'ok':False,'reason':'SOLVE:INTERNAL:'+type(e).__name__,'spec':spec}
    if not r['ok']:return {'route':route,'ok':False,'reason':'SOLVE:'+r['reason'],'spec':spec}
    try:c=_check(spec,r['values'])
    except (ArithmeticError,ValueError,KeyError,IndexError,TypeError,AttributeError,RecursionError) as e:
        return {'route':route,'ok':False,'reason':'CHECK:INTERNAL:'+type(e).__name__,'spec':spec}
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

def solve(text,llm='auto',data=None,learn=True,v1022=None,order=None):
    """v1022: a reading of the v1022 core made by the caller (think); it then replaces the core's own call.
    order: the parents in the order to ask them (life.trust_order: the child's trust), the configured ones only"""
    readings=[];tukuyo_ok=False
    store=None
    if data is not None:
        from .learn import Store,instantiate
        store=Store(Path(data)/'g4')
        try:t=store.find(text)
        except ValueError as e:t=None;readings.append({'route':'learned','ok':False,'reason':str(e)})
        if t:
            spec=instantiate(t,text)
            if spec:readings.append(evaluate(spec,'learned'));readings[-1]['template']=store.key_of(text);tukuyo_ok|=readings[-1]['ok']
    if v1022 is not None:readings.append(v1022);tukuyo_ok|=v1022['ok']
    if JA.search(text):
        if data is not None and v1022 is None:readings.append(_v1022(data,text));tukuyo_ok|=readings[-1]['ok']
    else:
        own=_own(text)
        if own is not None:
            readings.append(evaluate(own['spec'],'own') if own.get('spec') else {'route':'own','ok':False,'reason':own.get('reason','OWN_UNREAD')})
            tukuyo_ok|=readings[-1]['ok']
    use_llm=llm=='on' or (llm=='auto' and L.available())
    ps=(L.parents() or ['claude']) if use_llm else []
    if order:ps=[p for p in order if p in ps]+[p for p in ps if p not in order]
    if use_llm:
        if tukuyo_ok:plan=[(ps[0],'story')]
        elif len(ps)==1:plan=[(ps[0],'story'),(ps[0],'goal')]
        else:plan=[(p,'story') for p in ps]
        for parent,v in plan:
            route='llm_'+v if parent=='claude' else f'llm_{parent}_{v}'
            r=L.read(text,v,parent=parent)
            readings.append(evaluate(r['spec'],route) if r['ok'] else {'route':route,'ok':False,'reason':'LLM:'+str(r.get('reason'))})
            readings[-1]['parent']=parent
            if r.get('reply'):readings[-1]['llm']={'parent':parent,**{k:r['reply'].get(k) for k in ('model','request_id','usage','replayed')}}
    good=[r for r in readings if r['ok']]
    out={'answer':None,'value':None,'unit':None,'route':None,'learned':None,
         'readings':[{k:v for k,v in r.items() if k not in ('answer',)} for r in readings]}
    if not good:return {**out,'reason':'NO_VERIFIED_READING' if readings else 'NOT_READ'}
    vals={r['answer'] for r in good}
    if len(vals)>1:return {**out,'reason':'DISAGREE:'+','.join(sorted(fmt(v) for v in vals))}
    mine=[r['route'] for r in good if not r['route'].startswith('llm')]
    llms=[r for r in good if r['route'].startswith('llm')]
    fams=sorted({r.get('parent','claude') for r in llms})
    if mine:route='+'.join(dict.fromkeys(mine))+('+llm' if llms else '')
    elif len(fams)>=2:route='+'.join(fams)
    elif len(llms)>=2 and len(ps)==1:route='llm+llm'
    else:return {**out,'reason':'SINGLE_LLM_READING','withheld':good[0]['value']}
    g=next((r for r in good if r.get('spec')),good[0])
    res={**out,'answer':g['value'],'value':g['value'],'unit':g.get('unit'),'route':route,'reason':None}
    if learn and store is not None and llms and not any(r['route']=='learned' for r in good):
        prov={'route':route,'parents':fams,'models':sorted({str((r.get('llm') or {}).get('model')) for r in llms}),
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

def think(data,text,base,llm='auto',learn=True,order=None):
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
    r=solve(text,llm=llm,data=data,learn=learn,v1022=use if v['ok'] or ja else None,order=order)
    info={'route':r['route'],'reason':r['reason'],'learned':r.get('learned'),'value':r.get('value'),
          'readings':[{k:x.get(k) for k in ('route','ok','value','reason','proof_kind','llm','parent','template') if x.get(k) is not None} for x in r['readings']]+([ignored] if ignored else [])}
    if r['answer'] is None:
        out={'ok':True,'answer':None,'confidence':0.,'uncertain':True,'recognized':base.get('recognized',True),'proof':None,'gen4':info,
             'reason':r['reason'] if r['reason'] not in ('NO_VERIFIED_READING','NOT_READ') or not ignored else 'V1022_STORY_READING_UNCONFIRMED'}
        if ignored:out['withheld_answer']=ignored['value'];out['explanation']=f"v1022 の読みは {ignored['value']} でしたが、英語の物語の読みは第4世代の読みで確かめられないので、答えを確定しません。"
        elif r.get('withheld'):out['withheld_answer']=r['withheld']
        elif base.get('answer') is None and not str(r['reason']).startswith('DISAGREE'):return {**base,'gen4':info}
        return out
    if v['ok'] and use is not None and v['answer']==Fraction(r['value']):return {**base,'gen4':info}
    g=next((x for x in r['readings'] if x.get('ok') and x.get('spec')),None)
    return {'ok':True,'answer':r['answer'],'confidence':.9,'uncertain':False,'recognized':True,'reason':None,'unit':r.get('unit'),
            'proof':{'kind':'g4_reading','spec':g['spec'],'values':g['values']} if g else None,
            'verification_evidence':{'mode':'G4_EXACT_SOLVE_AND_SEPARATE_CHECK','route':r['route']},
            'explanation':_explain(g) if g else None,'gen4':info}

def _same(a,b):
    norm=lambda x:re.sub(r'[\s。、．，,.!！?？「」『』"\'()（）]','',str(x)).lower()
    return norm(a)==norm(b)

NOT_PROBLEM_SHAPES=('EN:QUESTION_FORM','EN:NO_QUESTION','EN:NO_SENTENCES','EN:QUESTION_NOT_LAST')
def _a_problem(r):
    """was this text taken as a math problem? A reading was written (by TUKUYO or a parent); or the parents asked did
    not all say it is not one; or, with no parent asked, TUKUYO's own reader found the shape of a problem ('How many
    ...?'). 'Who won the World Cup in 2018?' has a number but is a question"""
    rs=r.get('readings') or []
    if any(x.get('spec') or x.get('ok') for x in rs):return True
    llms=[x for x in rs if str(x.get('route','')).startswith('llm')]
    if llms and any(str(x.get('reason'))!='LLM:LLM_NOT_CONFIGURED' for x in llms):
        return any(str(x.get('reason'))!='LLM:NOT_READABLE' for x in llms)
    own=[x for x in rs if x.get('route')=='own']
    return not (own and all(str(x.get('reason')) in NOT_PROBLEM_SHAPES for x in own))

def ask(text,llm='auto',data=None,learn=True,voices='one',order=None,persona='',remember=True):
    """any question: a problem with numbers goes through solve(); anything else is answered by the parents when they
    are configured, marked unverified (TUKUYO does not check knowledge or conversation, it only labels it).
    voices='one': the voice parent answers (TUKUYO_LLM_VOICE, else the first of order, else llm.voice()); voices='all':
    every parent answers, the voice's answer comes first, and 'agree' says whether the short answers are the same once
    spaces and punctuation are removed. With data, an answer that two or more parents agree on is remembered
    (memory.py) and given again later without asking (route 'remembered', source 'parents_agreed', still unverified).
    persona: who is speaking (life.persona), added to the parents' instructions"""
    from . import numbers as N
    r=solve(text,llm=llm,data=data,learn=learn,order=order)
    if r['answer'] is not None:return {**r,'kind':'problem','verified':True}
    if N.find(text) and _a_problem(r):return {**r,'kind':'problem','verified':False}
    refused={}
    if data is not None and text.strip():
        from .memory import Memory
        try:e=Memory(data).recall(text)
        except ValueError as x:e=None;refused={'memory_refused':str(x)}        # a store that is not its own is not used
        if e:return {'answer':e['answer'],'route':'remembered','kind':'question','verified':False,'source':'parents_agreed','parents':e['parents'],
                     'models':e['models'],'since':e['utc'],'confirmed':e.get('confirmed',1),'reason':None,'readings':r['readings']}
    use_llm=llm=='on' or (llm=='auto' and L.available())
    if not use_llm:return {**r,'kind':'question','verified':False,'reason':'NOT_A_PROBLEM_AND_NO_LLM',**refused}
    ps=L.parents() or ['claude']
    if order:ps=[p for p in order if p in ps]+[p for p in ps if p not in order]
    env_voice=os.environ.get('TUKUYO_LLM_VOICE','').strip()
    v=env_voice if env_voice in ps else ps[0]
    who=[v]+[p for p in ps if p!=v] if voices=='all' else [v]
    got=[L.answer(text,parent=p,persona=persona) for p in who]
    ok=[a for a in got if a['ok']]
    if not ok:return {**r,'kind':'question','verified':False,'reason':'LLM:'+str(got[0].get('reason'))}
    a=ok[0]
    out={'answer':a['answer'],'route':'llm_voice','kind':'question','verified':False,'source':a.get('parent'),'model':a.get('model'),
         'request_id':a.get('request_id'),'reason':None,'readings':r['readings'],**refused}
    if voices=='all':
        out['answers']=[{k:x.get(k) for k in ('parent','ok','answer','model','reason')} for x in got]
        out['agree']=len(ok)>=2 and all(_same(x['answer'],a['answer']) for x in ok)
        if out['agree'] and remember and data is not None:
            from .memory import Memory
            try:out['remembered']=bool(Memory(data).remember(text,[{'parent':x['parent'],'model':x.get('model'),'answer':x['answer']} for x in ok]))
            except ValueError:out['remembered']=False
    return out
