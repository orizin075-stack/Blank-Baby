"""Finite resource ecology whose participants are actual independent runtimes.

Task answers affect resource transfers. Each runtime burns energy and becomes
irreversibly dead at energy exhaustion. Succession retains the mortality gate.
"""
from __future__ import annotations
import copy,hashlib,json,os,re,secrets,subprocess,sys
from pathlib import Path
from tukuyo_common.atomic_fs import atomic_write_bytes,atomic_write_text,maybe_crash
from tukuyo_v977 import whole_state as whole
from tukuyo_v1018 import succession
from tukuyo_v1019 import evolution
from tukuyo_v1019.transaction import transactional
from tukuyo_v978 import heart_loop
from tukuyo_v1007 import organism2
from . import cognition,store

NS='v1022_ecology';COMPONENT='runtime_metabolism_v1022';SCHEMA='tukuyo.v1022.metabolism/1'
CLAIMS={'every_participant_is_actual_runtime':True,'action_task_result_affects_energy':True,'energy_death_without_injury':True,
        'single_actual_trait_line':True,'mortality_gated_successor':True,'living_parent_reproduction':False,
        'natural_selection_established':False,'open_ended_evolution':False,'self_code_modification':False,'consciousness_established':False,'24h_completed':False}
def root(d):return Path(d)/NS
def child(d,rid):
    if not re.fullmatch(r'R\d{6}',rid):raise ValueError('V1022_RUNTIME_ID')
    return root(d)/'runtimes'/rid
def _cli(d,rid,*args):
    runtime=Path(__file__).resolve().parents[2];token=(root(d)/'private/delegation.token').read_text().strip()
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','TUKUYO_OWNER_DELEGATION':token};env.pop('TUKUYO_CRASH_POINT',None)
    p=subprocess.run([sys.executable,'-B',str(runtime/'run_tukuyo.py'),'--runtime-trust-file',str(root(d)/'RUNTIME_TRUST.txt'),
                      '--data',str(child(d,rid)),*map(str,args)],capture_output=True,text=True,env=env,timeout=180)
    try:r=json.loads(p.stdout)
    except Exception:raise ValueError('V1022_CHILD_OUTPUT')
    if p.returncode or not r.get('ok'):raise ValueError('V1022_CHILD_COMMAND:'+str(r.get('error',args[0])))
    return r
def _snapshot(d,rid):
    # The owner's mutable stage is not permission to re-sign an old child head.
    from tukuyo_v1019.transaction import ACTIVE
    token=ACTIVE.set(False)
    try:return _committed_snapshot(d,rid)
    finally:ACTIVE.reset(token)
def _committed_snapshot(d,rid):
    p=child(d,rid)
    if not whole.audit(p).get('ok'):raise ValueError('V1022_CHILD_AUDIT:'+rid)
    s=succession.ensure_state(p)[0];o=organism2.load(p)
    return {'individual_id':whole._live_identity(p)['individual_id'],'family':s['family_lineage_id'],'generation':s['generation'],
        'succession_public_key':succession.public_key(p),'whole_public_key':whole._key_paths(p)[1].read_text().strip(),
        'whole_sha256':hashlib.sha256(whole.state_path(p).read_bytes()).hexdigest(),
        'soul_sha256':hashlib.sha256(whole.soul_path(p).read_bytes()).hexdigest(),'heart_sha256':hashlib.sha256(heart_loop.state_path(p).read_bytes()).hexdigest(),
        'lifecycle':o['lifecycle'],'energy':int(round(o['energy']*100)),'profile':succession.effective_values(p),'learning_rounds':cognition.state(p)['rounds']}
