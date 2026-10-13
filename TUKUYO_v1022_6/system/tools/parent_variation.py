#!/usr/bin/env python3
"""How the child takes parents who write the same reading in other ways (the fusion limits round): real parents name
units and quantities as they like, quote the text loosely and order facts as they please; the recorded parents of the
tests all write the reading the same way. No parent is asked (cost 0); only the dev split is used.

  parent_variation.py DATA_DIR [--out REPORT.json]

For every reading the child's own reader verifies on ASDiv dev, each variant below rewrites it without changing what it
says. For each variant:
  checker   does the rewritten reading still pass solve + check, with the same answer
  agree     two parents (the own reader switched off), one writing the reading as it is and one the variant: does the
            child answer (and is it right), or hold back, and why
"""
from __future__ import annotations
import argparse,collections,copy,json,os,random,re,sys,tempfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE/'src'));sys.path.insert(0,str(HERE/'tools'))
import g4_measure as M
from tukuyo_g4 import api,llm

def _plural(u):
    if not isinstance(u,str) or not re.fullmatch(r'[a-z]+',u or ''):return u
    if u.endswith('s'):return u
    return u[:-1]+'ies' if u.endswith('y') and u[-2:-1] not in 'aeiou' else u+('es' if u.endswith(('ch','sh','x')) else 's')
# an English plural as a parent writes it: irregular nouns, -ves, -oes, -es, the last word of 't-shirt' and the first of
# 'piece of candy' (written here from English, not from the checker's table)
_IRREGULAR={'person':'people','child':'children','man':'men','woman':'women','foot':'feet','tooth':'teeth','mouse':'mice','goose':'geese',
            'leaf':'leaves','knife':'knives','wolf':'wolves','loaf':'loaves','shelf':'shelves','half':'halves','life':'lives','calf':'calves',
            'thief':'thieves','scarf':'scarves','potato':'potatoes','tomato':'tomatoes','hero':'heroes','mango':'mangoes','bus':'buses',
            'lens':'lenses','quiz':'quizzes','fish':'fish','sheep':'sheep','deer':'deer'}
def _english_word(w):
    if w in _IRREGULAR:return _IRREGULAR[w]
    if w.endswith('y') and w[-2:-1] not in 'aeiou':return w[:-1]+'ies'
    return w+('es' if w.endswith(('s','x','z','ch','sh')) else 's')
def _english_plural(u):
    if not isinstance(u,str):return u
    m=re.fullmatch(r'([a-z]+)( of [a-z ]+)',u)
    if m:return _english_word(m.group(1))+m.group(2)
    m=re.fullmatch(r'([a-z]+(?:-[a-z]+)*-)?([a-z]+)',u or '')
    return (m.group(1) or '')+_english_word(m.group(2)) if m else u
def _units(sp,f):
    sp=copy.deepcopy(sp)
    for q in sp['quantities']:
        if '/' not in str(q.get('unit','')):q['unit']=f(q.get('unit'))
    if sp.get('answer_unit') and '/' not in sp['answer_unit']:sp['answer_unit']=f(sp['answer_unit'])
    return sp
def _rename(sp):
    sp=copy.deepcopy(sp);names=[q['name'] for q in sp['quantities']];new={n:'the_'+n for n in names}
    for q in sp['quantities']:q['name']=new[q['name']]
    pat=re.compile(r'\b('+'|'.join(sorted(map(re.escape,names),key=len,reverse=True))+r')\b')
    for f in sp['facts']:f['eq']=pat.sub(lambda m:new[m.group(1)],f['eq'])
    sp['ask']=new[sp['ask']];return sp
def _spans(sp,f):
    sp=copy.deepcopy(sp)
    for x in sp['facts']:
        if x.get('span'):x['span']=f(x['span'])
    return sp
def _eqs(sp,f):
    sp=copy.deepcopy(sp)
    for x in sp['facts']:x['eq']=f(x['eq'])
    return sp
