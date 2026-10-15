import json,sys
SP='/tmp/claude-0/-home-user-Blank-Baby/dd3c6b53-ae17-5414-bda7-717330a62fb9/scratchpad'
a=json.load(open('/home/user/Blank-Baby/TUKUYO_v1022_5_claude_patch6/evidence_claude_patch5/research_lineage_inherit_vs_not.json'))
b=json.load(open(SP+'/rl6/research_lineage_patch6.json'))
for run in ('inherit','no_inherit'):
    if run not in b['runs']:print(run,'pending');continue
    x,y=a['runs'][run],b['runs'][run]
    print('==',run,'deaths',x['deaths'],y['deaths'],'successions',x['successions'],y['successions'],'audits',y['metabolism_audit'],y['whole_audit'],y['resource_conservation'])
    for g in ('founder','successor'):print(' ',g,'p5',x['by_generation'].get(g),'\n   p6',y['by_generation'].get(g))
    same=[r for r in x['per_runtime'] if x['per_runtime'][r]==y['per_runtime'].get(r)]
    print('  identical runtimes:',len(same),'/',len(x['per_runtime']))
    for r in x['per_runtime']:
        if x['per_runtime'][r]!=y['per_runtime'].get(r):
            p,q=x['per_runtime'][r],y['per_runtime'].get(r) or {}
            print('   diff',r,p['niche'],{k:(p.get(k),q.get(k)) for k in ('status','method','law','inherited_law','works','works_paid','injuries','probes','trials','rests') if p.get(k)!=q.get(k)})
