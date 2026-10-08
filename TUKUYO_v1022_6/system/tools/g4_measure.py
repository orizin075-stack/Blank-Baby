#!/usr/bin/env python3
"""Measure generation 4 without calling any parent (no API key, no cost). Only the dev splits are used.

  g4_measure.py DATA_DIR [--work WORK] [--only fuzz,specs,mutate,parents,learn,accuracy] [--out REPORT.json]

  fuzz      every entry point (numbers, forms, reader, solve, ask; with --work also the v1022 core and think) on the dev
            texts, 3000 mutated texts and odd inputs: nothing may raise
  specs     solve + check on 6000 malformed readings, as a parent might return them: nothing may raise
  mutate    the checker against the own reader's verified readings broken in nine known ways: how many are caught
  parents   simulated parents (1, 2, 3) that return the true reading or, with probability p, a wrong one the checker
            cannot catch; rho is the chance that a wrong reading repeats the shared mistake: how often a wrong answer
            is committed. This measures the arbitration code end to end through the replay path, not real models
  learn     templates learned from verified readings, used on the same wording with other numbers: they must agree
            with the own reader or abstain
  accuracy  ASDiv and MGSM-ja dev: the v1022 core, generation 4 alone and think (needs --work), with latencies
DATA_DIR is the folder written by g4_bench.py fetch. WORK holds a live individual (run_tukuyo.py --data WORK/v1022_individual init).
"""
from __future__ import annotations
import argparse,collections,copy,json,os,random,re,statistics,sys,tempfile,time,traceback
from fractions import Fraction
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE/'src'));sys.path.insert(0,str(HERE/'tools'))
from g4_bench import load,grade
from tukuyo_g4 import api,check as C,forms_en,learn,llm,numbers as N,reader

def dev(data,sets=('asdiv','mgsm_ja')):return [it for s in sets for it in load(data,s) if it['split']=='dev']

def verified(data):
    out=[]
    for it in dev(data,('asdiv',)):
        r=reader.read(it['text'])
        if r.get('spec'):
            e=api.evaluate(r['spec'],'own')
            if e['ok']:out.append((it['text'],r['spec'],e['answer']))
    return out

WEIRD=['','?','.','   ','How many?','What is the number?','0','1/0','How many apples? '*50,'A'*5000,'1'*500,'Ten. Twenty. How many?',
       'There are -5 apples. How many apples are there?','What is the greatest common factor of 0 and 0?','A car travels 0 km in 0 hours. What is its speed?',
       'If I divide it by 0, I get 9. What is the number?','Half of a number is 0. What is the number?','りんごが？個あります。','１２＋３４は？',
       '\x00\x01\x02','Tom has 3 apples.'*200+' How many apples does Tom have?','((((((((((','Ted has 9 pens. He puts them into 0 boxes equally. How many pens are in each box?']

def m_fuzz(data,work,rnd):
    base=[it['text'] for it in dev(data)]
    def mutate(t):
        k=rnd.randrange(10)
        if k==0:return re.sub(r'\d+',lambda m:str(rnd.choice([0,1,7,10**9])),t)
        if k==1:return re.sub(r'\d+',lambda m:rnd.choice(['1.5','2/3','-4','1,000','0.0','３']),t)
        if k==2:return t.upper()
        if k==3:return re.sub(r'[.?!。？]','',t)
        if k==4:return t+' '+t
        if k==5:return t[:rnd.randrange(1,max(2,len(t)))]
        if k==6:return ''.join(c for c in t if rnd.random()>0.05)
        if k==7:return t.replace(' ','  ').replace('.',' . ')
        if k==8:return '"'+t+'" ('+t[:20]+')'
        return t+' What is 3 + 4?'
    texts=base+[mutate(rnd.choice(base)) for _ in range(3000)]+WEIRD
    calls=[('numbers',N.find),('forms',forms_en.read),('reader',reader.read),('solve',lambda x:api.solve(x,llm='off')),('ask',lambda x:api.ask(x,llm='off'))]
    if work:
        from tukuyo_v1022 import cognition
        d=str(Path(work)/'v1022_individual')
        calls.append(('think',lambda x:api.think(d,x,cognition.solve(d,x),llm='off',learn=False)))
    crash=collections.Counter();ex={};t0=time.time()
    for t in texts:
        for name,f in calls:
            try:f(t)
            except Exception as e:  # noqa: BLE001 - counting faults is the point
                k=f'{name}:{type(e).__name__}';crash[k]+=1;ex.setdefault(k,[t[:200],traceback.format_exc()[-600:]])
    return {'texts':len(texts),'entry_points':[n for n,_ in calls],'crashes':sum(crash.values()),'by_kind':dict(crash),'examples':ex,'seconds':round(time.time()-t0,1)}

