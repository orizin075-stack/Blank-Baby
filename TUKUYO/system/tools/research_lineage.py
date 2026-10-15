"""claude-patch5: research niche inside the real metabolism, lineage with and without inherited laws.

Two ecologies are started from the same seed (same founders' niches):
  inherit     metabolism-init --research-world            (a successor may inherit the parent's CONFIRMED law)
  no_inherit  metabolism-init --research-world --no-learning
Each is stepped for the same number of ticks; the report compares, per generation,
successful work, injuries, experiments, inherited laws, deaths and audits.

usage: python3 -B tools/research_lineage.py --runtime-trust-file ANCHOR --out report.json [--ticks 64] [--max-age 24]
"""
from __future__ import annotations
import argparse,json,os,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--runtime-trust-file',required=True);ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--ticks',type=int,default=64);ap.add_argument('--max-age',type=int,default=24);ap.add_argument('--families',type=int,default=4)
    ap.add_argument('--seed',default='v1023r-lineage');ap.add_argument('--reservoir',type=int,default=200000);ap.add_argument('--regeneration',type=int,default=3000);ap.add_argument('--work',type=Path)
    a=ap.parse_args();base=a.work or Path(tempfile.mkdtemp(prefix='tukuyo-lineage-'))
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'};env.pop('TUKUYO_CRASH_POINT',None)
    out={'schema':'tukuyo.v1023r.lineage/1','seed':a.seed,'ticks':a.ticks,'max_age':a.max_age,'families':a.families,'reservoir':a.reservoir,'regeneration':a.regeneration,'runs':{}}
    for name,extra in (('inherit',[]),('no_inherit',['--no-learning'])):
        d=base/name;t0=time.time()
        def cli(*args):
            p=subprocess.run([sys.executable,'-B',str(ROOT/'run_tukuyo.py'),'--runtime-trust-file',a.runtime_trust_file,'--data',str(d),*map(str,args)],cwd=ROOT,env=env,capture_output=True,text=True,timeout=3600)
            r=json.loads(p.stdout)
            if not r.get('ok'):raise SystemExit(f'{name} {args[0]} failed: {r}')
            return r
        cli('init','--individual-id',f'LINEAGE-{name.upper()}')
        cli('metabolism-init','--families',a.families,'--seed',a.seed,'--reservoir',a.reservoir,'--regeneration',a.regeneration,'--max-age',a.max_age,'--research-world',*extra)
        ticks=[]
        for _ in range(0,a.ticks,8):
            r=cli('metabolism-step','--ticks',min(8,a.ticks-len(ticks)*8))
            ticks.append({'tick':r['tick'],'active':r['active_runtime_count'],'successions':r['actual_successions'],'reservoir':r['reservoir'],'living_energy':r['living_energy']})
        st=cli('metabolism-status');au=cli('metabolism-audit');wa=cli('whole-audit')
        gen={}
        for rid,row in st['research_niche'].items():
            g=next((s for s in st['successions'] if s['child']==rid),None);gk='founder' if g is None else 'successor'
            G=gen.setdefault(gk,{'n':0,'works':0,'works_paid':0,'injuries':0,'probes':0,'trials':0,'rests':0,'inherited_law':0,'confirmed_law':0})
            G['n']+=1;G['inherited_law']+=int(bool(row['inherited_law']));G['confirmed_law']+=int(row['status']=='CONFIRMED')
            for k in ('works','works_paid','injuries','probes','trials','rests'):G[k]+=row[k]
        out['runs'][name]={'ticks':ticks,'deaths':len(st['deaths']),'death_causes':sorted({x['cause'] for x in st['deaths']}),'successions':st['actual_successions'],
            'max_generation':st['max_generation'],'by_generation':gen,'per_runtime':st['research_niche'],'metabolism_audit':au.get('ok'),'whole_audit':wa.get('ok'),
            'resource_conservation':au.get('resource_conservation'),'seconds':round(time.time()-t0,1)}
        a.out.write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding='utf-8')
    print(json.dumps({k:{x:v[x] for x in ('deaths','successions','max_generation','by_generation','metabolism_audit','whole_audit','seconds')} for k,v in out['runs'].items()},ensure_ascii=False,indent=1))

if __name__=='__main__':main()
