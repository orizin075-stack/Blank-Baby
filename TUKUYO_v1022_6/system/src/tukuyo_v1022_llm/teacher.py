"""claude-patch1: the LLM as a TEACHER of the local core.

The local core can only use event meanings and wordings it has learned. For questions it
abstains on, the LLM is asked for structured labels in the existing dialogue-learn format.
Labels are accepted only when:
  - every labelled surface really occurs in the question,
  - the LLM's own numeric answer equals the arithmetic implied by its own labels,
  - two independent calls on two different numeric instances agree on every direction,
  - (aliases) the proposed canonical form is one the individual already knows, and two
    calls with the list shown in different orders agree.
Accepted labels go through the unchanged v1022 learner, which still requires two
distinct numeric supports before a rule becomes active. Afterwards the original question
is solved again by the LOCAL core alone, with no LLM involved.

Limitation (kept visible): a teacher that is consistently wrong in a self-consistent way
can still teach a wrong rule. Use more than one model as teacher for important domains.
"""
from __future__ import annotations
import json,re
from . import providers

EVENT_SYSTEM='''あなたは在庫の文章題を分解する先生です。質問文の中の「数量が変わる出来事」を1つずつ取り出して分類し、JSONだけを返します。
{"events":[{"surface":"質問文に書かれている通りの出来事の文（数字を含む）","direction":-1か0か1,"occurred":true/false,"scope":"current_inventory|other_inventory|hypothetical|uncertain"}],
 "answer":"最後に残る数（整数）。決められないなら null"}
direction: 今の在庫が減るなら-1、増えるなら1、変わらないなら0。予定・仮定・否定・他人の在庫は0。'''
ALIAS_SYSTEM='''あなたは言い換えを判定する先生です。質問文の中に、候補リストのどれかと同じ意味の語句があれば対応づけます。JSONだけを返します。
{"aliases":[{"surface":"質問文に書かれている通りの語句","canonical":"候補リストの中の1つ"}]}
同じ意味の語句が無ければ {"aliases":[]} を返します。'''

def _renumber(q,shift):
    # "1箱に…" style unit counts stay 1; every other quantity moves, so the two instances differ.
    return re.sub(r'(?<![\d.])(\d+)(?![\d.])',lambda m:m.group(1) if m.group(1)=='1' else str(int(m.group(1))+shift),q)

def _implied(q,labels):
    """Arithmetic implied by the labels, recomputed locally (not trusted from the LLM)."""
    from tukuyo_v1022 import cognition
    s=cognition.normalize(q);p=cognition.package(s)
    if p:initial=p['per']*p['count'];per=p['per'];unit=p['unit'];box=p['container']
    else:
        m=re.search(rf'(\d+)\s*({cognition.UNITS})(?:あります|ある|持っています|持っている|ありました|あった|あり)',s)
        if not m:return None
        initial=int(m[1]);per=1;unit=m[2];box='__none__'
    n=initial
    for e in labels:
        qs=list(re.finditer(rf'(\d+)\s*({cognition.UNITS}|{cognition.BOXES})',cognition.normalize(e['surface'])))
        if len(qs)!=1:return None
        k=int(qs[0][1])*(per if qs[0][2]==box else 1)
        n+=k*(e['direction'] if e['occurred'] and e['scope']=='current_inventory' else 0)
    return n if n>=0 else None

def _event_labels(q,cfg=None):
    rep=providers.complete(EVENT_SYSTEM,json.dumps({'question':q},ensure_ascii=False),temperature=0.0,cfg=cfg)
    o=providers.extract_json(rep.text);labels=[]
    for e in o.get('events',[]):
        if not isinstance(e,dict):return None,'LABEL_MALFORMED',rep
        surf=str(e.get('surface','')).strip();d=e.get('direction');occ=e.get('occurred');sc=e.get('scope')
        if not surf or surf not in q:return None,'SURFACE_NOT_IN_QUESTION',rep
        if type(d) is not int or d not in (-1,0,1) or type(occ) is not bool or sc not in ('current_inventory','other_inventory','hypothetical','uncertain'):return None,'LABEL_SCHEMA',rep
        labels.append({'surface':surf,'direction':d,'occurred':occ,'scope':sc})
    if not labels:return None,'NO_EVENTS',rep
    implied=_implied(q,labels)
    if implied is None:return None,'IMPLIED_ANSWER_UNDEFINED',rep
    if str(o.get('answer')).strip()!=str(implied):return None,'LLM_ANSWER_INCONSISTENT_WITH_OWN_LABELS',rep
    return {'labels':labels,'answer':str(implied)},None,rep

