"""Real organism + isolated synthetic research bridge. No automatic promotion."""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import math
from datetime import datetime, timezone

TASKS=('v935_reference','coupled_product','difference_shift')


def canon(o):
    return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')


def h(o):
    return hashlib.sha256(canon(o)).hexdigest()


def _state(data):
    return Path(data).resolve()/'state'


def _require_healthy(api,data):
    a=api['social'].audit(_state(data))
    b=api['organism'].audit(_state(data))
    if not a['ok'] or not b['ok']:
        raise RuntimeError('CORE_AUDIT_FAILED:'+str((a,b)))
    return a,b


def init(api,data,individual_id='TUKUYO-v938-001'):
    d=Path(data).resolve();d.mkdir(parents=True,exist_ok=True)
    api['social'].init(_state(d),individual_id)
    status(api,d)
    return status(api,d)


def status(api,data):
    social,org=_require_healthy(api,data)
    return {'ok':True,'version':'v938','core':'v837/v838/v840/v841',
            'social':social,'organism':org,
            'research':'v937_shadow_only',
            'auto_promotion':False,
            'accelerated_ticks_are_not_elapsed_wallclock':True}


def tick(api,data,count):
    _require_healthy(api,data)
    if not isinstance(count,int) or count<1 or count>10000:
        raise ValueError('ticks must be between 1 and 10000')
    api['organism'].run_life_ticks(_state(data),count)
    return status(api,data)


def evaluate(api,data,query):
    _require_healthy(api,data)
    if not isinstance(query,str) or len(query)>1024:
        raise ValueError('invalid query length')
    return api['organism'].evaluate(_state(data),query)


def _check_samples(body):
    if not isinstance(body,dict) or set(body)!={'surface','training','holdout'}:
        raise ValueError('JSON requires surface, training, holdout')
    if not isinstance(body['surface'],str) or not body['surface'].strip() or len(body['surface'])>80:
        raise ValueError('invalid surface')
    train=body['training'];hold=body['holdout']
    if not (isinstance(train,list) and isinstance(hold,list) and 2<=len(train)<=100 and 3<=len(hold)<=100):
        raise ValueError('training 2..100, holdout 3..100')
    seen=set()
    for row in train+hold:
        if not isinstance(row,dict) or set(row)!={'a','b','expected'} or any(type(row[k]) not in (int,float) for k in row):
            raise ValueError('sample row must have numeric a,b,expected')
        if any(not math.isfinite(float(row[k])) or abs(row[k])>10000 for k in row):
            raise ValueError('sample values must be finite and bounded')
        pair=(row['a'],row['b'])
        if pair in seen:
            raise ValueError('duplicate/overlapping training and holdout cases')
        seen.add(pair)
    return body


def teach(api,data,evidence_json,apply=False):
    _require_healthy(api,data)
    if not apply:
        raise PermissionError('EXPLICIT_APPLY_REQUIRED: add --apply to spend organism resources and change semantics')
    path=Path(evidence_json)
    if not path.is_file() or path.stat().st_size>64*1024:
        raise ValueError('evidence file missing or too large')
    body=_check_samples(json.loads(path.read_text(encoding='utf-8')))
    result=api['organism'].learn(_state(data),body['surface'],body['training'],body['holdout'],protocol_test_fixture=False)
    from tukuyo_v954.provenance import persist_teach_bundle,sha_obj
    request=persist_teach_bundle(data,body['surface'],result['semantic_provenance'])
    _require_healthy(api,data)
    return {'ok':True,'operator':result['operator'],'cost':result['cost'],
            'semantic_state_sha256':h(result['integration_state']),
            'promotion_authority':'EXTERNAL_CAPABILITY_AUTHORITY_REQUIRED_BEFORE_RUNTIME_RESOLUTION',
            'capability_request_sha256':sha_obj(request)}


