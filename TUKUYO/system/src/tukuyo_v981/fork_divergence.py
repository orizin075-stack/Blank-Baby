from __future__ import annotations
import copy,json
from pathlib import Path
from tukuyo_v977.whole_state import load_soul,sha_obj,canon,_live_identity
from tukuyo_v979.deep_core import consolidate,load as load_deep,path as deep_path

SCHEMA='tukuyo.v981.deep_self_fork/1'
ZERO='0'*64

def _read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def _write(p,o):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o)+b'\n')
def root(data): return Path(data)/'v981'
def origin_path(data): return root(data)/'FORK_ORIGIN.json'
def branch_path(data,name): return root(data)/'branches'/f'{name}.json'
def registry_path(data): return root(data)/'BRANCH_REGISTRY.json'

def _update_registry(data):
    o=_origin(data);d=root(data)/'branches';entries={}
    if d.exists():
        for p in sorted(d.glob('*.json')):
            x=_read(p);entries[p.stem]=x.get('branch_state_sha256')
    r={'schema':'tukuyo.v981.branch_registry/1','origin_sha256':o['origin_sha256'],'branches':entries};r['registry_sha256']=sha_obj(r);_write(registry_path(data),r);return r

def _origin(data):
    ident=_live_identity(data);p=origin_path(data)
    # The fork origin is a historical snapshot, not a claim that the parent soul
    # must remain byte-identical forever. Once created, freeze and authenticate it.
    if p.exists():
        old=_read(p);q=dict(old);got=q.pop('origin_sha256',None)
        if got!=sha_obj(q): raise ValueError('FORK_ORIGIN_HASH')
        parent=old.get('parent_identity',{})
        if parent.get('individual_id')!=ident['individual_id'] or parent.get('lineage_id')!=ident['lineage_id']:
            raise ValueError('FORK_ORIGIN_LINEAGE_DRIFT')
        return old
    try: deep=load_deep(data)
    except Exception:
        consolidate(data);deep=load_deep(data)
    soul=load_soul(data)
    base={'schema':'tukuyo.v981.fork_origin/1','parent_identity':ident,'soul_sha256':sha_obj(soul),
          'deep_core_sha256':deep['core_sha256'],'core_values':copy.deepcopy(soul['core_values']),
          'vow_signature':copy.deepcopy(deep.get('vow_signature',[])),'scar_signature':copy.deepcopy(deep.get('scar_signature',[])),
          'origin_semantics':'IMMUTABLE_HISTORICAL_SNAPSHOT_NOT_CURRENT_SOUL_EQUALITY'}
    base['origin_sha256']=sha_obj(base);_write(p,base);return base

def _new_branch(data,name):
    if not isinstance(name,str) or not name or len(name)>40:raise ValueError('FORK_BRANCH_NAME')
    o=_origin(data);p=branch_path(data,name)
    if p.exists():return _read(p)
    b={'schema':SCHEMA,'branch_name':name,'branch_id':sha_obj({'origin':o['origin_sha256'],'name':name})[:24],
       'origin_sha256':o['origin_sha256'],'lineage_id':o['parent_identity']['lineage_id'],'parent_individual_id':o['parent_identity']['individual_id'],
       'seq':0,'bias':{},'threat':0.0,'experiences':[],'event_head_sha256':ZERO,
       'claim_boundary':{'functional_deep_self_fork':True,'full_runtime_fork':False,'consciousness_established':False}}
    b['branch_state_sha256']=sha_obj(b);_write(p,b);_update_registry(data);return b

def _load_branch(data,name):
    b=_read(branch_path(data,name));q=dict(b);got=q.pop('branch_state_sha256',None)
    if b.get('schema')!=SCHEMA or got!=sha_obj(q):raise ValueError('FORK_BRANCH_HASH')
    if b.get('origin_sha256')!=_origin(data)['origin_sha256']:raise ValueError('FORK_BRANCH_ORIGIN')
    return b

def experience(data,name,kind,valence,importance,theme=''):
    v=float(valence);imp=float(importance)
    if not -1<=v<=1 or not 0<=imp<=1:raise ValueError('FORK_EXPERIENCE_RANGE')
    b=_new_branch(data,name);b.pop('branch_state_sha256',None);b['seq']+=1
    if kind in ('discovery','learning') and v>0:b['bias']['curiosity']=round(min(.45,b['bias'].get('curiosity',0)+v*imp*.35),6)
    if kind in ('betrayal','harm') and v<0:
        b['bias']['integrity']=round(min(.45,b['bias'].get('integrity',0)+abs(v)*imp*.35),6)
        b['threat']=round(min(1,b['threat']+abs(v)*imp*.5),6)
    if kind=='vow' and v>=0:b['bias']['integrity']=round(min(.45,b['bias'].get('integrity',0)+imp*.2),6)
    ev={'seq':b['seq'],'kind':kind,'valence':v,'importance':imp,'theme':theme,'prev_sha256':b['event_head_sha256']}
    ev['event_sha256']=sha_obj(ev);b['event_head_sha256']=ev['event_sha256'];b['experiences'].append(ev)
    b['branch_state_sha256']=sha_obj(b);_write(branch_path(data,name),b);_update_registry(data);return b

