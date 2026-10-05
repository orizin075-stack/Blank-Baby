"""Offline curriculum replay or file inbox for independent AI teachers.
Replay is exercise repetition, not a live conversation or additional AI model.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--runtime-trust-file',type=Path,required=True);p.add_argument('--inbox',type=Path);p.add_argument('--duration-seconds',type=int,default=3600);p.add_argument('--max-rounds',type=int,default=1000);p.add_argument('--repeats',type=int,default=1);a=p.parse_args();d=a.data.resolve()
 if d==ROOT or ROOT in d.parents:p.error('data must be outside signed distribution')
 if not 1<=a.duration_seconds<=86400 or not 1<=a.max_rounds<=10000 or not 1<=a.repeats<=100:p.error('duration/rounds/repeats bounds')
 def cli(*args):
  r=subprocess.run([sys.executable,'-B',str(ROOT/'run_tukuyo.py'),'--runtime-trust-file',str(a.runtime_trust_file.resolve()),'--data',str(d),*map(str,args)],env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=600);out=json.loads(r.stdout)
  if r.returncode or not out.get('ok'):raise RuntimeError(out)
  return out
 if not (d/'state/integration_state.json').exists():cli('init')
 log=d/'v1022_school';log.mkdir(exist_ok=True);seen=set();report={'mode':'external_teacher_file_inbox' if a.inbox else 'offline_replay','new_dialogue_rounds':0,'runtime_llm':False,'responses':[]};start=time.monotonic()
 sources=[p for p in sorted((ROOT/'META/TEACHER_CURRICULA').glob('*.json')) if 'feedback' not in p.name and 'manifest' not in p.name]*a.repeats
 while time.monotonic()-start<a.duration_seconds and report['new_dialogue_rounds']<a.max_rounds:
  files=sorted(a.inbox.glob('*.json')) if a.inbox else sources
  fresh=[f for f in files if (str(f),hashlib.sha256(f.read_bytes()).hexdigest()) not in seen] if a.inbox else files
  if not fresh:
   if not a.inbox:break
   time.sleep(1);continue
  for file in fresh:
   if cli('learning-status')['rounds']>=10000:report['stop_reason']='LEARNING_LIMIT';break
   digest=hashlib.sha256(file.read_bytes()).hexdigest();bundle=json.loads(file.read_text());examples=bundle['examples']
   for i in range(0,len(examples),10):
    allowance=min(a.max_rounds-report['new_dialogue_rounds'],10000-cli('learning-status')['rounds'])
    if allowance<=0:break
    b={'teacher':bundle['teacher'],'examples':examples[i:i+min(10,allowance)]};num=len(report['responses']);input_file=log/f'{num:05d}_input.json';input_file.write_text(json.dumps(b,ensure_ascii=False));r=cli('dialogue-learn',input_file);response_file=log/f'{num:05d}_response.json';response_file.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');report['new_dialogue_rounds']+=r['new_rounds'];report['responses'].append({'source':file.name,'sha256':digest,'response':str(response_file)});print(json.dumps({'teacher':bundle['teacher'],'rounds':r['rounds']}),flush=True)
    report['elapsed_seconds']=time.monotonic()-start;(log/'REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    if time.monotonic()-start>=a.duration_seconds or report['new_dialogue_rounds']>=a.max_rounds:break
   seen.add((str(file),digest))
   if time.monotonic()-start>=a.duration_seconds or report['new_dialogue_rounds']>=a.max_rounds:break
  if not a.inbox:break
  if report.get('stop_reason')=='LEARNING_LIMIT':break
 report['learning_audit']=cli('learning-audit');report['whole_audit']=cli('whole-audit');report['elapsed_seconds']=time.monotonic()-start;(log/'REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');return 0
if __name__=='__main__':raise SystemExit(main())
