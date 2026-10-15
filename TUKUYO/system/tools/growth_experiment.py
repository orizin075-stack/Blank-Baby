#!/usr/bin/env python3
"""Trial experiments: does generation 4 notice its own growth in conditions it was not built on? Offline: the parents are
recorded replies; no API key, no cost. ASDiv dev only (the test split is never read).

  growth_experiment.py DATA_DIR --before-src SRC --runtime-trust-file ANCHOR [--work DIR] [--out REPORT.json]
                       [--only upgrade,taught,mistaught] [--seed N]

SRC is the src folder of an earlier version of the child (for example the commit before this round: git archive). Its
reader files (reader.py, reader_en.py, numbers.py, forms_*.py) are put in place of this version's; everything else
(the soul, the heart, the stores, growth.py, voice.py) is this version. So a child can live with the reader it had then.

  upgrade    a child with the earlier reader meets every ASDiv dev problem alone, in a shuffled order. Then it becomes
             this version (the same individual, this version's command line), looks at what it could not read
             (g4-reflect) and tries again alone (g4-reflect --act). How many of the problems it could not read does it
             notice it can now read; are those answers right (the answer key); does it notice any it reads wrongly; how
             many could it have noticed (this version reads them) and did not, and why; what is left of its weak spots
  taught     a child with the earlier reader meets, alone, problems it cannot read: for each dev problem this version
             reads rightly and the earlier one does not, the same problem with its numbers doubled. Its three parents
             (recorded replies: this version's own reading of the original problem, the same from each) then teach it
             the original. Does it notice that it can read the problem it met; does it answer it alone, and does that
             answer agree with this version's own reading of it
  mistaught  its parents agree on a reading that is wrong but passes the checker (a sign turned round), for two
             wordings it cannot read. It notices a growth that is not real and answers wrongly. Later two parents read
             another problem of the wording otherwise, and later still its parents teach the wording again. What does it
             say of its growth at each step
A functional experiment on a functional model: it says nothing about consciousness or feeling.
"""
from __future__ import annotations
import argparse,hashlib,json,os,random,re,shutil,subprocess,sys,tempfile,time
from fractions import Fraction
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE/'src'));sys.path.insert(0,str(HERE/'tools'))
from g4_bench import load,grade
from tukuyo_g4 import api,growth,learn,llm,reader,numbers as N

READER_FILES=('reader.py','reader_en.py','numbers.py','forms_en.py','forms_more_en.py','forms_algebra_en.py')
PARENTS=('claude','chatgpt','gemini')
CLEAN=('TUKUYO_ANTHROPIC','TUKUYO_OPENAI','TUKUYO_GEMINI','TUKUYO_LLM','TUKUYO_CRASH')

# ----------------------------------------------------------------------------- the child: its command line, and a process
class CLI:
    """this version's command line (run_tukuyo.py), with no parent configured unless a recording is given"""
    def __init__(s,anchor):
        s.cmd=[sys.executable,'-B',str(HERE/'run_tukuyo.py')]+(['--runtime-trust-file',str(anchor)] if anchor else [])
        s.env={k:v for k,v in os.environ.items() if not k.startswith(CLEAN)};s.env['PYTHONDONTWRITEBYTECODE']='1'
    def __call__(s,d,*a,replay=None):
        e=dict(s.env)
        if replay:e['TUKUYO_LLM_REPLAY']=str(replay)
        p=subprocess.run(s.cmd+['--data',str(d),*map(str,a)],cwd=HERE,env=e,capture_output=True,text=True,timeout=1800)
        try:return json.loads(p.stdout)
        except ValueError:return {'ok':False,'cli_error':(p.stderr or p.stdout)[-600:]}

