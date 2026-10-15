#!/usr/bin/env python3
"""How soul-like is the child? An assay of the soul structure (v977 soul, v978 heart, v979 deep core, v980 continuity,
v989 temporal identity, v993 relations) as generation 4 lives through it. Offline: the parents are recorded replies; no
API key, no cost.

  soul_assay.py [--work DIR] [--out REPORT.json] [--only continuity,crash,forgetting,individuality,long_life,integrity,self,close_parents,
                 self_knowledge,inner_life,own_voice,growth]
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
  close_parents  a model of what the child observes of parents whose reliabilities are close (0.95, 0.90, 0.70), run
                 through the real soul law: how often its record orders them right, how many failed readings it sees and
                 how far apart its record keeps them, with and without looking back (hindsight.py)
  self_knowledge the child learns from its life where its own way of reading holds up and where it does not: its parents
                 confirm one way of reading (stories of giving and getting) and two of them read another way (comparisons)
                 against it, twice. It must ask the other parents when the one it asked disagrees, know what it is good at
                 and where it was wrong (g4-self), hold back on its own where it was contradicted while still answering
                 what it knows, and trust that way of reading again once its parents confirm it; a child without that life
                 answers as before (the humility is its own); its knowledge of itself is in its soul (it survives the
                 surface memory being erased) and every audit passes
  inner_life     between problems, the child looks at what it is unsure of (g4-reflect): a disagreement of its parents it
                 could not settle, and a way of reading of its own that its parents read otherwise. It must know these
                 open questions and say what it wants to ask; looking at them changes nothing by itself; with no parent
                 to ask it asks nobody; and when it may act (--act), it asks its parents again on its own, so that the
                 disagreement is settled (who was right is looked back on) and its own way of reading is checked again;
                 every audit passes
  own_voice      the child says in its own words how it read a problem and what it calculated (the words of the problem
                 it read each number from, each quantity it worked out with the numbers put in, the answer and its unit),
                 how sure it is and why (the checker; the parents who read it the same way; how often its parents
                 confirmed this way of reading: a child with that life is sure, a child without it is fairly sure and
                 says its parents have not checked it yet), and why it holds back (what it would have answered and how
                 often its parents read that way otherwise; what it could not read). Every number it says is a number
                 of the problem, a value of its reading or a count of its own record; the same thought is said in the
                 same words; no parent is asked and it speaks as itself (life.voice_check); every audit passes
  growth         the child notices its own growth. Alone, it meets problems it cannot read (a question asked in a way it does
                 not know, a story it does not know how to put together, a story in which an amount is not given): it keeps
                 them, knows its weak spots in words and with counts, and says what it wants to learn (not the story whose
                 amount is not given: that may be the problem's fault, not its own); meeting one again, it says it could
                 not read it before either. Its parents teach it the wording of one of them with other numbers: it notices
                 that it can now read that problem alone (one experience in its soul), says so when it meets it again and
                 who taught it, and that weak spot is gone; a child without that past learns the same wording and notices
                 nothing. A problem an earlier version of its reader could not read, which its reader now reads: it
                 notices that too. Looking at all this changes nothing; it survives the surface memory being erased; a
                 forged record of its growth is refused; every audit passes
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

# ----------------------------------------------------------------------------- close parents
def _close_life(rnd,rel,variant,n=600,k=60,rho=0.3):
    """one life of n thoughts on k wordings, as the child can observe it, through the real soul law (law 2) and trust
    record. variant 'at_once': only what it could judge at the time (before looking back existed); 'looking_back': also
    a checker failure when it withheld, and the disagreements it kept, answered once it learned the wording.
    A wording it has learned it reads itself, and only the parent it trusts most checks it (as api.solve plans it)."""
    from tukuyo_v977 import whole_state as W
    soul=W._default_soul({'individual_id':'model'});learned={};kept={};failed={p:0 for p in PARENTS}
    def ev(kind,p,theme):
        nonlocal soul
        soul=W._apply_experience_mutation(soul,kind,*((0.4,0.2) if kind=='parent_help' else (-0.3,0.2)),theme,'parent:'+p,law=2)
        if kind=='parent_error':failed[p]+=1
    def reading(p):
        if rnd.random()<rel[p]:return 'right'
        if rnd.random()<0.5:return None                                   # fails the checker
        return 'wrong:6' if rnd.random()<rho else 'wrong:%d'%rnd.randrange(10**6)
    for _ in range(n):
        w=rnd.randrange(k)
        if w in learned:
            tr={p:W.trust_record(soul,'parent:'+p) for p in PARENTS};p=min(PARENTS,key=lambda q:(-tr[q],PARENTS.index(q)));r=reading(p)
            if r is None:ev('parent_error',p,'g4:reading')                # its own reading answers; the parent's failed the checker
            elif r==learned[w]:ev('parent_help',p,'g4:reading')
            continue                                                      # a valid other answer: withheld, and no new agreement will settle it
        rs={p:reading(p) for p in PARENTS};good={p:r for p,r in rs.items() if r is not None}
        if len(good)>=2 and len(set(good.values()))==1:                   # the parents agree: answered and learned
            val=next(iter(good.values()))
            for p in sorted(good):ev('parent_help',p,'g4:reading')
            for p in sorted(rs):
                if rs[p] is None:ev('parent_error',p,'g4:reading')
            learned[w]=val
            if variant=='looking_back':
                for e in kept.pop(w,[]):
                    for p in sorted(e):ev('parent_help' if e[p]==val else 'parent_error',p,'g4:hindsight')
        elif variant=='looking_back':                                      # withheld
            for p in sorted(rs):
                if rs[p] is None:ev('parent_error',p,'g4:reading')
            if good:kept.setdefault(w,[]).append(good)
    return {p:W.trust_record(soul,'parent:'+p) for p in PARENTS},failed

def m_close_parents(cli,work,ctx):
    """can the child tell close parents apart (Claude 0.95, Gemini 0.90, ChatGPT 0.70)? Many model lives (_close_life),
    the same seeds for both variants: how often its record ranks the close pair in the right order at the end, and how
    many failed readings it gets to see. A model of what it observes, run through the real soul law"""
    rel={'claude':0.95,'gemini':0.90,'chatgpt':0.70};lives=int(ctx.get('lives',300));res={}
    for variant in ('at_once','looking_back'):
        right=0;full=0;gaps=[];failed={p:[] for p in PARENTS}
        for i in range(lives):
            tr,fl=_close_life(random.Random(ctx.get('seed',20261010)+i),rel,variant)
            right+=tr['claude']>tr['gemini'];full+=tr['claude']>tr['gemini']>tr['chatgpt'];gaps.append(tr['claude']-tr['gemini'])
            for p in PARENTS:failed[p].append(fl[p])
        res[variant]={'close_pair_in_order':round(right/lives,3),'all_three_in_order':round(full/lives,3),'mean_gap_claude_gemini':round(statistics.mean(gaps),4),
                      'failed_readings_seen_per_life':{p:round(statistics.mean(failed[p]),1) for p in PARENTS}}
    a,b=res['at_once'],res['looking_back'];seen=lambda r:sum(r['failed_readings_seen_per_life'].values())
    # what looking back is for: the child sees more of its parents' failed readings, and its record keeps close parents
    # further apart. How often the close pair ends in the right order is reported: with the most trusted parent checking
    # what it has learned, the child already orders them right in most lives
    checks={'close_parents_in_order_in_most_lives':b['close_pair_in_order']>=0.9,
            'looking_back_sees_more_failed_readings':seen(b)>=1.5*seen(a),
            'looking_back_keeps_close_parents_further_apart':b['mean_gap_claude_gemini']>=1.5*a['mean_gap_claude_gemini']}
    return {'ok':all(checks.values()),'checks':checks,'lives':lives,'thoughts_per_life':600,'wordings':60,'reliability':rel,**res,
            'note':'a model of what the child observes (readings drawn at these reliabilities), run through the real soul law and trust record'}

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

# ----------------------------------------------------------------------------- self-knowledge
SK_A=['Nora had 30 shells. She gave 8 shells to her cousin. How many shells does she have left?',
      'Owen had 12 stamps. He gave 5 stamps to his sister. How many stamps does he have left?',
      'Pia had 24 muffins. She gave 9 muffins to her friend. How many muffins does she have left?']
# the problem it meets alone is read the same way as the three its parents confirmed (reader_en:holding). Since the fusion with
# the adaptive-life line, 'gave 15 beads to Ann' (to a name) is read first by its episodic stock reader, another way of reading,
# for which it rightly says its parents have not checked it yet (experience of one way is not counted for another)
SK_A_ALONE=('Kim had 40 beads. She gave 15 beads to her friend. How many beads does she have left?','25')
SK_B=['Rosa has 6 more crayons than Ivan. Ivan has 15 crayons. How many crayons does Rosa have?',
      'Lena has 12 more stamps than Omar. Omar has 20 stamps. How many stamps does Lena have?']
SK_B_ALONE=('Kai has 7 more shells than Ivy. Ivy has 11 shells. How many shells does Kai have?','18')
SK_B_AGAIN=['Tia has 6 more pens than Max. Max has 14 pens. How many pens does Tia have?',
            'Ben has 9 more cards than Sue. Sue has 13 cards. How many cards does Ben have?',
            'Ada has 4 more kites than Eli. Eli has 8 kites. How many kites does Ada have?']
def _llm_reading(spec,flip=False):
    """the reading of the child's own reader, as a parent would send it; flip: 'x = y + d' read as 'x + d = y' (valid for
    the checker, another answer: a reading two parents may agree on against the child's)"""
    import re as _re
    facts=[{'eq':f['eq'],'span':f.get('span',''),'known':f.get('known','')} for f in spec['facts']]
    if flip:
        m=_re.fullmatch(r'\s*(\w+)\s*=\s*(\w+)\s*\+\s*(\w+)\s*',facts[-1]['eq'])
        facts[-1]['eq']=f'{m.group(1)} + {m.group(3)} = {m.group(2)}'
    return {'readable':True,'quantities':spec['quantities'],'facts':facts,'ask':spec['ask'],'answer_unit':spec.get('answer_unit',''),'unused':spec.get('unused') or []}

