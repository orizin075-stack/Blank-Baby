from __future__ import annotations
import hashlib
from .deps import activate
from .constants import H3_DEDUP_SHA256
activate()
import tukuyo_v846.evolution as ev
from tukuyo_v846.util import canonical,sha256_bytes
CASES=[{'id':f'C{i+1:02d}','x':x,'expected':2*abs(x)} for i,x in enumerate(range(-6,7))]
FOUNDER_SETS={
 'release':{
  'X':{'op':'x'},'ABS':{'op':'abs','arg':{'op':'x'}},'PLUS1':{'op':'add','left':{'op':'x'},'right':{'op':'const','value':1}},'DOUBLE':{'op':'mul','left':{'op':'x'},'right':{'op':'const','value':2}},
 },
 'no_double':{
  'X':{'op':'x'},'PLUS1':{'op':'add','left':{'op':'x'},'right':{'op':'const','value':1}},'MINUS1':{'op':'add','left':{'op':'x'},'right':{'op':'const','value':-1}},'NEG':{'op':'neg','arg':{'op':'x'}},
 },
 'far_shapes':{
  'CONST0':{'op':'const','value':0},'CONST1':{'op':'const','value':1},'MAX0':{'op':'max','left':{'op':'x'},'right':{'op':'const','value':0}},'MIN0':{'op':'min','left':{'op':'x'},'right':{'op':'const','value':0}},
 }
}

def simulate(fset,master,gens=6):
 founders={f'TUKUYO-v8461-{name}':g for name,g in fset.items()}
 members={pid:{'genome':g,'gsha':ev.genome_sha(g),'ssha':ev.shape_sha(g),'innov':[]} for pid,g in founders.items()};selected=sorted(members);ag={m['gsha'] for m in members.values()};ash={m['ssha'] for m in members.values()};struct=0;her=set();best0=max(ev.score_genome(g,CASES)['correct'] for g in founders.values())
 for gen in range(1,gens+1):
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
 return {'best0':best0,'best':best,'gain':best-best0,'structural':struct,'heritable':len(her),'archive_genomes':len(ag),'archive_shapes':len(ash),'final_perfect':best==len(CASES)}

def build_assay(replicates_each=20,generations_each=6):
 out={'schema':'tukuyo.v846_1.external_seed_assay/1','seed_source_sha256':H3_DEDUP_SHA256,'seed_source_role':'external-to-v846-evolution-fixture canonical benchmark identity only','human_independence_claim':False,'derivation':'sha256(seed_source_sha256|fixture_name|replicate_index)','generations_each':generations_each,'replicates_each':replicates_each,'fixtures':{}}
 for name,fset in FOUNDER_SETS.items():
  rows=[]
  for i in range(replicates_each):
   master=hashlib.sha256(f'{H3_DEDUP_SHA256}|{name}|{i}'.encode()).hexdigest();r=simulate(fset,master,generations_each);r['replicate_index']=i;r['master_seed']=master;rows.append(r)
  out['fixtures'][name]={'founder_best':rows[0]['best0'],'runs_with_structural_novelty':sum(r['structural']>0 for r in rows),'runs_with_performance_gain':sum(r['gain']>0 for r in rows),'runs_with_heritable_innovation':sum(r['heritable']>0 for r in rows),'runs_reaching_13_of_13':sum(r['final_perfect'] for r in rows),'max_gain':max(r['gain'] for r in rows),'replicate_results':rows}
 return out