def _validate(s):
    if s.get('schema')!=SCHEMA or s.get('claim_boundary')!=CLAIMS:raise ValueError('V1022_METABOLISM_SCHEMA')
    if type(s['tick']) is not int or not 0<=s['tick']<=512 or len(s['runtimes'])>64 or len(s['active'])>8:raise ValueError('V1022_METABOLISM_BOUND')
    if any(type(s[k]) is not int or s[k]<0 for k in ('reservoir','burned','initial_total','regenerated')):raise ValueError('V1022_RESOURCE_TYPE')
    if not set(s['active'])<=set(s['runtimes']) or len(s['active'])!=len(set(s['active'])):raise ValueError('V1022_ACTIVE_BINDING')
    energy=sum(s['runtimes'][r]['energy'] for r in s['active'])
    if s['initial_total']+s['regenerated']!=s['reservoir']+s['burned']+energy:raise ValueError('V1022_RESOURCE_CONSERVATION')
    if any(s['runtimes'][r]['lifecycle']=='DEAD' for r in s['active']):raise ValueError('V1022_ACTIVE_DEAD')
    if 'research' in s:
        # claude-patch5 opt-in research niche (metabolism-init --research-world)
        from tukuyo_v1023r import niche
        niche.validate(s['research'])
        if s['config'].get('research_world') is not True or not set(s['active'])<=set(s['research']['runtimes']):raise ValueError('V1023R_NICHE_BINDING')
def preflight(d):
    s=store.load(d,NS,COMPONENT,_validate)
    for rid,row in s['runtimes'].items():
        if _snapshot(d,rid)!=row:raise ValueError('V1022_RUNTIME_DRIFT:'+rid)
    for k in ('succession_public_key','whole_public_key'):
        if len({r[k] for r in s['runtimes'].values()})!=len(s['runtimes']):raise ValueError('V1022_SHARED_KEY')
    for e in s['successions']:
        if e['public_learning_commitment']:
            proofs=cognition.state(child(d,e['child']))['inherited_public_learning'];p=next((p for p in proofs if whole.sha_obj(p)==e['public_learning_commitment']),None)
            if p is None or p['public_key']!=s['runtimes'][e['parent']]['whole_public_key'] or p['payload']['source_individual_id']!=s['runtimes'][e['parent']]['individual_id']:raise ValueError('V1022_CULTURAL_PARENT_BINDING')
    return s
def _fresh(d,s):
    if len(s['runtimes'])>=64:raise ValueError('V1022_RUNTIME_LIMIT')
    rid=f"R{len(s['runtimes']):06d}";ident=whole._live_identity(d)['individual_id']+'-metabolic-'+rid
    _cli(d,rid,'init','--individual-id',ident,'--blank-learning');_cli(d,rid,'organism2-init')
    heart_loop.load(child(d,rid));heart_loop.audit(child(d,rid));whole.sync(child(d,rid));return rid,ident
def _culture(source,target,tag):
    # Public skills only. No private facts, autobiography, keys or dialogue
    # transcripts are copied to the next individual.
    parent=cognition.state(source);s=cognition.state(target);s['event_rules']=copy.deepcopy(parent['event_rules']);s['aliases']=dict(parent['aliases'])
    payload={'source_individual_id':whole._live_identity(source)['individual_id'],'target_individual_id':whole._live_identity(target)['individual_id'],
             'tag':tag,'rules_sha256':whole.sha_obj(s['event_rules']),'aliases_sha256':whole.sha_obj(s['aliases'])}
    proof=whole._sign(source,payload);s['inherited_public_learning'].append(proof);store.save(target,cognition.NS,cognition.COMPONENT,s);return whole.sha_obj(proof)
