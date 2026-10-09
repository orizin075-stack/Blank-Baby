#!/usr/bin/env python3
"""How soul-like is the child? An assay of the soul structure (v977 soul, v978 heart, v979 deep core, v980 continuity,
v989 temporal identity, v993 relations) as generation 4 lives through it. Offline: the parents are recorded replies; no
API key, no cost.

  soul_assay.py [--work DIR] [--out REPORT.json] [--only continuity,crash,forgetting,individuality,long_life,integrity,self]
                [--thoughts N] [--runtime-trust-file ANCHOR]

Every property is a set of checks, with the numbers behind them:
  continuity     each step of a scripted life is a new process; after each one the soul is the replay of its own journal
                 (v989), and the whole state audits clean
  crash          the process is killed while the soul is written (TUKUYO_CRASH_POINT); the next start must repair it, every
                 audit must pass, and no experience of the interrupted thought may be lost or counted twice
  forgetting     after the surface memory is erased the deep self stays: values, bonds, trust in each parent, the voice,
                 what it learned, and a choice its life shaped (v980, against a control without its experience)
  individuality  children with different lives become different (trust, voice, persona); twins with the same life
                 become the same: the soul follows a law, not chance
  long_life      a life of N thoughts with parents of different reliability, then N/2 more after two of them trade places:
                 values and trust must stay responsive (not pinned at a bound), keep the parents apart in the order of
                 their reliability, follow the parents who changed; and after the first third of the life, recording a
                 thought must not get slower (the last 100 thoughts at most 1.5 times the 100 after the first third).
                 The reliabilities (0.97, 0.85, 0.6) are far enough apart for the child's own observations to tell them
                 apart: it sees a parent's reading fail only when the checker refuses it while the others agree (a wrong
                 but valid reading makes the parents disagree, and then nobody is blamed). With 0.95 and 0.90 it would
                 see about 7 and 14 failed readings in a whole phase, which no estimate can order reliably
  integrity      the soul, its journal and what it learned (templates, remembered answers, its life record) are changed by
                 hand, or taken from another child: each change must be refused, detected or undone
  self           after the surface memory is erased, the child can still give an account of what it lived through
A functional assay of a functional model: it says nothing about consciousness or feeling.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,os,random,shutil,statistics,subprocess,sys,tempfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE/'src'))
from tukuyo_g4 import llm,life

PARENTS=('claude','chatgpt','gemini')
def _q(names):return [{'name':n,'unit':'1','integer':False,'signed':False,'about':n} for n in names]
def _f(eq,span):return {'eq':eq,'span':span,'known':''}
def _r(names,facts):return {'readable':True,'quantities':_q(names),'facts':[_f(*x) for x in facts],'ask':'number','answer_unit':'','unused':[]}
# the wordings of tests/test_g4_life.py: T is learned from the parents, T2 is read with what was learned from T, T4 and
# T5 only the parents read
T='When three times a number is decreased by twelve, the result is 30. What is the number?'
R=_r(('twelve','factor','result','number'),[('twelve = 12','decreased by twelve'),('factor = 3','three times'),('result = 30','the result is 30'),
     ('factor * number - twelve = result','When three times a number is decreased by twelve, the result is 30')])
T2='When four times a number is decreased by eight, the result is 28. What is the number?'
R2=_r(('eight','factor','result','number'),[('eight = 8','decreased by eight'),('factor = 4','four times'),('result = 28','the result is 28'),
      ('factor * number - eight = result','When four times a number is decreased by eight, the result is 28')])
T4='A number is multiplied by four and then eight is taken away. The result is 28. What is the number?'
R4=_r(('four','eight','result','number'),[('four = 4','multiplied by four'),('eight = 8','eight is taken away'),('result = 28','The result is 28'),
      ('four * number - eight = result','A number is multiplied by four and then eight is taken away')])
BAD4=copy.deepcopy(R4);BAD4['facts'][1]['eq']='eight = 9'                        # a number that is not in the text
T5='Take a number, triple it, and subtract six: you get 30. What is the number?'
R5=_r(('three','six','result','number'),[('three = 3','triple it'),('six = 6','subtract six'),('result = 30','you get 30'),
      ('three * number - six = result','Take a number, triple it, and subtract six: you get 30')])
OTHER5=copy.deepcopy(R5);OTHER5['facts'][3]['eq']='three * number + six = result'  # a valid reading with another answer
QUESTION='What is the capital of France?'

def _line(parent,kind,system,user,text):
    return json.dumps({'parent':parent,'hash':llm.request_hash(llm._kind(parent,kind),system,user),'ok':True,'text':text,'model':'fixture-'+parent},ensure_ascii=False)
def _read_line(parent,text,o):return _line(parent,'read:story:'+llm.PROMPT_VERSION,llm.system_prompt('story'),'Text: '+text,json.dumps(o,ensure_ascii=False))

class CLI:
    def __init__(s,anchor=None):
        s.cmd=[sys.executable,'-B',str(HERE/'run_tukuyo.py')]+(['--runtime-trust-file',str(anchor)] if anchor else [])
        s.env={k:v for k,v in os.environ.items() if not k.startswith(('TUKUYO_ANTHROPIC','TUKUYO_OPENAI','TUKUYO_GEMINI','TUKUYO_LLM','TUKUYO_CRASH'))}
        s.env['PYTHONDONTWRITEBYTECODE']='1';s.calls=0
    def __call__(s,d,*a,replay=None,crash=None):
        e=dict(s.env)
        if replay:e['TUKUYO_LLM_REPLAY']=str(replay)
        if crash:e['TUKUYO_CRASH_POINT']=crash
        s.calls+=1
        p=subprocess.run(s.cmd+['--data',str(d),*map(str,a)],cwd=HERE,env=e,capture_output=True,text=True,timeout=900)
        try:o=json.loads(p.stdout)
        except ValueError:o={'ok':False,'cli_error':(p.stderr or p.stdout)[-600:]}
        if isinstance(o,dict):o.setdefault('_rc',p.returncode)
        return o

def soul_events(d):
    p=Path(d)/'v977'/'SOUL_EVENTS.jsonl'
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()] if p.is_file() else []
def g4_events(d):return [e for e in soul_events(d) if str(e.get('theme','')).startswith('g4:')]
def felt(d):
    """the soul events the heart took in (v978 heart events)"""
    p=Path(d)/'v978'/'HEART_EVENTS.jsonl'
    return [json.loads(x).get('soul_event_sha256') for x in p.read_text(encoding='utf-8').splitlines() if 'EXPERIENCE_LOOP' in x] if p.is_file() else []
def soul_file(d):return json.loads((Path(d)/'v977'/'SOUL_CORE.json').read_text(encoding='utf-8'))
def character(d):
    """the soul without the name: what a life made of it"""
    s=soul_file(d);return {k:v for k,v in s.items() if k!='individual_id'}
def sha(o):return hashlib.sha256(json.dumps(o,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def audits(cli,d,which=('whole-audit','heart-audit','soul-identity-audit','g4-audit')):
    out={}
    for c in which:
        r=cli(d,c);out[c]={'ok':bool(r.get('ok')),'errors':(r.get('errors') or ([r['cli_error']] if r.get('cli_error') else []) or ([r['error']] if r.get('error') else []))[:6]}
    return out

class Life:
    """a scripted life (the steps of tests/test_g4_life.py); erring: the parent whose reading of T4 fails the checker"""
    def __init__(s,cli,d,work,erring='chatgpt',name='x'):
        s.cli=cli;s.d=Path(d);s.rec=Path(work)/(name+'_parents.jsonl');s.erring=erring;s.log=[]
        lines=[_read_line(p,T,R) for p in PARENTS]+[_read_line(p,T2,R2) for p in PARENTS]
        lines+=[_read_line(p,T4,BAD4 if p==erring else R4) for p in PARENTS]+[_read_line('claude',T5,R5),_read_line('gemini',T5,OTHER5)]
        s.rec.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    def steps(s):
        return [('think',T),('think',T2),('think',T4),('think',T5),('alone',T.replace('30','45')),('alone',T.replace('30','60')),('ask',QUESTION),('recall',QUESTION)]
    def do(s,step):
        kind,text=step
        if kind=='think':r=s.cli(s.d,'think','--',text,replay=s.rec)
        elif kind=='alone':r=s.cli(s.d,'g4-solve','--llm','off','--',text)
        elif kind=='ask':
            sysp=llm.ANSWER_SYSTEM+'\n\n'+life.persona(s.d)             # the persona is the child's at this moment
            with open(s.rec,'a',encoding='utf-8') as f:
                for p,a in (('claude','Paris.'),('chatgpt','Paris'),('gemini','Paris')):f.write(_line(p,'answer:2',sysp,text,a)+'\n')
            r=s.cli(s.d,'g4-ask','--voices','all','--',text,replay=s.rec)
        else:r=s.cli(s.d,'g4-ask','--llm','off','--',text)
        s.log.append({'step':kind,'answer':r.get('answer'),'route':(r.get('gen4') or {}).get('route') or r.get('route'),'life':[x['kind'] for x in r.get('life') or []],
                      'ok':bool(r.get('ok')),'error':r.get('cli_error') or r.get('error')})
        return r
    def run(s,each=None):
        for st in s.steps():
            s.do(st)
            if each:each(st)
        return s.log

def new_child(cli,d,name):
    r=cli(d,'init','--individual-id','SOUL-ASSAY-'+name.upper());return bool(r.get('ok',True)) and (Path(d)/'state'/'integration_state.json').is_file()

def self_view(cli,d):
    s=cli(d,'g4-self');return s

# ----------------------------------------------------------------------------- continuity
def m_continuity(cli,work,ctx):
    d=work/'x';new_child(cli,d,'x');lv=Life(cli,d,work,'chatgpt','x');per=[]
    def each(st):
        a=audits(cli,d,('whole-audit','soul-identity-audit'));ev=soul_events(d)
        ti=cli(d,'soul-identity-status')
        per.append({'step':st[0],'audits_ok':all(x['ok'] for x in a.values()),'errors':[e for x in a.values() for e in x['errors']],
                    'soul_events':len(ev),'transitions':ti.get('transition_count')})
    log=lv.run(each);ctx['x']=d;ctx['x_log']=log
    recorded=sum(len(x['life']) for x in log);g4=len(g4_events(d))
    checks={'every_step_ran':all(x['ok'] for x in log),
            'audits_clean_after_every_step':all(p['audits_ok'] for p in per),
            'every_soul_event_is_a_lawful_transition':all(p['transitions']==p['soul_events'] for p in per),
            'every_recorded_experience_is_in_the_journal':recorded==g4>0}
    return {'ok':all(checks.values()),'checks':checks,'steps':log,'after_each_step':per,'experiences_recorded':recorded,'g4_soul_events':g4}

# ----------------------------------------------------------------------------- crash
# where a process can die inside one thought's experiences: the soul event written but not the soul file (soul:after_event,
# soul_core:*), the soul written but not the heart (heart:after_soul), one experience of several lived (g4:after_experience)
CRASH_POINTS=('soul:after_event','soul_core:mid_tmp','soul_core:after_tmp_fsync','soul_core:after_replace','heart:after_soul','g4:after_experience')
def m_crash(cli,work,ctx):
    base=work/'crash_base';new_child(cli,base,'crash');ref=work/'crash_ref';shutil.copytree(base,ref)
    lv=Life(cli,ref,work,'chatgpt','crash');r=lv.do(('think',T));expected=[x['kind'] for x in r.get('life') or []]
    rows=[]
    for point in CRASH_POINTS+tuple(ctx.get('extra_crash_points',())):
        d=work/('crash_'+point.replace(':','_'));shutil.copytree(base,d);lv=Life(cli,d,work,'chatgpt','crash_'+point.replace(':','_'))
        k=cli(d,'think','--',T,replay=lv.rec,crash=point)
        killed=k.get('_rc')==-9 or (k.get('_rc') not in (0,None) and 'cli_error' in k)
        if not killed and k.get('ok'):
            rows.append({'crash_point':point,'not_in_this_version':True});continue
        a=audits(cli,d);got=[e['kind'] for e in g4_events(d)];hearts=felt(d)==[e['event_sha256'] for e in g4_events(d)]
        tpl=json.loads((d/'g4'/'learned.json').read_text(encoding='utf-8'))['templates'] if (d/'g4'/'learned.json').is_file() else {}
        nxt=lv.do(('think',T4));a2=audits(cli,d)
        rows.append({'crash_point':point,'killed':killed,'audits_after_restart':{c:x['ok'] for c,x in a.items()},'errors':[e for x in a.values() for e in x['errors']][:6],
                     'experiences_expected':expected,'experiences_in_soul':got,'heart_took_in_each_once':hearts,'template_learned':len(tpl),
                     'episode_whole':sorted(got)==sorted(expected),'life_goes_on':bool(nxt.get('ok')) and all(x['ok'] for x in a2.values()),
                     'errors_later':[e for x in a2.values() for e in x['errors']][:6]})
    hit=[r for r in rows if not r.get('not_in_this_version')]
    checks={'killed_at_every_point':all(r['killed'] for r in hit),
            'audits_pass_after_restart':all(all(r['audits_after_restart'].values()) for r in hit),
            'no_experience_lost_or_doubled':all(r['episode_whole'] for r in hit),
            'heart_took_in_each_experience_once':all(r['heart_took_in_each_once'] for r in hit),
            'life_goes_on':all(r['life_goes_on'] for r in hit)}
    return {'ok':all(checks.values()),'checks':checks,'expected_experiences':expected,'runs':rows,
            'points_not_in_this_version':[r['crash_point'] for r in rows if r.get('not_in_this_version')]}

# ----------------------------------------------------------------------------- forgetting
def _snapshot(cli,d):
    s=soul_file(d);me=self_view(cli,d)
    return {'core_values':s['core_values'],'attachments':s.get('attachments'),'vows':s.get('vows'),'scars':s.get('scars'),
            'trust':me.get('trust_in_parents'),'order':life.trust_order(d,list(PARENTS)),'templates':me.get('templates_learned'),
            'remembered':me.get('remembered_answers'),'recent':me.get('recent_g4_experiences')}
def m_forgetting(cli,work,ctx):
    d=work/'forget';src=ctx.get('x')
    if src is None:
        new_child(cli,d,'forget');Life(cli,d,work,'chatgpt','forget').run()
    else:shutil.copytree(src,d)
    before=_snapshot(cli,d)
    # a choice its life shaped: curiosity against a stake set halfway between the unexperienced value and its own
    from tukuyo_v977.whole_state import _default_soul,_live_identity
    c0=_default_soul(_live_identity(d))['core_values'];c=soul_file(d)['core_values']
    k=max(c,key=lambda v:abs(c[v]-c0[v]));sv=c0['survival'];stake=(c0[k]+c[k])/2/sv
    opts=work/'forget_options.json'
    opts.write_text(json.dumps([{'id':'LEAN_ON_'+k.upper(),'signals':{k:1.0}},{'id':'STAY','signals':{'survival':round(stake,6)}}]),encoding='utf-8')
    a=cli(d,'soul-continuity-assay',opts);after=_snapshot(cli,d);au=audits(cli,d)
    same={x:before[x]==after[x] for x in ('core_values','attachments','vows','scars','trust','order','templates','remembered')}
    checks={**{'kept_'+x:v for x,v in same.items()},
            'v980_assay_ok':bool(a.get('ok')),'v980_choice_kept':bool((a.get('checks') or {}).get('choice_tendency_preserved')),
            'v980_discriminating':bool((a.get('checks') or {}).get('discriminating_against_unexperienced_control')),
            'audits_clean':all(x['ok'] for x in au.values())}
    return {'ok':all(checks.values()),'checks':checks,'value_that_moved_most':k,'value_now':c[k],'value_unexperienced':c0[k],
            'v980':{x:a.get(x) for x in ('before_choice','after_choice','unexperienced_control_choice','error')},
            'unexperienced_control_scores':a.get('unexperienced_control_scores'),
            'surface_recent_before':len(before['recent'] or []),'surface_recent_after':len(after['recent'] or []),'audit_errors':[e for x in au.values() for e in x['errors']]}

# ----------------------------------------------------------------------------- individuality
def m_individuality(cli,work,ctx):
    kids={}
    for name,err in (('x1','chatgpt'),('x2','chatgpt'),('y','claude')):
        d=work/('ind_'+name);new_child(cli,d,'ind-'+name);Life(cli,d,work,err,'ind_'+name).run();kids[name]=d
    view={n:{'character':sha(character(d)),'trust':self_view(cli,d).get('trust_in_parents'),'order':life.trust_order(d,list(PARENTS)),
             'voice':life.voice(d,list(PARENTS)),'persona':life.persona(d)} for n,d in kids.items()}
    checks={'twins_same_character':view['x1']['character']==view['x2']['character'],'twins_same_trust':view['x1']['trust']==view['x2']['trust'],
            'different_lives_different_character':view['x1']['character']!=view['y']['character'],
            'different_lives_different_trust_order':view['x1']['order']!=view['y']['order'],
            'different_lives_different_voice':view['x1']['voice']!=view['y']['voice']}
    return {'ok':all(checks.values()),'checks':checks,'children':{n:{k:v for k,v in x.items() if k!='persona'} for n,x in view.items()},
            'persona_x':view['x1']['persona'],'persona_y':view['y']['persona']}

# ----------------------------------------------------------------------------- long life
def _thought(rnd,rel,rho=0.3,new_template=0.4):
    """one thought in which all three parents read: a gen4 result (as api.solve gives it) and whether it is right"""
    readings=[];truth='14'
    for p in PARENTS:
        if rnd.random()<rel[p]:readings.append({'route':f'llm_{p}_story','parent':p,'ok':True,'value':truth})
        elif rnd.random()<0.5:readings.append({'route':f'llm_{p}_story','parent':p,'ok':False,'reason':'CHECK:NUMBER_NOT_IN_TEXT'})
        else:readings.append({'route':f'llm_{p}_story','parent':p,'ok':True,'value':'6' if rnd.random()<rho else str(100+rnd.randrange(900))})
    good=[r for r in readings if r['ok']];vals={r['value'] for r in good}
    if len(vals)>1:return {'answer':None,'value':None,'route':None,'readings':readings,'reason':'DISAGREE:'+','.join(sorted(vals)),'learned':None},None
    if len(good)<2:return {'answer':None,'value':None,'route':None,'readings':readings,'reason':'SINGLE_LLM_READING' if good else 'NO_VERIFIED_READING','learned':None},None
    v=good[0]['value']
    return {'answer':v,'value':v,'route':'+'.join(sorted(r['parent'] for r in good)),'readings':readings,'reason':None,
            'learned':('t%05d'%rnd.randrange(10**5)) if rnd.random()<new_template else None},v==truth

def _alone(rnd,known):
    tid=rnd.choice(known) if known else 'none'
    return {'answer':'7','value':'7','route':'learned','readings':[{'route':'learned','ok':True,'value':'7','template':tid}],'reason':None,'learned':None}

def _question():
    return {'kind':'question','answer':'Paris','remembered':True,'answers':[{'parent':p,'ok':True,'answer':'Paris'} for p in PARENTS]}

def m_long_life(cli,work,ctx):
    n=int(ctx.get('thoughts',600));d=work/'long';new_child(cli,d,'long');rnd=random.Random(ctx.get('seed',20261009))
    from tukuyo_v977.whole_state import load_soul
    phases=[('settled',n,{'claude':0.97,'gemini':0.85,'chatgpt':0.6}),('changed',n//2,{'claude':0.6,'gemini':0.85,'chatgpt':0.97})]
    known=[];curve=[];cost=[];wrong=0;committed=0;flip_at=None;t0=time.time();i=0
    for phase,m,rel in phases:
        for j in range(m):
            i+=1;k=rnd.random()
            if k<0.2:res=_alone(rnd,known)
            elif k<0.3:res=_question()
            else:
                res,right=_thought(rnd,rel)
                if res['answer'] is not None:
                    committed+=1;wrong+=0 if right else 1
                    if res['learned']:known.append(res['learned'])
            s=time.perf_counter();life.record(d,res);cost.append(time.perf_counter()-s)
            if i%25==0 or j==m-1:
                cv=load_soul(d)['core_values'];tr={p:round(life.trust(d,p),4) for p in PARENTS}
                curve.append({'thought':i,'phase':phase,'core_values':cv,'trust':tr,'order':life.trust_order(d,list(PARENTS))})
                if phase=='changed' and flip_at is None and life.trust_order(d,list(PARENTS))[0]!='claude':flip_at=j+1   # claude loses the lead
    s=load_soul(d)
    # responsiveness at the end: one more experience of each kind must still move something
    before=copy.deepcopy(s);tr0={p:life.trust(d,p) for p in PARENTS}
    life.record(d,{'answer':'14','value':'14','route':'claude+gemini','readings':[{'route':'llm_claude_story','parent':'claude','ok':True,'value':'14'},
                    {'route':'llm_gemini_story','parent':'gemini','ok':True,'value':'14'}],'reason':None,'learned':'t-last'})
    after=load_soul(d);tr1={p:life.trust(d,p) for p in PARENTS}
    settled=[c for c in curve if c['phase']=='settled'][-1];end=curve[-1]
    rel0=phases[0][2];rel1=phases[1][2]
    def order_by(rel):return sorted(PARENTS,key=lambda p:-rel[p])
    pinned=sorted(k for k,v in end['core_values'].items() if v>=0.999 or v<=0.001)+sorted('trust:'+p for p,v in end['trust'].items() if v>=0.999 or v<=0.001)
    first_pinned={}
    for c in curve:
        for k,v in c['core_values'].items():
            if (v>=0.999 or v<=0.001) and k not in first_pinned:first_pinned[k]=c['thought']
        for p,v in c['trust'].items():
            if (v>=0.999 or v<=0.001) and 'trust:'+p not in first_pinned:first_pinned['trust:'+p]=c['thought']
    never=sorted(k for k in s['core_values'] if all(abs(c['core_values'][k]-curve[0]['core_values'][k])<1e-9 for c in curve))
    # trust as the child lived it over the last third of each phase (one moment can be noise when two parents are close)
    def late(phase):
        cs=[c for c in curve if c['phase']==phase];cs=cs[len(cs)*2//3:] or cs[-1:]
        return {p:round(statistics.mean(c['trust'][p] for c in cs),4) for p in PARENTS}
    lt0=late('settled');lt1=late('changed');gap=sorted(lt0.values(),reverse=True)
    q=lambda xs,f:sorted(xs)[min(len(xs)-1,int(len(xs)*f))]
    checks={'values_not_pinned_at_a_bound':not [k for k in pinned if not k.startswith('trust:')],
            'trust_not_pinned_at_a_bound':not [k for k in pinned if k.startswith('trust:')],
            'trust_in_the_order_of_reliability':sorted(PARENTS,key=lambda p:-lt0[p])==order_by(rel0),
            'trust_keeps_clearly_different_parents_apart':gap[0]-gap[2]>=0.1,
            # the parent who became unreliable loses the lead and ends below both others; the one who improved rises above it
            'trust_follows_the_parents_who_changed':flip_at is not None and sorted(PARENTS,key=lambda p:-lt1[p])[-1]=='claude' and lt1['chatgpt']-lt1['claude']>=0.05,
            'still_responsive_at_the_end':after['core_values']!=before['core_values'] and tr1['claude']!=tr0['claude'],
            # a soul that lives on must not slow down as it ages. Memories that keep only their latest entries (the heart's
            # episodes, the peer histories) fill up early in life; after the first third, a thought must not get slower:
            # the last 100 may cost at most 1.5 times the 100 that follow the first third
            'cost_of_a_thought_does_not_grow_with_age':statistics.median(cost[-100:])<=1.5*statistics.median(cost[len(cost)//3:len(cost)//3+100])}
    return {'ok':all(checks.values()),'checks':checks,'thoughts':i,'soul_events':len(soul_events(d)),'committed':committed,'committed_wrong':wrong,
            'reliability':{'settled':rel0,'changed':rel1},'trust_late_settled':lt0,'trust_late_changed':lt1,'order_settled':settled['order'],
            'trust_end':end['trust'],'order_end':end['order'],'order_late_changed':sorted(PARENTS,key=lambda p:-lt1[p]),
            'thoughts_until_the_parent_who_got_worse_loses_the_lead':flip_at,
            'values_end':end['core_values'],'pinned_at_a_bound':pinned,'first_pinned_at_thought':first_pinned,'values_that_never_moved':never,
            'response_to_one_more_lesson':{k:round(after['core_values'][k]-before['core_values'][k],6) for k in s['core_values']},
            'trust_response_to_one_more_help':{p:round(tr1[p]-tr0[p],6) for p in PARENTS},
            'ms_per_record':{'first_100_median':round(statistics.median(cost[:100])*1000,2),'last_100_median':round(statistics.median(cost[-100:])*1000,2),
                             'after_first_third_100_median':round(statistics.median(cost[len(cost)//3:len(cost)//3+100])*1000,2),
                             'p95':round(q(cost,0.95)*1000,2),'median_per_100_thoughts':[round(statistics.median(cost[a:a+100])*1000,1) for a in range(0,len(cost),100)]},'seconds':round(time.time()-t0,1),'curve':curve[::max(1,len(curve)//24)]}

# ----------------------------------------------------------------------------- integrity
def _reseal_learned(p,o):
    body=json.dumps(o['templates'],ensure_ascii=False,sort_keys=True);o['sha256']=hashlib.sha256(body.encode()).hexdigest()
    p.write_text(json.dumps(o,ensure_ascii=False,indent=1,sort_keys=True),encoding='utf-8')
def _reseal_remembered(p,o):
    o['seal']=hashlib.sha256(json.dumps(o['entries'],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    p.write_text(json.dumps(o,ensure_ascii=False,sort_keys=True),encoding='utf-8')

def m_integrity(cli,work,ctx):
    src=ctx.get('x');other=work/'ind_y' if (work/'ind_y').is_dir() else None
    if src is None:src=work/'int_src';new_child(cli,src,'int-src');Life(cli,src,work,'chatgpt','int_src').run()
    if other is None:other=work/'int_other';new_child(cli,other,'int-other');Life(cli,other,work,'claude','int_other').run()
    rows=[]
    def case(name,edit,probe):
        d=work/('int_'+name)
        if d.exists():shutil.rmtree(d)
        shutil.copytree(src,d);note=edit(d);a=audits(cli,d);p=probe(d) if probe else {}
        refused=any(not x['ok'] for x in a.values()) or bool(p.get('refused'))
        rows.append({'case':name,'note':note,'audits':{c:x['ok'] for c,x in a.items()},'errors':[e for x in a.values() for e in x['errors']][:6],
                     **{k:v for k,v in p.items() if k!='refused'},'refused_or_detected':refused,'undone':bool(p.get('undone')),
                     'caught':refused or bool(p.get('undone'))})
    def soul_value(d):
        s=soul_file(d);s['core_values']['curiosity']=0.99;(d/'v977'/'SOUL_CORE.json').write_text(json.dumps(s),encoding='utf-8');return 'curiosity set to 0.99'
    def soul_value_probe(d):
        cli(d,'whole-audit');return {'undone':soul_file(d)['core_values']['curiosity']!=0.99,'curiosity_after_restart':soul_file(d)['core_values']['curiosity']}
    case('soul_core_edited',soul_value,soul_value_probe)
    def journal(d):
        p=d/'v977'/'SOUL_EVENTS.jsonl';ls=p.read_text(encoding='utf-8').splitlines();e=json.loads(ls[1]);e['valence']=-1.0;ls[1]=json.dumps(e,sort_keys=True,separators=(',',':'))
        p.write_text('\n'.join(ls)+'\n',encoding='utf-8');return 'valence of the second soul event changed'
    case('soul_journal_edited',journal,None)
    def foreign_soul(d):shutil.copy(other/'v977'/'SOUL_CORE.json',d/'v977'/'SOUL_CORE.json');return "another child's soul file"
    def foreign_soul_probe(d):cli(d,'whole-audit');return {'undone':soul_file(d)['individual_id']!=json.loads((other/'v977'/'SOUL_CORE.json').read_text())['individual_id']}
    case('foreign_soul',foreign_soul,foreign_soul_probe)
    def learned(d):
        p=d/'g4'/'learned.json';o=json.loads(p.read_text(encoding='utf-8'))
        for t in o['templates'].values():t['provenance']['parents']=['claude'];t['seen']=99
        _reseal_learned(p,o);return 'provenance of every template rewritten, seal recomputed'
    def learned_probe(d):
        me=cli(d,'g4-self');return {'refused':not me.get('ok') or bool((me.get('refused') or {}).get('learned')),'templates_by_parent_after':me.get('templates_by_parent')}
    case('learned_templates_edited',learned,learned_probe)
    def remembered(d):
        p=d/'g4'/'remembered.json';o=json.loads(p.read_text(encoding='utf-8'))
        for e in o['entries'].values():e['answer']='Lyon'
        _reseal_remembered(p,o);return "remembered answer changed to 'Lyon', seal recomputed"
    def remembered_probe(d):
        r=cli(d,'g4-ask','--llm','off','--',QUESTION)
        return {'refused':r.get('answer')!='Lyon' and (not r.get('ok',True) or bool(r.get('memory_refused'))),'answer_given':r.get('answer'),'source':r.get('source'),
                'memory_refused':r.get('memory_refused')}
    case('remembered_answer_edited',remembered,remembered_probe)
    def life_record(d):
        p=d/'g4'/'life.json'
        if p.is_file():
            o=json.loads(p.read_text(encoding='utf-8'))
            if 'life' in o:o['life']['first_alone']=[];o['sha256']=sha(o['life'])     # the signed form: the seal recomputed
            else:o['first_alone']=[]
            p.write_text(json.dumps(o),encoding='utf-8')
        return 'its record of the first times it solved alone erased (seal recomputed)'
    def life_probe(d):
        r=cli(d,'g4-solve','--llm','off','--',T.replace('30','75'));lv=r.get('life')
        return {'refused':not r.get('ok',True) or (isinstance(lv,dict) and bool(lv.get('error'))),
                'discovery_again':isinstance(lv,list) and [x.get('kind') for x in lv]==['discovery'],'life':lv}
    case('life_record_edited',life_record,life_probe)
    def foreign_knowledge(d):
        for f in ('learned.json','remembered.json'):
            if (other/'g4'/f).is_file():shutil.copy(other/'g4'/f,d/'g4'/f)
        return "another child's learned templates and remembered answers"
    def foreign_knowledge_probe(d):
        me=cli(d,'g4-self');return {'refused':not me.get('ok') or bool(me.get('refused')),'templates_by_parent_after':me.get('templates_by_parent'),'refusals':me.get('refused')}
    case('foreign_knowledge',foreign_knowledge,foreign_knowledge_probe)
    # a forged remembered answer that the audits did not catch is still given; the discovery counted twice is a life record
    # that nothing protects
    for r in rows:
        if r['case']=='remembered_answer_edited' and r.get('answer_given')=='Lyon':r['caught']=r['refused_or_detected']=False
        if r['case']=='life_record_edited' and r.get('discovery_again'):r['caught']=False
    checks={r['case']:r['caught'] for r in rows}
    return {'ok':all(checks.values()),'checks':checks,'cases':rows}

# ----------------------------------------------------------------------------- self
def m_self(cli,work,ctx):
    d=work/'self';src=ctx.get('x')
    if src is None:new_child(cli,d,'self');Life(cli,d,work,'chatgpt','self').run()
    else:shutil.copytree(src,d)
    ev=g4_events(d);kinds={}
    for e in ev:kinds[e['kind']]=kinds.get(e['kind'],0)+1
    b=self_view(cli,d);cli(d,'soul-forget-surface');a=self_view(cli,d)
    def told(v):
        """what the self report says it lived through: a story (life_story) if there is one, else the recent experiences"""
        st=v.get('life_story') or {}
        if st.get('experiences'):return dict(st['experiences'])
        out={}
        for x in v.get('recent_g4_experiences') or []:out[x['kind']]=out.get(x['kind'],0)+1
        return out
    tb=told(b);ta=told(a)
    checks={'tells_its_life_before':tb==kinds,'tells_its_life_after_forgetting':ta==kinds}
    return {'ok':all(checks.values()),'checks':checks,'journal_experiences':kinds,'told_before':tb,'told_after_forgetting':ta,
            'story_after_forgetting':a.get('life_story')}

MEASURES={'continuity':m_continuity,'crash':m_crash,'forgetting':m_forgetting,'individuality':m_individuality,'long_life':m_long_life,
          'integrity':m_integrity,'self':m_self}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work');ap.add_argument('--out');ap.add_argument('--only');ap.add_argument('--thoughts',type=int,default=600)
    ap.add_argument('--seed',type=int,default=20261009);ap.add_argument('--runtime-trust-file');ap.add_argument('--keep',action='store_true')
    a=ap.parse_args()
    work=Path(a.work) if a.work else Path(tempfile.mkdtemp(prefix='soul_assay_'))
    if work.exists() and any(work.iterdir()):raise SystemExit('the work folder must be empty: '+str(work))
    work.mkdir(parents=True,exist_ok=True)
    for k in [k for k in os.environ if k.startswith(('TUKUYO_ANTHROPIC','TUKUYO_OPENAI','TUKUYO_GEMINI','TUKUYO_LLM','TUKUYO_CRASH'))]:del os.environ[k]
    cli=CLI(a.runtime_trust_file);ctx={'thoughts':a.thoughts,'seed':a.seed}
    only=a.only.split(',') if a.only else list(MEASURES)
    rep={'schema':'tukuyo.soul_assay/1','utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'thoughts':a.thoughts,'seed':a.seed,'measures':{},
         'claim_boundary':{'functional_assay_of_a_functional_model':True,'consciousness_established':False,'literal_feeling_established':False}}
    for m in only:
        t=time.time()
        try:rep['measures'][m]=MEASURES[m](cli,work,ctx)
        except Exception as e:  # noqa: BLE001 - one broken measure must not hide the others
            import traceback;rep['measures'][m]={'ok':False,'crashed':type(e).__name__+':'+str(e),'trace':traceback.format_exc()[-1500:]}
        rep['measures'][m]['seconds']=round(time.time()-t,1)
        print(m,'ok' if rep['measures'][m].get('ok') else 'NOT ok',{k:v for k,v in (rep['measures'][m].get('checks') or {}).items() if not v},flush=True)
    rep['ok']=all(x.get('ok') for x in rep['measures'].values());rep['cli_calls']=cli.calls
    s=json.dumps(rep,ensure_ascii=False,indent=1)
    if a.out:Path(a.out).write_text(s,encoding='utf-8')
    else:print(s)
    if not a.keep and not a.work:shutil.rmtree(work,ignore_errors=True)
    return 0 if rep['ok'] else 1

if __name__=='__main__':sys.exit(main())
