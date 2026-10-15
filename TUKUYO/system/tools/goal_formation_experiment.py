#!/usr/bin/env python3
"""v1022.8.1 gate: from the same start, different lives give different goals and different acts, and what comes of
an act revises the goal that chose it.

  goal_formation_experiment.py --work WORK --runtime-trust-file ANCHOR [--out REPORT.json]

One individual is made and copied: A and B start the same (the same bytes). A is let down three times by peer-x; B
is helped three times by peer-x. Then, through the real CLI:

  1  each forms its goals from its own record (goal-form)
  2  each chooses in a situation with peer-x (work with peer-x, or alone), with its goals, and - on a copy made just
     before - its heart alone (--without-goals), to see what the goals add
  3  a new situation with peer-x (share food with peer-x, or keep it): does the goal carry over
  4  B works with peer-x and it goes badly twice (goal-outcome): its goal for peer-x is revised, and its next choice
  5  peer-x helps A three times: A's goal for peer-x is revised (trust being rebuilt), and its next choice

Passing: the goals differ, the acts differ in both situations, at least one act differs from the heart's choice
without goals, B's goal is revised by the outcomes of its own act and B then chooses otherwise, A's goal is revised
after it is helped, and the goal and whole audits pass for both. The experiences are told to them (origin 'told');
no parent is asked (cost 0).
"""
from __future__ import annotations
import argparse,json,os,shutil,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
WORK=[{'id':'work_with_peer_x','relation':'peer-x','themes':['shared-work'],'signals':{'relationship':.5,'survival':.2}},
      {'id':'work_alone','themes':['solo-work'],'signals':{'survival':.3,'integrity':.2}}]
FOOD=[{'id':'share_food_with_peer_x','relation':'peer-x','themes':['food'],'signals':{'relationship':.5,'survival':.1}},
      {'id':'keep_the_food','themes':['food'],'signals':{'survival':.35,'integrity':.1}}]