def m_self_knowledge(cli,work,ctx):
    from tukuyo_g4 import reader
    d=work/'sk';new_child(cli,d,'sk');fresh=work/'sk_fresh';new_child(cli,fresh,'skf')
    rec=work/'sk_parents.jsonl';lines=[]
    for t in SK_A+SK_B_AGAIN:lines+=[_read_line(p,t,_llm_reading(reader.read(t)['spec'])) for p in PARENTS]
    for t in SK_B:lines+=[_read_line(p,t,_llm_reading(reader.read(t)['spec'],flip=True)) for p in PARENTS]
    rec.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    log=[]
    def solve(dd,t,alone=False):
        r=cli(dd,'g4-solve',*(['--llm','off'] if alone else []),'--',t,replay=None if alone else rec)
        log.append({'text':t[:40],'alone':alone,'answer':r.get('answer'),'route':r.get('route'),'reason':r.get('reason'),
                    'asked':sorted({x.get('parent') for x in r.get('readings') or [] if x.get('parent')}),'life':[x['kind'] for x in r.get('life') or []]})
        return r
    for t in SK_A:solve(d,t)
    contradicted=[solve(d,t) for t in SK_B]
    doubt=solve(d,SK_B_ALONE[0],alone=True);still=solve(d,SK_A_ALONE[0],alone=True)
    me=cli(d,'g4-self');fresh_r=solve(fresh,SK_B_ALONE[0],alone=True)
    cli(d,'soul-forget-surface');me2=cli(d,'g4-self')
    for t in SK_B_AGAIN:solve(d,t)
    again=solve(d,SK_B_ALONE[0],alone=True)
    au=audits(cli,d)
    know=me.get('self_knowledge') or {}
    def skill(name):return next((v for k,v in know.items() if k.endswith(':'+name)),{})
    hold,comp=skill('holding'),skill('compare')
    ev=[e for e in g4_events(d) if str(e.get('relation','')).startswith('self:')]
    checks={'asks_the_other_parents_when_contradicted':all(set(PARENTS)<=set(x['asked']) for x in log if x['text'] in [t[:40] for t in SK_B] and not x['alone']),
            'knows_what_it_is_good_at':(hold.get('confirmed') or 0)>=3 and not hold.get('doubted',True),
            'knows_where_it_was_wrong':(comp.get('contradicted') or 0)>=2 and bool(comp.get('doubted')),
            'holds_back_where_it_was_contradicted':doubt.get('answer') is None and 'SELF_DOUBT' in str(doubt.get('reason')),
            'still_answers_what_it_knows':still.get('answer')==SK_A_ALONE[1],
            'the_humility_is_its_own':fresh_r.get('answer')==SK_B_ALONE[1],
            'self_knowledge_survives_forgetting':bool(know) and me2.get('self_knowledge')==know,
            'trusts_itself_again_when_confirmed':again.get('answer')==SK_B_ALONE[1],
            'in_its_soul_under_its_law':bool(ev) and all(e.get('law')==3 for e in ev),
            'audits_pass':all(x['ok'] for x in au.values())}
    return {'ok':all(checks.values()),'checks':checks,'self_knowledge':know,'after_forgetting':me2.get('self_knowledge'),
            'held_back':{k:doubt.get(k) for k in ('answer','reason')},'log':log,'audits':au,'self_events':len(ev)}

