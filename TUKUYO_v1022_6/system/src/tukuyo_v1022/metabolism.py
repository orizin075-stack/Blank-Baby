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
    max_ticks,max_runtimes=bounds(s)
    if type(s['tick']) is not int or not 0<=s['tick']<=max_ticks or len(s['runtimes'])>max_runtimes or len(s['active'])>8:raise ValueError('V1022_METABOLISM_BOUND')
    changes=s.get('environment_changes',[])
    if any(type(c.get('tick')) is not int or type(c.get('regeneration')) is not int or not 0<=c['regeneration']<=100000 for c in changes):raise ValueError('V1022_ENVIRONMENT_CHANGE')
    if changes and changes[-1]['regeneration']!=s['config']['regeneration']:raise ValueError('V1022_ENVIRONMENT_BINDING')
    if any(type(s[k]) is not int or s[k]<0 for k in ('reservoir','burned','initial_total','regenerated')):raise ValueError('V1022_RESOURCE_TYPE')
    if not set(s['active'])<=set(s['runtimes']) or len(s['active'])!=len(set(s['active'])):raise ValueError('V1022_ACTIVE_BINDING')
    energy=sum(s['runtimes'][r]['energy'] for r in s['active'])
    if s['initial_total']+s['regenerated']!=s['reservoir']+s['burned']+energy:raise ValueError('V1022_RESOURCE_CONSERVATION')
    if any(s['runtimes'][r]['lifecycle']=='DEAD' for r in s['active']):raise ValueError('V1022_ACTIVE_DEAD')
    rewards=s.get('grounded_rewards',[]);receipt_ids=[]
    for i,row in enumerate(rewards,1):
        if (row.get('seq')!=i or not re.fullmatch(r'R\d{6}',row.get('runtime',''))
                or not re.fullmatch(r'[0-9a-f]{64}',row.get('receipt_sha256',''))
                or type(row.get('requested')) is not int or type(row.get('paid')) is not int
                or not 1<=row['paid']<=row['requested']<=1000):raise ValueError('V1022_GROUNDED_REWARD_ROW')
        receipt_ids.append(row['receipt_sha256'])
    if len(receipt_ids)!=len(set(receipt_ids)):raise ValueError('V1022_GROUNDED_RECEIPT_REPLAY')
    if 'research' in s:
        # claude-patch5 opt-in research niche (metabolism-init --research-world)
        from tukuyo_v1023r import niche
        niche.validate(s['research'])
        if s['config'].get('research_world') is not True or not set(s['active'])<=set(s['research']['runtimes']):raise ValueError('V1023R_NICHE_BINDING')
# v1022.7.9: a long run (the roadmap's v1022.8.2 asks for 1,000 steps or more) chooses larger bounds at init. An
# ecology made before keeps the old ones (512 ticks, 64 runtimes); the largest are 4096 ticks and 256 runtimes.
TICK_BOUND,RUNTIME_BOUND=4096,256
def bounds(s):
    c=s['config'];t=c.get('max_ticks',512);r=c.get('max_runtimes',64)
    if type(t) is not int or type(r) is not int or not 32<=t<=TICK_BOUND or not 8<=r<=RUNTIME_BOUND:raise ValueError('V1022_METABOLISM_BOUND_CONFIG')
    return t,r
