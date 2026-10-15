"""Run actual-runtime metabolism on a wall clock. No LLM calls.
Output is stored outside the signed distribution, in the individual's data root.
"""
from pathlib import Path
import argparse,datetime,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--runtime-trust-file',type=Path,required=True);p.add_argument('--duration-seconds',type=int,default=86400);p.add_argument('--tick-seconds',type=float,default=300);p.add_argument('--families',type=int,default=4);p.add_argument('--reservoir',type=int,default=160000);p.add_argument('--regeneration',type=int,default=1600);p.add_argument('--max-age',type=int,default=32);a=p.parse_args()
 if not 1<=a.duration_seconds<=86400 or a.tick_seconds<1:p.error('duration 1..86400; tick interval >=1')
 data=a.data.resolve()
 if data==ROOT or ROOT in data.parents:p.error('data must be outside the signed distribution')
 def cli(*args):
  r=subprocess.run([sys.executable,'-B',str(ROOT/'run_tukuyo.py'),'--runtime-trust-file',str(a.runtime_trust_file.resolve()),'--data',str(data),*map(str,args)],env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=600);out=json.loads(r.stdout)
  if r.returncode or not out.get('ok'):raise RuntimeError(out)
  return out
 if not (data/'state/integration_state.json').exists():cli('init')
 if not (data/'v1022_ecology').exists():cli('metabolism-init','--families',a.families,'--reservoir',a.reservoir,'--regeneration',a.regeneration,'--max-age',a.max_age)
 report={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'duration_requested':a.duration_seconds,'tick_interval':a.tick_seconds,'accelerated_ticks_are_elapsed_wallclock':False,'24h_completed':False,'rows':[],'completed':False};start=time.monotonic();due=start;deadline=start+a.duration_seconds;reason='DURATION';target=data/'v1022_wallclock_report.json'
 def save():
  report['elapsed_seconds']=time.monotonic()-start;temp=target.with_suffix('.tmp');temp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');os.replace(temp,target)
 try:
  while time.monotonic()<deadline:
   now=time.monotonic()
   if now<due:time.sleep(min(1,due-now));continue
   status=cli('metabolism-status')
   if status['tick']>=512:reason='TICK_BOUND';break
   if not status['active_runtime_count']:reason='EXTINCTION';break
   r=cli('metabolism-step','--ticks','1');report['rows'].append({'elapsed_seconds':time.monotonic()-start,'result':r});save();print(json.dumps({'tick':r['tick'],'alive':r['active_runtime_count'],'elapsed':round(time.monotonic()-start,2)}),flush=True);due=max(due+a.tick_seconds,time.monotonic())
  report['audit']=cli('metabolism-audit');report['whole_audit']=cli('whole-audit');report['completed']=reason=='DURATION';report['stop_reason']=reason;report['24h_completed']=report['completed'] and a.duration_seconds==86400 and time.monotonic()-start>=86400
 except KeyboardInterrupt:report['stop_reason']='INTERRUPTED'
 finally:report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
 return 0 if report['completed'] else 2
if __name__=='__main__':raise SystemExit(main())