def _performance():return {k:0 for k in ('attempts','correct','wrong','abstained','hard_attempts','hard_correct','simple_attempts','simple_correct')}
@transactional()
def init(d,trust_file,families=4,seed='v1022',reservoir=20000,regeneration=0,max_age=32,learning=True,actions=True,research_world=False):
    if root(d).exists():raise ValueError('V1022_METABOLISM_REINITIALIZATION')
    if type(families) is not int or not 2<=families<=8:raise ValueError('V1022_FAMILY_BOUND')
    if type(reservoir) is not int or not 0<=reservoir<=1000000 or type(regeneration) is not int or not 0<=regeneration<=100000:raise ValueError('V1022_RESOURCE_BOUND')
    if type(max_age) is not int or not 4<=max_age<=128:raise ValueError('V1022_AGE_BOUND')
    if trust_file is None:raise ValueError('V1022_EXTERNAL_RUNTIME_TRUST_REQUIRED')
    from tukuyo_v977.startup_guard import verify_distribution
    verify_distribution(Path(__file__).resolve().parents[2],trust_file)
    atomic_write_bytes(root(d)/'RUNTIME_TRUST.txt',Path(trust_file).read_bytes());atomic_write_text(root(d)/'private/delegation.token',secrets.token_hex(32),mode=0o600)
    s={'schema':SCHEMA,'tick':0,'seed':hashlib.sha256(str(seed).encode()).hexdigest(),'reservoir':reservoir,'burned':0,
       'initial_total':reservoir+6500*families,'regenerated':0,'config':{'regeneration':regeneration,'max_age':max_age,'learning':bool(learning),'actions':bool(actions)},
       'runtimes':{},'active':[],'performance':{},'deaths':[],'successions':[],'last_tick':None,'claim_boundary':CLAIMS}
    if research_world:
        from tukuyo_v1023r import niche
        s['config']['research_world']=True;s['research']={'schema':'tukuyo.v1023r.niche/1','claim_boundary':niche.CLAIMS,'runtimes':{},'econ':dict(niche.ECON)}
    for i in range(families):
        rid,ident=_fresh(d,s);_cli(d,rid,'succession-founder-init')
        if learning:_culture(d,child(d,rid),'owner-to-founder-public-skills')
        s['runtimes'][rid]=_snapshot(d,rid);s['active'].append(rid);s['performance'][rid]=_performance()
        if research_world:s['research']['runtimes'][rid]=niche.new_record(s['seed'],s['runtimes'][rid]['family'],f'N{i}',None)
    _validate(s);store.save(d,NS,COMPONENT,s);return summary(s)
def _task(s,rid,tick,hard):
    b=hashlib.sha256(f"{s['seed']}|{rid}|{tick}".encode()).digest();per=5+b[0]%9;count=3+b[1]%6;used=1+b[2]%5
    if hard:
        cs=[f'{used}個売った',f'{used}個を仕入先へ返品した',f'{used}個を紛失した',f'{used}個を借り入れた'];kind=b[3]%4
        query=f'1箱に{per}個入りが{count}箱、今の在庫としてあります。{cs[kind]}。今の在庫の残りは何個？';answer=per*count+(used if kind==3 else -used)
    else:query=f'({per} * {count}) - {used}';answer=per*count-used
    return query,str(answer)
def _successor(d,s,parent,tick):
    if s['reservoir']<6500 or len(s['runtimes'])>=64 or s['performance'][parent]['correct']<2:return None
    rid,ident=_fresh(d,s);pp=root(d)/'packages'/f'{parent}.pub';cp=root(d)/'packages'/f'{rid}.pub';pkg=root(d)/'packages'/f'{parent}-{rid}.json'
    _cli(d,parent,'succession-pubkey-export','--out',pp);_cli(d,rid,'succession-pubkey-export','--out',cp)
    _cli(d,parent,'evolution-export',ident,'--out',pkg,'--child-public-key-file',cp);s['runtimes'][parent]=_snapshot(d,parent)
    _cli(d,rid,'evolution-import',pkg,'--parent-trust-file',pp)
    cultural=_culture(child(d,parent),child(d,rid),'mortality-gated-public-skills') if s['config']['learning'] else None
    s['reservoir']-=6500;s['runtimes'][rid]=_snapshot(d,rid);s['active'].append(rid);s['performance'][rid]=_performance()
    s['successions'].append({'tick':tick,'parent':parent,'child':rid,'package_sha256':hashlib.sha256(pkg.read_bytes()).hexdigest(),
        'public_learning_commitment':cultural,'actual_inherited_profile':s['runtimes'][rid]['profile'],'funded_seed_energy':6500})
    if 'research' in s:
        # Science is culture too: only a CONFIRMED law of the parent, and only when learning is on.
        from tukuyo_v1023r import niche
        pa=s['research']['runtimes'][parent]['agent'];law=pa['claim'] if (s['config']['learning'] and pa['status']=='CONFIRMED' and pa['claim']) else None
        law={k:v for k,v in law.items() if k!='inherited'} if law else None
        s['research']['runtimes'][rid]=niche.new_record(s['seed'],s['runtimes'][rid]['family'],s['research']['runtimes'][parent]['niche'],law);s['successions'][-1]['inherited_law']=law['law'] if law else None
    maybe_crash('metabolism:after_successor');return rid