def preflight(d):
    s=store.load(d,NS,COMPONENT,_validate)
    if s.get('grounded_rewards'):
        from . import grounded_sensor
        authorized={whole.sha_obj(r['receipt_envelope']):r for r in grounded_sensor.load(d)['outcomes'] if r['success'] and r['resource_credit']}
        for reward in s['grounded_rewards']:
            source=authorized.get(reward['receipt_sha256'])
            if not source or source['runtime_id']!=reward['runtime'] or source['resource_credit']!=reward['requested']:
                raise ValueError('V1022_GROUNDED_AUTHORIZATION_BINDING')
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
    if len(s['runtimes'])>=bounds(s)[1]:raise ValueError('V1022_RUNTIME_LIMIT')
    rid=f"R{len(s['runtimes']):06d}";ident=whole._live_identity(d)['individual_id']+'-metabolic-'+rid
    if rid in s['runtimes']:raise ValueError('V1022_FRESH_REGISTERED_SLOT')
    p=child(d,rid)
    if p.exists() or p.is_symlink():
        # A late synchronized, unregistered future is not a fresh child. Keep
        # every old byte (including keys) in a private signed archive, then
        # create the new runtime without importing its identity or caches.
        import os,uuid
        from tukuyo_v1019.transaction import _reject_symlinks
        from tukuyo_common.atomic_fs import _fsync_dir
        if p.is_symlink() or not p.is_dir():raise ValueError('V1022_FRESH_SLOT_NOT_DIRECTORY')
        _reject_symlinks(p)
        files=sorted(q for q in p.rglob('*') if q.is_file())
        if len(files)>4096:raise ValueError('V1022_FRESH_COLLISION_BOUND')
        hashes={q.relative_to(p).as_posix():hashlib.sha256(q.read_bytes()).hexdigest() for q in files}
        bucket=root(d)/'private'/'newborn_collision_archive'/(rid+'-'+uuid.uuid4().hex)
        bucket.mkdir(parents=True,exist_ok=False)
        os.replace(p,bucket/'runtime');_fsync_dir(p.parent);_fsync_dir(bucket)
        receipt={'schema':'tukuyo.v1022_7_4.newborn_collision/1','runtime_id':rid,
                 'registered_runtime_replaced':False,'file_sha256':hashes,'old_keys_reused':False}
        atomic_write_bytes(bucket/'RECEIPT.json',whole.canon(whole._sign(d,receipt))+b'\n')
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
def init(d,trust_file,families=4,seed='v1022',reservoir=20000,regeneration=0,max_age=32,learning=True,actions=True,research_world=False,
         max_ticks=512,max_runtimes=64,sharing=False):
    if root(d).exists():raise ValueError('V1022_METABOLISM_REINITIALIZATION')
    if type(families) is not int or not 2<=families<=8:raise ValueError('V1022_FAMILY_BOUND')
    if type(reservoir) is not int or not 0<=reservoir<=1000000 or type(regeneration) is not int or not 0<=regeneration<=100000:raise ValueError('V1022_RESOURCE_BOUND')
    if type(max_age) is not int or not 4<=max_age<=128:raise ValueError('V1022_AGE_BOUND')
    if type(max_ticks) is not int or type(max_runtimes) is not int or not 32<=max_ticks<=TICK_BOUND or not 8<=max_runtimes<=RUNTIME_BOUND:raise ValueError('V1022_METABOLISM_BOUND_CONFIG')
    if trust_file is None:raise ValueError('V1022_EXTERNAL_RUNTIME_TRUST_REQUIRED')
    from tukuyo_v977.startup_guard import verify_distribution
    verify_distribution(Path(__file__).resolve().parents[2],trust_file)
    atomic_write_bytes(root(d)/'RUNTIME_TRUST.txt',Path(trust_file).read_bytes());atomic_write_text(root(d)/'private/delegation.token',secrets.token_hex(32),mode=0o600)
    s={'schema':SCHEMA,'tick':0,'seed':hashlib.sha256(str(seed).encode()).hexdigest(),'reservoir':reservoir,'burned':0,
       'initial_total':reservoir+6500*families,'regenerated':0,'config':{'regeneration':regeneration,'max_age':max_age,'learning':bool(learning),'actions':bool(actions),
                                                                        **({'max_ticks':max_ticks,'max_runtimes':max_runtimes} if (max_ticks,max_runtimes)!=(512,64) else {}),
                                                                        **({'sharing':True} if sharing else {})},
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
    if len(s['runtimes'])>=bounds(s)[1] or s['performance'][parent]['correct']<2:return None
    pledges={}
    if s['reservoir']<6500:
        # v1022.8.2: the commons cannot fund the child. With sharing on, the living are asked, each by its own heart,
        # whether to give of its energy to raise the child of the one that died (its bond with that one weighs)
        if not s['config'].get('sharing'):return None
        pledges=_pledges(d,s,parent,tick,6500-s['reservoir'])
        if sum(pledges.values())<6500-s['reservoir']:return None
    rid,ident=_fresh(d,s);pp=root(d)/'packages'/f'{parent}.pub';cp=root(d)/'packages'/f'{rid}.pub';pkg=root(d)/'packages'/f'{parent}-{rid}.json'
    _cli(d,parent,'succession-pubkey-export','--out',pp);_cli(d,rid,'succession-pubkey-export','--out',cp)
    _cli(d,parent,'evolution-export',ident,'--out',pkg,'--child-public-key-file',cp);s['runtimes'][parent]=_snapshot(d,parent)
    _cli(d,rid,'evolution-import',pkg,'--parent-trust-file',pp)
    cultural=_culture(child(d,parent),child(d,rid),'mortality-gated-public-skills') if s['config']['learning'] else None
    from_commons=6500-sum(pledges.values());s['reservoir']-=from_commons
    for giver,amount in pledges.items():_give(d,s,giver,rid,amount,{'tick':tick,'raised':rid,'for':parent},'raised-a-child',newborn=True)
    s['runtimes'][rid]=_snapshot(d,rid);s['active'].append(rid);s['performance'][rid]=_performance()
    s['successions'].append({'tick':tick,'parent':parent,'child':rid,'package_sha256':hashlib.sha256(pkg.read_bytes()).hexdigest(),
        'public_learning_commitment':cultural,'actual_inherited_profile':s['runtimes'][rid]['profile'],'funded_seed_energy':6500,
        **({'funded_by':{'commons':from_commons,'runtimes':pledges}} if pledges else {})})
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
    if s['tick']+ticks>bounds(s)[0]:raise ValueError('V1022_TOTAL_TICK_BOUND')
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
                    heart_loop.feedback(p,hc['id'],max(-1.,min(1.,(credit-(cost-300))/600)),.2,'niche-energy-outcome',origin='simulated')
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
                if not probe:heart_loop.feedback(p,chosen,max(-1.,min(1.,net/600)),.2,'grounded-energy-outcome',origin='simulated')
            age=organism2.load(p).get('metabolic_age',0)
            if energy+credit<=cost or age+1>=s['config']['max_age']:evolution.select(p,'resource',seed=f"{s['seed']}|{rid}|{tick}")
            m=organism2.metabolic_tick(p,credit,cost,s['config']['max_age']);s['burned']+=m['burn'];whole.sync(p);s['runtimes'][rid]=_snapshot(d,rid)
            rows.append({'runtime':rid,'action':chosen,'question':query,'answer':answer,'expected':expected,'correct':correct,'uncertain':uncertain,'credit':credit,'burn':m['burn'],'energy_after':s['runtimes'][rid]['energy'],**({'niche':niche_row} if niche_row else {})})
            if m['death_cause']:
                s['active'].remove(rid);s['deaths'].append({'runtime':rid,'tick':tick,'cause':m['death_cause']});maybe_crash('metabolism:after_death');_successor(d,s,rid,tick)
        shared=_share(d,s,tick) if s['config'].get('sharing') else []
        s['tick']=tick;s['last_tick']={'tick':tick,'regenerated':regen,'actions':rows,**({'shared':shared} if shared else {})};_validate(s)
        atomic_write_bytes(root(d)/'ticks'/f'{tick:06d}.json',whole.canon(s['last_tick'])+b'\n');store.save(d,NS,COMPONENT,s)
    return summary(s)

# v1022.8.2 relations: energy given between runtimes, decided by the giver's heart, its bond with the other weighing
HUNGRY,SATED,GIFT,KEEP_FLOOR=3000,7000,1000,4000
def _bond(d,giver,other):
    """what the giver's soul holds of the other runtime (its attachment, -1..1; 0 for one never met)"""
    try:return float(whole.load_soul(child(d,giver)).get('attachments',{}).get('runtime:'+other,0.0))
    except Exception:  # noqa: BLE001 - an unreadable soul gives no bond; the audits report it
        return 0.0
def _ask_heart(d,s,giver,other,context,cost,need):
    """the giver's heart chooses: give (the other's need and its bond with the other pull; what it costs itself, less when
    it has plenty, holds back) or keep. Its own values (inherited and lived) weigh both"""
    b=_bond(d,giver,other);surplus=max(0.,min(1.,(s['runtimes'][giver]['energy']-SATED)/(10000-SATED)))
    # what giving costs it weighs less the less of its own life is left (its energy will not serve it long)
    left=_life_left(d,s,giver)
    opts=[{'id':'give','signals':{'relationship':round(.3+.7*max(-1.,min(1.,b))+.6*need,6),'survival':round(-cost*(1-surplus)*left,6)}},
          {'id':'keep','signals':{'survival':.25}}]
    ok=heart_loop.choose(child(d,giver),opts,context=context)['chosen']=='give';whole.sync(child(d,giver))
    return ok,b
def _give(d,s,giver,taker,amount,what,theme,newborn=False):
    """move energy from one runtime to another (the total stays), and each lives it: the taker was helped by the giver"""
    receipt=hashlib.sha256(whole.canon({**what,'giver':giver,'taker':taker,'amount':amount})).hexdigest()
    pg,pt=child(d,giver),child(d,taker)
    organism2.resource_gift(pg,amount,receipt)
    if not newborn:organism2.resource_credit(pt,amount,receipt)
    heart_loop.process_experience(pt,'support',.8,.5,theme,'runtime:'+giver,origin='simulated')
    heart_loop.process_experience(pg,'care',.3,.3,theme,'runtime:'+taker,origin='simulated')
    whole.sync(pg);whole.sync(pt);s['runtimes'][giver]=_snapshot(d,giver)
    if not newborn:s['runtimes'][taker]=_snapshot(d,taker)
    rel=s.setdefault('relations',{'gifts':0,'energy_given':0,'returned':0,'refused':0,'raised':0,'pairs':{}})
    pair=f'{giver}>{taker}';back=f'{taker}>{giver}'
    rel['gifts']+=1;rel['energy_given']+=amount;rel['raised']+=int(newborn)
    if back in rel['pairs']:rel['returned']+=1          # it gives back to one that gave to it
    rel['pairs'][pair]=rel['pairs'].get(pair,0)+1
    return receipt
def _share(d,s,tick):
    out=[];rel=s.setdefault('relations',{'gifts':0,'energy_given':0,'returned':0,'refused':0,'raised':0,'pairs':{}})
    for taker in sorted([r for r in s['active'] if s['runtimes'][r]['energy']<HUNGRY],key=lambda r:s['runtimes'][r]['energy']):
        givers=sorted([r for r in s['active'] if r!=taker and s['runtimes'][r]['energy']>=SATED],key=lambda r:(-s['runtimes'][r]['energy'],r))
        if not givers:break
        giver=givers[0];ok,b=_ask_heart(d,s,giver,taker,f'share-tick-{tick}',.1,1-s['runtimes'][taker]['energy']/HUNGRY)
        if ok:_give(d,s,giver,taker,GIFT,{'tick':tick},'shared-energy');out.append({'giver':giver,'taker':taker,'amount':GIFT,'bond':round(b,4)})
        else:
            rel['refused']+=1;out.append({'giver':giver,'taker':taker,'amount':0,'bond':round(b,4)})
            s['runtimes'][giver]=_snapshot(d,giver)
    return out
def _life_left(d,s,rid):
    """the share of its life still ahead (1 newborn .. 0 at its last tick)"""
    age=organism2.load(child(d,rid)).get('metabolic_age',0);m=s['config']['max_age']
    return max(0.,min(1.,(m-age)/m))
def _pledges(d,s,parent,tick,need):
    out={}
    for r in sorted([r for r in s['active'] if r!=parent],key=lambda r:(-s['runtimes'][r]['energy'],r)):
        spare=s['runtimes'][r]['energy']-max(300,int(KEEP_FLOOR*_life_left(d,s,r)))
        if spare<=0:continue
        ok,_=_ask_heart(d,s,r,parent,f'raise-{parent}-tick-{tick}',.15,.5);s['runtimes'][r]=_snapshot(d,r)
        if ok:out[r]=min(spare,2500,need-sum(out.values()))
        if sum(out.values())>=need:break
    return {k:v for k,v in out.items() if v>0}

@transactional()
def environment(d,regeneration):
    """v1022.7.9: the environment changes from the next tick on (the regeneration of the shared reservoir), e.g. a
    drought. The runtimes are not told; they meet it. Every change is kept with its tick."""
    if type(regeneration) is not int or not 0<=regeneration<=100000:raise ValueError('V1022_RESOURCE_BOUND')
    s=copy.deepcopy(preflight(d));before=s['config']['regeneration']
    s.setdefault('environment_changes',[]).append({'tick':s['tick'],'from':before,'regeneration':regeneration})
    s['config']['regeneration']=regeneration;_validate(s);store.save(d,NS,COMPONENT,s)
    return {**summary(s),'environment_change':s['environment_changes'][-1]}

@transactional()
def grounded_reward(d,runtime_id,credit,receipt_sha256):
    """Transfer a verifier-bound finite reward into one actual runtime.

    The reward comes from the existing reservoir, so conservation is retained.
    The measured action must already be committed in the enclosing transaction.
    Receipt transfer does not advance age; metabolism.step owns elapsed ticks.
    """
    if not re.fullmatch(r'R\d{6}',runtime_id):raise ValueError('V1022_GROUNDED_RUNTIME_ID')
    if type(credit) is not int or not 1<=credit<=1000:raise ValueError('V1022_GROUNDED_CREDIT')
    if not re.fullmatch(r'[0-9a-f]{64}',receipt_sha256):raise ValueError('V1022_GROUNDED_RECEIPT')
    from . import grounded_sensor,sensor_action
    try:
        evidence=grounded_sensor.load(d)
        source=next(r for r in evidence['outcomes'] if whole.sha_obj(r['receipt_envelope'])==receipt_sha256)
        if (not source['success'] or source['runtime_id']!=runtime_id or source['resource_credit']!=credit
                or source['receipt_envelope']['payload']['schema']!=sensor_action.RECEIPT_SCHEMA):
            raise ValueError('authorization')
        intent=sensor_action.authorize(evidence,source['receipt_envelope']['payload'])
    except (ValueError,KeyError,StopIteration) as exc:
        raise ValueError('V1022_GROUNDED_AUTHORIZATION_REQUIRED') from exc
    s=copy.deepcopy(preflight(d));rewards=s.setdefault('grounded_rewards',[])
    if runtime_id not in s['active']:raise ValueError('V1022_GROUNDED_RUNTIME_INACTIVE')
    if s['runtimes'][runtime_id]['whole_sha256']!=intent['runtime_head_sha256']:
        raise ValueError('V1022_GROUNDED_RUNTIME_HEAD_CHANGED')
    if any(row['receipt_sha256']==receipt_sha256 for row in rewards):raise ValueError('V1022_GROUNDED_RECEIPT_REPLAY')
    p=child(d,runtime_id);before=s['runtimes'][runtime_id]['energy'];room=max(0,10000-before)
    paid=min(credit,s['reservoir'],room)
    if paid<=0:raise ValueError('V1022_GROUNDED_NO_RESOURCE_OR_CAPACITY')
    s['reservoir']-=paid
    m=organism2.resource_credit(p,paid,receipt_sha256);whole.sync(p)
    s['runtimes'][runtime_id]=_snapshot(d,runtime_id)
    row={'seq':len(rewards)+1,'runtime':runtime_id,'receipt_sha256':receipt_sha256,
         'runtime_head_before_sha256':intent['runtime_head_sha256'],
         'requested':credit,'paid':paid,'energy_before':before,
         'energy_after':s['runtimes'][runtime_id]['energy'],'burn':m['burn'],'death_cause':m['death_cause']}
    rewards.append(row)
    if m['death_cause']:
        s['active'].remove(runtime_id);s['deaths'].append({'runtime':runtime_id,'tick':s['tick'],'cause':m['death_cause'],'source':'grounded_reward'})
        _successor(d,s,runtime_id,s['tick'])
    _validate(s);store.save(d,NS,COMPONENT,s)
    return {'ok':True,'version':'v1022.7.3','runtime':runtime_id,'requested':credit,'paid':paid,
            'energy_before':before,'energy_after':s['runtimes'][runtime_id]['energy'],
            'reservoir_after':s['reservoir'],'resource_conservation':True,'death_cause':m['death_cause']}

def summary(s):
    total=lambda k:sum(p[k] for p in s['performance'].values())
    return {'ok':True,'version':'v1022','tick':s['tick'],'active_runtime_count':len(s['active']),'total_runtime_count':len(s['runtimes']),
        'actual_successions':len(s['successions']),'max_generation':max((r['generation'] for r in s['runtimes'].values()),default=0),
        'reservoir':s['reservoir'],'burned':s['burned'],'initial_total':s['initial_total'],'regenerated':s['regenerated'],
        'living_energy':sum(s['runtimes'][r]['energy'] for r in s['active']),**{k:total(k) for k in ('attempts','correct','wrong','abstained','hard_attempts','hard_correct')},
        'deaths':s['deaths'],'successions':s['successions'],'grounded_rewards':s.get('grounded_rewards',[]),'last_tick':s['last_tick'],'claim_boundary':CLAIMS,
        'bounds':dict(zip(('max_ticks','max_runtimes'),bounds(s))),
        'alive':[{'runtime':r,'family':s['runtimes'][r]['family'],'generation':s['runtimes'][r]['generation'],'energy':s['runtimes'][r]['energy']} for r in s['active']],
        'sharing':bool(s['config'].get('sharing')),'relations':{k:v for k,v in s.get('relations',{}).items() if k!='pairs'},'regeneration':s['config']['regeneration'],'environment_changes':s.get('environment_changes',[]),
        **({'research_niche':__import__('tukuyo_v1023r.niche',fromlist=['summary']).summary(s['research'],s['seed']),'research_claim_boundary':s['research']['claim_boundary']} if 'research' in s else {})}
def status(d):return summary(preflight(d))
def audit(d):
    try:return {**status(d),'resource_conservation':True,'errors':[]}
    except Exception as e:return {'ok':False,'version':'v1022','errors':[str(e)]}