# ----------------------------------------------------------------------------- inner life
def m_inner_life(cli,work,ctx):
    from tukuyo_g4 import reader
    d=work/'il';new_child(cli,d,'il')
    rec=work/'il_parents.jsonl';lines=[]
    # the life: T5, which Claude and Gemini read to different answers (kept to look back on), and two comparisons that all
    # its parents read otherwise than the child (its own way of reading comes into doubt)
    lines+=[_read_line('claude',T5,R5),_read_line('gemini',T5,OTHER5)]
    for t in SK_B:lines+=[_read_line(p,t,_llm_reading(reader.read(t)['spec'],flip=True)) for p in PARENTS]
    rec.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    cli(d,'think','--',T5,replay=rec)
    for t in SK_B:cli(d,'g4-solve','--',t,replay=rec)
    ev0=len(soul_events(d))
    look=cli(d,'g4-reflect')
    ev1=len(soul_events(d))
    nobody=cli(d,'g4-reflect','--act')                                   # no parent configured: nobody is asked
    ev2=len(soul_events(d))
    # later, its parents read again: now all three read T5 alike (Gemini differently than before), and they read the
    # comparisons as the child does
    rec2=work/'il_parents_later.jsonl'
    lines2=[_read_line(p,T5,R5) for p in PARENTS]
    for t in SK_B:lines2+=[_read_line(p,t,_llm_reading(reader.read(t)['spec'])) for p in PARENTS]
    rec2.write_text('\n'.join(lines2)+'\n',encoding='utf-8')
    acted=cli(d,'g4-reflect','--act',replay=rec2)
    after=cli(d,'g4-reflect');me=cli(d,'g4-self')
    au=audits(cli,d)
    texts=lambda o:[x.get('text') for x in (o.get('intentions') or [])]
    know=me.get('self_knowledge') or {}
    comp=next((v for k,v in know.items() if k.endswith(':compare')),{})
    story=(me.get('life_story') or {}).get('looked_back') or {}
    checks={'knows_its_open_questions':T5 in texts(look) and any(t in texts(look) for t in SK_B) and any(str(x.get('skill','')).endswith(':compare') for x in look.get('intentions') or []),
            'looking_changes_nothing_by_itself':ev1==ev0,
            'asks_nobody_without_parents':ev2==ev1 and not nobody.get('acted') and bool(nobody.get('note')),
            'acts_on_its_own_questions':bool(acted.get('acted')) and T5 not in texts(after),
            'who_was_right_is_looked_back_on':(story.get('claude') or {}).get('right',0)>=1 and (story.get('gemini') or {}).get('wrong',0)>=1,
            'its_doubt_is_checked_again':(comp.get('confirmed') or 0)>=1,
            'audits_pass':all(x['ok'] for x in au.values())}
    return {'ok':all(checks.values()),'checks':checks,'intentions':look.get('intentions'),'acted':acted.get('acted'),'after':after.get('intentions'),
            'note_without_parents':nobody.get('note'),'self_knowledge':know,'looked_back':story,'audits':au,
            'errors':[x.get('cli_error') for x in (look,nobody,acted,after) if x.get('cli_error')]}

