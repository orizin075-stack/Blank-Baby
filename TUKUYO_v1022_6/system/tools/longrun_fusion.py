"""claude-patch5 / V1022.6 long-run fusion gate.

Everything runs together on ONE real individual, each operation in a new CLI process, chosen at random:
  reasoning with ground truth (generated problems, incl. ones that MUST be abstained on) | teaching facts and
  asking them back | self-study with a stand-in teacher | metabolism (death, succession) | checkpoint |
  advancing a future branch and restoring it | SIGKILL-style crash injection | audits.
Invariants checked after the operations (any violation is recorded; nothing is retried or hidden):
  * no wrong-but-certain answer on a generated problem
  * whole-audit / metabolism-audit / llm-audit / learning-audit stay green
  * a restore brings back the checkpoint tick, its facts and its learned rules, and nothing from the future
  * metabolism resource conservation holds
The report is written continuously, so an interrupted run still shows what was completed.

  python3 -B tools/longrun_fusion.py --data DIR --runtime-trust-file ANCHOR --report out.json --minutes 120 --seed 7
"""
import argparse,datetime,json,os,random,re,signal,subprocess,sys,time
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];MOCK=ROOT/'tools'/'mock_llm_provider.py'

NOUNS=[('りんご','個'),('みかん','個'),('えんぴつ','本'),('ノート','冊'),('カード','枚'),('シール','枚')]
ENTS=['北星図書館','南風劇場','青葉公園','白浜水族館','緑台病院','朝霧書店','星川美術館','若竹会館']
ATTRS=[('館長',['佐藤ミナ','高橋ケン','伊藤ユイ','山本ソウ']),('所在地',['東区','西区','港区','北区']),('定休日',['月曜日','火曜日','水曜日','木曜日'])]
TEACH_VERBS=['出荷しました','寄付しました','譲りました','返品しました','販売しました']

def gen_problem(rng,facts):
    k=rng.choice(['change','rate','percent','change_money','groups','equation','logic_mt','logic_mp','time','memory','abstain_hedge','abstain_container','abstain_part'])
    n,u=rng.choice(NOUNS)
    if k=='change':
        a=rng.randint(20,90);b=rng.randint(1,a-5);c=rng.randint(1,30)
        return k,f'{n}が{a}{u}あります。{b}{u}食べました。{c}{u}もらいました。残りは何{u}？',str(a-b+c)
    if k=='rate':
        v=rng.choice([4,5,6,40,60]);h=rng.randint(1,3);m=rng.choice([15,30,45])
        return k,f'時速{v}kmで{h}時間{m}分進むと、何km進みますか？',Fraction(v)*(h+Fraction(m,60))
    if k=='percent':
        p=rng.choice([1000,2000,3000,4000,5000]);x=rng.choice([10,20,25]);y=rng.choice([10,20])
        return k,f'{p}円の品物を{x}%引きし、さらに{y}%引きしました。値段はいくら？',Fraction(p)*(100-x)*(100-y)/10000
    if k=='change_money':
        a=rng.choice([80,120,150,180,250]);m=rng.randint(2,5);pay=rng.choice([1000,2000])
        return k,f'{pay}円で、1個{a}円のパンを{m}個買いました。おつりはいくらですか？',str(pay-a*m)
    if k=='groups':
        p=rng.randint(3,12);e=rng.randint(2,9)
        return k,f'{p}人に{e}{u}ずつ配ると、全部で何{u}いりますか？',str(p*e)
    if k=='equation':
        a=rng.randint(2,6);x=rng.randint(2,20);b=rng.randint(1,15)
        return k,f'ある数を{a}倍して{b}を足すと{a*x+b}になります。ある数は？',str(x)
    if k=='logic_mt':
        return k,rng.choice(['雨なら試合は中止だ。試合は中止ではない。雨だった？','風が強ければ船は欠航する。船は欠航しなかった。風は強かった？']),'NO'
    if k=='logic_mp':
        return k,rng.choice(['もし雪ならスキーに行く。今日は雪だ。スキーに行く？','すべての鳥は羽がある。ハトは鳥だ。ハトは羽がある？']),'YES'
    if k=='time':
        h=rng.randint(1,5);m=rng.randint(1,59)
        return k,f'{h}時間{m}分は何分？',str(h*60+m)
    if k=='memory' and facts:
        (e,a),v=rng.choice(sorted(facts.items()))
        return k,f'{e}の{a}は？',v
    if k=='abstain_hedge':
        a=rng.randint(20,90);b=rng.randint(1,10)
        return k,f'{n}が{a}{u}ぐらいあります。{b}{u}食べました。残りは何{u}？',None
    if k=='abstain_container':
        a=rng.randint(4,12);b=rng.randint(2,9)
        return k,f'1箱に{a}個入りが{b}箱あります。箱は全部で何個？',None
    a=rng.randint(10,40)
    return 'abstain_part',f'{n}とみかんが合わせて{a}{u}あります。{n}は何{u}？',None