ATOMS=['x','y','1','0','100','99999999999999999999','-','+','*','/','(',')',',','floor(','gcd(','mod(','sqrt(','__import__("os")','é','=','1/0','((((((','1.5','.','inf',' ','"','\\']
def m_specs(data,work,rnd):
    seeds=[(t,o) for exs in llm.EXAMPLES.values() for t,o in exs]
    def junk():return ''.join(rnd.choice(ATOMS) for _ in range(rnd.randrange(1,14)))
    def mutate(o,text):
        o=copy.deepcopy(o);k=rnd.randrange(12)
        if k==0 and o['facts']:rnd.choice(o['facts'])['eq']=junk()
        elif k==1 and o['facts']:f=rnd.choice(o['facts']);f['eq']=f['eq'].split('=')[0]+'= '+junk()
        elif k==2 and o['quantities']:rnd.choice(o['quantities'])['unit']=rnd.choice(['','%','km/hour/hour','x^999','^','/','()'])
        elif k==3:o['ask']=rnd.choice(['','nope','x;y','__class__'])
        elif k==4:o['facts']=[]
        elif k==5:o['quantities']=[]
        elif k==6 and o['facts']:rnd.choice(o['facts'])['span']=rnd.choice(['','x'*5000,text[::-1]])
        elif k==7 and o['facts']:rnd.choice(o['facts'])['eq']='x = '+'('*400+'1'+')'*400
        elif k==8 and o['facts']:rnd.choice(o['facts'])['eq']='x = 2'+' * 2'*3000
        elif k==9:o['unused']=[{'raw':rnd.choice(['','1','999','abc']),'why':rnd.choice(['','because'])}]
        elif k==10 and o['quantities']:rnd.choice(o['quantities'])['name']=rnd.choice(['','1x','a b','é','x'*300])
        else:
            for q in o['quantities']:q['integer']=rnd.choice([True,False]);q['signed']=rnd.choice([True,False])
        return o
    crash=collections.Counter();t0=time.time();n=6000
    for _ in range(n):
        t,o=rnd.choice(seeds);o=mutate(o,t)
        spec={'schema':'tukuyo.g4.fpl/1','lang':'x','text':t,'quantities':o['quantities'],'ask':o['ask'],'answer_unit':'','unused':o.get('unused') or [],
              'facts':[{'eq':f['eq'],**({'span':f['span']} if f.get('span') else {}),**({'known':f['known']} if f.get('known') else {})} for f in o['facts']]}
        try:api.evaluate(spec,'fuzz')
        except Exception as e:crash[type(e).__name__]+=1  # noqa: BLE001
    return {'readings':n,'crashes':sum(crash.values()),'by_kind':dict(crash),'seconds':round(time.time()-t0,1)}

BIND=re.compile(r'\s*\w+\s*=\s*[\d/]+\s*')
def _binds(sp):return [i for i,f in enumerate(sp['facts']) if BIND.fullmatch(f['eq']) and f.get('span')]
def _rels(sp):return [i for i,f in enumerate(sp['facts']) if f.get('span') and not BIND.fullmatch(f['eq'])]
def _op_variants(sp):
    out=[]
    for i in _rels(sp):
        l,r=sp['facts'][i]['eq'].split('=')
        for m in re.finditer(r'[-+*/]',r):
            s2=copy.deepcopy(sp);s2['facts'][i]['eq']=l+'='+r[:m.start()]+{'+':'-','-':'+','*':'+','/':'*'}[m.group()]+r[m.end():];out.append(s2)
    return out