# ----------------------------------------------------------------------------- its own voice
OV_UNREAD='Mia had some shells. She found 4 more shells on the beach. How many shells does she have now?'
def _numbers(s):
    import re as _re
    return set(_re.findall(r'(?<![\w/.])\d+(?:/\d+)?(?:\.\d+)?(?![\w/])',str(s)))

def m_own_voice(cli,work,ctx):
    """the child says in its own words how it read a problem and what it calculated, how sure it is and why, and why it
    holds back; what it says comes from what it did and from its own record (no parent writes it)"""
    from tukuyo_g4 import reader,numbers as N
    d=work/'ov';new_child(cli,d,'ov');fresh=work/'ov_fresh';new_child(cli,fresh,'ovf')
    rec=work/'ov_parents.jsonl';lines=[]
    for t in SK_A:lines+=[_read_line(p,t,_llm_reading(reader.read(t)['spec'])) for p in PARENTS]
    for t in SK_B:lines+=[_read_line(p,t,_llm_reading(reader.read(t)['spec'],flip=True)) for p in PARENTS]
    rec.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    with_parents=[cli(d,'g4-solve','--',t,replay=rec) for t in SK_A]
    for t in SK_B:cli(d,'g4-solve','--',t,replay=rec)
    know=cli(d,'g4-self').get('self_knowledge') or {}
    alone=cli(d,'g4-solve','--llm','off','--',SK_A_ALONE[0]);again=cli(d,'g4-solve','--llm','off','--',SK_A_ALONE[0])
    first=cli(fresh,'g4-solve','--llm','off','--',SK_A_ALONE[0])
    doubt=cli(d,'g4-solve','--llm','off','--',SK_B_ALONE[0]);unread=cli(d,'g4-solve','--llm','off','--',OV_UNREAD)
    au=audits(cli,d)
    V=lambda r:r.get('voice') or {}
    hold=next((v for k,v in know.items() if k.endswith(':holding')),{});comp=next((v for k,v in know.items() if k.endswith(':compare')),{})
    counts={str(v.get(k,0)) for v in know.values() for k in ('confirmed','contradicted')}
    def grounded(r,text):
        """every number it says is a number of the problem, a value of its reading, what it would have answered, or a
        count of its own record"""
        said=V(r).get('said')
        if not said:return False
        ok={x for n in N.find(text) for x in (n.raw,str(n.value))}|counts|{str(r.get('withheld'))}
        for x in r.get('readings') or []:ok|={str(v) for v in (x.get('values') or {}).values()}
        return _numbers(said)<=ok
    def spans_from_the_text(r,text):
        import re as _re
        q=[m.group(1) for line in V(r).get('read') or [] for m in _re.finditer(r'"([^"]+)"',line)]
        return bool(q) and all(x in text for x in q)
    rs=[alone,again,first,doubt,unread]
    said=[V(r).get('said') or '' for r in rs+with_parents]
    checks={'explains_how_it_read_and_calculated':len(V(alone).get('read') or [])>=3 and spans_from_the_text(alone,SK_A_ALONE[0])
                                                    and SK_A_ALONE[1] in (V(alone).get('read') or [''])[-1],
            'says_its_answer':str(V(alone).get('answer','')).startswith(SK_A_ALONE[1]) and alone.get('answer')==SK_A_ALONE[1],
            'says_how_sure_from_its_record':V(alone).get('sure')=='sure' and bool(hold) and f"{hold.get('confirmed')} time" in str(V(alone).get('why')),
            'its_assurance_is_its_own':V(first).get('sure')=='fairly sure' and 'not checked' in str(V(first).get('why')) and V(first).get('read')==V(alone).get('read'),
            'says_who_read_it_the_same_way':all(r.get('route')=='own+llm' and 'claude' in str(V(r).get('why')).lower() and V(r).get('sure')=='sure' for r in with_parents),
            'says_why_it_holds_back':doubt.get('answer') is None and SK_B_ALONE[1] in str(V(doubt).get('held_back')) and bool(comp)
                                     and f"otherwise {comp.get('contradicted')} times" in str(V(doubt).get('held_back'))
                                     and unread.get('answer') is None and bool(V(unread).get('held_back')) and V(unread).get('held_back')!=V(doubt).get('held_back'),
            'every_number_it_says_is_grounded':all(grounded(r,t) for r,t in zip(rs,[SK_A_ALONE[0],SK_A_ALONE[0],SK_A_ALONE[0],SK_B_ALONE[0],OV_UNREAD])),
            'speaks_as_itself':all(x and life.voice_check(x)['speaks_as_tukuyo'] for x in said)
                               and not any(x.get('parent') for r in rs for x in r.get('readings') or []),
            'the_same_thought_in_the_same_words':bool(V(alone).get('said')) and V(alone).get('said')==V(again).get('said'),
            'audits_pass':all(x['ok'] for x in au.values())}
    return {'ok':all(checks.values()),'checks':checks,'self_knowledge':know,
            'said':{'alone':V(alone).get('said'),'first_time':V(first).get('said'),'held_back':V(doubt).get('said'),'unread':V(unread).get('said'),
                    'with_parents':V(with_parents[0]).get('said') if with_parents else None},'audits':au}

