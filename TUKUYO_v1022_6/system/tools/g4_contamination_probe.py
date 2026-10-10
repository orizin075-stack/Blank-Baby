#!/usr/bin/env python3
"""Have the parents seen the benchmark? A probe for data contamination of the parents (Claude, ChatGPT, Gemini) on the
third-party problem sets, and a check that the locked test split does not leak into what the child learns. Dev split
only for the parents; the test split is never sent anywhere.

  g4_contamination_probe.py DATA [--items N] [--parents claude,gemini] [--allow-paid] [--out REPORT.json]
  g4_contamination_probe.py DATA --simulate [--items N]          the probe itself, offline (no parent is asked)
  g4_contamination_probe.py DATA --split-overlap [--stores DIR ...]   counts only

  changed numbers  for dev problems TUKUYO's own reader reads and the checker accepts, a variant with other numbers is
                   made from the same reading (learn.template), its answer computed exactly. A parent that reads the
                   original right far more often than the variant (b = right only on the original, c = right only on
                   the variant; exact binomial test of b against c) may be answering from memory of the problem
  completion       the parent is given the first half of a problem and asked to continue it; the share of the true
                   second half's 8-character pieces in its continuation (1.0: word for word)
  split overlap    how many test problems have the wording of a dev problem apart from its numbers (a template learned
                   on dev would read them), and how many templates in the given stores were learned from a test problem
Without --allow-paid (or TUKUYO_LLM_REPLAY) no parent is asked: the probe says how many calls it would make. A probe of a
probe: --simulate runs it with two made-up parents through the replay path, one that answers from memory and one that
reads, to show that it tells them apart; it measures no real model.
"""
from __future__ import annotations
import argparse,json,math,os,random,re,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE/'src'));sys.path.insert(0,str(HERE/'tools'))
from g4_bench import load
from tukuyo_g4 import api,llm,reader
from tukuyo_g4.learn import instantiate,skeleton,template

COMPLETE_SYSTEM='Continue the text exactly as it goes on. Reply with the continuation only.'

def verified_items(data,n,seed):
    """dev problems its own reader reads with a reading the checker accepts: (item, spec, answer)"""
    items=[it for it in load(data,'asdiv') if it['split']=='dev']
    random.Random(seed).shuffle(items);out=[]
    for it in items:
        rd=reader.read(it['text'])
        if not rd.get('spec'):continue
        e=api.evaluate(rd['spec'],'own')
        if e['ok']:out.append((it,rd['spec'],e['answer']))
        if len(out)>=n:break
    return out

def variant(text,spec,answer,rng,tries=40):
    """the same problem with other numbers, and its answer from the same reading; None when no variant reads well"""
    t=template(spec)
    if not t:return None
    key,tt,nums,_=skeleton(text)
    for _ in range(tries):
        parts=[];pos=0
        for n in nums:
            parts.append(tt[pos:n.start]);pos=n.end
            v=n.value
            if n.kind not in ('digits','word') or v.denominator!=1 or v<=1:parts.append(n.raw);continue
            nv=int(v)+rng.choice((-2,-1,1,2,3))*max(1,int(v)//4)
            parts.append(str(max(2,nv)))
        parts.append(tt[pos:]);new=''.join(parts)
        if new==tt:continue
        s2=instantiate(t,new)
        if not s2:continue
        e=api.evaluate(s2,'variant')
        if e['ok'] and e['answer']!=answer and e['answer']>0 and (answer.denominator!=1 or e['answer'].denominator==1):
            return new,e['answer']
    return None

def binom_p(b,c):
    """two-sided exact binomial test of b successes in b + c at 1/2"""
    n=b+c
    if n==0:return 1.0
    k=min(b,c);tail=sum(math.comb(n,i) for i in range(k+1))/2**n
    return min(1.0,2*tail)

def overlap(truth,said,k=8):
    a=re.sub(r'\s+',' ',truth.lower()).strip();b=re.sub(r'\s+',' ',said.lower()).strip()
    grams={a[i:i+k] for i in range(max(0,len(a)-k+1))}
    return sum(1 for g in grams if g in b)/len(grams) if grams else 0.0

def probe(pairs,parents):
    """pairs: [(original text, answer, variant text, answer)]. Asks each parent; returns the measures per parent"""
    rep={}
    for p in parents:
        b=c=both=none=0;ov=[]
        for t0,a0,t1,a1 in pairs:
            def right(t,a):
                r=llm.read(t,'story',parent=p)
                if not r.get('ok'):return False
                e=api.evaluate(r['spec'],'probe');return bool(e['ok'] and e['answer']==a)
            r0,r1=right(t0,a0),right(t1,a1)
            if r0 and not r1:b+=1
            elif r1 and not r0:c+=1
            elif r0:both+=1
            else:none+=1
            half=len(t0)//2;cut=t0.rfind(' ',0,half) if t0.rfind(' ',0,half)>0 else half
            got=llm.call('probe:complete:1',COMPLETE_SYSTEM,t0[:cut],max_tokens=400,parent=p)
            ov.append(overlap(t0[cut:],got.get('text') or '') if got.get('ok') else None)
        n=len(pairs);ok=[x for x in ov if x is not None]
        rep[p]={'problems':n,'right_on_original':both+b,'right_on_variant':both+c,'right_only_on_original':b,'right_only_on_variant':c,
                'p_value':round(binom_p(b,c),6),'completion_overlap_mean':round(sum(ok)/len(ok),3) if ok else None,
                'completions_over_half':sum(1 for x in ok if x>0.5),'completions_answered':len(ok),
                'signs_of_memory':(b>c and binom_p(b,c)<0.01) or (bool(ok) and sum(1 for x in ok if x>0.5)>len(ok)/4)}
    return rep

def simulate(pairs,work):
    """two made-up parents through the replay path: 'claude' answers from memory (right on the originals it has seen,
    the original reading on a variant, the text word for word); 'gemini' reads (right on both, no recall of the text)"""
    lines=[]
    def read_line(parent,text,spec):
        o={'readable':True,'quantities':spec['quantities'],'facts':[{'eq':f['eq'],'span':f.get('span',''),'known':f.get('known','')} for f in spec['facts']],
           'ask':spec['ask'],'answer_unit':spec.get('answer_unit',''),'unused':spec.get('unused') or []}
        return {'parent':parent,'hash':llm.request_hash(llm._kind(parent,'read:story:'+llm.PROMPT_VERSION),llm.system_prompt('story'),'Text: '+text),
                'ok':True,'text':json.dumps(o,ensure_ascii=False),'model':'simulated-'+parent}
    for t0,a0,t1,a1,s0,s1 in pairs:
        lines+=[read_line('claude',t0,s0),read_line('claude',t1,s0),read_line('gemini',t0,s0),read_line('gemini',t1,s1)]
        half=len(t0)//2;cut=t0.rfind(' ',0,half) if t0.rfind(' ',0,half)>0 else half
        for p,txt in (('claude',t0[cut:]),('gemini','and then the story goes on in some other way entirely.')):
            lines.append({'parent':p,'hash':llm.request_hash(llm._kind(p,'probe:complete:1'),COMPLETE_SYSTEM,t0[:cut]),'ok':True,'text':txt,'model':'simulated-'+p})
    f=Path(work)/'simulated_parents.jsonl';f.write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in lines)+'\n',encoding='utf-8')
    os.environ['TUKUYO_LLM_REPLAY']=str(f);llm._replay_cache.clear()
    return probe([x[:4] for x in pairs],['claude','gemini'])

