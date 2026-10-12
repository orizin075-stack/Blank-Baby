"""Claim truth is necessary; relevance and whole-answer support are separate.

This bounded policy verifies only a locally established original question and
an exact answer, or an exact relevant cited memory. Free-form added statements
remain unverified even when a correct calculation occurs next to them.
"""
import re
import unicodedata

def _norm(x):return re.sub(r'\s+','',unicodedata.normalize('NFKC',str(x)))

def check(data,query,answer,claims,mem_index):
    from tukuyo_v1022 import cognition
    local=cognition.solve(data,query)
    report={'ok':False,'original_query_bound':False,'whole_answer_covered':False,
            'reason':'ORIGINAL_QUESTION_NOT_ESTABLISHED','free_form_entailment_established':False}
    if local.get('uncertain') or local.get('answer') is None:return report
    value=_norm(local['answer']);a=_norm(answer);q=_norm(query)
    relevant=[]
    for c in claims if isinstance(claims,list) else []:
        if not isinstance(c,dict):continue
        t=c.get('type')
        if t=='local' and _norm(c.get('question',''))==q and _norm(c.get('value',''))==value:
            relevant.append(c)
        elif t=='calc' and _norm(c.get('value',''))==value and (local.get('proof') or {}).get('kind') in ('arithmetic','deliberation'):
            # The independently established original question supplies meaning;
            # _check supplies arithmetic validity. A same-value unrelated claim
            # alone cannot establish an unknown question.
            relevant.append(c)
        elif t=='memory' and str(c.get('id','')) in mem_index:
            m=_norm(mem_index[str(c['id'])]);quote=_norm(c.get('quote',''))
            p=local.get('proof') or {}
            entity=_norm(p.get('entity',''));attribute=_norm(p.get('attribute',p.get('relation','')))
            if entity and attribute and entity in quote and attribute in quote and value in quote and quote in m:
                relevant.append(c)
    report['original_query_bound']=bool(relevant)
    if not relevant:report['reason']='CLAIMS_NOT_BOUND_TO_ORIGINAL_QUESTION';return report
    # Only an exact value plus a bounded politeness suffix is entailed.
    stripped=re.sub(r'(?:です|である|だ)?[。.!！]*$','',a)
    covered=stripped==value
    if not covered:
        for c in relevant:
            if c.get('type')=='memory':
                quote=_norm(c.get('quote',''))
                if a in (quote,'記憶では、'+quote,'記憶では,'+quote):covered=True
    report.update(ok=covered,whole_answer_covered=covered,
                  reason=None if covered else 'ANSWER_HAS_UNSUPPORTED_CONTENT')
    return report
