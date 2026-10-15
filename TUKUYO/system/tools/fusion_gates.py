#!/usr/bin/env python3
"""What the gates of v1022.7.7 hold back in generation 4 (the fusion v1022.7.7+gen4-r6). No parent is asked (cost 0);
only the dev splits are used.

  fusion_gates.py DATA_DIR --work WORK [--out REPORT.json]

  own       ASDiv dev, the child's own readings (api.solve, llm off): the answers with the input gate as it is now
            (event scope only, api._input_coverage(mine=True)), and with the full independent input audit of v1022.5.2
            on its own readings as well: what that would hold back, by reason, and whether it was right or wrong
  think     ASDiv dev: think against g4-solve, every problem where they differ, with think's reason (the parser B gate
            of v1022.7.7 holds back an answer that parser B decides otherwise)
  parents   the simulated parents of g4_measure.py (the same grid and seeds; the own reader switched off, so every reading
            is a parent's): what the independent input audit on parent-only readings holds back, by reason, and whether
            the answer without it would have been right or wrong

DATA_DIR is the folder written by g4_bench.py fetch. WORK holds a live individual (run_tukuyo.py --data WORK/v1022_individual init)
"""
from __future__ import annotations
import argparse,collections,copy,json,os,random,sys,tempfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE/'src'));sys.path.insert(0,str(HERE/'tools'))
from g4_bench import load,grade
import g4_measure as M
from tukuyo_g4 import api,llm

def _asdiv(data):return [it for it in load(data,'asdiv') if it['split']=='dev']

def m_own(data,work):
    real=api._input_coverage;seen={}
    def full(text,answer,proof=None,mine=False):
        r=real(text,answer,proof,mine=False);seen[text]=r;return r
    c=collections.Counter();why=collections.Counter();rows=[]
    try:
        for it in _asdiv(data):
            api._input_coverage=real;r=api.solve(it['text'],llm='off')
            seen.pop(it['text'],None);api._input_coverage=full;r1=api.solve(it['text'],llm='off')
            g,g1=grade(it,{'answer':r['answer']}),grade(it,{'answer':r1['answer']});c[(g,g1)]+=1
            if g!=g1:
                reason=(seen.get(it['text']) or {}).get('reason') or r1.get('reason');why[(reason,g)]+=1
                rows.append({'id':it['id'],'now':g,'with_the_full_audit':g1,'reason':reason,'text':it['text'][:160]})
    finally:api._input_coverage=real
    now=collections.Counter();full_=collections.Counter()
    for (a,b),n in c.items():now[a]+=n;full_[b]+=n
    return {'items':sum(c.values()),'now':dict(now),'with_the_full_audit_on_own_readings':dict(full_),
            'held_back_by_reason':{f'{k[0]}|{k[1]}':v for k,v in why.items()},'rows':rows}

def m_think(data,work):
    from tukuyo_v1022 import cognition as cog
    d=str(Path(work)/'v1022_individual');c=collections.Counter();rows=[]
    for it in _asdiv(data):
        g=api.solve(it['text'],llm='off');b=cog.solve(d,it['text']);th=api.think(d,it['text'],b,llm='off',learn=False)
        gg=grade(it,{'answer':g.get('answer')});tg=grade(it,{'answer':None if th.get('uncertain') else th.get('answer')});c[(gg,tg)]+=1
        if gg!=tg:rows.append({'id':it['id'],'g4_solve':gg,'think':tg,'think_reason':th.get('reason'),'text':it['text'][:160]})
    g4=collections.Counter();th=collections.Counter()
    for (a,b),n in c.items():g4[a]+=n;th[b]+=n
    return {'items':sum(c.values()),'g4_solve':dict(g4),'think':dict(th),'differ':rows}