WORKER=r'''
import json,sys
hybrid,src,jobf=sys.argv[1:4];job=json.load(open(jobf,encoding='utf-8'))
sys.path[:0]=[x for x in (hybrid,src) if x]
from tukuyo_g4 import api,life,voice
d=job.get('data');out=[]
for t in job['texts']:
    r=api.solve(t,llm=job['llm'],data=d,learn=job.get('learn',True))
    v=voice.explain(t,r,d) if job.get('voice') else {}
    lv=life.record(d,r,t) if d else None
    out.append({'text':t,'answer':r.get('answer'),'route':r.get('route'),'reason':r.get('reason'),'learned':r.get('learned'),
                'life':lv,'before':v.get('before'),'said':v.get('said')})
if d:
    from tukuyo_v977.whole_state import sync
    sync(d)
json.dump(out,open(job['out'],'w',encoding='utf-8'),ensure_ascii=False)
'''
def worker(work,texts,earlier,data=None,llm_mode='off',learn=True,voice=False,replay=None,tag='job'):
    """the child's thinking in one process: with the earlier reader (earlier=True) or this version's; with data, each
    thought is lived (life.record), as g4-solve does"""
    jobf=Path(work)/f'{tag}.json';outf=Path(work)/f'{tag}.out.json'
    jobf.write_text(json.dumps({'texts':texts,'llm':llm_mode,'data':str(data) if data else None,'learn':learn,'voice':voice,'out':str(outf)}),encoding='utf-8')
    env={k:v for k,v in os.environ.items() if not k.startswith(CLEAN)};env['PYTHONDONTWRITEBYTECODE']='1'
    if replay:env['TUKUYO_LLM_REPLAY']=str(replay)
    hybrid=str(Path(work)/'earlier') if earlier else ''
    p=subprocess.run([sys.executable,'-B','-c',WORKER,hybrid,str(HERE/'src'),str(jobf)],cwd=str(work),env=env,capture_output=True,text=True,timeout=7200)
    if p.returncode!=0:raise RuntimeError('worker failed: '+p.stderr[-1500:])
    return json.loads(outf.read_text(encoding='utf-8'))

def earlier_child(work,before_src):
    """this version's tukuyo_g4 with the reader files of the earlier version"""
    dst=Path(work)/'earlier'/'tukuyo_g4'
    if dst.exists():return
    shutil.copytree(HERE/'src'/'tukuyo_g4',dst,ignore=shutil.ignore_patterns('__pycache__'))
    for f in READER_FILES:
        src=Path(before_src)/'tukuyo_g4'/f
        if src.is_file():shutil.copy(src,dst/f)

def new_child(cli,d,name):
    r=cli(d,'init','--individual-id','GROWTH-EXP-'+name.upper())
    if not (Path(d)/'state'/'integration_state.json').is_file():raise RuntimeError('init failed: '+json.dumps(r)[:400])

def audits(cli,d):
    out={}
    for c in ('whole-audit','heart-audit','soul-identity-audit','g4-audit'):
        r=cli(d,c);out[c]={'ok':bool(r.get('ok')),'errors':(r.get('errors') or ([r['cli_error']] if r.get('cli_error') else []))[:4]}
    return out

def g4_events(d):
    p=Path(d)/'v977'/'SOUL_EVENTS.jsonl'
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if '"g4:' in x] if p.is_file() else []
def values(d):
    p=Path(d)/'v977'/'SOUL_CORE.json';return json.loads(p.read_text(encoding='utf-8')).get('core_values') if p.is_file() else None
def norm(t):return ' '.join(str(t).split())

def _reading(spec):
    """this version's own reading of a problem, as a parent would send it"""
    return {'readable':True,'quantities':spec['quantities'],'facts':[{'eq':f['eq'],'span':f.get('span',''),'known':f.get('known','')} for f in spec['facts']],
            'ask':spec['ask'],'answer_unit':spec.get('answer_unit',''),'unused':spec.get('unused') or []}
def _line(parent,text,o):
    return json.dumps({'parent':parent,'hash':llm.request_hash(llm._kind(parent,'read:story:'+llm.PROMPT_VERSION),llm.system_prompt('story'),'Text: '+text),
                       'ok':True,'text':json.dumps(o,ensure_ascii=False),'model':'recorded-'+parent},ensure_ascii=False)

def doubled(text):
    """the problem with each number written in digits doubled (a percent too); None when it has none"""
    out=text;changed=False
    for n in sorted(N.find(text),key=lambda n:-n.start):
        if n.kind not in ('digits','percent') or n.value!=int(n.value) or n.value<=0:continue
        m=re.search(r'\d[\d,]*',n.raw)
        if not m:continue
        new=n.raw[:m.start()]+str(int(n.value)*2)+n.raw[m.end():]
        out=out[:n.start]+new+out[n.end:];changed=True
    return out if changed else None