# ----------------------------------------------------------------------------- noticing its own growth
GR_STORY='Sam is 4 years older than his sister. In 3 years, the sum of their ages will be 30. How old is Sam now?'
GR_OWN=('A bike costs $200. It is on sale for 25% off. How much does the bike cost on sale?','150')
def _fsha(p):
    p=Path(p);return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None

def m_growth(cli,work,ctx):
    """the child keeps what it could not read alone, knows its weak spots and says what it wants to learn; when it can read
    alone what it could not (a wording its parents taught it, or its own reader reads it now), it notices, says so, and
    its soul keeps it"""
    d=work/'gr';new_child(cli,d,'gr');fresh=work/'gr_fresh';new_child(cli,fresh,'grf')
    rec=work/'gr_parents.jsonl';rec.write_text('\n'.join(_read_line(p,T,R) for p in PARENTS)+'\n',encoding='utf-8')
    # alone, it meets three problems it cannot read: a question asked in a way it does not know (T2), a story it does not
    # know how to put together, and a story in which an amount is not given; then T2 again
    met=[cli(d,'g4-solve','--llm','off','--',t) for t in (T2,GR_STORY,OV_UNREAD)]
    again=cli(d,'g4-solve','--llm','off','--',T2)
    me0=cli(d,'g4-self');g0=me0.get('growth') or {}
    ev0=len(soul_events(d));st0=_fsha(d/'g4'/'unread.json')
    look0=cli(d,'g4-reflect');g0b=cli(d,'g4-self').get('growth') or {}
    ev1=len(soul_events(d));st1=_fsha(d/'g4'/'unread.json')
    # its parents teach it T, the wording of T2 with other numbers
    cli(d,'think','--',T,replay=rec)
    me1=cli(d,'g4-self');g1=me1.get('growth') or {};grew1=[e for e in g4_events(d) if e.get('theme')=='g4:grew']
    look1=cli(d,'g4-reflect');now=cli(d,'g4-solve','--llm','off','--',T2)
    # a child without that past learns the same wording
    cli(fresh,'think','--',T,replay=rec);first=cli(fresh,'g4-solve','--llm','off','--',T2)
    fresh_grew=[e for e in g4_events(fresh) if e.get('theme')=='g4:grew']
    # its own reader grew: a later version of the child reads a problem an earlier version could not (kept as that version
    # kept it, with the reason its reader gave then)
    try:
        from tukuyo_g4 import growth
        from tukuyo_g4.learn import Store
        from tukuyo_v977.whole_state import sync
        growth.Unread(d).keep(GR_OWN[0],Store.key_of(GR_OWN[0]),'story','EN:NO_SCHEMA',None);sync(d)
        own=cli(d,'g4-solve','--llm','off','--',GR_OWN[0])
    except Exception as e:  # noqa: BLE001 - before the change there is no record to keep it in
        own={'error':type(e).__name__+':'+str(e)}
    grew2=[e for e in g4_events(d) if e.get('theme')=='g4:grew']
    meB=cli(d,'g4-self');cli(d,'soul-forget-surface');meA=cli(d,'g4-self')
    au=audits(cli,d)
    # a forged record of its growth: every problem marked as read, the seal recomputed
    forged=work/'gr_forged';shutil.copytree(d,forged);p=forged/'g4'/'unread.json';note='no record to forge'
    if p.is_file():
        o=json.loads(p.read_text(encoding='utf-8'))
        for e in (o.get('entries') or {}).values():e['grown']={'seq':1,'how':'own','value':'0'}
        o['sha256']=sha(o.get('entries') or {});p.write_text(json.dumps(o,ensure_ascii=False,sort_keys=True),encoding='utf-8');note='every problem marked as read'
    fa=audits(cli,forged,('whole-audit','g4-audit'));fs=cli(forged,'g4-self')
    V=lambda r:r.get('voice') or {}
    ws=g0.get('weak_spots') or [];wants=g0.get('wants_to_learn') or []
    learn=lambda o:[x.get('text') for x in (o.get('intentions') or []) if x.get('do')=='learn_to_read']
    story=lambda m:(m.get('life_story') or {})
    checks={'keeps_what_it_could_not_read':all(r.get('answer') is None for r in met) and g0.get('could_not_read')==3 and g0.get('can_read_now')==0
                                            and not V(met[0]).get('before') and 'before' in str(V(again).get('before')),
            'knows_its_weak_spots':{q.get('kind'):q.get('problems') for q in ws}=={'question':1,'story':1,'missing':1} and all(q.get('what') for q in ws),
            'says_what_it_wants_to_learn':{q.get('kind') for q in wants}=={'question','story'} and T2 in learn(look0) and OV_UNREAD not in learn(look0),
            'looking_changes_nothing':ev1==ev0 and st1==st0 and bool(g0) and g0==g0b,
            'notices_when_it_has_grown':len(grew1)==1 and g1.get('can_read_now')==1 and (g1.get('grew') or {}).get('learned_from_parents')==1
                                        and T2 not in learn(look1) and {q.get('kind') for q in g1.get('weak_spots') or []}=={'story','missing'},
            'says_it_could_not_read_it_before':now.get('answer')=='9' and 'before' in str(V(now).get('before')) and 'Claude' in str(V(now).get('before'))
                                               and str(V(now).get('before')) in str(V(now).get('said')),
            'its_growth_is_its_own':first.get('answer')=='9' and not fresh_grew and not V(first).get('before'),
            'notices_its_own_reader_grew':own.get('answer')==GR_OWN[1] and 'own reader' in str(V(own).get('before')) and len(grew2)==2
                                          and ((meB.get('growth') or {}).get('grew') or {}).get('own_reader')==1,
            'remembers_after_forgetting':bool(meB.get('growth')) and meA.get('growth')==meB.get('growth') and story(meA).get('grew')==story(meB).get('grew')==2
                                         and any('grown' in x for x in story(meA).get('told') or []),
            'a_forged_record_is_refused':note!='no record to forge' and not fa['g4-audit']['ok'] and bool((fs.get('refused') or {}).get('unread')),
            'audits_pass':all(x['ok'] for x in au.values())}
    return {'ok':all(checks.values()),'checks':checks,'growth_before':g0,'growth_after_learning':g1,'growth_end':meB.get('growth'),
            'said':{'again':V(again).get('said'),'now':V(now).get('said'),'own_reader':V(own).get('said'),'fresh':V(first).get('said')},
            'reflect_before':look0.get('intentions'),'reflect_after':look1.get('intentions'),'life_story':story(meA).get('told'),
            'forged':{'note':note,'audits':fa,'refused':fs.get('refused')},'own_reader_case':{k:own.get(k) for k in ('answer','route','reason','error')},'audits':au}

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

MEASURES={'continuity':m_continuity,'crash':m_crash,'forgetting':m_forgetting,'individuality':m_individuality,'long_life':m_long_life,'close_parents':m_close_parents,
          'integrity':m_integrity,'self':m_self,'self_knowledge':m_self_knowledge,'inner_life':m_inner_life,'own_voice':m_own_voice,'growth':m_growth}

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