def run_research(api,data,task='coupled_product',seed=93601):
    """Run existing v937 developer experiment without writing to organism state."""
    if task not in TASKS or type(seed) is not int or seed<0 or seed>100000000:
        raise ValueError('invalid task or seed')
    _require_healthy(api,data)
    state_file=_state(data)/api['organism'].ISTATE
    before=hashlib.sha256(state_file.read_bytes()).hexdigest()
    result=api['research'].one(task,train_seed=seed)
    model=result.pop('models')['chosen'];source=result.pop('generated_source')
    out=Path(data).resolve()/'research_runs'
    out.mkdir(parents=True,exist_ok=True)
    output_id=f'{task}_{seed}_{hashlib.sha256(source.encode()).hexdigest()[:12]}'
    path=out/output_id
    if path.exists():
        previous=json.loads((path/'REPORT.json').read_text(encoding='utf-8'))
        if previous['candidate_source_sha256']!=hashlib.sha256(source.encode()).hexdigest():
            raise RuntimeError('RESEARCH_RUN_COLLISION')
    else:
        path.mkdir()
        (path/'MODEL.json').write_bytes(canon(model)+b'\n')
        (path/'CANDIDATE.py').write_text(source,encoding='utf-8')
    after=hashlib.sha256(state_file.read_bytes()).hexdigest()
    if before!=after:raise RuntimeError('RESEARCH_MUTATED_LIVE_ORGANISM')
    report={'task':task,'seed':seed,'status':'SYNTHETIC_RESEARCH_ONLY',
            'candidate_source_sha256':hashlib.sha256(source.encode()).hexdigest(),
            'candidate_model_sha256':hashlib.sha256(canon(model)+b'\n').hexdigest(),
            'v937_original_zip_sha256':__import__('tukuyo_v938.bootstrap',fromlist=['V937_SHA256']).V937_SHA256,
            'organism_state_before_sha256':before,'organism_state_after_sha256':after,
            'auto_promoted':False,'metrics':result}
    (path/'REPORT.json').write_bytes(canon(report)+b'\n')
    return {'ok':True,'result_directory':str(path),'task':task,'candidate_source_sha256':report['candidate_source_sha256'],
            'chosen_grammar':result['chosen_grammar'],'test':result['test'],
            'organism_unchanged':True,'promotion':'BLOCKED_PENDING_REAL_EVALUATION'}


def diagnose(api,data,queries,model_task='v935_reference'):
    """Ground synthetic a,b,c in explicitly provided *real core* evaluation probes.

    Metrics do not share validated meanings with v937's synthetic labels, and
    the resulting action is advisory only, not a runtime control decision.
    """
    if model_task not in TASKS or not isinstance(queries,list) or not 1<=len(queries)<=200:
        raise ValueError('1..200 probes and valid model_task required')
    _require_healthy(api,data)
    raw=[]
    for q in queries:
        if not isinstance(q,str) or len(q)>1024:raise ValueError('invalid probe')
        x=evaluate(api,data,q)
        y=evaluate(api,data,q)
        raw.append({'query':q,'first':x,'repeated_same':x==y})
    open_rows=[r for r in raw if r['first'].get('status')=='OPEN']
    nonempty={r['first'].get('surface') for r in raw if r['first'].get('surface')}
    open_surfaces={r['first'].get('surface') for r in open_rows if r['first'].get('surface')}
    a=len(open_rows)/len(raw)
    b=(len(open_surfaces)/len(nonempty)) if nonempty else 0.
    c=sum(not x['repeated_same'] for x in raw)/len(raw)
    metrics={'a':a,'b':b,'c':c}
    path=api['research_root']/'evidence'/f'{model_task}_model.json'
    tree=json.loads(path.read_text(encoding='utf-8'))
    suggestion=api['learner'].predict(tree,metrics)
    return {'ok':True,'probes':len(raw),'open':len(open_rows),'metrics':metrics,
            'shadow_suggestion':suggestion,'suggestion_is_synthetic_unvalidated':True,
            'live_policy_modified':False,'results':raw}


def write_chat_log(data,user,response):
    d=Path(data).resolve()/'local_chat';d.mkdir(parents=True,exist_ok=True)
    file=d/'conversation.jsonl'
    head=d/'HEAD.json'
    before=json.loads(head.read_text()) if head.exists() else {'sequence':0,'sha256':'0'*64}
    body={'seq':before['sequence']+1,'prev_sha256':before['sha256'],
          'local_utc_time_unanchored':datetime.now(timezone.utc).isoformat(),
          'user':user,'response':response}
    body['entry_sha256']=h({k:v for k,v in body.items() if k!='entry_sha256'})
    with file.open('a',encoding='utf-8') as f:f.write(json.dumps(body,ensure_ascii=False,sort_keys=True)+'\n')
    head.write_bytes(canon({'sequence':body['seq'],'sha256':body['entry_sha256']})+b'\n')
    return body['seq']