# ----------------------------------------------------------------------------- upgrade
def x_upgrade(ctx):
    cli,work,items=ctx['cli'],ctx['work'],ctx['items'];d=work/'upgrade';new_child(cli,d,'upgrade')
    gold={norm(it['text']):it for it in items}
    t0=time.time();lived=worker(work,[it['text'] for it in items],True,data=d,tag='upgrade_life')
    t_life=time.time()-t0
    graded=[grade(gold[norm(r['text'])],{'answer':r['answer']}) for r in lived]
    then={'right':graded.count('correct'),'wrong':graded.count('wrong'),'held':graded.count('abstain')}
    kept0=growth.Unread(d).load()['entries'];me0=cli(d,'g4-self');g0=me0.get('growth') or {}
    # what this version reads alone, of what the child kept (nothing is written: no individual)
    could={}
    for k,e in kept0.items():
        r=api.solve(e['text'],llm='off')
        if r.get('answer') is not None:could[k]=grade(gold[norm(e['text'])],{'answer':r['answer']})
    ev0=len(g4_events(d));v0=values(d)
    t0=time.time();look=cli(d,'g4-reflect');t_look=time.time()-t0
    t0=time.time();act=cli(d,'g4-reflect','--act');t_act=time.time()-t0
    kept=growth.Unread(d).load()['entries'];me=cli(d,'g4-self');g1=me.get('growth') or {}
    grown={k:e for k,e in kept.items() if e.get('grown')}
    right=[k for k,e in grown.items() if grade(gold[norm(e['text'])],{'answer':e['grown']['value']})=='correct']
    false=[k for k in grown if k not in right]
    missed=[k for k in could if k not in grown]
    order=sorted(kept0,key=lambda k:kept0[k].get('first',0))
    beyond=[k for k in missed if order.index(k)>=100]          # g4-reflect reads again the 100 oldest it could not read
    again=[cli(d,'g4-solve','--llm','off','--',grown[k]['text']) for k in sorted(grown,key=lambda k:grown[k].get('first',0))[:3]]
    ev=g4_events(d);au=audits(cli,d)
    readable=sum(1 for it,r in zip(items,lived) if r['answer'] is None and api.solve(it['text'],llm='off').get('answer') is not None)
    checks={'keeps_every_problem_it_could_not_read':len(kept0)==then['held'],
            'notices_every_problem_it_can_now_read':bool(could) and len(grown)==len(could)==readable,
            'notices_no_growth_that_is_wrong':not false,
            'says_so_when_it_meets_them_again':bool(again) and all('own reader' in str((x.get('voice') or {}).get('before')) for x in again),
            'audits_pass':all(x['ok'] for x in au.values())}
    return {'ok':all(checks.values()),'checks':checks,'problems':len(items),'it_could_read_now_of_all_it_could_not':readable,'seconds_to_live_them':round(t_life,1),'earlier_version':then,
            'kept_could_not_read':len(kept0),'not_kept':then['held']-len(kept0),
            'this_version_reads_of_what_it_kept':{'right':sum(1 for x in could.values() if x=='correct'),'wrong':sum(1 for x in could.values() if x=='wrong')},
            'reflect':{'open':look.get('open'),'seconds':round(t_look,1),'try_again_alone':sum(1 for x in look.get('intentions') or [] if x.get('do')=='try_again_alone')},
            'act':{'tried_alone':len(act.get('tried_alone') or []),'answered':sum(1 for x in act.get('tried_alone') or [] if x.get('answer') is not None),
                   'note':act.get('note'),'seconds':round(t_act,1)},
            'noticed':len(grown),'noticed_right':len(right),'noticed_wrong':len(false),'not_noticed':len(missed),
            'not_noticed_beyond_the_100_it_reads_again':len(beyond),
            'grew_experiences':sum(1 for e in ev if e.get('theme')=='g4:grew'),'experiences_before':ev0,'experiences_after':len(ev),
            'values_before':v0,'values_after':values(d),
            'weak_spots_before':[(q['kind'],q['problems']) for q in g0.get('weak_spots') or []],
            'weak_spots_after':[(q['kind'],q['problems']) for q in g1.get('weak_spots') or []],
            'told_after':g1.get('told'),'said_when_met_again':[(x.get('answer'),(x.get('voice') or {}).get('before')) for x in again],
            'audits':au}