def _teach_event(data,q,teacher_name,teachers=None):
    variants=[q,_renumber(q,2)];per=[]
    for cfg in (teachers or [None]):
        got=[];who=providers.name_of(cfg) if cfg else teacher_name
        for v in variants:
            r,err,rep=_event_labels(v,cfg)
            if err:return {'outcome':'rejected','reason':err,'teacher':who,'variant':v},None
            got.append((v,r))
        dirs=[[(e['direction'],e['occurred'],e['scope']) for e in r['labels']] for _,r in got]
        if dirs[0]!=dirs[1]:return {'outcome':'rejected','reason':'TEACHER_INCONSISTENT_ACROSS_INSTANCES','teacher':who},None
        per.append((got,dirs[0],[r['answer'] for _,r in got]))
    # claude-patch2: with several teachers, every one must give the same directions AND the same recomputed answers
    if len({json.dumps([d,a]) for _,d,a in per})!=1:return {'outcome':'rejected','reason':'TEACHERS_DISAGREE','teachers':len(per)},None
    got=per[0][0]
    examples=[{'id':f'llm-teach-{i}','question':v,'expected_answer':r['answer'],'event_labels':r['labels'],'explanation':'LLM teacher label; locally recomputed'} for i,(v,r) in enumerate(got)]
    return {'outcome':'proposed','labels':got[0][1]['labels'],'expected':got[0][1]['answer']},{'teacher':teacher_name,'examples':examples}

def _known_canonicals(data):
    from tukuyo_v1022 import cognition
    st=cognition.state(data);known={f['relation'] for f in st.get('facts',[])}|set(st.get('aliases',{}).values())
    return sorted(k for k in known if 1<len(k)<=30)

def _alias_call(q,cands,cfg=None):
    rep=providers.complete(ALIAS_SYSTEM,json.dumps({'question':q,'candidates':cands},ensure_ascii=False),temperature=0.0,cfg=cfg)
    o=providers.extract_json(rep.text);out=set()
    for a in o.get('aliases',[]):
        if not isinstance(a,dict):continue
        s=str(a.get('surface','')).strip();c=str(a.get('canonical','')).strip()
        if s and c and s in q and c in cands and s!=c:out.add((s,c))
    return out

def _teach_alias(data,q,teacher_name,teachers=None):
    cands=_known_canonicals(data)
    if not cands:return {'outcome':'not_teachable','reason':'NO_KNOWN_CANONICAL_FORMS'},None
    agreed=None;a=b=set()
    for cfg in (teachers or [None]):
        a=_alias_call(q,cands,cfg);b=_alias_call(q,list(reversed(cands)),cfg)
        agreed=(a&b) if agreed is None else agreed&a&b
    if not agreed:return {'outcome':'rejected','reason':'NO_AGREED_ALIAS' if (a or b) else 'NO_ALIAS_PROPOSED'},None
    return {'outcome':'proposed','aliases':sorted(agreed)},{'teacher':teacher_name,'examples':[{'id':'llm-alias','question':q,'aliases':[{'surface':s,'canonical':c} for s,c in sorted(agreed)]}]}

def teach(data,questions):
    from tukuyo_v1022 import cognition
    from tukuyo_v1019.lifecycle import require_alive
    require_alive(data);import os
    teachers=providers.teachers()
    if not teachers:raise providers.LLMError('LLM_NOT_CONFIGURED')
    need=int(os.environ.get('TUKUYO_LLM_MIN_TEACHERS','1'))
    if not 1<=need<=8:raise providers.LLMError('TUKUYO_LLM_MIN_TEACHERS_LIMIT')
    if len(teachers)<need:raise providers.LLMError(f'NEED_{need}_TEACHERS_HAVE_{len(teachers)}')
    names=[providers.name_of(c) for c in teachers]
    teacher_name=names[0] if len(names)==1 else 'consensus:'+'+'.join(names)
    rows=[]
    for q in questions:
        q=str(q);before=cognition.solve(data,q)
        if before.get('recognized') and not before.get('uncertain'):rows.append({'question':q,'outcome':'already_known','answer':before['answer']});continue
        reason=before.get('reason')
        try:
            if reason=='UNKNOWN_EVENT_MEANING':row,bundle=_teach_event(data,q,teacher_name,teachers)
            elif reason=='MEMORY_PREMISES_MISSING':row,bundle=_teach_alias(data,q,teacher_name,teachers)
            else:row,bundle={'outcome':'not_teachable','reason':reason},None
        except providers.LLMError as e:row,bundle={'outcome':'error','reason':str(e)},None
        if bundle:
            cognition.learn(data,bundle,teacher_name)
            after=cognition.solve(data,q)
            row.update({'outcome':'learned' if (after.get('recognized') and not after.get('uncertain')) else 'taught_but_not_yet_active',
                        'local_answer_after':after.get('answer'),'local_reason_after':after.get('reason')})
        rows.append({'question':q,**row})
    summary={k:sum(1 for r in rows if r['outcome']==k) for k in ('learned','taught_but_not_yet_active','rejected','not_teachable','already_known','error')}
    return {'ok':True,'version':'v1022.5+claude-patch4','teacher':teacher_name,'teachers':names,'summary':summary,'rows':rows,
            'claim_boundary':{'local_core_answers_without_llm_after_learning':True,'llm_labels_locally_recomputed':True,'distinct_configured_teachers_that_must_agree':len(names),
                              'teacher_independence_verified':False,'consistently_wrong_teacher_detectable':False,'note':'consensus cannot rule out a shared systematic error'}}