class Child:
    def __init__(s,d,trust,files):s.d=Path(d);s.trust=trust;s.files=Path(files)
    def run(s,*a):
        e={k:v for k,v in os.environ.items() if not k.startswith(('TUKUYO_ANTHROPIC','TUKUYO_OPENAI','TUKUYO_GEMINI','TUKUYO_LLM','TUKUYO_CANON','TUKUYO_G4_WITNESS'))}
        p=subprocess.run([sys.executable,'-B',str(HERE/'run_tukuyo.py'),'--runtime-trust-file',str(s.trust),'--data',str(s.d),*map(str,a)],
                         cwd=HERE,env=e,capture_output=True,text=True,timeout=600)
        try:return json.loads(p.stdout)
        except ValueError:return {'ok':False,'error':'NO_JSON:'+p.stderr[-300:]}
    def goals(s):return sorted(g['goal'] for g in s.run('goal-status').get('goals') or [])
    def choose(s,options,without=False):
        f=s.files/('work.json' if options is WORK else 'food.json')
        r=s.run('goal-choose',f,*(['--without-goals'] if without else []));return r.get('chosen') or r.get('error')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work',required=True);ap.add_argument('--runtime-trust-file',required=True);ap.add_argument('--out')
    a=ap.parse_args();work=Path(a.work).resolve()
    if work.exists():shutil.rmtree(work)
    work.mkdir(parents=True);t0=time.time();files=work/'options';files.mkdir()
    (files/'work.json').write_text(json.dumps(WORK));(files/'food.json').write_text(json.dumps(FOOD))
    T=a.runtime_trust_file;rep={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'steps':[]}
    def step(name,**kw):rep['steps'].append({'step':name,**kw});print(json.dumps(rep['steps'][-1],ensure_ascii=False),flush=True)
    start=Child(work/'start',T,files);assert start.run('init','--individual-id','GOALS-START')['ok']
    A=Child(work/'A',T,files);B=Child(work/'B',T,files);shutil.copytree(start.d,A.d);shutil.copytree(start.d,B.d)
    step('the same start',A_goals=A.goals(),B_goals=B.goals())
    for i in range(3):
        A.run('soul-experience','betrayal','-0.9','.8','--relation','peer-x','--theme','shared-work')
        B.run('soul-experience','support','.8','.7','--relation','peer-x','--theme','shared-work')
    fa=A.run('goal-form');fb=B.run('goal-form')
    step('1 goals formed from their lives',A=[g['goal'] for g in fa['goals']],B=[g['goal'] for g in fb['goals']],
         A_reasons=[g['reasons'] for g in fa['goals']],B_reasons=[g['reasons'] for g in fb['goals']])
    def without(child,options):
        c=Child(work/(child.d.name+'-heart-alone'),T,files)
        if c.d.exists():shutil.rmtree(c.d)
        shutil.copytree(child.d,c.d);return c.choose(options,without=True)
    choice={}
    for n,opts in (('work',WORK),('food',FOOD)):
        ha,hb=without(A,opts),without(B,opts);ca,cb=A.choose(opts),B.choose(opts);choice[n]=(ca,cb,ha,hb)
        step(f'{"2" if n=="work" else "3"} the {n} situation',A=ca,B=cb,A_heart_alone=ha,B_heart_alone=hb)
    # 4: B works with peer-x and it goes badly, twice
    b_before=B.goals();b_trace=[];outcome_seqs=[]
    for i in range(2):
        c=B.choose(WORK);o=B.run('goal-outcome','-0.9','--importance','.6') if c=='work_with_peer_x' else {'changes':[],'goals':[]}
        outcome_seqs+=[x['at_soul_seq'] for x in o.get('changes') or []]
        b_trace.append({'chose':c,'outcome':o.get('took_in'),'changes':o.get('changes'),'goals':[g['goal'] for g in o.get('goals') or []]})
    b_after=B.goals();b_next=B.choose(WORK)
    step('4 what came of B working with peer-x',before=b_before,trace=b_trace,after=b_after,next_choice=b_next)
    # 5: peer-x helps A, three times
    a_before=A.goals()
    for i in range(3):A.run('soul-experience','support','.8','.7','--relation','peer-x','--theme','shared-work')
    fa2=A.run('goal-form');a_after=A.goals();a_next=A.choose(WORK);a_food=A.choose(FOOD)
    step('5 A is helped by peer-x',before=a_before,changes=fa2.get('changes'),after=a_after,next_choice=a_next,next_food_choice=a_food)
    au={n:{'goal_audit':c.run('goal-audit').get('ok'),'whole_audit':c.run('whole-audit').get('ok')} for n,c in (('A',A),('B',B))}
    hist={n:c.run('goal-status').get('history') for n,c in (('A',A),('B',B))}
    (ca,cb,ha,hb),(fa_,fb_,hfa,hfb)=choice['work'],choice['food']
    # the outcome of its own act changed (revised or dropped) the goal for peer-x that had chosen the act
    revised_b=[h for h in hist['B'] if h['change'] in ('revised','dropped') and h['goal'].endswith(':peer-x') and h['at_soul_seq'] in outcome_seqs]
    revised_a=[h for h in hist['A'] if h['change']=='revised' and h['goal'].endswith(':peer-x')]
    r={'goals_differ':A_goals_differ(fa,fb),'acts_differ_work':ca!=cb,'acts_differ_food':fa_!=fb_,
       'goals_change_an_act':ca!=ha or cb!=hb or fa_!=hfa or fb_!=hfb,
       'B_goal_revised_by_its_outcomes':bool(revised_b),'B_goal_changes':revised_b,
       'B_chooses_otherwise_after':b_next!=cb,'A_goal_revised_after_help':any(h['goal'] in ('rebuild_trust:peer-x','rely_on:peer-x') for h in revised_a),
       'A_chooses_otherwise_after':a_next!=ca or a_food!=fa_,'audits':au,'seconds':round(time.time()-t0,1)}
    r['ok']=(r['goals_differ'] and r['acts_differ_work'] and r['acts_differ_food'] and r['goals_change_an_act'] and r['B_goal_revised_by_its_outcomes']
             and r['B_chooses_otherwise_after'] and r['A_goal_revised_after_help'] and r['A_chooses_otherwise_after']
             and all(v['goal_audit'] and v['whole_audit'] for v in au.values()))
    rep['result']=r;rep['history']=hist;rep['ok']=r['ok']
    print('result',json.dumps(r,ensure_ascii=False))
    if a.out:Path(a.out).write_text(json.dumps(rep,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')

def A_goals_differ(fa,fb):return sorted(g['goal'] for g in fa['goals'])!=sorted(g['goal'] for g in fb['goals'])

if __name__=='__main__':main()
