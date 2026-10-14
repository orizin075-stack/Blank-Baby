"""Summarize ecology_long_run reports (round 10): survival through the drought (ticks 400-600), recovery after it,
births, exploring, learning. Usage: eco_summary.py REPORT.json ... (prints one JSON object per report)"""
import json,sys
from pathlib import Path
for f in sys.argv[1:]:
    r=json.loads(Path(f).read_text());st=r['steps'];res=r.get('result') or {}
    at=lambda t:next((x for x in st if x['tick']>=t),st[-1] if st else {})
    drought=[x for x in st if 400<x['tick']<=600];after=[x for x in st if x['tick']>600]
    b=lambda x:x.get('births') or 0
    out={'run':Path(f).stem,'config':{k:r['config'].get(k) for k in ('no_learning','sharing','stagger','reproduction','explore','bequest')},
         'stopped':res.get('stopped'),'ticks':res.get('ticks'),'audit_ok':(r.get('audit') or {}).get('ok'),'owner_whole_audit_ok':(r.get('owner_whole_audit') or {}).get('ok'),
         'alive_at_400':at(400).get('active_runtime_count'),'reservoir_at_400':at(400).get('reservoir'),
         'min_alive_in_drought':min((x['active_runtime_count'] for x in drought),default=None),
         'alive_at_600':at(600).get('active_runtime_count') if st and st[-1]['tick']>=600 else 0,
         'alive_at_end':res.get('alive_at_end'),'max_alive_after_drought':max((x['active_runtime_count'] for x in after),default=None),
         'houses_alive_at_end':res.get('houses_alive'),'generations':res.get('generations'),'runtimes':res.get('runtimes'),
         'births':res.get('births'),'births_after_drought':(b(st[-1])-b(at(600))) if after else 0,
         'provisioned_successors':res.get('provisioned'),'raised_together':res.get('raised_together'),'starved':res.get('starved'),'deaths':res.get('deaths'),
         'found_total':res.get('found'),'found_in_drought':(at(600).get('found') or 0)-(at(400).get('found') or 0) if st and st[-1]['tick']>=600 else None,
         'explore':f"{res.get('explore_correct')}/{res.get('explore_attempts')}" if res.get('explore_attempts') is not None else None,
         'hard':f"{st[-1].get('hard_correct')}/{st[-1].get('hard_attempts')}" if st else None,'wrong':st[-1].get('wrong') if st else None,
         'seconds':res.get('seconds')}
    print(json.dumps(out,ensure_ascii=False))
