#!/usr/bin/env python3
"""v1022.7.8 gate: an individual copied on purpose, a branch, a backup put back and a death - are they told apart?

  identity_branch_experiment.py --work WORK --runtime-trust-file ANCHOR [--out REPORT.json]

Every step runs the real CLI (run_tukuyo.py) on fresh individuals in WORK, twice: without a canon (as before v1022.7.8)
and with one kept outside the data directories (TUKUYO_CANON=WORK/canon). No parent is asked (cost 0).

  copy       an individual is copied; the original lives on, then the copy tries to
  branch     a copy lives on by itself without the canon, then comes back to it
  restore    a backup of the individual is put back in its place; the owner then says it is the individual
  death      the individual dies; a copy taken before its death tries to live on
  at_once    two copies run a command at the same moment
"""
from __future__ import annotations
import argparse,concurrent.futures,json,os,shutil,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
Q=['Tom has 3 apples. He buys 4 more apples. How many apples does he have now?','Ann has 5 pens. She buys 2 more pens. How many pens does she have now?',
   'Ben has 9 cards. He loses 3 cards. How many cards does he have now?','Kim has 2 cats. She gets 1 more cat. How many cats does she have now?']

def run(trust,canon,d,*a):
    env={k:v for k,v in os.environ.items() if not k.startswith(('TUKUYO_ANTHROPIC','TUKUYO_OPENAI','TUKUYO_GEMINI','TUKUYO_LLM','TUKUYO_CANON','TUKUYO_G4_WITNESS'))}
    if canon:env['TUKUYO_CANON']=str(canon)
    p=subprocess.run([sys.executable,'-B',str(HERE/'run_tukuyo.py'),'--runtime-trust-file',str(trust),'--data',str(d),*a],cwd=HERE,env=env,capture_output=True,text=True,timeout=600)
    try:r=json.loads(p.stdout)
    except ValueError:r={'ok':False,'error':'NO_JSON:'+p.stderr[-300:]}
    return r

def short(r):return {k:r.get(k) for k in ('ok','answer','error','state','errors') if k in r}

def scenario(work,trust,canon):
    out={};C=lambda d,*a:run(trust,canon,work/d,*a)
    def lives(d,i):r=C(d,'g4-solve','--llm','off','--',Q[i%len(Q)]);return r.get('answer') is not None and r.get('ok',True) is not False,short(r)
    assert C('a','init','--individual-id','BRANCH-GATE')['ok'];C('a','organism2-init')
    lives('a',0);shutil.copytree(work/'a',work/'backup')
    # copy
    shutil.copytree(work/'a',work/'copy')
    out['copy']={'original_lives_on':lives('a',1),'copy_tries':lives('copy',2),'copy_whole_audit':short(C('copy','whole-audit')),
                 'original_whole_audit':short(C('a','whole-audit'))}
    # branch: a copy lives on by itself, without the canon, then comes back
    shutil.copytree(work/'a',work/'branch')
    run(trust,None,work/'branch','g4-solve','--llm','off','--',Q[3]);run(trust,None,work/'branch','organism2-update','REST','--amount','0.2')
    out['branch']={'comes_back':lives('branch',0),'whole_audit':short(C('branch','whole-audit')),'original_lives_on':lives('a',2)}
    # restore: the backup put back in the individual's place
    shutil.copytree(work/'a',work/'before_restore');shutil.rmtree(work/'a');shutil.copytree(work/'backup',work/'a')
    out['restore']={'put_back_tries':lives('a',3),'adopt_look':short(C('a','identity-canon-adopt')),'adopt':C('a','identity-canon-adopt','--yes').get('adopted'),
                    'after_adopt_lives':lives('a',0),'the_newer_copy_tries':lives('before_restore',1)}
    # death: a copy taken before the individual died
    shutil.copytree(work/'a',work/'before_death')
    for _ in range(6):C('a','organism2-update','INJURY','--amount','1.0')
    out['death']={'dead_individual_tries':lives('a',2),'copy_from_before_death_tries':lives('before_death',3),
                  'copy_whole_audit':short(C('before_death','whole-audit')),'dead_whole_audit':short(C('a','whole-audit'))}
    # two copies at the same moment
    assert C('x','init','--individual-id','BRANCH-AT-ONCE')['ok'];C('x','organism2-init');shutil.copytree(work/'x',work/'y')
    with concurrent.futures.ThreadPoolExecutor(2) as ex:
        fx=ex.submit(lives,'x',0);fy=ex.submit(lives,'y',1);rx,ry=fx.result(),fy.result()
    out['at_once']={'x':rx,'y':ry,'then_x':lives('x',2),'then_y':lives('y',3)}
    if canon:
        alive='x' if out['at_once']['then_x'][0] else 'y'     # which of the two wrote its line first is not fixed
        out['canon_audit']={d:short(C(d,'identity-canon-audit')) for d in ('a',alive)}
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work',required=True);ap.add_argument('--runtime-trust-file',required=True);ap.add_argument('--out');a=ap.parse_args()
    work=Path(a.work).resolve();rep={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    for mode in ('without_canon','with_canon'):
        w=work/mode
        if w.exists():shutil.rmtree(w)
        w.mkdir(parents=True);canon=(work/(mode+'_canon')) if mode=='with_canon' else None
        if canon and canon.exists():shutil.rmtree(canon)
        rep[mode]=scenario(w,a.runtime_trust_file,canon)
    wc=rep['with_canon'];wo=rep['without_canon']
    rep['gate']={
      'without_canon_nothing_is_told':wo['copy']['copy_tries'][0] and wo['copy']['copy_whole_audit'].get('ok') and wo['death']['copy_from_before_death_tries'][0],
      'copy_refused':not wc['copy']['copy_tries'][0] and wc['copy']['original_lives_on'][0],
      'copy_reported_by_whole_audit':'CANON_BEHIND' in (wc['copy']['copy_whole_audit'].get('errors') or []),
      'branch_refused_as_branch':not wc['branch']['comes_back'][0] and 'CANON_BRANCH' in (wc['branch']['whole_audit'].get('errors') or []),
      'after_the_branch_the_individual_lives_on':wc['branch']['original_lives_on'][0],
      'restore_refused_until_adopted':not wc['restore']['put_back_tries'][0] and bool(wc['restore']['adopt']) and wc['restore']['after_adopt_lives'][0],
      'after_restore_the_newer_copy_refused':not wc['restore']['the_newer_copy_tries'][0],
      'copy_of_dead_refused':not wc['death']['copy_from_before_death_tries'][0] and 'CANON_DEAD' in (wc['death']['copy_whole_audit'].get('errors') or []),
      'dead_individual_itself_audits_clean':wc['death']['dead_whole_audit'].get('ok') is True,
      'at_once_one_lives_on':[wc['at_once']['then_x'][0],wc['at_once']['then_y'][0]].count(True)==1,
      'canon_chain_valid':bool(wc.get('canon_audit')) and all(v.get('ok') and v.get('state') in ('IN_SYNC','DEAD_SELF') for v in wc['canon_audit'].values()),
    }
    rep['ok']=all(rep['gate'].values())
    print(json.dumps(rep['gate'],indent=1));print('ok',rep['ok'])
    if a.out:Path(a.out).write_text(json.dumps(rep,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')

if __name__=='__main__':main()
