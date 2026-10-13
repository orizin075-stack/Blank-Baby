#!/usr/bin/env python3
"""v1022.9 (a part of its gate): restore an individual 100 times and check, every time, that it is whole and still itself.

  restore_cycles.py --work WORK --runtime-trust-file ANCHOR [--cycles 100] [--out REPORT.json]

One individual, kept with a canon outside its data directory (TUKUYO_CANON, v1022.7.8). A recovery checkpoint is taken;
then each cycle changes the individual (a problem solved alone, its body rests), every fifth cycle also breaks one of
its signed files, and restores a checkpoint (the first one, or the latest; a new checkpoint every tenth cycle). After
each restore:

  the canon refuses the restored copy until the owner says it is the individual (CANON_BEHIND, identity-canon-adopt)
  whole-audit and soul-identity-audit pass
  the individual's id is the same, and its whole state is the one the checkpoint holds

It runs the real CLI. No parent is asked (cost 0). The real-time gates of v1022.9 (24 hours, 72 hours, 7 days) are not
run here.
"""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
QS=['Tom has 3 apples. He buys 4 more apples. How many apples does he have now?','Ann has 5 pens. She buys 2 more pens. How many pens does she have now?',
    'Ben has 9 cards. He loses 3 cards. How many cards does he have now?','Kim has 2 cats. She gets 1 more cat. How many cats does she have now?']

def run(trust,canon,d,*a):
    env={k:v for k,v in os.environ.items() if not k.startswith(('TUKUYO_ANTHROPIC','TUKUYO_OPENAI','TUKUYO_GEMINI','TUKUYO_LLM','TUKUYO_CANON','TUKUYO_G4_WITNESS'))}
    if canon:env['TUKUYO_CANON']=str(canon)
    p=subprocess.run([sys.executable,'-B',str(HERE/'run_tukuyo.py'),'--runtime-trust-file',str(trust),'--data',str(d),*map(str,a)],cwd=HERE,env=env,
                     capture_output=True,text=True,timeout=900)
    try:return json.loads(p.stdout)
    except ValueError:return {'ok':False,'error':'NO_JSON:'+p.stderr[-300:]}

def fsha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest() if Path(p).is_file() else None

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work',required=True);ap.add_argument('--runtime-trust-file',required=True)
    ap.add_argument('--cycles',type=int,default=100);ap.add_argument('--out');a=ap.parse_args()
    work=Path(a.work).resolve();work.mkdir(parents=True,exist_ok=True);d=work/'individual';canon=work/'canon';T=a.runtime_trust_file
    C=lambda *x:run(T,canon,d,*x)
    rep={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'cycles':[],'config':{'cycles':a.cycles}}
    t0=time.time()
    assert C('init','--individual-id','RESTORE-CYCLES')['ok'];C('organism2-init');C('g4-solve','--llm','off','--',QS[0])
    C('realtime-start','--target-seconds','3600');C('realtime-tick')       # a checkpoint needs the individual's real-time record
    ident=json.loads((d/'state'/'integration_state.json').read_text())['payload']['individual_id']
    def checkpoint(note):
        r=C('recovery-checkpoint','--note',note)
        if not r.get('path'):return {'error':r.get('error') or r.get('errors') or 'NO_CHECKPOINT'}
        return {'path':r['path'],'whole':fsha(d/'v977'/'UNIFIED_STATE.json')}
    first=checkpoint('first');latest=first
    if 'error' in first:
        rep['stopped']='FIRST_CHECKPOINT:'+str(first['error']);print(rep['stopped'])
        if a.out:Path(a.out).write_text(json.dumps(rep,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
        return
    for i in range(1,a.cycles+1):
        row={'cycle':i};c0=time.time()
        r1=C('g4-solve','--llm','off','--',QS[i%len(QS)]);r2=C('organism2-update','REST','--amount','0.1')
        row['changed']=bool(r1.get('ok',True) and r2.get('ok'))
        if i%5==0:
            (d/'v977'/'WHOLE_STATE.json').write_text('{"corrupt":true}\n');row['broke']='v977/WHOLE_STATE.json'
        cp=first if i%2 else latest
        rr=C('recovery-restore',cp['path']);row['restored']=bool(rr.get('restored'))
        before=C('whole-audit');row['canon_before_adopt']=before.get('errors')
        ad=C('identity-canon-adopt','--yes');row['adopted']=(ad.get('adopted') or {}).get('kind')
        wa=C('whole-audit');sa=C('soul-identity-audit')
        row['whole_audit']=wa.get('ok');row['soul_identity_audit']=sa.get('ok')
        row['same_id']=json.loads((d/'state'/'integration_state.json').read_text())['payload']['individual_id']==ident
        row['whole_state_is_the_checkpoint']=fsha(d/'v977'/'UNIFIED_STATE.json')==cp['whole']
        row['lives_after']=C('g4-solve','--llm','off','--',QS[0]).get('answer')=='7'
        if i%10==0:
            cp2=checkpoint(f'cycle {i}')
            if 'error' in cp2:row['checkpoint_error']=cp2['error']
            else:latest=cp2
        row['seconds']=round(time.time()-c0,1)
        row['ok']=all([row['restored'],row['adopted'] in ('restore','branch',None),row['whole_audit'],row['soul_identity_audit'],row['same_id'],
                       row['whole_state_is_the_checkpoint'],row['lives_after'],'checkpoint_error' not in row])
        rep['cycles'].append(row);print(json.dumps(row),flush=True)
    au=C('identity-canon-audit');rep['canon_audit']={k:au.get(k) for k in ('ok','state','lines','kinds','errors')}
    ok=[r['ok'] for r in rep['cycles']]
    rep['result']={'cycles':len(ok),'passed':sum(ok),'failed_cycles':[r['cycle'] for r in rep['cycles'] if not r['ok']],
                   'broken_and_restored':sum(1 for r in rep['cycles'] if r.get('broke') and r['ok']),'canon_chain_ok':au.get('ok'),
                   'seconds':round(time.time()-t0,1)}
    rep['ok']=rep['result']['passed']==len(ok) and bool(au.get('ok'))
    print('result',json.dumps(rep['result']),'ok',rep['ok'])
    if a.out:Path(a.out).write_text(json.dumps(rep,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')

if __name__=='__main__':main()