def split_overlap(data,stores):
    sets={}
    for name in ('asdiv','svamp','mgsm_ja'):
        try:sets[name]=load(data,name)
        except Exception:continue  # noqa: BLE001 - a set that was not fetched
    out={};test_keys=set()
    for name,items in sets.items():
        dev={skeleton(it['text'])[0] for it in items if it['split']=='dev'}
        test=[skeleton(it['text'])[0] for it in items if it['split']=='test'];test_keys|=set(test)
        out[name]={'dev':len(items)-len(test),'test':len(test),'test_with_a_dev_wording':sum(1 for k in test if k in dev)}
    st={}
    for d in stores or []:
        p=Path(d)/'g4'/'learned.json'
        ts=json.loads(p.read_text(encoding='utf-8')).get('templates',{}) if p.is_file() else {}
        st[str(d)]={'templates':len(ts),'from_a_test_problem':sum(1 for t in ts.values() if skeleton(t.get('example',''))[0] in test_keys)}
    return {'sets':out,'stores':st,'note':'counts only; no test problem is shown or sent anywhere'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('data');ap.add_argument('--items',type=int,default=50);ap.add_argument('--parents')
    ap.add_argument('--allow-paid',action='store_true');ap.add_argument('--simulate',action='store_true');ap.add_argument('--split-overlap',action='store_true')
    ap.add_argument('--stores',nargs='*');ap.add_argument('--seed',type=int,default=20261010);ap.add_argument('--out');a=ap.parse_args()
    if a.split_overlap:rep={'split_overlap':split_overlap(a.data,a.stores)}
    else:
        rng=random.Random(a.seed);pairs=[]
        for it,spec,ans in verified_items(a.data,a.items*3,a.seed):
            v=variant(it['text'],spec,ans,rng)
            if v:
                s1=instantiate(template(spec),v[0])
                pairs.append((it['text'],ans,v[0],v[1],spec,s1))
            if len(pairs)>=a.items:break
        if a.simulate:
            for k in [k for k in os.environ if k.startswith(('TUKUYO_ANTHROPIC','TUKUYO_OPENAI','TUKUYO_GEMINI','TUKUYO_LLM'))]:del os.environ[k]
            rep={'simulated':True,'note':'made-up parents: this tests the probe, it measures no real model','pairs':len(pairs),
                 'parents':simulate(pairs,tempfile.mkdtemp(prefix='g4_probe_'))}
        else:
            ps=[x for x in (a.parents.split(',') if a.parents else llm.parents()) if x]
            calls=len(pairs)*3*len(ps)
            if not ps:raise SystemExit('no parent is configured (see g4-parents)')
            if not (a.allow_paid or os.environ.get('TUKUYO_LLM_REPLAY')):
                rep={'would_ask':ps,'pairs':len(pairs),'calls':calls,'note':'no parent was asked: pass --allow-paid after agreeing on the cost'}
            else:rep={'pairs':len(pairs),'calls':calls,'parents':probe([x[:4] for x in pairs],ps)}
    s=json.dumps(rep,ensure_ascii=False,indent=1)
    if a.out:Path(a.out).write_text(s,encoding='utf-8')
    print(s)

if __name__=='__main__':main()
