"""Active tutoring: learn a numeric-slot method only after two distinct examples.

Two views of one model are not independent teachers. Formal checking is
conditional on their translation. No general-language/weight learning claim.
"""
import copy,hashlib,json
from fractions import Fraction
from pathlib import Path
from . import api,llm,learn,numbers,chatgpt_chat as chat
from .fpl import parse_unit
from .methods import signature
from tukuyo_v1019.transaction import transactional

def needs(data,queries):
    if not isinstance(queries,list) or not 1<=len(queries)<=16 or any(not isinstance(q,str) or not 1<=len(q)<=6000 for q in queries):
        raise ValueError('CHATGPT_STUDY_QUERY_BOUND')
    rows=[]
    for q in queries:
        r=api.solve(q,llm='off',data=data,learn=False)
        rows.append({'query':q,'answer':r['answer'],'needs_teacher':r['answer'] is None,'reason':r['reason']})
    return {'ok':True,'queries':rows,'external_calls':0,'selection':'unresolved_local_numeric_problem'}

@transactional()
def promote(data,specs,provenance):
    st=learn.Store(Path(data)/'g4');ids=[st.add(s,provenance) for s in specs]
    if not all(ids) or len(set(ids))!=1:raise ValueError('CHATGPT_TEMPLATE_CONFLICT')
    return ids[0]

def study(data,queries,session='study',max_calls=32,force=False):
    todo=needs(data,queries)['queries'];groups={};rows=[];calls=0
    for item in todo:
        q=item['query']
        if not item['needs_teacher'] and not force:rows.append({**item,'status':'already_solved_locally'});continue
        readings=[]
        for view in ('story','goal'):
            t=chat.turn(data,'Text: '+q,session,max_calls,system=llm.system_prompt(view),schema=llm.FPL_SCHEMA,
                        kind='study:'+view+':1',history=False)
            if not t.get('ok'):
                readings.append({'ok':False,'reason':t.get('reason')})
                if (t.get('recovery') or {}).get('action')=='pause_usage':
                    rows.append({'query':q,'status':'stopped_usage','formal_checks_passed':False,'reasons':[t.get('reason')]})
                    return {'ok':False,'reason':t.get('reason'),'rows':rows,'adopted_templates':[],
                            'successful_teacher_replies':calls,'session':session,'usage_paused':True,
                            'weights_updated':False,'verified_semantics':False}
                continue
            calls+=1
            r=llm.read_reply(q,t['reply'])
            e=api.evaluate(r['spec'],view) if r.get('ok') else r
            if e.get('ok'):
                c=api._input_coverage(q,e['value'])
                if c.get('recognized') and not c['ok']:e={**e,'ok':False,'reason':c['reason']}
            readings.append(e)
        good=len(readings)==2 and all(x.get('ok') for x in readings)
        if good:good=readings[0]['value']==readings[1]['value'] and parse_unit(readings[0]['unit'])==parse_unit(readings[1]['unit'])
        row={'query':q,'status':'candidate' if good else 'not_learned','formal_checks_passed':bool(good),
             'reasons':[x.get('reason') for x in readings if not x.get('ok')],'answer':readings[0].get('value') if good else None}
        rows.append(row)
        if not good:continue
        tpl=learn.template(readings[0]['spec'])
        if not tpl:row['status']='template_not_abstractable';continue
        k=signature(tpl)
        groups.setdefault(k,[]).append((readings[0]['spec'],row))
    adopted=[]
    for examples in groups.values():
        signatures={tuple(str(n.value) for n in numbers.find(s['text'])) for s,_ in examples}
        if len(signatures)<2:
            for _,row in examples:row['status']='needs_distinct_numeric_example'
            continue
        specs=[x[0] for x in examples]
        try:
            tid=promote(data,specs,{'route':'chatgpt_two_example_study','parents':['chatgpt'],'distinct_numeric_examples':len(signatures),
                                   'same_provider_views_independent':False,'semantic_translation_fully_proven':False})
        except ValueError:
            for _,row in examples:row['status']='template_conflict'
            continue
        adopted.append(tid)
        for _,row in examples:row['status']='adopted';row['template_id']=tid
    return {'ok':True,'rows':rows,'adopted_templates':adopted,'successful_teacher_replies':calls,'session':session,
            'verified_semantics':False,'requires_two_distinct_numeric_examples':True,'weights_updated':False,
            'teacherless_numeric_transfer_enabled':bool(adopted)}
