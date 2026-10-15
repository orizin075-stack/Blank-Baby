"""Summarize ecology_long_run reports (round 11): survival through the drought (its ticks from the run's own changes:
regeneration set to 0 and back), recovery after it, births, exploring, learning. Usage: eco_summary11.py REPORT.json ..."""
import json,sys
from pathlib import Path
for f in sys.argv[1:]:
    r=json.loads(Path(f).read_text());st=r['steps'];res=r.get('result') or {}
    ch=r['config'].get('changes') or []
    a=next((t for t,v in ch if v==0),400);b=next((t for t,v in ch if t>a and v>0),600)
    at=lambda t:next((x for x in st if x['tick']>=t),st[-1] if st else {})
    drought=[x for x in st if a<x['tick']<=b];after=[x for x in st if x['tick']>b]
    bi=lambda x:x.get('births') or 0
    out={'run':Path(f).stem,'drought':[a,b],'config':{k:r['config'].get(k) for k in ('no_learning','sharing','stagger','reproduction','explore','bequest','seed','regeneration')},
         'stopped':res.get('stopped') or ('RUNNING' if not res else None),'ticks':res.get('ticks') or (st[-1]['tick'] if st else 0),
         'audit_ok':(r.get('audit') or {}).get('ok'),'owner_whole_audit_ok':(r.get('owner_whole_audit') or {}).get('ok'),
         'alive_at_drought_start':at(a).get('active_runtime_count'),'min_alive_in_drought':min((x['active_runtime_count'] for x in drought),default=None),
         'alive_at_drought_end':at(b).get('active_runtime_count') if st and st[-1]['tick']>=b else 0,
         'max_alive_after_drought':max((x['active_runtime_count'] for x in after),default=None),'alive_at_last':st[-1]['active_runtime_count'] if st else None,
         'houses_alive_at_last':st[-1].get('houses_alive') if st else None,'max_generation':st[-1].get('max_generation') if st else None,
         'births':st[-1].get('births') if st else None,'births_after_drought':(bi(st[-1])-bi(at(b))) if after else 0,
         'found_total':st[-1].get('found') if st else None,
         'explore':f"{st[-1].get('explore_correct')}/{st[-1].get('explore_attempts')}" if st and st[-1].get('explore_attempts') is not None else None,
         'hard':f"{st[-1].get('hard_correct')}/{st[-1].get('hard_attempts')}" if st else None,'wrong':st[-1].get('wrong') if st else None}
    print(json.dumps(out,ensure_ascii=False))