# ----------------------------------------------------------------------------- taught
def x_taught(ctx):
    cli,work,items=ctx['cli'],ctx['work'],ctx['items']
    texts=[it['text'] for it in items]
    then=worker(work,texts,True,tag='taught_earlier')                      # the earlier reader, nothing lived
    pairs=[]
    for it,r in zip(items,then):
        if r['answer'] is not None:continue
        now=api.solve(it['text'],llm='off')
        if now.get('answer') is None or grade(it,{'answer':now['answer']})!='correct':continue
        v=doubled(it['text'])
        if v is None:continue
        rv=api.solve(v,llm='off')
        if rv.get('answer') is None:continue
        pairs.append({'id':it['id'],'original':it['text'],'met':v,'this_version_reads_it_as':rv['answer']})
    vthen=worker(work,[p['met'] for p in pairs],True,tag='taught_earlier_variants')
    pairs=[p for p,r in zip(pairs,vthen) if r['answer'] is None]          # the child cannot read the one it meets
    d=work/'taught';new_child(cli,d,'taught')
    met=worker(work,[p['met'] for p in pairs],True,data=d,tag='taught_met')
    rec=work/'taught_parents.jsonl'
    rec.write_text('\n'.join(_line(par,p['original'],_reading(reader.read(p['original'])['spec'])) for p in pairs for par in PARENTS)+'\n',encoding='utf-8')
    taught=worker(work,[p['original'] for p in pairs],True,data=d,llm_mode='on',replay=rec,tag='taught_by_parents')
    alone=worker(work,[p['met'] for p in pairs],True,data=d,voice=True,tag='taught_alone')
    kept=growth.Unread(d).load()['entries'];rows=[];st=learn.Store(d/'g4')
    for p,m,t,a in zip(pairs,met,taught,alone):
        e=kept.get(growth.Unread.entry_id(p['met'])) or {}
        # does the wording it learned read the problem it met? Since v1022.7.7+gen4 a template does not carry over to a
        # text where a number it did not use changed (learn._transfer_guards): learned is then not the same as reads
        tpl=st.find(p['met']) if t['learned'] else None
        rows.append({'id':p['id'],'kept':bool(e),'learned':bool(t['learned']),'answer_when_taught':t['answer'],
                     'learned_wording_reads_it':bool(tpl and not tpl.get('contested') and learn.instantiate(tpl,p['met'])),
                     'noticed':bool(e.get('grown')),'grew_now':any(x.get('theme')=='g4:grew' for x in t['life'] or []) if isinstance(t['life'],list) else False,
                     'alone':a['answer'],'agrees':a['answer'] is not None and Fraction(a['answer'])==Fraction(p['this_version_reads_it_as']),
                     'says_before':bool(a['before']),'before':a['before']})
    n=lambda k:sum(1 for r in rows if r[k])
    au=audits(cli,d)
    checks={'keeps_what_it_met':n('kept')==len(rows)>0,
            'notices_each_problem_a_wording_it_learned_reads':n('noticed')==n('learned_wording_reads_it')>0,
            'answers_them_alone':sum(1 for r in rows if r['alone'] is not None)==n('noticed'),
            'its_answers_agree_with_this_versions_reading':n('agrees')==n('noticed'),
            'says_it_could_not_read_them_before':all(str(r['before']).startswith('I could not read this problem alone when I met it before; now I can') for r in rows if r['alone'] is not None),
            'audits_pass':all(x['ok'] for x in au.values())}
    return {'ok':all(checks.values()),'checks':checks,'pairs':len(rows),'kept':n('kept'),'learned':n('learned'),
            'learned_wording_reads_it':n('learned_wording_reads_it'),'noticed':n('noticed'),'answered_alone':sum(1 for r in rows if r['alone'] is not None),
            'agrees_with_this_version':n('agrees'),'answered_but_disagrees':sum(1 for r in rows if r['alone'] is not None and not r['agrees']),
            'noticed_but_cannot_answer':sum(1 for r in rows if r['noticed'] and r['alone'] is None),
            'rows':rows,'audits':au,
            'note':"the original problems were taught by recorded replies: this version's own reading, the same from each parent"}