@transactional()
def step(d,ticks=1):
    if type(ticks) is not int or not 1<=ticks<=32:raise ValueError('V1022_STEP_BOUND')
    s=copy.deepcopy(preflight(d))
    if s['tick']+ticks>512:raise ValueError('V1022_TOTAL_TICK_BOUND')
    for _ in range(ticks):
        tick=s['tick']+1;regen=s['config']['regeneration'];s['reservoir']+=regen;s['regenerated']+=regen;rows=[]
        for rid in list(s['active']):
            p=child(d,rid);perf=s['performance'][rid];energy=s['runtimes'][rid]['energy']
            query=answer=expected=None;correct=uncertain=False;credit=0;cost=300;niche_row=None
            if 'research' in s:
                # claude-patch5 research niche: the runtime's research agent proposes, its Heart accepts or rests.
                from tukuyo_v1023r import niche
                rec=s['research']['runtimes'][rid];age0=organism2.load(p).get('metabolic_age',0);hc={}
                def _heart(opts):
                    r=heart_loop.choose(p,opts,context=f'niche-tick-{tick}') if s['config']['actions'] else {'chosen':'rest'};hc['id']=r['chosen'];return r['chosen']
                chosen,credit,extra,niche_row=niche.tick(s['seed'],rec,rid,energy,s['config']['max_age']-age0,_heart,s['reservoir'])
                cost+=extra;s['reservoir']-=credit;correct=credit>0
                if chosen=='work':perf['attempts']+=1;perf['correct']+=int(correct)
                if hc.get('id') and hc['id']==chosen and chosen!='rest':
                    heart_loop.feedback(p,hc['id'],max(-1.,min(1.,(credit-(cost-300))/600)),.2,'niche-energy-outcome')
            else:
              # claude-patch1: homeostatic choice. Options carry EXPECTED NET ENERGY from the last few
              # paid outcomes; energy above the satiety set-point is worth nothing, so a fed individual
              # rests instead of burning the commons, and a hungry one works where it pays most.
              def p_paid(kind):
                r=perf.get('recent_'+kind,[]);return (sum(r)+1)/(len(r)+2)
              need=max(0,8000-energy);room=10000-energy;er=energy/10000
              ev_hard=p_paid('hard')*min(1100,need,room)-200;ev_simple=p_paid('simple')*min(600,need,room)-100
              opts=[{'id':'hard','signals':{'curiosity':1.2*er*(1 if ev_hard>=0 else .25),'survival':ev_hard/300,'truthfulness':.1}},
                  {'id':'simple','signals':{'curiosity':.05*er,'survival':ev_simple/300,'truthfulness':.3}},
                  {'id':'rest','signals':{'survival':.3 if max(ev_hard,ev_simple)<0 else 0.,'integrity':.1}}]
              chosen=heart_loop.choose(p,opts,context=f'metabolic-tick-{tick}')['chosen'] if s['config']['actions'] else 'rest'
              # Cheap periodic probe so a resting individual can notice that resources returned.
              probe=False
              if chosen=='rest' and s['config']['actions'] and energy>1500 and (tick+int(rid[1:]))%6==0:chosen='simple';probe=True
              if chosen!='rest':
                hard=chosen=='hard';query,expected=_task(s,rid,tick,hard);result=cognition.solve(p,query);answer=result['answer'];uncertain=result['uncertain'];correct=not uncertain and answer==expected
                perf['attempts']+=1;perf['correct']+=int(correct);perf['abstained']+=int(uncertain);perf['wrong']+=int(not uncertain and not correct)
                perf[chosen+'_attempts']+=1;perf[chosen+'_correct']+=int(correct);cost+=200 if hard else 100
                if correct:credit=min(1100 if hard else 600,s['reservoir'],10000-energy);s['reservoir']-=credit
                perf[chosen+'_paid']=perf.get(chosen+'_paid',perf[chosen+'_correct']-int(correct))+int(credit>0)
                perf['recent_'+chosen]=(perf.get('recent_'+chosen,[])+[int(credit>0)])[-6:]
                # Valence = net energy relative to resting (rest burns the base 300 only).
                net=credit-(cost-300)
                # A probe overrides the heart's own choice, so it is not fed back as that choice's outcome.
                if not probe:heart_loop.feedback(p,chosen,max(-1.,min(1.,net/600)),.2,'grounded-energy-outcome')
            age=organism2.load(p).get('metabolic_age',0)
            if energy+credit<=cost or age+1>=s['config']['max_age']:evolution.select(p,'resource',seed=f"{s['seed']}|{rid}|{tick}")
            m=organism2.metabolic_tick(p,credit,cost,s['config']['max_age']);s['burned']+=m['burn'];whole.sync(p);s['runtimes'][rid]=_snapshot(d,rid)
            rows.append({'runtime':rid,'action':chosen,'question':query,'answer':answer,'expected':expected,'correct':correct,'uncertain':uncertain,'credit':credit,'burn':m['burn'],'energy_after':s['runtimes'][rid]['energy'],**({'niche':niche_row} if niche_row else {})})
            if m['death_cause']:
                s['active'].remove(rid);s['deaths'].append({'runtime':rid,'tick':tick,'cause':m['death_cause']});maybe_crash('metabolism:after_death');_successor(d,s,rid,tick)
        s['tick']=tick;s['last_tick']={'tick':tick,'regenerated':regen,'actions':rows};_validate(s)
        atomic_write_bytes(root(d)/'ticks'/f'{tick:06d}.json',whole.canon(s['last_tick'])+b'\n');store.save(d,NS,COMPONENT,s)
    return summary(s)
def summary(s):
    total=lambda k:sum(p[k] for p in s['performance'].values())
    return {'ok':True,'version':'v1022','tick':s['tick'],'active_runtime_count':len(s['active']),'total_runtime_count':len(s['runtimes']),
        'actual_successions':len(s['successions']),'max_generation':max((r['generation'] for r in s['runtimes'].values()),default=0),
        'reservoir':s['reservoir'],'burned':s['burned'],'initial_total':s['initial_total'],'regenerated':s['regenerated'],
        'living_energy':sum(s['runtimes'][r]['energy'] for r in s['active']),**{k:total(k) for k in ('attempts','correct','wrong','abstained','hard_attempts','hard_correct')},
        'deaths':s['deaths'],'successions':s['successions'],'last_tick':s['last_tick'],'claim_boundary':CLAIMS,
        **({'research_niche':__import__('tukuyo_v1023r.niche',fromlist=['summary']).summary(s['research'],s['seed']),'research_claim_boundary':s['research']['claim_boundary']} if 'research' in s else {})}
def status(d):return summary(preflight(d))
def audit(d):
    try:return {**status(d),'resource_conservation':True,'errors':[]}
    except Exception as e:return {'ok':False,'version':'v1022','errors':[str(e)]}
