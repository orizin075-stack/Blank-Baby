"""Reproducible process-boundary restore gate for actual multi-generation life.

Every operation starts a new CLI process. No network/LLM or accelerated-time
claim is involved. The external report supports resuming completed cycles.
"""
import argparse,datetime,hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXCLUDE={'private','recovery_checkpoints','recovery_blobs','.lineage_transaction','__pycache__','.pytest_cache'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def key_hashes(d):
    return {p.relative_to(d).as_posix():sha(p) for p in d.rglob('*.key')
            if not {'.lineage_transaction','retired_runtimes'}&set(p.relative_to(d).parts)}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--data',type=Path,required=True)
    ap.add_argument('--runtime-trust-file',type=Path,required=True)
    ap.add_argument('--report',type=Path,required=True)
    ap.add_argument('--cycles',type=int,default=100)
    ap.add_argument('--families',type=int,default=4)
    ap.add_argument('--generations',type=int,default=3)
    ap.add_argument('--mutate-ticks',type=int,default=4)
    a=ap.parse_args();d=a.data.resolve();out=a.report.resolve();pin=a.runtime_trust_file.resolve()
    if not 1<=a.cycles<=1000 or not 2<=a.families<=4 or not 1<=a.generations<=4 or not 1<=a.mutate_ticks<=4:ap.error('bounded cycles/families/generations/mutation required')
    if d==ROOT or ROOT in d.parents or out==ROOT or ROOT in out.parents:ap.error('data and report must be outside signed distribution')
    out.parent.mkdir(parents=True,exist_ok=True);events=out.with_suffix('.jsonl');started=time.monotonic()
    report=json.loads(out.read_text()) if out.is_file() else {'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'completed_cycles':0,'cycles':[],'24h_completed':False,'completed':False,'configuration':{'data':str(d),'pin_sha256':sha(pin),'families':a.families,'generations':a.generations,'mutate_ticks':a.mutate_ticks},'release_receipt_sha256':sha(ROOT/'META/RELEASE_RECEIPT.json')}
    expected={'data':str(d),'pin_sha256':sha(pin),'families':a.families,'generations':a.generations,'mutate_ticks':a.mutate_ticks}
    if report['configuration']!=expected or report['release_receipt_sha256']!=sha(ROOT/'META/RELEASE_RECEIPT.json'):ap.error('resume configuration/release mismatch')
    def save():
        report['current_session_elapsed_seconds']=time.monotonic()-started
        report['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        temp=out.with_suffix('.tmp');temp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');os.replace(temp,out)
    def cli(*args,crash=None):
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'};env.pop('TUKUYO_CRASH_POINT',None)
        if crash:env['TUKUYO_CRASH_POINT']=crash
        cmd=[sys.executable,'-B',str(ROOT/'run_tukuyo.py'),'--runtime-trust-file',str(pin),'--data',str(d),*map(str,args)]
        begin=time.monotonic();p=subprocess.Popen(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
        try:stdout,stderr=p.communicate(timeout=240)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate();raise RuntimeError({'timeout':args,'stderr':stderr})
        except BaseException:
            if p.poll() is None:os.killpg(p.pid,signal.SIGKILL)
            p.communicate();raise
        r=json.loads(stdout) if stdout.strip() else None
        record={'cycle':report['completed_cycles']+1,'args':list(map(str,args)),'pid':p.pid,'returncode':p.returncode,'crash_point':crash,'elapsed_seconds':time.monotonic()-begin,'result':r,'stderr':stderr}
        with events.open('a') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
        if crash:
            if p.returncode not in (-signal.SIGKILL,137):raise RuntimeError({'crash_not_reached':record})
        elif p.returncode or not r or not r.get('ok'):raise RuntimeError(record)
        return r
    try:
        if 'checkpoint' not in report:
            if d.exists() and any(d.iterdir()):raise ValueError('NEW_GATE_REQUIRES_EMPTY_DATA')
            cli('init','--individual-id','RECOVERY-STRESS-v1022.4')
            cli('metabolism-init','--families',a.families,'--reservoir','160000','--regeneration','1800','--max-age','4')
            state=cli('metabolism-step','--ticks',a.generations*4)
            if state['max_generation']!=a.generations:raise AssertionError(state)
            cli('realtime-start');cli('realtime-tick')
            report['checkpoint']=cli('recovery-checkpoint','--note','multigeneration process-boundary gate')
            report['baseline']=state
            report['key_hashes']=key_hashes(d)
            save()
        cp=Path(report['checkpoint']['path']);targets=json.loads(cp.read_text())['payload']['files']
        if report['completed_cycles']:
            cli('recovery-restore',cp,'--trust-file',d/'v1014/recovery.pub')
        report['completed']=False;save()
        for cycle in range(report['completed_cycles']+1,a.cycles+1):
            begin=time.monotonic()
            if cycle==3:
                cli('metabolism-step','--ticks',a.mutate_ticks,crash='lineage:after_prepare')
                future=None
            elif cycle==4 and a.mutate_ticks==4:
                cli('metabolism-step','--ticks',4,crash='metabolism:after_death')
                assert cli('metabolism-audit')['tick']==a.generations*4
                future=cli('metabolism-step','--ticks',4)
            else:future=cli('metabolism-step','--ticks',a.mutate_ticks)
            if future is not None:
                assert future['tick']==a.generations*4+a.mutate_ticks
                cli('realtime-tick','--note',f'future-cycle-{cycle}')
            point={1:'restore:after_txn_marker',2:'restore:mid_commit'}.get(cycle)
            cli('recovery-restore',cp,'--trust-file',d/'v1014/recovery.pub',crash=point)
            restored=cli('metabolism-audit');cli('whole-audit');cli('realtime-audit')
            assert restored['tick']==a.generations*4 and restored['max_generation']==a.generations
            assert restored['total_runtime_count']==a.families*(a.generations+1)
            actual={p.relative_to(d).as_posix():sha(p) for p in d.rglob('*') if p.is_file() and not (EXCLUDE&set(p.relative_to(d).parts))}
            actual.pop('v1014/LAST_RECOVERY_RECEIPT.json',None)
            assert set(actual)==set(targets),{'extra':sorted(set(actual)-set(targets)),'missing':sorted(set(targets)-set(actual))}
            assert all(actual[k]==v['sha256'] for k,v in targets.items()),'checkpoint byte drift'
            assert all((d/k).is_file() and sha(d/k)==h for k,h in report['key_hashes'].items()),'private key drift'
            assert len(list((d/'v1022_ecology/runtimes').iterdir()))==a.families*(a.generations+1)
            assert not any(d.rglob('.lineage_transaction')),'future lineage redo survived restore'
            report['cycles'].append({'cycle':cycle,'elapsed_seconds':time.monotonic()-begin,'restored_tick':restored['tick'],'generation':restored['max_generation'],'checkpoint_projection_equal':True,'key_hashes_unchanged':True,'future_active_runtime_directories':0,'crash_point':point,'resource_conservation':restored['resource_conservation']})
            report['completed_cycles']=cycle;save()
            if cycle%10==0:print(json.dumps({'completed_cycles':cycle,'elapsed':round(time.monotonic()-started,2)}),flush=True)
        report['resume_after_final_restore']=cli('metabolism-step','--ticks','1')
        report['final_audit']=cli('metabolism-audit');report['final_whole_audit']=cli('whole-audit')
        report['completed']=True;report['requested_cycles']=a.cycles;save();return 0
    except BaseException as exc:
        report['completed']=False;report['failure']={'type':type(exc).__name__,'message':str(exc)};save();raise
if __name__=='__main__':raise SystemExit(main())