def m_mutate(data,work,rnd):
    V=verified(data)
    def number(sp):i=rnd.choice(_binds(sp));n,v=sp['facts'][i]['eq'].split('=');sp['facts'][i]['eq']=f'{n}= {Fraction(v.strip())+7}'
    def span(sp):i=rnd.choice(_binds(sp)+_rels(sp));sp['facts'][i]['span']+=' and then some'
    def literal(sp):i=rnd.choice(_rels(sp));sp['facts'][i]['eq']+=' + 3'
    def drop(sp):del sp['facts'][rnd.choice(_binds(sp))]
    def unit(sp):q=rnd.choice(sp['quantities']);q['unit']=q['unit']+'_x' if q['unit'] not in ('','1','%') else 'banana'
    def contradiction(sp):a=sp['quantities'][0]['name'];sp['facts'].append({'eq':f'{a} = {a} + 1','span':sp['facts'][_rels(sp)[0]]['span']})
    def unused_instead(sp):i=rnd.choice(_binds(sp));raw=sp['facts'][i]['eq'].split('=')[1].strip();del sp['facts'][i];sp['unused'].append({'raw':raw,'why':'x'})
    def operator(sp):
        vs=_op_variants(sp)
        if not vs:raise IndexError
        sp.clear();sp.update(rnd.choice(vs))
    def ask(sp):
        o=[q['name'] for q in sp['quantities'] if q['name']!=sp['ask']]
        if not o:raise IndexError
        sp['ask']=rnd.choice(o)
    out={}
    for name,m in (('number_not_in_text',number),('span_not_in_text',span),('number_in_relation',literal),('binding_dropped',drop),('unit_changed',unit),
                   ('contradiction_added',contradiction),('number_declared_unused',unused_instead),('operator_changed',operator),('other_quantity_asked',ask)):
        c=collections.Counter()
        for _,sp,ans in V:
            s2=copy.deepcopy(sp)
            try:m(s2)
            except IndexError:continue
            e=api.evaluate(s2,'mut')
            c['caught' if not e['ok'] else ('passed_same_answer' if e['answer']==ans else 'passed_other_answer')]+=1
        out[name]={'n':sum(c.values()),**{k:c[k] for k in ('caught','passed_same_answer','passed_other_answer')},'caught_pct':round(100*c['caught']/max(1,sum(c.values())),1)}
    return {'readings':len(V),'mutations':out}

def m_parents(data,work,rnd):
    V=verified(data);wrongs={}
    for text,sp,_ in V:
        ws=[s2 for s2 in _op_variants(sp) if api.evaluate(s2,'w')['ok']]
        for q in sp['quantities']:
            if q['name']!=sp['ask']:
                s2=copy.deepcopy(sp);s2['ask']=q['name']
                if api.evaluate(s2,'w')['ok']:ws.append(s2)
        wrongs[text]=ws
    def reply(sp):return {'readable':True,'quantities':sp['quantities'],'facts':[{'eq':f['eq'],'span':f.get('span',''),'known':f.get('known','')} for f in sp['facts']],
                          'ask':sp['ask'],'answer_unit':sp.get('answer_unit',''),'unused':sp.get('unused') or []}
    saved={k:os.environ.get(k) for k in ('TUKUYO_LLM_REPLAY','TUKUYO_LLM_PARENTS')};own=api._own;api._own=lambda text:None
    os.environ.pop('TUKUYO_LLM_PARENTS',None);out=[]
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
                    for text,sp,ans in V:
                        r=api.solve(text,llm='on')
                        c['abstain' if r['answer'] is None else ('correct' if r['value']==api.fmt(ans) else 'wrong')]+=1
                    os.unlink(f.name)
                    out.append({'parents':len(parents),'p_wrong':p,'rho':rho,**c,'committed_wrong_pct':round(100*c['wrong']/len(V),1)})
    finally:
        api._own=own;llm._replay_cache.clear()
        for k,v in saved.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v
    return {'items':len(V),'note':'simulated parents: wrong readings are operator or asked-quantity changes that pass the checker','grid':out}