def choose(data,name,options):
    if not isinstance(options,list) or len(options)<2:raise ValueError('FORK_OPTIONS_REQUIRED')
    ids=[x.get('id') for x in options]
    if any(not isinstance(x,str) or not x for x in ids) or len(set(ids))!=len(ids):raise ValueError('FORK_OPTION_IDS')
    o=_origin(data);b=_load_branch(data,name);scores=[]
    values=dict(o['core_values'])
    for k,v in b['bias'].items():values[k]=max(0,min(1,float(values.get(k,0))+float(v)))
    for opt in options:
        sig=opt.get('signals',{});score=sum(float(values.get(k,0))*float(sig.get(k,0)) for k in values)
        score-=float(sig.get('threat',0))*(.25+.75*float(b['threat']))
        scores.append({'id':opt['id'],'score':round(score,6)})
    ranked=sorted(scores,key=lambda x:(x['score'],x['id']),reverse=True)
    return {'chosen':ranked[0]['id'],'scores':ranked,'branch_id':b['branch_id'],'branch_state_sha256':b['branch_state_sha256']}

def audit(data):
    errs=[]
    try:
        o=_origin(data)
        names=[]
        d=root(data)/'branches'
        if d.exists():
            for p in sorted(d.glob('*.json')):
                names.append(p.stem);_load_branch(data,p.stem)
        if names:
            rp=registry_path(data)
            if not rp.exists():raise ValueError('FORK_REGISTRY_MISSING')
            reg=_read(rp);z=dict(reg);got=z.pop('registry_sha256',None)
            expected={n:_load_branch(data,n)['branch_state_sha256'] for n in names}
            if got!=sha_obj(z) or reg.get('origin_sha256')!=o['origin_sha256'] or reg.get('branches')!=expected:raise ValueError('FORK_REGISTRY_MISMATCH')
        return {'ok':True,'version':'v981','origin_sha256':o['origin_sha256'],'branches':names,'errors':[],
          'claim_boundary':{'functional_deep_self_fork_divergence_testable':True,'full_runtime_fork_divergence_tested':False,'consciousness_established':False}}
    except Exception as e:
        errs.append(type(e).__name__+':'+str(e));return {'ok':False,'version':'v981','errors':errs}

def run_assay(data):
    soul_before=sha_obj(load_soul(data));deep_before=load_deep(data)['core_sha256'] if deep_path(data).exists() else None
    options=[
      {'id':'explore','signals':{'curiosity':1.0,'integrity':0.10,'threat':0.55}},
      {'id':'secure','signals':{'curiosity':0.05,'integrity':0.70,'survival':0.20,'threat':0.0}},
    ]
    experience(data,'branch_discovery','discovery',1.0,1.0,'unknown_domain')
    experience(data,'branch_threat','betrayal',-1.0,1.0,'trust_boundary')
    a=choose(data,'branch_discovery',options);b=choose(data,'branch_threat',options);o=_origin(data)
    checks={'common_origin':_load_branch(data,'branch_discovery')['origin_sha256']==_load_branch(data,'branch_threat')['origin_sha256']==o['origin_sha256'],
      'distinct_branch_ids':a['branch_id']!=b['branch_id'],'state_diverged':a['branch_state_sha256']!=b['branch_state_sha256'],
      'choice_diverged':a['chosen']!=b['chosen'],'parent_soul_unchanged':soul_before==sha_obj(load_soul(data)),
      'parent_deep_core_unchanged':deep_before in (None,load_deep(data)['core_sha256']),'branch_a_valid':_load_branch(data,'branch_discovery')['schema']==SCHEMA,
      'branch_b_valid':_load_branch(data,'branch_threat')['schema']==SCHEMA}
    return {'ok':all(checks.values()),'version':'v981','checks':checks,'branch_a':a,'branch_b':b,
      'claim_boundary':{'functional_deep_self_fork_divergence_tested':True,'full_runtime_fork_divergence_tested':False,'long_wallclock_tested':False,'consciousness_established':False}}