def m_parents(data,work):
    V=M.verified(data);wrongs={}
    for text,sp,_ in V:
        ws=[s2 for s2 in M._op_variants(sp) if api.evaluate(s2,'w')['ok']]
        for q in sp['quantities']:
            if q['name']!=sp['ask']:
                s2=copy.deepcopy(sp);s2['ask']=q['name']
                if api.evaluate(s2,'w')['ok']:ws.append(s2)
        wrongs[text]=ws
    def reply(sp):return {'readable':True,'quantities':sp['quantities'],'facts':[{'eq':f['eq'],'span':f.get('span',''),'known':f.get('known','')} for f in sp['facts']],
                          'ask':sp['ask'],'answer_unit':sp.get('answer_unit',''),'unused':sp.get('unused') or []}
    real=api._input_coverage;seen={}
    def spy(text,answer,proof=None,mine=False):
        r=real(text,answer,proof,mine=mine);seen[text]=r;return r
    def none(text,answer,proof=None,mine=False):return {'recognized':False,'ok':True}
    saved={k:os.environ.get(k) for k in ('TUKUYO_LLM_REPLAY','TUKUYO_LLM_PARENTS')};own=api._own;api._own=lambda text:None
    os.environ.pop('TUKUYO_LLM_PARENTS',None);grid=[];why=collections.Counter()
    try:
        for parents in (('claude',),('claude','gemini'),('claude','chatgpt','gemini')):
            for p in (0.1,0.3):
                for rho in (0.0,0.5,1.0):
                    r2=random.Random(1);lines=[]
                    for text,sp,_ in V:
                        ws=wrongs[text];shared=r2.choice(ws) if ws else None
                        for par in parents:
                            for view in ('story','goal'):
                                o=(shared if r2.random()<rho else r2.choice(ws)) if ws and r2.random()<p else sp
                                h=llm.request_hash(llm._kind(par,'read:'+view+':'+llm.PROMPT_VERSION),llm.system_prompt(view),'Text: '+text)
                                lines.append(json.dumps({'parent':par,'hash':h,'ok':True,'text':json.dumps(reply(o),ensure_ascii=False),'model':'sim'},ensure_ascii=False))
                    with tempfile.NamedTemporaryFile('w',suffix='.jsonl',delete=False,encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
                    os.environ['TUKUYO_LLM_REPLAY']=f.name;llm._replay_cache.clear();c=collections.Counter()
                    g=lambda x,ans:'abstain' if x['answer'] is None else ('correct' if x['value']==api.fmt(ans) else 'wrong')
                    for text,sp,ans in V:
                        seen.pop(text,None);api._input_coverage=spy;r=api.solve(text,llm='on');cov=seen.get(text)
                        api._input_coverage=none;r0=api.solve(text,llm='on');a,a0=g(r,ans),g(r0,ans);c[(a0,a)]+=1
                        if a0!=a:why[((cov or {}).get('reason') or r.get('reason'),a0)]+=1
                    os.unlink(f.name)
                    grid.append({'parents':len(parents),'p_wrong':p,'rho':rho,'without_the_audit_to_with':{f'{k[0]}->{k[1]}':v for k,v in sorted(c.items())}})
    finally:
        api._input_coverage=real;api._own=own;llm._replay_cache.clear()
        for k,v in saved.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v
    return {'items':len(V),'settings':len(grid),'note':'simulated parents: wrong readings are operator or asked-quantity changes that pass the checker',
            'held_back_by_reason':{f'{k[0]}|{k[1]}':v for k,v in sorted(why.items())},'grid':grid}

MEASURES={'own':m_own,'think':m_think,'parents':m_parents}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('data');ap.add_argument('--work',required=True);ap.add_argument('--only');ap.add_argument('--out')
    a=ap.parse_args();out={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    for k in (a.only.split(',') if a.only else MEASURES):
        t=time.time();out[k]=MEASURES[k](a.data,a.work);out[k]['seconds']=round(time.time()-t,1)
        print(k,'done in',out[k]['seconds'],'s',flush=True)
    s=json.dumps(out,ensure_ascii=False,indent=1)
    if a.out:Path(a.out).write_text(s+'\n',encoding='utf-8')
    else:print(s)

if __name__=='__main__':main()