# ----------------------------------------------------------------------------- mistaught
def _q(names):return [{'name':n,'unit':'1','integer':False,'signed':False,'about':n} for n in names]
def _r(names,facts):return {'readable':True,'quantities':_q(names),'facts':[{'eq':e,'span':s,'known':''} for e,s in facts],'ask':'number','answer_unit':'','unused':[]}
WORDINGS=[
 {'taught':'When three times a number is decreased by twelve, the result is 30. What is the number?',
  'met':('When four times a number is decreased by eight, the result is 28. What is the number?','9'),
  'other':'When five times a number is decreased by ten, the result is 40. What is the number?',
  'reading':lambda op:_r(('twelve','factor','result','number'),[('twelve = 12','decreased by twelve'),('factor = 3','three times'),('result = 30','the result is 30'),
                         (f'factor * number {op} twelve = result','When three times a number is decreased by twelve, the result is 30')]),
  'other_reading':_r(('ten','factor','result','number'),[('ten = 10','decreased by ten'),('factor = 5','five times'),('result = 40','the result is 40'),
                     ('factor * number - ten = result','When five times a number is decreased by ten, the result is 40')])},
 {'taught':'A number is multiplied by four and then eight is taken away. The result is 28. What is the number?',
  'met':('A number is multiplied by three and then six is taken away. The result is 21. What is the number?','9'),
  'other':'A number is multiplied by five and then ten is taken away. The result is 40. What is the number?',
  'reading':lambda op:_r(('four','eight','result','number'),[('four = 4','multiplied by four'),('eight = 8','eight is taken away'),('result = 28','The result is 28'),
                         (f'four * number {op} eight = result','A number is multiplied by four and then eight is taken away')]),
  'other_reading':_r(('five','ten','result','number'),[('five = 5','multiplied by five'),('ten = 10','ten is taken away'),('result = 40','The result is 40'),
                     ('five * number - ten = result','A number is multiplied by five and then ten is taken away')])},
]
def x_mistaught(ctx):
    cli,work=ctx['cli'],ctx['work'];d=work/'mistaught';new_child(cli,d,'mistaught')
    def rec(name,lines):
        p=work/f'mistaught_{name}.jsonl';p.write_text('\n'.join(lines)+'\n',encoding='utf-8');return p
    wrong=rec('wrong',[_line(par,w['taught'],w['reading']('+')) for w in WORDINGS for par in PARENTS])
    other=rec('other',[_line(par,w['other'],w['other_reading']) for w in WORDINGS for par in PARENTS])
    right=rec('right',[_line(par,w['taught'],w['reading']('-')) for w in WORDINGS for par in PARENTS])
    G=lambda:cli(d,'g4-self').get('growth') or {}
    def alone(w):
        r=cli(d,'g4-solve','--llm','off','--',w['met'][0]);v=r.get('voice') or {}
        return {'answer':r.get('answer'),'right':w['met'][1],'reason':r.get('reason'),'before':v.get('before'),'held_back':v.get('held_back'),
                'grew':[x.get('theme') for x in r.get('life') or [] if isinstance(r.get('life'),list) and x.get('theme')=='g4:grew']}
    def told():g=G();return {k:g.get(k) for k in ('could_not_read','cannot_read_yet','can_read_now','grew')}|{'told':g.get('told')}
    steps=[]
    for w in WORDINGS:cli(d,'g4-solve','--llm','off','--',w['met'][0])
    steps.append({'step':'1. alone, it meets a problem of each wording and cannot read it','self':told()})
    t=[cli(d,'think','--',w['taught'],replay=wrong) for w in WORDINGS]
    steps.append({'step':'2. its three parents agree on a wrong reading of each wording (a sign turned round); it learns it',
                  'answers':[x.get('answer') for x in t],'grew':[sum(1 for e in x.get('life') or [] if e.get('theme')=='g4:grew') for x in t],'self':told()})
    steps.append({'step':'3. alone again: it answers with what it learned','alone':[alone(w) for w in WORDINGS],'self':told()})
    t=[cli(d,'think','--',w['other'],replay=other) for w in WORDINGS]
    steps.append({'step':'4. another problem of each wording, with its parents: they read it otherwise (the reading is contested)',
                  'answers':[x.get('answer') for x in t],'reasons':[x.get('reason') or (x.get('gen4') or {}).get('reason') for x in t],'self':told()})
    steps.append({'step':'5. alone again','alone':[alone(w) for w in WORDINGS],'self':told()})
    t=[cli(d,'think','--',w['taught'],replay=right) for w in WORDINGS]
    steps.append({'step':'6. its parents teach each wording again, rightly','answers':[x.get('answer') for x in t],
                  'grew':[sum(1 for e in x.get('life') or [] if e.get('theme')=='g4:grew') for x in t],'self':told()})
    steps.append({'step':'7. alone again','alone':[alone(w) for w in WORDINGS],'self':told()})
    me=cli(d,'g4-self');au=audits(cli,d)
    S=lambda i:steps[i]['self']
    k=len(WORDINGS)
    checks={'its_growth_follows_what_its_parents_agreed_on':S(1)['can_read_now']==k and steps[1]['grew']==[1]*k,
            'says_where_what_it_used_came_from':all('I learned this wording from' in str(x['before']) for x in steps[2]['alone']),
            'gives_up_a_growth_its_parents_read_otherwise':S(3)['can_read_now']==0 and S(3)['cannot_read_yet']==k,
            'does_not_answer_with_it_alone':all(x['answer'] is None for x in steps[4]['alone']),
            'notices_again_when_taught_again':steps[5]['grew']==[1]*k and S(5)['can_read_now']==k,
            'answers_rightly_and_says_it_had_been_wrong':all(x['answer']==x['right'] for x in steps[6]['alone'])
                and all('5' in str(x['before']) and x['right'] in str(x['before']) for x in steps[6]['alone']),
            # each parent taught the wrong reading of both wordings (wrong, looking back) and read the other problems rightly
            'the_parents_who_taught_it_wrongly_are_looked_back_on':{p:v for p,v in ((me.get('life_story') or {}).get('looked_back') or {}).items()}
                ==({p:{'right':k,'wrong':k} for p in PARENTS}),
            'audits_pass':all(x['ok'] for x in au.values())}
    return {'ok':all(checks.values()),'checks':checks,'steps':steps,'life_story':(me.get('life_story') or {}).get('told'),'grew_experiences':sum(1 for e in g4_events(d) if e.get('theme')=='g4:grew'),
            'audits':au}

