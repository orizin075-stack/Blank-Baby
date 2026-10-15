from __future__ import annotations
from pathlib import Path
from tukuyo_v1001.knowledge import add,search
from tukuyo_v1002.cognition import answer

def run(data):
    d=Path(data);add(d,'月は地球の衛星である。','benchmark');add(d,'TUKUYOの好きな符号名はSELENEである。','benchmark')
    checks=[]
    r=answer(d,'12*(7+3)');checks.append(('arithmetic',r['answer'].strip()=='120'))
    s=search(d,'TUKUYO 符号名',3);checks.append(('retrieval',bool(s) and 'SELENE' in s[0]['text']))
    c=answer(d,'TUKUYOの符号名');checks.append(('rag_answer','SELENE' in c['answer']))
    ok=all(x[1] for x in checks)
    return {'ok':ok,'version':'v1003','checks':[{'name':n,'pass':p} for n,p in checks],
            'claim_boundary':{'gpt4_level_standalone':False,'pluggable_high_capability_provider':True,'local_retrieval':True,'safe_arithmetic':True,'provider_quality_not_certified':True}}
