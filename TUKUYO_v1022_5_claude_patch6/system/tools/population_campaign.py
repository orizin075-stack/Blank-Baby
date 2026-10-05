"""Reproduce the v1020 bounded four-family campaign. Runtime data stays private."""
from pathlib import Path
import argparse,contextlib,hashlib,importlib.util,io,json,os,shutil,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser();p.add_argument('--runtime-trust-file',type=Path,required=True);p.add_argument('--out-dir',type=Path,required=True);p.add_argument('--ticks',type=int,default=64);p.add_argument('--execution-mode',choices=('in_process_cli','subprocess_cli'),default='in_process_cli');a=p.parse_args()
 out=a.out_dir.resolve()
 if out.exists():raise ValueError('Use a new output directory')
 if ROOT==out or ROOT in out.parents:raise ValueError('Output must be outside the signed distribution')
 if not 32<=a.ticks<=128:raise ValueError('ticks must be 32..128')
 out.mkdir(parents=True);anchor=a.runtime_trust_file.resolve();logs=out/'public';logs.mkdir()
 # Keep the original mode available for comparisons. The root cause of the
 # initial cross-process discrepancies is unconfirmed; neither mode proves it.
 sys.path.insert(0,str(ROOT/'src'))
 spec=importlib.util.spec_from_file_location('tukuyo_population_entry',ROOT/'run_tukuyo.py')
 entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
 from tukuyo_v1020 import ecology
 def run(data,*args):
  started=time.monotonic();stream=io.StringIO()
  argv=['--runtime-trust-file',str(anchor),'--data',str(data),*map(str,args)]
  if a.execution_mode=='subprocess_cli':
   completed=subprocess.run([sys.executable,'-B',str(ROOT/'run_tukuyo.py'),*argv],env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},cwd=ROOT,capture_output=True,text=True,timeout=300)
   code=completed.returncode;stream.write(completed.stdout)
  else:
   with contextlib.redirect_stdout(stream):code=entry.main(argv)
  parsed=json.loads(stream.getvalue())
  if code or not parsed.get('ok'):raise ValueError((args,parsed))
  return parsed,time.monotonic()-started
 def fresh_audit(data,command):
  r=subprocess.run([sys.executable,'-B',str(ROOT/'run_tukuyo.py'),'--runtime-trust-file',str(anchor),'--data',str(data),command],env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},cwd=ROOT,capture_output=True,text=True,timeout=300)
  parsed=json.loads(r.stdout)
  if r.returncode or not parsed.get('ok'):raise ValueError(('restart',command,parsed,r.stderr))
  return parsed
 def save(name,obj):
  from tukuyo_common.atomic_fs import atomic_write_bytes
  path=logs/name;encoded=(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
  atomic_write_bytes(path,encoded)
  if path.read_bytes()!=encoded:raise ValueError('campaign output readback differs: '+name)
 sources=[];pins=[]
 for i in range(4):
  data=out/f'source-{i}';run(data,'init','--individual-id',f'ecology-source-{i}');run(data,'succession-founder-init');pin=out/f'source-{i}.pub';run(data,'succession-pubkey-export','--out',pin);sources.append(data);pins.append(pin)
 rows=[]
 scenarios=[('no_regeneration',0,True),('scarce',18000,True),('medium',50000,True),('sustainable',100000,True),('abundant',240000,True),('scarce_no_cooperation',18000,False),('medium_no_cooperation',50000,False)]
 for name,regeneration,coop in scenarios:
  data=out/name;shutil.copytree(sources[0],data)
  args=['population-init','--seed','v1020-four-family-20261003','--capacity','240000','--regeneration',regeneration]
  if not coop:args+=['--no-cooperation']
  run(data,*args)
  for i in range(1,4):run(data,'population-join',sources[i],'--source-trust-file',pins[i])
  genesis=json.loads((data/'v1020/ECOLOGY_STATE.json').read_text());save(name+'_genesis.json',genesis)
  reports=[];durations=[]
  for start in range(0,a.ticks,16):
   environment=('resource','research','social','volatile')[(start//16)%4]
   r,elapsed=run(data,'population-step',environment,'--ticks',min(16,a.ticks-start));reports+=r['ticks'];durations.append(elapsed)
  status,_=run(data,'population-status');audit,_=run(data,'population-audit');whole,_=run(data,'whole-audit')
  save(name+'_ticks.json',reports);save(name+'_status.json',status);save(name+'_audit.json',audit);save(name+'_whole_audit.json',whole)
  cache_bytes=(data/'v1020/ECOLOGY_STATE.json').read_bytes();(data/'v1020/ECOLOGY_STATE.json').unlink();assert not ecology.state_path(data).exists();run(data,'population-audit');recovery_exact=(data/'v1020/ECOLOGY_STATE.json').read_bytes()==cache_bytes
  if not recovery_exact:raise ValueError('cache recovery differs')
  restart_audit=fresh_audit(data,'population-audit');restart_whole=fresh_audit(data,'whole-audit');save(name+'_restart_audit.json',restart_audit);save(name+'_restart_whole_audit.json',restart_whole)
  signed_files=list((data/'v1020/commits').glob('*.json'));max_mut=max((b['max_abs_mutation'] for r in reports for b in r['births']),default=0)
  balances=all(r['conservation']['before']+r['regenerated']==r['conservation']['after']+r['burned']+r['overflow'] for r in reports)
  row={'name':name,'regeneration':regeneration,'cooperation':coop,'summary':status['summary'],'checks':{'ecology_audit':audit['ok'],'whole_audit':whole['ok'],'cache_recovery_exact':recovery_exact,'fresh_process_audit':restart_audit['ok'],'fresh_process_whole_audit':restart_whole['ok'],'all_tick_balances':balances,'mutation_bound':max_mut<=.12},'max_mutation_observed':max_mut,'commit_count':len(signed_files),'ecology_bytes':sum(p.stat().st_size for p in (data/'v1020').rglob('*') if p.is_file()),'batch_elapsed_seconds':durations}
  rows.append(row);save('campaign_progress.json',rows)
 summary={'schema':'tukuyo.v1020.fresh_population_campaign/1','command_mutations':a.execution_mode,'fresh_process_checks_per_scenario':2,'ticks_per_scenario':a.ticks,'scenario_count':len(rows),'scenarios':rows,'ok':all(all(r['checks'].values()) for r in rows),'claim_boundary':{'bounded_model':True,'independent_external_validation':False,'wall_clock_24h':False,'natural_selection_established':False}}
 save('campaign_summary.json',summary);print(json.dumps(summary,ensure_ascii=False,sort_keys=True))

if __name__=='__main__':main()