VARIANTS={
 'unit_plural':lambda sp:_units(sp,_plural),
 'unit_plural_english':lambda sp:_units(sp,_english_plural),
 'unit_capitalized':lambda sp:_units(sp,lambda u:u.capitalize() if isinstance(u,str) else u),
 'answer_unit_dollar_sign':lambda sp:{**copy.deepcopy(sp),'answer_unit':'$'} if sp.get('answer_unit') in ('dollar','dollars') else copy.deepcopy(sp),
 'answer_unit_empty':lambda sp:{**copy.deepcopy(sp),'answer_unit':''},
 'quantity_names':_rename,
 'span_lower_case':lambda sp:_spans(sp,lambda s:s.lower()),
 'span_trailing_period':lambda sp:_spans(sp,lambda s:s.rstrip('.')+'.'),
 'span_extra_spaces':lambda sp:_spans(sp,lambda s:re.sub(r' ','  ',s,count=1)),
 'facts_shuffled':lambda sp:{**copy.deepcopy(sp),'facts':random.Random(len(sp['facts'])).sample(copy.deepcopy(sp['facts']),len(sp['facts']))},
 'numbers_as_decimals':lambda sp:_eqs(sp,lambda e:re.sub(r'(?<![\w.])(\d+)(?![\w.])',r'\1.0',e)),
 'eq_without_spaces':lambda sp:_eqs(sp,lambda e:re.sub(r'\s+','',e)),
}

def reply(sp):
    return {'readable':True,'quantities':sp['quantities'],'facts':[{'eq':f['eq'],'span':f.get('span',''),'known':f.get('known','')} for f in sp['facts']],
            'ask':sp['ask'],'answer_unit':sp.get('answer_unit',''),'unused':sp.get('unused') or []}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('data');ap.add_argument('--out');ap.add_argument('--only');a=ap.parse_args()
    V=M.verified(a.data);out={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'readings':len(V),'variants':{}}
    saved={k:os.environ.get(k) for k in ('TUKUYO_LLM_REPLAY','TUKUYO_LLM_PARENTS')};own=api._own;api._own=lambda text:None
    os.environ.pop('TUKUYO_LLM_PARENTS',None)
    try:
        for name,fn in VARIANTS.items():
            if a.only and name not in a.only.split(','):continue
            chk=collections.Counter();agr=collections.Counter();why=collections.Counter();lines=[];changed=0
            for text,sp,ans in V:
                v=fn(sp);changed+=v!=sp
                e=api.evaluate(copy.deepcopy(v),'variant')
                chk['same_answer' if e['ok'] and e['value']==api.fmt(ans) else ('other_answer' if e['ok'] else 'refused')]+=1
                if not e['ok']:why[str(e.get('reason'))[:60]]+=1
                for par,o in (('claude',sp),('gemini',v)):
                    h=llm.request_hash(llm._kind(par,'read:story:'+llm.PROMPT_VERSION),llm.system_prompt('story'),'Text: '+text)
                    lines.append(json.dumps({'parent':par,'hash':h,'ok':True,'text':json.dumps(reply(o),ensure_ascii=False),'model':'sim'},ensure_ascii=False))
            with tempfile.NamedTemporaryFile('w',suffix='.jsonl',delete=False,encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
            os.environ['TUKUYO_LLM_REPLAY']=f.name;llm._replay_cache.clear()
            for text,sp,ans in V:
                r=api.solve(text,llm='on',learn=False)
                agr['abstain:'+str(r['reason']).split(':')[0] if r['answer'] is None else ('right' if r['value']==api.fmt(ans) else 'wrong')]+=1
            os.unlink(f.name)
            out['variants'][name]={'changed':changed,'checker':dict(chk),'checker_refusals':dict(why.most_common(6)),'two_parents':dict(agr)}
            print(f"{name:24s} changed {changed:3d}  checker {dict(chk)}  two parents {dict(agr)}",flush=True)
    finally:
        api._own=own;llm._replay_cache.clear()
        for k,v in saved.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v
    if a.out:Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')

if __name__=='__main__':main()
