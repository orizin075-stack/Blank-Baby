#!/usr/bin/env python3
"""A long run of the runtime ecology (tukuyo_v1022.metabolism): several individuals, each an actual runtime, living on a
shared reservoir, dying, and succeeded by children. The roadmap's v1022.8.2 asks for 1,000 steps or more with several
individuals and generations, with economy, learning, relations, resources and survival linked.

  ecology_long_run.py --work WORK --runtime-trust-file ANCHOR [--ticks N] [--families F] [--regeneration R]
                      [--reservoir X] [--max-age A] [--no-learning] [--sharing] [--stagger] [--reproduction]
                      [--explore [--wild-regeneration W] [--wild-cap C]] [--change TICK:REGENERATION ...] [--out REPORT.json]

It runs the real CLI (run_tukuyo.py metabolism-init / metabolism-step) and records, after every step, the tick, the
living and all runtimes, the deepest generation, the reservoir, deaths and successions, and the tasks done. It stops
at N ticks, when no runtime is alive, or when the ecology refuses to go on (its bound). No parent is asked (cost 0).
"""
from __future__ import annotations
import argparse,json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]

def run(trust,d,*a,timeout=3600):
    env={k:v for k,v in os.environ.items() if not k.startswith(('TUKUYO_ANTHROPIC','TUKUYO_OPENAI','TUKUYO_GEMINI','TUKUYO_LLM','TUKUYO_CANON','TUKUYO_G4_WITNESS'))}
    p=subprocess.run([sys.executable,'-B',str(HERE/'run_tukuyo.py'),'--runtime-trust-file',str(trust),'--data',str(d),*map(str,a)],cwd=HERE,env=env,
                     capture_output=True,text=True,timeout=timeout)
    try:return json.loads(p.stdout)
    except ValueError:return {'ok':False,'error':'NO_JSON:'+p.stderr[-400:]}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work',required=True);ap.add_argument('--runtime-trust-file',required=True)
    ap.add_argument('--ticks',type=int,default=1000);ap.add_argument('--families',type=int,default=4);ap.add_argument('--regeneration',type=int,default=0)
    ap.add_argument('--reservoir',type=int,default=20000);ap.add_argument('--max-age',type=int,default=32);ap.add_argument('--no-learning',action='store_true')
    ap.add_argument('--step',type=int,default=32);ap.add_argument('--max-runtimes',type=int,default=64)
    ap.add_argument('--sharing',action='store_true',help='v1022.8.2: runtimes may give energy to a hungry one and raise a child together')
    ap.add_argument('--stagger',action='store_true',help='v1022.8.2 r10: founders born at different ticks')
    ap.add_argument('--reproduction',action='store_true',help='v1022.8.2 r10: living runtimes may bear children with their own energy')
    ap.add_argument('--explore',action='store_true',help='v1022.8.2 r10: a wild place found only by reading a clue right')
    ap.add_argument('--bequest',action='store_true',help='v1022.8.2 r10: an old runtime leaves what energy it has left to its successor')
    ap.add_argument('--wild-regeneration',type=int,default=1200);ap.add_argument('--wild-cap',type=int,default=24000)
    ap.add_argument('--change',action='append',default=[],metavar='TICK:REGENERATION',
                    help='change the environment at a tick (the reservoir regeneration from then on), e.g. 400:0 for a drought')
    ap.add_argument('--resume',action='store_true',help='go on with the ecology in WORK and the report in --out (after a restart)')
    ap.add_argument('--out');a=ap.parse_args()
    changes=sorted((int(x.split(':')[0]),int(x.split(':')[1])) for x in a.change)
    d=Path(a.work).resolve()/'ecology';d.parent.mkdir(parents=True,exist_ok=True)
    keys=('ticks','families','regeneration','reservoir','max_age','no_learning','step','max_runtimes','sharing','stagger','reproduction','explore','bequest')
    rep={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'config':{**{k:getattr(a,k) for k in keys},
                                                                           **({'wild_regeneration':a.wild_regeneration,'wild_cap':a.wild_cap} if a.explore else {}),
                                                                           'changes':[list(c) for c in changes]},'steps':[],'environment':[]}
    t0=time.time()
    if a.resume and a.out and Path(a.out).is_file() and (d/'v1022_ecology').is_dir():
        rep=json.loads(Path(a.out).read_text(encoding='utf-8'));rep.pop('stopped',None);rep.pop('result',None)
        rep.setdefault('resumed',[]).append(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()));rep['config']['ticks']=a.ticks
        st=run(a.runtime_trust_file,d,'metabolism-status')
        if not st.get('ok'):rep['stopped']='RESUME:'+str(st.get('error'));print(rep['stopped']);return _out(a,rep)
        done={e['asked_at'] for e in rep['environment'] if e.get('ok')};changes=[c for c in changes if c[0] not in done]
        t0-=rep['steps'][-1]['seconds'] if rep['steps'] else 0
        return _go(a,rep,d,st['tick'],changes,t0)
    r=run(a.runtime_trust_file,d,'init','--individual-id','ECOLOGY-OWNER')
    if not r.get('ok'):rep['stopped']='INIT:'+str(r.get('error'));print(rep['stopped']);return _out(a,rep)
    args=['metabolism-init','--families',a.families,'--reservoir',a.reservoir,'--regeneration',a.regeneration,'--max-age',a.max_age]+(['--no-learning'] if a.no_learning else [])
    if a.ticks>512 or a.max_runtimes!=64:args+=['--max-ticks',max(512,a.ticks),'--max-runtimes',a.max_runtimes]
    if a.sharing:args+=['--sharing']
    if a.stagger:args+=['--stagger']
    if a.reproduction:args+=['--reproduction']
    if a.bequest:args+=['--bequest']
    if a.explore:args+=['--explore','--wild-regeneration',a.wild_regeneration,'--wild-cap',a.wild_cap]
    r=run(a.runtime_trust_file,d,*args)
    if not r.get('ok'):rep['stopped']='METABOLISM_INIT:'+str(r.get('error'));print(rep['stopped']);return _out(a,rep)
    return _go(a,rep,d,0,changes,t0)