EXPERIMENTS={'upgrade':x_upgrade,'taught':x_taught,'mistaught':x_mistaught}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('data');ap.add_argument('--before-src',required=True);ap.add_argument('--runtime-trust-file')
    ap.add_argument('--work');ap.add_argument('--out');ap.add_argument('--only');ap.add_argument('--seed',type=int,default=20261012)
    a=ap.parse_args()
    for k in [k for k in os.environ if k.startswith(CLEAN)]:del os.environ[k]
    work=Path(a.work) if a.work else Path(tempfile.mkdtemp(prefix='growth_exp_'))
    if work.exists() and any(work.iterdir()):raise SystemExit('the work folder must be empty: '+str(work))
    work.mkdir(parents=True,exist_ok=True);earlier_child(work,a.before_src)
    items=[it for it in load(a.data,'asdiv') if it['split']=='dev'];random.Random(a.seed).shuffle(items)
    ctx={'cli':CLI(a.runtime_trust_file),'work':work,'items':items}
    rep={'schema':'tukuyo.growth_experiment/1','utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'seed':a.seed,
         'earlier_reader_files_sha256':{f:hashlib.sha256((Path(a.before_src)/'tukuyo_g4'/f).read_bytes()).hexdigest()[:16]
                                        for f in READER_FILES if (Path(a.before_src)/'tukuyo_g4'/f).is_file()},
         'claim_boundary':{'functional_experiment_of_a_functional_model':True,'consciousness_established':False},'experiments':{}}
    for name in (a.only.split(',') if a.only else list(EXPERIMENTS)):
        t=time.time()
        try:rep['experiments'][name]=EXPERIMENTS[name](ctx)
        except Exception as e:  # noqa: BLE001 - one broken experiment must not hide the others
            import traceback;rep['experiments'][name]={'crashed':type(e).__name__+':'+str(e)[:300],'trace':traceback.format_exc()[-1500:]}
        x=rep['experiments'][name];x['seconds']=round(time.time()-t,1)
        print(name,'ok' if x.get('ok') else 'NOT ok',{c:v for c,v in (x.get('checks') or {}).items() if not v},x['seconds'],'s',flush=True)
    rep['ok']=all(x.get('ok') for x in rep['experiments'].values())
    s=json.dumps(rep,ensure_ascii=False,indent=1,default=str)
    if a.out:Path(a.out).write_text(s,encoding='utf-8')
    else:print(s)

if __name__=='__main__':main()