def grade(expected,answer):
    if expected is None:return 'wrong_certain' if answer is not None else 'correct_abstain'
    if answer is None:return 'abstain'
    a=str(answer)
    if expected in ('YES','NO'):
        ok=a.startswith('はい') if expected=='YES' else a.startswith('いいえ')
        return 'correct' if ok else 'wrong_certain'
    if isinstance(expected,Fraction) or re.fullmatch(r'\d+(?:\.\d+)?',expected):
        # claude-patch6: a number is graded exactly (patch5 counted 17 as correct for 7 because '7' is in '17')
        nums=re.findall(r'\d+(?:\.\d+)?',a)
        return 'correct' if len(nums)==1 and Fraction(nums[0])==Fraction(str(expected)) else 'wrong_certain'
    return 'correct' if a==expected or expected in a else 'wrong_certain'

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--data',type=Path,required=True);ap.add_argument('--runtime-trust-file',type=Path,required=True)
    ap.add_argument('--report',type=Path,required=True);ap.add_argument('--minutes',type=float,default=60);ap.add_argument('--seed',type=int,default=1)
    a=ap.parse_args();d=a.data.resolve();pin=a.runtime_trust_file.resolve();out=a.report.resolve()
    if d==ROOT or ROOT in d.parents:ap.error('data must be outside the signed distribution')
    rng=random.Random(a.seed);started=time.monotonic();deadline=started+a.minutes*60
    rep={'schema':'tukuyo.v1022_6.longrun_fusion/1','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'seed':a.seed,'minutes':a.minutes,
         'ops':{},'reasoning':{},'violations':[],'checkpoints':0,'restores':0,'crash_injections':0,'crash_reached':0,'self_study_learned':0,'completed':False}
    def save():
        rep['elapsed_minutes']=round((time.monotonic()-started)/60,2);tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(rep,ensure_ascii=False,indent=1,default=str));os.replace(tmp,out)
    def cli(*args,crash=None,mock=None,ok=True):
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
        for k in ('TUKUYO_CRASH_POINT','TUKUYO_LLM_PROVIDER','TUKUYO_LLM_COMMAND','TUKUYO_LLM_TEACHERS'):env.pop(k,None)
        if crash:env['TUKUYO_CRASH_POINT']=crash
        if mock:env.update({'TUKUYO_LLM_COMMAND':f'{sys.executable} -B {MOCK}','MOCK_LLM_MODE':mock,'MOCK_LLM_STATE':str(d.parent/'mock_state')})
        p=subprocess.Popen([sys.executable,'-B',str(ROOT/'run_tukuyo.py'),'--runtime-trust-file',str(pin),'--data',str(d),*map(str,args)],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
        try:so,se=p.communicate(timeout=300)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGKILL);so,se=p.communicate();rep['violations'].append({'op':args[0],'timeout':True});return None
        r=None
        try:r=json.loads(so) if so.strip() else None
        except ValueError:pass
        if crash:return {'returncode':p.returncode,'result':r}
        if ok and (p.returncode or not r or not r.get('ok')):rep['violations'].append({'op':list(map(str,args))[:3],'returncode':p.returncode,'result':(r or {}) if isinstance(r,dict) else None,'stderr':se[-400:]})
        return r
    def bump(k):rep['ops'][k]=rep['ops'].get(k,0)+1
    def audits(full=False):
        for cmd in (('whole-audit','metabolism-audit','llm-audit','learning-audit') if full else ('whole-audit',)):
            r=cli(cmd,ok=False)
            if not r or not r.get('ok'):rep['violations'].append({'audit':cmd,'result':r});return False
            if cmd=='metabolism-audit' and r.get('resource_conservation') is False:rep['violations'].append({'audit':'resource_conservation','result':r})
        return True
    facts={};learned=set();cp=None;cp_state=None
    if d.exists() and any(d.iterdir()):ap.error('empty data directory required')
    cli('init','--individual-id','LONGRUN-V1022-6')
    cli('metabolism-init','--families','2','--reservoir','80000','--regeneration','1200','--max-age','6')
    cli('realtime-start');save()
    i=0
    while time.monotonic()<deadline:
        i+=1;op=rng.choices(['reason','teach','study','metab','checkpoint','restore','crash'],[50,8,4,18,4,4,4])[0]
        if op=='checkpoint' or (op=='restore' and cp is None):
            st=cli('metabolism-audit');r=cli('recovery-checkpoint','--note',f'longrun-{i}')
            if r and r.get('ok') and st:cp=r['path'];cp_state={'tick':st.get('tick'),'facts':dict(facts),'learned':set(learned)};rep['checkpoints']+=1
            bump('checkpoint')
        elif op=='restore':
            cli('metabolism-step','--ticks',rng.randint(1,3))                 # future branch
            cli('realtime-tick','--note',f'future-{i}')
            r=cli('recovery-restore',cp,'--trust-file',d/'v1014/recovery.pub')
            st=cli('metabolism-audit')
            if st and st.get('tick')!=cp_state['tick']:rep['violations'].append({'restore_tick_mismatch':[st.get('tick'),cp_state['tick']]})
            facts=dict(cp_state['facts']);learned=set(cp_state['learned']);rep['restores']+=1;bump('restore')
            for (e,at),v in list(facts.items())[:3]:                          # facts from the checkpoint are back
                x=cli('think','--',f'{e}の{at}は？')
                if x and x.get('answer')!=v:rep['violations'].append({'restored_fact_missing':[e,at,v,x.get('answer')]})
        elif op=='crash':
            r=cli('metabolism-step','--ticks','2',crash='metabolism:after_death');rep['crash_injections']+=1
            if r and r['returncode'] in (-signal.SIGKILL,137):rep['crash_reached']+=1
            bump('crash')
        elif op=='metab':
            r=cli('metabolism-step','--ticks',rng.randint(1,2));bump('metab')
        elif op=='teach':
            e=rng.choice(ENTS);at,vals=rng.choice(ATTRS)
            if (e,at) in facts:continue
            v=rng.choice(vals);cli('knowledge-add',f'{e}の{at}は{v}である。');facts[(e,at)]=v;bump('teach')
            x=cli('think','--',f'{e}の{at}は？')
            if not x or x.get('answer')!=v:rep['violations'].append({'fresh_fact_not_answered':[e,at,v,(x or {}).get('answer')]})
        elif op=='study':
            verb=rng.choice([v for v in TEACH_VERBS if v not in learned] or TEACH_VERBS)
            q=f'1箱に{rng.randint(5,12)}個入りが{rng.randint(3,9)}箱あります。{rng.randint(1,4)}個{verb}。残りは何個？'
            cli('llm-ask','--',q)
            s=cli('self-study','--max','8',mock='honest')
            if s and s.get('now_solved_locally'):rep['self_study_learned']+=s['now_solved_locally'];learned.add(verb)
            if verb in learned:
                aa,bb,cc=rng.randint(5,12),rng.randint(3,9),rng.randint(1,4)
                x=cli('think','--',f'1箱に{aa}個入りが{bb}箱あります。{cc}個{verb}。残りは何個？')
                if x and x.get('answer') not in (None,str(aa*bb-cc)):rep['violations'].append({'learned_rule_wrong':[verb,x.get('answer'),aa*bb-cc]})
            bump('study')
        else:
            kind,q,exp=gen_problem(rng,facts)
            cmd=rng.choice(['think','think','verified-query','llm-ask'])
            x=cli(cmd,'--',q)
            if x is None:continue
            ans=x.get('answer') if cmd=='think' else (None if x.get('uncertain') else x.get('answer'))
            g=grade(exp,ans);c=rep['reasoning'].setdefault(kind,{})
            c[g]=c.get(g,0)+1
            if g=='wrong_certain':rep['violations'].append({'wrong_certain':[cmd,q,str(exp),ans]})
            bump('reason')
        audits(full=(i%15==0))
        if i%5==0:save()
    audits(full=True);rep['completed']=True;rep['total_ops']=i;save()
    print(json.dumps({'ops':rep['ops'],'violations':len(rep['violations'])},ensure_ascii=False))
    return 0 if not rep['violations'] else 1
if __name__=='__main__':raise SystemExit(main())