def _go(a,rep,d,tick,changes,t0):
    while tick<a.ticks:
        while changes and changes[0][0]<=tick:
            at,regen=changes.pop(0);r=run(a.runtime_trust_file,d,'metabolism-environment','--regeneration',regen)
            rep['environment'].append({'asked_at':at,'tick':tick,'regeneration':regen,'ok':r.get('ok'),'error':r.get('error')});print('environment',rep['environment'][-1],flush=True);_out(a,rep)
        nxt=changes[0][0] if changes else a.ticks
        n=min(a.step,a.ticks-tick,max(1,nxt-tick));r=run(a.runtime_trust_file,d,'metabolism-step','--ticks',n)
        if not r.get('ok'):rep['stopped']='STEP:'+str(r.get('error'));break
        tick=r['tick']
        row={k:r.get(k) for k in ('tick','active_runtime_count','total_runtime_count','actual_successions','max_generation','reservoir','burned','regenerated',
                                  'living_energy','attempts','correct','wrong','abstained','hard_attempts','hard_correct','regeneration')}
        row['families_alive']=len({x['family'] for x in r.get('alive') or []})
        row['relations']=r.get('relations') or None
        row['raised_together']=sum(1 for x in r.get('successions') or [] if (x.get('funded_by') or {}).get('runtimes'))
        if a.reproduction:
            # a house: the founder a living runtime goes back to, through successions (death) and births (living parents)
            up={x['child']:x['parent'] for x in (r.get('successions') or [])+(r.get('births') or [])}
            def house(rid):
                while rid in up:rid=up[rid]
                return rid
            row['houses_alive']=len({house(x['runtime']) for x in r.get('alive') or []})
        row['starved']=sum(1 for x in r.get('deaths') or [] if x.get('cause')=='ENERGY')
        row['deaths']=len(r.get('deaths') or [])
        if a.bequest:row['provisioned']=sum(1 for x in r.get('successions') or [] if (x.get('funded_by') or {}).get('parent_bequest'))
        if a.reproduction:row['births']=len(r.get('births') or [])
        if a.stagger:row['unborn']=len(r.get('unborn') or [])
        if a.explore:row.update({k:r.get(k) for k in ('wild','found','explore_attempts','explore_correct','explore_paid')})
        row['seconds']=round(time.time()-t0,1);rep['steps'].append(row)
        print(json.dumps(row),flush=True);_out(a,rep)
        if not r.get('active_runtime_count'):rep['stopped']='EXTINCT';break
    else:rep['stopped']='REACHED_TICKS'
    au=run(a.runtime_trust_file,d,'metabolism-audit');rep['audit']={'ok':au.get('ok'),'errors':au.get('errors')}
    wa=run(a.runtime_trust_file,d,'whole-audit');rep['owner_whole_audit']={'ok':wa.get('ok'),'errors':wa.get('errors')}
    last=rep['steps'][-1] if rep['steps'] else {}
    rep['result']={'ticks':last.get('tick',0),'alive_at_end':last.get('active_runtime_count',0),'families_alive_at_end':last.get('families_alive',0),
                   'runtimes':last.get('total_runtime_count',0),
                   'generations':last.get('max_generation',0),'successions':last.get('actual_successions',0),'deaths':last.get('deaths',0),
                   'starved':last.get('starved',0),'raised_together':last.get('raised_together',0),'relations':last.get('relations'),
                   **{k:last.get(k) for k in ('births','houses_alive','provisioned','found','explore_attempts','explore_correct','explore_paid') if k in last},
                   'max_alive':max((x.get('active_runtime_count') or 0 for x in rep['steps']),default=0),
                   'stopped':rep.get('stopped'),'seconds':round(time.time()-t0,1)}
    print('result',json.dumps(rep['result']))
    return _out(a,rep)

def _out(a,rep):
    if a.out:Path(a.out).write_text(json.dumps(rep,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')

if __name__=='__main__':main()
