from __future__ import annotations
from .deps import activate
activate()
import tukuyo_v846.evolution as ev
from tukuyo_v846.util import canonical,sha256_bytes
CASES=[{'id':f'C{i+1:02d}','x':x,'expected':2*abs(x)} for i,x in enumerate(range(-6,7))]
FOUNDERS={
 'TUKUYO-v846-X':{'op':'x'},
 'TUKUYO-v846-ABS':{'op':'abs','arg':{'op':'x'}},
 'TUKUYO-v846-PLUS1':{'op':'add','left':{'op':'x'},'right':{'op':'const','value':1}},
 'TUKUYO-v846-DOUBLE':{'op':'mul','left':{'op':'x'},'right':{'op':'const','value':2}},
}
def simulate(seed_index,generations=6):
 master=f'v846-stress-seed-{seed_index}'
 members={pid:{'genome':g,'gsha':ev.genome_sha(g),'ssha':ev.shape_sha(g),'innov':[]} for pid,g in FOUNDERS.items()};selected=sorted(members);ag={m['gsha'] for m in members.values()};ash={m['ssha'] for m in members.values()};struct=0;her=set();best0=max(ev.score_genome(g,CASES)['correct'] for g in FOUNDERS.values())
 for gen in range(1,generations+1):
  cs=[]
  for pid in selected:
   p=members[pid];seed=ev.mutation_seed(master,gen,p['gsha'],pid);g,op=ev.mutate(p['genome'],seed);cls=ev._classify(g,ag,ash);cs.append({'id':f'G{gen}:{pid}:{seed[:12]}','parent':pid,'g':g,'gsha':ev.genome_sha(g),'ssha':ev.shape_sha(g),'score':ev.score_genome(g,CASES)['correct'],'cls':cls,'innov':list(p['innov'])})
  pool=[{'kind':'inc','id':pid,'gsha':members[pid]['gsha'],'score':ev.score_genome(members[pid]['genome'],CASES)['correct']} for pid in selected]+[{'kind':'cand','id':c['id'],'gsha':c['gsha'],'score':c['score']} for c in cs]
  rank=sorted(pool,key=lambda x:(-x['score'],0 if x['kind']=='cand' else 1,x['gsha'],x['id']))[:4];ns=[];serial=0
  for x in rank:
   if x['kind']=='inc':ns.append(x['id']);continue
   serial+=1;c=next(q for q in cs if q['id']==x['id']);iid=ev._child_name(gen,{'genome_sha256':c['gsha']},serial);innov=list(c['innov'])
   if c['cls']=='structural_novelty':innov.append('INNOV-'+sha256_bytes(canonical({'g':gen,'genome':c['gsha'],'parent':c['parent']}))[:16]);struct+=1
   her|=(set(innov)&set(members[c['parent']]['innov']));members[iid]={'genome':c['g'],'gsha':c['gsha'],'ssha':c['ssha'],'innov':innov};ns.append(iid)
  for c in cs:ag.add(c['gsha']);ash.add(c['ssha'])
  selected=sorted(ns)
 best=max(ev.score_genome(members[x]['genome'],CASES)['correct'] for x in selected)
 return {'best0':best0,'best':best,'gain':best-best0,'structural':struct,'heritable':len(her),'archive_genomes':len(ag),'archive_shapes':len(ash),'seed_index':seed_index}