def m_learn(data,work,rnd):
    V=verified(data);d=Path(tempfile.mkdtemp());st=learn.Store(d/'g4')
    for _,sp,_ in V:st.add(sp,{'route':'measure'})
    c=collections.Counter();bad=[]
    def variant(t):
        def rep(m):
            v=int(m.group())
            return str(max(1,v+rnd.choice([-3,-2,-1,1,2,3,5,10]) if v<20 else v*rnd.choice([2,3])//rnd.choice([1,2])+rnd.randrange(0,5)))
        return re.sub(r'(?<![\d.,/])\d{1,4}(?![\d.,/])',rep,t)
    for text,_,_ in V:
        for _ in range(3):
            v=variant(text)
            if v==text:continue
            tp=st.find(v)
            if not tp:c['no_template']+=1;continue
            spec=learn.instantiate(tp,v)
            if not spec:c['no_instance']+=1;continue
            e=api.evaluate(spec,'learned');own=reader.read(v)
            oe=api.evaluate(own['spec'],'own') if own.get('spec') else None
            ref=oe['value'] if oe and oe['ok'] else None
            if not e['ok']:c['template_abstains']+=1
            elif ref is None:c['template_only']+=1
            elif e['value']==ref:c['agree_with_own_reader']+=1
            else:c['disagree_with_own_reader']+=1;bad.append([v[:200],e['value'],ref])
    return {'templates':len(st.load()['templates']),'from_readings':len(V),'audit_ok':st.audit().get('ok'),**c,'disagreements':bad[:10]}

def m_accuracy(data,work,rnd):
    out={}
    cog=None
    if work:
        from tukuyo_v1022 import cognition as cog
        d=str(Path(work)/'v1022_individual')
    for s in ('asdiv','mgsm_ja'):
        items=dev(data,(s,));c=collections.defaultdict(collections.Counter);ts=collections.defaultdict(list)
        for it in items:
            t0=time.perf_counter();g=api.solve(it['text'],llm='off');t1=time.perf_counter();ts['g4_solve'].append(t1-t0)
            c['g4_solve'][grade(it,{'answer':g.get('answer')})]+=1
            if cog:
                a=time.perf_counter();b=cog.solve(d,it['text']);bb=time.perf_counter()
                th=api.think(d,it['text'],b,llm='off',learn=False);tt=time.perf_counter()
                ts['v1022'].append(bb-a);ts['think'].append(tt-a)
                c['v1022'][grade(it,{'answer':None if b.get('uncertain') else b.get('answer')})]+=1
                c['think'][grade(it,{'answer':None if th.get('uncertain') else th.get('answer')})]+=1
        out[s]={'items':len(items),**{k:dict(v) for k,v in c.items()},
                'ms':{k:{'median':round(1000*statistics.median(v),2),'p95':round(1000*sorted(v)[max(0,int(.95*len(v))-1)],2)} for k,v in ts.items()}}
    return out

MEASURES={'fuzz':m_fuzz,'specs':m_specs,'mutate':m_mutate,'parents':m_parents,'learn':m_learn,'accuracy':m_accuracy}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('data');ap.add_argument('--work');ap.add_argument('--only');ap.add_argument('--out');ap.add_argument('--seed',type=int,default=20261008)
    a=ap.parse_args()
    for k in [k for k in os.environ if k.startswith(('TUKUYO_ANTHROPIC','TUKUYO_OPENAI','TUKUYO_GEMINI'))]:os.environ.pop(k)   # never a real call
    names=a.only.split(',') if a.only else list(MEASURES)
    rep={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'seed':a.seed,'note':'no parent is called; dev splits only'}
    for n in names:
        t0=time.time();rep[n]=MEASURES[n](a.data,a.work,random.Random(a.seed));rep[n]['seconds_total']=round(time.time()-t0,1)
        print(f'{n}: done in {rep[n]["seconds_total"]} s',file=sys.stderr)
    s=json.dumps(rep,ensure_ascii=False,indent=1,default=str)
    if a.out:Path(a.out).write_text(s,encoding='utf-8')
    print(s)

if __name__=='__main__':main()
